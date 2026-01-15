"""
Report builder module for consolidating analysis results.

Purpose: Aggregate findings from all analysis modules (equipment, seasonal,
vendor, failure patterns) into a unified report structure ready for rendering.
"""

import pandas as pd
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Union, List, Dict, Any


@dataclass
class ReportSection:
    """
    Represents a section of a report with content and recommendations.

    Attributes:
        title: Section title (e.g., "Equipment Analysis")
        content: Section data (DataFrame or dict with structured data)
        summary_text: Brief summary of key findings
        recommendations: List of actionable recommendations
    """
    title: str
    content: Union[pd.DataFrame, Dict[str, Any]]
    summary_text: str
    recommendations: List[str] = field(default_factory=list)


@dataclass
class Report:
    """
    Complete report with metadata, sections, and executive summary.

    Attributes:
        metadata: Report metadata (dates, totals, etc.)
        sections: List of ReportSection objects
        executive_summary: High-level overview of key findings
    """
    metadata: Dict[str, Any]
    sections: List[ReportSection] = field(default_factory=list)
    executive_summary: str = ""


class ReportBuilder:
    """
    Builds comprehensive reports by aggregating analysis results.

    Orchestrates report generation by:
    1. Loading and preparing input data
    2. Running analysis modules
    3. Extracting key findings
    4. Consolidating into structured Report object
    """

    def __init__(self, input_file: str):
        """
        Initialize ReportBuilder with input data file.

        Args:
            input_file: Path to work order data file (CSV or Excel)
        """
        self.input_file = input_file
        self.df: Optional[pd.DataFrame] = None

    def _load_data(self) -> pd.DataFrame:
        """
        Load work order data from input file.

        Returns:
            DataFrame with loaded work order data

        Raises:
            FileNotFoundError: If input file does not exist
            ValueError: If file format is not supported
        """
        # Import data loader from pipeline
        from src.pipeline.data_loader import load_work_orders

        # Load data using existing pipeline
        self.df = load_work_orders(self.input_file)
        return self.df

    def _calculate_metadata(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Calculate report metadata from loaded data.

        Args:
            df: DataFrame with work order data

        Returns:
            Dictionary with metadata:
            - generated_date: Report generation timestamp
            - data_period_start: Earliest date in data
            - data_period_end: Latest date in data
            - total_records: Total work order count
            - total_cost: Total cost across all work orders
            - date_range_days: Number of days covered by data
        """
        metadata = {
            'generated_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'total_records': len(df)
        }

        # Calculate date range
        if 'Complete_Date' in df.columns:
            valid_dates = df['Complete_Date'].dropna()
            if len(valid_dates) > 0:
                metadata['data_period_start'] = valid_dates.min().strftime('%Y-%m-%d')
                metadata['data_period_end'] = valid_dates.max().strftime('%Y-%m-%d')
                metadata['date_range_days'] = (valid_dates.max() - valid_dates.min()).days
            else:
                metadata['data_period_start'] = 'N/A'
                metadata['data_period_end'] = 'N/A'
                metadata['date_range_days'] = 0
        else:
            metadata['data_period_start'] = 'N/A'
            metadata['data_period_end'] = 'N/A'
            metadata['date_range_days'] = 0

        # Calculate total cost
        if 'PO_AMOUNT' in df.columns:
            metadata['total_cost'] = df['PO_AMOUNT'].sum()
        else:
            metadata['total_cost'] = 0

        return metadata

    def _create_section(
        self,
        title: str,
        content: Union[pd.DataFrame, Dict[str, Any]],
        summary: str,
        recommendations: Optional[List[str]] = None
    ) -> ReportSection:
        """
        Helper to create a ReportSection.

        Args:
            title: Section title
            content: Section data (DataFrame or dict)
            summary: Summary text describing key findings
            recommendations: List of actionable recommendations

        Returns:
            ReportSection object
        """
        if recommendations is None:
            recommendations = []

        return ReportSection(
            title=title,
            content=content,
            summary_text=summary,
            recommendations=recommendations
        )

    def _build_executive_summary(self, all_sections: List[ReportSection]) -> str:
        """
        Aggregate top metrics across all sections into executive summary.

        Args:
            all_sections: List of all report sections

        Returns:
            Executive summary text with key findings across all analyses
        """
        summary_parts = []

        # Count sections
        summary_parts.append(f"Analysis completed across {len(all_sections)} areas:\n")

        # Extract key points from each section
        for section in all_sections:
            summary_parts.append(f"\n{section.title}:")
            summary_parts.append(f"  {section.summary_text}")

            # Include top recommendation if available
            if section.recommendations:
                summary_parts.append(f"  → {section.recommendations[0]}")

        return '\n'.join(summary_parts)

    def build_report(self) -> Report:
        """
        Orchestrate full report generation.

        Process:
        1. Load data
        2. Calculate metadata
        3. Run all analysis modules
        4. Build sections
        5. Generate executive summary
        6. Return complete Report object

        Returns:
            Complete Report object with all sections and metadata
        """
        # Load data
        df = self._load_data()

        # Calculate metadata
        metadata = self._calculate_metadata(df)

        # Initialize report
        report = Report(metadata=metadata)

        # TODO: Add analysis sections in Task 2
        # - add_equipment_analysis()
        # - add_seasonal_analysis()
        # - add_vendor_analysis()
        # - add_failure_analysis()

        # Build executive summary
        report.executive_summary = self._build_executive_summary(report.sections)

        return report
