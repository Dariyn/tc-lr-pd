"""
Outlier detection module for identifying equipment with abnormal repair frequencies.

Purpose: Use statistical methods (z-score, IQR, percentile) to flag equipment
requiring attention based on frequency comparison to category peers.
"""

import pandas as pd
import numpy as np
from scipy import stats
import logging

logger = logging.getLogger(__name__)


def detect_zscore_outliers(freq_df: pd.DataFrame, threshold: float = 2.0) -> pd.DataFrame:
    """
    Detect outliers using z-score method (standard deviations from category mean).

    For each equipment category, calculates how many standard deviations each
    equipment's frequency is from the category mean. Equipment with |z-score| > threshold
    are flagged as outliers.

    Args:
        freq_df: DataFrame from calculate_equipment_frequencies() with:
            - Equipment_ID
            - equipment_primary_category
            - work_orders_per_month
        threshold: Number of standard deviations for outlier cutoff (default 2.0 = ~95th percentile)

    Returns:
        DataFrame with added columns:
        - z_score: Standard deviations from category mean
        - is_zscore_outlier: Boolean flag for outliers
    """
    result_df = freq_df.copy()
    result_df['z_score'] = np.nan
    result_df['is_zscore_outlier'] = False

    # Process each category separately
    for category in result_df['equipment_primary_category'].unique():
        mask = result_df['equipment_primary_category'] == category
        category_data = result_df.loc[mask, 'work_orders_per_month']

        # Calculate category statistics
        category_mean = category_data.mean()
        category_std = category_data.std()

        # Handle case where all values are the same (std = 0)
        if category_std == 0 or pd.isna(category_std):
            # All equipment have same frequency - none are outliers
            result_df.loc[mask, 'z_score'] = 0.0
            result_df.loc[mask, 'is_zscore_outlier'] = False
        else:
            # Calculate z-scores
            z_scores = (category_data - category_mean) / category_std
            result_df.loc[mask, 'z_score'] = z_scores

            # Flag outliers (using absolute value for both high and low outliers)
            # Note: For repair frequency, we care primarily about HIGH outliers
            result_df.loc[mask, 'is_zscore_outlier'] = z_scores > threshold

    outlier_count = result_df['is_zscore_outlier'].sum()
    logger.info(f"Z-score method flagged {outlier_count} outliers (threshold={threshold})")

    return result_df


def detect_iqr_outliers(freq_df: pd.DataFrame) -> pd.DataFrame:
    """
    Detect outliers using IQR (Interquartile Range) method.

    More robust to skewed distributions than z-score. Flags equipment with
    frequencies above Q3 + 1.5*IQR as outliers.

    Args:
        freq_df: DataFrame from calculate_equipment_frequencies() with:
            - Equipment_ID
            - equipment_primary_category
            - work_orders_per_month

    Returns:
        DataFrame with added column:
        - is_iqr_outlier: Boolean flag for outliers
    """
    result_df = freq_df.copy()
    result_df['is_iqr_outlier'] = False

    # Process each category separately
    for category in result_df['equipment_primary_category'].unique():
        mask = result_df['equipment_primary_category'] == category
        category_data = result_df.loc[mask, 'work_orders_per_month']

        # Calculate quartiles
        q1 = category_data.quantile(0.25)
        q3 = category_data.quantile(0.75)
        iqr = q3 - q1

        # Calculate upper outlier threshold (we care about high frequencies)
        upper_threshold = q3 + 1.5 * iqr

        # Flag outliers
        result_df.loc[mask, 'is_iqr_outlier'] = category_data > upper_threshold

    outlier_count = result_df['is_iqr_outlier'].sum()
    logger.info(f"IQR method flagged {outlier_count} outliers")

    return result_df


