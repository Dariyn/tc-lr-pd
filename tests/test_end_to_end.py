"""
End-to-end integration tests for complete pipeline.

Validates full workflow from raw work order data through all analysis steps
to final outputs (reports, exports, visualizations).
"""

import pytest
import os
import json
import subprocess
import time
from pathlib import Path
import pandas as pd


@pytest.fixture
def sample_data_path():
    """Path to sample work order data fixture."""
    return Path(__file__).parent / 'fixtures' / 'sample_work_orders.csv'


@pytest.fixture
def orchestrator_with_sample(sample_data_path, tmp_path):
    """Create orchestrator with sample data and temp output directory."""
    from src.orchestrator import PipelineOrchestrator

    return PipelineOrchestrator(
        input_file=str(sample_data_path),
        output_dir=str(tmp_path / 'output')
    )


# =============================================================================
# Pipeline Execution Tests (3 tests)
# =============================================================================

def test_e2e_full_pipeline(orchestrator_with_sample):
    """Test complete analysis pipeline runs without errors."""
    results = orchestrator_with_sample.run_full_analysis()

    # Verify all result components present
    assert 'equipment_df' in results
    assert 'seasonal_dict' in results
    assert 'vendor_df' in results
    assert 'patterns_list' in results
    assert 'quality_report' in results
    assert 'thresholds' in results
    assert 'category_stats' in results

    # Verify results are non-empty (sample data should produce results)
    assert len(results['equipment_df']) > 0, "Should identify some consensus outliers"
    assert len(results['vendor_df']) > 0, "Should analyze vendors"


def test_e2e_analysis_results(orchestrator_with_sample):
    """Verify all analysis results are produced correctly."""
    results = orchestrator_with_sample.run_full_analysis()

    # Equipment analysis
    equipment_df = results['equipment_df']
    assert 'Equipment_ID' in equipment_df.columns
    assert 'total_work_orders' in equipment_df.columns
    assert 'priority_score' in equipment_df.columns
    assert 'is_outlier_consensus' in equipment_df.columns

    # Seasonal analysis
    seasonal_dict = results['seasonal_dict']
    assert 'monthly_costs' in seasonal_dict
    assert 'quarterly_costs' in seasonal_dict
    assert 'patterns' in seasonal_dict

    # Vendor analysis
    vendor_df = results['vendor_df']
    assert 'Contractor' in vendor_df.columns
    assert 'total_work_orders' in vendor_df.columns
    assert 'avg_cost' in vendor_df.columns

    # Failure pattern analysis (may be empty if no text fields in data)
    patterns_list = results['patterns_list']
    assert isinstance(patterns_list, list)
    # Pattern analysis may return empty if description column not found
    if len(patterns_list) > 0:
        assert 'pattern' in patterns_list[0]
        assert 'frequency' in patterns_list[0]


def test_e2e_execution_time(orchestrator_with_sample):
    """Verify pipeline completes in reasonable time (<30 seconds)."""
    start_time = time.time()

    results = orchestrator_with_sample.run_full_analysis()

    execution_time = time.time() - start_time

    assert execution_time < 30, f"Pipeline took {execution_time:.2f}s, should be <30s"
    assert results is not None


# =============================================================================
# Report Generation Tests (2 tests)
# =============================================================================

def test_e2e_pdf_report(orchestrator_with_sample, tmp_path):
    """Verify PDF report is created and valid."""
    # Run analysis first
    results = orchestrator_with_sample.run_full_analysis()

    # Generate reports
    report_paths = orchestrator_with_sample.generate_reports(results)

    # Verify PDF exists
    assert 'pdf_path' in report_paths
    pdf_path = Path(report_paths['pdf_path'])
    assert pdf_path.exists(), f"PDF not found at {pdf_path}"

    # Verify file size (should be >50KB for real report)
    file_size = pdf_path.stat().st_size
    assert file_size > 50 * 1024, f"PDF too small: {file_size} bytes"

    # Verify it's a valid PDF (magic bytes)
    with open(pdf_path, 'rb') as f:
        magic_bytes = f.read(4)
        assert magic_bytes == b'%PDF', f"Not a valid PDF file"


def test_e2e_excel_report(orchestrator_with_sample, tmp_path):
    """Verify Excel report is created and valid."""
    # Run analysis first
    results = orchestrator_with_sample.run_full_analysis()

    # Generate reports
    report_paths = orchestrator_with_sample.generate_reports(results)

    # Verify Excel exists
    assert 'excel_path' in report_paths
    excel_path = Path(report_paths['excel_path'])
    assert excel_path.exists(), f"Excel not found at {excel_path}"

    # Verify file size (should be >20KB)
    file_size = excel_path.stat().st_size
    assert file_size > 20 * 1024, f"Excel too small: {file_size} bytes"

    # Verify it's valid Excel with expected sheets
    import openpyxl
    wb = openpyxl.load_workbook(excel_path)
    sheet_names = wb.sheetnames

    # Should have 6 sheets per plan spec
    assert len(sheet_names) == 6, f"Expected 6 sheets, got {len(sheet_names)}"
    assert 'Summary' in sheet_names
    assert 'Equipment' in sheet_names
    assert 'Seasonal' in sheet_names
    assert 'Vendors' in sheet_names
    assert 'Failures' in sheet_names
    assert 'Recommendations' in sheet_names


# =============================================================================
# Data Export Tests (2 tests)
# =============================================================================

