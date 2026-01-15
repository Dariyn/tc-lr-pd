"""
Vendor/contractor cost performance analysis module.

Purpose: Identify high-cost vendors, efficiency patterns, and quality issues
to inform vendor selection and contract negotiations.
"""

import pandas as pd
import logging
from typing import Optional, Literal, List, Dict, Any

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

    def calculate_cost_efficiency(
        self,
        df: pd.DataFrame,
        include_unknown: bool = False
    ) -> pd.DataFrame:
        """
        Calculate cost efficiency for vendors (cost per day).

        Cost efficiency = avg_cost_per_wo / avg_duration_days
        Lower values indicate better efficiency (less cost per day of work).

        Args:
            df: DataFrame with work order data
            include_unknown: If True, include contractors with missing names (default: False)

        Returns:
            DataFrame with columns:
            - contractor: Contractor name
            - avg_cost_per_wo: Average cost per work order
            - avg_duration_days: Average completion days
            - cost_per_day: Cost efficiency (cost per day)
            - work_order_count: Number of work orders
        """
        # Get ranked vendors (includes both cost and duration)
        vendor_df = self.rank_vendors(df, by='total_cost', include_unknown=include_unknown)

        if len(vendor_df) == 0:
            return pd.DataFrame(columns=[
                'contractor', 'avg_cost_per_wo', 'avg_duration_days',
                'cost_per_day', 'work_order_count'
            ])

        # Calculate cost per day (only for vendors with duration data)
        result_rows = []
        for _, row in vendor_df.iterrows():
            if pd.notna(row['avg_duration_days']) and row['avg_duration_days'] > 0:
                cost_per_day = row['avg_cost_per_wo'] / row['avg_duration_days']
                result_rows.append({
                    'contractor': row['contractor'],
                    'avg_cost_per_wo': row['avg_cost_per_wo'],
                    'avg_duration_days': row['avg_duration_days'],
                    'cost_per_day': cost_per_day,
                    'work_order_count': row['work_order_count']
                })

        result_df = pd.DataFrame(result_rows)

        if len(result_df) > 0:
            # Sort by cost per day (lower is better)
            result_df = result_df.sort_values('cost_per_day', ascending=True).reset_index(drop=True)

        logger.info(f"Calculated cost efficiency for {len(result_df)} contractors")

        return result_df

    def calculate_quality_indicators(
        self,
        df: pd.DataFrame,
        include_unknown: bool = False
    ) -> pd.DataFrame:
        """
        Calculate quality indicators for vendors based on repeat issues.

        Identifies potential rework by counting work orders for the same equipment
        by the same contractor. Higher repeat counts may indicate quality issues.

        Args:
            df: DataFrame with work order data, must include:
                - Contractor: Vendor/contractor name
                - Equipment_ID: Equipment identifier
                - Problem (optional): Problem description for analysis
                - Remedy (optional): Remedy description for analysis
            include_unknown: If True, include contractors with missing names (default: False)

        Returns:
            DataFrame with columns:
            - contractor: Contractor name
            - total_work_orders: Total work orders
            - unique_equipment: Number of unique equipment serviced
            - repeat_equipment_count: Number of equipment with 2+ work orders
            - repeat_rate: Percentage of repeat equipment (potential rework indicator)
        """
        # Handle missing Contractor values
        df_work = df.copy()
        df_work['Contractor'] = df_work['Contractor'].fillna(self.unknown_label)

        # Filter out unknown if requested
        if not include_unknown:
            df_work = df_work[df_work['Contractor'] != self.unknown_label]

        results = []

        # Group by contractor
        for contractor, contractor_group in df_work.groupby('Contractor'):
            work_order_count = len(contractor_group)

            # Filter by minimum work order threshold
            if work_order_count < self.min_work_orders:
                continue

            # Count work orders per equipment for this contractor
            equipment_counts = contractor_group.groupby('Equipment_ID').size()
            unique_equipment = len(equipment_counts)
            repeat_equipment_count = (equipment_counts >= 2).sum()
            repeat_rate = (repeat_equipment_count / unique_equipment * 100) if unique_equipment > 0 else 0

            results.append({
                'contractor': contractor,
                'total_work_orders': work_order_count,
                'unique_equipment': unique_equipment,
                'repeat_equipment_count': repeat_equipment_count,
                'repeat_rate': repeat_rate
            })

        result_df = pd.DataFrame(results)

        if len(result_df) > 0:
            # Sort by repeat rate descending (higher = more potential quality issues)
            result_df = result_df.sort_values('repeat_rate', ascending=False).reset_index(drop=True)

        logger.info(f"Calculated quality indicators for {len(result_df)} contractors")

        return result_df

    def get_vendor_recommendations(
        self,
        df: pd.DataFrame,
        include_unknown: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Generate actionable recommendations based on vendor metrics.

        Analyzes vendor performance across cost, duration, efficiency, and quality
        to identify vendors needing review or contract renegotiation.

        Args:
            df: DataFrame with work order data
            include_unknown: If True, include contractors with missing names (default: False)

        Returns:
            List of recommendation dictionaries with:
            - vendor: Contractor name
            - issue: Issue category (High cost, Slow completion, Low efficiency, Quality concerns)
            - metric: Specific metric value
            - suggestion: Actionable recommendation
        """
        recommendations = []

        # Get various metrics
        cost_df = self.calculate_vendor_costs(df, include_unknown=include_unknown)
        duration_df = self.calculate_vendor_duration(df, include_unknown=include_unknown)
        efficiency_df = self.calculate_cost_efficiency(df, include_unknown=include_unknown)
        quality_df = self.calculate_quality_indicators(df, include_unknown=include_unknown)

        # High cost vendors (top 25%)
        if len(cost_df) > 0:
            high_cost_threshold = cost_df['total_cost'].quantile(0.75)
            high_cost_vendors = cost_df[cost_df['total_cost'] >= high_cost_threshold]

            for _, row in high_cost_vendors.iterrows():
                recommendations.append({
                    'vendor': row['contractor'],
                    'issue': 'High cost',
                    'metric': f"${row['total_cost']:,.2f} total ({row['work_order_count']} WOs)",
                    'suggestion': 'Review contract terms and pricing structure for potential cost savings'
                })

        # Slow completion vendors (top 25%)
        if len(duration_df) > 0:
            slow_threshold = duration_df['avg_duration_days'].quantile(0.75)
            slow_vendors = duration_df[duration_df['avg_duration_days'] >= slow_threshold]

            for _, row in slow_vendors.iterrows():
                recommendations.append({
                    'vendor': row['contractor'],
                    'issue': 'Slow completion',
                    'metric': f"{row['avg_duration_days']:.1f} days average",
                    'suggestion': 'Discuss completion time expectations and potential service level agreements'
                })

        # Low efficiency vendors (top 25% cost per day)
        if len(efficiency_df) > 0:
            inefficient_threshold = efficiency_df['cost_per_day'].quantile(0.75)
            inefficient_vendors = efficiency_df[efficiency_df['cost_per_day'] >= inefficient_threshold]

            for _, row in inefficient_vendors.iterrows():
                recommendations.append({
                    'vendor': row['contractor'],
                    'issue': 'Low efficiency',
                    'metric': f"${row['cost_per_day']:.2f} per day",
                    'suggestion': 'Evaluate work efficiency and consider alternative vendors for comparison'
                })

        # Quality concerns (repeat rate > 50%)
        if len(quality_df) > 0:
            quality_concern_vendors = quality_df[quality_df['repeat_rate'] > 50]

            for _, row in quality_concern_vendors.iterrows():
                recommendations.append({
                    'vendor': row['contractor'],
                    'issue': 'Quality concerns',
                    'metric': f"{row['repeat_rate']:.1f}% repeat equipment rate",
                    'suggestion': 'Investigate repeat work orders on same equipment for potential quality issues'
                })

        logger.info(f"Generated {len(recommendations)} vendor recommendations")

        return recommendations
