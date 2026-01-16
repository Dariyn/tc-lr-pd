# GEMINI.md

This file provides context for the Gemini AI agent interacting with this project.

## Project Overview

**Project Name:** Work Order Cost Reduction Analysis Pipeline
**Type:** Python Data Pipeline (CLI)
**Purpose:** Analyzes adhoc work order data (Jan 2024 - May 2025) to identify cost reduction opportunities through pattern analysis and equipment performance comparisons.
**Core Value:** Provides actionable insights for budget planning by identifying equipment with abnormal repair frequencies and cost patterns.

## Architecture

The project follows a modular pipeline architecture located in `src/`:

1.  **Load (`src/pipeline/data_loader.py`):** Ingests CSV/Excel data, validates schema, handles encoding/BOM.
2.  **Clean (`src/pipeline/data_cleaner.py`):** Standardizes data, fills missing values, flags outliers (99th percentile), handles dates.
3.  **Categorize (`src/pipeline/categorizer.py`):** Normalizes equipment categories based on service type and FM type.
4.  **Validate (`src/pipeline/quality_reporter.py`):** Generates a comprehensive quality report with scores for completeness, consistency, and outliers.
5.  **Orchestrate (`src/pipeline/pipeline.py`):** Ties all stages together, logging progress and handling errors.

### Directory Structure

-   `src/`: Source code.
    -   `pipeline/`: Core data processing logic.
    -   `analysis/`: Analytical modules (Phase 2).
    -   `reporting/`: Reporting modules.
-   `tests/`: Unit tests using `pytest`.
-   `input/`: Directory for input data files (e.g., `adhoc_wo_...csv`).
-   `.planning/`: Project management documentation (Roadmap, Phases).

## Building and Running

### Prerequisites
-   Python 3.8+
-   Dependencies in `requirements.txt`

### Setup
```bash
pip install -r requirements.txt
```

### Execution
Run the full pipeline:
```bash
python -m src.pipeline.pipeline
```
This processes the default input file (`input/adhoc_wo_20240101_20250531.xlsx - in.csv`) and outputs a quality report to the console.

### Testing
Run unit tests:
```bash
pytest tests/
```

## Development Conventions

-   **Language:** Python 3.8+
-   **Style:** Adhere to PEP 8.
-   **Type Hinting:** Strictly used for all function signatures (`def func(arg: type) -> type:`).
-   **Logging:** Use the standard `logging` library. All major steps should be logged.
-   **Docstrings:** Detailed docstrings for modules and functions (Google style preferred).
-   **Testing:** `pytest` is the framework. Tests mirror the source structure in the `tests/` directory.
-   **Error Handling:** Custom exception handling in the pipeline to ensure graceful failures and informative logs.

## Roadmap Status

**Current State:** Phase 1 (Data Pipeline Foundation) is **COMPLETE**.
**Next Phase:** Phase 2 (Equipment Category Analysis).

**Phase 1 Capabilities:**
-   Schema validation & data loading.
-   Data cleaning & standardization.
-   Category normalization.
-   Quality reporting (Completeness, Consistency, Outliers).

**Phase 2 Goals:**
-   Identify equipment with high repair frequencies.
-   Compare equipment performance within categories.
-   Generate ranked lists for cost reduction.

## Key Files

-   `src/pipeline/pipeline.py`: Main entry point and orchestrator.
-   `src/pipeline/quality_reporter.py`: Logic for calculating data quality scores.
-   `README.md`: User-facing documentation.
-   `.planning/PROJECT.md`: High-level project goals and constraints.
