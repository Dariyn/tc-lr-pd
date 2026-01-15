"""
Vendor/contractor cost performance analysis module.

Purpose: Identify high-cost vendors, efficiency patterns, and quality issues
to inform vendor selection and contract negotiations.
"""

import pandas as pd
import logging
from typing import Optional, Literal

logger = logging.getLogger(__name__)


class VendorAnalyzer:
    """
    Analyzes vendor/contractor performance across cost, duration, and quality metrics.

    This class provides methods to:
    - Aggregate costs by contractor
    - Calculate performance metrics (cost, duration, efficiency)
    - Rank vendors by various criteria
    - Identify high-cost vendors for review
    """

    def __init__(self, min_work_orders: int = 3, unknown_label: str = "Unknown"):
        """
        Initialize VendorAnalyzer with configuration parameters.

        Args:
            min_work_orders: Minimum work order count to include vendor (default: 3)
            unknown_label: Label for missing Contractor values (default: "Unknown")
        """
        self.min_work_orders = min_work_orders
        self.unknown_label = unknown_label

    def calculate_vendor_costs(
        self,
        df: pd.DataFrame,
        include_unknown: bool = False
    ) -> pd.DataFrame:
        """
        Calculate cost aggregations by vendor/contractor.

        Groups work orders by Contractor and calculates:
        - total_cost: Sum of all PO_AMOUNT values
        - work_order_count: Number of work orders
        - avg_cost_per_wo: Average cost per work order

        Args:
            df: DataFrame with work order data, must include:
                - Contractor: Vendor/contractor name
                - PO_AMOUNT: Cost amount
            include_unknown: If True, include contractors with missing names (default: False)

        Returns:
            DataFrame with columns:
            - contractor: Contractor name
            - total_cost: Total cost across all work orders
            - work_order_count: Number of work orders
            - avg_cost_per_wo: Average cost per work order
        """
        # Handle missing Contractor values
        df_work = df.copy()
        df_work['Contractor'] = df_work['Contractor'].fillna(self.unknown_label)

        # Filter out unknown if requested
        if not include_unknown:
            df_work = df_work[df_work['Contractor'] != self.unknown_label]

        # Group by contractor
        grouped = df_work.groupby('Contractor')

        results = []
        for contractor, group in grouped:
            work_order_count = len(group)

            # Filter by minimum work order threshold
            if work_order_count < self.min_work_orders:
                continue

            # Calculate cost metrics
            total_cost = group['PO_AMOUNT'].sum()
            avg_cost_per_wo = group['PO_AMOUNT'].mean()

            results.append({
                'contractor': contractor,
                'total_cost': total_cost,
                'work_order_count': work_order_count,
                'avg_cost_per_wo': avg_cost_per_wo
            })

        result_df = pd.DataFrame(results)

        if len(result_df) > 0:
            # Sort by total cost descending
            result_df = result_df.sort_values('total_cost', ascending=False).reset_index(drop=True)

        logger.info(f"Calculated costs for {len(result_df)} contractors")

        return result_df

    def calculate_vendor_duration(
        self,
        df: pd.DataFrame,
        include_unknown: bool = False
    ) -> pd.DataFrame:
        """
        Calculate average completion time by vendor/contractor.

        Calculates the average number of days between Create_Date and Complete_Date
        for each contractor. Only includes work orders with valid date data.

        Args:
            df: DataFrame with work order data, must include:
                - Contractor: Vendor/contractor name
                - Create_Date: Work order creation date
                - Complete_Date: Work order completion date
            include_unknown: If True, include contractors with missing names (default: False)

        Returns:
            DataFrame with columns:
            - contractor: Contractor name
            - work_order_count: Number of work orders with valid dates
            - avg_duration_days: Average completion time in days
        """
        # Handle missing Contractor values
        df_work = df.copy()
        df_work['Contractor'] = df_work['Contractor'].fillna(self.unknown_label)

        # Filter out unknown if requested
        if not include_unknown:
            df_work = df_work[df_work['Contractor'] != self.unknown_label]

        # Filter to rows with valid dates
        df_work = df_work[
            pd.notna(df_work['Create_Date']) &
            pd.notna(df_work['Complete_Date'])
        ].copy()

        # Calculate duration
        df_work['duration_days'] = (
            df_work['Complete_Date'] - df_work['Create_Date']
        ).dt.days

        # Group by contractor
        grouped = df_work.groupby('Contractor')

        results = []
        for contractor, group in grouped:
            work_order_count = len(group)

            # Filter by minimum work order threshold
            if work_order_count < self.min_work_orders:
                continue

            avg_duration_days = group['duration_days'].mean()

            results.append({
                'contractor': contractor,
                'work_order_count': work_order_count,
                'avg_duration_days': avg_duration_days
            })

        result_df = pd.DataFrame(results)

        if len(result_df) > 0:
            # Sort by average duration descending
            result_df = result_df.sort_values('avg_duration_days', ascending=False).reset_index(drop=True)

        logger.info(f"Calculated duration for {len(result_df)} contractors")

        return result_df

    def rank_vendors(
        self,
        df: pd.DataFrame,
        by: Literal['total_cost', 'avg_cost', 'work_order_count'] = 'total_cost',
        include_unknown: bool = False
    ) -> pd.DataFrame:
        """
        Rank vendors by specified metric.

        Combines cost and duration data to rank vendors. Higher values = higher rank.

        Args:
            df: DataFrame with work order data
            by: Ranking metric - 'total_cost', 'avg_cost', or 'work_order_count'
            include_unknown: If True, include contractors with missing names (default: False)

        Returns:
            DataFrame with columns:
            - contractor: Contractor name
            - total_cost: Total cost
            - work_order_count: Number of work orders
            - avg_cost_per_wo: Average cost per work order
            - avg_duration_days: Average completion days (if available)
            - rank: Rank by specified metric (1 = highest)
        """
        # Get cost data
        cost_df = self.calculate_vendor_costs(df, include_unknown=include_unknown)

        if len(cost_df) == 0:
            return pd.DataFrame(columns=[
                'contractor', 'total_cost', 'work_order_count',
                'avg_cost_per_wo', 'avg_duration_days', 'rank'
            ])

        # Get duration data
        duration_df = self.calculate_vendor_duration(df, include_unknown=include_unknown)

        # Merge cost and duration
        if len(duration_df) > 0:
            result_df = cost_df.merge(
                duration_df[['contractor', 'avg_duration_days']],
                on='contractor',
                how='left'
            )
        else:
            result_df = cost_df.copy()
            result_df['avg_duration_days'] = None

        # Determine ranking column
        rank_column_map = {
            'total_cost': 'total_cost',
            'avg_cost': 'avg_cost_per_wo',
            'work_order_count': 'work_order_count'
        }
        rank_column = rank_column_map[by]

        # Sort by ranking metric (descending) and add rank
        result_df = result_df.sort_values(rank_column, ascending=False).reset_index(drop=True)
        result_df['rank'] = range(1, len(result_df) + 1)

        logger.info(f"Ranked {len(result_df)} contractors by {by}")

        return result_df

    def identify_high_cost_vendors(
        self,
        df: pd.DataFrame,
        threshold: Literal['75th_percentile', '90th_percentile', 'top_10'] = '75th_percentile',
        include_unknown: bool = False
    ) -> pd.DataFrame:
        """
        Identify vendors exceeding cost thresholds.

        Flags vendors with total costs above specified threshold for review.

        Args:
            df: DataFrame with work order data
            threshold: Threshold method:
                - '75th_percentile': Above 75th percentile of total cost
                - '90th_percentile': Above 90th percentile of total cost
                - 'top_10': Top 10 vendors by total cost
            include_unknown: If True, include contractors with missing names (default: False)

        Returns:
            DataFrame with high-cost vendors:
            - contractor: Contractor name
            - total_cost: Total cost
            - work_order_count: Number of work orders
            - avg_cost_per_wo: Average cost per work order
            - cost_threshold: The threshold value used
        """
        # Get cost data
        cost_df = self.calculate_vendor_costs(df, include_unknown=include_unknown)

        if len(cost_df) == 0:
            return pd.DataFrame(columns=[
                'contractor', 'total_cost', 'work_order_count',
                'avg_cost_per_wo', 'cost_threshold'
            ])

        # Calculate threshold
        if threshold == '75th_percentile':
            threshold_value = cost_df['total_cost'].quantile(0.75)
            high_cost_df = cost_df[cost_df['total_cost'] >= threshold_value].copy()
        elif threshold == '90th_percentile':
            threshold_value = cost_df['total_cost'].quantile(0.90)
            high_cost_df = cost_df[cost_df['total_cost'] >= threshold_value].copy()
        elif threshold == 'top_10':
            high_cost_df = cost_df.head(10).copy()
            threshold_value = high_cost_df['total_cost'].min() if len(high_cost_df) > 0 else 0
        else:
            raise ValueError(f"Invalid threshold: {threshold}")

        high_cost_df['cost_threshold'] = threshold_value

        logger.info(
            f"Identified {len(high_cost_df)} high-cost contractors "
            f"(threshold: {threshold}, value: ${threshold_value:,.2f})"
        )

        return high_cost_df
