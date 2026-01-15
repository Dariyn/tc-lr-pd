"""
Test suite for seasonal cost analysis.

Tests the SeasonalAnalyzer class to ensure correct aggregation of costs by time periods,
variance calculation, pattern detection, and recommendation generation.
"""

import pytest
import pandas as pd
import numpy as np
from pandas.testing import assert_frame_equal

from src.analysis.seasonal_analyzer import SeasonalAnalyzer


@pytest.fixture
def analyzer():
    """Fixture providing a SeasonalAnalyzer instance."""
    return SeasonalAnalyzer()


@pytest.fixture
def sample_data():
    """Fixture providing sample work order data spanning 12 months."""
    dates = pd.date_range('2024-01-01', periods=12, freq='ME')
    costs = [100, 150, 200, 180, 190, 210, 220, 230, 200, 180, 160, 140]

    return pd.DataFrame({
        'Complete_Date': dates,
        'PO_AMOUNT': costs
    })


@pytest.fixture
def seasonal_pattern_data():
    """Fixture with pronounced seasonal pattern for pattern detection tests."""
    dates = pd.date_range('2024-01-01', periods=12, freq='ME')
    # Q3 (Summer) has significantly higher costs
    costs = [100, 150, 200, 180, 190, 500, 600, 550, 200, 180, 160, 140]

    return pd.DataFrame({
        'Complete_Date': dates,
        'PO_AMOUNT': costs
    })


class TestMonthlyAggregation:
    """Tests for calculate_monthly_costs method."""

    def test_monthly_aggregation_basic(self, analyzer, sample_data):
        """Test basic monthly aggregation with 12 months of data."""
        result = analyzer.calculate_monthly_costs(sample_data)

        # Should have 12 months
        assert len(result) == 12

        # Check column names
        assert list(result.columns) == ['period', 'total_cost', 'avg_cost', 'work_order_count']

        # Check first month (January)
        january = result[result['period'] == 'January'].iloc[0]
        assert january['total_cost'] == 100
        assert january['avg_cost'] == 100.0
        assert january['work_order_count'] == 1

    def test_monthly_aggregation_multiple_orders_per_month(self, analyzer):
        """Test monthly aggregation when multiple work orders fall in same month."""
        dates = pd.to_datetime(['2024-01-15', '2024-01-20', '2024-02-10'])
        costs = [100, 200, 150]

        df = pd.DataFrame({
            'Complete_Date': dates,
            'PO_AMOUNT': costs
        })

        result = analyzer.calculate_monthly_costs(df)

        # Should have 2 months
        assert len(result) == 2

        # Check January aggregation
        january = result[result['period'] == 'January'].iloc[0]
        assert january['total_cost'] == 300  # 100 + 200
        assert january['avg_cost'] == 150.0  # (100 + 200) / 2
        assert january['work_order_count'] == 2

    def test_monthly_empty_dataframe(self, analyzer):
        """Test monthly aggregation with empty DataFrame."""
        empty_df = pd.DataFrame(columns=['Complete_Date', 'PO_AMOUNT'])
        result = analyzer.calculate_monthly_costs(empty_df)

        assert len(result) == 0
        assert list(result.columns) == ['period', 'total_cost', 'avg_cost', 'work_order_count']

    def test_monthly_missing_dates(self, analyzer):
        """Test monthly aggregation with missing/null dates."""
        df = pd.DataFrame({
            'Complete_Date': [pd.Timestamp('2024-01-15'), pd.NaT, pd.Timestamp('2024-02-10')],
            'PO_AMOUNT': [100, 200, 150]
        })

        result = analyzer.calculate_monthly_costs(df)

        # Should only include rows with valid dates
        assert len(result) == 2


