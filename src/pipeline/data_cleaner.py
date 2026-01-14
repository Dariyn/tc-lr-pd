"""
Work order data cleaning and standardization.

This module provides functions to clean work order data by:
- Handling missing equipment identifiers
- Cleaning and validating cost data
- Cleaning and validating date data
- Flagging outliers for review
- Calculating derived fields
"""

import logging
import hashlib
import numpy as np
import pandas as pd


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def clean_equipment_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean equipment identification fields.

    Processing steps:
    1. Drop rows where both Equipment_ID and EquipmentName are null
       (cannot analyze without equipment identifier)
    2. For rows with Equipment_ID but missing EquipmentName, set
       EquipmentName = f"Unknown Equipment {Equipment_ID}"
    3. For rows with EquipmentName but missing Equipment_ID, create
       synthetic ID from name hash
    4. Standardize EquipmentName: strip whitespace, title case

    Args:
        df: DataFrame with Equipment_ID and EquipmentName columns

    Returns:
        Cleaned DataFrame with consistent equipment identifiers
    """
    initial_count = len(df)

    # Drop rows where both Equipment_ID and EquipmentName are null
    df = df[~(df['Equipment_ID'].isna() & df['EquipmentName'].isna())]
    dropped_count = initial_count - len(df)

    if dropped_count > 0:
        logger.warning(
            f"Dropped {dropped_count} rows with no equipment identifier "
            f"(both Equipment_ID and EquipmentName null)"
        )

    # For rows with Equipment_ID but missing EquipmentName
    mask_id_no_name = df['Equipment_ID'].notna() & df['EquipmentName'].isna()
    if mask_id_no_name.any():
        df.loc[mask_id_no_name, 'EquipmentName'] = (
            df.loc[mask_id_no_name, 'Equipment_ID'].apply(
                lambda x: f"Unknown Equipment {x}"
            )
        )
        logger.info(
            f"Set EquipmentName for {mask_id_no_name.sum()} rows "
            f"with Equipment_ID but missing name"
        )

    # For rows with EquipmentName but missing Equipment_ID
    mask_name_no_id = df['EquipmentName'].notna() & df['Equipment_ID'].isna()
    if mask_name_no_id.any():
        # Convert Equipment_ID to string type to avoid dtype warnings
        df['Equipment_ID'] = df['Equipment_ID'].astype('object')
        df.loc[mask_name_no_id, 'Equipment_ID'] = (
            df.loc[mask_name_no_id, 'EquipmentName'].apply(
                lambda x: hashlib.md5(str(x).encode()).hexdigest()[:12]
            )
        )
        logger.info(
            f"Created synthetic Equipment_ID for {mask_name_no_id.sum()} rows "
            f"with EquipmentName but missing ID"
        )

    # Standardize EquipmentName: strip whitespace, title case
    df['EquipmentName'] = df['EquipmentName'].str.strip().str.title()
    logger.info("Standardized EquipmentName format (title case)")

    return df


def clean_cost_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and validate cost data.

    Processing steps:
    1. Fill missing PO_AMOUNT with 0 (adhoc work may not have PO)
    2. Replace negative costs with 0 (log warning)
    3. Flag outliers: costs > 99th percentile get 'cost_outlier' flag
       (don't remove - may be legitimate high-cost repairs)

    Args:
        df: DataFrame with PO_AMOUNT column (already converted to numeric)

    Returns:
        Cleaned DataFrame with cost_outlier flag column
    """
    # Fill missing PO_AMOUNT with 0
    missing_count = df['PO_AMOUNT'].isna().sum()
    if missing_count > 0:
        df['PO_AMOUNT'] = df['PO_AMOUNT'].fillna(0)
        logger.info(f"Filled {missing_count} missing PO_AMOUNT values with 0")

    # Replace negative costs with 0 and log warning
    negative_mask = df['PO_AMOUNT'] < 0
    negative_count = negative_mask.sum()
    if negative_count > 0:
        df.loc[negative_mask, 'PO_AMOUNT'] = 0
        logger.warning(
            f"Replaced {negative_count} negative PO_AMOUNT values with 0"
        )

    # Flag cost outliers (> 99th percentile)
    if len(df) > 0 and df['PO_AMOUNT'].max() > 0:
        cost_99th = df['PO_AMOUNT'].quantile(0.99)
        df['cost_outlier'] = df['PO_AMOUNT'] > cost_99th
        outlier_count = df['cost_outlier'].sum()
        logger.info(
            f"Flagged {outlier_count} cost outliers "
            f"(> 99th percentile: ${cost_99th:,.2f})"
        )
    else:
        df['cost_outlier'] = False

    return df


