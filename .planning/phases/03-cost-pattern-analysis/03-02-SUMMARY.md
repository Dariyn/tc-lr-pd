# Plan 03-02 Summary: Vendor Cost Performance Analysis

**Phase:** 03-cost-pattern-analysis
**Plan:** 02
**Status:** Complete
**Date:** 2026-01-15

## Objective

Analyze vendor/contractor cost performance to identify high-cost vendors and efficiency patterns for informed vendor selection and contract negotiations.

## What Was Built

### VendorAnalyzer Class
Complete vendor analysis module (`src/analysis/vendor_analyzer.py`) with comprehensive methods:

1. **Cost Aggregation**
   - `calculate_vendor_costs()`: Aggregate total cost, work order count, and average cost per vendor
   - Configurable minimum work order threshold (default: 3) to filter one-off outliers
   - Handles missing Contractor values with configurable label

2. **Performance Metrics**
   - `calculate_vendor_duration()`: Average completion time by vendor
   - `rank_vendors()`: Rank by total cost, average cost, or work order count
   - `identify_high_cost_vendors()`: Flag vendors above cost thresholds (75th/90th percentile or top-N)

3. **Efficiency & Quality Analysis**
   - `calculate_cost_efficiency()`: Cost per day metric (avg_cost / avg_duration) - lower is better
   - `calculate_quality_indicators()`: Track repeat work on same equipment by vendor
   - Repeat rate > 50% flags potential quality/rework issues

4. **Actionable Recommendations**
   - `get_vendor_recommendations()`: Generate structured recommendations
   - Categories: High cost, Slow completion, Low efficiency, Quality concerns
   - Each recommendation includes vendor, issue, metric, and actionable suggestion

### Test Coverage
Comprehensive test suite (`tests/test_vendor_analyzer.py`) with 19 tests:
- Cost aggregation with varying work order counts
- Duration calculation with missing date handling
- Ranking by multiple criteria with ties
- High-cost identification using different thresholds
- Cost efficiency calculation and zero duration edge cases
- Quality indicators for repeat equipment work
- Recommendation generation for various issues
- Custom configuration testing (min work orders, unknown label)

All tests pass successfully.

## Key Decisions

1. **Minimum Work Order Threshold (3)**: Filter vendors with fewer than 3 work orders to exclude one-off contractors and focus analysis on regular vendors

2. **Cost Efficiency Metric**: Use cost per day (avg_cost / avg_duration) as efficiency indicator - identifies vendors who complete work quickly at reasonable cost

3. **Quality Indicator**: Repeat rate (% of equipment with 2+ work orders) as proxy for rework - simpler than complex problem/remedy text analysis

4. **Recommendation Thresholds**:
   - High cost/slow/inefficient: 75th percentile (top 25%)
   - Quality concerns: > 50% repeat rate
   - Balances actionability with focused vendor list

5. **Unknown Contractor Handling**: Group missing Contractor values as "Unknown" with configurable label, exclude by default but allow inclusion via parameter

## Files Modified

- `src/analysis/vendor_analyzer.py` (created, 505 lines)
- `tests/test_vendor_analyzer.py` (created, 403 lines)

## Verification Results

- All 19 tests pass
- VendorAnalyzer processes sample work order data correctly
- Vendor ranking produces correct order for different criteria
- Cost efficiency calculation handles edge cases (zero duration, missing data)
- Recommendations are actionable and category-specific
- No import errors or type issues

## Integration Points

**Input Requirements:**
- Contractor: Vendor/contractor name (optional, handled as "Unknown")
- PO_AMOUNT: Cost amount (from data_loader)
- Create_Date, Complete_Date: Date fields (from data_loader)
- Equipment_ID: For quality analysis (repeat work detection)

**Output Format:**
- All methods return pandas DataFrames with structured columns
- Recommendations return list of dictionaries for easy consumption
- Consistent sorting (highest/worst first) for review prioritization

## Performance Notes

- Efficient groupby operations on contractor dimension
- Filters applied early (min work order threshold) to reduce processing
- Separate methods allow selective analysis (don't need all metrics every time)
- Duration calculation only uses rows with valid date pairs

## Next Steps

This vendor analysis module is ready for:
1. Integration into main analysis pipeline
2. Use in vendor performance reports
3. Contract review and negotiation support
4. Vendor selection for specific work types

Recommended next phase: Integrate with seasonal analysis and part failure patterns for comprehensive cost pattern insights.

---
*Completed: 2026-01-15*
