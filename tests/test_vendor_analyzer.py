"""
Tests for vendor/contractor cost performance analysis.

Validates vendor aggregation, cost metrics, efficiency calculations,
quality indicators, and recommendation generation.
"""

import pytest
import pandas as pd
from datetime import datetime, timedelta
from src.analysis.vendor_analyzer import VendorAnalyzer


@pytest.fixture
def sample_work_orders():
    """Create sample work order data for testing."""
    start_date = datetime(2024, 1, 1)
    data = {
        'Contractor': [
            'ABC Corp', 'ABC Corp', 'ABC Corp', 'ABC Corp',
            'XYZ Inc', 'XYZ Inc', 'XYZ Inc',
            'Quick Fix', 'Quick Fix', 'Quick Fix',
            None, None  # Unknown contractor
        ],
        'Equipment_ID': [
            'EQ001', 'EQ002', 'EQ003', 'EQ001',  # ABC: EQ001 appears twice
            'EQ004', 'EQ005', 'EQ006',            # XYZ: all unique
            'EQ007', 'EQ008', 'EQ007',            # Quick Fix: EQ007 appears twice
            'EQ009', 'EQ010'                      # Unknown
        ],
        'PO_AMOUNT': [
            1000.0, 1500.0, 2000.0, 1200.0,       # ABC: total 5700, avg 1425
            500.0, 600.0, 700.0,                  # XYZ: total 1800, avg 600
            800.0, 900.0, 850.0,                  # Quick Fix: total 2550, avg 850
            100.0, 200.0                          # Unknown
        ],
        'Create_Date': [
            start_date, start_date + timedelta(days=5), start_date + timedelta(days=10), start_date + timedelta(days=15),
            start_date, start_date + timedelta(days=10), start_date + timedelta(days=20),
            start_date, start_date + timedelta(days=2), start_date + timedelta(days=4),
            start_date, start_date + timedelta(days=5)
        ],
        'Complete_Date': [
            start_date + timedelta(days=5), start_date + timedelta(days=10), start_date + timedelta(days=20), start_date + timedelta(days=17),
            start_date + timedelta(days=3), start_date + timedelta(days=13), start_date + timedelta(days=25),
            start_date + timedelta(days=1), start_date + timedelta(days=3), start_date + timedelta(days=5),
            start_date + timedelta(days=2), start_date + timedelta(days=7)
        ]
    }
    return pd.DataFrame(data)


def test_calculate_vendor_costs_basic(sample_work_orders):
    """Test basic vendor cost aggregation."""
    analyzer = VendorAnalyzer(min_work_orders=3)
    result = analyzer.calculate_vendor_costs(sample_work_orders)

    assert len(result) == 3  # ABC, XYZ, Quick Fix (Unknown excluded by default)

    # Check ABC Corp (highest total cost)
    abc_row = result[result['contractor'] == 'ABC Corp'].iloc[0]
    assert abc_row['total_cost'] == 5700.0
    assert abc_row['work_order_count'] == 4
    assert abc_row['avg_cost_per_wo'] == 1425.0

    # Check XYZ Inc
    xyz_row = result[result['contractor'] == 'XYZ Inc'].iloc[0]
    assert xyz_row['total_cost'] == 1800.0
    assert xyz_row['work_order_count'] == 3
    assert xyz_row['avg_cost_per_wo'] == 600.0

    # Check Quick Fix
    qf_row = result[result['contractor'] == 'Quick Fix'].iloc[0]
    assert qf_row['total_cost'] == 2550.0
    assert qf_row['work_order_count'] == 3
    assert qf_row['avg_cost_per_wo'] == 850.0


def test_calculate_vendor_costs_include_unknown(sample_work_orders):
    """Test including unknown contractors."""
    analyzer = VendorAnalyzer(min_work_orders=2)
    result = analyzer.calculate_vendor_costs(sample_work_orders, include_unknown=True)

    assert len(result) == 4  # ABC, XYZ, Quick Fix, Unknown

    unknown_row = result[result['contractor'] == 'Unknown'].iloc[0]
    assert unknown_row['total_cost'] == 300.0
    assert unknown_row['work_order_count'] == 2


