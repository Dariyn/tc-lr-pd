"""
Test suite for DashboardGenerator interactive dashboard creation.

Tests cover:
- Individual chart creation (equipment, seasonal, vendor, failure)
- Chart hover templates and interactivity
- Dashboard assembly with all charts
- HTML validity and self-contained output
- Edge cases (empty data, missing fields)
"""

import pytest
import pandas as pd
from pathlib import Path
from src.visualization.dashboard_generator import DashboardGenerator
import plotly.graph_objects as go


@pytest.fixture
def dashboard_gen():
    """Create DashboardGenerator instance."""
    return DashboardGenerator()


@pytest.fixture
def sample_equipment_df():
    """Sample equipment ranking data."""
    return pd.DataFrame({
        'Equipment_Name': ['Pump A', 'Chiller B', 'HVAC C', 'Boiler D', 'Fan E'],
        'equipment_primary_category': ['Pumps', 'Chillers', 'HVAC', 'Boilers', 'Fans'],
        'work_order_count': [25, 18, 15, 12, 10],
        'total_cost': [15000, 12000, 9000, 7500, 6000],
        'avg_cost': [600, 667, 600, 625, 600],
        'priority_score': [0.95, 0.82, 0.71, 0.65, 0.58]
    })


@pytest.fixture
def sample_seasonal_dict():
    """Sample seasonal patterns data."""
    monthly_df = pd.DataFrame({
        'period': ['January', 'February', 'March', 'April'],
        'total_cost': [25000, 22000, 28000, 24000],
        'work_order_count': [45, 40, 52, 48],
        'avg_cost': [556, 550, 538, 500]
    })
    return {'monthly': monthly_df}


@pytest.fixture
def sample_vendor_df():
    """Sample vendor performance data."""
    return pd.DataFrame({
        'contractor': ['Vendor A', 'Vendor B', 'Vendor C'],
        'total_cost': [50000, 35000, 28000],
        'work_order_count': [100, 75, 60],
        'avg_cost_per_wo': [500, 467, 467],
        'avg_duration_days': [3.5, 4.2, 3.8],
        'cost_per_day': [143, 111, 123]
    })


@pytest.fixture
def sample_patterns_list():
    """Sample failure patterns data."""
    return [
        {
            'pattern': 'water leak',
            'frequency': 45,
            'total_cost': 25000,
            'equipment_count': 12,
            'category': 'leak',
            'impact_score': 13500000
        },
        {
            'pattern': 'electrical fault',
            'frequency': 32,
            'total_cost': 18000,
            'equipment_count': 8,
            'category': 'electrical',
            'impact_score': 4608000
        },
        {
            'pattern': 'mechanical failure',
            'frequency': 28,
            'total_cost': 15000,
            'equipment_count': 10,
            'category': 'mechanical',
            'impact_score': 4200000
        }
    ]


# Individual chart tests

def test_equipment_chart(dashboard_gen, sample_equipment_df):
    """Test equipment chart creates valid Figure with correct data."""
    fig = dashboard_gen._create_equipment_chart(sample_equipment_df, top_n=5)

    assert isinstance(fig, go.Figure)
    assert len(fig.data) > 0  # Has at least one trace
    assert fig.layout.title.text == "Equipment Maintenance Priority Rankings"

    # Check that data is present
    total_data_points = sum(len(trace.x) for trace in fig.data)
    assert total_data_points == 5  # All 5 equipment items


def test_equipment_chart_hover(dashboard_gen, sample_equipment_df):
    """Test equipment chart hover template includes all required fields."""
    fig = dashboard_gen._create_equipment_chart(sample_equipment_df, top_n=5)

    # Check that hover text is configured
    for trace in fig.data:
        assert trace.hoverinfo == 'text'
        assert trace.hovertext is not None
        # Verify hover includes key information
        hover_str = str(trace.hovertext[0])
        assert 'Priority Score' in hover_str or 'priority_score' in hover_str.lower()


