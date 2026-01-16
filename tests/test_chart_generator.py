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
