"""
Seasonal cost analysis for work orders.

This module provides tools to analyze seasonal patterns in work order costs,
identifying trends across months, quarters, and seasons to inform budget planning
and preventive maintenance scheduling.
"""

import pandas as pd
from typing import Dict, List, Optional


class SeasonalAnalyzer:
    """
    Analyzes seasonal trends in work order costs.

    Provides methods to aggregate costs by time periods (monthly, quarterly, seasonal)
    and identify patterns such as recurring high-cost periods.
    """

    # Season mapping: month number to season name
    SEASON_MAP = {
        12: 'Winter', 1: 'Winter', 2: 'Winter',
        3: 'Spring', 4: 'Spring', 5: 'Spring',
        6: 'Summer', 7: 'Summer', 8: 'Summer',
        9: 'Fall', 10: 'Fall', 11: 'Fall'
    }

    def calculate_monthly_costs(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Aggregate work order costs by month.

        Groups work orders by completion month and calculates total costs,
        average costs, and work order counts for each month.

        Args:
            df: DataFrame with 'Complete_Date' and 'PO_AMOUNT' columns

        Returns:
            DataFrame with columns:
                - period: Month name (e.g., 'January', 'February')
                - total_cost: Sum of PO_AMOUNT for the month
                - avg_cost: Average PO_AMOUNT for the month
                - work_order_count: Number of work orders in the month

        Example:
            >>> df = load_work_orders('data.csv')
            >>> analyzer = SeasonalAnalyzer()
            >>> monthly = analyzer.calculate_monthly_costs(df)
            >>> print(monthly.head())
        """
        # Handle empty dataframe
        if df.empty:
            return pd.DataFrame(columns=['period', 'total_cost', 'avg_cost', 'work_order_count'])

        # Filter to valid dates and costs
        valid_df = df[df['Complete_Date'].notna() & df['PO_AMOUNT'].notna()].copy()

        if valid_df.empty:
            return pd.DataFrame(columns=['period', 'total_cost', 'avg_cost', 'work_order_count'])

        # Extract month and month name
        valid_df['month'] = valid_df['Complete_Date'].dt.month
        valid_df['month_name'] = valid_df['Complete_Date'].dt.month_name()

        # Group by month
        monthly = valid_df.groupby(['month', 'month_name']).agg(
            total_cost=('PO_AMOUNT', 'sum'),
            avg_cost=('PO_AMOUNT', 'mean'),
            work_order_count=('PO_AMOUNT', 'count')
        ).reset_index()

        # Rename month_name to period and drop month number
        monthly = monthly.rename(columns={'month_name': 'period'})
        monthly = monthly[['period', 'total_cost', 'avg_cost', 'work_order_count']]

        return monthly

    def calculate_quarterly_costs(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Aggregate work order costs by quarter.

        Groups work orders by completion quarter (Q1-Q4) and calculates total costs,
        average costs, and work order counts for each quarter.

        Args:
            df: DataFrame with 'Complete_Date' and 'PO_AMOUNT' columns

        Returns:
            DataFrame with columns:
                - period: Quarter name (e.g., 'Q1', 'Q2')
                - total_cost: Sum of PO_AMOUNT for the quarter
                - avg_cost: Average PO_AMOUNT for the quarter
                - work_order_count: Number of work orders in the quarter

        Example:
            >>> df = load_work_orders('data.csv')
            >>> analyzer = SeasonalAnalyzer()
            >>> quarterly = analyzer.calculate_quarterly_costs(df)
            >>> print(quarterly)
        """
        # Handle empty dataframe
        if df.empty:
            return pd.DataFrame(columns=['period', 'total_cost', 'avg_cost', 'work_order_count'])

        # Filter to valid dates and costs
        valid_df = df[df['Complete_Date'].notna() & df['PO_AMOUNT'].notna()].copy()

        if valid_df.empty:
            return pd.DataFrame(columns=['period', 'total_cost', 'avg_cost', 'work_order_count'])

        # Extract quarter
        valid_df['quarter'] = valid_df['Complete_Date'].dt.quarter
        valid_df['quarter_name'] = 'Q' + valid_df['quarter'].astype(str)

        # Group by quarter
        quarterly = valid_df.groupby(['quarter', 'quarter_name']).agg(
            total_cost=('PO_AMOUNT', 'sum'),
            avg_cost=('PO_AMOUNT', 'mean'),
            work_order_count=('PO_AMOUNT', 'count')
        ).reset_index()

        # Rename quarter_name to period and drop quarter number
        quarterly = quarterly.rename(columns={'quarter_name': 'period'})
        quarterly = quarterly[['period', 'total_cost', 'avg_cost', 'work_order_count']]

        return quarterly

    def calculate_seasonal_costs(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Aggregate work order costs by season.

        Groups work orders by meteorological season (Winter/Spring/Summer/Fall)
        and calculates total costs, average costs, and work order counts.

        Season mapping:
            - Winter: December, January, February
            - Spring: March, April, May
            - Summer: June, July, August
            - Fall: September, October, November

        Args:
            df: DataFrame with 'Complete_Date' and 'PO_AMOUNT' columns

        Returns:
            DataFrame with columns:
                - period: Season name (e.g., 'Winter', 'Spring')
                - total_cost: Sum of PO_AMOUNT for the season
                - avg_cost: Average PO_AMOUNT for the season
                - work_order_count: Number of work orders in the season

        Example:
            >>> df = load_work_orders('data.csv')
            >>> analyzer = SeasonalAnalyzer()
            >>> seasonal = analyzer.calculate_seasonal_costs(df)
            >>> print(seasonal)
        """
        # Handle empty dataframe
        if df.empty:
            return pd.DataFrame(columns=['period', 'total_cost', 'avg_cost', 'work_order_count'])

        # Filter to valid dates and costs
        valid_df = df[df['Complete_Date'].notna() & df['PO_AMOUNT'].notna()].copy()

        if valid_df.empty:
            return pd.DataFrame(columns=['period', 'total_cost', 'avg_cost', 'work_order_count'])

        # Map month to season
        valid_df['month'] = valid_df['Complete_Date'].dt.month
        valid_df['season'] = valid_df['month'].map(self.SEASON_MAP)

        # Group by season
        seasonal = valid_df.groupby('season').agg(
            total_cost=('PO_AMOUNT', 'sum'),
            avg_cost=('PO_AMOUNT', 'mean'),
            work_order_count=('PO_AMOUNT', 'count')
        ).reset_index()

        # Rename season to period
        seasonal = seasonal.rename(columns={'season': 'period'})

        # Sort by season order (Winter, Spring, Summer, Fall)
        season_order = ['Winter', 'Spring', 'Summer', 'Fall']
        seasonal['sort_order'] = seasonal['period'].map({s: i for i, s in enumerate(season_order)})
        seasonal = seasonal.sort_values('sort_order').drop(columns=['sort_order'])

        return seasonal

    def identify_peaks(self, series: pd.Series, threshold: float = 1.2) -> pd.Series:
        """
        Identify periods where costs exceed a threshold multiple of the average.

        Flags periods (months, quarters, or seasons) where costs are significantly
        higher than the average across all periods.

        Args:
            series: Series of costs (typically 'total_cost' column from aggregation)
            threshold: Multiplier of average cost to flag as peak (default: 1.2 = 20% above avg)

        Returns:
            Boolean Series where True indicates a peak period

        Example:
            >>> monthly = analyzer.calculate_monthly_costs(df)
            >>> peaks = analyzer.identify_peaks(monthly['total_cost'], threshold=1.2)
            >>> monthly['is_peak'] = peaks
            >>> print(monthly[monthly['is_peak']])
        """
        # Handle empty series
        if series.empty:
            return pd.Series([], dtype=bool)

        # Calculate average
        avg_cost = series.mean()

        # Flag values exceeding threshold
        return series > (avg_cost * threshold)
