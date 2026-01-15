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
        # Will be implemented in Task 2
        pass

    def _add_seasonal_sheet(self, workbook: xlsxwriter.Workbook,
                           section: ReportSection) -> None:
        """
        Add seasonal analysis sheet with monthly/quarterly tables.

        Args:
            workbook: xlsxwriter Workbook object
            section: ReportSection with seasonal analysis data
        """
        # Will be implemented in Task 2
        pass

    def _add_vendor_sheet(self, workbook: xlsxwriter.Workbook,
                         section: ReportSection) -> None:
        """
        Add vendor performance sheet with metrics.

        Args:
            workbook: xlsxwriter Workbook object
            section: ReportSection with vendor analysis data
        """
        # Will be implemented in Task 2
        pass

    def _add_failure_sheet(self, workbook: xlsxwriter.Workbook,
                          section: ReportSection) -> None:
        """
        Add failure patterns sheet with impact scores.

        Args:
            workbook: xlsxwriter Workbook object
            section: ReportSection with failure analysis data
        """
        # Will be implemented in Task 2
        pass

    def _add_recommendations_sheet(self, workbook: xlsxwriter.Workbook,
                                  all_sections: list) -> None:
        """
        Add consolidated recommendations sheet from all sections.

        Args:
            workbook: xlsxwriter Workbook object
            all_sections: List of all ReportSection objects
        """
        # Will be implemented in Task 2
        pass
