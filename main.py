#!/usr/bin/env python3
"""
Work Order Analysis Pipeline - Command Line Interface

Main entry point for running end-to-end work order analysis with reports,
exports, and visualizations.

Example Usage:
    # Basic analysis with PDF and Excel reports only (default)
    python main.py analyze -i data/work_orders.csv

    # Generate everything (reports + exports + visualizations)
    python main.py analyze -i data/work_orders.csv --all

    # Custom output directory with specific outputs
    python main.py analyze -i data/work_orders.csv -o results/ --exports --visualizations

    # Disable reports, only generate exports
    python main.py analyze -i data/work_orders.csv --no-reports --exports
"""

import argparse
import sys
import logging
import os
from pathlib import Path
from time import time

from src.orchestrator import PipelineOrchestrator


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def validate_input_file(input_path: str) -> Path:
    """
    Validate that input file exists and has correct extension.

    Args:
        input_path: Path to input file

    Returns:
        Path object to validated input file

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If file has unsupported extension
    """
    input_file = Path(input_path)

    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    if input_file.suffix.lower() not in ['.csv', '.xlsx', '.xls']:
        raise ValueError(f"Unsupported file format: {input_file.suffix}. Use .csv or .xlsx")

    return input_file


def print_summary(
    analysis_results: dict,
    report_paths: dict = None,
    export_paths: dict = None,
    viz_paths: dict = None,
    execution_time: float = 0
) -> None:
    """
    Print execution summary to console.

    Args:
        analysis_results: Results dict from run_full_analysis()
        report_paths: Dict with report file paths (optional)
        export_paths: Dict with export file paths (optional)
        viz_paths: Dict with visualization file paths (optional)
        execution_time: Total execution time in seconds
    """
    print("\n" + "=" * 60)
    print("PIPELINE EXECUTION COMPLETE")
    print("=" * 60)

    # Analysis summary
    print("\nAnalysis Summary:")
    print(f"  Total work orders: {analysis_results.get('quality_report', {}).get('total_records', 0):,}")
    print(f"  Consensus outliers: {len(analysis_results.get('equipment_df', []))} equipment")
    print(f"  Seasonal patterns: {analysis_results.get('seasonal_dict', {}).get('pattern_count', 0)}")
    print(f"  Vendors analyzed: {len(analysis_results.get('vendor_df', []))}")
    print(f"  Failure patterns: {len(analysis_results.get('patterns_list', []))}")

    # Report files
    if report_paths:
        print("\nReports Generated:")
        if 'pdf_path' in report_paths:
            print(f"  PDF:   {report_paths['pdf_path']}")
        if 'excel_path' in report_paths:
            print(f"  Excel: {report_paths['excel_path']}")

    # Export files
    if export_paths:
        csv_count = len(export_paths.get('csv', []))
        json_count = len(export_paths.get('json', []))
        print(f"\nData Exports: {csv_count + json_count} files ({csv_count} CSV + {json_count} JSON)")
        print(f"  Location: {Path(export_paths.get('csv', [''])[0]).parent if export_paths.get('csv') else 'N/A'}")

    # Visualizations
    if viz_paths:
        chart_count = len(viz_paths.get('charts', []))
        print(f"\nVisualizations: {chart_count} charts + 1 dashboard")
        if viz_paths.get('dashboard'):
            print(f"  Dashboard: {viz_paths['dashboard']}")

    # Execution time
    minutes = int(execution_time // 60)
    seconds = int(execution_time % 60)
    if minutes > 0:
        print(f"\nExecution Time: {minutes}m {seconds}s")
    else:
        print(f"\nExecution Time: {seconds}s")

    print("\n" + "=" * 60)


def cmd_analyze(args: argparse.Namespace) -> int:
    """
    Execute analyze command.

    Args:
        args: Parsed command line arguments

    Returns:
        Exit code (0 for success, 1 for error)
    """
    start_time = time()

    try:
        # Validate input file
        input_file = validate_input_file(args.input)
        logger.info(f"Input file validated: {input_file}")

        # Initialize orchestrator
        orchestrator = PipelineOrchestrator(
            input_file=str(input_file),
            output_dir=args.output
        )

        # Run analysis
        logger.info("Starting analysis pipeline...")
        analysis_results = orchestrator.run_full_analysis()

        report_paths = None
        export_paths = None
        viz_paths = None

        # Generate reports (default behavior unless --no-reports specified)
        if args.reports:
            logger.info("Generating reports...")
            report_paths = orchestrator.generate_reports(analysis_results)

        # Generate exports (if --exports or --all specified)
        if args.exports or args.all:
            logger.info("Exporting data files...")
            export_paths = orchestrator.export_data(analysis_results)

        # Generate visualizations (if --visualizations or --all specified)
        if args.visualizations or args.all:
            logger.info("Generating visualizations...")
            viz_paths = orchestrator.generate_visualizations(analysis_results)

        # Print summary
        execution_time = time() - start_time
        print_summary(
            analysis_results=analysis_results,
            report_paths=report_paths,
            export_paths=export_paths,
            viz_paths=viz_paths,
            execution_time=execution_time
        )

        return 0

    except FileNotFoundError as e:
        logger.error(f"Error: {str(e)}")
        return 1

    except ValueError as e:
        logger.error(f"Error: {str(e)}")
        return 1

    except Exception as e:
        logger.error(f"Pipeline failed: {str(e)}")
        logger.exception("Full traceback:")
        return 1


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Work Order Analysis Pipeline - Analyze maintenance data and generate reports',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic analysis with PDF and Excel reports only (default)
  python main.py analyze -i data/work_orders.csv

  # Generate everything (reports + exports + visualizations)
  python main.py analyze -i data/work_orders.csv --all

  # Custom output directory with specific outputs
  python main.py analyze -i data/work_orders.csv -o results/ --exports --visualizations

  # Disable reports, only generate exports
  python main.py analyze -i data/work_orders.csv --no-reports --exports

For more information, visit: https://github.com/yourusername/work-order-analysis
        """
    )

    # Add subcommands
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Analyze command
    analyze_parser = subparsers.add_parser(
        'analyze',
        help='Run full analysis pipeline on work order data',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Output Flags:
  By default, only PDF and Excel reports are generated.
  Use flags to enable additional outputs:

  --all              : Generate everything (reports + exports + visualizations)
  --exports          : Export CSV and JSON data files
  --visualizations   : Generate charts and interactive dashboard
  --no-reports       : Skip PDF/Excel report generation

Output Structure:
  output/
    reports/
      - work_order_analysis.pdf
      - work_order_analysis.xlsx
    exports/
      - equipment_rankings.csv/json
      - seasonal_patterns.csv/json
      - vendor_metrics.csv/json
      - failure_patterns.csv/json
    visualizations/
      - equipment_ranking.png
      - seasonal_costs.png
      - vendor_costs.png
      - failure_patterns.png
      - dashboard.html
        """
    )

    # Required arguments
    analyze_parser.add_argument(
        '-i', '--input',
        required=True,
        help='Path to input CSV or Excel file with work order data'
    )

    # Optional arguments
    analyze_parser.add_argument(
        '-o', '--output',
        default='output',
        help='Output directory for all generated files (default: output/)'
    )

    # Output control flags
    analyze_parser.add_argument(
        '--no-reports',
        dest='reports',
        action='store_false',
        default=True,
        help='Skip PDF and Excel report generation'
    )

    analyze_parser.add_argument(
        '-e', '--exports',
        action='store_true',
        default=False,
        help='Export CSV and JSON data files'
    )

    analyze_parser.add_argument(
        '-v', '--visualizations',
        action='store_true',
        default=False,
        help='Generate charts (PNG) and interactive dashboard (HTML)'
    )

    analyze_parser.add_argument(
        '-a', '--all',
        action='store_true',
        default=False,
        help='Generate everything: reports + exports + visualizations'
    )

    # Parse arguments
    args = parser.parse_args()

    # Show help if no command specified
    if not args.command:
        parser.print_help()
        return 0

    # Route to command handler
    if args.command == 'analyze':
        return cmd_analyze(args)

    return 0


if __name__ == '__main__':
    sys.exit(main())
