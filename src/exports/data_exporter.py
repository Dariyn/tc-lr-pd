"""
Data exporter module for converting analysis results to CSV and JSON formats.

Purpose: Enable stakeholders to consume analysis data in standard formats for
external tools, spreadsheets, or custom processing.
"""

import pandas as pd
import json
from pathlib import Path
from typing import Union, Dict, List, Any
import logging

logger = logging.getLogger(__name__)


class DataExporter:
    """
    Export analysis results to CSV and JSON formats.

    Provides methods to export:
    - Equipment rankings (DataFrames with priority scores)
    - Seasonal patterns (dictionaries with monthly/quarterly data)
    - Vendor metrics (DataFrames with vendor performance)
    - Failure patterns (lists of pattern dictionaries)
    """

    def export_equipment_rankings(self, df: pd.DataFrame, output_path: Union[str, Path]) -> None:
        """
        Export equipment ranking DataFrame to CSV.

        Args:
            df: DataFrame with equipment rankings (from equipment_ranker.rank_equipment)
            output_path: Path to output CSV file

        The CSV includes columns like Equipment_Name, equipment_primary_category,
        work_orders_per_month, avg_cost, cost_impact, priority_score, overall_rank.
        Data is sorted by priority_score descending.
        """
        # Handle empty DataFrame
        if df is None or len(df) == 0:
            logger.warning("Empty DataFrame provided for equipment rankings export")
            empty_df = pd.DataFrame(columns=[
                'Equipment_Name', 'equipment_primary_category', 'work_orders_per_month',
                'avg_cost', 'cost_impact', 'priority_score', 'overall_rank'
            ])
            empty_df.to_csv(output_path, index=False)
            return

        # Create a copy for export (don't modify original)
        export_df = df.copy()

        # Sort by priority_score descending
        if 'priority_score' in export_df.columns:
            export_df = export_df.sort_values('priority_score', ascending=False)

        # Export to CSV without index
        export_df.to_csv(output_path, index=False)
        logger.info(f"Exported {len(export_df)} equipment rankings to {output_path}")

    def export_seasonal_patterns(self, patterns_dict: Dict[str, Any], output_path: Union[str, Path]) -> None:
        """
        Export seasonal analysis patterns to CSV.

        Args:
            patterns_dict: Dictionary with seasonal data, typically contains:
                - 'monthly_costs': DataFrame with monthly aggregations
                - 'quarterly_costs': DataFrame with quarterly aggregations
                - 'patterns': List of detected patterns
            output_path: Path to output CSV file

        Creates a CSV with columns: period, total_cost, work_order_count, avg_cost
        Combines monthly and quarterly data if available.
        """
        # Handle None or empty dict
        if patterns_dict is None or len(patterns_dict) == 0:
            logger.warning("Empty patterns_dict provided for seasonal patterns export")
            empty_df = pd.DataFrame(columns=['period', 'total_cost', 'work_order_count', 'avg_cost'])
            empty_df.to_csv(output_path, index=False)
            return

        # Try to extract DataFrame from patterns_dict
        export_df = None

        # Prefer monthly_costs if available
        if 'monthly_costs' in patterns_dict and patterns_dict['monthly_costs'] is not None:
            export_df = patterns_dict['monthly_costs']
        elif 'quarterly_costs' in patterns_dict and patterns_dict['quarterly_costs'] is not None:
            export_df = patterns_dict['quarterly_costs']

        # If still no DataFrame found, create empty
        if export_df is None or len(export_df) == 0:
            logger.warning("No monthly or quarterly cost data found in patterns_dict")
            empty_df = pd.DataFrame(columns=['period', 'total_cost', 'work_order_count', 'avg_cost'])
            empty_df.to_csv(output_path, index=False)
            return

        # Create a copy for export
        export_df = export_df.copy()

        # Ensure required columns exist
        required_cols = ['period', 'total_cost', 'work_order_count', 'avg_cost']
        for col in required_cols:
            if col not in export_df.columns:
                export_df[col] = None

        # Select and reorder columns
        export_df = export_df[required_cols]

        # Export to CSV without index
        export_df.to_csv(output_path, index=False)
        logger.info(f"Exported {len(export_df)} seasonal patterns to {output_path}")

    def export_vendor_metrics(self, df: pd.DataFrame, output_path: Union[str, Path]) -> None:
        """
        Export vendor performance DataFrame to CSV.

        Args:
            df: DataFrame with vendor metrics (from vendor_analyzer.calculate_vendor_costs)
            output_path: Path to output CSV file

        The CSV includes columns like contractor, total_cost, work_order_count,
        avg_cost_per_wo. Data is sorted by total_cost descending.
        """
        # Handle empty DataFrame
        if df is None or len(df) == 0:
            logger.warning("Empty DataFrame provided for vendor metrics export")
            empty_df = pd.DataFrame(columns=[
                'contractor', 'total_cost', 'work_order_count', 'avg_cost_per_wo'
            ])
            empty_df.to_csv(output_path, index=False)
            return

        # Create a copy for export
        export_df = df.copy()

        # Sort by total_cost descending
        if 'total_cost' in export_df.columns:
            export_df = export_df.sort_values('total_cost', ascending=False)

        # Export to CSV without index
        export_df.to_csv(output_path, index=False)
        logger.info(f"Exported {len(export_df)} vendor metrics to {output_path}")

    def export_failure_patterns(self, patterns_list: List[Dict[str, Any]], output_path: Union[str, Path]) -> None:
        """
        Export failure patterns to CSV.

        Args:
            patterns_list: List of pattern dictionaries from failure_pattern_analyzer
                Each dict typically contains: pattern, occurrences, total_cost,
                avg_cost, category, equipment_affected, impact_score
            output_path: Path to output CSV file

        Creates CSV with columns: pattern, frequency, total_cost, equipment_count, category
        """
        # Handle None or empty list
        if patterns_list is None or len(patterns_list) == 0:
            logger.warning("Empty patterns_list provided for failure patterns export")
            empty_df = pd.DataFrame(columns=[
                'pattern', 'frequency', 'total_cost', 'equipment_count', 'category'
            ])
            empty_df.to_csv(output_path, index=False)
            return

        # Convert list of dicts to DataFrame
        df = pd.DataFrame(patterns_list)

        # Standardize column names for export
        # Map various possible input column names to standard export names
        column_mapping = {
            'occurrences': 'frequency',
            'equipment_affected': 'equipment_count'
        }

        for old_name, new_name in column_mapping.items():
            if old_name in df.columns and new_name not in df.columns:
                df = df.rename(columns={old_name: new_name})

        # Ensure required columns exist
        required_cols = ['pattern', 'frequency', 'total_cost', 'equipment_count', 'category']
        for col in required_cols:
            if col not in df.columns:
                df[col] = None

        # Select and reorder columns
        export_df = df[required_cols].copy()

        # Export to CSV without index
        export_df.to_csv(output_path, index=False)
        logger.info(f"Exported {len(export_df)} failure patterns to {output_path}")

    # JSON Export Methods

    def export_equipment_rankings_json(self, df: pd.DataFrame, output_path: Union[str, Path]) -> None:
        """
        Export equipment ranking DataFrame to JSON.

        Args:
            df: DataFrame with equipment rankings (from equipment_ranker.rank_equipment)
            output_path: Path to output JSON file

        Creates pretty-printed JSON array of equipment objects sorted by priority_score.
        Handles NaN values by converting to null.
        """
        # Handle empty DataFrame
        if df is None or len(df) == 0:
            logger.warning("Empty DataFrame provided for equipment rankings JSON export")
            with open(output_path, 'w') as f:
                json.dump([], f, indent=2)
            return

        # Create a copy for export
        export_df = df.copy()

        # Sort by priority_score descending
        if 'priority_score' in export_df.columns:
            export_df = export_df.sort_values('priority_score', ascending=False)

        # Convert to list of dicts, replacing NaN with None
        records = export_df.to_dict('records')

        # Clean NaN/Infinity values
        cleaned_records = self._clean_for_json(records)

        # Write to JSON with pretty printing
        with open(output_path, 'w') as f:
            json.dump(cleaned_records, f, indent=2)

        logger.info(f"Exported {len(cleaned_records)} equipment rankings to {output_path}")

    def export_seasonal_patterns_json(self, patterns_dict: Dict[str, Any], output_path: Union[str, Path]) -> None:
        """
        Export seasonal analysis patterns to JSON.

        Args:
            patterns_dict: Dictionary with seasonal data containing monthly_costs,
                quarterly_costs DataFrames and patterns list
            output_path: Path to output JSON file

        Creates JSON object with structure:
        {
            "monthly": [...],
            "quarterly": [...],
            "patterns": [...]
        }
        """
        # Handle None or empty dict
        if patterns_dict is None or len(patterns_dict) == 0:
            logger.warning("Empty patterns_dict provided for seasonal patterns JSON export")
            with open(output_path, 'w') as f:
                json.dump({}, f, indent=2)
            return

        # Build output structure
        output = {}

        # Convert monthly costs DataFrame to list
        if 'monthly_costs' in patterns_dict and patterns_dict['monthly_costs'] is not None:
            monthly_df = patterns_dict['monthly_costs']
            if len(monthly_df) > 0:
                output['monthly'] = self._clean_for_json(monthly_df.to_dict('records'))

        # Convert quarterly costs DataFrame to list
        if 'quarterly_costs' in patterns_dict and patterns_dict['quarterly_costs'] is not None:
            quarterly_df = patterns_dict['quarterly_costs']
            if len(quarterly_df) > 0:
                output['quarterly'] = self._clean_for_json(quarterly_df.to_dict('records'))

        # Include patterns list if available
        if 'patterns' in patterns_dict and patterns_dict['patterns'] is not None:
            output['patterns'] = patterns_dict['patterns']

        # Write to JSON with pretty printing
        with open(output_path, 'w') as f:
            json.dump(output, f, indent=2)

        logger.info(f"Exported seasonal patterns to {output_path}")

    def export_vendor_metrics_json(self, df: pd.DataFrame, output_path: Union[str, Path]) -> None:
        """
        Export vendor performance DataFrame to JSON.

        Args:
            df: DataFrame with vendor metrics (from vendor_analyzer.calculate_vendor_costs)
            output_path: Path to output JSON file

        Creates pretty-printed JSON array of vendor objects sorted by total_cost.
        """
        # Handle empty DataFrame
        if df is None or len(df) == 0:
            logger.warning("Empty DataFrame provided for vendor metrics JSON export")
            with open(output_path, 'w') as f:
                json.dump([], f, indent=2)
            return

        # Create a copy for export
        export_df = df.copy()

        # Sort by total_cost descending
        if 'total_cost' in export_df.columns:
            export_df = export_df.sort_values('total_cost', ascending=False)

        # Convert to list of dicts
        records = export_df.to_dict('records')

        # Clean NaN/Infinity values
        cleaned_records = self._clean_for_json(records)

        # Write to JSON with pretty printing
        with open(output_path, 'w') as f:
            json.dump(cleaned_records, f, indent=2)

        logger.info(f"Exported {len(cleaned_records)} vendor metrics to {output_path}")

    def export_failure_patterns_json(self, patterns_list: List[Dict[str, Any]], output_path: Union[str, Path]) -> None:
        """
        Export failure patterns to JSON.

        Args:
            patterns_list: List of pattern dictionaries from failure_pattern_analyzer
            output_path: Path to output JSON file

        Creates pretty-printed JSON array preserving all fields from input.
        """
        # Handle None or empty list
        if patterns_list is None or len(patterns_list) == 0:
            logger.warning("Empty patterns_list provided for failure patterns JSON export")
            with open(output_path, 'w') as f:
                json.dump([], f, indent=2)
            return

        # Clean for JSON (handle any NaN or special values)
        cleaned_list = self._clean_for_json(patterns_list)

        # Write to JSON with pretty printing
        with open(output_path, 'w') as f:
            json.dump(cleaned_list, f, indent=2)

        logger.info(f"Exported {len(cleaned_list)} failure patterns to {output_path}")

    def _clean_for_json(self, data: Union[List[Dict], Dict]) -> Union[List[Dict], Dict]:
        """
        Clean data for JSON serialization.

        Replaces NaN and Infinity values with None for valid JSON.
        Converts pandas Timestamp to ISO format strings.

        Args:
            data: List of dicts or dict to clean

        Returns:
            Cleaned data structure safe for JSON serialization
        """
        import math
        import numpy as np

        if isinstance(data, list):
            return [self._clean_for_json(item) for item in data]
        elif isinstance(data, dict):
            cleaned = {}
            for key, value in data.items():
                # Handle various special cases
                if isinstance(value, (float, np.floating)):
                    if math.isnan(value) or math.isinf(value):
                        cleaned[key] = None
                    else:
                        cleaned[key] = float(value)
                elif isinstance(value, (int, np.integer)):
                    cleaned[key] = int(value)
                elif isinstance(value, pd.Timestamp):
                    cleaned[key] = value.isoformat()
                elif pd.isna(value):
                    cleaned[key] = None
                elif isinstance(value, (list, dict)):
                    cleaned[key] = self._clean_for_json(value)
                else:
                    cleaned[key] = value
            return cleaned
        else:
            return data
