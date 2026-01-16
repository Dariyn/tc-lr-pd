"""
Tests for the pipeline orchestrator module.

Covers:
- Orchestrator initialization
- Output directory creation
- Full analysis execution
- Results structure validation
- Report generation
- Data export (CSV and JSON)
- Visualization generation
- Edge cases: empty data, invalid inputs, missing files
- Integration with all 16 modules
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch, MagicMock
import tempfile
import shutil
import os

from src.orchestrator.pipeline_orchestrator import PipelineOrchestrator


# Test Fixtures

@pytest.fixture
def sample_csv_file(tmp_path):
    """
    Create a sample CSV file with work order data for testing.

    Returns path to the temporary CSV file.
    """
    base_date = datetime(2024, 1, 1)

    data = {
        'id_': [f'ID-{i:05d}' for i in range(1, 51)],
        'wo_no': [f'WO-{i:04d}' for i in range(1, 51)],
        'Equipment_ID': [f'EQ-{i % 10:03d}' for i in range(1, 51)],
        'EquipmentName': [f'Equipment {i % 10}' for i in range(1, 51)],
        'Property_category': ['Commercial'] * 30 + ['Residential'] * 20,
        'Work_Order_Type': ['Adhoc'] * 30 + ['Preventive'] * 20,
        'service_type_lv2': ['Repair'] * 30 + ['Maintenance'] * 20,
        'service_type_lv3': ['HVAC Repair'] * 25 + ['Plumbing Repair'] * 15 + ['Electrical Repair'] * 10,
        'FM_Type': ['Corrective'] * 30 + ['Preventive'] * 20,
        'Create_Date': [base_date + timedelta(days=i*3) for i in range(50)],
        'Complete_Date': [base_date + timedelta(days=i*3 + 2) for i in range(50)],
        'PO_AMOUNT': np.random.uniform(100, 5000, 50),
        'Contractor': ['Vendor A'] * 15 + ['Vendor B'] * 15 + ['Vendor C'] * 10 + ['Vendor D'] * 10,
        'Problem': ['leak issue'] * 10 + ['broken motor'] * 10 + ['electrical fault'] * 10 +
                   ['noise problem'] * 10 + ['sensor malfunction'] * 10,
        'Cause': ['worn seal'] * 10 + ['motor failure'] * 10 + ['wiring short'] * 10 +
                 ['bearing wear'] * 10 + ['sensor defect'] * 10,
        'Remedy': ['replaced seal'] * 10 + ['replaced motor'] * 10 + ['repaired wiring'] * 10 +
                  ['lubricated bearing'] * 10 + ['replaced sensor'] * 10,
    }

    df = pd.DataFrame(data)
    csv_path = tmp_path / 'test_work_orders.csv'
    df.to_csv(csv_path, index=False)

    return csv_path


@pytest.fixture
def empty_csv_file(tmp_path):
    """Create empty CSV with headers but no data."""
    df = pd.DataFrame(columns=[
        'id_', 'wo_no', 'Equipment_ID', 'EquipmentName', 'Property_category',
        'Work_Order_Type', 'service_type_lv2', 'service_type_lv3', 'FM_Type', 'Create_Date', 'Complete_Date',
        'PO_AMOUNT', 'Contractor', 'Problem', 'Cause', 'Remedy'
    ])

    csv_path = tmp_path / 'empty_work_orders.csv'
    df.to_csv(csv_path, index=False)

    return csv_path


@pytest.fixture
def output_dir(tmp_path):
    """Create temporary output directory."""
    output = tmp_path / 'output'
    output.mkdir()
    return output


# Orchestrator Initialization Tests (2 tests)

def test_orchestrator_init(sample_csv_file, output_dir):
    """Test orchestrator initialization with input file and output directory."""
    orchestrator = PipelineOrchestrator(
        input_file=str(sample_csv_file),
        output_dir=str(output_dir)
    )

    assert orchestrator.input_file == str(sample_csv_file)
    assert orchestrator.output_dir == Path(output_dir)


def test_orchestrator_output_dir_creation(sample_csv_file, tmp_path):
    """Test that orchestrator creates output directory structure."""
    output_dir = tmp_path / 'new_output'

    # Directory should not exist yet
    assert not output_dir.exists()

    orchestrator = PipelineOrchestrator(
        input_file=str(sample_csv_file),
        output_dir=str(output_dir)
    )

    # Verify all directories were created
    assert output_dir.exists()
    assert (output_dir / 'reports').exists()
    assert (output_dir / 'exports').exists()
    assert (output_dir / 'visualizations').exists()


# Analysis Execution Tests (4 tests)

def test_run_full_analysis(sample_csv_file, output_dir):
    """Test that full analysis executes all 5 stages and returns results."""
    orchestrator = PipelineOrchestrator(
        input_file=str(sample_csv_file),
        output_dir=str(output_dir)
    )

    results = orchestrator.run_full_analysis()

    # Verify results is a dictionary
    assert isinstance(results, dict)

    # Verify all expected keys are present
    expected_keys = [
        'equipment_df', 'seasonal_dict', 'vendor_df', 'patterns_list',
        'quality_report', 'thresholds', 'category_stats'
    ]
    for key in expected_keys:
        assert key in results, f"Missing key: {key}"


def test_run_full_analysis_results_structure(sample_csv_file, output_dir):
    """Test that analysis results have correct types and structure."""
    orchestrator = PipelineOrchestrator(
        input_file=str(sample_csv_file),
        output_dir=str(output_dir)
    )

    results = orchestrator.run_full_analysis()

    # Verify types
    assert isinstance(results['equipment_df'], pd.DataFrame), "equipment_df should be DataFrame"
    assert isinstance(results['seasonal_dict'], dict), "seasonal_dict should be dict"
    assert isinstance(results['vendor_df'], pd.DataFrame), "vendor_df should be DataFrame"
    assert isinstance(results['patterns_list'], list), "patterns_list should be list"
    assert isinstance(results['quality_report'], dict), "quality_report should be dict"
    assert isinstance(results['thresholds'], dict), "thresholds should be dict"
    assert isinstance(results['category_stats'], pd.DataFrame), "category_stats should be DataFrame"

    # Verify quality report has expected structure
    assert 'total_records' in results['quality_report']
    assert 'overall_quality_score' in results['quality_report']
    assert 'quality_passed' in results['quality_report']


def test_run_full_analysis_empty_data(empty_csv_file, output_dir):
    """Test that analysis handles empty input data gracefully."""
    orchestrator = PipelineOrchestrator(
        input_file=str(empty_csv_file),
        output_dir=str(output_dir)
    )

    # Should not raise exception, but return empty results
    results = orchestrator.run_full_analysis()

    # Verify results structure is intact
    assert isinstance(results, dict)
    assert 'equipment_df' in results
    assert 'seasonal_dict' in results

    # Empty data should result in empty DataFrames/lists
    assert len(results['equipment_df']) == 0
    assert len(results['vendor_df']) == 0
    assert len(results['patterns_list']) == 0


def test_run_full_analysis_invalid_input(output_dir):
    """Test that analysis raises error for invalid input file path."""
    orchestrator = PipelineOrchestrator(
        input_file='nonexistent_file.csv',
        output_dir=str(output_dir)
    )

    # Should raise FileNotFoundError
    with pytest.raises(FileNotFoundError):
        orchestrator.run_full_analysis()


# Report Generation Tests (2 tests)

def test_generate_reports(sample_csv_file, output_dir):
    """Test that PDF and Excel reports are generated successfully."""
    orchestrator = PipelineOrchestrator(
        input_file=str(sample_csv_file),
        output_dir=str(output_dir)
    )

    # Run analysis first
    results = orchestrator.run_full_analysis()

    # Generate reports
    report_paths = orchestrator.generate_reports(results)

    # Verify return structure
    assert isinstance(report_paths, dict)
    assert 'pdf_path' in report_paths
    assert 'excel_path' in report_paths

    # Verify files were created
    pdf_path = Path(report_paths['pdf_path'])
    excel_path = Path(report_paths['excel_path'])

    assert pdf_path.exists(), f"PDF not created at {pdf_path}"
    assert excel_path.exists(), f"Excel not created at {excel_path}"


def test_generate_reports_file_validity(sample_csv_file, output_dir):
    """Test that generated report files are valid (size > 0, correct format)."""
    orchestrator = PipelineOrchestrator(
        input_file=str(sample_csv_file),
        output_dir=str(output_dir)
    )

    results = orchestrator.run_full_analysis()
    report_paths = orchestrator.generate_reports(results)

    pdf_path = Path(report_paths['pdf_path'])
    excel_path = Path(report_paths['excel_path'])

    # Verify file sizes are > 0
    assert pdf_path.stat().st_size > 0, "PDF file is empty"
    assert excel_path.stat().st_size > 0, "Excel file is empty"

    # Verify file extensions
    assert pdf_path.suffix == '.pdf', "PDF has wrong extension"
    assert excel_path.suffix == '.xlsx', "Excel has wrong extension"

    # Verify files are in correct directory
    assert pdf_path.parent == output_dir / 'reports'
    assert excel_path.parent == output_dir / 'reports'


# Export Generation Tests (2 tests)

def test_export_data(sample_csv_file, output_dir):
    """Test that CSV and JSON files are created for all 4 analysis types."""
    orchestrator = PipelineOrchestrator(
        input_file=str(sample_csv_file),
        output_dir=str(output_dir)
    )

    results = orchestrator.run_full_analysis()
    export_paths = orchestrator.export_data(results)

    # Verify return structure
    assert isinstance(export_paths, dict)
    assert 'csv' in export_paths
    assert 'json' in export_paths

    # Verify we have lists of paths
    assert isinstance(export_paths['csv'], list)
    assert isinstance(export_paths['json'], list)

    # Verify all files exist
    for csv_path in export_paths['csv']:
        assert Path(csv_path).exists(), f"CSV not created: {csv_path}"

    for json_path in export_paths['json']:
        assert Path(json_path).exists(), f"JSON not created: {json_path}"


def test_export_data_file_counts(sample_csv_file, output_dir):
    """Test that correct number of files are exported (8 total: 4 CSV + 4 JSON)."""
    orchestrator = PipelineOrchestrator(
        input_file=str(sample_csv_file),
        output_dir=str(output_dir)
    )

    results = orchestrator.run_full_analysis()
    export_paths = orchestrator.export_data(results)

    # Should have 4 CSV files
    assert len(export_paths['csv']) == 4, f"Expected 4 CSV files, got {len(export_paths['csv'])}"

    # Should have 4 JSON files
    assert len(export_paths['json']) == 4, f"Expected 4 JSON files, got {len(export_paths['json'])}"

    # Verify file names match expected patterns
    csv_names = [Path(p).name for p in export_paths['csv']]
    json_names = [Path(p).name for p in export_paths['json']]

    expected_base_names = [
        'equipment_rankings',
        'seasonal_patterns',
        'vendor_metrics',
        'failure_patterns'
    ]

    for base_name in expected_base_names:
        assert f"{base_name}.csv" in csv_names, f"Missing {base_name}.csv"
        assert f"{base_name}.json" in json_names, f"Missing {base_name}.json"

    # Verify all files are in exports directory
    for csv_path in export_paths['csv']:
        assert Path(csv_path).parent == output_dir / 'exports'


# Visualization Generation Tests (2 tests)

def test_generate_visualizations(sample_csv_file, output_dir):
    """Test that charts (PNG) and dashboard (HTML) are created."""
    orchestrator = PipelineOrchestrator(
        input_file=str(sample_csv_file),
        output_dir=str(output_dir)
    )

    results = orchestrator.run_full_analysis()
    viz_paths = orchestrator.generate_visualizations(results)

    # Verify return structure
    assert isinstance(viz_paths, dict)
    assert 'charts' in viz_paths
    assert 'dashboard' in viz_paths

    # Verify charts is a list
    assert isinstance(viz_paths['charts'], list)

    # Verify dashboard is a string path
    assert isinstance(viz_paths['dashboard'], str)

    # Verify all chart files exist
    for chart_path in viz_paths['charts']:
        assert Path(chart_path).exists(), f"Chart not created: {chart_path}"

    # Verify dashboard exists
    dashboard_path = Path(viz_paths['dashboard'])
    assert dashboard_path.exists(), f"Dashboard not created: {dashboard_path}"


def test_generate_visualizations_file_validity(sample_csv_file, output_dir):
    """Test that visualization files are valid formats and in correct location."""
    orchestrator = PipelineOrchestrator(
        input_file=str(sample_csv_file),
        output_dir=str(output_dir)
    )

    results = orchestrator.run_full_analysis()
    viz_paths = orchestrator.generate_visualizations(results)

    # Verify we have 4 chart files
    assert len(viz_paths['charts']) == 4, f"Expected 4 charts, got {len(viz_paths['charts'])}"

    # Verify chart file formats and sizes
    for chart_path in viz_paths['charts']:
        chart_file = Path(chart_path)
        assert chart_file.suffix == '.png', f"Chart should be PNG: {chart_path}"
        assert chart_file.stat().st_size > 0, f"Chart file is empty: {chart_path}"
        assert chart_file.parent == output_dir / 'visualizations'

    # Verify dashboard format and size
    dashboard_path = Path(viz_paths['dashboard'])
    assert dashboard_path.suffix == '.html', "Dashboard should be HTML"
    assert dashboard_path.stat().st_size > 0, "Dashboard file is empty"
    assert dashboard_path.parent == output_dir / 'visualizations'

    # Verify chart names match expected patterns
    chart_names = [Path(p).name for p in viz_paths['charts']]
    expected_charts = [
        'equipment_ranking.png',
        'seasonal_costs.png',
        'vendor_costs.png',
        'failure_patterns.png'
    ]

    for expected_name in expected_charts:
        assert expected_name in chart_names, f"Missing chart: {expected_name}"


# Integration Tests

def test_full_pipeline_integration(sample_csv_file, output_dir):
    """
    Integration test: Run complete pipeline with all outputs.

    Verifies that all modules work together correctly.
    """
    orchestrator = PipelineOrchestrator(
        input_file=str(sample_csv_file),
        output_dir=str(output_dir)
    )

    # Run analysis
    results = orchestrator.run_full_analysis()
    assert results is not None

    # Generate all outputs
    report_paths = orchestrator.generate_reports(results)
    export_paths = orchestrator.export_data(results)
    viz_paths = orchestrator.generate_visualizations(results)

    # Verify total file count
    total_files = (
        2 +  # PDF + Excel
        len(export_paths['csv']) + len(export_paths['json']) +  # Exports
        len(viz_paths['charts']) + 1  # Charts + Dashboard
    )

    expected_files = 2 + 4 + 4 + 4 + 1  # 15 total files
    assert total_files == expected_files, f"Expected {expected_files} files, got {total_files}"

    # Verify all directories have files
    assert len(list((output_dir / 'reports').glob('*'))) == 2
    assert len(list((output_dir / 'exports').glob('*'))) == 8
    assert len(list((output_dir / 'visualizations').glob('*'))) == 5


def test_pipeline_with_edge_case_data(tmp_path, output_dir):
    """
    Test pipeline handles edge cases:
    - Missing optional fields
    - Incomplete dates
    - Zero/negative costs
    - Unknown contractors
    """
    # Create CSV with edge cases
    data = {
        'id_': ['ID-001', 'ID-002', 'ID-003'],
        'wo_no': ['WO-001', 'WO-002', 'WO-003'],
        'Equipment_ID': ['EQ-001', 'EQ-002', 'EQ-003'],
        'EquipmentName': ['Equipment 1', 'Equipment 2', 'Equipment 3'],
        'Property_category': ['Commercial', 'Commercial', 'Residential'],
        'Work_Order_Type': ['Adhoc', 'Preventive', 'Adhoc'],
        'service_type_lv2': ['Repair', None, 'Maintenance'],
        'service_type_lv3': ['HVAC Repair', None, 'Plumbing Maintenance'],
        'FM_Type': ['Corrective', 'Corrective', 'Preventive'],
        'Create_Date': [datetime(2024, 1, 1), None, datetime(2024, 1, 3)],
        'Complete_Date': [datetime(2024, 1, 2), datetime(2024, 1, 3), None],
        'PO_AMOUNT': [100, 0, -50],  # Zero and negative costs
        'Contractor': ['Vendor A', None, 'Unknown'],  # None and Unknown
        'Problem': ['test', None, ''],
        'Cause': ['test', '', None],
        'Remedy': ['', None, 'test']
    }

    df = pd.DataFrame(data)
    csv_path = tmp_path / 'edge_case_orders.csv'
    df.to_csv(csv_path, index=False)

    # Should not crash
    orchestrator = PipelineOrchestrator(
        input_file=str(csv_path),
        output_dir=str(output_dir)
    )

    results = orchestrator.run_full_analysis()
    assert results is not None

    # Should still generate all outputs (even if empty/minimal)
    report_paths = orchestrator.generate_reports(results)
    assert Path(report_paths['pdf_path']).exists()
    assert Path(report_paths['excel_path']).exists()
