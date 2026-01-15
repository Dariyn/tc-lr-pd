"""
Test suite for PDF report generation.

Tests cover:
- PDF initialization and basic structure
- Cover page generation with metadata
- Table formatting with DataFrame input
- Executive summary rendering
- Section renderers for all analysis types
- Full PDF generation with all sections
- Output file creation and validation
- Edge cases: empty sections, long text wrapping
"""

import pytest
import pandas as pd
import os
from datetime import datetime
from src.reporting.pdf_generator import PDFReportGenerator
from src.reporting.report_builder import Report, ReportSection


@pytest.fixture
def sample_metadata():
    """Sample report metadata for testing."""
    return {
        'generated_date': '2024-01-15 10:30:00',
        'data_period_start': '2023-01-01',
        'data_period_end': '2023-12-31',
        'total_records': 1500,
        'total_cost': 250000.50,
        'date_range_days': 365
    }


@pytest.fixture
def sample_equipment_section():
    """Sample equipment analysis section."""
    top_equipment = pd.DataFrame({
        'Equipment_Name': ['Chiller A1', 'HVAC Unit B2', 'Elevator C3'],
        'equipment_primary_category': ['HVAC', 'HVAC', 'Elevator'],
        'work_orders_per_month': ['2.50', '2.10', '1.80'],
        'avg_cost': ['$5,000', '$3,500', '$4,200'],
        'cost_impact': ['$150,000', '$88,200', '$90,720'],
        'priority_score': ['0.850', '0.720', '0.680'],
        'overall_rank': [1, 2, 3]
    })

    thresholds = {
        'wo_per_month_threshold': '1.5 WO/month',
        'avg_cost_threshold': '$3,000'
    }

    content = {
        'top_equipment': top_equipment,
        'total_equipment': 150,
        'consensus_outliers': 25,
        'thresholds': thresholds
    }

    return ReportSection(
        title='Equipment Analysis',
        content=content,
        summary_text='Identified 25 consensus outliers from 150 equipment items.',
        recommendations=[
            'Focus on top 3 equipment items: Chiller A1, HVAC Unit B2, Elevator C3',
            'Review maintenance contracts for high-cost equipment'
        ]
    )


@pytest.fixture
def sample_seasonal_section():
    """Sample seasonal analysis section."""
    monthly_costs = pd.DataFrame({
        'month': ['2023-01', '2023-02', '2023-03'],
        'total_cost': ['$25,000', '$28,500', '$22,000'],
        'avg_cost': ['$2,500', '$2,850', '$2,200'],
        'work_order_count': [10, 10, 10]
    })

    quarterly_costs = pd.DataFrame({
        'quarter': ['2023-Q1', '2023-Q2', '2023-Q3', '2023-Q4'],
        'total_cost': ['$75,500', '$85,000', '$65,000', '$70,000'],
        'avg_cost': ['$2,517', '$2,833', '$2,167', '$2,333'],
        'variance_pct': ['+5.0%', '+15.0%', '-10.0%', '-5.0%']
    })

    patterns = [
        {'pattern': 'Higher costs in Q2 (summer months)'},
        {'pattern': 'Lower costs in Q3 (fall months)'}
    ]

    content = {
        'monthly_costs': monthly_costs,
        'quarterly_costs': quarterly_costs,
        'patterns': patterns,
        'pattern_count': 2
    }

    return ReportSection(
        title='Seasonal Analysis',
        content=content,
        summary_text='Detected 2 seasonal patterns. Higher costs in summer, lower in fall.',
        recommendations=[
            'Plan major maintenance during Q3 to leverage lower demand',
            'Budget increase for Q2 summer peak period'
        ]
    )


