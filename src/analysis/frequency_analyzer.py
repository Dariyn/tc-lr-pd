"""
Frequency analysis module for calculating work order rates and category statistics.

Purpose: Establish baseline frequency metrics to enable statistical comparison
and outlier detection for equipment within their categories.
"""

import pandas as pd
import logging

logger = logging.getLogger(__name__)


def calculate_equipment_frequencies(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate work order frequency metrics for each equipment item.

    Groups equipment by their primary category and calculates:
    - Total work orders
    - Timespan (days between first and last work order)
    - Work orders per month (normalized rate)
    - Average completion time
    - Average cost

    Args:
        df: DataFrame with work order data, must include:
            - Equipment_ID
            - equipment_primary_category
            - Create_Date
            - Complete_Date (optional)
            - PO_AMOUNT (optional)

    Returns:
        DataFrame with equipment-level frequency statistics:
        - Equipment_ID
        - equipment_primary_category
        - total_work_orders
        - timespan_days
        - work_orders_per_month
        - avg_completion_days
        - avg_cost
    """
    # Group by equipment and category
    grouped = df.groupby(['Equipment_ID', 'equipment_primary_category'])

    results = []

    for (equipment_id, category), group in grouped:
        # Calculate total work orders
        total_work_orders = len(group)

        # Calculate timespan from Create_Date
        valid_create_dates = group['Create_Date'].dropna()
        if len(valid_create_dates) > 0:
            min_date = valid_create_dates.min()
            max_date = valid_create_dates.max()
            timespan_days = (max_date - min_date).days + 1  # +1 to include both dates
        else:
            timespan_days = 1  # Default for missing dates

        # Ensure minimum timespan of 1 day
        if timespan_days < 1:
            timespan_days = 1

        # Calculate work orders per month (30.44 avg days/month)
        work_orders_per_month = (total_work_orders / timespan_days) * 30.44

        # Calculate average completion days
        # Only use rows where both Create_Date and Complete_Date exist
        completion_times = []
        for _, row in group.iterrows():
            if pd.notna(row['Create_Date']) and pd.notna(row['Complete_Date']):
                days = (row['Complete_Date'] - row['Create_Date']).days
                completion_times.append(days)

        avg_completion_days = sum(completion_times) / len(completion_times) if completion_times else None

        # Calculate average cost (exclude zero and negative costs)
        valid_costs = group[group['PO_AMOUNT'] > 0]['PO_AMOUNT']
        avg_cost = valid_costs.mean() if len(valid_costs) > 0 else None

        results.append({
            'Equipment_ID': equipment_id,
            'equipment_primary_category': category,
            'total_work_orders': total_work_orders,
            'timespan_days': timespan_days,
            'work_orders_per_month': work_orders_per_month,
            'avg_completion_days': avg_completion_days,
            'avg_cost': avg_cost
        })

    result_df = pd.DataFrame(results)

    logger.info(f"Calculated frequencies for {len(result_df)} equipment items")
    logger.info(f"Across {result_df['equipment_primary_category'].nunique()} categories")

    return result_df


def calculate_category_statistics(freq_df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate category-level statistics from equipment frequency data.

    Aggregates equipment frequency metrics by category to establish baselines
    for comparison and outlier detection.

    Args:
        freq_df: DataFrame from calculate_equipment_frequencies() with:
            - equipment_primary_category
            - total_work_orders
            - work_orders_per_month

    Returns:
        DataFrame with category-level statistics:
        - equipment_primary_category
        - equipment_count
        - total_work_orders
        - mean_frequency
        - median_frequency
        - std_frequency
        - min_frequency
        - max_frequency
    """
    # Group by category
    grouped = freq_df.groupby('equipment_primary_category')

    stats = []

    for category, group in grouped:
        stats.append({
            'equipment_primary_category': category,
            'equipment_count': len(group),
            'total_work_orders': group['total_work_orders'].sum(),
            'mean_frequency': group['work_orders_per_month'].mean(),
            'median_frequency': group['work_orders_per_month'].median(),
            'std_frequency': group['work_orders_per_month'].std(),
            'min_frequency': group['work_orders_per_month'].min(),
            'max_frequency': group['work_orders_per_month'].max()
        })

    stats_df = pd.DataFrame(stats)

    logger.info(f"Calculated statistics for {len(stats_df)} categories")

    return stats_df
