"""
Work order data schema definition and validation.

This module defines the expected fields for work order data and provides
validation functions to ensure data integrity for downstream analysis.
"""

from typing import List
import pandas as pd


# Required fields that must be present in all work order datasets
REQUIRED_FIELDS = [
    'id_',              # Unique identifier for the work order
    'wo_no',            # Work order number
    'Equipment_ID',     # Equipment unique identifier
    'EquipmentName',    # Equipment name/description
    'Create_Date',      # Work order creation date
    'Complete_Date',    # Work order completion date
    'PO_AMOUNT',        # Purchase order amount (cost)
    'Property_category', # Property categorization
    'FM_Type',          # Facility management type
    'Work_Order_Type',  # Type of work order (adhoc, preventive, etc.)
]

# Optional fields that are useful for analysis but not required
OPTIONAL_FIELDS = [
    'work_request_no',   # Work request reference
    'EquipmentNumber',   # Equipment number (may differ from ID)
    'service_type_lv1',  # Service type level 1 (hierarchical categorization)
    'service_type_lv2',  # Service type level 2
    'service_type_lv3',  # Service type level 3
    'Close_Date',        # Work order close date
    'Request_Create_Date', # Original request creation date
    'Cluster',           # Property cluster/grouping
    'Property',          # Property name
    'Property_Code',     # Property code
    'location_desc',     # Location description
    'Contractor',        # Contractor/vendor name
    'contract_id',       # Contract identifier
    'Problem',           # Problem description
    'Cause',             # Cause of the problem
    'Remedy',            # Remedy applied
    'description',       # General description
]

# Field types mapping (using pandas dtypes)
# Note: Most fields are 'object' (string) by default, with specific conversions
# handled in the data loader for dates and numeric fields
FIELD_TYPES = {
    'id_': 'object',
    'wo_no': 'object',
    'Equipment_ID': 'object',
    'EquipmentName': 'object',
    'Create_Date': 'object',  # Will be converted to datetime in loader
    'Complete_Date': 'object',  # Will be converted to datetime in loader
    'PO_AMOUNT': 'object',  # Will be converted to numeric in loader
    'Property_category': 'object',
    'FM_Type': 'object',
    'Work_Order_Type': 'object',
}


def validate_schema(df: pd.DataFrame) -> List[str]:
    """
    Validate that a DataFrame contains all required fields.

    Args:
        df: pandas DataFrame to validate

    Returns:
        List of missing required field names. Empty list if all required fields present.

    Example:
        >>> df = pd.read_csv('work_orders.csv')
        >>> missing = validate_schema(df)
        >>> if missing:
        >>>     raise ValueError(f"Missing required fields: {', '.join(missing)}")
    """
    df_columns = set(df.columns)
    required_set = set(REQUIRED_FIELDS)
    missing_fields = required_set - df_columns

    return sorted(list(missing_fields))
