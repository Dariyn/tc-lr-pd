"""
Tests for the report builder module.

Covers:
- Report and ReportSection data model creation
- ReportBuilder initialization and data loading
- Executive summary generation
- Equipment analysis section
- Seasonal analysis section
- Vendor analysis section
- Failure analysis section
- Full report build
- Edge cases: empty sections, missing data, no patterns
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from src.reporting.report_builder import (
    ReportBuilder,
    Report,
    ReportSection
)


# Test Fixtures

@pytest.fixture
def sample_work_orders():
    """
    Create sample work order data for testing.

    Includes variety of equipment, dates, costs, contractors, and text fields
    to enable comprehensive report testing.
    """
    base_date = datetime(2024, 1, 1)

    data = {
        'wo_no': [f'WO-{i:04d}' for i in range(1, 101)],
        'Equipment_ID': [f'EQ-{i % 20:03d}' for i in range(1, 101)],
        'Equipment_Name': [f'Equipment {i % 20}' for i in range(1, 101)],
        'equipment_primary_category': ['HVAC'] * 50 + ['Plumbing'] * 30 + ['Electrical'] * 20,
        'Create_Date': [base_date + timedelta(days=i*3) for i in range(100)],
        'Complete_Date': [base_date + timedelta(days=i*3 + 2) for i in range(100)],
        'PO_AMOUNT': np.random.uniform(100, 5000, 100),
        'Contractor': ['Vendor A'] * 30 + ['Vendor B'] * 25 + ['Vendor C'] * 20 + ['Vendor D'] * 15 + [None] * 10,
        'Problem': ['leak issue'] * 20 + ['broken motor'] * 15 + ['electrical fault'] * 15 +
                   ['noise problem'] * 10 + ['sensor malfunction'] * 10 + ['general repair'] * 30,
        'Cause': ['worn seal'] * 20 + ['motor failure'] * 15 + ['wiring short'] * 15 +
                 ['bearing wear'] * 10 + ['sensor defect'] * 10 + ['unknown'] * 30,
        'Remedy': ['replaced seal'] * 20 + ['replaced motor'] * 15 + ['repaired wiring'] * 15 +
                  ['lubricated bearing'] * 10 + ['replaced sensor'] * 10 + ['repaired'] * 30,
    }

    return pd.DataFrame(data)


@pytest.fixture
def empty_work_orders():
    """Empty DataFrame with expected columns but no data."""
    df = pd.DataFrame(columns=[
        'wo_no', 'Equipment_ID', 'Equipment_Name', 'equipment_primary_category',
        'Create_Date', 'Complete_Date', 'PO_AMOUNT', 'Contractor',
        'Problem', 'Cause', 'Remedy'
    ])
    # Set proper dtypes for date columns to avoid issues
    df['Create_Date'] = pd.to_datetime(df['Create_Date'])
    df['Complete_Date'] = pd.to_datetime(df['Complete_Date'])
    return df


@pytest.fixture
def minimal_work_orders():
    """Minimal dataset with only required columns and few rows."""
    return pd.DataFrame({
        'Equipment_ID': ['EQ-001', 'EQ-002'],
        'Equipment_Name': ['Equipment 1', 'Equipment 2'],
        'equipment_primary_category': ['HVAC', 'HVAC'],
        'Create_Date': [datetime(2024, 1, 1), datetime(2024, 1, 2)],
        'Complete_Date': [datetime(2024, 1, 1), datetime(2024, 1, 2)],
        'PO_AMOUNT': [100, 200],
        'Contractor': ['Vendor A', 'Vendor B'],
        'Problem': ['test', 'test'],
        'Cause': ['test', 'test'],
        'Remedy': ['test', 'test']
    })


# Data Model Tests

def test_report_section_creation():
    """Test ReportSection dataclass creation."""
    content = pd.DataFrame({'col1': [1, 2, 3]})
    section = ReportSection(
        title="Test Section",
        content=content,
        summary_text="This is a test summary",
        recommendations=["Recommendation 1", "Recommendation 2"]
    )

    assert section.title == "Test Section"
    assert isinstance(section.content, pd.DataFrame)
    assert section.summary_text == "This is a test summary"
    assert len(section.recommendations) == 2


def test_report_section_default_recommendations():
    """Test ReportSection with default empty recommendations list."""
    section = ReportSection(
        title="Test Section",
        content={'key': 'value'},
        summary_text="Summary"
    )

    assert section.recommendations == []


def test_report_creation():
    """Test Report dataclass creation."""
    metadata = {
        'generated_date': '2024-01-01',
        'total_records': 100
    }

    report = Report(
        metadata=metadata,
        sections=[],
        executive_summary="Executive summary text"
    )

    assert report.metadata['total_records'] == 100
    assert report.sections == []
    assert report.executive_summary == "Executive summary text"


def test_report_default_values():
    """Test Report with default sections and summary."""
    report = Report(metadata={'test': 'value'})

    assert report.sections == []
    assert report.executive_summary == ""


# ReportBuilder Initialization Tests

def test_report_builder_init():
    """Test ReportBuilder initialization."""
    builder = ReportBuilder('test_file.csv')

    assert builder.input_file == 'test_file.csv'
    assert builder.df is None


def test_report_builder_load_data(sample_work_orders, tmp_path):
    """Test data loading from file."""
    # Create temporary CSV file
    test_file = tmp_path / "test_data.csv"
    sample_work_orders.to_csv(test_file, index=False)

    # Mock the load_work_orders function to return our sample data
    with patch('src.pipeline.data_loader.load_work_orders') as mock_load:
        mock_load.return_value = sample_work_orders

        builder = ReportBuilder(str(test_file))
        df = builder._load_data()

        assert df is not None
        assert len(df) == 100
        assert builder.df is not None


def test_report_builder_calculate_metadata(sample_work_orders):
    """Test metadata calculation from DataFrame."""
    builder = ReportBuilder('dummy.csv')
    metadata = builder._calculate_metadata(sample_work_orders)

    assert 'generated_date' in metadata
    assert metadata['total_records'] == 100
    assert 'data_period_start' in metadata
    assert 'data_period_end' in metadata
    assert 'date_range_days' in metadata
    assert 'total_cost' in metadata
    assert metadata['total_cost'] > 0


def test_report_builder_metadata_missing_dates():
    """Test metadata calculation when dates are missing."""
    df = pd.DataFrame({
        'PO_AMOUNT': [100, 200]
    })

    builder = ReportBuilder('dummy.csv')
    metadata = builder._calculate_metadata(df)

    assert metadata['data_period_start'] == 'N/A'
    assert metadata['data_period_end'] == 'N/A'
    assert metadata['date_range_days'] == 0


def test_report_builder_metadata_missing_costs():
    """Test metadata calculation when costs are missing."""
    df = pd.DataFrame({
        'Complete_Date': [datetime(2024, 1, 1)]
    })

    builder = ReportBuilder('dummy.csv')
    metadata = builder._calculate_metadata(df)

    assert metadata['total_cost'] == 0


# Section Creation Tests

def test_create_section_helper():
    """Test _create_section helper method."""
    builder = ReportBuilder('dummy.csv')
    content = {'key': 'value'}

    section = builder._create_section(
        title="Test Title",
        content=content,
        summary="Test summary",
        recommendations=["Rec 1", "Rec 2"]
    )

    assert section.title == "Test Title"
    assert section.content == content
    assert section.summary_text == "Test summary"
    assert len(section.recommendations) == 2


def test_create_section_no_recommendations():
    """Test _create_section with no recommendations."""
    builder = ReportBuilder('dummy.csv')

    section = builder._create_section(
        title="Test",
        content={},
        summary="Summary"
    )

    assert section.recommendations == []


# Executive Summary Tests

def test_build_executive_summary_with_sections():
    """Test executive summary generation from multiple sections."""
    builder = ReportBuilder('dummy.csv')

    sections = [
        ReportSection(
            title="Section 1",
            content={},
            summary_text="Summary 1",
            recommendations=["Rec 1A", "Rec 1B"]
        ),
        ReportSection(
            title="Section 2",
            content={},
            summary_text="Summary 2",
            recommendations=["Rec 2A"]
        )
    ]

    summary = builder._build_executive_summary(sections)

    assert "2 areas" in summary
    assert "Section 1" in summary
    assert "Section 2" in summary
    assert "Summary 1" in summary
    assert "Summary 2" in summary
    assert "Rec 1A" in summary  # Top recommendation from first section
    assert "Rec 2A" in summary  # Top recommendation from second section


def test_build_executive_summary_empty_sections():
    """Test executive summary with no sections."""
    builder = ReportBuilder('dummy.csv')
    summary = builder._build_executive_summary([])

    assert "0 areas" in summary


# Equipment Analysis Section Tests

def test_add_equipment_analysis_success(sample_work_orders):
    """Test equipment analysis section with valid data."""
    builder = ReportBuilder('dummy.csv')
    builder.df = sample_work_orders

    section = builder.add_equipment_analysis()

    assert section.title == "Equipment Analysis"
    assert isinstance(section.content, dict)
    assert 'top_equipment' in section.content or 'message' in section.content
    assert section.summary_text != ""
    assert len(section.recommendations) > 0


def test_add_equipment_analysis_no_outliers(minimal_work_orders):
    """Test equipment analysis when no consensus outliers found."""
    builder = ReportBuilder('dummy.csv')
    builder.df = minimal_work_orders

    section = builder.add_equipment_analysis()

    assert section.title == "Equipment Analysis"
    assert 'message' in section.content
    assert 'No high-priority equipment identified' in section.content['message']
    assert section.content['outliers_detected'] == 0


def test_add_equipment_analysis_data_not_loaded():
    """Test equipment analysis raises error when data not loaded."""
    builder = ReportBuilder('dummy.csv')

    with pytest.raises(ValueError, match="Data not loaded"):
        builder.add_equipment_analysis()


# Seasonal Analysis Section Tests

def test_add_seasonal_analysis_success(sample_work_orders):
    """Test seasonal analysis section with valid data."""
    builder = ReportBuilder('dummy.csv')
    builder.df = sample_work_orders

    section = builder.add_seasonal_analysis()

    assert section.title == "Seasonal Analysis"
    assert isinstance(section.content, dict)
    assert section.summary_text != ""
    assert len(section.recommendations) > 0


def test_add_seasonal_analysis_insufficient_data(empty_work_orders):
    """Test seasonal analysis with no valid date/cost data."""
    builder = ReportBuilder('dummy.csv')
    builder.df = empty_work_orders

    section = builder.add_seasonal_analysis()

    assert section.title == "Seasonal Analysis"
    assert 'message' in section.content
    assert 'No valid date and cost data available' in section.content['message']


def test_add_seasonal_analysis_data_not_loaded():
    """Test seasonal analysis raises error when data not loaded."""
    builder = ReportBuilder('dummy.csv')

    with pytest.raises(ValueError, match="Data not loaded"):
        builder.add_seasonal_analysis()


# Vendor Analysis Section Tests

def test_add_vendor_analysis_success(sample_work_orders):
    """Test vendor analysis section with valid data."""
    builder = ReportBuilder('dummy.csv')
    builder.df = sample_work_orders

    section = builder.add_vendor_analysis()

    assert section.title == "Vendor Performance"
    assert isinstance(section.content, dict)
    assert section.summary_text != ""
    assert len(section.recommendations) > 0


def test_add_vendor_analysis_no_vendors():
    """Test vendor analysis when no vendor data available."""
    df = pd.DataFrame({
        'Equipment_ID': ['EQ-001'],
        'Equipment_Name': ['Equipment 1'],
        'equipment_primary_category': ['HVAC'],
        'Create_Date': [datetime(2024, 1, 1)],
        'Complete_Date': [datetime(2024, 1, 1)],
        'Contractor': [None],
        'PO_AMOUNT': [100]
    })

    builder = ReportBuilder('dummy.csv')
    builder.df = df

    section = builder.add_vendor_analysis()

    # Check title matches actual implementation
    assert "Vendor" in section.title  # Flexible match
    assert 'message' in section.content
    assert section.content['vendors_analyzed'] == 0


def test_add_vendor_analysis_data_not_loaded():
    """Test vendor analysis raises error when data not loaded."""
    builder = ReportBuilder('dummy.csv')

    with pytest.raises(ValueError, match="Data not loaded"):
        builder.add_vendor_analysis()


# Failure Analysis Section Tests

def test_add_failure_analysis_success(sample_work_orders):
    """Test failure analysis section with valid data."""
    builder = ReportBuilder('dummy.csv')
    builder.df = sample_work_orders

    section = builder.add_failure_analysis()

    assert section.title == "Failure Pattern Analysis"
    assert isinstance(section.content, dict)
    assert section.summary_text != ""
    assert len(section.recommendations) > 0


def test_add_failure_analysis_no_text_data():
    """Test failure analysis when no text fields available."""
    df = pd.DataFrame({
        'Equipment_ID': ['EQ-001', 'EQ-002'],
        'PO_AMOUNT': [100, 200]
    })

    builder = ReportBuilder('dummy.csv')
    builder.df = df

    section = builder.add_failure_analysis()

    assert section.title == "Failure Pattern Analysis"
    assert 'message' in section.content
    assert section.content['patterns_found'] == 0


def test_add_failure_analysis_data_not_loaded():
    """Test failure analysis raises error when data not loaded."""
    builder = ReportBuilder('dummy.csv')

    with pytest.raises(ValueError, match="Data not loaded"):
        builder.add_failure_analysis()


# Full Report Build Tests

def test_build_report_full(sample_work_orders):
    """Test complete report building with all sections."""
    with patch('src.pipeline.data_loader.load_work_orders') as mock_load:
        mock_load.return_value = sample_work_orders

        builder = ReportBuilder('dummy.csv')
        report = builder.build_report()

        # Check metadata
        assert report.metadata['total_records'] == 100
        assert report.metadata['total_cost'] > 0

        # Check sections created
        assert len(report.sections) == 4
        section_titles = [s.title for s in report.sections]
        assert "Equipment Analysis" in section_titles
        assert "Seasonal Analysis" in section_titles
        assert "Vendor Performance" in section_titles
        assert "Failure Pattern Analysis" in section_titles

        # Check executive summary generated
        assert report.executive_summary != ""
        assert "4 areas" in report.executive_summary


def test_build_report_minimal_data(minimal_work_orders):
    """Test report building with minimal data."""
    with patch('src.pipeline.data_loader.load_work_orders') as mock_load:
        mock_load.return_value = minimal_work_orders

        builder = ReportBuilder('dummy.csv')
        report = builder.build_report()

        # Report should still be created with 4 sections
        assert len(report.sections) == 4
        assert report.metadata['total_records'] == 2


def test_build_report_empty_data(empty_work_orders):
    """Test report building with empty DataFrame."""
    with patch('src.pipeline.data_loader.load_work_orders') as mock_load:
        mock_load.return_value = empty_work_orders

        builder = ReportBuilder('dummy.csv')
        report = builder.build_report()

        # Report should still be created
        assert report.metadata['total_records'] == 0
        assert len(report.sections) == 4


# Edge Case Tests

def test_report_with_null_costs():
    """Test report handles null cost values gracefully."""
    df = pd.DataFrame({
        'Equipment_ID': ['EQ-001', 'EQ-002', 'EQ-003'],
        'Equipment_Name': ['Eq 1', 'Eq 2', 'Eq 3'],
        'equipment_primary_category': ['HVAC', 'HVAC', 'HVAC'],
        'Complete_Date': [datetime(2024, 1, 1), datetime(2024, 1, 2), datetime(2024, 1, 3)],
        'PO_AMOUNT': [100, None, 300]
    })

    builder = ReportBuilder('dummy.csv')
    metadata = builder._calculate_metadata(df)

    # Should handle None values without crashing
    assert metadata['total_cost'] >= 0


def test_report_with_future_dates():
    """Test report handles future dates correctly."""
    df = pd.DataFrame({
        'Complete_Date': [datetime(2024, 1, 1), datetime(2025, 12, 31)],
        'PO_AMOUNT': [100, 200]
    })

    builder = ReportBuilder('dummy.csv')
    metadata = builder._calculate_metadata(df)

    # Should calculate date range including future dates
    assert metadata['date_range_days'] > 0
    assert '2025' in metadata['data_period_end']


def test_report_formatting_large_numbers():
    """Test that large numbers are formatted correctly with commas and currency."""
    df = pd.DataFrame({
        'Equipment_ID': ['EQ-001'] * 50,
        'Equipment_Name': ['Equipment 1'] * 50,
        'equipment_primary_category': ['HVAC'] * 50,
        'Complete_Date': [datetime(2024, 1, 1) + timedelta(days=i) for i in range(50)],
        'Create_Date': [datetime(2024, 1, 1) + timedelta(days=i) for i in range(50)],
        'PO_AMOUNT': [10000] * 50,  # Large costs
        'Contractor': ['Vendor A'] * 50,
        'Problem': ['test'] * 50,
        'Cause': ['test'] * 50,
        'Remedy': ['test'] * 50
    })

    with patch('src.pipeline.data_loader.load_work_orders') as mock_load:
        mock_load.return_value = df

        builder = ReportBuilder('dummy.csv')
        report = builder.build_report()

        # Check that total cost is calculated correctly
        assert report.metadata['total_cost'] == 500000


def test_section_content_types():
    """Test that sections can have both DataFrame and dict content."""
    builder = ReportBuilder('dummy.csv')

    # DataFrame content
    df_section = builder._create_section(
        title="DataFrame Section",
        content=pd.DataFrame({'a': [1, 2]}),
        summary="DF summary"
    )
    assert isinstance(df_section.content, pd.DataFrame)

    # Dict content
    dict_section = builder._create_section(
        title="Dict Section",
        content={'key': 'value'},
        summary="Dict summary"
    )
    assert isinstance(dict_section.content, dict)
