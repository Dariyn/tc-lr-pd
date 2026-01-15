# Plan 03-03 Summary: Failure Pattern Analysis

**Phase:** 03-cost-pattern-analysis
**Plan:** 03
**Completed:** 2026-01-15
**Status:** ✅ Complete

## Objective

Extract and analyze failure patterns from work order text fields to identify recurring issues, enabling prioritization of preventive maintenance and equipment upgrades.

## What Was Built

### Core Implementation

**FailurePatternAnalyzer** (`src/analysis/failure_pattern_analyzer.py`)
- Text extraction and keyword filtering with stopword removal
- Support for mixed language text (English/Chinese)
- Common phrase detection (2-3 word patterns)
- Failure categorization by keywords (leak, broken, malfunction, electrical, etc.)
- Recurring issue identification by equipment or overall
- Pattern cost calculation with total/average aggregation
- High-impact pattern detection (frequency + cost + equipment affected)
- Actionable recommendations with category-specific suggestions

### Test Coverage

**Comprehensive Test Suite** (`tests/test_failure_pattern_analyzer.py`)
- 24 tests covering all functionality
- Keyword extraction (basic, min_length, mixed language, punctuation)
- Phrase detection and frequency counting
- Failure categorization and cost calculation
- Recurring issue identification (by equipment and overall)
- Pattern cost analysis and aggregation
- High-impact pattern filtering with thresholds
- Recommendation generation with category-specific suggestions
- Edge cases: empty text, single words, missing fields, no patterns
- All tests passing ✅

## Key Features

### 1. Text Processing
- Keyword extraction with configurable minimum length
- Stopword filtering for English text
- Preservation of non-ASCII characters for Chinese/multilingual text
- Punctuation removal and normalization

### 2. Pattern Detection
- Bigram and trigram phrase extraction
- Frequency counting across work orders
- Category assignment based on failure keywords
- Recurring issue tracking per equipment or system-wide

### 3. Cost Correlation
- Total and average cost calculation per pattern
- Equipment affected count
- Impact score: `frequency × cost × equipment_affected`
- High-impact pattern filtering (above median cost + minimum occurrences)

### 4. Recommendations
- Category-specific maintenance suggestions
- 10 failure categories with tailored recommendations:
  - Leak: seal/gasket upgrades
  - Broken: preventive replacement
  - Electrical: system audit
  - Malfunction: root cause investigation
  - Worn: preventive maintenance program
  - Clog: cleaning frequency increase
  - Noise: vibration analysis
  - Motor: predictive maintenance
  - Sensor: calibration/replacement
  - Valve: inspection/upgrade

## Technical Decisions

| Decision | Rationale |
|----------|-----------|
| Simple text processing over ML | Faster development, no training data needed, transparent logic |
| 2-3 word phrases for patterns | Balance between specificity and frequency |
| Stopword filtering for English only | Preserve meaning in multilingual text |
| Multiple failure categories | Enable targeted recommendations |
| Impact score formula | Combines frequency, cost, and scope for prioritization |
| Median cost threshold | Relative comparison within dataset |
| Min 5 occurrences for high-impact | Focus on truly recurring issues |

## Files Modified

- `src/analysis/failure_pattern_analyzer.py` - New analyzer class
- `tests/test_failure_pattern_analyzer.py` - Comprehensive test suite

## Verification Results

- ✅ All 24 tests passing
- ✅ Keyword extraction filters stopwords correctly
- ✅ Common phrases identified with frequency counts
- ✅ Pattern costs calculated accurately
- ✅ High-impact patterns flagged appropriately
- ✅ Recommendations are actionable and category-specific
- ✅ No import errors or type issues
- ✅ Edge cases handled gracefully

## Example Output

### Pattern Detection
```
pattern              | occurrences | total_cost | avg_cost | category | equipment_affected
---------------------|-------------|------------|----------|----------|-------------------
refrigerant leak     | 15          | $67,500    | $4,500   | leak     | 8
motor malfunction    | 12          | $36,000    | $3,000   | motor    | 12
pipe leak            | 10          | $8,000     | $800     | leak     | 10
```

### Recommendations
```json
{
  "pattern": "refrigerant leak",
  "occurrences": 15,
  "total_cost": "$67,500",
  "avg_cost": "$4,500",
  "category": "leak",
  "equipment_affected": 8,
  "suggestion": "Inspect all affected equipment for refrigerant leak. Consider upgrading seals, gaskets, or piping to prevent future leaks. Priority: affects 8 equipment items."
}
```

## Integration Points

**Inputs:**
- Work order DataFrame with text fields: Problem, Cause, Remedy, description
- PO_AMOUNT for cost correlation
- Equipment_ID for recurring issue tracking per equipment

**Outputs:**
- Pattern frequency DataFrames
- Failure category distributions
- High-impact pattern lists
- Actionable recommendation lists

## Next Steps

This analyzer provides the foundation for:
- Phase 3 Plan 4: Integration with seasonal trends
- Phase 4: Report generation with pattern insights
- Phase 5: Visualization of failure patterns and categories
- Budget planning informed by high-impact recurring issues

## Performance Notes

- Fast text processing (no ML overhead)
- Scales linearly with number of work orders
- Memory efficient (streaming phrase generation)
- 24 tests run in < 1 second

---

**Plan completed successfully on 2026-01-15**
