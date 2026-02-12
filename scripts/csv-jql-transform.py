#!/usr/bin/env python3
"""Transform raw Venkat CSV files by inserting a Full Filter URL column.

Usage:
    python csv-jql-transform.py                          # process all CSVs in default original/ dir
    python csv-jql-transform.py -i path/to/input.csv     # process a single file
    python csv-jql-transform.py -d path/to/dir/           # process all CSVs in a directory
    python csv-jql-transform.py -o path/to/output/        # specify output directory
"""

import argparse
import csv
import os
import re
import sys
from pathlib import Path

JIRA_BASE_URL = "https://jira-sd.mc1.oracleiaas.com/issues/"
DEFAULT_INPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "docs", "venkat-csv", "original")
DEFAULT_OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "docs", "venkat-csv")
DEFAULT_JQL_DIR = os.path.join(os.path.dirname(__file__), "jql")


def to_jql_filename(category: str) -> str:
    """Convert a Category value to a JQL-friendly filename slug.

    E.g. 'CPV IB Jira: Pollara - IB Issues' -> 'cpv_ib_jira_pollara_ib_issues'
    """
    slug = category.lower()
    # Replace any non-alphanumeric character (except underscore) with underscore
    slug = re.sub(r"[^a-z0-9]+", "_", slug)
    # Strip leading/trailing underscores
    slug = slug.strip("_")
    return f"{slug}.jql"


def build_filter_url(filter_id: str) -> str:
    """Build a Jira filter URL from a numeric filter ID."""
    filter_id = filter_id.strip()
    if not filter_id:
        return ""
    return f"{JIRA_BASE_URL}?filter={filter_id}&mode=advanced"


def transform_csv(input_path: Path, output_path: Path, jql_dir: Path | None = None) -> None:
    """Read a raw CSV, insert Full Filter URL and JQL Filename columns, write transformed CSV.

    If jql_dir is provided, also write individual .jql files with the filter query.
    """
    with open(input_path, "r", newline="", encoding="utf-8-sig") as infile:
        reader = csv.reader(infile)
        header = next(reader)
        header = [h.strip() for h in header]

        if "Full Filter URL" in header:
            print(f"  SKIP (already transformed): {input_path}")
            return

        if "Filter" not in header or "Category" not in header:
            print(f"  SKIP (missing Filter or Category column): {input_path}")
            return

        filter_idx = header.index("Filter")
        category_idx = header.index("Category")
        new_header = (
            header[: filter_idx + 1]
            + ["Full Filter URL", "JQL Filename"]
            + header[filter_idx + 1 :]
        )

        rows = []
        for row in reader:
            row = [cell.strip() for cell in row]
            # Pad row if shorter than header
            while len(row) < len(header):
                row.append("")
            filter_val = row[filter_idx]
            category_val = row[category_idx]
            url = build_filter_url(filter_val)
            jql_name = to_jql_filename(category_val)
            new_row = (
                row[: filter_idx + 1]
                + [url, jql_name]
                + row[filter_idx + 1 :]
            )
            rows.append(new_row)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", newline="", encoding="utf-8") as outfile:
        writer = csv.writer(outfile, quoting=csv.QUOTE_MINIMAL)
        writer.writerow(new_header)
        writer.writerows(rows)

    print(f"  OK: {input_path.name} -> {output_path}")

    if jql_dir:
        jql_dir.mkdir(parents=True, exist_ok=True)
        # JQL Filename is at filter_idx + 2 in new_header (after Filter, Full Filter URL)
        jql_filename_idx = filter_idx + 2
        filter_id_idx = filter_idx
        jql_count = 0
        for row in rows:
            jql_name = row[jql_filename_idx]
            filter_id = row[filter_id_idx].strip()
            if not jql_name or not filter_id:
                continue
            jql_path = jql_dir / jql_name
            jql_path.write_text(f"filter = {filter_id}\n", encoding="utf-8")
            jql_count += 1
        print(f"  JQL: wrote {jql_count} .jql file(s) to {jql_dir}")


def main():
    parser = argparse.ArgumentParser(
        description="Transform raw CSV files by inserting a Jira Full Filter URL column."
    )
    parser.add_argument(
        "-i", "--input", type=str, default=None,
        help="Path to a single input CSV file"
    )
    parser.add_argument(
        "-d", "--input-dir", type=str, default=None,
        help=f"Directory of input CSVs (default: {DEFAULT_INPUT_DIR})"
    )
    parser.add_argument(
        "-o", "--output-dir", type=str, default=None,
        help=f"Output directory for transformed CSVs (default: {DEFAULT_OUTPUT_DIR})"
    )
    parser.add_argument(
        "--write-jql", action="store_true", default=False,
        help=f"Write individual .jql files to the JQL directory (default: {DEFAULT_JQL_DIR})"
    )
    parser.add_argument(
        "--jql-dir", type=str, default=None,
        help=f"Directory for .jql files (default: {DEFAULT_JQL_DIR}). Implies --write-jql."
    )
    args = parser.parse_args()

    output_dir = Path(args.output_dir) if args.output_dir else Path(DEFAULT_OUTPUT_DIR)
    jql_dir = None
    if args.jql_dir:
        jql_dir = Path(args.jql_dir)
    elif args.write_jql:
        jql_dir = Path(DEFAULT_JQL_DIR)

    if args.input:
        # Single file mode
        input_path = Path(args.input)
        if not input_path.exists():
            print(f"Error: {input_path} not found", file=sys.stderr)
            sys.exit(1)
        output_path = output_dir / input_path.name
        print(f"Transforming single file:")
        transform_csv(input_path, output_path, jql_dir=jql_dir)
    else:
        # Directory mode
        input_dir = Path(args.input_dir) if args.input_dir else Path(DEFAULT_INPUT_DIR)
        if not input_dir.is_dir():
            print(f"Error: {input_dir} is not a directory", file=sys.stderr)
            sys.exit(1)

        csv_files = sorted(input_dir.glob("*.csv"))
        if not csv_files:
            print(f"No CSV files found in {input_dir}")
            sys.exit(0)

        print(f"Transforming {len(csv_files)} file(s) from {input_dir}:")
        for csv_file in csv_files:
            output_path = output_dir / csv_file.name
            transform_csv(csv_file, output_path, jql_dir=jql_dir)

    print("Done.")


if __name__ == "__main__":
    main()
