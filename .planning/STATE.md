# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-01-14)

**Core value:** Accurate identification of cost reduction opportunities that stakeholders can confidently act on.
**Current focus:** Phase 6 — Integration Testing

## Current Position

Phase: 6 of 6 (Integration Testing)
Plan: 2 of 2 in current phase
Status: Phase complete
Last activity: 2026-01-16 — Completed 06-02-PLAN.md

Progress: █████████████ 100%

## Performance Metrics

**Velocity:**
- Total plans completed: 18
- Average duration: 14 min
- Total execution time: 4.0 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 1 | 4 | 16 min | 4 min |
| 2 | 3 | 12 min | 4 min |
| 3 | 3 | 20 min | 7 min |
| 4 | 3 | 130 min | 43 min |
| 5 | 3 | 35 min | 12 min |
| 6 | 2 | 65 min | 33 min |

**Recent Trend:**
- Last 5 plans: 15 min, 15 min, 25 min, 40 min
- Trend: Integration testing requires more time (averaging 33min for comprehensive test suites)

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- Multiple output formats (reports + exports + visualizations) for different stakeholder needs
- Batch processing approach aligning with export-based workflow
- Use pandas for data loading instead of csv module for better handling of mixed types (Phase 1, Plan 1)
- Schema validation with Python constants rather than external schema file (Phase 1, Plan 1)
- Graceful error handling with errors='coerce' for data quality issues (Phase 1, Plan 1)
- Flag outliers instead of removing them for review (Phase 1, Plan 2)
- Use 99th percentile as outlier threshold (Phase 1, Plan 2)
- Generate synthetic Equipment_ID from name hash when missing (Phase 1, Plan 2)
- Fill missing PO_AMOUNT with 0 for adhoc work (Phase 1, Plan 2)
- Priority-based fallback: service_type_lv2 > FM_Type > Uncategorized for category assignment (Phase 1, Plan 3)
- 80% consistency threshold to flag potentially miscategorized equipment (Phase 1, Plan 3)
- Title case standardization for mixed language category names (Phase 1, Plan 3)
- Quality score uses weighted average: completeness 40%, consistency 40%, outlier rate 20% (Phase 1, Plan 4)
- Pass threshold set to 85/100 for overall quality score (Phase 1, Plan 4)
- Pipeline exits with code 0 if quality passed, code 1 if failed (Phase 1, Plan 4)
- Work orders per month uses 30.44 avg days/month for consistent normalization (Phase 2, Plan 1)
- Timespan defaults to 1 day for single work order equipment (Phase 2, Plan 1)
- Zero and negative costs excluded from average cost calculation (Phase 2, Plan 1)
- Z-score threshold set to 2.0 standard deviations for outlier detection (Phase 2, Plan 2)
- IQR method uses 1.5*IQR beyond Q3 for robust detection (Phase 2, Plan 2)
- Percentile method set to 90th percentile to flag top 10% in category (Phase 2, Plan 2)
- Consensus approach requires 2+ methods to flag equipment as outlier (Phase 2, Plan 2)
- Priority score weighted: frequency 40%, cost 40%, outlier status 20% (Phase 2, Plan 3)
- Normalized metrics within categories (0-1 scale) for fair comparison (Phase 2, Plan 3)
- Cost impact = total_work_orders * avg_cost representing total maintenance spend (Phase 2, Plan 3)
- Outlier score levels: 1.0 consensus, 0.5 any flag, 0.0 none (Phase 2, Plan 3)
- Filter to consensus outliers only for focused actionable results (Phase 2, Plan 3)
- Thresholds calculated from median values of consensus outliers (Phase 2, Plan 3)
- Minimum work order threshold of 3 for vendor analysis to exclude one-off contractors (Phase 3, Plan 2)
- Cost efficiency metric: cost per day (avg_cost / avg_duration) for vendor performance (Phase 3, Plan 2)
- Quality indicator: repeat rate (% equipment with 2+ WOs) as proxy for rework (Phase 3, Plan 2)
- Vendor recommendation thresholds: 75th percentile for cost/duration/efficiency, >50% for quality (Phase 3, Plan 2)
- Unknown contractors grouped as "Unknown" with configurable label, excluded by default (Phase 3, Plan 2)
- Simple text processing (no ML) for pattern detection with transparent logic (Phase 3, Plan 3)
- 2-3 word phrases for pattern identification balancing specificity and frequency (Phase 3, Plan 3)
- Stopword filtering for English only to preserve meaning in multilingual text (Phase 3, Plan 3)
- Impact score formula: frequency × cost × equipment_affected for prioritization (Phase 3, Plan 3)
- Median cost threshold for high-impact pattern relative comparison (Phase 3, Plan 3)
- Minimum 5 occurrences for high-impact patterns to focus on truly recurring issues (Phase 3, Plan 3)
- Use dataclasses for Report and ReportSection for clean data modeling (Phase 4, Plan 1)
- Builder pattern for orchestrating report generation across modules (Phase 4, Plan 1)
- Section-based structure: equipment, seasonal, vendor, failure analyses (Phase 4, Plan 1)
- Handle edge cases gracefully: no outliers, missing data, empty sections (Phase 4, Plan 1)
- Format numbers for display: currency with $, commas, percentages to 1 decimal (Phase 4, Plan 1)
- Use fpdf2 for PDF generation (pure Python, lightweight, no external dependencies) (Phase 4, Plan 2)
- Specialized section renderers for each analysis type with custom layouts (Phase 4, Plan 2)
- Calculate text width explicitly for bullet points: text_width = page_width - margins - indent (Phase 4, Plan 2)
- Dark blue headers (#1f4788) and light gray alternating rows (#f0f0f0) for professional PDF appearance (Phase 4, Plan 2)
- Use xlsxwriter for Excel generation (optimized for creating new files, rich formatting) (Phase 4, Plan 3)
- 6-sheet Excel structure: Summary, Equipment, Seasonal, Vendors, Failures, Recommendations (Phase 4, Plan 3)
- Format standards: dark blue headers (#1f4788), alternating rows (#f0f0f0), borders, frozen panes (Phase 4, Plan 3)
- Freeze header rows and add autofilters for all data tables in Excel (Phase 4, Plan 3)
- Handle Excel edge cases with informative messages instead of errors (Phase 4, Plan 3)
- Use pandas.to_csv() with index=False for clean CSV exports (Phase 5, Plan 1)
- JSON exports use indent=2 for human readability (Phase 5, Plan 1)
- Clean NaN/Infinity values by converting to null in JSON exports (Phase 5, Plan 1)
- Serialize pandas Timestamps as ISO strings for JSON compatibility (Phase 5, Plan 1)
- Column name mapping for export consistency (occurrences → frequency, equipment_affected → equipment_count) (Phase 5, Plan 1)
- Use matplotlib with Agg backend for headless chart generation without GUI dependencies (Phase 5, Plan 2)
- Professional color scheme: dark blue #1f4788 for primary, consistent with PDF/Excel reports (Phase 5, Plan 2)
- Support both PNG (300 DPI for print quality) and SVG formats for visualization flexibility (Phase 5, Plan 2)
- Create placeholder charts for empty data instead of errors for robust report generation (Phase 5, Plan 2)
- Normalize vendor metrics to similar scales for grouped bar chart visibility (Phase 5, Plan 2)
- Use plotly for interactive dashboards (best library for HTML output, self-contained, no server required) (Phase 5, Plan 3)
- CDN approach for plotly.js acceptable (works offline with browser cache, simpler than embedding full library) (Phase 5, Plan 3)
- Subplot layout (2x2 grid) for comprehensive dashboard with all four analysis views (Phase 5, Plan 3)
- Dynamic chart heights based on data size (max(400, n*30) for bar charts) (Phase 5, Plan 3)
- Category-based color coding with clickable legend filtering for equipment and failure charts (Phase 5, Plan 3)
- Dual Y-axes for seasonal charts (cost + work order count) to show correlation (Phase 5, Plan 3)
- Consistent hover templates across all charts with formatted currency and counts (Phase 5, Plan 3)
- PipelineOrchestrator provides 4 main methods: run_full_analysis(), generate_reports(), export_data(), generate_visualizations() (Phase 6, Plan 1)
- CLI defaults to reports only, requires explicit flags for exports and visualizations (Phase 6, Plan 1)
- Output directory structure: output/{reports,exports,visualizations}/ (Phase 6, Plan 1)
- Graceful error handling for missing data - return empty structures rather than crash (Phase 6, Plan 1)
- Integration tests use real pipeline execution with sample data (not mocking) (Phase 6, Plan 1)
- Created 65-row realistic dataset spanning full year with seasonal patterns (Phase 6, Plan 2)
- Used actual column names (is_outlier_consensus) not assumptions (Phase 6, Plan 2)
- Smoke tests verify graceful handling of edge cases (Phase 6, Plan 2)
- Performance benchmarks use @pytest.mark.slow for selective execution (Phase 6, Plan 2)
- Tests verify file format validity (PDF magic bytes, Excel sheets, JSON parsing) (Phase 6, Plan 2)

### Deferred Issues

None yet.

### Blockers/Concerns

None yet.

## Session Continuity

Last session: 2026-01-16T12:20:00Z
Stopped at: Completed 06-02-PLAN.md (Phase 6 complete - ALL PHASES COMPLETE)
Resume file: None