def test_calculate_vendor_costs_min_threshold():
    """Test minimum work order threshold filtering."""
    data = {
        'Contractor': ['Vendor A', 'Vendor A', 'Vendor B'],
        'PO_AMOUNT': [100.0, 200.0, 150.0],
        'Create_Date': [datetime(2024, 1, 1)] * 3,
        'Complete_Date': [datetime(2024, 1, 2)] * 3,
        'Equipment_ID': ['EQ1', 'EQ2', 'EQ3']
    }
    df = pd.DataFrame(data)

    # With min_work_orders=3, only no vendors should appear
    analyzer = VendorAnalyzer(min_work_orders=3)
    result = analyzer.calculate_vendor_costs(df)
    assert len(result) == 0

    # With min_work_orders=2, Vendor A should appear
    analyzer = VendorAnalyzer(min_work_orders=2)
    result = analyzer.calculate_vendor_costs(df)
    assert len(result) == 1
    assert result.iloc[0]['contractor'] == 'Vendor A'


def test_calculate_vendor_duration(sample_work_orders):
    """Test average duration calculation by vendor."""
    analyzer = VendorAnalyzer(min_work_orders=3)
    result = analyzer.calculate_vendor_duration(sample_work_orders)

    assert len(result) == 3

    # ABC Corp: (5 + 5 + 10 + 2) / 4 = 5.5 days
    abc_row = result[result['contractor'] == 'ABC Corp'].iloc[0]
    assert abc_row['avg_duration_days'] == 5.5

    # XYZ Inc: (3 + 3 + 5) / 3 = 3.67 days
    xyz_row = result[result['contractor'] == 'XYZ Inc'].iloc[0]
    assert abs(xyz_row['avg_duration_days'] - 3.667) < 0.01

    # Quick Fix: (1 + 1 + 1) / 3 = 1.0 days
    qf_row = result[result['contractor'] == 'Quick Fix'].iloc[0]
    assert qf_row['avg_duration_days'] == 1.0


def test_calculate_vendor_duration_missing_dates():
    """Test handling of missing Complete_Date values."""
    data = {
        'Contractor': ['Vendor A', 'Vendor A', 'Vendor A', 'Vendor A'],
        'PO_AMOUNT': [100.0, 200.0, 150.0, 175.0],
        'Equipment_ID': ['EQ1', 'EQ2', 'EQ3', 'EQ4'],
        'Create_Date': [
            datetime(2024, 1, 1),
            datetime(2024, 1, 5),
            datetime(2024, 1, 10),
            datetime(2024, 1, 15)
        ],
        'Complete_Date': [
            datetime(2024, 1, 3),  # 2 days
            pd.NaT,                 # Missing
            datetime(2024, 1, 14),  # 4 days
            pd.NaT                  # Missing
        ]
    }
    df = pd.DataFrame(data)

    analyzer = VendorAnalyzer(min_work_orders=2)
    result = analyzer.calculate_vendor_duration(df)

    # Should only count the 2 valid durations: (2 + 4) / 2 = 3 days
    assert len(result) == 1
    assert result.iloc[0]['work_order_count'] == 2
    assert result.iloc[0]['avg_duration_days'] == 3.0


def test_rank_vendors_by_total_cost(sample_work_orders):
    """Test vendor ranking by total cost."""
    analyzer = VendorAnalyzer(min_work_orders=3)
    result = analyzer.rank_vendors(sample_work_orders, by='total_cost')

    assert len(result) == 3

    # Check ranking order (highest cost = rank 1)
    assert result.iloc[0]['contractor'] == 'ABC Corp'
    assert result.iloc[0]['rank'] == 1
    assert result.iloc[1]['contractor'] == 'Quick Fix'
    assert result.iloc[1]['rank'] == 2
    assert result.iloc[2]['contractor'] == 'XYZ Inc'
    assert result.iloc[2]['rank'] == 3

    # Check all columns present
    assert 'total_cost' in result.columns
    assert 'work_order_count' in result.columns
    assert 'avg_cost_per_wo' in result.columns
    assert 'avg_duration_days' in result.columns


def test_rank_vendors_by_avg_cost(sample_work_orders):
    """Test vendor ranking by average cost."""
    analyzer = VendorAnalyzer(min_work_orders=3)
    result = analyzer.rank_vendors(sample_work_orders, by='avg_cost')

    # Ranking by avg_cost: ABC (1425) > Quick Fix (850) > XYZ (600)
    assert result.iloc[0]['contractor'] == 'ABC Corp'
    assert result.iloc[0]['rank'] == 1
    assert result.iloc[1]['contractor'] == 'Quick Fix'
    assert result.iloc[1]['rank'] == 2
    assert result.iloc[2]['contractor'] == 'XYZ Inc'
    assert result.iloc[2]['rank'] == 3


