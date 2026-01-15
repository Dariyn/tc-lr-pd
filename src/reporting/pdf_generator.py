"""
PDF report generator module for creating formatted PDF reports.

Purpose: Convert Report objects from report_builder into professional PDF documents
with tables, formatting, and recommendations for stakeholder distribution.
"""

import pandas as pd
from datetime import datetime
from fpdf import FPDF
from typing import Dict, Any, List, Optional
from src.reporting.report_builder import Report, ReportSection


class PDFReportGenerator:
    """
    Generates professional PDF reports with tables and formatting.

    Uses fpdf2 library to create multi-page PDF documents with:
    - Cover page with summary metrics
    - Table of contents
    - Executive summary
    - Analysis sections (equipment, seasonal, vendor, failure)
    - Formatted tables with alternating row colors
    - Recommendations and page numbering
    """

    # Color constants
    HEADER_COLOR = (31, 71, 136)  # Dark blue #1f4788
    ALT_ROW_COLOR = (240, 240, 240)  # Light gray #f0f0f0

    def __init__(self):
        """Initialize PDF generator with default settings."""
        self.pdf = None
        self.report = None

    def generate_pdf(self, report: Report, output_file: str) -> None:
        """
        Main entry point - generate complete PDF from Report object.

        Args:
            report: Report object with metadata and sections
            output_file: Path to save PDF file

        Raises:
            ValueError: If report is invalid or output path is invalid
        """
        self.report = report

        # Initialize FPDF with A4 page size, portrait orientation
        self.pdf = FPDF(orientation='P', unit='mm', format='A4')
        self.pdf.set_auto_page_break(auto=True, margin=20)
        self.pdf.set_margins(left=20, top=20, right=20)

        # Add pages
        self._add_cover_page(report)
        self._add_table_of_contents(report)
        self._add_executive_summary(report.executive_summary)

        # Add analysis sections
        for section in report.sections:
            self._add_section(section)

        # Add consolidated recommendations page
        self._add_recommendations_page(report.sections)

        # Output PDF
        self.pdf.output(output_file)

    def _add_cover_page(self, report: Report) -> None:
        """
        Create cover page with title, date, and key metrics summary.

        Args:
            report: Report object with metadata
        """
        self.pdf.add_page()

        # Title
        self.pdf.set_font('Arial', 'B', 24)
        self.pdf.ln(40)
        self.pdf.cell(0, 10, 'Work Order Analysis Report', 0, 1, 'C')

        # Date
        self.pdf.set_font('Arial', '', 12)
        self.pdf.ln(10)
        self.pdf.cell(0, 10, f"Generated: {report.metadata.get('generated_date', 'N/A')}", 0, 1, 'C')

        # Data period
        self.pdf.ln(5)
        start = report.metadata.get('data_period_start', 'N/A')
        end = report.metadata.get('data_period_end', 'N/A')
        self.pdf.cell(0, 10, f"Data Period: {start} to {end}", 0, 1, 'C')

        # Key metrics box
        self.pdf.ln(20)
        self.pdf.set_font('Arial', 'B', 14)
        self.pdf.cell(0, 10, 'Summary Metrics', 0, 1, 'C')

        self.pdf.ln(10)
        self.pdf.set_font('Arial', '', 12)

        # Metrics
        metrics = [
            ('Total Work Orders:', f"{report.metadata.get('total_records', 0):,}"),
            ('Total Cost:', f"${report.metadata.get('total_cost', 0):,.0f}"),
            ('Analysis Period:', f"{report.metadata.get('date_range_days', 0)} days"),
            ('Sections:', str(len(report.sections)))
        ]

        for label, value in metrics:
            self.pdf.cell(90, 8, label, 0, 0, 'R')
            self.pdf.set_font('Arial', 'B', 12)
            self.pdf.cell(0, 8, value, 0, 1, 'L')
            self.pdf.set_font('Arial', '', 12)

    def _add_table_of_contents(self, report: Report) -> None:
        """
        Create table of contents with section list.

        Args:
            report: Report object with sections

        Note: Page numbers are placeholders - full TOC with dynamic page numbers
        would require two-pass generation (not implemented for simplicity).
        """
        self.pdf.add_page()

        # Title
        self.pdf.set_font('Arial', 'B', 16)
        self.pdf.cell(0, 10, 'Table of Contents', 0, 1, 'L')
        self.pdf.ln(10)

        # Sections
        self.pdf.set_font('Arial', '', 12)

        sections = [
            'Executive Summary',
        ] + [section.title for section in report.sections] + [
            'Recommendations Summary'
        ]

        for i, section_title in enumerate(sections, 1):
            self.pdf.cell(140, 8, f"{i}. {section_title}", 0, 0, 'L')
            self.pdf.cell(0, 8, '...', 0, 1, 'R')

    def _add_executive_summary(self, summary_text: str) -> None:
        """
        Add executive summary page with key findings.

        Args:
            summary_text: Executive summary text from report
        """
        self.pdf.add_page()

        # Title
        self.pdf.set_font('Arial', 'B', 16)
        self.pdf.cell(0, 10, 'Executive Summary', 0, 1, 'L')
        self.pdf.ln(5)

        # Summary text
        self.pdf.set_font('Arial', '', 10)
        self.pdf.multi_cell(0, 6, summary_text)

    def _add_section(self, section: ReportSection) -> None:
        """
        Generic section renderer with title, content tables, recommendations.

        Args:
            section: ReportSection object with title, content, summary, recommendations
        """
        self.pdf.add_page()

        # Section title
        self.pdf.set_font('Arial', 'B', 16)
        self.pdf.cell(0, 10, section.title, 0, 1, 'L')
        self.pdf.ln(5)

        # Summary text
        self.pdf.set_font('Arial', '', 10)
        self.pdf.multi_cell(0, 6, section.summary_text)
        self.pdf.ln(5)

        # Content - handle DataFrame or dict
        if isinstance(section.content, pd.DataFrame):
            self._format_table(section.content)
        elif isinstance(section.content, dict):
            # Handle dict content with DataFrames inside
            for key, value in section.content.items():
                if isinstance(value, pd.DataFrame) and not value.empty:
                    self.pdf.ln(5)
                    self.pdf.set_font('Arial', 'B', 12)
                    self.pdf.cell(0, 8, key.replace('_', ' ').title(), 0, 1, 'L')
                    self.pdf.ln(2)
                    self._format_table(value)
                elif key == 'thresholds' and isinstance(value, dict):
                    # Handle thresholds specially
                    self.pdf.ln(5)
                    self.pdf.set_font('Arial', 'B', 12)
                    self.pdf.cell(0, 8, 'Detection Thresholds', 0, 1, 'L')
                    self.pdf.set_font('Arial', '', 10)
                    self.pdf.multi_cell(0, 6, f"WO/Month: {value.get('wo_per_month_threshold', 'N/A')}")
                    self.pdf.multi_cell(0, 6, f"Avg Cost: {value.get('avg_cost_threshold', 'N/A')}")

        self.pdf.ln(5)

        # Recommendations
        if section.recommendations:
            self.pdf.set_font('Arial', 'B', 12)
            self.pdf.cell(0, 8, 'Recommendations', 0, 1, 'L')
            self.pdf.ln(2)

            self.pdf.set_font('Arial', '', 10)
            for rec in section.recommendations:
                # Bullet point
                x_pos = self.pdf.get_x()
                y_pos = self.pdf.get_y()
                self.pdf.cell(5, 6, chr(149), 0, 0, 'L')  # Bullet character
                self.pdf.set_xy(x_pos + 7, y_pos)
                self.pdf.multi_cell(0, 6, rec)

    def _format_table(self, df: pd.DataFrame, max_rows: int = 20) -> None:
        """
        Convert DataFrame to formatted PDF table with headers, borders, alternating rows.

        Args:
            df: DataFrame to render as table
            max_rows: Maximum number of rows to display (default 20)
        """
        if df.empty:
            self.pdf.set_font('Arial', 'I', 10)
            self.pdf.cell(0, 8, 'No data available', 0, 1, 'L')
            return

        # Limit rows
        display_df = df.head(max_rows)

        # Calculate column widths based on content
        # For simplicity, use equal widths adjusted to fit page
        available_width = 170  # Page width minus margins
        num_cols = len(display_df.columns)
        col_width = available_width / num_cols if num_cols > 0 else 30

        # Ensure minimum readable width
        if col_width < 20:
            col_width = 20

        # Header row
        self.pdf.set_font('Arial', 'B', 9)
        self.pdf.set_fill_color(*self.HEADER_COLOR)
        self.pdf.set_text_color(255, 255, 255)

        for col in display_df.columns:
            # Truncate long column names
            col_name = str(col).replace('_', ' ').title()
            if len(col_name) > 20:
                col_name = col_name[:17] + '...'
            self.pdf.cell(col_width, 7, col_name, 1, 0, 'C', True)
        self.pdf.ln()

        # Data rows
        self.pdf.set_font('Arial', '', 9)
        self.pdf.set_text_color(0, 0, 0)

        for idx, row in display_df.iterrows():
            # Alternating row colors
            if idx % 2 == 0:
                self.pdf.set_fill_color(*self.ALT_ROW_COLOR)
                fill = True
            else:
                fill = False

            for col in display_df.columns:
                value = str(row[col])
                # Truncate long values
                if len(value) > 30:
                    value = value[:27] + '...'
                self.pdf.cell(col_width, 6, value, 1, 0, 'L', fill)
            self.pdf.ln()

        # Note if truncated
        if len(df) > max_rows:
            self.pdf.ln(2)
            self.pdf.set_font('Arial', 'I', 8)
            self.pdf.cell(0, 5, f"Showing top {max_rows} of {len(df)} rows", 0, 1, 'L')

    def _add_recommendations_page(self, sections: List[ReportSection]) -> None:
        """
        Consolidated recommendations from all sections.

        Args:
            sections: List of all ReportSection objects
        """
        self.pdf.add_page()

        # Title
        self.pdf.set_font('Arial', 'B', 16)
        self.pdf.cell(0, 10, 'Recommendations Summary', 0, 1, 'L')
        self.pdf.ln(5)

        # Collect all recommendations by section
        for section in sections:
            if section.recommendations:
                # Section name
                self.pdf.set_font('Arial', 'B', 12)
                self.pdf.cell(0, 8, section.title, 0, 1, 'L')
                self.pdf.ln(2)

                # Recommendations
                self.pdf.set_font('Arial', '', 10)
                for rec in section.recommendations:
                    x_pos = self.pdf.get_x()
                    y_pos = self.pdf.get_y()
                    self.pdf.cell(5, 6, chr(149), 0, 0, 'L')
                    self.pdf.set_xy(x_pos + 7, y_pos)
                    self.pdf.multi_cell(0, 6, rec)

                self.pdf.ln(3)

    def _add_page_footer(self) -> None:
        """
        Add page footer with page number and generation timestamp.

        Note: This method would be called via FPDF's footer() callback system.
        For this implementation, we're using auto-generated page numbers from FPDF.
        """
        # Position at 15mm from bottom
        self.pdf.set_y(-15)

        # Footer text
        self.pdf.set_font('Arial', 'I', 8)
        self.pdf.cell(0, 10, 'Generated by Work Order Analysis Pipeline', 0, 0, 'L')

        # Page number
        self.pdf.cell(0, 10, f'Page {self.pdf.page_no()}', 0, 0, 'R')
