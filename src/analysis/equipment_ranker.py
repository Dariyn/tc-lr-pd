"""Equipment ranking and prioritization module.

Ranks equipment by cost reduction priority, combining:
- Frequency: Work orders per month (high frequency = more repairs)
- Cost impact: Total maintenance spend (total_work_orders * avg_cost)
- Outlier status: Statistical significance (consensus flag adds confidence)

Output: Ranked equipment list for actionable cost reduction targeting.
"""

import pandas as pd
import numpy as np
from typing import Dict


def calculate_cost_impact(outlier_df: pd.DataFrame) -> pd.DataFrame:
    """Calculate total cost impact for each equipment.

    Cost impact = total_work_orders * avg_cost
    Represents total maintenance spend over timespan.

    Args:
        outlier_df: DataFrame with outlier detection results

    Returns:
        DataFrame with cost_impact column added
    """
    df = outlier_df.copy()

    # Calculate cost impact (handle missing avg_cost by using 0)
    df['cost_impact'] = df['total_work_orders'] * df['avg_cost'].fillna(0)

    return df


def calculate_priority_score(outlier_df: pd.DataFrame) -> pd.DataFrame:
    """Calculate priority score for each equipment within its category.

    Priority score combines normalized metrics:
    - freq_score: Normalized work_orders_per_month (0-1 within category)
    - cost_score: Normalized cost_impact (0-1 within category)
    - outlier_score: 1.0 if consensus outlier, 0.5 if any flag, 0.0 otherwise

    Weighted formula: (freq_score * 0.4) + (cost_score * 0.4) + (outlier_score * 0.2)

    Args:
        outlier_df: DataFrame with cost_impact column

    Returns:
        DataFrame with priority_score column added (0-1 range)
    """
    df = outlier_df.copy()

    # Initialize score columns
    df['freq_score'] = 0.0
    df['cost_score'] = 0.0
    df['outlier_score'] = 0.0
    df['priority_score'] = 0.0

    # Calculate scores within each category
    for category in df['equipment_primary_category'].unique():
        cat_mask = df['equipment_primary_category'] == category
        cat_df = df[cat_mask]

        # Normalize frequency score within category (0-1)
        freq_min = cat_df['work_orders_per_month'].min()
        freq_max = cat_df['work_orders_per_month'].max()
        if freq_max > freq_min:
            df.loc[cat_mask, 'freq_score'] = (
                (cat_df['work_orders_per_month'] - freq_min) / (freq_max - freq_min)
            )
        else:
            # All same frequency - assign 0.5 (middle)
            df.loc[cat_mask, 'freq_score'] = 0.5

        # Normalize cost score within category (0-1)
        cost_min = cat_df['cost_impact'].min()
        cost_max = cat_df['cost_impact'].max()
        if cost_max > cost_min:
            df.loc[cat_mask, 'cost_score'] = (
                (cat_df['cost_impact'] - cost_min) / (cost_max - cost_min)
            )
        else:
            # All same cost - assign 0.5 (middle)
            df.loc[cat_mask, 'cost_score'] = 0.5

        # Outlier score based on flags
        # 1.0 = consensus outlier (high confidence)
        # 0.5 = any outlier flag (medium confidence)
        # 0.0 = no flags (not an outlier)
        df.loc[cat_mask & df['is_outlier_consensus'], 'outlier_score'] = 1.0
        df.loc[cat_mask & ~df['is_outlier_consensus'] & (
            df['is_zscore_outlier'] | df['is_iqr_outlier'] | df['is_percentile_outlier']
        ), 'outlier_score'] = 0.5

    # Calculate weighted priority score
    # Weights: frequency 40%, cost 40%, outlier status 20%
    df['priority_score'] = (
        (df['freq_score'] * 0.4) +
        (df['cost_score'] * 0.4) +
        (df['outlier_score'] * 0.2)
    )

    return df


def rank_equipment(
    outlier_df: pd.DataFrame,
    exclude_no_equipment: bool = True
) -> pd.DataFrame:
    """Rank equipment by priority score for cost reduction action.

    Process:
    1. Calculate cost impact and priority scores
    2. Sort by priority_score descending within categories
    3. Assign category_rank (rank within category)
    4. Assign overall_rank (rank across all categories)
    5. Filter to consensus outliers only (focused results)

    Args:
        outlier_df: DataFrame with outlier detection results
        exclude_no_equipment: If True (default), exclude 'No Equipment' category
            from ranking. These records represent interior/general maintenance
            without specific equipment to prioritize.

    Returns:
        DataFrame with ranked consensus outliers, sorted by priority
    """
    # Filter out 'No Equipment' category if requested
    if exclude_no_equipment and 'equipment_primary_category' in outlier_df.columns:
        no_equip_mask = outlier_df['equipment_primary_category'] == 'No Equipment'
        if no_equip_mask.any():
            outlier_df = outlier_df[~no_equip_mask]

    # Calculate metrics
    df = calculate_cost_impact(outlier_df)
    df = calculate_priority_score(df)

    # Sort by priority score descending
    df = df.sort_values('priority_score', ascending=False)

    # Assign overall rank (across all categories)
    df['overall_rank'] = range(1, len(df) + 1)

    # Assign category rank (within each category)
    df['category_rank'] = df.groupby('equipment_primary_category').cumcount() + 1

    # Filter to consensus outliers only (focused results)
    ranked = df[df['is_outlier_consensus']].copy()

    # Re-rank after filtering
    ranked = ranked.sort_values('priority_score', ascending=False)
    ranked['overall_rank'] = range(1, len(ranked) + 1)

    # Recalculate category ranks for outliers only
    ranked['category_rank'] = ranked.groupby('equipment_primary_category').cumcount() + 1

    return ranked