def test_rank_vendors_by_work_order_count(sample_work_orders):
    """Test vendor ranking by work order count."""
    analyzer = VendorAnalyzer(min_work_orders=3)
    result = analyzer.rank_vendors(sample_work_orders, by='work_order_count')

    # Ranking by count: ABC (4) > XYZ (3) = Quick Fix (3)
    assert result.iloc[0]['contractor'] == 'ABC Corp'
    assert result.iloc[0]['rank'] == 1


def test_identify_high_cost_vendors_75th_percentile(sample_work_orders):
    """Test identifying high-cost vendors using 75th percentile."""
    analyzer = VendorAnalyzer(min_work_orders=3)
    result = analyzer.identify_high_cost_vendors(sample_work_orders, threshold='75th_percentile')

    # 75th percentile of [1800, 2550, 5700] = 4125
    # Only ABC (5700) should be above this
    assert len(result) >= 1
    assert 'ABC Corp' in result['contractor'].values
    assert 'cost_threshold' in result.columns


def test_identify_high_cost_vendors_90th_percentile(sample_work_orders):
    """Test identifying high-cost vendors using 90th percentile."""
    analyzer = VendorAnalyzer(min_work_orders=3)
    result = analyzer.identify_high_cost_vendors(sample_work_orders, threshold='90th_percentile')

    # 90th percentile should be higher, may include only ABC
    assert len(result) >= 1
    assert all(row['total_cost'] >= row['cost_threshold'] for _, row in result.iterrows())


def test_identify_high_cost_vendors_top_10(sample_work_orders):
    """Test identifying top 10 vendors by cost."""
    analyzer = VendorAnalyzer(min_work_orders=3)
    result = analyzer.identify_high_cost_vendors(sample_work_orders, threshold='top_10')

    # We only have 3 vendors, so all should be included
    assert len(result) == 3
    assert set(result['contractor']) == {'ABC Corp', 'XYZ Inc', 'Quick Fix'}


def test_calculate_cost_efficiency(sample_work_orders):
    """Test cost efficiency calculation (cost per day)."""
    analyzer = VendorAnalyzer(min_work_orders=3)
    result = analyzer.calculate_cost_efficiency(sample_work_orders)

    assert len(result) == 3

    # Quick Fix: 850 / 1.0 = 850 cost per day (highest but fastest)
    # ABC Corp: 1425 / 5.5 = 259.09 cost per day
    # XYZ Inc: 600 / 3.67 = 163.52 cost per day (most efficient)

    # Should be sorted by cost_per_day ascending (lower = better)
    assert result.iloc[0]['contractor'] == 'XYZ Inc'
    assert abs(result.iloc[0]['cost_per_day'] - 163.52) < 1

    assert 'avg_cost_per_wo' in result.columns
    assert 'avg_duration_days' in result.columns
    assert 'cost_per_day' in result.columns


def test_calculate_cost_efficiency_zero_duration():
    """Test cost efficiency handles vendors without duration data."""
    data = {
        'Contractor': ['Vendor A', 'Vendor A', 'Vendor A'],
        'PO_AMOUNT': [100.0, 200.0, 150.0],
        'Equipment_ID': ['EQ1', 'EQ2', 'EQ3'],
        'Create_Date': [datetime(2024, 1, 1)] * 3,
        'Complete_Date': [pd.NaT, pd.NaT, pd.NaT]  # No valid dates
    }
    df = pd.DataFrame(data)

    analyzer = VendorAnalyzer(min_work_orders=3)
    result = analyzer.calculate_cost_efficiency(df)

    # Should return empty DataFrame (no duration data available)
    assert len(result) == 0


def test_calculate_quality_indicators(sample_work_orders):
    """Test quality indicator calculation based on repeat equipment."""
    analyzer = VendorAnalyzer(min_work_orders=3)
    result = analyzer.calculate_quality_indicators(sample_work_orders)

    assert len(result) == 3

    # ABC Corp: 4 WOs on equipment [EQ001, EQ002, EQ003, EQ001]
    # Unique: 3, Repeat: 1 (EQ001), Rate: 33.33%
    abc_row = result[result['contractor'] == 'ABC Corp'].iloc[0]
    assert abc_row['total_work_orders'] == 4
    assert abc_row['unique_equipment'] == 3
    assert abc_row['repeat_equipment_count'] == 1
    assert abs(abc_row['repeat_rate'] - 33.33) < 0.1

    # XYZ Inc: 3 WOs on equipment [EQ004, EQ005, EQ006]
    # Unique: 3, Repeat: 0, Rate: 0%
    xyz_row = result[result['contractor'] == 'XYZ Inc'].iloc[0]
    assert xyz_row['unique_equipment'] == 3
    assert xyz_row['repeat_equipment_count'] == 0
    assert xyz_row['repeat_rate'] == 0.0

    # Quick Fix: 3 WOs on equipment [EQ007, EQ008, EQ007]
    # Unique: 2, Repeat: 1 (EQ007), Rate: 50%
    qf_row = result[result['contractor'] == 'Quick Fix'].iloc[0]
    assert qf_row['unique_equipment'] == 2
    assert qf_row['repeat_equipment_count'] == 1
    assert qf_row['repeat_rate'] == 50.0


