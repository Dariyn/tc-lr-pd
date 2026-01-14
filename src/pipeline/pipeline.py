"""
Integrated data pipeline orchestrator.

Orchestrates the complete work order data pipeline:
load → clean → categorize → validate → report
"""

import logging
import sys
from typing import Tuple, Optional
import pandas as pd

from src.pipeline.data_loader import load_work_orders
from src.pipeline.data_cleaner import clean_work_orders
from src.pipeline.categorizer import categorize_work_orders
from src.pipeline.quality_reporter import generate_quality_report


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_pipeline(
    input_file: str,
    output_file: Optional[str] = None
) -> Tuple[pd.DataFrame, dict]:
    """
    Run the complete data pipeline on work order data.

    Orchestrates: load → clean → categorize → validate

    Args:
        input_file: Path to input CSV/Excel file
        output_file: Optional path to save processed data as CSV

    Returns:
        Tuple of (processed_df, quality_report)

    Raises:
        FileNotFoundError: If input file doesn't exist
        ValueError: If data fails validation
        Exception: For other processing errors
    """
    try:
        # Stage 1: Load
        logger.info("=" * 60)
        logger.info("PIPELINE STAGE 1: Loading data")
        logger.info("=" * 60)
        df = load_work_orders(input_file)
        logger.info(f"[OK] Loaded {len(df)} work orders")

        # Stage 2: Clean
        logger.info("")
        logger.info("=" * 60)
        logger.info("PIPELINE STAGE 2: Cleaning data")
        logger.info("=" * 60)
        df = clean_work_orders(df)
        logger.info(f"[OK] Cleaned data: {len(df)} work orders ready")

        # Stage 3: Categorize
        logger.info("")
        logger.info("=" * 60)
        logger.info("PIPELINE STAGE 3: Categorizing equipment")
        logger.info("=" * 60)
        df = categorize_work_orders(df)
        logger.info(f"[OK] Categorized {df['equipment_category'].nunique()} equipment categories")

        # Stage 4: Validate
        logger.info("")
        logger.info("=" * 60)
        logger.info("PIPELINE STAGE 4: Validating data quality")
        logger.info("=" * 60)
        quality_report = generate_quality_report(df)
        logger.info("[OK] Quality report generated")

        # Print quality report summary
        print_quality_summary(quality_report)

        # Save output if requested
        if output_file:
            logger.info("")
            logger.info(f"Saving processed data to: {output_file}")
            df.to_csv(output_file, index=False, encoding='utf-8-sig')
            logger.info(f"[OK] Saved {len(df)} work orders to {output_file}")

        logger.info("")
        logger.info("=" * 60)
        logger.info("PIPELINE COMPLETE")
        logger.info("=" * 60)

        return df, quality_report

    except FileNotFoundError as e:
        logger.error(f"[ERROR] File not found: {input_file}")
        raise

    except ValueError as e:
        logger.error(f"[ERROR] Validation error: {str(e)}")
        raise

    except Exception as e:
        logger.error(f"[ERROR] Pipeline error: {str(e)}")
        logger.exception("Full traceback:")
        raise


def print_quality_summary(report: dict) -> None:
    """
    Print formatted quality report summary.

    Args:
        report: Quality report dict from generate_quality_report()
    """
    print("")
    print("=" * 60)
    print("DATA QUALITY REPORT")
    print("=" * 60)
    print("")

    # Overall score
    score = report['overall_quality_score']
    passed = report['quality_passed']
    status = "[PASSED]" if passed else "[FAILED]"

    print(f"Overall Quality Score: {score:.2f}/100 {status}")
    print("")

    # Component scores
    print("Component Scores:")
    print(f"  Completeness:  {report['completeness_score']:.2f}/100 (40% weight)")
    print(f"  Consistency:   {report['consistency_score']:.2f}/100 (40% weight)")
    print(f"  Outlier Rate:  {report['outlier_score']:.2f}/100 (20% weight)")
    print("")

    # Key metrics
    print("Key Metrics:")
    print(f"  Total Records: {report['total_records']:,}")

    # Completeness details
    completeness = report['completeness']
    print("")
    print("  Field Completeness:")
    for field, metrics in completeness.items():
        if isinstance(metrics, dict):
            pct = metrics['completeness_pct']
            status = "[OK]" if metrics['is_complete'] else "[LOW]"
            print(f"    {status} {field}: {pct:.1f}%")

    # Consistency details
    consistency = report['consistency']
    print("")
    print("  Data Consistency:")
    if consistency.get('category_consistency_avg') is not None:
        print(f"    Category Consistency: {consistency['category_consistency_avg']:.1f}%")
    if consistency.get('date_consistency_pct') is not None:
        print(f"    Valid Date Order: {consistency['date_consistency_pct']:.1f}%")
    if consistency.get('cost_consistency_pct') is not None:
        print(f"    Valid Costs (>=0): {consistency['cost_consistency_pct']:.1f}%")

    # Outlier details
    outliers = report['outliers']
    print("")
    print("  Outliers Detected:")
    print(f"    Cost Outliers: {outliers['cost_outlier_count']} ({outliers['cost_outlier_pct']:.2f}%)")
    if outliers.get('cost_outlier_threshold'):
        print(f"      Threshold: ${outliers['cost_outlier_threshold']:,.2f}")
    print(f"    Duration Outliers: {outliers['duration_outlier_count']} ({outliers['duration_outlier_pct']:.2f}%)")
    if outliers.get('duration_outlier_threshold'):
        print(f"      Threshold: {outliers['duration_outlier_threshold']:.1f} hours")

    # Coverage details
    coverage = report['coverage']
    print("")
    print("  Data Coverage:")
    if coverage.get('date_range_start'):
        print(f"    Date Range: {coverage['date_range_start'].date()} to {coverage['date_range_end'].date()}")
        print(f"    Days Covered: {coverage['date_range_days']:,}")
    print(f"    Unique Equipment: {coverage['unique_equipment_count']:,}")
    print(f"    Unique Categories: {coverage['unique_category_count']:,}")
    print(f"    Unique Properties: {coverage['unique_property_count']:,}")

    # Recommendations
    recommendations = report['recommendations']
    print("")
    print("Recommendations:")
    for i, rec in enumerate(recommendations, 1):
        print(f"  {i}. {rec}")

    print("")
    print("=" * 60)


def main():
    """
    CLI entry point for pipeline execution.

    Runs pipeline on default input file and prints quality report.
    Exits with code 0 if quality passed, code 1 if failed.
    """
    input_file = 'input/adhoc_wo_20240101_20250531.xlsx - in.csv'

    try:
        logger.info("Starting Work Order Analysis Pipeline")
        logger.info(f"Input: {input_file}")
        logger.info("")

        # Run pipeline
        df, quality_report = run_pipeline(input_file)

        # Exit with appropriate code
        if quality_report['quality_passed']:
            logger.info("[SUCCESS] Pipeline completed successfully - data quality passed")
            sys.exit(0)
        else:
            logger.warning("[WARNING] Pipeline completed with quality concerns")
            sys.exit(1)

    except Exception as e:
        logger.error(f"[ERROR] Pipeline failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
