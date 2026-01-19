#!/usr/bin/env python
import argparse
from pathlib import Path

import pandas as pd


DATE_FORMAT = "%d%m%Y"  # ddmmyyyy


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Analyze create_date_yyyymmdd (ddmmyyyy) and report date range."
    )
    parser.add_argument("csv_path", type=Path, help="Path to CSV file")
    parser.add_argument(
        "--column",
        default="create_date_yyyymmdd",
        help="Column to analyze (default: create_date_yyyymmdd)",
    )
    args = parser.parse_args()

    if not args.csv_path.exists():
        print(f"File not found: {args.csv_path}")
        return 1

    try:
        df = pd.read_csv(
            args.csv_path,
            usecols=[args.column],
            dtype={args.column: "string"},
            encoding="utf-8-sig",
            low_memory=False,
        )
    except ValueError:
        columns = pd.read_csv(args.csv_path, nrows=0).columns
        print(f"Column '{args.column}' not found.")
        print(f"Available columns: {', '.join(columns)}")
        return 1

    raw = df[args.column].dropna().astype(str).str.strip()
    cleaned = raw.str.replace(r"\.0$", "", regex=True)
    cleaned = cleaned.str.replace(r"[^0-9]", "", regex=True)
    cleaned = cleaned[cleaned != ""]

    parsed = pd.to_datetime(cleaned, format=DATE_FORMAT, errors="coerce")
    valid = parsed.dropna()

    print(f"Column: {args.column}")
    print(f"Non-empty values: {len(cleaned)}")
    print(f"Invalid values: {parsed.isna().sum()}")

    if valid.empty:
        print("No valid dates found.")
        return 0

    min_date = valid.min()
    max_date = valid.max()
    print(f"Date range: {min_date:%d%m%Y} to {max_date:%d%m%Y}")
    print(f"Date range (ISO): {min_date.date()} to {max_date.date()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
