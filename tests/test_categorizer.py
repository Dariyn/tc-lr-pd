"""
Tests for work order categorization functions.

These tests validate the category normalization logic, equipment type assignment,
and consistency score calculations using sample DataFrames with known categories.
"""

import pandas as pd
import pytest

from src.pipeline.categorizer import (
    normalize_categories,
    create_category_hierarchy,
    assign_equipment_types,
    categorize_work_orders
)


def test_normalize_categories_uses_priority():
    """
    Test that normalize_categories prefers service_type_lv2 over FM_Type.

    When both fields are present, service_type_lv2 should be used as the primary
    equipment_category.
    """
    # Create sample data with both fields populated
    df = pd.DataFrame({
        'Equipment_ID': ['E001', 'E002', 'E003'],
        'service_type_lv2': ['HVAC', 'Electrical', None],
        'service_type_lv3': ['Air Conditioning', 'Lighting', None],
        'FM_Type': ['Mechanical', 'Power Systems', 'Plumbing'],
    })

    result = normalize_categories(df)

    # service_type_lv2 should be preferred when present
    assert result.loc[0, 'equipment_category'] == 'Hvac'
    assert result.loc[1, 'equipment_category'] == 'Electrical'

    # FM_Type should be used when service_type_lv2 is null
    assert result.loc[2, 'equipment_category'] == 'Plumbing'


def test_normalize_categories_handles_nulls():
    """
    Test that normalize_categories handles null values with proper fallback.

    Should fallback to 'Uncategorized' when both service_type_lv2 and FM_Type are null.
    """
    # Create sample data with nulls
    df = pd.DataFrame({
        'Equipment_ID': ['E001', 'E002'],
        'service_type_lv2': [None, None],
        'service_type_lv3': [None, None],
        'FM_Type': [None, 'HVAC'],
    })

    result = normalize_categories(df)

    # Should fallback to Uncategorized when all are null
    assert result.loc[0, 'equipment_category'] == 'Uncategorized'

    # Should use FM_Type when service_type_lv2 is null
    assert result.loc[1, 'equipment_category'] == 'Hvac'

    # Subcategory should fallback to General
    assert result.loc[0, 'equipment_subcategory'] == 'General'


def test_normalize_categories_standardizes_text():
    """
    Test that normalize_categories standardizes text formatting.

    Should strip whitespace and convert to title case.
    """
    df = pd.DataFrame({
        'Equipment_ID': ['E001', 'E002'],
        'service_type_lv2': ['  hvac systems  ', 'ELECTRICAL'],
        'service_type_lv3': ['air conditioning', 'LIGHTING  '],
        'FM_Type': ['Mechanical', 'Power'],
    })

    result = normalize_categories(df)

    # Text should be stripped and title cased
    assert result.loc[0, 'equipment_category'] == 'Hvac Systems'
    assert result.loc[1, 'equipment_category'] == 'Electrical'
    assert result.loc[0, 'equipment_subcategory'] == 'Air Conditioning'
    assert result.loc[1, 'equipment_subcategory'] == 'Lighting'


def test_create_category_hierarchy():
    """
    Test that create_category_hierarchy counts equipment and work orders correctly.

    Should group by category and count unique equipment IDs and total work orders.
    """
    df = pd.DataFrame({
        'Equipment_ID': ['E001', 'E001', 'E002', 'E003', 'E003', 'E003'],
        'equipment_category': ['HVAC', 'HVAC', 'HVAC', 'Electrical', 'Electrical', 'Electrical'],
    })

    result = create_category_hierarchy(df)

    # Check structure
    assert list(result.columns) == ['category', 'equipment_count', 'work_order_count']

    # Check counts
    hvac_row = result[result['category'] == 'HVAC'].iloc[0]
    assert hvac_row['equipment_count'] == 2  # E001 and E002
    assert hvac_row['work_order_count'] == 3  # 3 work orders

    electrical_row = result[result['category'] == 'Electrical'].iloc[0]
    assert electrical_row['equipment_count'] == 1  # E003 only
    assert electrical_row['work_order_count'] == 3  # 3 work orders

    # Should be sorted by work_order_count descending
    assert result['work_order_count'].is_monotonic_decreasing or \
           result['work_order_count'].nunique() == 1  # Allow ties


def test_assign_equipment_types_finds_primary():
    """
    Test that assign_equipment_types assigns the mode category as primary.

    Equipment appearing in multiple categories should be assigned to the most
    frequent category.
    """
    df = pd.DataFrame({
        'Equipment_ID': ['E001', 'E001', 'E001', 'E001', 'E002', 'E002'],
        'equipment_category': ['HVAC', 'HVAC', 'HVAC', 'Electrical', 'Plumbing', 'Plumbing'],
    })

    result = assign_equipment_types(df)

    # E001 appears 3 times in HVAC, 1 time in Electrical - should be HVAC
    e001_rows = result[result['Equipment_ID'] == 'E001']
    assert all(e001_rows['equipment_primary_category'] == 'HVAC')

    # E002 appears only in Plumbing
    e002_rows = result[result['Equipment_ID'] == 'E002']
    assert all(e002_rows['equipment_primary_category'] == 'Plumbing')


