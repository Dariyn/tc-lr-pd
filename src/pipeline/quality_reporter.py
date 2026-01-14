"""
Data quality reporter for work order data.

Provides comprehensive quality assessment metrics including completeness,
consistency, outlier detection, and coverage statistics.
"""

import logging
import pandas as pd
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


def calculate_completeness_metrics(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Calculate completeness metrics for critical fields.

    Args:
        df: DataFrame with work order data

    Returns:
        Dict with field_name → {completeness_pct, null_count, is_complete}
    """
    critical_fields = [
        'Equipment_ID',
        'EquipmentName',
        'equipment_category',
        'Create_Date',
        'Complete_Date',
        'PO_AMOUNT'
    ]

    metrics = {}
    quality_concerns = []

    total_rows = len(df)

    for field in critical_fields:
        if field not in df.columns:
            metrics[field] = {
                'completeness_pct': 0.0,
                'null_count': total_rows,
                'is_complete': False
            }
            quality_concerns.append(f"{field} field missing from data")
            continue

        non_null_count = df[field].notna().sum()
        null_count = df[field].isna().sum()
        completeness_pct = (non_null_count / total_rows) * 100 if total_rows > 0 else 0.0
        is_complete = completeness_pct >= 95.0

        metrics[field] = {
            'completeness_pct': completeness_pct,
            'null_count': null_count,
            'is_complete': is_complete
        }

        if not is_complete:
            quality_concerns.append(
                f"{field} only {completeness_pct:.1f}% complete ({null_count} nulls)"
            )

    metrics['_quality_concerns'] = quality_concerns

    return metrics


def calculate_consistency_metrics(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Calculate consistency metrics for data integrity.

    Args:
        df: DataFrame with work order data

    Returns:
        Dict with metric_name → value
    """
    metrics = {}

    # Equipment category consistency
    if 'equipment_category_consistency' in df.columns:
        avg_consistency = df['equipment_category_consistency'].mean()
        metrics['category_consistency_avg'] = avg_consistency
    else:
        metrics['category_consistency_avg'] = None

    # Date consistency: Complete_Date >= Create_Date
    if 'Complete_Date' in df.columns and 'Create_Date' in df.columns:
        both_dates = df[df['Complete_Date'].notna() & df['Create_Date'].notna()].copy()
        if len(both_dates) > 0:
            valid_dates = (both_dates['Complete_Date'] >= both_dates['Create_Date']).sum()
            metrics['date_consistency_pct'] = (valid_dates / len(both_dates)) * 100
        else:
            metrics['date_consistency_pct'] = None
    else:
        metrics['date_consistency_pct'] = None

    # Cost consistency: PO_AMOUNT >= 0
    if 'PO_AMOUNT' in df.columns:
        non_null_costs = df[df['PO_AMOUNT'].notna()]
        if len(non_null_costs) > 0:
            valid_costs = (non_null_costs['PO_AMOUNT'] >= 0).sum()
            metrics['cost_consistency_pct'] = (valid_costs / len(non_null_costs)) * 100
        else:
            metrics['cost_consistency_pct'] = None
    else:
        metrics['cost_consistency_pct'] = None

    return metrics


def calculate_outlier_metrics(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Calculate outlier metrics for cost and duration anomalies.

    Args:
        df: DataFrame with work order data

    Returns:
        Dict with outlier counts, percentages, and thresholds
    """
    metrics = {}

    # Cost outliers
    if 'cost_outlier' in df.columns:
        cost_outliers = df['cost_outlier'].sum()
        metrics['cost_outlier_count'] = int(cost_outliers)
        metrics['cost_outlier_pct'] = (cost_outliers / len(df)) * 100 if len(df) > 0 else 0.0

        # Calculate 99th percentile threshold
        if 'PO_AMOUNT' in df.columns:
            non_null_costs = df[df['PO_AMOUNT'].notna()]['PO_AMOUNT']
            if len(non_null_costs) > 0:
                metrics['cost_outlier_threshold'] = non_null_costs.quantile(0.99)
            else:
                metrics['cost_outlier_threshold'] = None
        else:
            metrics['cost_outlier_threshold'] = None
    else:
        metrics['cost_outlier_count'] = 0
        metrics['cost_outlier_pct'] = 0.0
        metrics['cost_outlier_threshold'] = None

    # Duration outliers
    if 'duration_outlier' in df.columns:
        duration_outliers = df['duration_outlier'].sum()
        metrics['duration_outlier_count'] = int(duration_outliers)
        metrics['duration_outlier_pct'] = (duration_outliers / len(df)) * 100 if len(df) > 0 else 0.0

        # Calculate 99th percentile threshold
        if 'duration_hours' in df.columns:
            non_null_durations = df[df['duration_hours'].notna()]['duration_hours']
            if len(non_null_durations) > 0:
                metrics['duration_outlier_threshold'] = non_null_durations.quantile(0.99)
            else:
                metrics['duration_outlier_threshold'] = None
        else:
            metrics['duration_outlier_threshold'] = None
    else:
        metrics['duration_outlier_count'] = 0
        metrics['duration_outlier_pct'] = 0.0
        metrics['duration_outlier_threshold'] = None

    return metrics


def calculate_coverage_metrics(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Calculate coverage metrics for data scope.

    Args:
        df: DataFrame with work order data

    Returns:
        Dict with coverage statistics
    """
    metrics = {}

    # Date range coverage
    if 'Create_Date' in df.columns:
        valid_dates = df[df['Create_Date'].notna()]['Create_Date']
        if len(valid_dates) > 0:
            metrics['date_range_start'] = valid_dates.min()
            metrics['date_range_end'] = valid_dates.max()
            metrics['date_range_days'] = (valid_dates.max() - valid_dates.min()).days
        else:
            metrics['date_range_start'] = None
            metrics['date_range_end'] = None
            metrics['date_range_days'] = None
    else:
        metrics['date_range_start'] = None
        metrics['date_range_end'] = None
        metrics['date_range_days'] = None

    # Equipment coverage
    if 'Equipment_ID' in df.columns:
        metrics['unique_equipment_count'] = df['Equipment_ID'].nunique()
    else:
        metrics['unique_equipment_count'] = 0

    # Category coverage
    if 'equipment_category' in df.columns:
        metrics['unique_category_count'] = df['equipment_category'].nunique()
    else:
        metrics['unique_category_count'] = 0

    # Property coverage
    if 'Property' in df.columns:
        metrics['unique_property_count'] = df['Property'].nunique()
    else:
        metrics['unique_property_count'] = 0

    return metrics


def generate_quality_report(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Generate comprehensive quality report for work order data.

    Orchestrates all metric calculations and compiles into single report
    with overall quality score and recommendations.

    Args:
        df: DataFrame with work order data

    Returns:
        Dict with quality report sections and overall score
    """
    logger.info(f"Generating quality report for {len(df)} work orders")

    # Calculate all metric sections
    completeness = calculate_completeness_metrics(df)
    consistency = calculate_consistency_metrics(df)
    outliers = calculate_outlier_metrics(df)
    coverage = calculate_coverage_metrics(df)

    # Extract quality concerns from completeness
    quality_concerns = completeness.pop('_quality_concerns', [])

    # Calculate overall quality score
    # Weighted average: completeness (40%), consistency (40%), outlier rate (20%)

    # Completeness score: average of all field completeness percentages
    completeness_scores = [
        metrics['completeness_pct']
        for field, metrics in completeness.items()
        if isinstance(metrics, dict) and 'completeness_pct' in metrics
    ]
    completeness_score = sum(completeness_scores) / len(completeness_scores) if completeness_scores else 0.0

    # Consistency score: average of available consistency metrics (as percentages)
    consistency_scores = []
    if consistency.get('category_consistency_avg') is not None:
        # category_consistency_avg is already a percentage from categorizer (0-100 range)
        consistency_scores.append(consistency['category_consistency_avg'])
    if consistency.get('date_consistency_pct') is not None:
        consistency_scores.append(consistency['date_consistency_pct'])
    if consistency.get('cost_consistency_pct') is not None:
        consistency_scores.append(consistency['cost_consistency_pct'])

    consistency_score = sum(consistency_scores) / len(consistency_scores) if consistency_scores else 100.0

    # Outlier score: inverse of outlier rate (100 - outlier_pct), averaged
    cost_outlier_score = 100.0 - outliers.get('cost_outlier_pct', 0.0)
    duration_outlier_score = 100.0 - outliers.get('duration_outlier_pct', 0.0)
    outlier_score = (cost_outlier_score + duration_outlier_score) / 2

    # Weighted overall score
    overall_score = (
        completeness_score * 0.40 +
        consistency_score * 0.40 +
        outlier_score * 0.20
    )

    quality_passed = overall_score >= 85.0

    # Generate recommendations
    recommendations = []

    if completeness_score < 95.0:
        recommendations.append(f"Address data completeness issues: {', '.join(quality_concerns)}")

    if consistency.get('date_consistency_pct') and consistency['date_consistency_pct'] < 100.0:
        invalid_pct = 100.0 - consistency['date_consistency_pct']
        recommendations.append(
            f"Review {invalid_pct:.1f}% of records with Complete_Date before Create_Date"
        )

    if consistency.get('cost_consistency_pct') and consistency['cost_consistency_pct'] < 100.0:
        invalid_pct = 100.0 - consistency['cost_consistency_pct']
        recommendations.append(
            f"Review {invalid_pct:.1f}% of records with negative costs"
        )

    if outliers.get('cost_outlier_pct', 0.0) > 2.0:
        recommendations.append(
            f"Review {outliers['cost_outlier_count']} cost outliers "
            f"(>{outliers.get('cost_outlier_threshold', 'N/A'):.2f})"
        )

    if outliers.get('duration_outlier_pct', 0.0) > 2.0:
        recommendations.append(
            f"Review {outliers['duration_outlier_count']} duration outliers "
            f"(>{outliers.get('duration_outlier_threshold', 'N/A'):.1f} hours)"
        )

    if not recommendations:
        recommendations.append("Data quality is good - no major issues detected")

    # Compile final report
    report = {
        'overall_quality_score': overall_score,
        'quality_passed': quality_passed,
        'completeness': completeness,
        'completeness_score': completeness_score,
        'consistency': consistency,
        'consistency_score': consistency_score,
        'outliers': outliers,
        'outlier_score': outlier_score,
        'coverage': coverage,
        'recommendations': recommendations,
        'total_records': len(df)
    }

    logger.info(f"Quality report generated: score={overall_score:.2f}, passed={quality_passed}")

    return report