def detect_percentile_outliers(freq_df: pd.DataFrame, percentile: float = 90) -> pd.DataFrame:
    """
    Detect outliers using percentile method.

    Simple method: flags equipment above the Nth percentile within their category.
    For example, percentile=90 flags the top 10% of equipment by frequency.

    Args:
        freq_df: DataFrame from calculate_equipment_frequencies() with:
            - Equipment_ID
            - equipment_primary_category
            - work_orders_per_month
        percentile: Percentile threshold (default 90 = top 10%)

    Returns:
        DataFrame with added columns:
        - percentile_rank: Percentile rank within category (0-100)
        - is_percentile_outlier: Boolean flag for outliers
    """
    result_df = freq_df.copy()
    result_df['percentile_rank'] = np.nan
    result_df['is_percentile_outlier'] = False

    # Process each category separately
    for category in result_df['equipment_primary_category'].unique():
        mask = result_df['equipment_primary_category'] == category
        category_data = result_df.loc[mask, 'work_orders_per_month']

        # Calculate percentile rank for each equipment
        # Using 'average' method to handle ties
        percentile_ranks = category_data.rank(pct=True) * 100
        result_df.loc[mask, 'percentile_rank'] = percentile_ranks

        # Flag outliers above threshold
        result_df.loc[mask, 'is_percentile_outlier'] = percentile_ranks > percentile

    outlier_count = result_df['is_percentile_outlier'].sum()
    logger.info(f"Percentile method flagged {outlier_count} outliers (threshold={percentile})")

    return result_df


def detect_outliers(
    freq_df: pd.DataFrame,
    methods: list = None,
    exclude_no_equipment: bool = True
) -> pd.DataFrame:
    """
    Orchestrate multiple outlier detection methods with consensus flagging.

    Applies selected detection methods and creates a consensus flag based on
    majority voting (equipment flagged by 2+ methods).

    Args:
        freq_df: DataFrame from calculate_equipment_frequencies() with:
            - Equipment_ID
            - equipment_primary_category
            - work_orders_per_month
        methods: List of methods to apply. Options: ['zscore', 'iqr', 'percentile']
                Default: all three methods
        exclude_no_equipment: If True (default), exclude 'No Equipment' category
            from outlier detection. These records represent interior/general
            maintenance without specific equipment to analyze.

    Returns:
        DataFrame with all outlier flags plus:
        - outlier_count: Number of methods that flagged this equipment
        - is_outlier_consensus: True if flagged by 2+ methods (majority vote)
    """
    if methods is None:
        methods = ['zscore', 'iqr', 'percentile']

    result_df = freq_df.copy()

    # Filter out 'No Equipment' category if requested
    if exclude_no_equipment and 'equipment_primary_category' in result_df.columns:
        no_equip_mask = result_df['equipment_primary_category'] == 'No Equipment'
        no_equip_count = no_equip_mask.sum()
        if no_equip_count > 0:
            logger.info(
                f"Excluding {no_equip_count} 'No Equipment' records from outlier detection"
            )
            result_df = result_df[~no_equip_mask]

    logger.info(f"Running outlier detection with methods: {methods}")

    # Apply each enabled method
    if 'zscore' in methods:
        result_df = detect_zscore_outliers(result_df)

    if 'iqr' in methods:
        result_df = detect_iqr_outliers(result_df)

    if 'percentile' in methods:
        result_df = detect_percentile_outliers(result_df)

    # Calculate consensus
    outlier_flags = []
    if 'zscore' in methods:
        outlier_flags.append('is_zscore_outlier')
    if 'iqr' in methods:
        outlier_flags.append('is_iqr_outlier')
    if 'percentile' in methods:
        outlier_flags.append('is_percentile_outlier')

    # Count how many methods flagged each equipment
    result_df['outlier_count'] = result_df[outlier_flags].sum(axis=1)

    # Consensus: flagged by 2 or more methods (majority vote)
    result_df['is_outlier_consensus'] = result_df['outlier_count'] >= 2

    consensus_count = result_df['is_outlier_consensus'].sum()
    logger.info(f"Consensus flagged {consensus_count} outliers (2+ methods agree)")

    return result_df
