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

        # Add analysis sections using specialized renderers
        for section in report.sections:
            if section.title == 'Equipment Analysis':
                self._add_equipment_section(section)
            elif section.title == 'Seasonal Analysis':
                self._add_seasonal_section(section)
            elif section.title == 'Vendor Performance':
                self._add_vendor_section(section)
            elif section.title == 'Failure Pattern Analysis':
                self._add_failure_section(section)
            else:
                # Fallback to generic renderer for unknown sections
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

    def _add_equipment_section(self, section: ReportSection) -> None:
        """
        Specialized renderer for equipment analysis section.

        Renders ranked equipment table (top 10), thresholds as text, and recommendations.

        Args:
            section: ReportSection with equipment analysis content
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

        # Extract content
        content = section.content

        if isinstance(content, dict):
            # Top equipment table
            if 'top_equipment' in content and isinstance(content['top_equipment'], pd.DataFrame):
                top_equipment = content['top_equipment']
                if not top_equipment.empty:
                    self.pdf.set_font('Arial', 'B', 12)
                    self.pdf.cell(0, 8, 'Top Priority Equipment (Top 10)', 0, 1, 'L')
                    self.pdf.ln(2)

                    # Define column widths for equipment table
                    col_widths = {
                        'Equipment_Name': 35,
                        'equipment_primary_category': 35,
                        'work_orders_per_month': 25,
                        'avg_cost': 25,
                        'cost_impact': 25,
                        'priority_score': 20,
                        'overall_rank': 15
                    }

                    # Header row
                    self.pdf.set_font('Arial', 'B', 8)
                    self.pdf.set_fill_color(*self.HEADER_COLOR)
                    self.pdf.set_text_color(255, 255, 255)

                    col_labels = {
                        'Equipment_Name': 'Equipment',
                        'equipment_primary_category': 'Category',
                        'work_orders_per_month': 'WO/Month',
                        'avg_cost': 'Avg Cost',
                        'cost_impact': 'Cost Impact',
                        'priority_score': 'Priority',
                        'overall_rank': 'Rank'
                    }

                    for col in top_equipment.columns:
                        if col in col_widths:
                            label = col_labels.get(col, col)
                            self.pdf.cell(col_widths[col], 7, label, 1, 0, 'C', True)
                    self.pdf.ln()

                    # Data rows
                    self.pdf.set_font('Arial', '', 8)
                    self.pdf.set_text_color(0, 0, 0)

                    for idx, row in top_equipment.iterrows():
                        # Alternating row colors
                        if idx % 2 == 0:
                            self.pdf.set_fill_color(*self.ALT_ROW_COLOR)
                            fill = True
                        else:
                            fill = False

                        for col in top_equipment.columns:
                            if col in col_widths:
                                value = str(row[col])
                                # Truncate long values
                                max_len = int(col_widths[col] / 2)
                                if len(value) > max_len:
                                    value = value[:max_len-3] + '...'
                                self.pdf.cell(col_widths[col], 6, value, 1, 0, 'L', fill)
                        self.pdf.ln()

            # Thresholds
            if 'thresholds' in content and isinstance(content['thresholds'], dict):
                self.pdf.ln(5)
                self.pdf.set_font('Arial', 'B', 12)
                self.pdf.cell(0, 8, 'Detection Thresholds', 0, 1, 'L')
                self.pdf.set_font('Arial', '', 10)
                thresholds = content['thresholds']
                threshold_text = (
                    f"Work Orders per Month: {thresholds.get('wo_per_month_threshold', 'N/A')}\n"
                    f"Average Cost: {thresholds.get('avg_cost_threshold', 'N/A')}"
                )
                self.pdf.multi_cell(0, 6, threshold_text)

        # Recommendations
        if section.recommendations:
            self.pdf.ln(5)
            self.pdf.set_font('Arial', 'B', 12)
            self.pdf.cell(0, 8, 'Recommendations', 0, 1, 'L')
            self.pdf.ln(2)

            self.pdf.set_font('Arial', '', 10)
            for rec in section.recommendations:
                # Calculate available width for bullet text
                left_margin = self.pdf.l_margin
                right_margin = self.pdf.r_margin
                page_width = self.pdf.w
                bullet_indent = 7
                text_width = page_width - left_margin - right_margin - bullet_indent

                x_pos = self.pdf.get_x()
                y_pos = self.pdf.get_y()
                self.pdf.cell(5, 6, chr(149), 0, 0, 'L')
                self.pdf.set_x(left_margin + bullet_indent)
                self.pdf.multi_cell(text_width, 6, str(rec) if rec else '')

    def _add_seasonal_section(self, section: ReportSection) -> None:
        """
        Specialized renderer for seasonal analysis section.

        Renders monthly/quarterly cost tables and detected patterns as bulleted list.

        Args:
            section: ReportSection with seasonal analysis content
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

        # Extract content
        content = section.content

        if isinstance(content, dict):
            # Monthly costs table
            if 'monthly_costs' in content and isinstance(content['monthly_costs'], pd.DataFrame):
                monthly = content['monthly_costs']
                if not monthly.empty:
                    self.pdf.set_font('Arial', 'B', 12)
                    self.pdf.cell(0, 8, 'Monthly Cost Trends', 0, 1, 'L')
                    self.pdf.ln(2)
                    self._format_table(monthly, max_rows=12)

            # Quarterly costs table
            if 'quarterly_costs' in content and isinstance(content['quarterly_costs'], pd.DataFrame):
                quarterly = content['quarterly_costs']
                if not quarterly.empty:
                    self.pdf.ln(5)
                    self.pdf.set_font('Arial', 'B', 12)
                    self.pdf.cell(0, 8, 'Quarterly Cost Analysis', 0, 1, 'L')
                    self.pdf.ln(2)
                    self._format_table(quarterly, max_rows=8)

            # Detected patterns
            if 'patterns' in content and content['patterns']:
                self.pdf.ln(5)
                self.pdf.set_font('Arial', 'B', 12)
                self.pdf.cell(0, 8, 'Detected Patterns', 0, 1, 'L')
                self.pdf.ln(2)

                self.pdf.set_font('Arial', '', 10)
                for pattern in content['patterns']:
                    pattern_text = pattern.get('pattern', 'Unknown pattern')
                    # Calculate available width for bullet text
                    left_margin = self.pdf.l_margin
                    right_margin = self.pdf.r_margin
                    page_width = self.pdf.w
                    bullet_indent = 7
                    text_width = page_width - left_margin - right_margin - bullet_indent

                    x_pos = self.pdf.get_x()
                    y_pos = self.pdf.get_y()
                    self.pdf.cell(5, 6, chr(149), 0, 0, 'L')
                    self.pdf.set_x(left_margin + bullet_indent)
                    self.pdf.multi_cell(text_width, 6, pattern_text)

        # Recommendations
        if section.recommendations:
            self.pdf.ln(5)
            self.pdf.set_font('Arial', 'B', 12)
            self.pdf.cell(0, 8, 'Recommendations', 0, 1, 'L')
            self.pdf.ln(2)

            self.pdf.set_font('Arial', '', 10)
            for rec in section.recommendations:
                # Calculate available width for bullet text
                left_margin = self.pdf.l_margin
                right_margin = self.pdf.r_margin
                page_width = self.pdf.w
                bullet_indent = 7
                text_width = page_width - left_margin - right_margin - bullet_indent

                x_pos = self.pdf.get_x()
                y_pos = self.pdf.get_y()
                self.pdf.cell(5, 6, chr(149), 0, 0, 'L')
                self.pdf.set_x(left_margin + bullet_indent)
                self.pdf.multi_cell(text_width, 6, str(rec) if rec else '')

    def _add_vendor_section(self, section: ReportSection) -> None:
        """
        Specialized renderer for vendor performance section.

        Renders vendor performance table (top 15) with cost, efficiency, and quality metrics.

        Args:
            section: ReportSection with vendor analysis content
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

        # Extract content
        content = section.content

        if isinstance(content, dict):
            # Top vendors table
            if 'top_vendors' in content and isinstance(content['top_vendors'], pd.DataFrame):
                vendors = content['top_vendors']
                if not vendors.empty:
                    self.pdf.set_font('Arial', 'B', 12)
                    self.pdf.cell(0, 8, 'Top Vendors by Cost', 0, 1, 'L')
                    self.pdf.ln(2)

                    # Define column widths
                    col_widths = {
                        'contractor': 50,
                        'total_cost': 30,
                        'avg_cost_per_wo': 30,
                        'work_order_count': 25,
                        'avg_duration_days': 25
                    }

                    # Header row
                    self.pdf.set_font('Arial', 'B', 8)
                    self.pdf.set_fill_color(*self.HEADER_COLOR)
                    self.pdf.set_text_color(255, 255, 255)

                    col_labels = {
                        'contractor': 'Contractor',
                        'total_cost': 'Total Cost',
                        'avg_cost_per_wo': 'Avg Cost/WO',
                        'work_order_count': 'WO Count',
                        'avg_duration_days': 'Avg Duration'
                    }

                    for col in vendors.columns:
                        if col in col_widths:
                            label = col_labels.get(col, col)
                            self.pdf.cell(col_widths[col], 7, label, 1, 0, 'C', True)
                    self.pdf.ln()

                    # Data rows (top 15)
                    self.pdf.set_font('Arial', '', 8)
                    self.pdf.set_text_color(0, 0, 0)

                    for idx, row in vendors.head(15).iterrows():
                        # Alternating row colors
                        if idx % 2 == 0:
                            self.pdf.set_fill_color(*self.ALT_ROW_COLOR)
                            fill = True
                        else:
                            fill = False

                        for col in vendors.columns:
                            if col in col_widths:
                                value = str(row[col])
                                # Truncate long values
                                max_len = int(col_widths[col] / 2)
                                if len(value) > max_len:
                                    value = value[:max_len-3] + '...'
                                self.pdf.cell(col_widths[col], 6, value, 1, 0, 'L', fill)
                        self.pdf.ln()

        # Recommendations
        if section.recommendations:
            self.pdf.ln(5)
            self.pdf.set_font('Arial', 'B', 12)
            self.pdf.cell(0, 8, 'Recommendations', 0, 1, 'L')
            self.pdf.ln(2)

            self.pdf.set_font('Arial', '', 10)
            for rec in section.recommendations:
                # Calculate available width for bullet text
                left_margin = self.pdf.l_margin
                right_margin = self.pdf.r_margin
                page_width = self.pdf.w
                bullet_indent = 7
                text_width = page_width - left_margin - right_margin - bullet_indent

                x_pos = self.pdf.get_x()
                y_pos = self.pdf.get_y()
                self.pdf.cell(5, 6, chr(149), 0, 0, 'L')
                self.pdf.set_x(left_margin + bullet_indent)
                self.pdf.multi_cell(text_width, 6, str(rec) if rec else '')

    def _add_failure_section(self, section: ReportSection) -> None:
        """
        Specialized renderer for failure pattern analysis section.

        Renders high-impact patterns table (top 20) with occurrences, costs, and affected equipment.

        Args:
            section: ReportSection with failure pattern analysis content
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

        # Extract content
        content = section.content

        if isinstance(content, dict):
            # High-impact patterns table
            if 'high_impact_patterns' in content and isinstance(content['high_impact_patterns'], pd.DataFrame):
                patterns = content['high_impact_patterns']
                if not patterns.empty:
                    self.pdf.set_font('Arial', 'B', 12)
                    self.pdf.cell(0, 8, 'High-Impact Failure Patterns (Top 20)', 0, 1, 'L')
                    self.pdf.ln(2)

                    # Define column widths
                    col_widths = {
                        'pattern': 70,
                        'occurrences': 25,
                        'total_cost': 30,
                        'avg_cost': 30,
                        'equipment_affected': 25
                    }

                    # Header row
                    self.pdf.set_font('Arial', 'B', 8)
                    self.pdf.set_fill_color(*self.HEADER_COLOR)
                    self.pdf.set_text_color(255, 255, 255)

                    col_labels = {
                        'pattern': 'Pattern',
                        'occurrences': 'Occurrences',
                        'total_cost': 'Total Cost',
                        'avg_cost': 'Avg Cost',
                        'equipment_affected': 'Equipment'
                    }

                    for col in patterns.columns:
                        if col in col_widths:
                            label = col_labels.get(col, col)
                            self.pdf.cell(col_widths[col], 7, label, 1, 0, 'C', True)
                    self.pdf.ln()

                    # Data rows (top 20)
                    self.pdf.set_font('Arial', '', 8)
                    self.pdf.set_text_color(0, 0, 0)

                    for idx, row in patterns.head(20).iterrows():
                        # Alternating row colors
                        if idx % 2 == 0:
                            self.pdf.set_fill_color(*self.ALT_ROW_COLOR)
                            fill = True
                        else:
                            fill = False

                        for col in patterns.columns:
                            if col in col_widths:
                                value = str(row[col])
                                # Truncate long values
                                max_len = int(col_widths[col] / 2)
                                if len(value) > max_len:
                                    value = value[:max_len-3] + '...'
                                self.pdf.cell(col_widths[col], 6, value, 1, 0, 'L', fill)
                        self.pdf.ln()

        # Recommendations
        if section.recommendations:
            self.pdf.ln(5)
            self.pdf.set_font('Arial', 'B', 12)
            self.pdf.cell(0, 8, 'Recommendations', 0, 1, 'L')
            self.pdf.ln(2)

            self.pdf.set_font('Arial', '', 10)
            for rec in section.recommendations:
                # Calculate available width for bullet text
                left_margin = self.pdf.l_margin
                right_margin = self.pdf.r_margin
                page_width = self.pdf.w
                bullet_indent = 7
                text_width = page_width - left_margin - right_margin - bullet_indent

                x_pos = self.pdf.get_x()
                y_pos = self.pdf.get_y()
                self.pdf.cell(5, 6, chr(149), 0, 0, 'L')
                self.pdf.set_x(left_margin + bullet_indent)
                self.pdf.multi_cell(text_width, 6, str(rec) if rec else '')

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
                # Calculate available width for bullet text
                left_margin = self.pdf.l_margin
                right_margin = self.pdf.r_margin
                page_width = self.pdf.w
                bullet_indent = 7
                text_width = page_width - left_margin - right_margin - bullet_indent

                x_pos = self.pdf.get_x()
                y_pos = self.pdf.get_y()
                self.pdf.cell(5, 6, chr(149), 0, 0, 'L')  # Bullet character
                self.pdf.set_x(left_margin + bullet_indent)
                self.pdf.multi_cell(text_width, 6, str(rec) if rec else '')

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
                    # Calculate available width for bullet text
                    left_margin = self.pdf.l_margin
                    right_margin = self.pdf.r_margin
                    page_width = self.pdf.w
                    bullet_indent = 7
                    text_width = page_width - left_margin - right_margin - bullet_indent

                    x_pos = self.pdf.get_x()
                    y_pos = self.pdf.get_y()
                    self.pdf.cell(5, 6, chr(149), 0, 0, 'L')
                    self.pdf.set_x(left_margin + bullet_indent)
                    self.pdf.multi_cell(text_width, 6, str(rec) if rec else '')

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