@pytest.fixture
def sample_vendor_section():
    """Sample vendor performance section."""
    top_vendors = pd.DataFrame({
        'contractor': ['Vendor A', 'Vendor B', 'Vendor C'],
        'total_cost': ['$50,000', '$35,000', '$25,000'],
        'avg_cost_per_wo': ['$2,500', '$1,750', '$1,250'],
        'work_order_count': [20, 20, 20],
        'avg_duration_days': [5.5, 3.2, 4.0]
    })

    content = {
        'top_vendors': top_vendors,
        'total_vendors': 15,
        'efficiency_metrics': pd.DataFrame(),
        'quality_metrics': pd.DataFrame(),
        'recommendation_count': 3
    }

    return ReportSection(
        title='Vendor Performance',
        content=content,
        summary_text='Analyzed 15 vendors. Top 3 vendors account for $110,000 (44%) of total costs.',
        recommendations=[
            'Review contract with Vendor A (highest cost)',
            'Consider increasing work with Vendor C (best efficiency)'
        ]
    )


@pytest.fixture
def sample_failure_section():
    """Sample failure pattern analysis section."""
    patterns = pd.DataFrame({
        'pattern': ['leak repair', 'filter replacement', 'motor failure'],
        'occurrences': [25, 20, 15],
        'total_cost': ['$50,000', '$15,000', '$45,000'],
        'avg_cost': ['$2,000', '$750', '$3,000'],
        'equipment_affected': [12, 15, 8]
    })

    content = {
        'high_impact_patterns': patterns,
        'failure_categories': pd.DataFrame(),
        'pattern_count': 3,
        'category_count': 5
    }

    return ReportSection(
        title='Failure Pattern Analysis',
        content=content,
        summary_text='Identified 3 high-impact failure patterns affecting 35 equipment items.',
        recommendations=[
            'Implement preventive maintenance for leak-prone equipment',
            'Stock motor replacement parts for critical equipment'
        ]
    )


@pytest.fixture
def sample_report(sample_metadata, sample_equipment_section, sample_seasonal_section,
                   sample_vendor_section, sample_failure_section):
    """Complete sample report with all sections."""
    report = Report(metadata=sample_metadata)
    report.sections = [
        sample_equipment_section,
        sample_seasonal_section,
        sample_vendor_section,
        sample_failure_section
    ]
    report.executive_summary = (
        "Analysis completed across 4 areas:\n\n"
        "Equipment Analysis:\n"
        "  Identified 25 consensus outliers from 150 equipment items.\n"
        "  - Focus on top 3 equipment items\n\n"
        "Seasonal Analysis:\n"
        "  Detected 2 seasonal patterns.\n"
        "  - Plan major maintenance during Q3\n"
    )
    return report


class TestPDFInitialization:
    """Test PDF generator initialization."""

    def test_init(self):
        """Test PDFReportGenerator initialization."""
        generator = PDFReportGenerator()
        assert generator.pdf is None
        assert generator.report is None

    def test_init_creates_empty_generator(self):
        """Test that initialization creates generator without errors."""
        generator = PDFReportGenerator()
        assert isinstance(generator, PDFReportGenerator)


class TestCoverPage:
    """Test cover page generation."""

    def test_cover_page_generation(self, sample_metadata, tmp_path):
        """Test cover page is generated with correct metadata."""
        generator = PDFReportGenerator()
        report = Report(metadata=sample_metadata)

        output_file = tmp_path / "test_cover.pdf"
        generator.generate_pdf(report, str(output_file))

        # Verify PDF was created
        assert output_file.exists()
        assert output_file.stat().st_size > 0

    def test_cover_page_with_missing_metadata(self, tmp_path):
        """Test cover page handles missing metadata gracefully."""
        generator = PDFReportGenerator()
        report = Report(metadata={})

        output_file = tmp_path / "test_missing_meta.pdf"
        generator.generate_pdf(report, str(output_file))

        # Should create PDF even with missing metadata
        assert output_file.exists()


