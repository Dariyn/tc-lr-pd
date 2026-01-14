"""
Tests for frequency analysis calculations.

Validates work order frequency metrics and category statistics.
"""

import pytest
import pandas as pd
from datetime import datetime, timedelta
from src.analysis.frequency_analyzer import (
    calculate_equipment_frequencies,
    calculate_category_statistics
)


def test_calculate_equipment_frequencies_basic():
    """Test basic frequency calculation with known equipment and dates."""
    # Create sample data with 3 work orders for one equipment over 60 days
    start_date = datetime(2024, 1, 1)
    data = {
        'Equipment_ID': ['EQ001', 'EQ001', 'EQ001'],
        'equipment_primary_category': ['HVAC', 'HVAC', 'HVAC'],
        'Create_Date': [
            start_date,
            start_date + timedelta(days=30),
            start_date + timedelta(days=60)
        ],
        'Complete_Date': [
            start_date + timedelta(days=1),
            start_date + timedelta(days=31),
            start_date + timedelta(days=62)
        ],
        'PO_AMOUNT': [100.0, 200.0, 150.0]
    }
    df = pd.DataFrame(data)

    result = calculate_equipment_frequencies(df)

    assert len(result) == 1
    assert result.iloc[0]['Equipment_ID'] == 'EQ001'
    assert result.iloc[0]['equipment_primary_category'] == 'HVAC'
    assert result.iloc[0]['total_work_orders'] == 3

    # Timespan: day 0 to day 60 = 61 days (inclusive)
    assert result.iloc[0]['timespan_days'] == 61

    # Work orders per month: (3 / 61) * 30.44 ≈ 1.498
    expected_wpm = (3 / 61) * 30.44
    assert abs(result.iloc[0]['work_orders_per_month'] - expected_wpm) < 0.001

    # Average completion: (1 + 1 + 2) / 3 = 1.33 days
    assert abs(result.iloc[0]['avg_completion_days'] - 1.333) < 0.01

    # Average cost: (100 + 200 + 150) / 3 = 150
    assert result.iloc[0]['avg_cost'] == 150.0


def test_calculate_equipment_frequencies_single_order():
    """Test equipment with only one work order has correct defaults."""
    data = {
        'Equipment_ID': ['EQ002'],
        'equipment_primary_category': ['Electrical'],
        'Create_Date': [datetime(2024, 1, 15)],
        'Complete_Date': [datetime(2024, 1, 16)],
        'PO_AMOUNT': [500.0]
    }
    df = pd.DataFrame(data)

    result = calculate_equipment_frequencies(df)

    assert len(result) == 1
    assert result.iloc[0]['total_work_orders'] == 1

    # Single work order: timespan defaults to 1 day
    assert result.iloc[0]['timespan_days'] == 1

    # Work orders per month: (1 / 1) * 30.44 = 30.44
    assert abs(result.iloc[0]['work_orders_per_month'] - 30.44) < 0.001

    # Single completion time: 1 day
    assert result.iloc[0]['avg_completion_days'] == 1.0

    # Single cost
    assert result.iloc[0]['avg_cost'] == 500.0


def test_calculate_equipment_frequencies_missing_dates():
    """Test handling of missing Complete_Date values."""
    data = {
        'Equipment_ID': ['EQ003', 'EQ003', 'EQ003'],
        'equipment_primary_category': ['Plumbing', 'Plumbing', 'Plumbing'],
        'Create_Date': [
            datetime(2024, 1, 1),
            datetime(2024, 2, 1),
            datetime(2024, 3, 1)
        ],
        'Complete_Date': [
            datetime(2024, 1, 5),  # Complete
            pd.NaT,                # Missing
            datetime(2024, 3, 3)   # Complete
        ],
        'PO_AMOUNT': [100.0, 200.0, 150.0]
    }
    df = pd.DataFrame(data)

    result = calculate_equipment_frequencies(df)

    assert len(result) == 1

    # Should only average the 2 valid completion times: (4 + 2) / 2 = 3 days
    assert result.iloc[0]['avg_completion_days'] == 3.0


def test_calculate_equipment_frequencies_zero_costs():
    """Test that zero and negative costs are excluded from average."""
    data = {
        'Equipment_ID': ['EQ004', 'EQ004', 'EQ004', 'EQ004'],
        'equipment_primary_category': ['Security', 'Security', 'Security', 'Security'],
        'Create_Date': [
            datetime(2024, 1, 1),
            datetime(2024, 1, 2),
            datetime(2024, 1, 3),
            datetime(2024, 1, 4)
        ],
        'Complete_Date': [
            datetime(2024, 1, 2),
            datetime(2024, 1, 3),
            datetime(2024, 1, 4),
            datetime(2024, 1, 5)
        ],
        'PO_AMOUNT': [100.0, 0.0, 200.0, -50.0]  # Only 100 and 200 should be averaged
    }
    df = pd.DataFrame(data)

    result = calculate_equipment_frequencies(df)

    assert len(result) == 1

    # Average cost should only include positive values: (100 + 200) / 2 = 150
    assert result.iloc[0]['avg_cost'] == 150.0