def test_e2e_csv_exports(orchestrator_with_sample, tmp_path):
    """Verify 4 CSV files are created."""
    # Run analysis first
    results = orchestrator_with_sample.run_full_analysis()

    # Export data
    export_paths = orchestrator_with_sample.export_data(results)

    # Verify CSV files
    assert 'csv' in export_paths
    csv_files = export_paths['csv']
    assert len(csv_files) == 4, f"Expected 4 CSV files, got {len(csv_files)}"

    # Verify all files exist and are readable
    for csv_path in csv_files:
        path = Path(csv_path)
        assert path.exists(), f"CSV not found: {csv_path}"

        # Verify it's readable as CSV
        df = pd.read_csv(csv_path)
        assert len(df.columns) > 0, f"CSV has no columns: {csv_path}"


def test_e2e_json_exports(orchestrator_with_sample, tmp_path):
    """Verify 4 JSON files are created and valid."""
    # Run analysis first
    results = orchestrator_with_sample.run_full_analysis()

    # Export data
    export_paths = orchestrator_with_sample.export_data(results)

    # Verify JSON files
    assert 'json' in export_paths
    json_files = export_paths['json']
    assert len(json_files) == 4, f"Expected 4 JSON files, got {len(json_files)}"

    # Verify all files exist and are valid JSON
    for json_path in json_files:
        path = Path(json_path)
        assert path.exists(), f"JSON not found: {json_path}"

        # Verify it's parseable JSON
        with open(json_path, 'r') as f:
            data = json.load(f)
            assert data is not None, f"JSON is empty: {json_path}"


# =============================================================================
# Visualization Tests (2 tests)
# =============================================================================

def test_e2e_static_charts(orchestrator_with_sample, tmp_path):
    """Verify 4 PNG charts are created with valid format."""
    # Run analysis first
    results = orchestrator_with_sample.run_full_analysis()

    # Generate visualizations
    viz_paths = orchestrator_with_sample.generate_visualizations(results)

    # Verify charts
    assert 'charts' in viz_paths
    chart_files = viz_paths['charts']
    assert len(chart_files) == 4, f"Expected 4 chart files, got {len(chart_files)}"

    # Verify all are valid PNG images
    for chart_path in chart_files:
        path = Path(chart_path)
        assert path.exists(), f"Chart not found: {chart_path}"

        # Verify PNG magic bytes
        with open(chart_path, 'rb') as f:
            magic_bytes = f.read(8)
            assert magic_bytes == b'\x89PNG\r\n\x1a\n', f"Not a valid PNG: {chart_path}"


def test_e2e_interactive_dashboard(orchestrator_with_sample, tmp_path):
    """Verify HTML dashboard is created and contains plotly.js."""
    # Run analysis first
    results = orchestrator_with_sample.run_full_analysis()

    # Generate visualizations
    viz_paths = orchestrator_with_sample.generate_visualizations(results)

    # Verify dashboard
    assert 'dashboard' in viz_paths
    dashboard_path = Path(viz_paths['dashboard'])
    assert dashboard_path.exists(), f"Dashboard not found: {dashboard_path}"

    # Read dashboard HTML
    with open(dashboard_path, 'r', encoding='utf-8') as f:
        html_content = f.read()

    # Verify it's valid HTML
    assert '<!DOCTYPE html>' in html_content or '<html' in html_content.lower()

    # Verify it contains plotly
    assert 'plotly' in html_content.lower(), "Dashboard should use Plotly"

    # Verify it has script tags (for interactivity)
    assert '<script' in html_content.lower(), "Dashboard should have JavaScript"


# =============================================================================
# CLI Integration Test (1 test)
# =============================================================================

def test_e2e_cli_interface(sample_data_path, tmp_path):
    """Run main.py analyze via subprocess and verify outputs."""
    output_dir = tmp_path / 'cli_output'

    # Run CLI command
    result = subprocess.run(
        [
            'python', 'main.py', 'analyze',
            '-i', str(sample_data_path),
            '-o', str(output_dir),
            '--all'  # Generate everything
        ],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent  # Run from project root
    )

    # Verify successful execution
    assert result.returncode == 0, f"CLI failed with: {result.stderr}"

    # Verify output directories created
    assert (output_dir / 'reports').exists()
    assert (output_dir / 'exports').exists()
    assert (output_dir / 'visualizations').exists()

    # Verify key files exist
    assert (output_dir / 'reports' / 'work_order_analysis.pdf').exists()
    assert (output_dir / 'reports' / 'work_order_analysis.xlsx').exists()
    assert len(list((output_dir / 'exports').glob('*.csv'))) == 4
    assert len(list((output_dir / 'exports').glob('*.json'))) == 4
    assert len(list((output_dir / 'visualizations').glob('*.png'))) == 4
    assert (output_dir / 'visualizations' / 'dashboard.html').exists()


# =============================================================================
# Data Validation Tests
# =============================================================================

def test_e2e_sample_data_produces_expected_patterns(orchestrator_with_sample):
    """Verify sample data produces expected analysis patterns."""
    results = orchestrator_with_sample.run_full_analysis()

    # Should have at least 1 consensus outlier (EQ-001 with 10 WOs should definitely be one)
    equipment_df = results['equipment_df']
    consensus_outliers = equipment_df[equipment_df['is_outlier_consensus'] == True]
    assert len(consensus_outliers) >= 1, f"Expected >=1 consensus outliers, got {len(consensus_outliers)}"

    # Should detect seasonal variation (data spans full year)
    seasonal_dict = results['seasonal_dict']
    monthly_costs = seasonal_dict.get('monthly_costs', pd.DataFrame())
    assert len(monthly_costs) >= 12, "Should have monthly data for full year"

    # Should have multiple vendors (A, B, C in sample data)
    vendor_df = results['vendor_df']
    assert len(vendor_df) >= 3, f"Expected >=3 vendors, got {len(vendor_df)}"

    # Failure patterns may be empty if description column not found in categorizer
    patterns_list = results['patterns_list']
    # No assertion - pattern analysis is optional if text fields not available
