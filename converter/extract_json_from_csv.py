#!/usr/bin/env python3
"""Extract Signavio model JSON documents from a CSV export."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path


def configure_csv_field_limit() -> None:
    """Raise CSV field size limit to support large JSON payloads."""
    limit = sys.maxsize
    while True:
        try:
            csv.field_size_limit(limit)
            return
        except OverflowError:
            limit //= 10
            if limit <= 0:
                raise


def sanitize_token(value: str, max_len: int | None = None) -> str:
    allowed = []
    for char in value:
        if char.isalnum() or char in {" ", "-", "_"}:
            allowed.append(char)
        else:
            allowed.append("_")
    sanitized = "".join(allowed).strip()
    if max_len is not None:
        sanitized = sanitized[:max_len]
    return sanitized


def is_empty(value: str | None) -> bool:
    return value is None or value.strip() == ""


def unique_path(path: Path) -> Path:
    if not path.exists():
        return path

    counter = 1
    while True:
        candidate = path.with_name(f"{path.stem}_{counter}{path.suffix}")
        if not candidate.exists():
            return candidate
        counter += 1


def build_filename(
    row: dict[str, str],
    row_index: int,
    id_column: str,
    name_column: str,
) -> str:
    raw_model_id = row.get(id_column, "")
    model_id = sanitize_token(raw_model_id) if not is_empty(raw_model_id) else f"unknown_{row_index}"
    if is_empty(model_id):
        model_id = f"unknown_{row_index}"

    raw_name = row.get(name_column, "")
    safe_name = sanitize_token(raw_name, max_len=50) if not is_empty(raw_name) else ""

    if safe_name:
        return f"{model_id}_{safe_name}.json"
    return f"{model_id}.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract JSON from a CSV column and save one JSON file per model.",
    )
    parser.add_argument(
        "--input-csv",
        type=Path,
        default=Path("1020000.csv"),
        help="Input CSV path (default: ./1020000.csv)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("json"),
        help="Directory for extracted JSON files (default: ./json)",
    )
    parser.add_argument(
        "--model-json-column",
        default="Model JSON",
        help="Column name containing serialized model JSON (default: 'Model JSON')",
    )
    parser.add_argument(
        "--id-column",
        default="Model ID",
        help="Column name used for model ID in output filename (default: 'Model ID')",
    )
    parser.add_argument(
        "--name-column",
        default="Name",
        help="Column name used for model name in output filename (default: 'Name')",
    )
    parser.add_argument(
        "--encoding",
        default="utf-8",
        help="CSV file encoding (default: utf-8)",
    )
    parser.add_argument(
        "--max-rows",
        type=int,
        default=None,
        help="Optional row limit for test runs",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite files when names collide (default: create unique suffix)",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress per-file output (summary still printed)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    input_csv: Path = args.input_csv
    output_dir: Path = args.output_dir

    if not input_csv.exists() or not input_csv.is_file():
        print(f"Input CSV not found: {input_csv}", file=sys.stderr)
        return 2

    configure_csv_field_limit()
    output_dir.mkdir(parents=True, exist_ok=True)

    written = 0
    skipped_empty = 0
    parse_errors = 0
    other_errors = 0

    with input_csv.open("r", encoding=args.encoding, newline="") as handle:
        reader = csv.DictReader(handle)
        required_columns = {args.model_json_column, args.id_column, args.name_column}
        missing_columns = [column for column in required_columns if column not in reader.fieldnames]
        if missing_columns:
            print(
                "Missing required CSV columns: " + ", ".join(sorted(missing_columns)),
                file=sys.stderr,
            )
            return 2

        for row_index, row in enumerate(reader):
            if args.max_rows is not None and row_index >= args.max_rows:
                break

            model_json_str = row.get(args.model_json_column, "")
            if is_empty(model_json_str):
                skipped_empty += 1
                continue

            try:
                model_json = json.loads(model_json_str)
            except json.JSONDecodeError as exc:
                parse_errors += 1
                print(f"Row {row_index}: JSON parse error: {exc}", file=sys.stderr)
                continue

            try:
                filename = build_filename(row, row_index, args.id_column, args.name_column)
                output_path = output_dir / filename
                if not args.overwrite:
                    output_path = unique_path(output_path)

                with output_path.open("w", encoding="utf-8") as output_handle:
                    json.dump(model_json, output_handle, indent=2, ensure_ascii=False)

                written += 1
                if not args.quiet:
                    print(f"Saved: {output_path.name}")

            except Exception as exc:  # noqa: BLE001
                other_errors += 1
                print(f"Row {row_index}: write error: {exc}", file=sys.stderr)

    print(
        "Done. "
        f"Written: {written}, "
        f"Skipped empty: {skipped_empty}, "
        f"Parse errors: {parse_errors}, "
        f"Other errors: {other_errors}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
