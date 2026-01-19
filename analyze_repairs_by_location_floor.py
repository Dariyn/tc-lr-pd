#!/usr/bin/env python
import argparse
import re
from pathlib import Path
from typing import List, Optional, Tuple

import pandas as pd


FLOOR_PATTERNS = [
    re.compile(r"(?P<floor>[A-Za-z0-9]+/F)", re.IGNORECASE),
    re.compile(r"(?P<floor>\b\d+F\b)", re.IGNORECASE),
    re.compile(r"(?P<floor>\b(?:UG|LG)\b)", re.IGNORECASE),
    re.compile("(?P<floor>\\d+\\s*\u6a13)"),
]
LEADING_SEPARATORS_RE = re.compile(r"^[\s\-,/]+")
TRAILING_SEPARATORS_RE = re.compile(r"[\s\-,/]+$")


def _clean_series(series: pd.Series) -> pd.Series:
    cleaned = series.astype("string").str.strip()
    cleaned = cleaned.where(cleaned != "", pd.NA)
    return cleaned


def _normalize_floor(floor: str) -> str:
    return re.sub(r"\s+", "", floor).upper()


def _extract_floor(text: str) -> Tuple[Optional[str], Optional[int], Optional[int]]:
    matches: List[Tuple[int, int, str]] = []
    for pattern in FLOOR_PATTERNS:
        match = pattern.search(text)
        if match:
            matches.append((match.start(), match.end(), match.group("floor")))
    if not matches:
        return None, None, None
    start, end, floor = min(matches, key=lambda item: (item[0], -(item[1] - item[0])))
    return _normalize_floor(floor), start, end


def parse_location_desc(value: str) -> Tuple[object, object, object]:
    if pd.isna(value):
        return pd.NA, pd.NA, pd.NA
    text = str(value).strip()
    if not text:
        return pd.NA, pd.NA, pd.NA
    floor, start, end = _extract_floor(text)
    if floor is None or start is None or end is None:
        return text, pd.NA, pd.NA
    location = text[:start].strip()
    location = TRAILING_SEPARATORS_RE.sub("", location).strip()
    remainder = text[end:].strip()
    remainder = LEADING_SEPARATORS_RE.sub("", remainder).strip()
    if not location:
        location = pd.NA
    if not remainder:
        remainder = pd.NA
    return location, floor, remainder


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Analyze repair counts by parsed location name and floor."
    )
    parser.add_argument("csv_path", type=Path, help="Path to CSV file")
    parser.add_argument(
        "--location-desc-column",
        default="location_desc",
        help="Column name for location description (default: location_desc)",
    )
    parser.add_argument(
        "--amount-column",
        default="PO_AMOUNT",
        help="Column name for amount to sum (default: PO_AMOUNT)",
    )
    parser.add_argument(
        "--include-unparsed",
        action="store_true",
        help="Include rows with unparsed floor values in results.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional output CSV path for the grouped results.",
    )
    args = parser.parse_args()

    if not args.csv_path.exists():
        print(f"File not found: {args.csv_path}")
        return 1

    try:
        df = pd.read_csv(
            args.csv_path,
            usecols=[args.location_desc_column, args.amount_column],
            dtype="string",
            encoding="utf-8-sig",
            low_memory=False,
        )
    except ValueError:
        columns = pd.read_csv(args.csv_path, nrows=0).columns
        print(f"Column '{args.location_desc_column}' not found.")
        print(f"Available columns: {', '.join(columns)}")
        return 1

    location_desc = _clean_series(df[args.location_desc_column])
    amount_series = _clean_series(df[args.amount_column])
    amount_numeric = (
        amount_series.astype("string")
        .str.replace(",", "", regex=False)
        .str.replace(r"[^0-9.\-]", "", regex=True)
    )
    amount_numeric = pd.to_numeric(amount_numeric, errors="coerce").fillna(0)
    parsed = location_desc.apply(parse_location_desc)
    parsed_df = pd.DataFrame(
        parsed.tolist(),
        columns=["location_name", "floor", "location_detail"],
    )
    parsed_df["amount"] = amount_numeric

    total_rows = len(parsed_df)
    parsed_floor_mask = parsed_df["floor"].notna()
    parsed_floor_count = int(parsed_floor_mask.sum())
    unparsed_floor_count = total_rows - parsed_floor_count

    report_df = parsed_df.copy()
    if not args.include_unparsed:
        report_df = report_df.loc[parsed_floor_mask].copy()
    else:
        report_df["floor"] = report_df["floor"].fillna("UNKNOWN")
    report_df["location_name"] = report_df["location_name"].fillna("UNKNOWN")
    report_df["location_detail"] = report_df["location_detail"].fillna("")

    if report_df.empty:
        print("No rows available after filtering.")
        print(f"Rows: {total_rows}")
        print(f"Parsed floors: {parsed_floor_count}")
        print(f"Unparsed floors: {unparsed_floor_count}")
        return 0

    counts = (
        report_df.groupby(
            ["location_name", "floor", "location_detail"], dropna=False, as_index=False
        )
        .agg(
            repair_count=("amount", "size"),
            total_amount=("amount", "sum"),
        )
        .sort_values("repair_count", ascending=False)
    )
    counts["total_amount"] = counts["total_amount"].round(2)
    counts = counts[
        ["location_name", "floor", "location_detail", "total_amount", "repair_count"]
    ]

    print(f"Rows: {total_rows}")
    print(f"Parsed floors: {parsed_floor_count}")
    print(f"Unparsed floors: {unparsed_floor_count}")
    print()
    print(counts.to_string(index=False))

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        counts.to_csv(args.output, index=False, encoding="utf-8-sig")
        print()
        print(f"Saved results to: {args.output}")
        positive_counts = counts.loc[counts["total_amount"] > 0].copy()
        positive_output = args.output.with_name(
            f"{args.output.stem}_amount_gt_0{args.output.suffix}"
        )
        positive_counts.to_csv(positive_output, index=False, encoding="utf-8-sig")
        print(f"Saved positive amount results to: {positive_output}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