class TestQuarterlyAggregation:
    """Tests for calculate_quarterly_costs method."""

    def test_quarterly_aggregation_basic(self, analyzer, sample_data):
        """Test basic quarterly aggregation."""
        result = analyzer.calculate_quarterly_costs(sample_data)

        # Should have 4 quarters
        assert len(result) == 4

        # Check column names
        assert list(result.columns) == ['period', 'total_cost', 'avg_cost', 'work_order_count']

        # Check Q1 (Jan, Feb, Mar)
        q1 = result[result['period'] == 'Q1'].iloc[0]
        assert q1['total_cost'] == 450  # 100 + 150 + 200
        assert q1['avg_cost'] == 150.0  # (100 + 150 + 200) / 3
        assert q1['work_order_count'] == 3

    def test_quarterly_labels(self, analyzer, sample_data):
        """Test that quarters are correctly labeled Q1-Q4."""
        result = analyzer.calculate_quarterly_costs(sample_data)

        periods = result['period'].tolist()
        assert periods == ['Q1', 'Q2', 'Q3', 'Q4']

    def test_quarterly_empty_dataframe(self, analyzer):
        """Test quarterly aggregation with empty DataFrame."""
        empty_df = pd.DataFrame(columns=['Complete_Date', 'PO_AMOUNT'])
        result = analyzer.calculate_quarterly_costs(empty_df)

        assert len(result) == 0
        assert list(result.columns) == ['period', 'total_cost', 'avg_cost', 'work_order_count']


class TestSeasonalAggregation:
    """Tests for calculate_seasonal_costs method."""

    def test_seasonal_aggregation_basic(self, analyzer, sample_data):
        """Test basic seasonal aggregation."""
        result = analyzer.calculate_seasonal_costs(sample_data)

        # Should have 4 seasons
        assert len(result) == 4

        # Check column names
        assert list(result.columns) == ['period', 'total_cost', 'avg_cost', 'work_order_count']

        # Check Winter (Dec, Jan, Feb)
        winter = result[result['period'] == 'Winter'].iloc[0]
        # Winter includes Jan, Feb, Dec (from sample data: 100, 150, 140)
        assert winter['total_cost'] == 390
        assert winter['work_order_count'] == 3

    def test_seasonal_mapping(self, analyzer):
        """Test that months are correctly mapped to seasons."""
        # Create data covering all 12 months
        dates = pd.date_range('2024-01-01', periods=12, freq='ME')
        costs = [100] * 12

        df = pd.DataFrame({
            'Complete_Date': dates,
            'PO_AMOUNT': costs
        })

        result = analyzer.calculate_seasonal_costs(df)

        # Check that all seasons have the correct number of months
        for season in result['period']:
            season_row = result[result['period'] == season].iloc[0]
            assert season_row['work_order_count'] == 3  # Each season has 3 months

    def test_seasonal_order(self, analyzer, sample_data):
        """Test that seasons are ordered Winter, Spring, Summer, Fall."""
        result = analyzer.calculate_seasonal_costs(sample_data)

        periods = result['period'].tolist()
        assert periods == ['Winter', 'Spring', 'Summer', 'Fall']

    def test_seasonal_empty_dataframe(self, analyzer):
        """Test seasonal aggregation with empty DataFrame."""
        empty_df = pd.DataFrame(columns=['Complete_Date', 'PO_AMOUNT'])
        result = analyzer.calculate_seasonal_costs(empty_df)

        assert len(result) == 0
        assert list(result.columns) == ['period', 'total_cost', 'avg_cost', 'work_order_count']


