"""
Work order categorization and equipment type assignment.

This module provides functions to normalize equipment categories from multiple
classification schemes and assign equipment to primary categories for accurate
cross-category comparisons.
"""

import logging
from typing import Dict, Tuple

import pandas as pd


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def normalize_categories(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize equipment categories from multiple classification fields.

    Creates standardized category fields using prioritized fallback logic:
    - equipment_category: primary category (service_type_lv2 > FM_Type > 'Uncategorized')
    - equipment_subcategory: granular category (service_type_lv3 > service_type_lv2 > 'General')

    Handles mixed language text (Chinese/English) by preserving as-is with whitespace stripped.

    Args:
        df: DataFrame with raw work order data containing classification fields

    Returns:
        DataFrame with added equipment_category and equipment_subcategory columns

    Example:
        >>> df = load_work_orders('work_orders.csv')
        >>> df = normalize_categories(df)
        >>> print(df[['equipment_category', 'equipment_subcategory']].head())
    """
    logger.info("Starting category normalization")

    # Create equipment_category with priority fallback
    df['equipment_category'] = df['service_type_lv2'].fillna(
        df['FM_Type']
    ).fillna('Uncategorized')

    # Create equipment_subcategory from most granular level
    df['equipment_subcategory'] = df['service_type_lv3'].fillna(
        df['service_type_lv2']
    ).fillna('General')

    # Standardize text: strip whitespace and title case
    df['equipment_category'] = df['equipment_category'].str.strip().str.title()
    df['equipment_subcategory'] = df['equipment_subcategory'].str.strip().str.title()

    # Count category assignments
    uncategorized_count = (df['equipment_category'] == 'Uncategorized').sum()
    unique_categories = df['equipment_category'].nunique()

    logger.info(
        f"Category normalization complete: "
        f"{unique_categories} unique categories, "
        f"{uncategorized_count} uncategorized work orders"
    )

    return df


def create_category_hierarchy(df: pd.DataFrame) -> pd.DataFrame:
    """
    Create category hierarchy with equipment and work order counts.

    This helps identify which categories have sufficient data for statistical analysis.

    Args:
        df: DataFrame with normalized equipment_category field

    Returns:
        DataFrame with columns:
        - category: equipment category name
        - equipment_count: unique equipment IDs in this category
        - work_order_count: total work orders in this category
        Sorted by work_order_count descending

    Example:
        >>> hierarchy = create_category_hierarchy(df)
        >>> print(hierarchy.head(10))  # Top 10 categories by work order volume
    """
    logger.info("Creating category hierarchy")

    hierarchy = df.groupby('equipment_category').agg(
        equipment_count=('Equipment_ID', 'nunique'),
        work_order_count=('Equipment_ID', 'count')
    ).reset_index()

    hierarchy.columns = ['category', 'equipment_count', 'work_order_count']
    hierarchy = hierarchy.sort_values('work_order_count', ascending=False)

    logger.info(
        f"Category hierarchy created: {len(hierarchy)} categories, "
        f"avg {hierarchy['work_order_count'].mean():.0f} work orders per category"
    )

    return hierarchy


def assign_equipment_types(df: pd.DataFrame) -> pd.DataFrame:
    """
    Assign primary category to each equipment based on most frequent category.

    Some equipment may appear in multiple categories if miscategorized over time.
    This function:
    1. Identifies the mode (most frequent) category for each equipment
    2. Adds equipment_primary_category column to original df
    3. Calculates equipment_category_consistency score (% of work orders in primary)
    4. Identifies potentially miscategorized equipment (consistency < 80%)

    Args:
        df: DataFrame with Equipment_ID and equipment_category fields

    Returns:
        DataFrame with added columns:
        - equipment_primary_category: most frequent category for this equipment
        - equipment_category_consistency: percentage (0-100) of work orders in primary category

    Example:
        >>> df = assign_equipment_types(df)
        >>> inconsistent = df[df['equipment_category_consistency'] < 80]
        >>> print(f"Found {len(inconsistent['Equipment_ID'].unique())} potentially miscategorized equipment")
    """
    logger.info("Assigning equipment primary categories")

    # Find mode category for each equipment
    equipment_primary = df.groupby('Equipment_ID')['equipment_category'].agg(
        lambda x: x.mode()[0] if not x.mode().empty else x.iloc[0]
    ).reset_index()
    equipment_primary.columns = ['Equipment_ID', 'equipment_primary_category']

    # Merge primary category back to original df
    df = df.merge(equipment_primary, on='Equipment_ID', how='left')

    # Calculate consistency score
    df['is_primary_category'] = (
        df['equipment_category'] == df['equipment_primary_category']
    )

    consistency = df.groupby('Equipment_ID')['is_primary_category'].agg(
        lambda x: (x.sum() / len(x) * 100) if len(x) > 0 else 100
    ).reset_index()
    consistency.columns = ['Equipment_ID', 'equipment_category_consistency']

    # Merge consistency back to df
    df = df.merge(consistency, on='Equipment_ID', how='left')

    # Drop temporary column
    df = df.drop('is_primary_category', axis=1)

    # Count equipment by consistency threshold
    low_consistency_equipment = df[
        df['equipment_category_consistency'] < 80
    ]['Equipment_ID'].nunique()

    logger.info(
        f"Equipment type assignment complete: "
        f"{df['Equipment_ID'].nunique()} unique equipment, "
        f"{low_consistency_equipment} with consistency < 80% (potentially miscategorized)"
    )

    # Log consistency distribution
    consistency_ranges = pd.cut(
        df['equipment_category_consistency'],
        bins=[0, 50, 80, 90, 100],
        labels=['<50%', '50-80%', '80-90%', '90-100%']
    )
    consistency_dist = consistency_ranges.value_counts().sort_index()
    logger.info(f"Consistency distribution:\n{consistency_dist}")

    return df


def categorize_work_orders(df: pd.DataFrame) -> pd.DataFrame:
    """
    Orchestrate all categorization steps: normalize, create hierarchy, assign equipment types.

    This is the main entry point for categorization. It:
    1. Normalizes categories from multiple classification fields
    2. Creates category hierarchy for analysis
    3. Assigns equipment to primary categories with consistency scores
    4. Logs comprehensive categorization statistics

    Args:
        df: DataFrame with raw work order data from load_work_orders()

    Returns:
        DataFrame with added columns:
        - equipment_category: normalized primary category
        - equipment_subcategory: normalized granular category
        - equipment_primary_category: most frequent category for this equipment
        - equipment_category_consistency: consistency score (0-100)

    Example:
        >>> from src.pipeline.data_loader import load_work_orders
        >>> df = load_work_orders('input/work_orders.csv')
        >>> df = categorize_work_orders(df)
        >>> print(f"{df['equipment_category'].nunique()} unique categories")
    """
    logger.info("=" * 60)
    logger.info("Starting work order categorization")
    logger.info("=" * 60)

    # Step 1: Normalize categories
    df = normalize_categories(df)

    # Step 2: Create hierarchy (for logging/inspection)
    hierarchy = create_category_hierarchy(df)
    logger.info(f"\nTop 5 categories by volume:")
    for idx, row in hierarchy.head(5).iterrows():
        logger.info(
            f"  {row['category']}: "
            f"{row['equipment_count']} equipment, "
            f"{row['work_order_count']} work orders"
        )

    # Step 3: Assign equipment types
    df = assign_equipment_types(df)

    logger.info("=" * 60)
    logger.info("Categorization complete")
    logger.info("=" * 60)

    return df