def test_calculate_quality_indicators_high_repeat():
    """Test quality indicators with high repeat rate."""
    data = {
        'Contractor': ['Vendor A'] * 5,
        'Equipment_ID': ['EQ1', 'EQ1', 'EQ1', 'EQ2', 'EQ2'],  # Both equipment have repeats
        'PO_AMOUNT': [100.0] * 5,
        'Create_Date': [datetime(2024, 1, 1)] * 5,
        'Complete_Date': [datetime(2024, 1, 2)] * 5
    }
    df = pd.DataFrame(data)

    analyzer = VendorAnalyzer(min_work_orders=3)
    result = analyzer.calculate_quality_indicators(df)

    assert len(result) == 1
    assert result.iloc[0]['unique_equipment'] == 2
    assert result.iloc[0]['repeat_equipment_count'] == 2
    assert result.iloc[0]['repeat_rate'] == 100.0  # Both equipment have repeats


def test_get_vendor_recommendations(sample_work_orders):
    """Test generation of vendor recommendations."""
    analyzer = VendorAnalyzer(min_work_orders=3)
    recommendations = analyzer.get_vendor_recommendations(sample_work_orders)

    # Should have recommendations
    assert len(recommendations) > 0

    # Check structure
    for rec in recommendations:
        assert 'vendor' in rec
        assert 'issue' in rec
        assert 'metric' in rec
        assert 'suggestion' in rec

    # Should include ABC Corp for high cost
    high_cost_recs = [r for r in recommendations if r['issue'] == 'High cost']
    assert any(r['vendor'] == 'ABC Corp' for r in high_cost_recs)


def test_get_vendor_recommendations_quality_concerns():
    """Test recommendations for quality concerns."""
    # Create data with high repeat rate (>50%)
    data = {
        'Contractor': ['Problem Vendor'] * 6 + ['Good Vendor'] * 3,
        'Equipment_ID': ['EQ1', 'EQ1', 'EQ2', 'EQ2', 'EQ3', 'EQ3'] + ['EQ4', 'EQ5', 'EQ6'],
        'PO_AMOUNT': [100.0] * 9,
        'Create_Date': [datetime(2024, 1, 1)] * 9,
        'Complete_Date': [datetime(2024, 1, 2)] * 9
    }
    df = pd.DataFrame(data)

    analyzer = VendorAnalyzer(min_work_orders=3)
    recommendations = analyzer.get_vendor_recommendations(df)

    # Should flag Problem Vendor for quality concerns (100% repeat rate)
    quality_recs = [r for r in recommendations if r['issue'] == 'Quality concerns']
    assert any(r['vendor'] == 'Problem Vendor' for r in quality_recs)


def test_get_vendor_recommendations_empty_data():
    """Test recommendations with empty or insufficient data."""
    data = {
        'Contractor': ['Vendor A', 'Vendor B'],
        'Equipment_ID': ['EQ1', 'EQ2'],
        'PO_AMOUNT': [100.0, 200.0],
        'Create_Date': [datetime(2024, 1, 1)] * 2,
        'Complete_Date': [datetime(2024, 1, 2)] * 2
    }
    df = pd.DataFrame(data)

    analyzer = VendorAnalyzer(min_work_orders=3)
    recommendations = analyzer.get_vendor_recommendations(df)

    # Should return empty list (no vendors meet minimum threshold)
    assert len(recommendations) == 0


def test_vendor_analyzer_custom_label():
    """Test custom unknown label."""
    data = {
        'Contractor': ['Vendor A', None, None, None],
        'Equipment_ID': ['EQ1', 'EQ2', 'EQ3', 'EQ4'],
        'PO_AMOUNT': [100.0, 200.0, 150.0, 175.0],
        'Create_Date': [datetime(2024, 1, 1)] * 4,
        'Complete_Date': [datetime(2024, 1, 2)] * 4
    }
    df = pd.DataFrame(data)

    analyzer = VendorAnalyzer(min_work_orders=3, unknown_label='N/A')
    result = analyzer.calculate_vendor_costs(df, include_unknown=True)

    assert len(result) == 1
    assert result.iloc[0]['contractor'] == 'N/A'
