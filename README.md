# Work Order Cost Reduction Analysis Pipeline

A comprehensive analysis pipeline that processes maintenance work order data to identify cost reduction opportunities through statistical analysis, pattern detection, and automated reporting.

## Overview

The Work Order Cost Reduction Analysis Pipeline transforms historical work order data into actionable insights for budget planning and maintenance optimization. By analyzing equipment maintenance patterns, seasonal trends, vendor performance, and failure modes, the pipeline identifies high-maintenance equipment and recurring cost drivers that stakeholders can confidently address.

The pipeline processes adhoc work order data (Excel or CSV format) through a multi-stage analysis workflow and produces professional PDF reports, detailed Excel workbooks, structured data exports (CSV/JSON), and interactive HTML dashboards. All outputs are designed to inform budget planning decisions with accurate, data-driven recommendations.

Stakeholders receive clear identification of:
- **High-maintenance equipment** - Statistical outlier detection identifies equipment with abnormally high repair frequencies or costs within their category
- **Seasonal cost patterns** - Monthly and quarterly trend analysis reveals budget planning opportunities
- **Vendor performance issues** - Cost efficiency, duration, and quality metrics highlight underperforming contractors
- **Recurring failure patterns** - Text analysis extracts common repair descriptions and failure modes

## Features

- **Automated work order data ingestion and cleaning** - Handles Excel (.xlsx) and CSV formats with robust error handling and data quality validation
- **Equipment maintenance priority ranking** - Multi-method statistical outlier detection (Z-score, IQR, percentile) with consensus-based flagging
- **Seasonal cost trend analysis** - Monthly and quarterly aggregation with pattern detection and variance calculation
- **Vendor performance comparison** - Cost efficiency, average duration, repeat work rates, and actionable recommendations
- **Failure pattern identification** - Keyword extraction from work order descriptions with impact scoring
- **Multiple output formats**:
  - **PDF reports** - Executive-friendly summary with visualizations and recommendations
  - **Excel workbooks** - 6-sheet detailed analysis with filters and formatting for data exploration
  - **CSV/JSON exports** - Structured data files for integration with other tools
  - **Interactive HTML dashboards** - Plotly-based visualizations with filtering and hover details
- **Comprehensive data quality validation** - Automated checks for completeness, consistency, and outlier rates with pass/fail scoring

## Requirements

- **Python 3.9+**
- **Dependencies:** See requirements.txt
  - pandas (data processing)
  - openpyxl (Excel I/O)
  - scipy (statistical analysis)
  - fpdf2 (PDF generation)
  - xlsxwriter (Excel report formatting)
  - matplotlib (static charts)
  - plotly (interactive visualizations)
- **Input:** CSV or Excel file with work order data (see Input Data Format below)

## Installation

```bash
# Clone repository
git clone https://github.com/yourusername/linkreit-pd.git
cd linkreit-pd

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scriptsctivate

# Install dependencies
pip install -r requirements.txt
```

## Quick Start

```bash
# Run basic analysis with PDF and Excel reports (default)
python main.py analyze -i data/work_orders.csv

# Generate all outputs (reports + exports + visualizations)
python main.py analyze -i data/work_orders.csv --all

# Custom output directory
python main.py analyze -i data/work_orders.csv -o results/

# Exports and visualizations only (skip reports)
python main.py analyze -i data/work_orders.csv --no-reports --exports --visualizations
```

## Input Data Format

The pipeline expects work order data with the following columns:

| Column | Description | Example | Required |
|--------|-------------|---------|----------|
| Work_order_id | Unique work order identifier | WO-001 | Yes |
| Equipment_ID | Equipment identifier | EQ-12345 | Yes* |
| Equipment_Name | Equipment description | Air Conditioner Unit 3 | Yes |
| Contractor | Vendor/contractor name | ABC Maintenance | No |
| Service_Type_lv2 | Service category level 2 | HVAC Repair | No |
| FM_Type | Facility management type | Mechanical | No |
| PO_AMOUNT | Purchase order amount (cost) | 1250.50 | Yes |
| Work_Order_created_Date | Work order creation date | 2024-01-15 | Yes |
| Work_Order_Completed_Date | Work order completion date | 2024-01-18 | Yes |
| Work_Order_Description | Problem description | AC compressor failure | No |

