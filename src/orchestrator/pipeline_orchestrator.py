"""
Pipeline orchestrator for end-to-end work order analysis.

Coordinates all analysis modules and output generation to provide
a unified entry point for batch processing workflows.
"""

import logging
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
import pandas as pd

# Pipeline modules
from src.pipeline.pipeline import run_pipeline

# Analysis modules
from src.analysis.frequency_analyzer import calculate_equipment_frequencies
from src.analysis.outlier_detector import detect_outliers
from src.analysis.equipment_ranker import rank_equipment, rank_all_equipment, identify_thresholds
from src.analysis.seasonal_analyzer import SeasonalAnalyzer
from src.analysis.vendor_analyzer import VendorAnalyzer
from src.analysis.failure_pattern_analyzer import FailurePatternAnalyzer

# Reporting modules
from src.reporting.report_builder import ReportBuilder
from src.reporting.pdf_generator import PDFReportGenerator
from src.reporting.excel_generator import ExcelReportGenerator

# Export modules
from src.exports.data_exporter import DataExporter

# Visualization modules
from src.visualization.chart_generator import ChartGenerator
from src.visualization.dashboard_generator import DashboardGenerator


logger = logging.getLogger(__name__)


class PipelineOrchestrator:
    """
    Unified orchestrator for complete work order analysis pipeline.

    Coordinates execution of all 16 modules:
    - Data pipeline (4): load, clean, categorize, quality check
    - Equipment analysis (3): frequency, outlier detection, ranking
    - Seasonal analysis (1): monthly/quarterly patterns
    - Vendor analysis (1): cost performance, efficiency, quality
    - Failure pattern analysis (1): text extraction, categorization
    - Reporting (2): PDF and Excel generation
    - Exports (1): CSV and JSON data files
    - Visualizations (2): static charts and interactive dashboard

    Provides single entry point for batch processing workflows.
    """

    def __init__(self, input_file: str, output_dir: str = 'output'):
        """
        Initialize orchestrator with input file and output directory.

        Args:
            input_file: Path to input CSV/Excel file with work order data
            output_dir: Base directory for all outputs (default: 'output')
        """
        self.input_file = input_file
        self.output_dir = Path(output_dir)

        # Create output directory structure
        self._create_output_directories()

        logger.info(f"PipelineOrchestrator initialized")
        logger.info(f"  Input: {input_file}")
        logger.info(f"  Output: {output_dir}")

    def _create_output_directories(self) -> None:
        """Create output directory structure if it doesn't exist."""
        directories = [
            self.output_dir,
            self.output_dir / 'reports',
            self.output_dir / 'exports',
            self.output_dir / 'visualizations'
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Ensured directory exists: {directory}")

    def run_full_analysis(self) -> Dict[str, Any]:
        """
        Execute complete analysis pipeline and return results.

        Orchestrates:
        1. Data pipeline (load, clean, categorize, quality check)
        2. Equipment analysis (frequency, outlier detection, ranking)
        3. Seasonal analysis (monthly/quarterly patterns)
        4. Vendor analysis (cost performance, efficiency, quality)
        5. Failure pattern analysis (text extraction, categorization)

        Returns:
            Dictionary with analysis results:
            {
                'equipment_df': DataFrame with ranked equipment,
                'seasonal_dict': Dict with monthly/quarterly patterns,
                'vendor_df': DataFrame with vendor metrics,
                'patterns_list': List of failure patterns,
                'quality_report': Dict with data quality metrics,
                'thresholds': Dict with threshold recommendations,
                'category_stats': DataFrame with category statistics
            }

        Raises:
            FileNotFoundError: If input file doesn't exist
            ValueError: If data fails quality checks
            Exception: For other processing errors
        """
        logger.info("=" * 60)
        logger.info("STARTING FULL ANALYSIS PIPELINE")
        logger.info("=" * 60)

        try:
            # Stage 1: Data Pipeline
            logger.info("\n[Stage 1/5] Running data pipeline...")
            df, quality_report = run_pipeline(self.input_file)
            logger.info(f"✓ Data pipeline complete: {len(df)} work orders processed")

            # Stage 2: Equipment Analysis
            logger.info("\n[Stage 2/5] Running equipment analysis...")
            equipment_results = self._run_equipment_analysis(df)
            logger.info(f"✓ Equipment analysis complete: {len(equipment_results['equipment_df'])} outliers identified")

            # Stage 3: Seasonal Analysis
            logger.info("\n[Stage 3/5] Running seasonal analysis...")
            seasonal_results = self._run_seasonal_analysis(df)
            logger.info(f"✓ Seasonal analysis complete: {seasonal_results.get('pattern_count', 0)} patterns detected")

            # Stage 4: Vendor Analysis
            logger.info("\n[Stage 4/5] Running vendor analysis...")
            vendor_results = self._run_vendor_analysis(df)
            logger.info(f"✓ Vendor analysis complete: {len(vendor_results['vendor_df'])} vendors analyzed")

            # Stage 5: Failure Pattern Analysis
            logger.info("\n[Stage 5/5] Running failure pattern analysis...")
            failure_results = self._run_failure_analysis(df)
            logger.info(f"✓ Failure analysis complete: {len(failure_results['patterns_list'])} patterns identified")

            # Consolidate results
            results = {
                'equipment_df': equipment_results['equipment_df'],  # Outliers only
                'all_equipment_df': equipment_results.get('all_equipment_df', pd.DataFrame()),  # All equipment
                'seasonal_dict': seasonal_results,
                'vendor_df': vendor_results['vendor_df'],
                'patterns_list': failure_results['patterns_list'],
                'quality_report': quality_report,
                'thresholds': equipment_results.get('thresholds', {}),
                'category_stats': equipment_results.get('category_stats', pd.DataFrame()),
                'no_equipment_summary': equipment_results.get('no_equipment_summary', {})
            }
            if 'vendor_df_no_equipment' in vendor_results:
                results['vendor_df_no_equipment'] = vendor_results['vendor_df_no_equipment']

            logger.info("\n" + "=" * 60)
            logger.info("FULL ANALYSIS PIPELINE COMPLETE")
            logger.info("=" * 60)

            return results

        except FileNotFoundError as e:
            logger.error(f"[ERROR] Input file not found: {self.input_file}")
            raise

        except ValueError as e:
            logger.error(f"[ERROR] Data validation error: {str(e)}")
            raise

        except Exception as e:
            logger.error(f"[ERROR] Analysis pipeline failed: {str(e)}")
            logger.exception("Full traceback:")
            raise

    def _run_equipment_analysis(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Run equipment frequency, outlier detection, and ranking.

        Separates analysis into two tracks:
        - Equipment-based: Frequency, outlier, ranking analysis (excludes 'No Equipment')
        - No-equipment: Summary statistics for interior/general maintenance work

        Args:
            df: Cleaned and categorized work order DataFrame

        Returns:
            Dict with equipment_df, thresholds, category_stats, and no_equipment_summary
        """
        # Separate no-equipment records for summary
        no_equipment_summary = self._calculate_no_equipment_summary(df)

        # Calculate frequencies (excludes 'No Equipment' by default)
        freq_df = calculate_equipment_frequencies(df, exclude_no_equipment=True)

        # Rank ALL equipment by priority (for comprehensive view)
        all_equipment_df = rank_all_equipment(freq_df, exclude_no_equipment=True)
        logger.info(f"Ranked {len(all_equipment_df)} equipment items by priority")

        # Detect outliers (excludes 'No Equipment' by default)
        outliers_df = detect_outliers(freq_df, exclude_no_equipment=True)

        # Rank equipment - outliers only (excludes 'No Equipment' by default)
        ranked_df = rank_equipment(outliers_df, exclude_no_equipment=True)

        # Get thresholds (only if we have outliers)
        if len(ranked_df) > 0:
            thresholds = identify_thresholds(ranked_df)
        else:
            thresholds = {}
            logger.warning("No consensus outliers found - skipping threshold calculation")

        return {
            'equipment_df': ranked_df,  # Outliers only
            'all_equipment_df': all_equipment_df,  # All equipment ranked
            'thresholds': thresholds,
            'category_stats': freq_df,
            'no_equipment_summary': no_equipment_summary
        }

    def _calculate_no_equipment_summary(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Calculate summary statistics for 'No Equipment' records.

        These are interior fixes and general maintenance work orders
        that don't have specific equipment associated.

        Args:
            df: Full work order DataFrame

        Returns:
            Dict with no-equipment summary statistics
        """
        # Check if is_no_equipment column exists
        if 'is_no_equipment' not in df.columns:
            return {'count': 0, 'percentage': 0.0}

        no_equip_df = df[df['is_no_equipment']]
        total_count = len(df)
        no_equip_count = len(no_equip_df)

        if no_equip_count == 0:
            return {'count': 0, 'percentage': 0.0}

        # Calculate summary statistics
        summary = {
            'count': no_equip_count,
            'percentage': (no_equip_count / total_count * 100) if total_count > 0 else 0,
            'total_cost': no_equip_df['PO_AMOUNT'].sum() if 'PO_AMOUNT' in no_equip_df.columns else 0,
            'avg_cost': no_equip_df['PO_AMOUNT'].mean() if 'PO_AMOUNT' in no_equip_df.columns else 0,
        }

        # Property distribution (top 10)
        if 'Property' in no_equip_df.columns:
            property_counts = no_equip_df['Property'].value_counts().head(10)
            summary['top_properties'] = property_counts.to_dict()

        # Work type distribution
        if 'FM_Type' in no_equip_df.columns:
            fm_type_counts = no_equip_df['FM_Type'].value_counts().head(10)
            summary['work_types'] = fm_type_counts.to_dict()

        logger.info(
            f"No-equipment summary: {no_equip_count} records "
            f"({summary['percentage']:.1f}%), "
            f"total cost: ${summary['total_cost']:,.0f}"
        )

        return summary

    def _run_seasonal_analysis(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Run seasonal pattern analysis on work order costs.

        Args:
            df: Cleaned work order DataFrame

        Returns:
            Dict with monthly_costs, quarterly_costs, patterns, and pattern_count
        """
        analyzer = SeasonalAnalyzer()

        try:
            # Calculate monthly and quarterly costs
            monthly_costs = analyzer.calculate_monthly_costs(df)
            quarterly_costs = analyzer.calculate_quarterly_costs(df)

            # Handle edge case: no data
            if len(monthly_costs) == 0 or len(quarterly_costs) == 0:
                logger.warning("Insufficient data for seasonal analysis")
                return {
                    'monthly_costs': pd.DataFrame(),
                    'quarterly_costs': pd.DataFrame(),
                    'patterns': [],
                    'pattern_count': 0
                }

            # Calculate variance
            quarterly_with_variance = analyzer.calculate_variance(quarterly_costs)

            # Detect patterns
            patterns = analyzer.detect_patterns(quarterly_with_variance)

            return {
                'monthly_costs': monthly_costs,
                'quarterly_costs': quarterly_with_variance,
                'patterns': patterns,
                'pattern_count': len(patterns)
            }

        except Exception as e:
            logger.warning(f"Seasonal analysis failed: {str(e)} - continuing with empty results")
            return {
                'monthly_costs': pd.DataFrame(),
                'quarterly_costs': pd.DataFrame(),
                'patterns': [],
                'pattern_count': 0
            }

    def _run_vendor_analysis(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Run vendor cost, efficiency, and quality analysis.

        Args:
            df: Cleaned work order DataFrame

        Returns:
            Dict with vendor_df and recommendation count.
            Includes vendor_df_no_equipment when no-equipment rows can be excluded.
        """
        analyzer = VendorAnalyzer(min_work_orders=3)

        try:
            # Calculate vendor costs
            vendor_costs = analyzer.calculate_vendor_costs(df, include_unknown=False)
            vendor_costs_no_equipment = None
            if 'is_no_equipment' in df.columns:
                df_vendor = df[~df['is_no_equipment']].copy()
                vendor_costs_no_equipment = analyzer.calculate_vendor_costs(
                    df_vendor,
                    include_unknown=False
                )

            # Handle edge case: no vendor data
            if len(vendor_costs) == 0:
                logger.warning("No vendor data available for analysis")
                results = {
                    'vendor_df': pd.DataFrame(),
                    'recommendations': []
                }
                if vendor_costs_no_equipment is not None:
                    results['vendor_df_no_equipment'] = vendor_costs_no_equipment
                return results

            # Get recommendations
            recommendations = analyzer.get_vendor_recommendations(df, include_unknown=False)

            results = {
                'vendor_df': vendor_costs,
                'recommendations': recommendations
            }
            if vendor_costs_no_equipment is not None:
                results['vendor_df_no_equipment'] = vendor_costs_no_equipment
            return results

        except Exception as e:
            logger.warning(f"Vendor analysis failed: {str(e)} - continuing with empty results")
            return {
                'vendor_df': pd.DataFrame(),
                'recommendations': []
            }

    def _run_failure_analysis(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Run failure pattern extraction and categorization.

        Args:
            df: Cleaned work order DataFrame

        Returns:
            Dict with patterns_list and category counts
        """
        analyzer = FailurePatternAnalyzer()

        try:
            # Find high-impact patterns
            high_impact = analyzer.find_high_impact_patterns(df, min_occurrences=5)

            # Get failure categories
            categories = analyzer.categorize_by_failure_type(df)

            # Handle edge case: no text data
            if len(high_impact) == 0 and len(categories) == 0:
                logger.warning("No text data available for failure pattern analysis")
                return {
                    'patterns_list': [],
                    'categories': {}
                }

            # Convert DataFrame to list of dicts for easier consumption
            if len(high_impact) > 0:
                patterns_list = high_impact.to_dict('records')
            else:
                patterns_list = []

            return {
                'patterns_list': patterns_list,
                'categories': categories
            }

        except Exception as e:
            logger.warning(f"Failure pattern analysis failed: {str(e)} - continuing with empty results")
            return {
                'patterns_list': [],
                'categories': {}
            }

    def generate_reports(self, analysis_results: Dict[str, Any]) -> Dict[str, str]:
        """
        Generate PDF and Excel reports from analysis results.

        Args:
            analysis_results: Dict returned from run_full_analysis()

        Returns:
            Dict with file paths:
            {
                'pdf_path': Path to generated PDF report,
                'excel_path': Path to generated Excel report
            }

        Raises:
            Exception: If report generation fails
        """
        logger.info("\n" + "=" * 60)
        logger.info("GENERATING REPORTS")
        logger.info("=" * 60)

        try:
            # Build report using ReportBuilder
            logger.info("\n[1/3] Building consolidated report...")
            builder = ReportBuilder(self.input_file)
            report = builder.build_report()
            logger.info("✓ Report structure built")

            # Generate PDF
            logger.info("\n[2/3] Generating PDF report...")
            pdf_path = self.output_dir / 'reports' / 'work_order_analysis.pdf'
            pdf_generator = PDFReportGenerator()
            pdf_generator.generate_pdf(report, str(pdf_path))
            logger.info(f"✓ PDF report saved: {pdf_path}")

            # Generate Excel
            logger.info("\n[3/3] Generating Excel report...")
            excel_path = self.output_dir / 'reports' / 'work_order_analysis.xlsx'
            excel_generator = ExcelReportGenerator()
            excel_generator.generate_excel(report, str(excel_path))
            logger.info(f"✓ Excel report saved: {excel_path}")

            logger.info("\n" + "=" * 60)
            logger.info("REPORT GENERATION COMPLETE")
            logger.info("=" * 60)

            return {
                'pdf_path': str(pdf_path),
                'excel_path': str(excel_path)
            }

        except Exception as e:
            logger.error(f"[ERROR] Report generation failed: {str(e)}")
            logger.exception("Full traceback:")
            raise

    def export_data(self, analysis_results: Dict[str, Any]) -> Dict[str, List[str]]:
        """
        Export analysis results to CSV and JSON files.

        Exports 4 analysis types × 2 formats = 8 files:
        - equipment_rankings.csv/json
        - seasonal_patterns.csv/json
        - vendor_metrics.csv/json
        - failure_patterns.csv/json

        Args:
            analysis_results: Dict returned from run_full_analysis()

        Returns:
            Dict with file paths organized by format:
            {
                'csv': [list of CSV file paths],
                'json': [list of JSON file paths]
            }

        Raises:
            Exception: If export fails
        """
        logger.info("\n" + "=" * 60)
        logger.info("EXPORTING DATA FILES")
        logger.info("=" * 60)

        exporter = DataExporter()
        csv_files = []
        json_files = []

        try:
            # Export equipment rankings (outliers only)
            logger.info("\n[1/5] Exporting equipment outliers...")
            equipment_csv = self.output_dir / 'exports' / 'equipment_rankings.csv'
            equipment_json = self.output_dir / 'exports' / 'equipment_rankings.json'
            exporter.export_equipment_rankings(analysis_results['equipment_df'], equipment_csv)
            exporter.export_equipment_rankings_json(analysis_results['equipment_df'], equipment_json)
            csv_files.append(str(equipment_csv))
            json_files.append(str(equipment_json))
            logger.info(f"✓ Equipment outliers exported")

            # Export all equipment rankings
            logger.info("\n[2/5] Exporting all equipment rankings...")
            all_equipment_csv = self.output_dir / 'exports' / 'all_equipment_rankings.csv'
            all_equipment_json = self.output_dir / 'exports' / 'all_equipment_rankings.json'
            exporter.export_equipment_rankings(analysis_results['all_equipment_df'], all_equipment_csv)
            exporter.export_equipment_rankings_json(analysis_results['all_equipment_df'], all_equipment_json)
            csv_files.append(str(all_equipment_csv))
            json_files.append(str(all_equipment_json))
            logger.info(f"✓ All equipment rankings exported")

            # Export seasonal patterns
            logger.info("\n[3/5] Exporting seasonal patterns...")
            seasonal_csv = self.output_dir / 'exports' / 'seasonal_patterns.csv'
            seasonal_json = self.output_dir / 'exports' / 'seasonal_patterns.json'
            exporter.export_seasonal_patterns(analysis_results['seasonal_dict'], seasonal_csv)
            exporter.export_seasonal_patterns_json(analysis_results['seasonal_dict'], seasonal_json)
            csv_files.append(str(seasonal_csv))
            json_files.append(str(seasonal_json))
            logger.info(f"✓ Seasonal patterns exported")

            # Export vendor metrics
            logger.info("\n[4/5] Exporting vendor metrics...")
            vendor_csv = self.output_dir / 'exports' / 'vendor_metrics.csv'
            vendor_json = self.output_dir / 'exports' / 'vendor_metrics.json'
            exporter.export_vendor_metrics(analysis_results['vendor_df'], vendor_csv)
            exporter.export_vendor_metrics_json(analysis_results['vendor_df'], vendor_json)
            csv_files.append(str(vendor_csv))
            json_files.append(str(vendor_json))
            logger.info(f"✓ Vendor metrics exported")

            # Export failure patterns
            logger.info("\n[5/5] Exporting failure patterns...")
            failure_csv = self.output_dir / 'exports' / 'failure_patterns.csv'
            failure_json = self.output_dir / 'exports' / 'failure_patterns.json'
            exporter.export_failure_patterns(analysis_results['patterns_list'], failure_csv)
            exporter.export_failure_patterns_json(analysis_results['patterns_list'], failure_json)
            csv_files.append(str(failure_csv))
            json_files.append(str(failure_json))
            logger.info(f"✓ Failure patterns exported")

            logger.info("\n" + "=" * 60)
            logger.info("DATA EXPORT COMPLETE")
            logger.info(f"Total files: {len(csv_files) + len(json_files)} ({len(csv_files)} CSV + {len(json_files)} JSON)")
            logger.info("=" * 60)

            return {
                'csv': csv_files,
                'json': json_files
            }

        except Exception as e:
            logger.error(f"[ERROR] Data export failed: {str(e)}")
            logger.exception("Full traceback:")
            raise

    def generate_visualizations(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate static charts (PNG/SVG) and interactive dashboard (HTML).

        Creates:
        - Static charts: equipment_ranking.png, seasonal_costs.png,
          vendor_costs.png, vendor_costs_scaled.png, failure_patterns.png
        - Interactive dashboard: dashboard.html with all 4 chart types

        Args:
            analysis_results: Dict returned from run_full_analysis()

        Returns:
            Dict with file paths:
            {
                'charts': [list of chart file paths],
                'dashboard': Path to dashboard HTML file
            }

        Raises:
            Exception: If visualization generation fails
        """
        logger.info("\n" + "=" * 60)
        logger.info("GENERATING VISUALIZATIONS")
        logger.info("=" * 60)

        chart_files = []

        try:
            # Initialize generators
            chart_gen = ChartGenerator(dpi=300)
            dashboard_gen = DashboardGenerator()

            # Generate static charts
            logger.info("\n[1/7] Generating equipment outliers chart...")
            equipment_chart = self.output_dir / 'visualizations' / 'equipment_ranking.png'
            chart_gen.create_equipment_ranking_chart(
                analysis_results['equipment_df'],
                equipment_chart,
                top_n=5,
                format='png'
            )
            chart_files.append(str(equipment_chart))
            logger.info(f"✓ Equipment outliers chart saved: {equipment_chart}")

            logger.info("\n[2/7] Generating all equipment ranking chart...")
            all_equipment_chart = self.output_dir / 'visualizations' / 'all_equipment_ranking.png'
            chart_gen.create_equipment_ranking_chart(
                analysis_results['all_equipment_df'],
                all_equipment_chart,
                top_n=10,
                format='png'
            )
            chart_files.append(str(all_equipment_chart))
            logger.info(f"✓ All equipment chart saved: {all_equipment_chart}")

            logger.info("\n[3/7] Generating seasonal trend chart...")
            seasonal_chart = self.output_dir / 'visualizations' / 'seasonal_costs.png'
            seasonal_data = {
                'monthly': analysis_results['seasonal_dict'].get('monthly_costs', pd.DataFrame())
            }
            chart_gen.create_seasonal_trend_chart(
                seasonal_data,
                seasonal_chart,
                format='png'
            )
            chart_files.append(str(seasonal_chart))
            logger.info(f"✓ Seasonal chart saved: {seasonal_chart}")

            logger.info("\n[4/7] Generating vendor performance chart...")
            vendor_chart = self.output_dir / 'visualizations' / 'vendor_costs.png'
            vendor_df_for_chart = analysis_results.get(
                'vendor_df_no_equipment',
                analysis_results['vendor_df']
            )
            vendor_title_note = None
            if 'vendor_df_no_equipment' in analysis_results:
                vendor_title_note = 'No Equipment excluded'
            chart_gen.create_vendor_performance_chart(
                vendor_df_for_chart,
                vendor_chart,
                top_n=10,
                format='png',
                title_note=vendor_title_note
            )
            chart_files.append(str(vendor_chart))
            logger.info(f"✓ Vendor chart saved: {vendor_chart}")

            logger.info("\n[5/7] Generating vendor scaled cost chart...")
            vendor_scaled_chart = self.output_dir / 'visualizations' / 'vendor_costs_scaled.png'
            chart_gen.create_vendor_costs_scaled_chart(
                analysis_results['vendor_df'],
                vendor_scaled_chart,
                top_n=10,
                format='png'
            )
            chart_files.append(str(vendor_scaled_chart))
            logger.info(f"Vendor scaled chart saved: {vendor_scaled_chart}")

            logger.info("\n[6/7] Generating failure pattern chart...")
            failure_chart = self.output_dir / 'visualizations' / 'failure_patterns.png'
            # Convert patterns list to DataFrame if needed
            if analysis_results['patterns_list']:
                patterns_df = pd.DataFrame(analysis_results['patterns_list'])
            else:
                patterns_df = pd.DataFrame()
            chart_gen.create_failure_pattern_chart(
                patterns_df,
                failure_chart,
                top_n=10,
                format='png'
            )
            chart_files.append(str(failure_chart))
            logger.info(f"✓ Failure patterns chart saved: {failure_chart}")

            # Generate interactive dashboard
            logger.info("\n[7/7] Generating interactive dashboard...")
            dashboard_path = self.output_dir / 'visualizations' / 'dashboard.html'
            dashboard_gen.create_dashboard(
                equipment_df=analysis_results['equipment_df'],
                seasonal_dict=analysis_results['seasonal_dict'],
                vendor_df=analysis_results['vendor_df'],
                patterns_list=analysis_results['patterns_list'],
                output_path=dashboard_path
            )
            logger.info(f"✓ Dashboard saved: {dashboard_path}")

            logger.info("\n" + "=" * 60)
            logger.info("VISUALIZATION GENERATION COMPLETE")
            logger.info(f"Charts: {len(chart_files)}, Dashboard: 1")
            logger.info("=" * 60)

            return {
                'charts': chart_files,
                'dashboard': str(dashboard_path)
            }

        except Exception as e:
            logger.error(f"[ERROR] Visualization generation failed: {str(e)}")
            logger.exception("Full traceback:")
            raise