class TestPeakDetection:
    """Tests for identify_peaks method."""

    def test_peak_detection_default_threshold(self, analyzer):
        """Test peak detection with default threshold (1.2)."""
        costs = pd.Series([100, 100, 100, 200])  # Last value is 2x average

        peaks = analyzer.identify_peaks(costs)

        # Only the last value should be flagged (200 > 125 * 1.2 = 150)
        assert peaks.tolist() == [False, False, False, True]

    def test_peak_detection_custom_threshold(self, analyzer):
        """Test peak detection with custom threshold."""
        costs = pd.Series([100, 100, 100, 150])  # Last value is 1.2x average

        peaks = analyzer.identify_peaks(costs, threshold=1.5)

        # None should be flagged (150 < 112.5 * 1.5 = 168.75)
        assert peaks.tolist() == [False, False, False, False]

    def test_peak_detection_empty_series(self, analyzer):
        """Test peak detection with empty series."""
        empty_series = pd.Series([], dtype=float)

        peaks = analyzer.identify_peaks(empty_series)

        assert len(peaks) == 0

    def test_peak_detection_all_same(self, analyzer):
        """Test peak detection when all costs are the same."""
        costs = pd.Series([100, 100, 100, 100])

        peaks = analyzer.identify_peaks(costs)

        # None should be flagged since all values equal the average
        assert peaks.tolist() == [False, False, False, False]


class TestVarianceCalculation:
    """Tests for calculate_variance method."""

    def test_variance_calculation_basic(self, analyzer):
        """Test basic variance calculation."""
        df = pd.DataFrame({
            'period': ['Q1', 'Q2', 'Q3', 'Q4'],
            'total_cost': [100, 100, 150, 50],
            'avg_cost': [100, 100, 150, 50],
            'work_order_count': [1, 1, 1, 1]
        })

        result = analyzer.calculate_variance(df)

        # Average cost is 100
        # Q1: 0%, Q2: 0%, Q3: +50%, Q4: -50%
        assert 'variance_pct' in result.columns
        assert result.loc[0, 'variance_pct'] == pytest.approx(0.0)
        assert result.loc[2, 'variance_pct'] == pytest.approx(50.0)
        assert result.loc[3, 'variance_pct'] == pytest.approx(-50.0)

    def test_variance_calculation_empty_dataframe(self, analyzer):
        """Test variance calculation with empty DataFrame."""
        empty_df = pd.DataFrame(columns=['period', 'total_cost', 'avg_cost', 'work_order_count'])

        result = analyzer.calculate_variance(empty_df)

        assert len(result) == 0

    def test_variance_calculation_missing_column(self, analyzer):
        """Test variance calculation with missing total_cost column."""
        df = pd.DataFrame({
            'period': ['Q1', 'Q2'],
            'avg_cost': [100, 150]
        })

        result = analyzer.calculate_variance(df)

        # Should return original dataframe unchanged
        assert 'variance_pct' not in result.columns


class TestPatternDetection:
    """Tests for detect_patterns method."""

    def test_pattern_detection_high_costs(self, analyzer, seasonal_pattern_data):
        """Test pattern detection for high cost periods."""
        quarterly = analyzer.calculate_quarterly_costs(seasonal_pattern_data)
        quarterly = analyzer.calculate_variance(quarterly)

        patterns = analyzer.detect_patterns(quarterly)

        # Should detect Q3 as high cost period
        high_patterns = [p for p in patterns if 'High costs' in p['pattern']]
        assert len(high_patterns) >= 1

        # Check Q3 pattern
        q3_pattern = [p for p in high_patterns if 'Q3' in p['pattern']][0]
        assert q3_pattern['confidence'] == 'high'  # Variance > 30%
        assert '+' in q3_pattern['avg_variance']

    def test_pattern_detection_low_costs(self, analyzer, seasonal_pattern_data):
        """Test pattern detection for low cost periods."""
        quarterly = analyzer.calculate_quarterly_costs(seasonal_pattern_data)
        quarterly = analyzer.calculate_variance(quarterly)

        patterns = analyzer.detect_patterns(quarterly)

        # Should detect low cost periods
        low_patterns = [p for p in patterns if 'Low costs' in p['pattern']]
        assert len(low_patterns) >= 1

    def test_pattern_detection_empty_dataframe(self, analyzer):
        """Test pattern detection with empty DataFrame."""
        empty_df = pd.DataFrame(columns=['period', 'total_cost', 'variance_pct'])

        patterns = analyzer.detect_patterns(empty_df)

        assert patterns == []

    def test_pattern_detection_no_patterns(self, analyzer):
        """Test pattern detection when costs are stable."""
        df = pd.DataFrame({
            'period': ['Q1', 'Q2', 'Q3', 'Q4'],
            'total_cost': [100, 105, 95, 100],
            'variance_pct': [0, 5, -5, 0]
        })

        patterns = analyzer.detect_patterns(df)

        # No patterns should be detected (variance < 15%)
        assert len(patterns) == 0


