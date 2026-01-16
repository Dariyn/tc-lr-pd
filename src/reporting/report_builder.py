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
        Load and prepare work order data from input file.

        Returns:
            DataFrame with cleaned and categorized work order data

        Raises:
            FileNotFoundError: If input file does not exist
            ValueError: If file format is not supported
        """
        # Import pipeline steps to ensure required derived fields are present
        from src.pipeline.data_loader import load_work_orders
        from src.pipeline.data_cleaner import clean_work_orders
        from src.pipeline.categorizer import categorize_work_orders

        df = load_work_orders(self.input_file)
        df = clean_work_orders(df)
        df = categorize_work_orders(df)

        self.df = df
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

        # Calculate date range - prefer create_date_yyyymmdd (when repair was requested)
        valid_dates = None
        date_col = None

        for col in ['create_date_yyyymmdd', 'Create_Date', 'Complete_Date']:
            if col in df.columns:
                valid_dates = df[col].dropna()
                if len(valid_dates) > 0:
                    date_col = col
                    break

        if valid_dates is not None and len(valid_dates) > 0:
            min_date = valid_dates.min()
            max_date = valid_dates.max()
            metadata['data_period_start'] = min_date.strftime('%Y-%m-%d')
            metadata['data_period_end'] = max_date.strftime('%Y-%m-%d')
            # Calculate days, ensuring at least 1 day if dates exist
            days_diff = (max_date - min_date).days
            metadata['date_range_days'] = max(1, days_diff)  # At least 1 day if we have data
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

    def add_equipment_analysis(self) -> ReportSection:
        """
        Run equipment ranking analysis and create equipment section.

        Analyzes equipment frequency, cost impact, and outlier status to identify
        high-priority maintenance targets.

        Returns:
            ReportSection with equipment analysis results including:
            - Top 10 ranked equipment by priority score
            - Outlier detection thresholds
            - Count of consensus outliers

        Raises:
            ValueError: If data not loaded or required columns missing
        """
        if self.df is None:
            raise ValueError("Data not loaded. Call _load_data() first.")

        # Import analysis modules
        from src.analysis.frequency_analyzer import calculate_equipment_frequencies
        from src.analysis.outlier_detector import detect_outliers
        from src.analysis.equipment_ranker import rank_equipment, identify_thresholds

        # Run frequency analysis
        freq_df = calculate_equipment_frequencies(self.df)

        # Run outlier detection
        outlier_df = detect_outliers(freq_df)

        # Run ranking
        ranked_df = rank_equipment(outlier_df)

        # Handle edge case: no consensus outliers found
        if len(ranked_df) == 0:
            summary = "No consensus outliers detected. All equipment within normal operating ranges."
            content = {
                'message': 'No high-priority equipment identified',
                'total_equipment': len(freq_df),
                'outliers_detected': 0
            }
            recommendations = [
                "Continue monitoring equipment performance",
                "Review outlier detection thresholds if results seem unexpected"
            ]
            return self._create_section(
                title="Equipment Analysis",
                content=content,
                summary=summary,
                recommendations=recommendations
            )

        # Get thresholds
        thresholds = identify_thresholds(ranked_df)

        # Extract top 10 equipment
        top_equipment = ranked_df.head(10)[
            ['Equipment_Name', 'equipment_primary_category', 'work_orders_per_month',
             'avg_cost', 'cost_impact', 'priority_score', 'overall_rank']
        ].copy()

        # Format numbers for display
        top_equipment['work_orders_per_month'] = top_equipment['work_orders_per_month'].map('{:.2f}'.format)
        top_equipment['avg_cost'] = top_equipment['avg_cost'].map('${:,.0f}'.format)
        top_equipment['cost_impact'] = top_equipment['cost_impact'].map('${:,.0f}'.format)
        top_equipment['priority_score'] = top_equipment['priority_score'].map('{:.3f}'.format)

        # Build summary
        summary = (
            f"Identified {len(ranked_df)} consensus outliers from {len(freq_df)} equipment items. "
            f"Top priority: {ranked_df.iloc[0]['Equipment_Name']} "
            f"({ranked_df.iloc[0]['equipment_primary_category']}) with "
            f"{ranked_df.iloc[0]['work_orders_per_month']:.2f} WO/month and "
            f"${ranked_df.iloc[0]['cost_impact']:,.0f} cost impact."
        )

        # Build recommendations
        recommendations = [
            f"Focus on top 3 equipment items: {', '.join(ranked_df.head(3)['Equipment_Name'].tolist())}",
            thresholds['rationale']
        ]

        # Create content dict
        content = {
            'top_equipment': top_equipment,
            'total_equipment': len(freq_df),
            'consensus_outliers': len(ranked_df),
            'thresholds': thresholds
        }

        return self._create_section(
            title="Equipment Analysis",
            content=content,
            summary=summary,
            recommendations=recommendations
        )

    def add_seasonal_analysis(self) -> ReportSection:
        """
        Run seasonal cost analysis and create seasonal section.

        Analyzes cost patterns across months, quarters, and seasons to identify
        recurring high-cost periods.

        Returns:
            ReportSection with seasonal analysis results including:
            - Monthly/quarterly cost trends
            - Detected seasonal patterns
            - Peak period identification

        Raises:
            ValueError: If data not loaded or required columns missing
        """
        if self.df is None:
            raise ValueError("Data not loaded. Call _load_data() first.")

        # Import seasonal analyzer
        from src.analysis.seasonal_analyzer import SeasonalAnalyzer

        analyzer = SeasonalAnalyzer()

        # Calculate monthly and quarterly costs
        monthly_costs = analyzer.calculate_monthly_costs(self.df)
        quarterly_costs = analyzer.calculate_quarterly_costs(self.df)

        # Handle edge case: insufficient data
        if len(monthly_costs) == 0 or len(quarterly_costs) == 0:
            summary = "Insufficient date/cost data for seasonal analysis."
            content = {
                'message': 'No valid date and cost data available',
                'monthly_data_points': len(monthly_costs),
                'quarterly_data_points': len(quarterly_costs)
            }
            recommendations = [
                "Ensure Complete_Date and PO_AMOUNT fields are populated",
                "Collect data over longer time period for pattern detection"
            ]
            return self._create_section(
                title="Seasonal Analysis",
                content=content,
                summary=summary,
                recommendations=recommendations
            )

        # Calculate variance
        monthly_with_variance = analyzer.calculate_variance(monthly_costs)
        quarterly_with_variance = analyzer.calculate_variance(quarterly_costs)

        # Detect patterns
        patterns = analyzer.detect_patterns(quarterly_with_variance)

        # Get recommendations
        recommendations = analyzer.get_recommendations(quarterly_with_variance)

        # Format costs for display
        monthly_display = monthly_costs.copy()
        monthly_display['total_cost'] = monthly_display['total_cost'].map('${:,.0f}'.format)
        monthly_display['avg_cost'] = monthly_display['avg_cost'].map('${:,.0f}'.format)

        quarterly_display = quarterly_with_variance.copy()
        quarterly_display['total_cost'] = quarterly_display['total_cost'].map('${:,.0f}'.format)
        quarterly_display['avg_cost'] = quarterly_display['avg_cost'].map('${:,.0f}'.format)
        quarterly_display['variance_pct'] = quarterly_display['variance_pct'].map('{:+.1f}%'.format)

        # Build summary
        if patterns:
            pattern_desc = ', '.join([p['pattern'] for p in patterns[:2]])
            summary = (
                f"Detected {len(patterns)} seasonal patterns. "
                f"Key findings: {pattern_desc}. "
                f"Cost variance ranges from {quarterly_with_variance['variance_pct'].min():.1f}% "
                f"to {quarterly_with_variance['variance_pct'].max():.1f}% across quarters."
            )
        else:
            summary = (
                f"No significant seasonal patterns detected. "
                f"Costs relatively stable across {len(quarterly_costs)} quarters."
            )

        # Create content dict
        content = {
            'monthly_costs': monthly_display,
            'quarterly_costs': quarterly_display,
            'patterns': patterns,
            'pattern_count': len(patterns)
        }

        return self._create_section(
            title="Seasonal Analysis",
            content=content,
            summary=summary,
            recommendations=recommendations
        )

    def add_vendor_analysis(self) -> ReportSection:
        """
        Run vendor performance analysis and create vendor section.

        Analyzes vendor costs, efficiency, and quality to identify high-cost
        vendors and those needing contract review.

        Returns:
            ReportSection with vendor analysis results including:
            - Top/bottom vendors by cost
            - Efficiency metrics
            - Quality indicators
            - Vendor recommendations

        Raises:
            ValueError: If data not loaded or required columns missing
        """
        if self.df is None:
            raise ValueError("Data not loaded. Call _load_data() first.")

        # Import vendor analyzer
        from src.analysis.vendor_analyzer import VendorAnalyzer

        analyzer = VendorAnalyzer(min_work_orders=3)

        # Calculate vendor costs
        vendor_costs = analyzer.calculate_vendor_costs(self.df, include_unknown=False)

        # Handle edge case: no vendor data
        if len(vendor_costs) == 0:
            summary = "No vendor data available for analysis."
            content = {
                'message': 'No contractors with minimum 3 work orders found',
                'vendors_analyzed': 0
            }
            recommendations = [
                "Ensure Contractor field is populated in work order data",
                "Reduce min_work_orders threshold if needed for analysis"
            ]
            return self._create_section(
                title="Vendor Analysis",
                content=content,
                summary=summary,
                recommendations=recommendations
            )

        # Get efficiency and quality metrics
        efficiency = analyzer.calculate_cost_efficiency(self.df, include_unknown=False)
        quality = analyzer.calculate_quality_indicators(self.df, include_unknown=False)

        # Get recommendations
        recommendations_list = analyzer.get_vendor_recommendations(self.df, include_unknown=False)

        # Extract top recommendation texts
        recommendations = [rec['suggestion'] for rec in recommendations_list[:5]]
        if not recommendations:
            recommendations = ["No significant vendor issues identified"]

        # Format display data
        top_vendors = vendor_costs.head(10).copy()
        top_vendors['total_cost'] = top_vendors['total_cost'].map('${:,.0f}'.format)
        top_vendors['avg_cost_per_wo'] = top_vendors['avg_cost_per_wo'].map('${:,.0f}'.format)

        # Build summary
        total_cost = vendor_costs['total_cost'].sum()
        top_3_cost = vendor_costs.head(3)['total_cost'].sum()
        top_3_pct = (top_3_cost / total_cost * 100) if total_cost > 0 else 0

        summary = (
            f"Analyzed {len(vendor_costs)} vendors. "
            f"Top 3 vendors ({', '.join(vendor_costs.head(3)['contractor'].tolist())}) "
            f"account for ${top_3_cost:,.0f} ({top_3_pct:.1f}%) of total vendor costs. "
            f"Generated {len(recommendations_list)} recommendations for review."
        )

        # Create content dict
        content = {
            'top_vendors': top_vendors,
            'total_vendors': len(vendor_costs),
            'efficiency_metrics': efficiency.head(10) if len(efficiency) > 0 else pd.DataFrame(),
            'quality_metrics': quality.head(10) if len(quality) > 0 else pd.DataFrame(),
            'recommendation_count': len(recommendations_list)
        }

        return self._create_section(
            title="Vendor Performance",
            content=content,
            summary=summary,
            recommendations=recommendations
        )

    def add_failure_analysis(self) -> ReportSection:
        """
        Run failure pattern analysis and create failure section.

        Analyzes work order text fields to identify recurring failure patterns
        and high-impact issues.

        Returns:
            ReportSection with failure analysis results including:
            - High-impact failure patterns
            - Categorized failure types
            - Equipment affected by patterns
            - Pattern-specific recommendations

        Raises:
            ValueError: If data not loaded or required columns missing
        """
        if self.df is None:
            raise ValueError("Data not loaded. Call _load_data() first.")

        # Import failure pattern analyzer
        from src.analysis.failure_pattern_analyzer import FailurePatternAnalyzer

        analyzer = FailurePatternAnalyzer()

        # Find high-impact patterns
        high_impact = analyzer.find_high_impact_patterns(self.df, min_occurrences=5)

        # Get failure categories
        categories = analyzer.categorize_by_failure_type(self.df)

        # Handle edge case: no text data available
        if len(high_impact) == 0 and len(categories) == 0:
            summary = "No text data available for failure pattern analysis."
            content = {
                'message': 'Problem, Cause, Remedy, or description fields not populated',
                'patterns_found': 0
            }
            recommendations = [
                "Ensure work orders include Problem and Remedy descriptions",
                "Train staff on importance of detailed failure documentation"
            ]
            return self._create_section(
                title="Failure Pattern Analysis",
                content=content,
                summary=summary,
                recommendations=recommendations
            )

        # Get recommendations
        recommendations_list = analyzer.get_pattern_recommendations(self.df)

        # Extract top recommendation texts
        recommendations = [rec['suggestion'] for rec in recommendations_list[:5]]
        if not recommendations:
            recommendations = ["No high-impact patterns found - failure diversity is healthy"]

        # Format display data
        if len(high_impact) > 0:
            high_impact_display = high_impact.head(10).copy()
            high_impact_display['total_cost'] = high_impact_display['total_cost'].map('${:,.0f}'.format)
            high_impact_display['avg_cost'] = high_impact_display['avg_cost'].map('${:,.0f}'.format)
            high_impact_display['impact_score'] = high_impact_display['impact_score'].map('{:.1f}'.format)
        else:
            high_impact_display = pd.DataFrame()

        # Build summary
        if len(high_impact) > 0:
            top_pattern = high_impact.iloc[0]
            summary = (
                f"Identified {len(high_impact)} high-impact failure patterns. "
                f"Top issue: '{top_pattern['pattern']}' ({top_pattern['category']}) "
                f"with {top_pattern['occurrences']} occurrences affecting "
                f"{top_pattern['equipment_affected']} equipment items. "
                f"Categorized {len(categories)} failure types."
            )
        else:
            summary = (
                f"Categorized {len(categories)} failure types. "
                f"No recurring high-impact patterns detected (threshold: 5 occurrences)."
            )

        # Create content dict
        content = {
            'high_impact_patterns': high_impact_display,
            'failure_categories': categories,
            'pattern_count': len(high_impact),
            'category_count': len(categories)
        }

        return self._create_section(
            title="Failure Pattern Analysis",
            content=content,
            summary=summary,
            recommendations=recommendations
        )

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

        # Add all analysis sections
        report.sections.append(self.add_equipment_analysis())
        report.sections.append(self.add_seasonal_analysis())
        report.sections.append(self.add_vendor_analysis())
        report.sections.append(self.add_failure_analysis())

        # Build executive summary
        report.executive_summary = self._build_executive_summary(report.sections)

        return report