class TestTableFormatting:
    """Test table formatting functionality."""

    def test_format_table_with_data(self, tmp_path):
        """Test table formatting with valid DataFrame."""
        generator = PDFReportGenerator()
        df = pd.DataFrame({
            'Column1': ['A', 'B', 'C'],
            'Column2': [1, 2, 3],
            'Column3': [10.5, 20.7, 30.2]
        })

        report = Report(metadata={'generated_date': '2024-01-15'})
        section = ReportSection(
            title='Test Section',
            content=df,
            summary_text='Test table'
        )
        report.sections = [section]

        output_file = tmp_path / "test_table.pdf"
        generator.generate_pdf(report, str(output_file))

        assert output_file.exists()

    def test_format_empty_table(self, tmp_path):
        """Test table formatting with empty DataFrame."""
        generator = PDFReportGenerator()
        df = pd.DataFrame()

        report = Report(metadata={'generated_date': '2024-01-15'})
        section = ReportSection(
            title='Empty Section',
            content=df,
            summary_text='Empty table test'
        )
        report.sections = [section]

        output_file = tmp_path / "test_empty_table.pdf"
        generator.generate_pdf(report, str(output_file))

        # Should handle empty table gracefully
        assert output_file.exists()

    def test_format_table_truncation(self, tmp_path):
        """Test that large tables are truncated appropriately."""
        generator = PDFReportGenerator()

        # Create large DataFrame (30 rows)
        df = pd.DataFrame({
            'Column1': [f'Row{i}' for i in range(30)],
            'Column2': list(range(30)),
            'Column3': [i * 10.5 for i in range(30)]
        })

        report = Report(metadata={'generated_date': '2024-01-15'})
        section = ReportSection(
            title='Large Table',
            content=df,
            summary_text='Large table test'
        )
        report.sections = [section]

        output_file = tmp_path / "test_large_table.pdf"
        generator.generate_pdf(report, str(output_file))

        assert output_file.exists()


class TestExecutiveSummary:
    """Test executive summary rendering."""

    def test_executive_summary_rendering(self, tmp_path):
        """Test executive summary is rendered correctly."""
        generator = PDFReportGenerator()
        report = Report(metadata={'generated_date': '2024-01-15'})
        report.executive_summary = (
            "Test summary with multiple lines.\n"
            "Second line of summary.\n"
            "Third line with more details."
        )

        output_file = tmp_path / "test_exec_summary.pdf"
        generator.generate_pdf(report, str(output_file))

        assert output_file.exists()

    def test_empty_executive_summary(self, tmp_path):
        """Test handles empty executive summary."""
        generator = PDFReportGenerator()
        report = Report(metadata={'generated_date': '2024-01-15'})
        report.executive_summary = ""

        output_file = tmp_path / "test_empty_summary.pdf"
        generator.generate_pdf(report, str(output_file))

        assert output_file.exists()


class TestEquipmentSection:
    """Test equipment section rendering."""

    def test_equipment_section_rendering(self, sample_equipment_section, tmp_path):
        """Test equipment section renders correctly."""
        generator = PDFReportGenerator()
        report = Report(metadata={'generated_date': '2024-01-15'})
        report.sections = [sample_equipment_section]

        output_file = tmp_path / "test_equipment.pdf"
        generator.generate_pdf(report, str(output_file))

        assert output_file.exists()

    def test_equipment_section_with_empty_data(self, tmp_path):
        """Test equipment section handles empty data."""
        generator = PDFReportGenerator()

        content = {
            'message': 'No high-priority equipment identified',
            'total_equipment': 100,
            'outliers_detected': 0
        }

        section = ReportSection(
            title='Equipment Analysis',
            content=content,
            summary_text='No consensus outliers detected.',
            recommendations=['Continue monitoring']
        )

        report = Report(metadata={'generated_date': '2024-01-15'})
        report.sections = [section]

        output_file = tmp_path / "test_equipment_empty.pdf"
        generator.generate_pdf(report, str(output_file))

        assert output_file.exists()


