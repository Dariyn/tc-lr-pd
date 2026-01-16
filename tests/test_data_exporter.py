"""
Comprehensive test suite for data export functionality.

Tests CSV and JSON export methods for all analysis types with edge cases.
"""

import pytest
import pandas as pd
import json
import os
from pathlib import Path
from src.exports.data_exporter import DataExporter


# Fixtures for sample data
@pytest.fixture
def sample_equipment_df():
    """Sample equipment ranking DataFrame."""
    return pd.DataFrame({
        'Equipment_Name': ['Chiller A', 'Elevator B', 'HVAC C'],
        'equipment_primary_category': ['HVAC', 'Vertical Transport', 'HVAC'],
        'work_orders_per_month': [5.2, 3.1, 2.8],
        'avg_cost': [15000.50, 8000.25, 12000.75],
        'cost_impact': [78002.60, 24800.78, 33602.10],
        'priority_score': [0.95, 0.72, 0.68],
        'overall_rank': [1, 2, 3]
    })


@pytest.fixture
def sample_seasonal_dict():
    """Sample seasonal patterns dictionary."""
    monthly_df = pd.DataFrame({
        'period': ['January', 'February', 'March'],
        'total_cost': [50000, 45000, 60000],
        'work_order_count': [25, 22, 30],
        'avg_cost': [2000, 2045, 2000]
    })
    return {
        'monthly_costs': monthly_df,
        'quarterly_costs': pd.DataFrame({
            'period': ['Q1', 'Q2'],
            'total_cost': [155000, 120000],
            'work_order_count': [77, 60],
            'avg_cost': [2013, 2000]
        }),
        'patterns': [
            {'pattern': 'High costs in March', 'confidence': 'high'}
        ]
    }


@pytest.fixture
def sample_vendor_df():
    """Sample vendor metrics DataFrame."""
    return pd.DataFrame({
        'contractor': ['ABC Contractors', 'XYZ Services', 'Best Maintenance'],
        'total_cost': [150000, 120000, 95000],
        'work_order_count': [45, 38, 30],
        'avg_cost_per_wo': [3333.33, 3157.89, 3166.67]
    })


@pytest.fixture
def sample_patterns_list():
    """Sample failure patterns list."""
    return [
        {
            'pattern': 'water leak',
            'occurrences': 15,
            'total_cost': 45000,
            'avg_cost': 3000,
            'equipment_affected': 8,
            'category': 'leak',
            'impact_score': 120.5
        },
        {
            'pattern': 'motor failure',
            'occurrences': 10,
            'total_cost': 35000,
            'avg_cost': 3500,
            'equipment_affected': 5,
            'category': 'motor',
            'impact_score': 87.5
        }
    ]


# CSV Export Tests
def test_export_equipment_rankings_csv(sample_equipment_df, tmp_path):
    """Test CSV export for equipment rankings."""
    exporter = DataExporter()
    output_file = tmp_path / "equipment.csv"

    exporter.export_equipment_rankings(sample_equipment_df, output_file)

    # Verify file exists
    assert output_file.exists()

    # Read back and verify
    result_df = pd.read_csv(output_file)
    assert len(result_df) == 3
    assert 'Equipment_Name' in result_df.columns
    assert 'priority_score' in result_df.columns

    # Verify sorting by priority_score descending
    assert result_df.iloc[0]['Equipment_Name'] == 'Chiller A'
    assert result_df.iloc[0]['priority_score'] == 0.95


def test_export_seasonal_patterns_csv(sample_seasonal_dict, tmp_path):
    """Test CSV export for seasonal patterns."""
    exporter = DataExporter()
    output_file = tmp_path / "seasonal.csv"

    exporter.export_seasonal_patterns(sample_seasonal_dict, output_file)

    # Verify file exists
    assert output_file.exists()

    # Read back and verify
    result_df = pd.read_csv(output_file)
    assert len(result_df) == 3  # Monthly data has 3 rows
    assert 'period' in result_df.columns
    assert 'total_cost' in result_df.columns
    assert result_df.iloc[0]['period'] == 'January'


def test_export_vendor_metrics_csv(sample_vendor_df, tmp_path):
    """Test CSV export for vendor metrics."""
    exporter = DataExporter()
    output_file = tmp_path / "vendors.csv"

    exporter.export_vendor_metrics(sample_vendor_df, output_file)

    # Verify file exists
    assert output_file.exists()

    # Read back and verify
    result_df = pd.read_csv(output_file)
    assert len(result_df) == 3
    assert 'contractor' in result_df.columns
    assert 'total_cost' in result_df.columns

    # Verify sorting by total_cost descending
    assert result_df.iloc[0]['contractor'] == 'ABC Contractors'
    assert result_df.iloc[0]['total_cost'] == 150000