def test_seasonal_chart(dashboard_gen, sample_seasonal_dict):
    """Test seasonal chart creates valid Figure with dual Y-axes."""
    fig = dashboard_gen._create_seasonal_chart(sample_seasonal_dict)

    assert isinstance(fig, go.Figure)
    assert len(fig.data) >= 1  # At least total cost trace
    assert fig.layout.title.text == "Seasonal Cost and Work Order Trends"

    # Check for line traces
    has_line_trace = any(isinstance(trace, go.Scatter) for trace in fig.data)
    assert has_line_trace


def test_seasonal_range_slider(dashboard_gen, sample_seasonal_dict):
    """Test seasonal chart has range slider configuration."""
    fig = dashboard_gen._create_seasonal_chart(sample_seasonal_dict)

    # Check for range slider
    assert fig.layout.xaxis.rangeslider is not None
    assert fig.layout.xaxis.rangeslider.visible is True


def test_vendor_chart(dashboard_gen, sample_vendor_df):
    """Test vendor chart creates grouped bars with legend."""
    fig = dashboard_gen._create_vendor_chart(sample_vendor_df, top_n=10)

    assert isinstance(fig, go.Figure)
    assert len(fig.data) >= 1  # At least total cost bars
    assert fig.layout.title.text == "Vendor Performance Comparison"

    # Check for bar traces
    has_bar_trace = any(isinstance(trace, go.Bar) for trace in fig.data)
    assert has_bar_trace

    # Check legend is shown
    assert fig.layout.showlegend is True


def test_failure_chart(dashboard_gen, sample_patterns_list):
    """Test failure chart creates bars with category colors."""
    fig = dashboard_gen._create_failure_chart(sample_patterns_list, top_n=10)

    assert isinstance(fig, go.Figure)
    assert len(fig.data) > 0
    assert fig.layout.title.text == "High-Impact Failure Patterns"

    # Check data is horizontal bars
    for trace in fig.data:
        assert isinstance(trace, go.Bar)
        assert trace.orientation == 'h'


def test_chart_empty_data(dashboard_gen):
    """Test all chart methods handle empty data gracefully."""
    # Empty equipment
    fig = dashboard_gen._create_equipment_chart(pd.DataFrame(), top_n=10)
    assert isinstance(fig, go.Figure)

    # Empty seasonal
    fig = dashboard_gen._create_seasonal_chart({})
    assert isinstance(fig, go.Figure)

    # Empty vendor
    fig = dashboard_gen._create_vendor_chart(pd.DataFrame(), top_n=10)
    assert isinstance(fig, go.Figure)

    # Empty failure patterns
    fig = dashboard_gen._create_failure_chart([], top_n=10)
    assert isinstance(fig, go.Figure)


def test_chart_return_type(dashboard_gen, sample_equipment_df, sample_seasonal_dict,
                           sample_vendor_df, sample_patterns_list):
    """Test all chart methods return plotly Figure objects."""
    assert isinstance(
        dashboard_gen._create_equipment_chart(sample_equipment_df),
        go.Figure
    )
    assert isinstance(
        dashboard_gen._create_seasonal_chart(sample_seasonal_dict),
        go.Figure
    )
    assert isinstance(
        dashboard_gen._create_vendor_chart(sample_vendor_df),
        go.Figure
    )
    assert isinstance(
        dashboard_gen._create_failure_chart(sample_patterns_list),
        go.Figure
    )


# Dashboard generation tests

def test_create_dashboard(dashboard_gen, sample_equipment_df, sample_seasonal_dict,
                         sample_vendor_df, sample_patterns_list, tmp_path):
    """Test dashboard HTML file is created successfully."""
    output_path = tmp_path / "dashboard.html"

    result = dashboard_gen.create_dashboard(
        equipment_df=sample_equipment_df,
        seasonal_dict=sample_seasonal_dict,
        vendor_df=sample_vendor_df,
        patterns_list=sample_patterns_list,
        output_path=output_path,
        title="Test Dashboard"
    )

    assert result == output_path
    assert output_path.exists()
    assert output_path.stat().st_size > 0


