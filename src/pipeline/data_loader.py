"""
Work order data loading and preprocessing.

This module provides functions to load work order data from Excel/CSV files,
validate schema integrity, and perform basic type conversions and cleaning.
"""

import logging
from pathlib import Path
from typing import Union

import pandas as pd

from .schema import validate_schema


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_work_orders(file_path: Union[str, Path]) -> pd.DataFrame:
    """
    Load work order data from CSV file with validation and preprocessing.

    This function:
    1. Loads CSV data with proper encoding
    2. Validates required fields are present
    3. Converts date columns to datetime
    4. Converts cost columns to numeric
    5. Strips whitespace from string columns
    6. Logs summary statistics

    Args:
        file_path: Path to the CSV file containing work order data

    Returns:
        pandas DataFrame with cleaned and validated work order data

    Raises:
        FileNotFoundError: If the specified file does not exist
        ValueError: If required fields are missing from the data
        Exception: For other data loading or processing errors

    Example:
        >>> df = load_work_orders('input/work_orders.csv')
        >>> print(f"Loaded {len(df)} work orders")
    """
    file_path = Path(file_path)

    # Check file exists
    if not file_path.exists():
        raise FileNotFoundError(
            f"Data file not found: {file_path}\n"
            f"Please ensure the file exists at the specified path."
        )

    logger.info(f"Loading work order data from: {file_path}")

    try:
        # Load CSV with UTF-8-sig encoding (handles BOM) and mixed types
        df = pd.read_csv(
            file_path,
            encoding='utf-8-sig',
            low_memory=False  # Read entire file to infer types correctly
        )

        logger.info(f"Successfully loaded {len(df)} rows from CSV")

    except UnicodeDecodeError as e:
        raise Exception(
            f"Encoding error reading file: {file_path}\n"
            f"Error: {str(e)}\n"
            f"Try opening the file in a text editor and saving with UTF-8 encoding."
        ) from e
    except Exception as e:
        raise Exception(
            f"Error loading CSV file: {file_path}\n"
            f"Error: {str(e)}"
        ) from e

    # Validate schema
    missing_fields = validate_schema(df)
    if missing_fields:
        raise ValueError(
            f"Data validation failed: Missing required fields\n"
            f"Missing fields: {', '.join(missing_fields)}\n"
            f"Available fields: {', '.join(sorted(df.columns))}\n"
            f"Please ensure the input file contains all required fields."
        )

    logger.info("Schema validation passed: all required fields present")

    # Convert date columns to datetime
    date_columns = ['Create_Date', 'Complete_Date']
    for col in date_columns:
        if col in df.columns:
            original_count = df[col].notna().sum()
            df[col] = pd.to_datetime(df[col], errors='coerce')
            converted_count = df[col].notna().sum()
            invalid_count = original_count - converted_count

            if invalid_count > 0:
                logger.warning(
                    f"{col}: {invalid_count} invalid dates converted to NaT"
                )

    # Convert create_date_yyyymmdd with dayfirst format (D/M/YYYY)
    if 'create_date_yyyymmdd' in df.columns:
        original_count = df['create_date_yyyymmdd'].notna().sum()
        df['create_date_yyyymmdd'] = pd.to_datetime(
            df['create_date_yyyymmdd'],
            errors='coerce',
            dayfirst=True  # Handle D/M/YYYY format
        )
        converted_count = df['create_date_yyyymmdd'].notna().sum()
        invalid_count = original_count - converted_count

        if invalid_count > 0:
            logger.warning(
                f"create_date_yyyymmdd: {invalid_count} invalid dates converted to NaT"
            )

    logger.info("Date columns converted to datetime")

    # Convert PO_AMOUNT to numeric
    if 'PO_AMOUNT' in df.columns:
        original_count = df['PO_AMOUNT'].notna().sum()
        df['PO_AMOUNT'] = pd.to_numeric(df['PO_AMOUNT'], errors='coerce')
        converted_count = df['PO_AMOUNT'].notna().sum()
        invalid_count = original_count - converted_count

        if invalid_count > 0:
            logger.warning(
                f"PO_AMOUNT: {invalid_count} non-numeric values converted to NaN"
            )

    logger.info("Numeric columns converted")

    # Strip whitespace from string columns
    string_columns = df.select_dtypes(include=['object']).columns
    for col in string_columns:
        df[col] = df[col].str.strip()

    logger.info("Whitespace stripped from string columns")

    # Log summary statistics - prefer create_date_yyyymmdd
    date_col_for_log = None
    for col in ['create_date_yyyymmdd', 'Create_Date']:
        if col in df.columns and df[col].notna().any():
            date_col_for_log = col
            break

    if date_col_for_log:
        date_range_start = df[date_col_for_log].min()
        date_range_end = df[date_col_for_log].max()
        logger.info(
            f"Date range ({date_col_for_log}): {date_range_start} to {date_range_end}"
        )

    if 'PO_AMOUNT' in df.columns:
        total_cost = df['PO_AMOUNT'].sum()
        logger.info(f"Total work order cost: ${total_cost:,.2f}")

    logger.info(f"Data loading complete: {len(df)} work orders ready for analysis")

    return df