*Equipment_ID is auto-generated from Equipment_Name hash if missing.

**Data Quality Requirements:**
- At least 85% of records must have complete required fields
- Valid date formats (ISO 8601 or common formats)
- Numeric cost values (negative values excluded from analysis)
- Consistent equipment categorization (80%+ consistency threshold)

## Output Files

After running the pipeline, outputs are organized in the `output/` directory:

### Reports (`output/reports/`)
- `work_order_analysis.pdf` - Executive summary with visualizations, outlier equipment lists, seasonal trends, vendor recommendations, and failure patterns
- `work_order_analysis.xlsx` - Detailed 6-sheet workbook:
  - **Summary** - Key metrics and recommendations
  - **Equipment** - Ranked equipment with frequency, cost, and outlier flags
  - **Seasonal** - Monthly and quarterly cost trends
  - **Vendors** - Vendor performance metrics and rankings
  - **Failures** - High-impact failure patterns with frequencies
  - **Recommendations** - Actionable items by category

### Exports (`output/exports/`)
Structured data files (CSV and JSON formats) for each analysis type:
- `equipment_rankings.csv/json` - Complete equipment analysis with scores
- `seasonal_patterns.csv/json` - Monthly and quarterly cost data
- `vendor_metrics.csv/json` - Vendor performance statistics
- `failure_patterns.csv/json` - Extracted patterns with impact scores

### Visualizations (`output/visualizations/`)
- `equipment_ranking.png` - Top 10 equipment by priority score
- `seasonal_costs.png` - Monthly cost trends over time
- `vendor_costs.png` - Vendor performance comparison
- `failure_patterns.png` - Top 10 failure patterns by frequency
- `dashboard.html` - Interactive dashboard with all 4 chart types, filtering, and hover details

## Documentation

- [Usage Guide](docs/USAGE.md) - Detailed usage scenarios, CLI reference, and troubleshooting
- [Architecture](docs/ARCHITECTURE.md) - System design, module overview, and data flow
- [API Reference](docs/API.md) - Programmatic API documentation for Python integration

## Project Structure

```
linkreit-pd/
├── main.py                    # CLI entry point
├── requirements.txt           # Python dependencies
├── data/                      # Input data files (user-provided)
├── output/                    # Generated outputs
│   ├── reports/              # PDF and Excel reports
│   ├── exports/              # CSV and JSON exports
│   └── visualizations/       # Charts and dashboard
├── src/
│   ├── pipeline/             # Data pipeline (load, clean, categorize, quality)
│   ├── analysis/             # Analysis modules (equipment, seasonal, vendor, failure)
│   ├── reporting/            # Report generation (PDF, Excel)
│   ├── exports/              # Data export utilities
│   ├── visualization/        # Chart and dashboard generation
│   └── orchestrator/         # Pipeline orchestration
└── tests/                     # Test suite
```

## Example Workflow

1. **Prepare data** - Export work order data from your system as CSV or Excel
2. **Run analysis** - Execute pipeline with desired output flags
3. **Review quality report** - Check console output for data quality score (must be 85+)
4. **Examine outputs**:
   - PDF report for executive summary
   - Excel workbook for detailed exploration with filters
   - Interactive dashboard for visual pattern discovery
   - CSV exports for integration with other tools
5. **Share with stakeholders** - Distribute reports and recommendations for budget planning

## License

[Specify license - MIT recommended for open source]

## Contributing

[Add contribution guidelines if applicable]

## Support

For issues, questions, or feature requests, please [open an issue](https://github.com/yourusername/linkreit-pd/issues).