def clean_date_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and validate date data, calculate derived fields.

    Processing steps:
    1. Drop rows missing Create_Date (can't analyze without creation date)
    2. For missing Complete_Date where Status_Eng == 'Closed', use Close_Date
    3. Calculate duration_hours for completed work orders
    4. Flag duration outliers: duration > 99th percentile

    Args:
        df: DataFrame with Create_Date, Complete_Date, Status_Eng, Close_Date
            (dates already converted to datetime)

    Returns:
        Cleaned DataFrame with duration_hours and duration_outlier columns
    """
    initial_count = len(df)

    # Drop rows missing Create_Date
    df = df[df['Create_Date'].notna()]
    dropped_count = initial_count - len(df)

    if dropped_count > 0:
        logger.warning(
            f"Dropped {dropped_count} rows with missing Create_Date "
            f"(cannot analyze without creation date)"
        )

    # For missing Complete_Date where Status_Eng == 'Closed', use Close_Date
    if 'Close_Date' in df.columns:
        # Convert Close_Date to datetime if it's not already
        if not pd.api.types.is_datetime64_any_dtype(df['Close_Date']):
            df['Close_Date'] = pd.to_datetime(df['Close_Date'], errors='coerce')

        mask_closed_no_complete = (
            (df['Complete_Date'].isna()) &
            (df['Status_Eng'] == 'Closed') &
            (df['Close_Date'].notna())
        )
        if mask_closed_no_complete.any():
            df.loc[mask_closed_no_complete, 'Complete_Date'] = (
                df.loc[mask_closed_no_complete, 'Close_Date']
            )
            logger.info(
                f"Used Close_Date for {mask_closed_no_complete.sum()} closed work orders "
                f"with missing Complete_Date"
            )

    # Calculate duration_hours for completed work orders
    completed_mask = (df['Complete_Date'].notna() & df['Create_Date'].notna())
    df['duration_hours'] = pd.Series(dtype=float)

    if completed_mask.any():
        duration = (
            df.loc[completed_mask, 'Complete_Date'].values -
            df.loc[completed_mask, 'Create_Date'].values
        )
        # Convert timedelta to hours
        df.loc[completed_mask, 'duration_hours'] = (
            pd.to_timedelta(duration).total_seconds() / 3600
        )
        logger.info(
            f"Calculated duration_hours for {completed_mask.sum()} completed work orders"
        )

    # Flag duration outliers (> 99th percentile)
    duration_valid_mask = df['duration_hours'].notna() & (df['duration_hours'] >= 0)
    if duration_valid_mask.any():
        duration_99th = df.loc[duration_valid_mask, 'duration_hours'].quantile(0.99)
        df['duration_outlier'] = (df['duration_hours'] > duration_99th) & duration_valid_mask
        outlier_count = df['duration_outlier'].sum()
        logger.info(
            f"Flagged {outlier_count} duration outliers "
            f"(> 99th percentile: {duration_99th:,.1f} hours)"
        )
    else:
        df['duration_outlier'] = False

    return df


def clean_work_orders(df: pd.DataFrame) -> pd.DataFrame:
    """
    Orchestrate all cleaning operations on work order data.

    This function applies cleaning in the correct order:
    1. Equipment cleaning (drops rows with no equipment identifier)
    2. Cost cleaning (fills missing, removes negatives, flags outliers)
    3. Date cleaning (drops rows with no Create_Date, calculates duration)

    Args:
        df: Raw DataFrame from load_work_orders()

    Returns:
        Cleaned DataFrame with added columns:
        - cost_outlier (bool): Cost > 99th percentile
        - duration_outlier (bool): Duration > 99th percentile
        - duration_hours (float): Work order duration in hours
    """
    initial_count = len(df)
    logger.info(f"Starting data cleaning: {initial_count} work orders")

    # Make a copy to avoid modifying original
    df_clean = df.copy()

    # Clean equipment data
    df_clean = clean_equipment_data(df_clean)

    # Clean cost data
    df_clean = clean_cost_data(df_clean)

    # Clean date data
    df_clean = clean_date_data(df_clean)

    final_count = len(df_clean)
    rows_dropped = initial_count - final_count

    # Log cleaning summary
    logger.info("=" * 60)
    logger.info("Data Cleaning Summary")
    logger.info("=" * 60)
    logger.info(f"Initial rows:          {initial_count:>10,}")
    logger.info(f"Final rows:            {final_count:>10,}")
    logger.info(f"Rows dropped:          {rows_dropped:>10,} ({rows_dropped/initial_count*100:.1f}%)")
    logger.info(f"Cost outliers flagged: {df_clean['cost_outlier'].sum():>10,}")
    logger.info(f"Duration outliers:     {df_clean['duration_outlier'].sum():>10,}")
    logger.info("=" * 60)

    return df_clean
