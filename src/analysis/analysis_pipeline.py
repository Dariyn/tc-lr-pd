"""Integrated analysis pipeline orchestrating complete equipment analysis.

Orchestrates: data loading → frequency calculation → outlier detection → ranking
Output: Ranked equipment list with priority scores and actionable thresholds.
"""

import logging
from typing import Tuple, Dict
import pandas as pd

from src.pipeline.pipeline import run_pipeline
from src.analysis.frequency_analyzer import (
    calculate_equipment_frequencies,
    calculate_category_statistics
)
from src.analysis.outlier_detector import detect_outliers
from src.analysis.equipment_ranker import rank_equipment, identify_thresholds

logger = logging.getLogger(__name__)


def run_equipment_analysis(input_file: str) -> Tuple[pd.DataFrame, pd.DataFrame, Dict]:
    """Run complete equipment analysis pipeline.

    Orchestrates:
    1. Load and prepare data (run_pipeline)
    2. Calculate equipment frequencies and category baselines
    3. Detect statistical outliers (z-score, IQR, percentile)
    4. Rank equipment by priority (frequency + cost + outlier status)
    5. Identify threshold recommendations

    Args:
        input_file: Path to input CSV file with work order data

    Returns:
        Tuple of:
        - ranked_equipment_df: DataFrame with ranked consensus outliers
        - category_stats_df: DataFrame with category-level statistics
        - thresholds_dict: Dict with threshold recommendations
    """
    logger.info("=" * 60)
    logger.info("STARTING EQUIPMENT ANALYSIS PIPELINE")
    logger.info("=" * 60)

    # Stage 1: Load and prepare data
    logger.info("\n[Stage 1/5] Loading and preparing data...")
    df, quality_report = run_pipeline(input_file)
    logger.info(f"✓ Loaded {len(df)} work orders")

    # Stage 2: Calculate frequencies
    logger.info("\n[Stage 2/5] Calculating equipment frequencies...")
    freq_df = calculate_equipment_frequencies(df)
    logger.info(f"✓ Calculated frequencies for {len(freq_df)} equipment items")

    # Stage 3: Calculate category statistics
    logger.info("\n[Stage 3/5] Calculating category baselines...")
    category_stats_df = calculate_category_statistics(freq_df)
    logger.info(f"✓ Calculated statistics for {len(category_stats_df)} categories")

    # Stage 4: Detect outliers
    logger.info("\n[Stage 4/5] Detecting statistical outliers...")
    outliers_df = detect_outliers(freq_df)
    consensus_count = outliers_df['is_outlier_consensus'].sum()
    logger.info(f"✓ Identified {consensus_count} consensus outliers")

    # Stage 5: Rank equipment
    logger.info("\n[Stage 5/5] Ranking equipment by priority...")
    ranked_df = rank_equipment(outliers_df)
    logger.info(f"✓ Ranked {len(ranked_df)} high-priority equipment")

    # Identify thresholds
    logger.info("\n[Recommendations] Identifying thresholds...")
    thresholds_dict = identify_thresholds(ranked_df)
    logger.info(f"✓ Threshold recommendations generated")

    logger.info("\n" + "=" * 60)
    logger.info("EQUIPMENT ANALYSIS PIPELINE COMPLETE")
    logger.info("=" * 60)

    return ranked_df, category_stats_df, thresholds_dict


def main():
    """CLI entry point: runs equipment analysis on default input file."""
    # Configure logging for console output
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Default input file
    input_file = 'input/adhoc_wo_20240101_20250531.xlsx - in.csv'

    print("\n" + "=" * 60)
    print("EQUIPMENT COST REDUCTION ANALYSIS")
    print("=" * 60)

    # Run analysis
    ranked_df, category_stats_df, thresholds_dict = run_equipment_analysis(input_file)

    # Print summary statistics
    print("\n" + "=" * 60)
    print("ANALYSIS SUMMARY")
    print("=" * 60)

    print(f"\nTotal equipment analyzed: {category_stats_df['equipment_count'].sum()} items")
    print(f"Equipment categories: {len(category_stats_df)}")
    print(f"Consensus outliers found: {len(ranked_df)}")

    # Print top 5 highest-priority equipment
    print("\n" + "-" * 60)
    print("TOP 5 HIGHEST-PRIORITY EQUIPMENT")
    print("-" * 60)

    if len(ranked_df) > 0:
        top_5 = ranked_df.head(5)
        print("\n{:<15} {:<30} {:<12} {:<15} {:<12}".format(
            "Equipment_ID", "Category", "WO/Month", "Cost Impact", "Priority"
        ))
        print("-" * 60)

        for _, row in top_5.iterrows():
            eq_id = str(row['Equipment_ID'])[:15]
            category = str(row['equipment_primary_category'])[:30]
            wo_per_month = f"{row['work_orders_per_month']:.2f}"
            cost_impact = f"${row['cost_impact']:,.0f}"
            priority = f"{row['priority_score']:.3f}"

            print("{:<15} {:<30} {:<12} {:<15} {:<12}".format(
                eq_id, category, wo_per_month, cost_impact, priority
            ))
    else:
        print("\nNo consensus outliers found - all equipment within normal ranges")

    # Print threshold recommendations
    print("\n" + "-" * 60)
    print("RECOMMENDED THRESHOLDS")
    print("-" * 60)

    print(f"\nFrequency threshold: {thresholds_dict['frequency_threshold']:.2f} work orders/month")
    print(f"Cost threshold: ${thresholds_dict['cost_threshold']:,.0f}")
    print(f"Percentile threshold: {thresholds_dict['percentile_threshold']:.0f}th percentile")
    print(f"\nRationale: {thresholds_dict['rationale']}")

    print("\n" + "=" * 60)
    print("ANALYSIS COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()
