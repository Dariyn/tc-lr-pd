"""Tests for equipment ranking and prioritization module."""

import pandas as pd
import numpy as np
import pytest

from src.analysis.equipment_ranker import (
    calculate_cost_impact,
    calculate_priority_score,
    rank_equipment,
    identify_thresholds
)


class TestCalculateCostImpact:
    """Tests for calculate_cost_impact function."""

    def test_calculate_cost_impact(self):
        """Test cost impact calculation with basic data."""
        # Sample data: equipment with total_work_orders=10, avg_cost=1000
        df = pd.DataFrame({
            'Equipment_ID': ['EQ001', 'EQ002'],
            'equipment_primary_category': ['HVAC', 'HVAC'],
            'total_work_orders': [10, 5],
            'avg_cost': [1000, 2000],
            'work_orders_per_month': [5.0, 2.5]
        })

        result = calculate_cost_impact(df)

        # Verify cost_impact = total_work_orders * avg_cost
        assert result.loc[0, 'cost_impact'] == 10000
        assert result.loc[1, 'cost_impact'] == 10000

    def test_calculate_cost_impact_missing_avg_cost(self):
        """Test cost impact calculation with missing avg_cost."""
        df = pd.DataFrame({
            'Equipment_ID': ['EQ001', 'EQ002'],
            'equipment_primary_category': ['HVAC', 'HVAC'],
            'total_work_orders': [10, 5],
            'avg_cost': [1000, np.nan],  # EQ002 has missing cost
            'work_orders_per_month': [5.0, 2.5]
        })

        result = calculate_cost_impact(df)

        # Missing avg_cost should result in 0 cost_impact
        assert result.loc[0, 'cost_impact'] == 10000
        assert result.loc[1, 'cost_impact'] == 0


class TestCalculatePriorityScore:
    """Tests for calculate_priority_score function."""

    def test_calculate_priority_score_weighting(self):
        """Test priority score weighting formula."""
        # Create data with known normalized scores
        df = pd.DataFrame({
            'Equipment_ID': ['EQ001', 'EQ002'],
            'equipment_primary_category': ['HVAC', 'HVAC'],
            'work_orders_per_month': [10.0, 5.0],  # Will normalize to 1.0 and 0.0
            'cost_impact': [1000.0, 0.0],  # Will normalize to 1.0 and 0.0
            'is_outlier_consensus': [True, False],  # 1.0 and 0.0
            'is_zscore_outlier': [True, False],
            'is_iqr_outlier': [True, False],
            'is_percentile_outlier': [True, False]
        })

        result = calculate_priority_score(df)

        # EQ001: freq=1.0, cost=1.0, outlier=1.0
        # Priority = 1.0*0.4 + 1.0*0.4 + 1.0*0.2 = 1.0
        assert abs(result.loc[0, 'priority_score'] - 1.0) < 0.001

        # EQ002: freq=0.0, cost=0.0, outlier=0.0
        # Priority = 0.0*0.4 + 0.0*0.4 + 0.0*0.2 = 0.0
        assert abs(result.loc[1, 'priority_score'] - 0.0) < 0.001

    def test_calculate_priority_score_range(self):
        """Test priority score is in [0, 1] range."""
        df = pd.DataFrame({
            'Equipment_ID': ['EQ001', 'EQ002', 'EQ003'],
            'equipment_primary_category': ['HVAC', 'HVAC', 'HVAC'],
            'work_orders_per_month': [10.0, 5.0, 7.5],
            'cost_impact': [1000.0, 500.0, 750.0],
            'is_outlier_consensus': [True, False, True],
            'is_zscore_outlier': [True, False, True],
            'is_iqr_outlier': [True, True, True],
            'is_percentile_outlier': [True, False, True]
        })

        result = calculate_priority_score(df)

        # All priority scores should be in [0, 1]
        assert (result['priority_score'] >= 0).all()
        assert (result['priority_score'] <= 1).all()

    def test_outlier_score_levels(self):
        """Test outlier score calculation for different flag combinations."""
        df = pd.DataFrame({
            'Equipment_ID': ['EQ001', 'EQ002', 'EQ003'],
            'equipment_primary_category': ['HVAC', 'HVAC', 'HVAC'],
            'work_orders_per_month': [10.0, 5.0, 7.5],
            'cost_impact': [1000.0, 500.0, 750.0],
            'is_outlier_consensus': [True, False, False],  # 1.0, 0.5, 0.0
            'is_zscore_outlier': [True, True, False],  # Consensus, any flag, no flag
            'is_iqr_outlier': [True, False, False],
            'is_percentile_outlier': [True, False, False]
        })

        result = calculate_priority_score(df)

        # EQ001: consensus outlier = 1.0
        assert result.loc[0, 'outlier_score'] == 1.0

        # EQ002: any outlier flag but not consensus = 0.5
        assert result.loc[1, 'outlier_score'] == 0.5

        # EQ003: no outlier flags = 0.0
        assert result.loc[2, 'outlier_score'] == 0.0


