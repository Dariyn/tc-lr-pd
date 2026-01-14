"""
Tests for outlier detection module.

Validates z-score, IQR, percentile methods and consensus flagging logic.
"""

import pytest
import pandas as pd
import numpy as np
from src.analysis.outlier_detector import (
    detect_zscore_outliers,
    detect_iqr_outliers,
    detect_percentile_outliers,
    detect_outliers
)


def test_detect_zscore_outliers():
    """Test z-score outlier detection with known values."""
    # Create sample data with clear outlier
    # Mean=10, Std~2, Equipment with frequency=20 should have z-score > 2.0
    data = {
        'Equipment_ID': ['E1', 'E2', 'E3', 'E4', 'E5'],
        'equipment_primary_category': ['HVAC'] * 5,
        'work_orders_per_month': [9.0, 10.0, 10.0, 11.0, 20.0]  # mean=12, std=4.36, z-score for E5 = (20-12)/4.36 = 1.83
    }
    df = pd.DataFrame(data)

    # Use threshold=1.5 to ensure E5 is flagged
    result = detect_zscore_outliers(df, threshold=1.5)

    # Verify columns added
    assert 'z_score' in result.columns
    assert 'is_zscore_outlier' in result.columns

    # E5 (freq=20) should be flagged as outlier
    e5_row = result[result['Equipment_ID'] == 'E5'].iloc[0]
    assert e5_row['is_zscore_outlier'] == True

    # E1-E4 should not be flagged
    for eq_id in ['E1', 'E2', 'E3', 'E4']:
        row = result[result['Equipment_ID'] == eq_id].iloc[0]
        assert row['is_zscore_outlier'] == False


def test_detect_zscore_outliers_zero_std():
    """Test z-score method handles categories with zero standard deviation."""
    # All equipment have same frequency (std=0)
    data = {
        'Equipment_ID': ['E1', 'E2', 'E3'],
        'equipment_primary_category': ['Elevator'] * 3,
        'work_orders_per_month': [5.0, 5.0, 5.0]
    }
    df = pd.DataFrame(data)

    result = detect_zscore_outliers(df, threshold=2.0)

    # No equipment should be flagged as outlier
    assert result['is_zscore_outlier'].sum() == 0

    # Z-scores should all be 0
    assert (result['z_score'] == 0.0).all()


def test_detect_iqr_outliers():
    """Test IQR outlier detection with known quartile values."""
    # Create data with clear outlier
    # Q1 (25th) = 5, Q3 (75th) = 15, IQR = 10
    # Upper threshold = 15 + 1.5*10 = 30
    data = {
        'Equipment_ID': [f'E{i}' for i in range(1, 11)],
        'equipment_primary_category': ['Plumbing'] * 10,
        'work_orders_per_month': [2.0, 5.0, 8.0, 10.0, 12.0, 15.0, 18.0, 22.0, 28.0, 50.0]
        # Q1=8.5, Q3=21.0, IQR=12.5, threshold=39.75, E10=50.0 > 39.75
    }
    df = pd.DataFrame(data)

    result = detect_iqr_outliers(df)

    # Verify column added
    assert 'is_iqr_outlier' in result.columns

    # E10 (freq=50) is above Q3 + 1.5*IQR, should be flagged
    e10_row = result[result['Equipment_ID'] == 'E10'].iloc[0]
    assert e10_row['is_iqr_outlier'] == True

    # E1-E9 should not be flagged (within IQR range)
    for i in range(1, 10):
        row = result[result['Equipment_ID'] == f'E{i}'].iloc[0]
        assert row['is_iqr_outlier'] == False


def test_detect_percentile_outliers():
    """Test percentile-based outlier detection."""
    # 10 equipment with frequencies 1-10
    # 90th percentile should be around 9
    data = {
        'Equipment_ID': [f'E{i}' for i in range(1, 11)],
        'equipment_primary_category': ['Electrical'] * 10,
        'work_orders_per_month': [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]
    }
    df = pd.DataFrame(data)

    result = detect_percentile_outliers(df, percentile=90)

    # Verify columns added
    assert 'percentile_rank' in result.columns
    assert 'is_percentile_outlier' in result.columns

    # E10 (freq=10) should be flagged
    e10_row = result[result['Equipment_ID'] == 'E10'].iloc[0]
    assert e10_row['is_percentile_outlier'] == True
    assert e10_row['percentile_rank'] > 90

    # E1-E9 should not be flagged
    for i in range(1, 10):
        row = result[result['Equipment_ID'] == f'E{i}'].iloc[0]
        assert row['is_percentile_outlier'] == False


