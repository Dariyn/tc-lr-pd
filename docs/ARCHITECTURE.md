# Architecture Overview

System architecture and design documentation for the Work Order Cost Reduction Analysis Pipeline.

## System Design

### High-Level Architecture

The pipeline follows a three-stage architecture: Data Pipeline → Analysis → Output Generation.

**Stage 1: Data Pipeline** loads, cleans, categorizes, and validates work order data.
**Stage 2: Analysis** applies statistical methods to identify outliers, patterns, and trends.
**Stage 3: Output** generates reports, exports, and visualizations in multiple formats.

### Component Architecture

```
main.py (CLI Entry Point)
    ↓
PipelineOrchestrator
    ├─> Data Pipeline (4 modules)
    ├─> Analysis (6 modules)
    ├─> Reporting (3 modules)
    ├─> Exports (1 module)
    └─> Visualizations (2 modules)
```

## Module Overview

### 1. Data Pipeline (`src/pipeline/`)

Transforms raw CSV/Excel into clean, validated DataFrames.

**Modules:**
- `data_loader.py` - Load files with pandas, handle mixed types
- `data_cleaner.py` - Standardize formats, handle missing values
- `equipment_categorizer.py` - Assign categories (Service_Type_lv2 > FM_Type > Uncategorized)
- `quality_checker.py` - Calculate quality score (completeness 40%, consistency 40%, outliers 20%)

**Key Functions:**
- `run_pipeline(input_file)` → Returns (DataFrame, quality_report)

### 2. Analysis Modules (`src/analysis/`)

Statistical analysis to identify cost reduction opportunities.

**Equipment Analysis:**
- `frequency_analyzer.py` - Calculate work orders per month
- `outlier_detector.py` - Multi-method detection (Z-score, IQR, percentile)
- `equipment_ranker.py` - Priority scoring with consensus outliers

**Pattern Analysis:**
- `seasonal_analyzer.py` - Monthly/quarterly aggregation
- `vendor_analyzer.py` - Contractor performance metrics
- `failure_pattern_analyzer.py` - Text extraction from descriptions

**Statistical Methods:**
- Z-score threshold: 2.0 standard deviations
- IQR method: Q3 + 1.5×IQR
- Percentile threshold: 90th (top 10%)
- Consensus: Equipment flagged by 2+ methods

### 3. Reporting Engine (`src/reporting/`)

Generate professional reports from analysis results.

**Modules:**
- `report_builder.py` - Orchestrate report generation, build data structures
- `pdf_generator.py` - Create PDF with fpdf2
- `excel_generator.py` - Create 6-sheet workbook with xlsxwriter

**Design Pattern:**
- Builder pattern with Report and ReportSection dataclasses
- Specialized renderers for each section type
- Professional color scheme: Dark blue (#1f4788), light gray (#f0f0f0)

### 4. Data Export (`src/exports/`)

Export analysis results for integration with other tools.

**Module:**
- `data_exporter.py` - Convert DataFrames to CSV/JSON

**Features:**
- Clean NaN/Infinity → null in JSON
- Serialize pandas Timestamps as ISO strings
- UTF-8 encoding, pretty-printed JSON

### 5. Visualizations (`src/visualization/`)

Create static charts and interactive dashboards.

**Modules:**
- `chart_generator.py` - Matplotlib charts (PNG/SVG at 300 DPI)
- `dashboard_generator.py` - Plotly dashboard (HTML)

**Chart Types:**
- Equipment ranking: Horizontal bar chart
- Seasonal costs: Line chart with dual Y-axes
- Vendor performance: Grouped bar chart
- Failure patterns: Bar chart sorted by impact

### 6. Orchestration (`src/orchestrator/`)

Unified entry point coordinating all modules.

**Class:** `PipelineOrchestrator`

**Public Methods:**
```python
run_full_analysis() -> Dict[str, Any]
generate_reports(results: Dict) -> Dict[str, str]
export_data(results: Dict) -> Dict[str, List[str]]
generate_visualizations(results: Dict) -> Dict[str, Any]
```

## Data Flow

### End-to-End Pipeline

1. CLI parses arguments
2. PipelineOrchestrator initialized
3. run_full_analysis():
   - Load and clean data
   - Run all analysis modules
   - Return consolidated results dict
4. generate_reports() - Create PDF and Excel
5. export_data() - Generate CSV and JSON files
6. generate_visualizations() - Create charts and dashboard

### Data Schemas

**Cleaned Data (Stage 1 Output):**
```
Work_order_id, Equipment_ID, Equipment_Name, Equipment_Category,
Contractor, PO_AMOUNT, Work_Order_created_Date, 
Work_Order_Completed_Date, Work_Order_Description,
duration_days, is_outlier_cost
```

**Analysis Results (Stage 2 Output):**
```python
{
    'equipment_df': DataFrame,  # Ranked outliers with priority scores
    'seasonal_dict': dict,      # Monthly/quarterly cost patterns
    'vendor_df': DataFrame,     # Contractor performance metrics
    'patterns_list': list,      # High-impact failure patterns
    'quality_report': dict,     # Data quality score and issues
    'thresholds': dict          # Statistical thresholds
}
```

## Design Decisions

### Key Architectural Decisions

**1. Pandas for data handling**
- Better handling of mixed types than csv module
- Built-in statistical functions
- Efficient groupby operations
- Tradeoff: Higher memory usage

**2. Multi-method outlier detection**
- Z-score: Sensitive to distribution
- IQR: Robust to extremes
- Percentile: Category-relative
- Consensus reduces false positives

**3. Multiple output formats**
- PDF: Executive summary, print-friendly
- Excel: Data exploration with filtering
- CSV/JSON: Integration with other systems
- HTML: Interactive presentations

**4. Library choices**
- fpdf2: Pure Python, no external dependencies
- xlsxwriter: Optimized for creating new files
- matplotlib: Headless rendering (Agg backend)
- plotly: Best for interactive HTML

**5. Error handling**
- Graceful degradation for missing data
- Fail fast for critical errors (missing columns, quality < 85)
- Log warnings for non-critical issues

## Extensibility

### Adding New Analysis Modules

1. Create new file in `src/analysis/`
2. Implement analysis logic
3. Add to `PipelineOrchestrator._run_XXXX_analysis()`
4. Include results in consolidated dict
5. Update report builders

### Adding Custom Report Formats

1. Create new generator in `src/reporting/`
2. Implement `generate_report(report, output_path)`
3. Add to `PipelineOrchestrator.generate_reports()`

### Adding Export Formats

1. Add methods to `DataExporter`
2. Call from `PipelineOrchestrator.export_data()`

## Performance Considerations

### Memory Usage
- Typical dataset (10k records): ~50MB RAM
- Large dataset (100k records): ~500MB RAM

### Execution Time
- Data pipeline: 1-5 seconds
- Analysis: 2-10 seconds
- Reporting: 5-15 seconds
- Visualization: 3-8 seconds
- **Total:** 11-38 seconds typical

### Bottlenecks
- PDF table rendering
- Plotly dashboard for large datasets

### Optimization Opportunities
- Parallel processing for independent analyses
- Caching intermediate results
- Vectorized pandas operations

## Testing Strategy

- **Unit tests:** Individual module functions
- **Integration tests:** PipelineOrchestrator with sample data
- **Edge case tests:** Empty data, missing columns, extreme outliers

---

*For API usage, see [API Reference](API.md)*
*For usage examples, see [Usage Guide](USAGE.md)*
