"""
Tests for data_cleaner module.

Tests cover equipment cleaning, cost cleaning, and date cleaning logic.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytest

from src.pipeline.data_cleaner import (
    clean_equipment_data,
    clean_cost_data,
    clean_date_data,
    clean_work_orders
)


def test_clean_equipment_data_drops_null_equipment():
    """Test that rows with no equipment info are dropped."""
    df = pd.DataFrame({
        'Equipment_ID': [1.0, np.nan, np.nan, 4.0],
        'EquipmentName': ['Equipment A', 'Equipment B', np.nan, 'Equipment D']
    })

    result = clean_equipment_data(df)

    # Should drop row 2 (index 2) with both ID and Name null
    assert len(result) == 3
    assert 2 not in result.index


def test_clean_equipment_data_handles_partial_info():
    """Test that synthetic IDs and names are created for partial info."""
    df = pd.DataFrame({
        'Equipment_ID': [1.0, np.nan, 3.0, np.nan],
        'EquipmentName': ['Equipment A', 'Equipment B', np.nan, 'Equipment D']
    })

    result = clean_equipment_data(df)

    # Row with ID but no name should get synthetic name
    assert 'Unknown Equipment' in result.loc[2, 'EquipmentName']

    # Rows with name but no ID should get synthetic ID (hash-based)
    assert pd.notna(result.loc[1, 'Equipment_ID'])
    assert pd.notna(result.loc[3, 'Equipment_ID'])

    # All rows should have both ID and Name
    assert result['Equipment_ID'].notna().all()
    assert result['EquipmentName'].notna().all()


def test_clean_cost_data_fills_missing():
    """Test that missing costs are filled with 0."""
    df = pd.DataFrame({
        'PO_AMOUNT': [100.0, np.nan, 200.0, np.nan]
    })

    result = clean_cost_data(df)

    # Missing values should be filled with 0
    assert result['PO_AMOUNT'].isna().sum() == 0
    assert result.loc[1, 'PO_AMOUNT'] == 0
    assert result.loc[3, 'PO_AMOUNT'] == 0


def test_clean_cost_data_removes_negatives():
    """Test that negative costs are replaced with 0."""
    df = pd.DataFrame({
        'PO_AMOUNT': [100.0, -50.0, 200.0, -10.0]
    })

    result = clean_cost_data(df)

    # Negative values should be replaced with 0
    assert (result['PO_AMOUNT'] >= 0).all()
    assert result.loc[1, 'PO_AMOUNT'] == 0
    assert result.loc[3, 'PO_AMOUNT'] == 0


def test_clean_cost_data_flags_outliers():
    """Test that cost outliers are flagged correctly."""
    # Create data with clear outlier (value 1000 is > 99th percentile)
    costs = [10.0] * 98 + [20.0, 1000.0]
    df = pd.DataFrame({'PO_AMOUNT': costs})

    result = clean_cost_data(df)

    # Should have cost_outlier column
    assert 'cost_outlier' in result.columns

    # The 1000.0 value should be flagged as outlier
    assert result.loc[99, 'cost_outlier'] == True

    # Most other values should not be flagged
    assert result['cost_outlier'].sum() <= 2  # At most 1-2 outliers


def test_clean_date_data_drops_missing_create():
    """Test that rows without Create_Date are dropped."""
    df = pd.DataFrame({
        'Create_Date': [
            pd.Timestamp('2024-01-01'),
            pd.NaT,
            pd.Timestamp('2024-01-03'),
            pd.NaT
        ],
        'Complete_Date': [
            pd.Timestamp('2024-01-02'),
            pd.Timestamp('2024-01-05'),
            pd.Timestamp('2024-01-04'),
            pd.NaT
        ],
        'Status_Eng': ['Closed', 'Closed', 'Closed', 'Open'],
        'Close_Date': [
            pd.Timestamp('2024-01-02'),
            pd.Timestamp('2024-01-05'),
            pd.Timestamp('2024-01-04'),
            pd.NaT
        ]
    })

    result = clean_date_data(df)

    # Rows with missing Create_Date should be dropped
    assert len(result) == 2
    assert 1 not in result.index
    assert 3 not in result.index


def test_clean_date_data_calculates_duration():
    """Test that duration_hours is calculated correctly."""
    df = pd.DataFrame({
        'Create_Date': [
            pd.Timestamp('2024-01-01 10:00:00'),
            pd.Timestamp('2024-01-02 08:00:00'),
            pd.Timestamp('2024-01-03 14:00:00')
        ],
        'Complete_Date': [
            pd.Timestamp('2024-01-01 14:00:00'),  # 4 hours
            pd.Timestamp('2024-01-02 10:00:00'),  # 2 hours
            pd.NaT  # Not completed
        ],
        'Status_Eng': ['Closed', 'Closed', 'Open'],
        'Close_Date': [pd.NaT, pd.NaT, pd.NaT]
    })

    result = clean_date_data(df)

    # Should have duration_hours column
    assert 'duration_hours' in result.columns

    # Check calculated durations
    assert result.loc[0, 'duration_hours'] == 4.0
    assert result.loc[1, 'duration_hours'] == 2.0
    assert pd.isna(result.loc[2, 'duration_hours'])


def test_clean_date_data_uses_close_date_when_needed():
    """Test that Close_Date is used when Complete_Date is missing for closed work orders."""
    df = pd.DataFrame({
        'Create_Date': [
            pd.Timestamp('2024-01-01'),
            pd.Timestamp('2024-01-02')
        ],
        'Complete_Date': [pd.NaT, pd.NaT],
        'Status_Eng': ['Closed', 'Open'],
        'Close_Date': [
            pd.Timestamp('2024-01-03'),
            pd.Timestamp('2024-01-05')
        ]
    })

    result = clean_date_data(df)

    # For closed work order with missing Complete_Date, should use Close_Date
    assert pd.notna(result.loc[0, 'Complete_Date'])
    assert result.loc[0, 'Complete_Date'] == pd.Timestamp('2024-01-03')

    # For open work order, Complete_Date should remain NaT
    assert pd.isna(result.loc[1, 'Complete_Date'])


def test_clean_work_orders_integration():
    """Test full cleaning pipeline integration."""
    df = pd.DataFrame({
        'Equipment_ID': [1.0, np.nan, 3.0, np.nan],
        'EquipmentName': ['Pump A', 'Pump B', np.nan, np.nan],
        'PO_AMOUNT': [100.0, np.nan, -50.0, 200.0],
        'Create_Date': [
            pd.Timestamp('2024-01-01'),
            pd.Timestamp('2024-01-02'),
            pd.Timestamp('2024-01-03'),
            pd.NaT  # This row will be dropped
        ],
        'Complete_Date': [
            pd.Timestamp('2024-01-02'),
            pd.Timestamp('2024-01-03'),
            pd.Timestamp('2024-01-04'),
            pd.NaT
        ],
        'Status_Eng': ['Closed', 'Closed', 'Closed', 'Open'],
        'Close_Date': [pd.NaT, pd.NaT, pd.NaT, pd.NaT]
    })

    result = clean_work_orders(df)

    # Row with both Equipment_ID and EquipmentName null should be dropped (row 3)
    # Row with missing Create_Date should be dropped (row 3 - same row)
    # So we should have 3 rows remaining
    assert len(result) == 3

    # Should have all required columns
    assert 'cost_outlier' in result.columns
    assert 'duration_outlier' in result.columns
    assert 'duration_hours' in result.columns

    # Equipment data should be cleaned
    assert result['Equipment_ID'].notna().all()
    assert result['EquipmentName'].notna().all()

    # Cost data should be cleaned
    assert (result['PO_AMOUNT'] >= 0).all()

    # Duration should be calculated where possible
    assert result['duration_hours'].notna().sum() >= 1