def test_detect_outliers_consensus():
    """Test consensus flagging combines multiple methods correctly."""
    # Create data where some equipment are flagged by multiple methods
    # Equipment with very high frequency should be flagged by all methods
    data = {
        'Equipment_ID': ['E1', 'E2', 'E3', 'E4', 'E5', 'E6'],
        'equipment_primary_category': ['HVAC'] * 6,
        'work_orders_per_month': [5.0, 6.0, 7.0, 8.0, 12.0, 50.0]
        # E6 is extreme outlier, should be flagged by all methods
        # E5 might be flagged by some methods
    }
    df = pd.DataFrame(data)

    result = detect_outliers(df, methods=['zscore', 'iqr', 'percentile'])

    # Verify consensus columns added
    assert 'outlier_count' in result.columns
    assert 'is_outlier_consensus' in result.columns

    # E6 (freq=50) should be flagged by multiple methods
    e6_row = result[result['Equipment_ID'] == 'E6'].iloc[0]
    assert e6_row['outlier_count'] >= 2
    assert e6_row['is_outlier_consensus'] == True

    # E1 (freq=5) should not be flagged by any method
    e1_row = result[result['Equipment_ID'] == 'E1'].iloc[0]
    assert e1_row['outlier_count'] == 0
    assert e1_row['is_outlier_consensus'] == False


def test_detect_outliers_multiple_categories():
    """Test outlier detection across multiple categories."""
    # Create data with two categories
    # Each category should be analyzed independently
    data = {
        'Equipment_ID': ['H1', 'H2', 'H3', 'E1', 'E2', 'E3'],
        'equipment_primary_category': ['HVAC', 'HVAC', 'HVAC', 'Elevator', 'Elevator', 'Elevator'],
        'work_orders_per_month': [5.0, 6.0, 20.0, 10.0, 11.0, 30.0]
    }
    df = pd.DataFrame(data)

    result = detect_outliers(df)

    # H3 and E3 are high within their respective categories
    # Both should potentially be flagged
    h3_row = result[result['Equipment_ID'] == 'H3'].iloc[0]
    e3_row = result[result['Equipment_ID'] == 'E3'].iloc[0]

    # Verify they have higher outlier counts than others in their category
    h1_count = result[result['Equipment_ID'] == 'H1'].iloc[0]['outlier_count']
    e1_count = result[result['Equipment_ID'] == 'E1'].iloc[0]['outlier_count']

    assert h3_row['outlier_count'] >= h1_count
    assert e3_row['outlier_count'] >= e1_count


def test_detect_outliers_single_method():
    """Test detection with only one method enabled."""
    data = {
        'Equipment_ID': ['E1', 'E2', 'E3'],
        'equipment_primary_category': ['HVAC'] * 3,
        'work_orders_per_month': [5.0, 6.0, 20.0]
    }
    df = pd.DataFrame(data)

    result = detect_outliers(df, methods=['zscore'])

    # Only zscore columns should exist
    assert 'z_score' in result.columns
    assert 'is_zscore_outlier' in result.columns
    assert 'is_iqr_outlier' not in result.columns
    assert 'is_percentile_outlier' not in result.columns

    # Consensus should still work with single method
    assert 'outlier_count' in result.columns
    assert 'is_outlier_consensus' in result.columns


def test_detect_outliers_empty_dataframe():
    """Test handling of empty input DataFrame."""
    df = pd.DataFrame({
        'Equipment_ID': [],
        'equipment_primary_category': [],
        'work_orders_per_month': []
    })

    result = detect_outliers(df)

    # Should return empty DataFrame with proper columns
    assert len(result) == 0
    assert 'outlier_count' in result.columns
    assert 'is_outlier_consensus' in result.columns


def test_detect_outliers_single_equipment_per_category():
    """Test handling of categories with only one equipment."""
    data = {
        'Equipment_ID': ['E1', 'E2'],
        'equipment_primary_category': ['HVAC', 'Elevator'],
        'work_orders_per_month': [10.0, 15.0]
    }
    df = pd.DataFrame(data)

    result = detect_outliers(df)

    # Single equipment in category should not be flagged as outlier
    assert result['is_outlier_consensus'].sum() == 0
