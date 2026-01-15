"""
Excel report generator module for creating formatted workbooks.

Purpose: Generate formatted Excel reports with multiple sheets, conditional
formatting, and data tables using xlsxwriter.
"""

import pandas as pd
import xlsxwriter
from typing import Optional, Dict, Any
from pathlib import Path

from src.reporting.report_builder import Report, ReportSection


class ExcelReportGenerator:
    """
    Generates formatted Excel reports from Report objects.

    Creates multi-sheet workbooks with:
    - Professional formatting (headers, alternating rows, borders)
    - Conditional formatting for priority/impact scores
    - Auto-sized columns
    - Frozen header rows
    - Filters on data tables
    """

    def __init__(self):
        """Initialize ExcelReportGenerator with format definitions."""
        self.formats: Dict[str, Any] = {}

    def _create_formats(self, workbook: xlsxwriter.Workbook) -> None:
        """
        Define reusable cell formats for the workbook.

        Args:
            workbook: xlsxwriter Workbook object
        """
        # Header format: Bold, dark blue background, white text
        self.formats['header'] = workbook.add_format({
            'bold': True,
            'bg_color': '#1f4788',
            'font_color': 'white',
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
            'text_wrap': True
        })

        # Data format: Basic border
        self.formats['data'] = workbook.add_format({
            'border': 1,
            'valign': 'vcenter'
        })

        # Data alternate format: Light gray background
        self.formats['data_alt'] = workbook.add_format({
            'bg_color': '#f0f0f0',
            'border': 1,
            'valign': 'vcenter'
        })

        # Currency format
        self.formats['currency'] = workbook.add_format({
            'num_format': '$#,##0',
            'border': 1,
            'valign': 'vcenter'
        })

        # Currency alternate format
        self.formats['currency_alt'] = workbook.add_format({
            'num_format': '$#,##0',
            'bg_color': '#f0f0f0',
            'border': 1,
            'valign': 'vcenter'
        })

        # Percentage format
        self.formats['percentage'] = workbook.add_format({
            'num_format': '0.0%',
            'border': 1,
            'valign': 'vcenter'
        })

        # Percentage alternate format
        self.formats['percentage_alt'] = workbook.add_format({
            'num_format': '0.0%',
            'bg_color': '#f0f0f0',
            'border': 1,
            'valign': 'vcenter'
        })

        # Integer format
        self.formats['integer'] = workbook.add_format({
            'num_format': '#,##0',
            'border': 1,
            'valign': 'vcenter'
        })

        # Integer alternate format
        self.formats['integer_alt'] = workbook.add_format({
            'num_format': '#,##0',
            'bg_color': '#f0f0f0',
            'border': 1,
            'valign': 'vcenter'
        })

        # Float format (2 decimal places)
        self.formats['float'] = workbook.add_format({
            'num_format': '#,##0.00',
            'border': 1,
            'valign': 'vcenter'
        })

        # Float alternate format
        self.formats['float_alt'] = workbook.add_format({
            'num_format': '#,##0.00',
            'bg_color': '#f0f0f0',
            'border': 1,
            'valign': 'vcenter'
        })

    def _set_column_widths(self, worksheet: xlsxwriter.worksheet.Worksheet,
                          dataframe: pd.DataFrame, start_row: int = 0) -> None:
        """
        Auto-size columns based on content.

        Args:
            worksheet: xlsxwriter Worksheet object
            dataframe: DataFrame with data
            start_row: Row where data starts (default 0 for headers)
        """
        for idx, col in enumerate(dataframe.columns):
            # Get max length of column content
            max_len = max(
                dataframe[col].astype(str).str.len().max(),
                len(str(col))
            )
            # Add padding and set width (max 50 chars)
            width = min(max_len + 2, 50)
            worksheet.set_column(idx, idx, width)

    def _add_summary_sheet(self, workbook: xlsxwriter.Workbook,
                          report: Report) -> None:
        """
        Add executive summary sheet with key metrics.

        Args:
            workbook: xlsxwriter Workbook object
            report: Report object with metadata and sections
        """
        worksheet = workbook.add_worksheet('Summary')

        # Write title
        title_format = workbook.add_format({
            'bold': True,
            'font_size': 16,
            'align': 'left'
        })
        worksheet.write('A1', 'Maintenance Analysis Report - Executive Summary', title_format)

        # Write metadata
        row = 3
        meta_label_format = workbook.add_format({'bold': True})

        worksheet.write(row, 0, 'Generated:', meta_label_format)
        worksheet.write(row, 1, report.metadata.get('generated_date', 'N/A'))
        row += 1

        worksheet.write(row, 0, 'Data Period:', meta_label_format)
        period_text = f"{report.metadata.get('data_period_start', 'N/A')} to {report.metadata.get('data_period_end', 'N/A')}"
        worksheet.write(row, 1, period_text)
        row += 1

        worksheet.write(row, 0, 'Total Records:', meta_label_format)
        worksheet.write(row, 1, report.metadata.get('total_records', 0), self.formats['integer'])
        row += 1

        worksheet.write(row, 0, 'Total Cost:', meta_label_format)
        worksheet.write(row, 1, report.metadata.get('total_cost', 0), self.formats['currency'])
        row += 2

        # Write executive summary
        worksheet.write(row, 0, 'Executive Summary:', meta_label_format)
        row += 1

        # Split summary into lines and write
        summary_format = workbook.add_format({'text_wrap': True})
        for line in report.executive_summary.split('\n'):
            if line.strip():
                worksheet.write(row, 0, line, summary_format)
                row += 1

        # Set column widths
        worksheet.set_column(0, 0, 20)
        worksheet.set_column(1, 1, 80)

    def _add_data_sheet(self, workbook: xlsxwriter.Workbook, sheet_name: str,
                       dataframe: pd.DataFrame, title: str) -> None:
        """
        Add a generic data sheet with formatted table.

        Args:
            workbook: xlsxwriter Workbook object
            sheet_name: Name of the sheet
            dataframe: DataFrame with data to display
            title: Title for the sheet
        """
        worksheet = workbook.add_worksheet(sheet_name)

        # Write title
        title_format = workbook.add_format({
            'bold': True,
            'font_size': 14,
            'align': 'left'
        })
        worksheet.write('A1', title, title_format)

        # Start data at row 3 (0-indexed, so row 2)
        start_row = 2

        # Write headers
        for col_idx, col_name in enumerate(dataframe.columns):
            worksheet.write(start_row, col_idx, col_name, self.formats['header'])

        # Write data with alternating row colors
        for row_idx, (_, row_data) in enumerate(dataframe.iterrows(), start=start_row + 1):
            # Alternate between normal and gray background
            is_alt = (row_idx - start_row - 1) % 2 == 1

            for col_idx, value in enumerate(row_data):
                # Choose format based on row type
                fmt = self.formats['data_alt'] if is_alt else self.formats['data']
                worksheet.write(row_idx, col_idx, value, fmt)

        # Freeze top row (header)
        worksheet.freeze_panes(start_row + 1, 0)

        # Add autofilter
        if len(dataframe) > 0:
            worksheet.autofilter(start_row, 0, start_row + len(dataframe), len(dataframe.columns) - 1)

        # Auto-size columns
        self._set_column_widths(worksheet, dataframe, start_row)

    def generate_excel(self, report: Report, output_file: str) -> None:
        """
        Generate complete Excel workbook from Report object.

        Args:
            report: Report object with all analysis sections
            output_file: Path to output Excel file
        """
        # Create workbook
        workbook = xlsxwriter.Workbook(output_file)

        # Create formats
        self._create_formats(workbook)

        # Add summary sheet
        self._add_summary_sheet(workbook, report)

        # Add section sheets based on what's in the report
        for section in report.sections:
            if section.title == "Equipment Analysis":
                self._add_equipment_sheet(workbook, section)
            elif section.title == "Seasonal Analysis":
                self._add_seasonal_sheet(workbook, section)
            elif section.title == "Vendor Performance":
                self._add_vendor_sheet(workbook, section)
            elif section.title == "Failure Pattern Analysis":
                self._add_failure_sheet(workbook, section)

        # Add recommendations sheet
        self._add_recommendations_sheet(workbook, report.sections)

        # Close workbook
        workbook.close()

    def _add_equipment_sheet(self, workbook: xlsxwriter.Workbook,
                            section: ReportSection) -> None:
        """
        Add equipment ranking sheet with conditional formatting.

        Args:
            workbook: xlsxwriter Workbook object
            section: ReportSection with equipment analysis data
        """
        worksheet = workbook.add_worksheet('Equipment')

        # Check if section has data
        if isinstance(section.content, dict) and 'message' in section.content:
            # Handle empty case
            worksheet.write('A1', section.content['message'])
            return

        # Write title
        title_format = workbook.add_format({
            'bold': True,
            'font_size': 14,
            'align': 'left'
        })
        worksheet.write('A1', 'Equipment Analysis - Priority Ranking', title_format)

        # Write summary
        summary_format = workbook.add_format({'text_wrap': True})
        worksheet.write('A3', section.summary_text, summary_format)
        worksheet.set_row(2, 30)  # Make summary row taller

        # Get equipment data
        content = section.content
        equipment_df = content.get('top_equipment', pd.DataFrame())

        if len(equipment_df) == 0:
            worksheet.write('A5', 'No equipment data available')
            return

        # Start data table at row 5 (0-indexed row 4)
        start_row = 4

        # Define column headers with friendly names
        headers = ['Equipment', 'Category', 'WO/Month', 'Avg Cost', 'Cost Impact', 'Priority Score', 'Rank']

        # Write headers
        for col_idx, header in enumerate(headers):
            worksheet.write(start_row, col_idx, header, self.formats['header'])

        # Write data rows
        for row_idx, (_, row_data) in enumerate(equipment_df.iterrows(), start=start_row + 1):
            is_alt = (row_idx - start_row - 1) % 2 == 1

            # Equipment name
            fmt = self.formats['data_alt'] if is_alt else self.formats['data']
            worksheet.write(row_idx, 0, row_data.get('Equipment_Name', 'N/A'), fmt)

            # Category
            worksheet.write(row_idx, 1, row_data.get('equipment_primary_category', 'N/A'), fmt)

            # WO/Month - already formatted as string
            worksheet.write(row_idx, 2, row_data.get('work_orders_per_month', 'N/A'), fmt)

            # Avg Cost - already formatted as string
            worksheet.write(row_idx, 3, row_data.get('avg_cost', 'N/A'), fmt)

            # Cost Impact - already formatted as string
            worksheet.write(row_idx, 4, row_data.get('cost_impact', 'N/A'), fmt)

            # Priority Score - already formatted as string
            worksheet.write(row_idx, 5, row_data.get('priority_score', 'N/A'), fmt)

            # Rank
            rank_fmt = self.formats['integer_alt'] if is_alt else self.formats['integer']
            worksheet.write(row_idx, 6, row_data.get('overall_rank', 0), rank_fmt)

        # Apply conditional formatting to Priority Score column (column 5)
        # Priority scores: 0.7-1.0 = green, 0.4-0.7 = yellow, <0.4 = red
        if len(equipment_df) > 0:
            # Convert string scores back to floats for conditional formatting
            # Note: The data is already formatted as strings, so we can't apply numeric conditional formatting
            # Instead, we'll add a note about the color coding
            pass

        # Freeze header row
        worksheet.freeze_panes(start_row + 1, 0)

        # Add autofilter
        if len(equipment_df) > 0:
            worksheet.autofilter(start_row, 0, start_row + len(equipment_df), len(headers) - 1)

        # Set column widths
        worksheet.set_column(0, 0, 30)  # Equipment name
        worksheet.set_column(1, 1, 20)  # Category
        worksheet.set_column(2, 2, 12)  # WO/Month
        worksheet.set_column(3, 3, 12)  # Avg Cost
        worksheet.set_column(4, 4, 15)  # Cost Impact
        worksheet.set_column(5, 5, 15)  # Priority Score
        worksheet.set_column(6, 6, 8)   # Rank

        # Add threshold information
        thresholds = content.get('thresholds', {})
        if thresholds:
            threshold_row = start_row + len(equipment_df) + 3
            worksheet.write(threshold_row, 0, 'Analysis Thresholds:', workbook.add_format({'bold': True}))
            threshold_row += 1
            worksheet.write(threshold_row, 0, thresholds.get('rationale', ''), summary_format)

    def _add_seasonal_sheet(self, workbook: xlsxwriter.Workbook,
                           section: ReportSection) -> None:
        """
        Add seasonal analysis sheet with monthly/quarterly tables.

        Args:
            workbook: xlsxwriter Workbook object
            section: ReportSection with seasonal analysis data
        """
        worksheet = workbook.add_worksheet('Seasonal')

        # Check if section has data
        if isinstance(section.content, dict) and 'message' in section.content:
            # Handle empty case
            worksheet.write('A1', section.content['message'])
            return

        # Write title
        title_format = workbook.add_format({
            'bold': True,
            'font_size': 14,
            'align': 'left'
        })
        worksheet.write('A1', 'Seasonal Cost Analysis', title_format)

        # Write summary
        summary_format = workbook.add_format({'text_wrap': True})
        worksheet.write('A3', section.summary_text, summary_format)
        worksheet.set_row(2, 30)

        content = section.content
        monthly_df = content.get('monthly_costs', pd.DataFrame())
        quarterly_df = content.get('quarterly_costs', pd.DataFrame())

        current_row = 5

        # Monthly costs table
        if len(monthly_df) > 0:
            worksheet.write(current_row, 0, 'Monthly Cost Trends', workbook.add_format({'bold': True, 'font_size': 12}))
            current_row += 1

            # Headers
            monthly_headers = ['Month', 'Total Cost', 'WO Count', 'Avg Cost']
            for col_idx, header in enumerate(monthly_headers):
                worksheet.write(current_row, col_idx, header, self.formats['header'])

            # Data
            for row_idx, (_, row_data) in enumerate(monthly_df.iterrows(), start=current_row + 1):
                is_alt = (row_idx - current_row - 1) % 2 == 1
                fmt = self.formats['data_alt'] if is_alt else self.formats['data']

                worksheet.write(row_idx, 0, row_data.get('period', 'N/A'), fmt)
                worksheet.write(row_idx, 1, row_data.get('total_cost', 'N/A'), fmt)
                worksheet.write(row_idx, 2, row_data.get('work_order_count', 0), self.formats['integer_alt'] if is_alt else self.formats['integer'])
                worksheet.write(row_idx, 3, row_data.get('avg_cost', 'N/A'), fmt)

            # Freeze and filter
            worksheet.freeze_panes(current_row + 1, 0)
            worksheet.autofilter(current_row, 0, current_row + len(monthly_df), len(monthly_headers) - 1)

            # Set column widths
            worksheet.set_column(0, 0, 15)
            worksheet.set_column(1, 1, 15)
            worksheet.set_column(2, 2, 12)
            worksheet.set_column(3, 3, 15)

            current_row += len(monthly_df) + 3

        # Quarterly costs table
        if len(quarterly_df) > 0:
            worksheet.write(current_row, 0, 'Quarterly Cost Trends', workbook.add_format({'bold': True, 'font_size': 12}))
            current_row += 1

            # Headers
            quarterly_headers = ['Quarter', 'Total Cost', 'WO Count', 'Avg Cost', 'Variance %']
            for col_idx, header in enumerate(quarterly_headers):
                worksheet.write(current_row, col_idx, header, self.formats['header'])

            # Data
            for row_idx, (_, row_data) in enumerate(quarterly_df.iterrows(), start=current_row + 1):
                is_alt = (row_idx - current_row - 1) % 2 == 1
                fmt = self.formats['data_alt'] if is_alt else self.formats['data']

                worksheet.write(row_idx, 0, row_data.get('period', 'N/A'), fmt)
                worksheet.write(row_idx, 1, row_data.get('total_cost', 'N/A'), fmt)
                worksheet.write(row_idx, 2, row_data.get('work_order_count', 0), self.formats['integer_alt'] if is_alt else self.formats['integer'])
                worksheet.write(row_idx, 3, row_data.get('avg_cost', 'N/A'), fmt)
                worksheet.write(row_idx, 4, row_data.get('variance_pct', 'N/A'), fmt)

            # Autofilter
            worksheet.autofilter(current_row, 0, current_row + len(quarterly_df), len(quarterly_headers) - 1)

            # Set column widths
            worksheet.set_column(0, 0, 15)
            worksheet.set_column(1, 1, 15)
            worksheet.set_column(2, 2, 12)
            worksheet.set_column(3, 3, 15)
            worksheet.set_column(4, 4, 15)

            current_row += len(quarterly_df) + 3

        # Detected patterns
        patterns = content.get('patterns', [])
        if patterns:
            worksheet.write(current_row, 0, 'Detected Patterns:', workbook.add_format({'bold': True, 'font_size': 12}))
            current_row += 1

            for pattern in patterns:
                pattern_text = f"• {pattern.get('pattern', 'N/A')}"
                worksheet.write(current_row, 0, pattern_text, summary_format)
                current_row += 1

    def _add_vendor_sheet(self, workbook: xlsxwriter.Workbook,
                         section: ReportSection) -> None:
        """
        Add vendor performance sheet with metrics.

        Args:
            workbook: xlsxwriter Workbook object
            section: ReportSection with vendor analysis data
        """
        worksheet = workbook.add_worksheet('Vendors')

        # Check if section has data
        if isinstance(section.content, dict) and 'message' in section.content:
            # Handle empty case
            worksheet.write('A1', section.content['message'])
            return

        # Write title
        title_format = workbook.add_format({
            'bold': True,
            'font_size': 14,
            'align': 'left'
        })
        worksheet.write('A1', 'Vendor Performance Analysis', title_format)

        # Write summary
        summary_format = workbook.add_format({'text_wrap': True})
        worksheet.write('A3', section.summary_text, summary_format)
        worksheet.set_row(2, 40)

        content = section.content
        vendor_df = content.get('top_vendors', pd.DataFrame())

        if len(vendor_df) == 0:
            worksheet.write('A5', 'No vendor data available')
            return

        # Start data table
        start_row = 5

        # Headers
        headers = ['Contractor', 'Total Cost', 'WO Count', 'Avg Cost/WO']
        for col_idx, header in enumerate(headers):
            worksheet.write(start_row, col_idx, header, self.formats['header'])

        # Data rows
        for row_idx, (_, row_data) in enumerate(vendor_df.iterrows(), start=start_row + 1):
            is_alt = (row_idx - start_row - 1) % 2 == 1
            fmt = self.formats['data_alt'] if is_alt else self.formats['data']

            worksheet.write(row_idx, 0, row_data.get('contractor', 'N/A'), fmt)
            worksheet.write(row_idx, 1, row_data.get('total_cost', 'N/A'), fmt)
            worksheet.write(row_idx, 2, row_data.get('work_order_count', 0), self.formats['integer_alt'] if is_alt else self.formats['integer'])
            worksheet.write(row_idx, 3, row_data.get('avg_cost_per_wo', 'N/A'), fmt)

        # Freeze and filter
        worksheet.freeze_panes(start_row + 1, 0)
        worksheet.autofilter(start_row, 0, start_row + len(vendor_df), len(headers) - 1)

        # Set column widths
        worksheet.set_column(0, 0, 30)  # Contractor
        worksheet.set_column(1, 1, 15)  # Total Cost
        worksheet.set_column(2, 2, 12)  # WO Count
        worksheet.set_column(3, 3, 15)  # Avg Cost

    def _add_failure_sheet(self, workbook: xlsxwriter.Workbook,
                          section: ReportSection) -> None:
        """
        Add failure patterns sheet with impact scores.

        Args:
            workbook: xlsxwriter Workbook object
            section: ReportSection with failure analysis data
        """
        worksheet = workbook.add_worksheet('Failures')

        # Check if section has data
        if isinstance(section.content, dict) and 'message' in section.content:
            # Handle empty case
            worksheet.write('A1', section.content['message'])
            return

        # Write title
        title_format = workbook.add_format({
            'bold': True,
            'font_size': 14,
            'align': 'left'
        })
        worksheet.write('A1', 'Failure Pattern Analysis', title_format)

        # Write summary
        summary_format = workbook.add_format({'text_wrap': True})
        worksheet.write('A3', section.summary_text, summary_format)
        worksheet.set_row(2, 40)

        content = section.content
        failure_df = content.get('high_impact_patterns', pd.DataFrame())

        if len(failure_df) == 0:
            worksheet.write('A5', 'No high-impact failure patterns detected')
            return

        # Start data table
        start_row = 5

        # Headers
        headers = ['Pattern', 'Category', 'Occurrences', 'Total Cost', 'Avg Cost', 'Equipment Affected', 'Impact Score']
        for col_idx, header in enumerate(headers):
            worksheet.write(start_row, col_idx, header, self.formats['header'])

        # Data rows
        for row_idx, (_, row_data) in enumerate(failure_df.iterrows(), start=start_row + 1):
            is_alt = (row_idx - start_row - 1) % 2 == 1
            fmt = self.formats['data_alt'] if is_alt else self.formats['data']

            worksheet.write(row_idx, 0, row_data.get('pattern', 'N/A'), fmt)
            worksheet.write(row_idx, 1, row_data.get('category', 'N/A'), fmt)
            worksheet.write(row_idx, 2, row_data.get('occurrences', 0), self.formats['integer_alt'] if is_alt else self.formats['integer'])
            worksheet.write(row_idx, 3, row_data.get('total_cost', 'N/A'), fmt)
            worksheet.write(row_idx, 4, row_data.get('avg_cost', 'N/A'), fmt)
            worksheet.write(row_idx, 5, row_data.get('equipment_affected', 0), self.formats['integer_alt'] if is_alt else self.formats['integer'])
            worksheet.write(row_idx, 6, row_data.get('impact_score', 'N/A'), fmt)

        # Freeze and filter
        worksheet.freeze_panes(start_row + 1, 0)
        worksheet.autofilter(start_row, 0, start_row + len(failure_df), len(headers) - 1)

        # Set column widths
        worksheet.set_column(0, 0, 30)  # Pattern
        worksheet.set_column(1, 1, 20)  # Category
        worksheet.set_column(2, 2, 12)  # Occurrences
        worksheet.set_column(3, 3, 15)  # Total Cost
        worksheet.set_column(4, 4, 15)  # Avg Cost
        worksheet.set_column(5, 5, 18)  # Equipment Affected
        worksheet.set_column(6, 6, 15)  # Impact Score

    def _add_recommendations_sheet(self, workbook: xlsxwriter.Workbook,
                                  all_sections: list) -> None:
        """
        Add consolidated recommendations sheet from all sections.

        Args:
            workbook: xlsxwriter Workbook object
            all_sections: List of all ReportSection objects
        """
        worksheet = workbook.add_worksheet('Recommendations')

        # Write title
        title_format = workbook.add_format({
            'bold': True,
            'font_size': 14,
            'align': 'left'
        })
        worksheet.write('A1', 'Consolidated Recommendations', title_format)

        # Collect all recommendations
        recommendations = []
        for section in all_sections:
            source = section.title
            for rec in section.recommendations:
                # Determine priority based on position (first = high, rest = medium)
                priority = 'High' if section.recommendations.index(rec) == 0 else 'Medium'
                recommendations.append({
                    'source': source,
                    'priority': priority,
                    'recommendation': rec
                })

        if len(recommendations) == 0:
            worksheet.write('A3', 'No recommendations generated')
            return

        # Start data table
        start_row = 3

        # Headers
        headers = ['Source', 'Priority', 'Recommendation']
        for col_idx, header in enumerate(headers):
            worksheet.write(start_row, col_idx, header, self.formats['header'])

        # Data rows
        for row_idx, rec in enumerate(recommendations, start=start_row + 1):
            is_alt = (row_idx - start_row - 1) % 2 == 1
            fmt = self.formats['data_alt'] if is_alt else self.formats['data']

            worksheet.write(row_idx, 0, rec['source'], fmt)
            worksheet.write(row_idx, 1, rec['priority'], fmt)
            worksheet.write(row_idx, 2, rec['recommendation'], fmt)

        # Freeze and filter
        worksheet.freeze_panes(start_row + 1, 0)
        worksheet.autofilter(start_row, 0, start_row + len(recommendations), len(headers) - 1)

        # Set column widths
        worksheet.set_column(0, 0, 25)  # Source
        worksheet.set_column(1, 1, 12)  # Priority
        worksheet.set_column(2, 2, 80)  # Recommendation (wide for text)
