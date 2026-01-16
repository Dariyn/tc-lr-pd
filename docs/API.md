# API Reference

Programmatic API documentation for using the Work Order Analysis Pipeline as a Python library.

## Overview

While the pipeline provides a CLI interface via `main.py`, you can also use it programmatically in your own Python scripts. This allows for custom integration, automation, and batch processing workflows.

## Installation

Import the pipeline modules into your Python environment:

```python
from src.orchestrator import PipelineOrchestrator
from src.pipeline.pipeline import run_pipeline
from src.analysis import *
from src.reporting import *
from src.exports import DataExporter
from src.visualization import *
```

## Core APIs

### PipelineOrchestrator

Main orchestration class that coordinates all pipeline modules.

#### Initialization

```python
from src.orchestrator import PipelineOrchestrator

orchestrator = PipelineOrchestrator(
    input_file='data/work_orders.csv',
    output_dir='output/'
)
```

**Parameters:**
- `input_file` (str): Path to input CSV or Excel file
- `output_dir` (str, optional): Base directory for outputs (default: 'output/')

#### Methods

##### run_full_analysis()

Execute complete analysis pipeline and return results.

```python
results = orchestrator.run_full_analysis()
```

**Returns:** `Dict[str, Any]`
```python
{
    'equipment_df': pd.DataFrame,     # Ranked equipment with priority scores
    'seasonal_dict': dict,            # Monthly/quarterly cost patterns
    'vendor_df': pd.DataFrame,        # Vendor performance metrics
    'patterns_list': list,            # High-impact failure patterns
    'quality_report': dict,           # Data quality metrics
    'thresholds': dict,               # Statistical thresholds
    'category_stats': pd.DataFrame    # Category statistics
}
```

**Raises:**
- `FileNotFoundError`: Input file doesn't exist
- `ValueError`: Data fails quality checks (score < 85)
- `Exception`: Processing errors


**Example:**
```python
try:
    results = orchestrator.run_full_analysis()
    print(f"Found {len(results['equipment_df'])} outlier equipment")
except ValueError as e:
    print(f"Data quality check failed: {e}")
```

##### generate_reports(results)

Generate PDF and Excel reports.

```python
report_paths = orchestrator.generate_reports(results)
# Returns: {'pdf_path': '...', 'excel_path': '...'}
```

##### export_data(results)

Export to CSV and JSON files.

```python
export_paths = orchestrator.export_data(results)
# Returns: {'csv': [...], 'json': [...]}
```

##### generate_visualizations(results)

Generate charts and dashboard.

```python
viz_paths = orchestrator.generate_visualizations(results)
# Returns: {'charts': [...], 'dashboard': '...'}
```

### Data Pipeline

```python
from src.pipeline.pipeline import run_pipeline
df, quality_report = run_pipeline('data/work_orders.csv')
```

### Analysis Modules

**Equipment Analysis:**
```python
from src.analysis.analysis_pipeline import run_equipment_analysis
ranked_df, category_stats, thresholds = run_equipment_analysis('data/work_orders.csv')
```

**Seasonal Analysis:**
```python
from src.analysis.seasonal_analyzer import SeasonalAnalyzer
analyzer = SeasonalAnalyzer()
monthly_costs = analyzer.calculate_monthly_costs(df)
```

**Vendor Analysis:**
```python
from src.analysis.vendor_analyzer import VendorAnalyzer
analyzer = VendorAnalyzer(min_work_orders=3)
vendor_costs = analyzer.calculate_vendor_costs(df)
```

**Failure Pattern Analysis:**
```python
from src.analysis.failure_pattern_analyzer import FailurePatternAnalyzer
analyzer = FailurePatternAnalyzer()
high_impact = analyzer.find_high_impact_patterns(df, min_occurrences=5)
```

### Report Generation

```python
from src.reporting.pdf_generator import PDFReportGenerator
from src.reporting.excel_generator import ExcelReportGenerator
from src.reporting.report_builder import ReportBuilder

builder = ReportBuilder('data/work_orders.csv')
report = builder.build_report()

pdf_gen = PDFReportGenerator()
pdf_gen.generate_pdf(report, 'output/report.pdf')

excel_gen = ExcelReportGenerator()
excel_gen.generate_report(report, 'output/report.xlsx')
```

### Data Exports

```python
from src.exports.data_exporter import DataExporter

exporter = DataExporter()
exporter.export_equipment_rankings(equipment_df, 'output/equipment.csv')
exporter.export_equipment_rankings_json(equipment_df, 'output/equipment.json')
```

### Visualizations

```python
from src.visualization.chart_generator import ChartGenerator
from src.visualization.dashboard_generator import DashboardGenerator

# Charts
chart_gen = ChartGenerator(dpi=300)
chart_gen.create_equipment_ranking_chart(equipment_df, 'output/chart.png', top_n=10)

# Dashboard
dashboard_gen = DashboardGenerator()
dashboard_gen.create_dashboard(
    equipment_df=equipment_df,
    seasonal_dict=seasonal_dict,
    vendor_df=vendor_df,
    patterns_list=patterns_list,
    output_path='output/dashboard.html'
)
```

## Complete Examples

### Example 1: Basic Workflow

```python
from src.orchestrator import PipelineOrchestrator

orchestrator = PipelineOrchestrator('data/work_orders.csv', 'output/')
results = orchestrator.run_full_analysis()
orchestrator.generate_reports(results)
orchestrator.export_data(results)
orchestrator.generate_visualizations(results)

print(f"Outlier equipment: {len(results['equipment_df'])}")
print(f"Quality score: {results['quality_report']['score']}")
```

### Example 2: Batch Processing

```python
import os
from src.orchestrator import PipelineOrchestrator

for quarter in ['Q1', 'Q2', 'Q3', 'Q4']:
    input_file = f'data/2024_{quarter}.csv'
    if not os.path.exists(input_file):
        continue
    
    orchestrator = PipelineOrchestrator(input_file, f'output/{quarter}/')
    try:
        results = orchestrator.run_full_analysis()
        orchestrator.generate_reports(results)
        print(f"{quarter} complete")
    except Exception as e:
        print(f"Error: {e}")
```

## Error Handling

```python
try:
    orchestrator = PipelineOrchestrator(input_file='data.csv')
    results = orchestrator.run_full_analysis()
except FileNotFoundError:
    print("Input file not found")
except ValueError as e:
    print(f"Data quality check failed: {e}")
except Exception as e:
    print(f"Pipeline error: {e}")
```

## Best Practices

1. Always check data quality before relying on results
2. Handle exceptions with try/except blocks
3. Validate inputs before processing
4. Use appropriate formats for different audiences
5. Process large datasets in chunks
6. Clear matplotlib cache after generating many charts

---

*See also: [Usage Guide](USAGE.md), [Architecture](ARCHITECTURE.md), [README](../README.md)*