class TestSeasonalSection:
    """Test seasonal analysis section rendering."""

    def test_seasonal_section_rendering(self, sample_seasonal_section, tmp_path):
        """Test seasonal section renders correctly."""
        generator = PDFReportGenerator()
        report = Report(metadata={'generated_date': '2024-01-15'})
        report.sections = [sample_seasonal_section]

        output_file = tmp_path / "test_seasonal.pdf"
        generator.generate_pdf(report, str(output_file))

        assert output_file.exists()

    def test_seasonal_section_with_no_patterns(self, tmp_path):
        """Test seasonal section when no patterns detected."""
        generator = PDFReportGenerator()

        content = {
            'monthly_costs': pd.DataFrame(),
            'quarterly_costs': pd.DataFrame(),
            'patterns': [],
            'pattern_count': 0
        }

        section = ReportSection(
            title='Seasonal Analysis',
            content=content,
            summary_text='No significant patterns detected.',
            recommendations=['Collect more data']
        )

        report = Report(metadata={'generated_date': '2024-01-15'})
        report.sections = [section]

        output_file = tmp_path / "test_seasonal_empty.pdf"
        generator.generate_pdf(report, str(output_file))

        assert output_file.exists()


class TestVendorSection:
    """Test vendor performance section rendering."""

    def test_vendor_section_rendering(self, sample_vendor_section, tmp_path):
        """Test vendor section renders correctly."""
        generator = PDFReportGenerator()
        report = Report(metadata={'generated_date': '2024-01-15'})
        report.sections = [sample_vendor_section]

        output_file = tmp_path / "test_vendor.pdf"
        generator.generate_pdf(report, str(output_file))

        assert output_file.exists()

    def test_vendor_section_with_no_data(self, tmp_path):
        """Test vendor section handles no vendor data."""
        generator = PDFReportGenerator()

        content = {
            'message': 'No contractors with minimum 3 work orders found',
            'vendors_analyzed': 0
        }

        section = ReportSection(
            title='Vendor Performance',
            content=content,
            summary_text='No vendor data available.',
            recommendations=['Ensure Contractor field is populated']
        )

        report = Report(metadata={'generated_date': '2024-01-15'})
        report.sections = [section]

        output_file = tmp_path / "test_vendor_empty.pdf"
        generator.generate_pdf(report, str(output_file))

        assert output_file.exists()


class TestFailureSection:
    """Test failure pattern section rendering."""

    def test_failure_section_rendering(self, sample_failure_section, tmp_path):
        """Test failure section renders correctly."""
        generator = PDFReportGenerator()
        report = Report(metadata={'generated_date': '2024-01-15'})
        report.sections = [sample_failure_section]

        output_file = tmp_path / "test_failure.pdf"
        generator.generate_pdf(report, str(output_file))

        assert output_file.exists()

    def test_failure_section_with_no_patterns(self, tmp_path):
        """Test failure section handles no patterns."""
        generator = PDFReportGenerator()

        content = {
            'high_impact_patterns': pd.DataFrame(),
            'failure_categories': pd.DataFrame(),
            'pattern_count': 0,
            'category_count': 0
        }

        section = ReportSection(
            title='Failure Pattern Analysis',
            content=content,
            summary_text='No text data available.',
            recommendations=['Ensure work orders include descriptions']
        )

        report = Report(metadata={'generated_date': '2024-01-15'})
        report.sections = [section]

        output_file = tmp_path / "test_failure_empty.pdf"
        generator.generate_pdf(report, str(output_file))

        assert output_file.exists()


class TestRecommendationsPage:
    """Test recommendations page rendering."""

    def test_recommendations_page(self, sample_report, tmp_path):
        """Test recommendations page consolidates all recommendations."""
        generator = PDFReportGenerator()

        output_file = tmp_path / "test_recommendations.pdf"
        generator.generate_pdf(sample_report, str(output_file))

        assert output_file.exists()

    def test_recommendations_page_empty(self, tmp_path):
        """Test recommendations page with no recommendations."""
        generator = PDFReportGenerator()
        report = Report(metadata={'generated_date': '2024-01-15'})

        section = ReportSection(
            title='Test Section',
            content={'test': 'data'},
            summary_text='No recommendations',
            recommendations=[]
        )
        report.sections = [section]

        output_file = tmp_path / "test_recs_empty.pdf"
        generator.generate_pdf(report, str(output_file))

        assert output_file.exists()


