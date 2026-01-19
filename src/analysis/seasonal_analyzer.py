"""
Seasonal cost analysis for work orders.

This module provides tools to analyze seasonal patterns in work order costs,
identifying trends across months, quarters, and seasons to inform budget planning
and preventive maintenance scheduling.

Uses Create_Date (when repair was requested) to capture when equipment failures
actually occur, rather than Complete_Date (when work was finished).
"""

import pandas as pd
from typing import Dict, List, Optional


class SeasonalAnalyzer:
    """
    Analyzes seasonal trends in work order costs.

    Provides methods to aggregate costs by time periods (monthly, quarterly, seasonal)
    and identify patterns such as recurring high-cost periods.

    Uses Create_Date by default to analyze when failures occur, not when they're fixed.
    """

    # Season mapping: month number to season name
    SEASON_MAP = {
        12: 'Winter', 1: 'Winter', 2: 'Winter',
        3: 'Spring', 4: 'Spring', 5: 'Spring',
        6: 'Summer', 7: 'Summer', 8: 'Summer',
        9: 'Fall', 10: 'Fall', 11: 'Fall'
    }

    def _get_date_column(self, df: pd.DataFrame) -> str:
        """
        Determine which date column to use for analysis.

        Prefers create_date_yyyymmdd (when failure occurred) over Complete_Date.

        Args:
            df: DataFrame with date columns

        Returns:
            Name of the date column to use
        """
        # Prefer create_date_yyyymmdd as it shows when the failure actually occurred
        if 'create_date_yyyymmdd' in df.columns and df['create_date_yyyymmdd'].notna().any():
            return 'create_date_yyyymmdd'
        elif 'Create_Date' in df.columns and df['Create_Date'].notna().any():
            return 'Create_Date'
        elif 'Complete_Date' in df.columns and df['Complete_Date'].notna().any():
            return 'Complete_Date'
        return None

    def calculate_monthly_costs(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Aggregate work order costs by month.

        Groups work orders by creation month (when repair was requested) and
        calculates total costs, average costs, and work order counts for each month.

        Args:
            df: DataFrame with 'Create_Date' (or 'Complete_Date') and 'PO_AMOUNT' columns

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

        # Determine which date column to use
        date_col = self._get_date_column(df)
        if date_col is None:
            return pd.DataFrame(columns=['period', 'total_cost', 'avg_cost', 'work_order_count'])

        # Filter to valid dates and costs
        valid_df = df[df[date_col].notna() & df['PO_AMOUNT'].notna()].copy()

        if valid_df.empty:
            return pd.DataFrame(columns=['period', 'total_cost', 'avg_cost', 'work_order_count'])

        # Extract month and month name
        valid_df['month'] = valid_df[date_col].dt.month
        valid_df['month_name'] = valid_df[date_col].dt.month_name()

        # Group by month
        monthly = valid_df.groupby(['month', 'month_name']).agg(
            total_cost=('PO_AMOUNT', 'sum'),
            avg_cost=('PO_AMOUNT', 'mean'),
            work_order_count=('PO_AMOUNT', 'count')
        ).reset_index()

        # Sort by month number for proper ordering
        monthly = monthly.sort_values('month')

        # Rename month_name to period and drop month number
        monthly = monthly.rename(columns={'month_name': 'period'})
        monthly = monthly[['period', 'total_cost', 'avg_cost', 'work_order_count']]

        return monthly

    def calculate_monthly_costs_by_year(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Aggregate work order costs by year and month.

        Groups work orders by creation year and month (when repair was requested)
        and calculates total costs, average costs, and work order counts.

        Args:
            df: DataFrame with 'Create_Date' (or 'Complete_Date') and 'PO_AMOUNT' columns

        Returns:
            DataFrame with columns:
                - year: Year number (e.g., 2024)
                - month: Month number (1-12)
                - period: Month name (e.g., 'January')
                - total_cost: Sum of PO_AMOUNT for the month
                - avg_cost: Average PO_AMOUNT for the month
                - work_order_count: Number of work orders in the month
        """
        if df.empty:
            return pd.DataFrame(columns=[
                'year', 'month', 'period', 'total_cost', 'avg_cost', 'work_order_count'
            ])

        date_col = self._get_date_column(df)
        if date_col is None:
            return pd.DataFrame(columns=[
                'year', 'month', 'period', 'total_cost', 'avg_cost', 'work_order_count'
            ])

        valid_df = df[df[date_col].notna() & df['PO_AMOUNT'].notna()].copy()
        if valid_df.empty:
            return pd.DataFrame(columns=[
                'year', 'month', 'period', 'total_cost', 'avg_cost', 'work_order_count'
            ])

        valid_df['year'] = valid_df[date_col].dt.year
        valid_df['month'] = valid_df[date_col].dt.month
        valid_df['month_name'] = valid_df[date_col].dt.month_name()

        monthly = valid_df.groupby(['year', 'month', 'month_name']).agg(
            total_cost=('PO_AMOUNT', 'sum'),
            avg_cost=('PO_AMOUNT', 'mean'),
            work_order_count=('PO_AMOUNT', 'count')
        ).reset_index()

        monthly = monthly.sort_values(['year', 'month'])
        monthly = monthly.rename(columns={'month_name': 'period'})
        monthly = monthly[['year', 'month', 'period', 'total_cost', 'avg_cost', 'work_order_count']]

        return monthly

    def calculate_quarterly_costs(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Aggregate work order costs by quarter.

        Groups work orders by creation quarter (Q1-Q4) and calculates total costs,
        average costs, and work order counts for each quarter.

        Args:
            df: DataFrame with 'Create_Date' (or 'Complete_Date') and 'PO_AMOUNT' columns

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

        # Determine which date column to use
        date_col = self._get_date_column(df)
        if date_col is None:
            return pd.DataFrame(columns=['period', 'total_cost', 'avg_cost', 'work_order_count'])

        # Filter to valid dates and costs
        valid_df = df[df[date_col].notna() & df['PO_AMOUNT'].notna()].copy()

        if valid_df.empty:
            return pd.DataFrame(columns=['period', 'total_cost', 'avg_cost', 'work_order_count'])

        # Extract quarter
        valid_df['quarter'] = valid_df[date_col].dt.quarter
        valid_df['quarter_name'] = 'Q' + valid_df['quarter'].astype(str)

        # Group by quarter
        quarterly = valid_df.groupby(['quarter', 'quarter_name']).agg(
            total_cost=('PO_AMOUNT', 'sum'),
            avg_cost=('PO_AMOUNT', 'mean'),
            work_order_count=('PO_AMOUNT', 'count')
        ).reset_index()

        # Sort by quarter number
        quarterly = quarterly.sort_values('quarter')

        # Rename quarter_name to period and drop quarter number
        quarterly = quarterly.rename(columns={'quarter_name': 'period'})
        quarterly = quarterly[['period', 'total_cost', 'avg_cost', 'work_order_count']]

        return quarterly

    def calculate_seasonal_costs(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Aggregate work order costs by season.

        Groups work orders by meteorological season (Winter/Spring/Summer/Fall)
        based on when the repair was requested (Create_Date).

        Season mapping:
            - Winter: December, January, February
            - Spring: March, April, May
            - Summer: June, July, August
            - Fall: September, October, November

        Args:
            df: DataFrame with 'Create_Date' (or 'Complete_Date') and 'PO_AMOUNT' columns

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

        # Determine which date column to use
        date_col = self._get_date_column(df)
        if date_col is None:
            return pd.DataFrame(columns=['period', 'total_cost', 'avg_cost', 'work_order_count'])

        # Filter to valid dates and costs
        valid_df = df[df[date_col].notna() & df['PO_AMOUNT'].notna()].copy()

        if valid_df.empty:
            return pd.DataFrame(columns=['period', 'total_cost', 'avg_cost', 'work_order_count'])

        # Map month to season
        valid_df['month'] = valid_df[date_col].dt.month
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

    def calculate_variance(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate percentage variance from overall average for each period.

        Adds a 'variance_pct' column showing how much each period's total cost
        deviates from the average across all periods.

        Args:
            df: DataFrame from calculate_monthly_costs, calculate_quarterly_costs,
                or calculate_seasonal_costs (must have 'total_cost' column)

        Returns:
            DataFrame with added 'variance_pct' column showing percentage variance
            (e.g., +25.5 means 25.5% above average, -15.2 means 15.2% below average)

        Example:
            >>> quarterly = analyzer.calculate_quarterly_costs(df)
            >>> quarterly_with_variance = analyzer.calculate_variance(quarterly)
            >>> print(quarterly_with_variance)
        """
        # Handle empty dataframe
        if df.empty or 'total_cost' not in df.columns:
            return df.copy()

        # Calculate overall average cost
        avg_cost = df['total_cost'].mean()

        # Calculate percentage variance for each period
        result = df.copy()
        result['variance_pct'] = ((df['total_cost'] - avg_cost) / avg_cost) * 100

        return result

    def detect_patterns(self, df: pd.DataFrame, min_occurrences: int = 2) -> List[Dict]:
        """
        Identify recurring patterns in seasonal cost data.

        Analyzes cost variance across periods to detect recurring high or low cost
        patterns, helping to identify predictable seasonal trends.

        Args:
            df: DataFrame from calculate_*_costs with variance calculated
                (should include 'period', 'total_cost', and 'variance_pct' columns)
            min_occurrences: Minimum number of periods that must show pattern
                (default: 2, useful for multi-year data)

        Returns:
            List of pattern dictionaries with keys:
                - pattern: Description of the pattern (e.g., "High costs in Q3")
                - confidence: "high" if variance > 30%, "medium" if > 15%, "low" otherwise
                - occurrences: Number of periods showing this pattern
                - avg_variance: Average variance percentage as string (e.g., "+35%")

        Example:
            >>> quarterly = analyzer.calculate_quarterly_costs(df)
            >>> quarterly = analyzer.calculate_variance(quarterly)
            >>> patterns = analyzer.detect_patterns(quarterly)
            >>> for p in patterns:
            ...     print(f"{p['pattern']} (confidence: {p['confidence']})")
        """
        # Handle empty or invalid dataframe
        if df.empty or 'variance_pct' not in df.columns or 'period' not in df.columns:
            return []

        patterns = []

        # Detect high cost periods (variance > 15%)
        high_periods = df[df['variance_pct'] > 15.0].copy()
        for _, row in high_periods.iterrows():
            variance = row['variance_pct']
            period = row['period']

            # Determine confidence based on variance magnitude
            if variance > 30:
                confidence = "high"
            elif variance > 15:
                confidence = "medium"
            else:
                confidence = "low"

            patterns.append({
                'pattern': f"High costs in {period}",
                'confidence': confidence,
                'occurrences': 1,  # Single period analysis
                'avg_variance': f"+{variance:.1f}%"
            })

        # Detect low cost periods (variance < -15%)
        low_periods = df[df['variance_pct'] < -15.0].copy()
        for _, row in low_periods.iterrows():
            variance = row['variance_pct']
            period = row['period']

            # Determine confidence based on variance magnitude
            if abs(variance) > 30:
                confidence = "high"
            elif abs(variance) > 15:
                confidence = "medium"
            else:
                confidence = "low"

            patterns.append({
                'pattern': f"Low costs in {period}",
                'confidence': confidence,
                'occurrences': 1,  # Single period analysis
                'avg_variance': f"{variance:.1f}%"
            })

        return patterns

    def get_recommendations(self, df: pd.DataFrame) -> List[str]:
        """
        Generate actionable recommendations based on detected patterns.

        Analyzes seasonal patterns and provides specific recommendations for
        budget planning and preventive maintenance scheduling.

        Args:
            df: DataFrame from calculate_*_costs with variance calculated
                (should include 'period', 'total_cost', and 'variance_pct' columns)

        Returns:
            List of recommendation strings with actionable guidance

        Example:
            >>> quarterly = analyzer.calculate_quarterly_costs(df)
            >>> quarterly = analyzer.calculate_variance(quarterly)
            >>> recommendations = analyzer.get_recommendations(quarterly)
            >>> for rec in recommendations:
            ...     print(f"- {rec}")
        """
        # Handle empty or invalid dataframe
        if df.empty or 'variance_pct' not in df.columns or 'period' not in df.columns:
            return ["Insufficient data for recommendations"]

        recommendations = []

        # Detect patterns
        patterns = self.detect_patterns(df)

        if not patterns:
            recommendations.append("No significant seasonal patterns detected. Costs are relatively stable across periods.")
            return recommendations

        # Generate recommendations for high cost periods
        high_cost_patterns = [p for p in patterns if 'High costs' in p['pattern']]
        for pattern in high_cost_patterns:
            period = pattern['pattern'].replace('High costs in ', '')

            # Quarter-specific recommendations
            if period.startswith('Q'):
                quarter_num = period[1]
                prev_quarter = f"Q{int(quarter_num) - 1 if int(quarter_num) > 1 else 4}"
                recommendations.append(
                    f"Schedule preventive maintenance before {period} to reduce reactive work during high-cost period"
                )
                recommendations.append(
                    f"Allocate {pattern['avg_variance'].strip('+')} additional budget for {period} compared to average"
                )
            # Season-specific recommendations
            elif period in ['Winter', 'Spring', 'Summer', 'Fall']:
                recommendations.append(
                    f"Plan preventive maintenance before {period} to mitigate seasonal cost spikes"
                )
                recommendations.append(
                    f"Expect {period} costs to be {pattern['avg_variance'].strip('+')} above average"
                )
            # Month-specific recommendations
            else:
                recommendations.append(
                    f"Increase preventive maintenance in months leading up to {period}"
                )

        # Generate recommendations for low cost periods
        low_cost_patterns = [p for p in patterns if 'Low costs' in p['pattern']]
        for pattern in low_cost_patterns:
            period = pattern['pattern'].replace('Low costs in ', '')
            recommendations.append(
                f"Utilize {period}'s lower demand period for non-urgent maintenance and capital projects"
            )

        # General recommendation if high variance detected
        if any(abs(float(p['avg_variance'].strip('%+'))) > 30 for p in patterns):
            recommendations.append(
                "Consider smoothing maintenance schedules across periods to reduce cost volatility"
            )

        return recommendations