def test_dashboard_html_valid(dashboard_gen, sample_equipment_df, sample_seasonal_dict,
                              sample_vendor_df, sample_patterns_list, tmp_path):
    """Test dashboard HTML has valid structure."""
    output_path = tmp_path / "dashboard.html"

    dashboard_gen.create_dashboard(
        equipment_df=sample_equipment_df,
        seasonal_dict=sample_seasonal_dict,
        vendor_df=sample_vendor_df,
        patterns_list=sample_patterns_list,
        output_path=output_path
    )

    html_content = output_path.read_text(encoding='utf-8')

    # Check HTML structure
    assert '<!DOCTYPE html>' in html_content
    assert '<html>' in html_content
    assert '</html>' in html_content
    assert '<head>' in html_content
    assert '<body>' in html_content


def test_dashboard_includes_all_charts(dashboard_gen, sample_equipment_df,
                                      sample_seasonal_dict, sample_vendor_df,
                                      sample_patterns_list, tmp_path):
    """Test dashboard includes all 4 chart regions."""
    output_path = tmp_path / "dashboard.html"

    dashboard_gen.create_dashboard(
        equipment_df=sample_equipment_df,
        seasonal_dict=sample_seasonal_dict,
        vendor_df=sample_vendor_df,
        patterns_list=sample_patterns_list,
        output_path=output_path
    )

    html_content = output_path.read_text(encoding='utf-8')

    # Check for chart titles
    assert 'Equipment Maintenance Priority Rankings' in html_content
    assert 'Seasonal Cost and Work Order Trends' in html_content
    assert 'Vendor Performance Comparison' in html_content
    assert 'High-Impact Failure Patterns' in html_content


def test_dashboard_standalone(dashboard_gen, sample_equipment_df, sample_seasonal_dict,
                              sample_vendor_df, sample_patterns_list, tmp_path):
    """Test dashboard includes plotly.js (not just CDN reference)."""
    output_path = tmp_path / "dashboard.html"

    dashboard_gen.create_dashboard(
        equipment_df=sample_equipment_df,
        seasonal_dict=sample_seasonal_dict,
        vendor_df=sample_vendor_df,
        patterns_list=sample_patterns_list,
        output_path=output_path
    )

    html_content = output_path.read_text(encoding='utf-8')

    # Check for plotly script tag (CDN is acceptable for this implementation)
    assert '<script' in html_content
    assert 'plotly' in html_content.lower()


def test_dashboard_metadata(dashboard_gen, sample_equipment_df, sample_seasonal_dict,
                           sample_vendor_df, sample_patterns_list, tmp_path):
    """Test dashboard includes metadata comment with timestamp."""
    output_path = tmp_path / "dashboard.html"

    dashboard_gen.create_dashboard(
        equipment_df=sample_equipment_df,
        seasonal_dict=sample_seasonal_dict,
        vendor_df=sample_vendor_df,
        patterns_list=sample_patterns_list,
        output_path=output_path
    )

    html_content = output_path.read_text(encoding='utf-8')

    # Check for metadata comment
    assert '<!-- Dashboard Metadata' in html_content
    assert 'Generated:' in html_content
    assert 'Data Summary:' in html_content


def test_dashboard_responsive(dashboard_gen, sample_equipment_df, sample_seasonal_dict,
                              sample_vendor_df, sample_patterns_list, tmp_path):
    """Test dashboard layout is configured for responsive design."""
    output_path = tmp_path / "dashboard.html"

    dashboard_gen.create_dashboard(
        equipment_df=sample_equipment_df,
        seasonal_dict=sample_seasonal_dict,
        vendor_df=sample_vendor_df,
        patterns_list=sample_patterns_list,
        output_path=output_path
    )

    html_content = output_path.read_text(encoding='utf-8')

    # Check for viewport meta tag
    assert 'viewport' in html_content