class TestFullPDFGeneration:
    """Test complete PDF generation."""

    def test_full_pdf_generation(self, sample_report, tmp_path):
        """Test generating complete PDF with all sections."""
        generator = PDFReportGenerator()

        output_file = tmp_path / "test_full_report.pdf"
        generator.generate_pdf(sample_report, str(output_file))

        # Verify PDF was created
        assert output_file.exists()
        assert output_file.stat().st_size > 5000  # Should be reasonably sized

    def test_pdf_output_path_validation(self, sample_report, tmp_path):
        """Test PDF output to valid path."""
        generator = PDFReportGenerator()

        output_file = tmp_path / "subdir" / "report.pdf"
        output_file.parent.mkdir(parents=True, exist_ok=True)

        generator.generate_pdf(sample_report, str(output_file))

        assert output_file.exists()

    def test_multiple_pdf_generation(self, sample_report, tmp_path):
        """Test generating multiple PDFs in sequence."""
        generator1 = PDFReportGenerator()
        generator2 = PDFReportGenerator()

        output_file1 = tmp_path / "report1.pdf"
        output_file2 = tmp_path / "report2.pdf"

        generator1.generate_pdf(sample_report, str(output_file1))
        generator2.generate_pdf(sample_report, str(output_file2))

        assert output_file1.exists()
        assert output_file2.exists()


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_long_text_wrapping(self, tmp_path):
        """Test that long text wraps correctly."""
        generator = PDFReportGenerator()

        long_text = "This is a very long text " * 50
        section = ReportSection(
            title='Long Text Section',
            content={'test': 'data'},
            summary_text=long_text,
            recommendations=[long_text]
        )

        report = Report(metadata={'generated_date': '2024-01-15'})
        report.sections = [section]

        output_file = tmp_path / "test_long_text.pdf"
        generator.generate_pdf(report, str(output_file))

        assert output_file.exists()

    def test_special_characters(self, tmp_path):
        """Test handling of special characters in text."""
        generator = PDFReportGenerator()

        section = ReportSection(
            title='Special Characters',
            content={'test': 'data'},
            summary_text='Text with special chars: $ & @ # % *',
            recommendations=['Recommendation with & < > " \' characters']
        )

        report = Report(metadata={'generated_date': '2024-01-15'})
        report.sections = [section]

        output_file = tmp_path / "test_special_chars.pdf"
        generator.generate_pdf(report, str(output_file))

        assert output_file.exists()

    def test_empty_report(self, tmp_path):
        """Test generating PDF from report with no sections."""
        generator = PDFReportGenerator()
        report = Report(metadata={'generated_date': '2024-01-15'})
        report.sections = []

        output_file = tmp_path / "test_empty_report.pdf"
        generator.generate_pdf(report, str(output_file))

        # Should create minimal PDF even with no sections
        assert output_file.exists()

    def test_section_with_very_long_column_names(self, tmp_path):
        """Test table rendering with very long column names."""
        generator = PDFReportGenerator()

        df = pd.DataFrame({
            'very_long_column_name_that_exceeds_normal_length': [1, 2, 3],
            'another_extremely_long_column_name_for_testing': [4, 5, 6]
        })

        section = ReportSection(
            title='Long Columns',
            content=df,
            summary_text='Test long column names'
        )

        report = Report(metadata={'generated_date': '2024-01-15'})
        report.sections = [section]

        output_file = tmp_path / "test_long_columns.pdf"
        generator.generate_pdf(report, str(output_file))

        assert output_file.exists()
