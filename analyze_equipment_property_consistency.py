#!/usr/bin/env python
import argparse
from pathlib import Path

import pandas as pd


def _clean_series(series: pd.Series) -> pd.Series:
    cleaned = series.astype("string").str.strip()
    cleaned = cleaned.where(cleaned != "", pd.NA)
    return cleaned


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check if an equipment name has consistent property values."
    )
    parser.add_argument("csv_path", type=Path, help="Path to CSV file")
    parser.add_argument(
        "--equipmentname",
        default="Fire Extinguisher",
        help='Equipment name to match (default: "Lift No. 1")',
    )
    parser.add_argument(
        "--equipment-column",
        default="equipmentname",
        help="Column name for equipment (default: equipmentname)",
    )
    parser.add_argument(
        "--property-column",
        default="property",
        help="Column name for property (default: property)",
    )
    parser.add_argument(
        "--property-code-column",
        default="property_code",
        help="Column name for property code (default: property_code)",
    )
    parser.add_argument(
        "--location-desc-column",
        default="location_desc",
        help="Column name for location description (default: location_desc)",
    )
    parser.add_argument(
        "--case-insensitive",
        action="store_true",
        help="Match equipment name case-insensitively",
    )
    args = parser.parse_args()

    if not args.csv_path.exists():
        print(f"File not found: {args.csv_path}")
        return 1

    usecols = [
        args.equipment_column,
        args.property_column,
        args.property_code_column,
        args.location_desc_column,
    ]

    try:
        df = pd.read_csv(
            args.csv_path,
            usecols=usecols,
            dtype="string",
            encoding="utf-8-sig",
            low_memory=False,
        )
    except ValueError:
        columns = pd.read_csv(args.csv_path, nrows=0).columns
        print("One or more columns not found.")
        print(f"Available columns: {', '.join(columns)}")
        return 1

    equip = _clean_series(df[args.equipment_column])
    property_vals = _clean_series(df[args.property_column])
    property_code_vals = _clean_series(df[args.property_code_column])
    location_desc_vals = _clean_series(df[args.location_desc_column])

    if args.case_insensitive:
        equip_match = equip.str.casefold() == args.equipmentname.casefold()
    else:
        equip_match = equip == args.equipmentname

    filtered = df.loc[equip_match].copy()
    if filtered.empty:
        print(f'No rows found for equipmentname: "{args.equipmentname}"')
        return 0

    filtered[args.property_column] = property_vals.loc[filtered.index]
    filtered[args.property_code_column] = property_code_vals.loc[filtered.index]
    filtered[args.location_desc_column] = location_desc_vals.loc[filtered.index]

    property_unique = (
        filtered[args.property_column].dropna().unique().tolist()
    )
    property_code_unique = (
        filtered[args.property_code_column].dropna().unique().tolist()
    )
    location_desc_unique = (
        filtered[args.location_desc_column].dropna().unique().tolist()
    )

    print(f'Equipment: "{args.equipmentname}"')
    print(f"Rows: {len(filtered)}")

    def report_column(label: str, values: list) -> None:
        if not values:
            print(f"{label}: no non-empty values")
            return
        if len(values) == 1:
            print(f"{label}: consistent ({values[0]})")
        else:
            joined = ", ".join(values)
            print(f"{label}: inconsistent ({len(values)} values) -> {joined}")

    report_column(args.property_column, property_unique)
    report_column(args.property_code_column, property_code_unique)
    report_column(args.location_desc_column, location_desc_unique)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
