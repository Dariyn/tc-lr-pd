# Usage Guide

Comprehensive guide to using the Work Order Cost Reduction Analysis Pipeline for maintenance data analysis and budget planning.

## Table of Contents

- [Installation and Setup](#installation-and-setup)
- [CLI Reference](#cli-reference)
- [Input Data Preparation](#input-data-preparation)
- [Running Analysis](#running-analysis)
- [Understanding Outputs](#understanding-outputs)
- [Advanced Usage](#advanced-usage)
- [Troubleshooting](#troubleshooting)

## Installation and Setup

### Prerequisites

- Python 3.9 or higher
- pip package manager
- 500MB disk space for outputs
- Windows, macOS, or Linux operating system

### Step-by-Step Installation

1. **Install Python** (if not already installed)
   - Download from [python.org](https://www.python.org/downloads/)
   - Verify installation: `python --version`

2. **Clone or download the repository**
   ```bash
   git clone https://github.com/yourusername/linkreit-pd.git
   cd linkreit-pd
   ```

3. **Create virtual environment** (recommended)
   ```bash
   # Create virtual environment
   python -m venv venv
   
   # Activate on Windows
   venv\Scriptsctivate
   
   # Activate on macOS/Linux
   source venv/bin/activate
   ```

4. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Verify installation**
   ```bash
   python main.py --help
   ```
   You should see the CLI help message.

## CLI Reference

### Basic Command Structure

```bash
python main.py analyze [OPTIONS]
```

### Required Arguments

- `-i, --input PATH` - Path to input CSV or Excel file with work order data

### Optional Arguments

- `-o, --output DIR` - Output directory for all generated files (default: `output/`)
- `--no-reports` - Skip PDF and Excel report generation
- `-e, --exports` - Export CSV and JSON data files
- `-v, --visualizations` - Generate charts (PNG) and interactive dashboard (HTML)
- `-a, --all` - Generate everything: reports + exports + visualizations

### Usage Examples

#### Example 1: Basic Analysis (Reports Only)

Generate PDF and Excel reports only (default behavior):

```bash
python main.py analyze -i data/work_orders.csv
```

**Output:**
- `output/reports/work_order_analysis.pdf`
- `output/reports/work_order_analysis.xlsx`

#### Example 2: Complete Analysis (All Outputs)

Generate reports, exports, and visualizations:

```bash
python main.py analyze -i data/work_orders.csv --all
```

**Output:**
- Reports: PDF and Excel
- Exports: 8 files (4 CSV + 4 JSON)
- Visualizations: 4 PNG charts + 1 HTML dashboard

#### Example 3: Custom Output Directory

Save outputs to a custom location:

```bash
python main.py analyze -i data/work_orders.csv -o results/2024_analysis/
```

**Output:**
- `results/2024_analysis/reports/...`
- `results/2024_analysis/exports/...`
- `results/2024_analysis/visualizations/...`

#### Example 4: Exports Only (No Reports)

Generate data exports without PDF/Excel reports:

```bash
python main.py analyze -i data/work_orders.csv --no-reports --exports
```

**Use case:** When you want raw data files for integration with other systems.

#### Example 5: Reports + Visualizations (No Exports)

```bash
python main.py analyze -i data/work_orders.csv --visualizations
```

**Use case:** Presentation materials without raw data files.

#### Example 6: Excel Input File

The pipeline accepts both CSV and Excel formats:

```bash
python main.py analyze -i data/work_orders.xlsx --all
```

## Input Data Preparation

### Required Columns

The pipeline requires these columns in your input file:

| Column | Type | Description | Validation Rules |
|--------|------|-------------|------------------|
| Work_order_id | String | Unique identifier | Must be unique |
| Equipment_ID | String | Equipment identifier | Auto-generated if missing |
| Equipment_Name | String | Equipment description | Required |
| PO_AMOUNT | Number | Cost/amount | Must be numeric, negatives excluded |
| Work_Order_created_Date | Date | Creation date | Valid date format |
| Work_Order_Completed_Date | Date | Completion date | Valid date format, after created date |

### Optional Columns

These columns enhance analysis quality when present:

| Column | Purpose | Impact if Missing |
|--------|---------|-------------------|
| Contractor | Vendor analysis | Vendor metrics unavailable |
| Service_Type_lv2 | Categorization | Uses FM_Type fallback |
| FM_Type | Categorization | Uses "Uncategorized" fallback |
| Work_Order_Description | Failure patterns | Pattern analysis unavailable |

### Data Quality Requirements

The pipeline validates data quality before analysis:

1. **Completeness** (40% weight)
   - At least 85% of records must have all required fields
   - Missing Equipment_ID is auto-generated
   - Missing PO_AMOUNT defaults to 0 for adhoc work

2. **Consistency** (40% weight)
   - Equipment categorization must be 80%+ consistent
   - Date formats must be valid and parseable
   - Numeric fields must be valid numbers

3. **Outlier Rate** (20% weight)
   - Extreme outliers are flagged but not removed
   - Must be below 1% of total records

4. **Overall Score**
   - Weighted average must be 85/100 or higher
   - Pipeline exits with error if quality check fails

### Common Data Issues and Fixes

**Issue:** Missing Equipment_ID column
**Fix:** Automatically generated from Equipment_Name hash

**Issue:** Date formats vary (MM/DD/YYYY vs YYYY-MM-DD)
**Fix:** Pipeline parses multiple date formats automatically

**Issue:** Mixed case in category names
**Fix:** Standardized to Title Case during cleaning

**Issue:** Negative costs in data
**Fix:** Excluded from average cost calculations, flagged in quality report

**Issue:** Missing contractor information
**Fix:** Grouped as "Unknown" and excluded from vendor analysis

### Sample Data Template

CSV format:

\n
## Running Analysis

### Step-by-Step Walkthrough

#### Step 1: Prepare Input Data

1. Export work order data from your system
2. Save as CSV or Excel (.xlsx) format
3. Verify required columns are present
4. Place file in `data/` directory (or specify custom path)

#### Step 2: Run Analysis

```bash
python main.py analyze -i data/work_orders.csv --all
```

The pipeline will:
1. **Load data** - Read CSV/Excel and parse columns
2. **Clean data** - Standardize formats, handle missing values
3. **Categorize** - Assign equipment categories
4. **Validate quality** - Check data quality score (must be 85+)
5. **Analyze equipment** - Detect outliers, rank by priority
6. **Analyze seasonality** - Calculate monthly/quarterly patterns
7. **Analyze vendors** - Evaluate contractor performance
8. **Analyze failures** - Extract recurring patterns
9. **Generate outputs** - Create reports, exports, visualizations

#### Step 3: Review Quality Report

During execution, watch for quality check results:

```
============================================================
DATA QUALITY CHECK
============================================================
Completeness: 92% (Pass)
Consistency: 88% (Pass)
Outlier Rate: 0.3% (Pass)
------------------------------------------------------------
Overall Score: 90/100 (PASS)
============================================================
```

If quality check fails (score < 85), the pipeline will:
- Display detailed quality issues
- Exit with error code 1
- Not generate outputs

#### Step 4: Examine Outputs

After successful completion:

```
============================================================
PIPELINE EXECUTION COMPLETE
============================================================

Analysis Summary:
  Total work orders: 1,523
  Consensus outliers: 23 equipment
  Seasonal patterns: 4
  Vendors analyzed: 15
  Failure patterns: 12

Reports Generated:
  PDF:   output/reports/work_order_analysis.pdf
  Excel: output/reports/work_order_analysis.xlsx

Data Exports: 8 files (4 CSV + 4 JSON)
  Location: output/exports/

Visualizations: 4 charts + 1 dashboard
  Dashboard: output/visualizations/dashboard.html

Execution Time: 1m 23s
============================================================
```

#### Step 5: Share with Stakeholders

- **For executives:** Share PDF report (executive summary)
- **For analysts:** Share Excel workbook (detailed exploration)
- **For presentations:** Share dashboard.html (interactive visuals)
- **For integration:** Share CSV exports (raw data files)

## Understanding Outputs

### PDF Report

**Location:** `output/reports/work_order_analysis.pdf`

**Sections:**

1. **Executive Summary**
   - Total work orders processed
   - Consensus outliers identified
   - Cost reduction opportunities

2. **Equipment Analysis**
   - Top 20 high-maintenance equipment ranked by priority
   - Statistical thresholds for frequency and cost
   - Category-specific comparisons

3. **Seasonal Trends**
   - Monthly cost patterns with line charts
   - Quarterly variance analysis
   - Budget planning insights

4. **Vendor Performance**
   - Contractor cost comparison
   - Efficiency and quality metrics
   - Recommendations for vendor review

5. **Failure Patterns**
   - Top 15 recurring failure descriptions
   - Impact scores (frequency × cost × equipment affected)
   - Root cause categories

6. **Recommendations**
   - Prioritized action items by category
   - Expected cost savings
   - Implementation timelines

**Interpretation:**
- Priority scores combine frequency, cost, and statistical outlier status
- Higher priority = greater cost reduction opportunity
- Seasonal trends guide budget allocation across quarters
- Vendor recommendations based on 75th percentile thresholds

### Excel Workbook

**Location:** `output/reports/work_order_analysis.xlsx`

**Sheet 1: Summary**
- Key metrics and insights
- Data quality report
- Analysis thresholds

**Sheet 2: Equipment**
- All equipment ranked by priority score
- Columns: Equipment ID, Name, Category, Total WOs, Avg Cost, Priority Score, Outlier Flags
- Autofilter enabled for sorting/filtering
- Frozen header row

**Sheet 3: Seasonal**
- Monthly and quarterly cost aggregations
- Work order counts per period
- Variance calculations

**Sheet 4: Vendors**
- Contractor performance metrics
- Columns: Contractor, Total Cost, Work Orders, Avg Cost, Avg Duration, Repeat Rate, Recommendation
- Color coding for recommendations (green = good, red = review)

**Sheet 5: Failures**
- High-impact failure patterns
- Columns: Pattern, Frequency, Equipment Affected, Total Cost, Impact Score
- Sorted by impact score descending

**Sheet 6: Recommendations**
- Actionable items organized by category
- Priority levels (High/Medium/Low)
- Expected savings estimates

**Usage Tips:**
- Use autofilters to focus on specific categories
- Sort by Priority Score to see top opportunities
- Pivot tables can be created from Equipment sheet for custom analysis
- Export individual sheets to CSV for further processing

### CSV/JSON Exports

**Location:** `output/exports/`

**Files:**
- `equipment_rankings.csv/json` - Full equipment analysis dataset
- `seasonal_patterns.csv/json` - Time series cost data
- `vendor_metrics.csv/json` - Contractor performance data
- `failure_patterns.csv/json` - Pattern extraction results

**Schema:**

Equipment Rankings:
```json
{
  "equipment_id": "EQ-12345",
  "equipment_name": "Air Conditioner Unit 3",
  "category": "HVAC Repair",
  "total_work_orders": 23,
  "avg_cost": 1250.50,
  "priority_score": 0.87,
  "outlier_zscore": true,
  "outlier_iqr": true,
  "outlier_percentile": false
}
```

**Use Cases:**
- Import into BI tools (Tableau, Power BI)
- Integrate with CMMS/EAM systems
- Custom analysis in R, Python, or Excel
- API consumption for dashboards

### Charts and Dashboard

**Static Charts (PNG):**
- `equipment_ranking.png` - Horizontal bar chart of top 10 equipment by priority
- `seasonal_costs.png` - Line chart showing monthly cost trends
- `vendor_costs.png` - Grouped bar chart comparing vendor metrics
- `failure_patterns.png` - Bar chart of top 10 failure patterns

**Interactive Dashboard (HTML):**
- `dashboard.html` - Plotly-based dashboard with all 4 visualizations
- Features:
  - Hover tooltips with detailed metrics
  - Legend click to filter categories
  - Zoom and pan on charts
  - Downloadable as PNG from browser
  - No server required (opens in any web browser)

**Usage:**
- Open dashboard.html in Chrome, Firefox, Edge, or Safari
- Use for presentations and stakeholder meetings
- Export individual charts as images via browser menu

## Advanced Usage

### Batch Processing Multiple Files

Process multiple months or years of data:

```bash
# Process each file separately
python main.py analyze -i data/2024_Q1.csv -o output/Q1/ --all
python main.py analyze -i data/2024_Q2.csv -o output/Q2/ --all
python main.py analyze -i data/2024_Q3.csv -o output/Q3/ --all
python main.py analyze -i data/2024_Q4.csv -o output/Q4/ --all
```

Or create a batch script (Linux/macOS):

```bash
#!/bin/bash
for quarter in Q1 Q2 Q3 Q4; do
  echo "Processing $quarter..."
  python main.py analyze -i data/2024_$quarter.csv -o output/$quarter/ --all
done
```

### Programmatic API Usage

Use the pipeline as a Python library in your own scripts:

```python
from src.orchestrator import PipelineOrchestrator

# Initialize orchestrator
orchestrator = PipelineOrchestrator(
    input_file="data/work_orders.csv",
    output_dir="output/"
)

# Run analysis
results = orchestrator.run_full_analysis()

# Generate specific outputs
report_paths = orchestrator.generate_reports(results)
export_paths = orchestrator.export_data(results)
viz_paths = orchestrator.generate_visualizations(results)

# Access analysis results
print(f"Found {len(results['equipment_df'])} outlier equipment")
print(f"Quality score: {results['quality_report']['score']}")
```

See [API Reference](API.md) for complete documentation.

### Integration with Other Tools

**Excel/Power BI:**
1. Use CSV exports from `output/exports/`
2. Import into Power Query or Excel
3. Create custom visualizations and dashboards

**Tableau:**
1. Connect to CSV or JSON exports
2. Use equipment_rankings.csv as primary data source
3. Join with seasonal_patterns.csv for time-based analysis

**Python/R:**
1. Read JSON exports with pandas or jsonlite
2. Perform custom statistical analysis
3. Create specialized visualizations

## Troubleshooting

### Common Issues

#### Issue: "FileNotFoundError: Input file not found"

**Cause:** Invalid path to input file

**Solution:**
- Verify file exists: `ls data/work_orders.csv`
- Use absolute path: `python main.py analyze -i /full/path/to/file.csv`
- Check spelling and file extension

#### Issue: "ValueError: Unsupported file format"

**Cause:** File extension not .csv or .xlsx

**Solution:**
- Save file as CSV or Excel format
- Rename file to have correct extension

#### Issue: Data quality check fails (score < 85)

**Cause:** Too many missing values or inconsistent data

**Solution:**
1. Review quality report output for specific issues
2. Check for:
   - Missing required columns
   - Empty/null values in required fields
   - Invalid date formats
   - Non-numeric values in PO_AMOUNT column
3. Clean data and re-run analysis

#### Issue: Memory error with large datasets

**Cause:** Insufficient RAM for dataset size

**Solution:**
- Split data into smaller chunks (by year, quarter, or month)
- Process each chunk separately
- Increase system memory if possible
- Use 64-bit Python (supports larger datasets)

#### Issue: Charts not displaying correctly

**Cause:** Missing matplotlib backend or display issues

**Solution:**
- Charts are saved as files, no display required
- Open PNG files with image viewer
- Open dashboard.html in web browser
- Verify matplotlib installed: `pip list | grep matplotlib`

#### Issue: Dashboard shows "Loading..." indefinitely

**Cause:** JavaScript disabled or network issue loading Plotly CDN

**Solution:**
- Enable JavaScript in browser
- Check internet connection (Plotly loads from CDN)
- Try different browser (Chrome, Firefox, Edge)
- Disable browser extensions that might block CDN

### Getting Help

If you encounter issues not covered here:

1. Check logs for detailed error messages
2. Verify Python version: `python --version` (must be 3.9+)
3. Verify dependencies: `pip list`
4. Review [Architecture documentation](ARCHITECTURE.md) for system design
5. Open an issue on GitHub with:
   - Error message
   - Python version
   - Operating system
   - Input file characteristics (size, format, column names)
   - Full command used