class TestRankEquipment:
    """Tests for rank_equipment function."""

    def test_rank_equipment_sorting(self):
        """Test equipment sorted by priority score descending."""
        df = pd.DataFrame({
            'Equipment_ID': ['EQ001', 'EQ002', 'EQ003'],
            'equipment_primary_category': ['HVAC', 'HVAC', 'Plumbing'],
            'total_work_orders': [20, 10, 15],
            'work_orders_per_month': [10.0, 5.0, 8.0],
            'avg_cost': [500, 1000, 750],
            'is_outlier_consensus': [True, True, True],
            'is_zscore_outlier': [True, True, True],
            'is_iqr_outlier': [True, True, True],
            'is_percentile_outlier': [True, True, True]
        })

        result = rank_equipment(df)

        # Result should be sorted by priority_score descending
        priority_scores = result['priority_score'].tolist()
        assert priority_scores == sorted(priority_scores, reverse=True)

    def test_rank_equipment_category_rank(self):
        """Test category_rank assigned correctly within categories."""
        df = pd.DataFrame({
            'Equipment_ID': ['EQ001', 'EQ002', 'EQ003', 'EQ004'],
            'equipment_primary_category': ['HVAC', 'HVAC', 'Plumbing', 'Plumbing'],
            'total_work_orders': [20, 10, 30, 15],
            'work_orders_per_month': [20.0, 10.0, 30.0, 15.0],
            'avg_cost': [500, 1000, 750, 500],
            'is_outlier_consensus': [True, True, True, True],
            'is_zscore_outlier': [True, True, True, True],
            'is_iqr_outlier': [True, True, True, True],
            'is_percentile_outlier': [True, True, True, True]
        })

        result = rank_equipment(df)

        # Within each category, ranks should be consecutive starting from 1
        hvac_ranks = result[result['equipment_primary_category'] == 'HVAC']['category_rank'].tolist()
        plumbing_ranks = result[result['equipment_primary_category'] == 'Plumbing']['category_rank'].tolist()

        assert sorted(hvac_ranks) == list(range(1, len(hvac_ranks) + 1))
        assert sorted(plumbing_ranks) == list(range(1, len(plumbing_ranks) + 1))

    def test_rank_equipment_overall_rank(self):
        """Test overall_rank assigned correctly across all categories."""
        df = pd.DataFrame({
            'Equipment_ID': ['EQ001', 'EQ002', 'EQ003'],
            'equipment_primary_category': ['HVAC', 'HVAC', 'Plumbing'],
            'total_work_orders': [20, 10, 15],
            'work_orders_per_month': [20.0, 10.0, 15.0],
            'avg_cost': [500, 1000, 750],
            'is_outlier_consensus': [True, True, True],
            'is_zscore_outlier': [True, True, True],
            'is_iqr_outlier': [True, True, True],
            'is_percentile_outlier': [True, True, True]
        })

        result = rank_equipment(df)

        # Overall ranks should be consecutive 1, 2, 3, ...
        overall_ranks = result['overall_rank'].tolist()
        assert overall_ranks == list(range(1, len(result) + 1))

    def test_rank_equipment_filters_consensus_outliers(self):
        """Test that only consensus outliers are included in results."""
        df = pd.DataFrame({
            'Equipment_ID': ['EQ001', 'EQ002', 'EQ003', 'EQ004'],
            'equipment_primary_category': ['HVAC', 'HVAC', 'HVAC', 'HVAC'],
            'total_work_orders': [20, 10, 15, 12],
            'work_orders_per_month': [20.0, 10.0, 15.0, 12.0],
            'avg_cost': [500, 1000, 750, 600],
            'is_outlier_consensus': [True, True, False, False],  # Only first 2 are consensus
            'is_zscore_outlier': [True, True, True, False],
            'is_iqr_outlier': [True, True, False, False],
            'is_percentile_outlier': [True, True, True, True]
        })

        result = rank_equipment(df)

        # Only consensus outliers (EQ001, EQ002) should be in results
        assert len(result) == 2
        assert set(result['Equipment_ID'].tolist()) == {'EQ001', 'EQ002'}


