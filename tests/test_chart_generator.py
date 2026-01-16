"""
Tests for chart generation functionality.

Tests cover all chart types (equipment, seasonal, vendor, failure) and
edge cases (empty data, missing fields, various formats).
"""

import pytest
import pandas as pd
from pathlib import Path
from src.visualization.chart_generator import ChartGenerator


@pytest.fixture
def sample_equipment_data():
    """Sample equipment ranking data."""
    return pd.DataFrame({
        'Equipment_ID': ['EQ-001', 'EQ-002', 'EQ-003', 'EQ-004', 'EQ-005'],
        'equipment_name': ['Chiller A', 'Boiler B', 'Pump C', 'HVAC Unit D', 'Elevator E'],
        'priority_score': [0.95, 0.87, 0.76, 0.68, 0.54],
        'work_order_count': [45, 38, 32, 28, 21],
        'equipment_primary_category': ['HVAC', 'Mechanical', 'Plumbing', 'HVAC', 'Elevator']
    })


@pytest.fixture
def sample_seasonal_data():
    """Sample seasonal trend data."""
    monthly_df = pd.DataFrame({
        'period': ['January', 'February', 'March', 'April', 'May', 'June'],
        'total_cost': [50000, 45000, 52000, 48000, 55000, 60000],
        'work_order_count': [120, 110, 125, 115, 130, 140]
    })
    return {'monthly': monthly_df}


@pytest.fixture
def sample_vendor_data():
    """Sample vendor performance data."""
    return pd.DataFrame({
        'contractor': ['Vendor A', 'Vendor B', 'Vendor C', 'Vendor D', 'Vendor E'],
        'total_cost': [150000, 120000, 95000, 80000, 65000],
        'avg_cost_per_wo': [2500, 2000, 1900, 1600, 1300],
        'cost_per_day': [500, 400, 380, 320, 260]
    })


@pytest.fixture
def chart_generator():
    """Chart generator instance."""
    return ChartGenerator(dpi=100)  # Lower DPI for faster tests


class TestEquipmentRankingChart:
    """Tests for equipment ranking chart generation."""

    def test_equipment_ranking_chart_png(self, chart_generator, sample_equipment_data, tmp_path):
        """Test creating equipment ranking chart in PNG format."""
        output_file = tmp_path / "equipment_ranking.png"

        chart_generator.create_equipment_ranking_chart(
            sample_equipment_data,
            output_file,
            top_n=5,
            format='png'
        )

        # Verify file exists and has content
        assert output_file.exists()
        assert output_file.stat().st_size > 0

        # Verify PNG magic bytes
        with open(output_file, 'rb') as f:
            assert f.read(8) == b'\x89PNG\r\n\x1a\n'

    def test_equipment_ranking_chart_svg(self, chart_generator, sample_equipment_data, tmp_path):
        """Test creating equipment ranking chart in SVG format."""
        output_file = tmp_path / "equipment_ranking.svg"

        chart_generator.create_equipment_ranking_chart(
            sample_equipment_data,
            output_file,
            top_n=5,
            format='svg'
        )

        # Verify file exists and has content
        assert output_file.exists()
        assert output_file.stat().st_size > 0

        # Verify SVG format
        with open(output_file, 'r', encoding='utf-8') as f:
            content = f.read()
            assert '<svg' in content or '<?xml' in content

    def test_equipment_chart_top_n(self, chart_generator, sample_equipment_data, tmp_path):
        """Test limiting to top N items."""
        output_file = tmp_path / "equipment_top3.png"

        chart_generator.create_equipment_ranking_chart(
            sample_equipment_data,
            output_file,
            top_n=3,
            format='png'
        )

        # Verify file created
        assert output_file.exists()
        assert output_file.stat().st_size > 0

    def test_equipment_chart_empty_data(self, chart_generator, tmp_path):
        """Test handling empty DataFrame."""
        output_file = tmp_path / "equipment_empty.png"
        empty_df = pd.DataFrame()

        chart_generator.create_equipment_ranking_chart(
            empty_df,
            output_file,
            format='png'
        )

        # Should create placeholder chart
        assert output_file.exists()
        assert output_file.stat().st_size > 0

    def test_equipment_chart_missing_columns(self, chart_generator, tmp_path):
        """Test handling missing required columns."""
        output_file = tmp_path / "equipment_missing.png"
        df = pd.DataFrame({
            'Equipment_ID': ['EQ-001', 'EQ-002'],
            # Missing priority_score
        })

        chart_generator.create_equipment_ranking_chart(
            df,
            output_file,
            format='png'
        )

        # Should create placeholder chart with error message
        assert output_file.exists()
        assert output_file.stat().st_size > 0


class TestSeasonalTrendChart:
    """Tests for seasonal trend chart generation."""

    def test_seasonal_trend_chart(self, chart_generator, sample_seasonal_data, tmp_path):
        """Test creating seasonal trend chart with dual y-axis."""
        output_file = tmp_path / "seasonal_trend.png"

        chart_generator.create_seasonal_trend_chart(
            sample_seasonal_data,
            output_file,
            format='png'
        )

        # Verify file exists and has content
        assert output_file.exists()
        assert output_file.stat().st_size > 0

    def test_seasonal_missing_months(self, chart_generator, tmp_path):
        """Test handling sparse seasonal data."""
        output_file = tmp_path / "seasonal_sparse.png"
        sparse_data = {
            'monthly': pd.DataFrame({
                'period': ['January', 'March', 'June'],
                'total_cost': [50000, 52000, 60000],
                'work_order_count': [120, 125, 140]
            })
        }

        chart_generator.create_seasonal_trend_chart(
            sparse_data,
            output_file,
            format='png'
        )

        # Should handle sparse data gracefully
        assert output_file.exists()
        assert output_file.stat().st_size > 0

    def test_seasonal_empty_data(self, chart_generator, tmp_path):
        """Test handling empty seasonal data."""
        output_file = tmp_path / "seasonal_empty.png"

        chart_generator.create_seasonal_trend_chart(
            {},
            output_file,
            format='png'
        )

        # Should create placeholder chart
        assert output_file.exists()
        assert output_file.stat().st_size > 0


class TestVendorPerformanceChart:
    """Tests for vendor performance chart generation."""

    def test_vendor_performance_chart(self, chart_generator, sample_vendor_data, tmp_path):
        """Test creating vendor performance chart with grouped bars."""
        output_file = tmp_path / "vendor_performance.png"

        chart_generator.create_vendor_performance_chart(
            sample_vendor_data,
            output_file,
            top_n=5,
            format='png'
        )

        # Verify file exists and has content
        assert output_file.exists()
        assert output_file.stat().st_size > 0

    def test_vendor_single_vendor(self, chart_generator, tmp_path):
        """Test handling single vendor edge case."""
        output_file = tmp_path / "vendor_single.png"
        single_vendor_df = pd.DataFrame({
            'contractor': ['Vendor A'],
            'total_cost': [150000],
            'avg_cost_per_wo': [2500]
        })

        chart_generator.create_vendor_performance_chart(
            single_vendor_df,
            output_file,
            format='png'
        )

        # Should handle single vendor gracefully
        assert output_file.exists()
        assert output_file.stat().st_size > 0

    def test_vendor_empty_data(self, chart_generator, tmp_path):
        """Test handling empty vendor data."""
        output_file = tmp_path / "vendor_empty.png"
        empty_df = pd.DataFrame()

        chart_generator.create_vendor_performance_chart(
            empty_df,
            output_file,
            format='png'
        )

        # Should create placeholder chart
        assert output_file.exists()
        assert output_file.stat().st_size > 0