def test_export_failure_patterns_csv(sample_patterns_list, tmp_path):
    """Test CSV export for failure patterns."""
    exporter = DataExporter()
    output_file = tmp_path / "patterns.csv"

    exporter.export_failure_patterns(sample_patterns_list, output_file)

    # Verify file exists
    assert output_file.exists()

    # Read back and verify
    result_df = pd.read_csv(output_file)
    assert len(result_df) == 2
    assert 'pattern' in result_df.columns
    assert 'frequency' in result_df.columns  # Mapped from occurrences
    assert 'equipment_count' in result_df.columns  # Mapped from equipment_affected


def test_csv_empty_dataframe(tmp_path):
    """Test CSV export handles empty DataFrame gracefully."""
    exporter = DataExporter()
    output_file = tmp_path / "empty.csv"

    empty_df = pd.DataFrame()
    exporter.export_equipment_rankings(empty_df, output_file)

    # Should create file with headers
    assert output_file.exists()
    result_df = pd.read_csv(output_file)
    assert len(result_df) == 0
    assert 'Equipment_Name' in result_df.columns


def test_csv_missing_columns(tmp_path):
    """Test CSV export handles DataFrame with missing columns."""
    exporter = DataExporter()
    output_file = tmp_path / "incomplete.csv"

    # DataFrame with only some columns
    incomplete_df = pd.DataFrame({
        'Equipment_Name': ['Equipment A'],
        'avg_cost': [5000]
    })

    exporter.export_equipment_rankings(incomplete_df, output_file)

    # Should still export successfully
    assert output_file.exists()
    result_df = pd.read_csv(output_file)
    assert 'Equipment_Name' in result_df.columns
    assert 'avg_cost' in result_df.columns


def test_csv_special_characters(tmp_path):
    """Test CSV export handles equipment names with commas and quotes."""
    exporter = DataExporter()
    output_file = tmp_path / "special_chars.csv"

    special_df = pd.DataFrame({
        'Equipment_Name': ['Chiller, Unit "A"', 'Elevator (Main)', 'HVAC-1'],
        'equipment_primary_category': ['HVAC', 'Vertical Transport', 'HVAC'],
        'priority_score': [0.95, 0.85, 0.75],
        'overall_rank': [1, 2, 3]
    })

    exporter.export_equipment_rankings(special_df, output_file)

    # Read back and verify special characters preserved
    result_df = pd.read_csv(output_file)
    assert result_df.iloc[0]['Equipment_Name'] == 'Chiller, Unit "A"'
    assert result_df.iloc[1]['Equipment_Name'] == 'Elevator (Main)'


def test_csv_file_creation(tmp_path):
    """Test CSV files are created at correct paths."""
    exporter = DataExporter()

    # Test with nested directory
    nested_dir = tmp_path / "exports" / "csv"
    nested_dir.mkdir(parents=True)
    output_file = nested_dir / "test.csv"

    df = pd.DataFrame({'Equipment_Name': ['Test'], 'priority_score': [0.9]})
    exporter.export_equipment_rankings(df, output_file)

    assert output_file.exists()
    assert output_file.parent == nested_dir


def test_csv_roundtrip(sample_equipment_df, tmp_path):
    """Test CSV export and re-import preserves data integrity."""
    exporter = DataExporter()
    output_file = tmp_path / "roundtrip.csv"

    exporter.export_equipment_rankings(sample_equipment_df, output_file)

    # Read back
    result_df = pd.read_csv(output_file)

    # Compare data (allowing for floating point precision)
    assert len(result_df) == len(sample_equipment_df)
    assert list(result_df['Equipment_Name']) == list(sample_equipment_df['Equipment_Name'])
    assert abs(result_df.iloc[0]['priority_score'] - 0.95) < 0.001


def test_csv_no_index(sample_equipment_df, tmp_path):
    """Test CSV export does not include index column."""
    exporter = DataExporter()
    output_file = tmp_path / "no_index.csv"

    exporter.export_equipment_rankings(sample_equipment_df, output_file)

    # Read raw CSV content
    with open(output_file, 'r') as f:
        first_line = f.readline().strip()

    # First line should be headers, not starting with index
    assert not first_line.startswith('0,')
    assert first_line.startswith('Equipment_Name')