class TestIdentifyThresholds:
    """Tests for identify_thresholds function."""

    def test_identify_thresholds_basic(self):
        """Test threshold calculation from ranked equipment."""
        df = pd.DataFrame({
            'Equipment_ID': ['EQ001', 'EQ002', 'EQ003'],
            'equipment_primary_category': ['HVAC', 'HVAC', 'HVAC'],
            'work_orders_per_month': [10.0, 20.0, 15.0],  # Median = 15.0
            'cost_impact': [1000.0, 3000.0, 2000.0],  # Median = 2000.0
            'priority_score': [0.8, 0.9, 0.85]
        })

        result = identify_thresholds(df)

        # Verify threshold structure
        assert 'frequency_threshold' in result
        assert 'cost_threshold' in result
        assert 'percentile_threshold' in result
        assert 'rationale' in result

        # Verify median values
        assert result['frequency_threshold'] == 15.0
        assert result['cost_threshold'] == 2000.0
        assert result['percentile_threshold'] == 90.0

    def test_identify_thresholds_empty_dataframe(self):
        """Test threshold calculation with empty DataFrame."""
        df = pd.DataFrame()

        result = identify_thresholds(df)

        # Should return default thresholds with appropriate message
        assert result['frequency_threshold'] == 0.0
        assert result['cost_threshold'] == 0.0
        assert result['percentile_threshold'] == 90.0
        assert 'insufficient data' in result['rationale'].lower()


class TestIntegration:
    """Integration tests for ranking pipeline."""

    def test_full_ranking_pipeline(self):
        """Test complete ranking pipeline from frequencies to ranked output."""
        # Simulate frequency analyzer output with outlier flags
        freq_df = pd.DataFrame({
            'Equipment_ID': ['EQ001', 'EQ002', 'EQ003', 'EQ004'],
            'equipment_primary_category': ['HVAC', 'HVAC', 'Plumbing', 'Plumbing'],
            'total_work_orders': [100, 50, 80, 40],
            'work_orders_per_month': [10.0, 5.0, 8.0, 4.0],
            'avg_cost': [1000, 800, 1200, 600],
            'is_outlier_consensus': [True, True, True, False],
            'is_zscore_outlier': [True, True, True, False],
            'is_iqr_outlier': [True, True, True, False],
            'is_percentile_outlier': [True, True, True, True]
        })

        # Run ranking
        ranked_df = rank_equipment(freq_df)

        # Verify output structure
        assert 'cost_impact' in ranked_df.columns
        assert 'priority_score' in ranked_df.columns
        assert 'category_rank' in ranked_df.columns
        assert 'overall_rank' in ranked_df.columns

        # Verify only consensus outliers
        assert len(ranked_df) == 3
        assert all(ranked_df['is_outlier_consensus'])

        # Verify cost impact calculated
        assert ranked_df.iloc[0]['cost_impact'] > 0

        # Get thresholds
        thresholds = identify_thresholds(ranked_df)
        assert thresholds['frequency_threshold'] > 0
        assert thresholds['cost_threshold'] > 0
