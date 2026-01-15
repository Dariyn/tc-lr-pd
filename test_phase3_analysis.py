"""Quick test runner for Phase 3 cost pattern analyses."""

import pandas as pd
from src.pipeline.pipeline import run_pipeline
from src.analysis.seasonal_analyzer import SeasonalAnalyzer
from src.analysis.vendor_analyzer import VendorAnalyzer
from src.analysis.failure_pattern_analyzer import FailurePatternAnalyzer

# Input file
input_file = 'input/adhoc_wo_20240101_20250531.xlsx - in.csv'

print("=" * 70)
print("PHASE 3: COST PATTERN ANALYSIS - TEST RUN")
print("=" * 70)

# Load and prepare data
print("\n[1/4] Loading data...")
df, quality_report = run_pipeline(input_file)
print(f"✓ Loaded {len(df)} work orders")

# Test 1: Seasonal Analysis
print("\n" + "=" * 70)
print("TEST 1: SEASONAL COST PATTERNS")
print("=" * 70)

seasonal = SeasonalAnalyzer()

# Monthly costs
monthly = seasonal.calculate_monthly_costs(df)
print(f"\n✓ Monthly analysis: {len(monthly)} months")
print("\nTop 3 most expensive months:")
print(monthly.nlargest(3, 'total_cost')[['month', 'total_cost', 'work_order_count']])

# Quarterly costs
quarterly = seasonal.calculate_quarterly_costs(df)
print(f"\n✓ Quarterly analysis: {len(quarterly)} quarters")
print("\nQuarterly breakdown:")
print(quarterly[['quarter', 'total_cost', 'work_order_count']])

# Detect patterns
patterns = seasonal.detect_patterns(monthly)
print(f"\n✓ Pattern detection: {len(patterns)} patterns found")
if patterns:
    print("\nIdentified patterns:")
    for p in patterns[:3]:
        print(f"  - {p['pattern']} ({p['confidence']} confidence)")

# Test 2: Vendor Analysis
print("\n" + "=" * 70)
print("TEST 2: VENDOR COST PERFORMANCE")
print("=" * 70)

vendor = VendorAnalyzer()

# Vendor costs
vendor_costs = vendor.calculate_vendor_costs(df, min_work_orders=3)
print(f"\n✓ Vendor analysis: {len(vendor_costs)} vendors (3+ work orders)")

if len(vendor_costs) > 0:
    print("\nTop 5 vendors by total cost:")
    top_vendors = vendor_costs.nlargest(5, 'total_cost')
    print(top_vendors[['contractor', 'total_cost', 'wo_count', 'avg_cost']])

    # High-cost vendors
    high_cost = vendor.identify_high_cost_vendors(vendor_costs)
    print(f"\n✓ High-cost vendors (75th percentile): {len(high_cost)}")

    # Get recommendations
    recommendations = vendor.get_vendor_recommendations(vendor_costs)
    print(f"\n✓ Recommendations: {len(recommendations)} generated")
    if recommendations:
        print("\nSample recommendations:")
        for rec in recommendations[:3]:
            print(f"  - {rec['vendor']}: {rec['issue']} - {rec['suggestion']}")
else:
    print("\n⚠ No vendors found with 3+ work orders")

# Test 3: Failure Pattern Analysis
print("\n" + "=" * 70)
print("TEST 3: FAILURE PATTERN DETECTION")
print("=" * 70)

failure = FailurePatternAnalyzer()

# Find common phrases
phrases = failure.find_common_phrases(df, field='Problem', top_n=10)
print(f"\n✓ Common phrases: Top 10 from Problem field")
if len(phrases) > 0:
    print("\nMost common failure descriptions:")
    print(phrases[['phrase', 'frequency']].head(5))

# Categorize failures
categorized = failure.categorize_by_failure_type(df)
print(f"\n✓ Failure categorization: {categorized['failure_category'].nunique()} categories")
print("\nFailure type breakdown:")
print(categorized['failure_category'].value_counts().head(5))

# High-impact patterns
high_impact = failure.find_high_impact_patterns(categorized, min_occurrences=3)
print(f"\n✓ High-impact patterns: {len(high_impact)} patterns (3+ occurrences)")
if len(high_impact) > 0:
    print("\nTop patterns by cost:")
    print(high_impact[['pattern', 'occurrences', 'total_cost', 'avg_cost']].head(5))

    # Get recommendations
    recs = failure.get_pattern_recommendations(high_impact)
    print(f"\n✓ Recommendations: {len(recs)} generated")
    if recs:
        print("\nSample recommendations:")
        for rec in recs[:3]:
            print(f"  - {rec['pattern']}: {rec['suggestion']}")

print("\n" + "=" * 70)
print("PHASE 3 ANALYSIS COMPLETE")
print("=" * 70)
print("\n✓ All three analysis types executed successfully")
print("✓ Seasonal trends, vendor performance, and failure patterns analyzed")
print("\nNext steps:")
print("  - Review findings above for actionable insights")
print("  - Phase 4: Generate formal reports (PDF/Excel)")
print("  - Phase 5: Create interactive visualizations")