def test_assign_equipment_types_calculates_consistency():
    """
    Test that assign_equipment_types calculates consistency score correctly.

    Consistency should be percentage of work orders in primary category.
    """
    df = pd.DataFrame({
        'Equipment_ID': ['E001', 'E001', 'E001', 'E001', 'E002', 'E002', 'E002', 'E002'],
        'equipment_category': ['HVAC', 'HVAC', 'HVAC', 'Electrical', 'Plumbing', 'Plumbing', 'Plumbing', 'Plumbing'],
    })

    result = assign_equipment_types(df)

    # E001: 3 HVAC + 1 Electrical = 75% consistency (3/4)
    e001_consistency = result[result['Equipment_ID'] == 'E001']['equipment_category_consistency'].iloc[0]
    assert e001_consistency == 75.0

    # E002: 4 Plumbing + 0 other = 100% consistency (4/4)
    e002_consistency = result[result['Equipment_ID'] == 'E002']['equipment_category_consistency'].iloc[0]
    assert e002_consistency == 100.0


def test_assign_equipment_types_handles_ties():
    """
    Test that assign_equipment_types handles ties in category frequency.

    When equipment appears equally in multiple categories, should pick one consistently.
    """
    df = pd.DataFrame({
        'Equipment_ID': ['E001', 'E001', 'E001', 'E001'],
        'equipment_category': ['HVAC', 'HVAC', 'Electrical', 'Electrical'],
    })

    result = assign_equipment_types(df)

    # Should pick one of the tied categories
    primary = result['equipment_primary_category'].iloc[0]
    assert primary in ['HVAC', 'Electrical']

    # All rows for same equipment should have same primary
    assert result['equipment_primary_category'].nunique() == 1

    # Consistency should be 50% (2/4)
    assert result['equipment_category_consistency'].iloc[0] == 50.0


def test_categorize_work_orders_integration():
    """
    Test the full categorize_work_orders orchestration function.

    Should apply all categorization steps and return df with all expected columns.
    """
    df = pd.DataFrame({
        'Equipment_ID': ['E001', 'E001', 'E002', 'E003', 'E003'],
        'service_type_lv2': ['HVAC', 'HVAC', None, 'Electrical', 'Electrical'],
        'service_type_lv3': ['Air Conditioning', 'Air Conditioning', None, 'Lighting', 'Power'],
        'FM_Type': ['Mechanical', 'Mechanical', 'Plumbing', 'Power', 'Power'],
    })

    result = categorize_work_orders(df)

    # Should have all expected columns
    expected_columns = [
        'equipment_category',
        'equipment_subcategory',
        'equipment_primary_category',
        'equipment_category_consistency'
    ]
    for col in expected_columns:
        assert col in result.columns

    # Check specific values
    assert result.loc[0, 'equipment_category'] == 'Hvac'
    assert result.loc[2, 'equipment_category'] == 'Plumbing'

    # E001 should have HVAC as primary (appears twice)
    e001_rows = result[result['Equipment_ID'] == 'E001']
    assert all(e001_rows['equipment_primary_category'] == 'Hvac')
    assert e001_rows['equipment_category_consistency'].iloc[0] == 100.0

    # E003 should have Electrical as primary
    e003_rows = result[result['Equipment_ID'] == 'E003']
    assert all(e003_rows['equipment_primary_category'] == 'Electrical')


def test_categorize_work_orders_with_minimal_data():
    """
    Test categorize_work_orders with minimal/edge case data.

    Should handle single row and all-null scenarios gracefully.
    """
    # Single row
    df = pd.DataFrame({
        'Equipment_ID': ['E001'],
        'service_type_lv2': ['HVAC'],
        'service_type_lv3': ['Air Conditioning'],
        'FM_Type': ['Mechanical'],
    })

    result = categorize_work_orders(df)
    assert len(result) == 1
    assert result.loc[0, 'equipment_category'] == 'Hvac'
    assert result.loc[0, 'equipment_category_consistency'] == 100.0

    # All nulls
    df_nulls = pd.DataFrame({
        'Equipment_ID': ['E001', 'E002'],
        'service_type_lv2': [None, None],
        'service_type_lv3': [None, None],
        'FM_Type': [None, None],
    })

    result_nulls = categorize_work_orders(df_nulls)
    assert all(result_nulls['equipment_category'] == 'Uncategorized')
    assert all(result_nulls['equipment_subcategory'] == 'General')
