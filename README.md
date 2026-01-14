# Work Order Cost Reduction Analysis Pipeline

Analyzes adhoc work order data to identify cost reduction opportunities through pattern analysis and equipment performance comparisons.

## Overview

This pipeline processes work order data (Excel/CSV) through a series of stages to produce quality-validated, analysis-ready data. It identifies equipment with abnormal repair frequencies, validates data quality, and provides comprehensive metrics for cost reduction analysis.

## Phase 1 Status: Data Pipeline Foundation Complete

The foundation is now complete and provides:
- Data loading with schema validation
- Data cleaning and standardization
- Category normalization
- Quality reporting and validation

Ready for Phase 2: Equipment Category Analysis

## Setup

### Requirements
- Python 3.8+
- Dependencies listed in requirements.txt

### Installation

```bash
pip install -r requirements.txt
```

## Usage

### Run Full Pipeline

```bash
python -m src.pipeline.pipeline
```

This runs the complete pipeline on the default input file and displays a quality report.

### Quality Report Output

The pipeline generates a comprehensive quality report showing:
- **Overall Quality Score** (0-100) with pass/fail status
- **Component Scores**: Completeness, Consistency, Outlier Rate
- **Field Completeness**: Percentage of non-null values for critical fields
- **Data Consistency**: Category consistency, date order validation, cost validation
- **Outliers**: Cost and duration outliers flagged for review
- **Coverage**: Date range, equipment count, category count, property count
- **Recommendations**: Actionable suggestions for data quality improvements

Example output:
```
============================================================
DATA QUALITY REPORT
============================================================

Overall Quality Score: 84.13/100 [FAILED]

Component Scores:
  Completeness:  92.94/100 (40% weight)
  Consistency:   67.59/100 (40% weight)
  Outlier Rate:  99.58/100 (20% weight)

Key Metrics:
  Total Records: 19,291

  Field Completeness:
    [OK] Equipment_ID: 100.0%
    [OK] EquipmentName: 100.0%
    [OK] equipment_category: 100.0%
    [OK] Create_Date: 100.0%
    [LOW] Complete_Date: 57.7%
    [OK] PO_AMOUNT: 100.0%

  Data Consistency:
    Category Consistency: 52.0%
    Valid Date Order: 50.8%
    Valid Costs (>=0): 100.0%

  Outliers Detected:
    Cost Outliers: 106 (0.55%)
    Duration Outliers: 57 (0.30%)

  Data Coverage:
    Date Range: 2026-01-14 to 2026-01-14
    Days Covered: 0
    Unique Equipment: 60
    Unique Categories: 30
    Unique Properties: 205

Recommendations:
  1. Address data completeness issues: Complete_Date only 57.7% complete (8168 nulls)
  2. Review 49.2% of records with Complete_Date before Create_Date

============================================================
```

## Project Structure

```
src/
├── pipeline/
│   ├── data_loader.py       # Loads and validates CSV/Excel data
│   ├── data_cleaner.py      # Cleans and standardizes data
│   ├── categorizer.py       # Normalizes equipment categories
│   ├── quality_reporter.py  # Generates quality metrics
│   └── pipeline.py          # Orchestrates full pipeline
├── __init__.py
tests/
├── test_data_cleaner.py
├── test_categorizer.py
└── __init__.py
input/
└── adhoc_wo_20240101_20250531.xlsx - in.csv
requirements.txt
README.md
```

### Module Descriptions

#### data_loader.py
Loads work order data from CSV or Excel files with:
- Schema validation (ensures required fields are present)
- Date parsing (Create_Date, Complete_Date, Close_Date)
- Numeric conversion (PO_AMOUNT)
- UTF-8-sig encoding support for BOM characters
- Comprehensive logging for data quality issues

#### data_cleaner.py
Cleans and standardizes data with:
- Equipment ID handling (generates synthetic IDs from names when missing)
- Cost data cleaning (fills missing PO_AMOUNT with 0, flags outliers)
- Date data cleaning (uses Close_Date as fallback, calculates duration)
- Outlier detection (99th percentile threshold for cost and duration)
- Drops records with missing critical data (no equipment identifier or Create_Date)

#### categorizer.py
Normalizes equipment categories with:
- Priority-based category assignment (service_type_lv2 > FM_Type > Uncategorized)
- Equipment primary category assignment based on mode frequency
- Consistency scoring (flags equipment with <80% consistency as potentially miscategorized)
- Category hierarchy generation for analysis-ready groupings

#### quality_reporter.py
Generates comprehensive quality metrics:
- **Completeness metrics**: Percentage of non-null values for critical fields
- **Consistency metrics**: Category consistency, date order validation, cost validation
- **Outlier metrics**: Cost and duration outliers with thresholds
- **Coverage metrics**: Date range, equipment count, category count, property count
- **Overall quality score**: Weighted average (completeness 40%, consistency 40%, outlier rate 20%)
- **Recommendations**: Actionable suggestions based on quality analysis

#### pipeline.py
Orchestrates the complete pipeline:
- Runs load → clean → categorize → validate workflow
- Comprehensive error handling at each stage
- Progress logging for observability
- Optional CSV output for processed data
- CLI entry point with exit codes (0 = success, 1 = quality concerns)

## Data Quality Metrics Explained

### Completeness (40% weight)
Measures the percentage of non-null values for critical fields:
- Equipment_ID, EquipmentName, equipment_category
- Create_Date, Complete_Date, PO_AMOUNT

Fields with <95% completeness are flagged as quality concerns.

### Consistency (40% weight)
Measures data integrity:
- **Category Consistency**: Average consistency score for equipment categorization (0-100%)
- **Date Consistency**: Percentage of records with Complete_Date >= Create_Date
- **Cost Consistency**: Percentage of records with PO_AMOUNT >= 0

### Outlier Rate (20% weight)
Inverse of outlier detection rate:
- **Cost Outliers**: Records with PO_AMOUNT > 99th percentile
- **Duration Outliers**: Records with duration_hours > 99th percentile

Lower outlier rates indicate better data quality (outliers are flagged, not removed).

### Overall Quality Score
Weighted average of component scores:
```
Score = (Completeness * 0.40) + (Consistency * 0.40) + (Outlier Rate * 0.20)
```

**Pass threshold**: 85/100

Quality scores help validate data readiness for downstream analysis and identify areas needing attention.

## Next Steps

Phase 2 will add equipment category analysis to:
- Identify equipment with abnormally high adhoc repair frequencies
- Compare equipment performance within categories
- Generate ranked lists of equipment for cost reduction opportunities

## Input Data Format

Expected CSV/Excel columns:
- **Equipment_ID**: Unique equipment identifier (can be missing if EquipmentName provided)
- **EquipmentName**: Equipment name (used to generate synthetic ID if Equipment_ID missing)
- **equipment_category**: Primary category (derived from service_type_lv2 or FM_Type)
- **Create_Date**: Work order creation date (required)
- **Complete_Date**: Work order completion date (optional, Close_Date used as fallback)
- **PO_AMOUNT**: Purchase order amount (optional, filled with 0 if missing)
- **service_type_lv2**: Service type level 2 (used for category normalization)
- **FM_Type**: Facility management type (fallback for category normalization)
- **Property**: Property identifier (for coverage analysis)

## Testing

Run tests with pytest:
```bash
pytest tests/
```

Current test coverage:
- data_cleaner.py: 9 tests
- categorizer.py: 9 tests