class TestRecommendations:
    """Tests for get_recommendations method."""

    def test_recommendations_with_patterns(self, analyzer, seasonal_pattern_data):
        """Test recommendation generation with detected patterns."""
        quarterly = analyzer.calculate_quarterly_costs(seasonal_pattern_data)
        quarterly = analyzer.calculate_variance(quarterly)

        recommendations = analyzer.get_recommendations(quarterly)

        # Should have multiple recommendations
        assert len(recommendations) > 0

        # Should mention Q3 (high cost period)
        q3_recs = [r for r in recommendations if 'Q3' in r]
        assert len(q3_recs) > 0

    def test_recommendations_no_patterns(self, analyzer):
        """Test recommendation generation when no patterns detected."""
        df = pd.DataFrame({
            'period': ['Q1', 'Q2', 'Q3', 'Q4'],
            'total_cost': [100, 105, 95, 100],
            'variance_pct': [0, 5, -5, 0]
        })

        recommendations = analyzer.get_recommendations(df)

        # Should return stable costs message
        assert len(recommendations) == 1
        assert 'stable' in recommendations[0].lower()

    def test_recommendations_empty_dataframe(self, analyzer):
        """Test recommendation generation with empty DataFrame."""
        empty_df = pd.DataFrame(columns=['period', 'total_cost', 'variance_pct'])

        recommendations = analyzer.get_recommendations(empty_df)

        assert recommendations == ["Insufficient data for recommendations"]

    def test_recommendations_high_variance(self, analyzer):
        """Test that high variance triggers volatility recommendation."""
        df = pd.DataFrame({
            'period': ['Q1', 'Q2', 'Q3', 'Q4'],
            'total_cost': [100, 100, 200, 50],
            'variance_pct': [0, 0, 60, -40]
        })

        recommendations = analyzer.get_recommendations(df)

        # Should include volatility smoothing recommendation
        volatility_recs = [r for r in recommendations if 'smoothing' in r.lower()]
        assert len(volatility_recs) > 0


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_single_record(self, analyzer):
        """Test with single work order."""
        df = pd.DataFrame({
            'Complete_Date': [pd.Timestamp('2024-01-15')],
            'PO_AMOUNT': [100]
        })

        # Should not crash
        monthly = analyzer.calculate_monthly_costs(df)
        assert len(monthly) == 1

        quarterly = analyzer.calculate_quarterly_costs(df)
        assert len(quarterly) == 1

        seasonal = analyzer.calculate_seasonal_costs(df)
        assert len(seasonal) == 1

    def test_missing_amounts(self, analyzer):
        """Test with missing PO_AMOUNT values."""
        df = pd.DataFrame({
            'Complete_Date': pd.date_range('2024-01-01', periods=3, freq='ME'),
            'PO_AMOUNT': [100, np.nan, 200]
        })

        result = analyzer.calculate_monthly_costs(df)

        # Should only include rows with valid amounts
        assert len(result) == 2

    def test_all_costs_same(self, analyzer):
        """Test when all costs are identical."""
        df = pd.DataFrame({
            'Complete_Date': pd.date_range('2024-01-01', periods=12, freq='ME'),
            'PO_AMOUNT': [100] * 12
        })

        quarterly = analyzer.calculate_quarterly_costs(df)
        quarterly = analyzer.calculate_variance(quarterly)
        patterns = analyzer.detect_patterns(quarterly)

        # Should have no patterns (all variance is 0%)
        assert len(patterns) == 0