def rank_all_equipment(
    freq_df: pd.DataFrame,
    exclude_no_equipment: bool = True
) -> pd.DataFrame:
    """Rank ALL equipment by priority score (not just outliers).

    Similar to rank_equipment but returns all equipment items sorted by
    priority score, useful for seeing the full equipment landscape.

    Args:
        freq_df: DataFrame from calculate_equipment_frequencies() with:
            - Equipment_ID, Equipment_Name, equipment_primary_category
            - total_work_orders, work_orders_per_month, avg_cost
        exclude_no_equipment: If True (default), exclude 'No Equipment' category

    Returns:
        DataFrame with all equipment ranked by priority_score
    """
    # Filter out 'No Equipment' category if requested
    if exclude_no_equipment and 'equipment_primary_category' in freq_df.columns:
        no_equip_mask = freq_df['equipment_primary_category'] == 'No Equipment'
        if no_equip_mask.any():
            freq_df = freq_df[~no_equip_mask]

    if len(freq_df) == 0:
        return pd.DataFrame()

    df = freq_df.copy()

    # Calculate cost impact
    df['cost_impact'] = df['total_work_orders'] * df['avg_cost'].fillna(0)

    # Calculate normalized scores within each category
    df['freq_score'] = 0.0
    df['cost_score'] = 0.0

    for category in df['equipment_primary_category'].unique():
        cat_mask = df['equipment_primary_category'] == category
        cat_df = df[cat_mask]

        # Normalize frequency score (0-1)
        freq_min = cat_df['work_orders_per_month'].min()
        freq_max = cat_df['work_orders_per_month'].max()
        if freq_max > freq_min:
            df.loc[cat_mask, 'freq_score'] = (
                (cat_df['work_orders_per_month'] - freq_min) / (freq_max - freq_min)
            )
        else:
            df.loc[cat_mask, 'freq_score'] = 0.5

        # Normalize cost score (0-1)
        cost_min = cat_df['cost_impact'].min()
        cost_max = cat_df['cost_impact'].max()
        if cost_max > cost_min:
            df.loc[cat_mask, 'cost_score'] = (
                (cat_df['cost_impact'] - cost_min) / (cost_max - cost_min)
            )
        else:
            df.loc[cat_mask, 'cost_score'] = 0.5

    # Calculate priority score (frequency 50%, cost 50% - no outlier bonus)
    df['priority_score'] = (df['freq_score'] * 0.5) + (df['cost_score'] * 0.5)

    # Sort and rank
    df = df.sort_values('priority_score', ascending=False)
    df['overall_rank'] = range(1, len(df) + 1)
    df['category_rank'] = df.groupby('equipment_primary_category').cumcount() + 1

    return df


def identify_thresholds(ranked_df: pd.DataFrame) -> Dict[str, float]:
    """Identify threshold recommendations from ranked outliers.

    Analyzes ranked consensus outliers to suggest thresholds for future analysis:
    - frequency_threshold: Median work_orders_per_month of outliers
    - cost_threshold: Median cost_impact of outliers
    - percentile_threshold: Standard 90th percentile (already used)

    Args:
        ranked_df: DataFrame with ranked consensus outliers

    Returns:
        Dict with threshold recommendations and rationale
    """
    if len(ranked_df) == 0:
        return {
            'frequency_threshold': 0.0,
            'cost_threshold': 0.0,
            'percentile_threshold': 90.0,
            'rationale': 'No consensus outliers found - insufficient data for threshold recommendations'
        }

    # Calculate median thresholds from consensus outliers
    freq_threshold = ranked_df['work_orders_per_month'].median()
    cost_threshold = ranked_df['cost_impact'].median()

    return {
        'frequency_threshold': freq_threshold,
        'cost_threshold': cost_threshold,
        'percentile_threshold': 90.0,  # Standard percentile used
        'rationale': (
            f'Equipment exceeding {freq_threshold:.2f} work orders/month '
            f'or ${cost_threshold:,.0f} cost impact in their category warrant review'
        )
    }