def test_calculate_equipment_frequencies_multiple_equipment():
    """Test calculation for multiple equipment in different categories."""
    data = {
        'Equipment_ID': ['EQ001', 'EQ001', 'EQ002', 'EQ002'],
        'equipment_primary_category': ['HVAC', 'HVAC', 'Electrical', 'Electrical'],
        'Create_Date': [
            datetime(2024, 1, 1),
            datetime(2024, 2, 1),
            datetime(2024, 1, 1),
            datetime(2024, 3, 1)
        ],
        'Complete_Date': [
            datetime(2024, 1, 2),
            datetime(2024, 2, 2),
            datetime(2024, 1, 3),
            datetime(2024, 3, 2)
        ],
        'PO_AMOUNT': [100.0, 200.0, 150.0, 250.0]
    }
    df = pd.DataFrame(data)

    result = calculate_equipment_frequencies(df)

    assert len(result) == 2
    assert set(result['Equipment_ID']) == {'EQ001', 'EQ002'}
    assert set(result['equipment_primary_category']) == {'HVAC', 'Electrical'}


def test_calculate_category_statistics():
    """Test category statistics aggregation."""
    # Create frequency data for 3 equipment in 2 categories
    freq_data = {
        'Equipment_ID': ['EQ001', 'EQ002', 'EQ003'],
        'equipment_primary_category': ['HVAC', 'HVAC', 'Electrical'],
        'total_work_orders': [10, 5, 8],
        'work_orders_per_month': [2.0, 1.0, 1.5]
    }
    freq_df = pd.DataFrame(freq_data)

    result = calculate_category_statistics(freq_df)

    assert len(result) == 2

    # Check HVAC category
    hvac_stats = result[result['equipment_primary_category'] == 'HVAC'].iloc[0]
    assert hvac_stats['equipment_count'] == 2
    assert hvac_stats['total_work_orders'] == 15  # 10 + 5
    assert hvac_stats['mean_frequency'] == 1.5    # (2.0 + 1.0) / 2
    assert hvac_stats['median_frequency'] == 1.5  # median of [1.0, 2.0]
    assert hvac_stats['min_frequency'] == 1.0
    assert hvac_stats['max_frequency'] == 2.0

    # Check Electrical category
    elec_stats = result[result['equipment_primary_category'] == 'Electrical'].iloc[0]
    assert elec_stats['equipment_count'] == 1
    assert elec_stats['total_work_orders'] == 8
    assert elec_stats['mean_frequency'] == 1.5
    assert elec_stats['median_frequency'] == 1.5


def test_calculate_category_statistics_std_dev():
    """Test standard deviation calculation in category statistics."""
    # Create data with known variance
    freq_data = {
        'Equipment_ID': ['EQ001', 'EQ002', 'EQ003'],
        'equipment_primary_category': ['HVAC', 'HVAC', 'HVAC'],
        'total_work_orders': [10, 10, 10],
        'work_orders_per_month': [1.0, 2.0, 3.0]  # Mean=2.0, std≈0.816
    }
    freq_df = pd.DataFrame(freq_data)

    result = calculate_category_statistics(freq_df)

    assert len(result) == 1
    hvac_stats = result.iloc[0]

    assert hvac_stats['mean_frequency'] == 2.0
    # Standard deviation of [1.0, 2.0, 3.0] with ddof=1
    assert abs(hvac_stats['std_frequency'] - 1.0) < 0.01


def test_calculate_equipment_frequencies_no_valid_completion():
    """Test equipment with no valid completion dates."""
    data = {
        'Equipment_ID': ['EQ005'],
        'equipment_primary_category': ['Other'],
        'Create_Date': [datetime(2024, 1, 1)],
        'Complete_Date': [pd.NaT],
        'PO_AMOUNT': [100.0]
    }
    df = pd.DataFrame(data)

    result = calculate_equipment_frequencies(df)

    assert len(result) == 1
    # avg_completion_days should be None when no valid completion dates
    assert pd.isna(result.iloc[0]['avg_completion_days'])


def test_calculate_equipment_frequencies_no_valid_costs():
    """Test equipment with only zero/negative costs."""
    data = {
        'Equipment_ID': ['EQ006'],
        'equipment_primary_category': ['Other'],
        'Create_Date': [datetime(2024, 1, 1)],
        'Complete_Date': [datetime(2024, 1, 2)],
        'PO_AMOUNT': [0.0]
    }
    df = pd.DataFrame(data)

    result = calculate_equipment_frequencies(df)

    assert len(result) == 1
    # avg_cost should be None when no positive costs
    assert pd.isna(result.iloc[0]['avg_cost'])
