#!/usr/bin/env python3
"""Validate BPMN XML files against the BPMN 2.0 XSD schema set."""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

try:
    from lxml import etree
except ImportError:  # pragma: no cover - runtime dependency check
    print("Missing dependency: lxml. Install with 'pip install lxml'.", file=sys.stderr)
    sys.exit(1)


class LocalSchemaResolver(etree.Resolver):
    def __init__(self, schema_dir: Path) -> None:
        super().__init__()
        self.schema_dir = schema_dir

    def resolve(self, url, pubid, context):  # type: ignore[override]
        candidate = self.schema_dir / url
        if candidate.exists():
            return self.resolve_filename(str(candidate), context)
        return None


def build_schema(schema_dir: Path) -> etree.XMLSchema:
    entry = schema_dir / "BPMN20.xsd"
    if not entry.exists():
        raise FileNotFoundError(f"Entry XSD not found: {entry}")

    parser = etree.XMLParser(resolve_entities=False, no_network=True)
    parser.resolvers.add(LocalSchemaResolver(schema_dir))
    schema_doc = etree.parse(str(entry), parser)
    return etree.XMLSchema(schema_doc)


def iter_model_files(input_dir: Path) -> list[Path]:
    return sorted(
        path
        for path in input_dir.iterdir()
        if path.is_file() and path.suffix.lower() in {".bpmn", ".xml"}
    )


def normalize_message(message: str) -> str:
    return " ".join(message.replace("\r", " ").replace("\n", " ").split())


def validate_files(input_dir: Path, schema: etree.XMLSchema, output_path: Path) -> tuple[int, int]:
    valid_count = 0
    invalid_count = 0
    parser = etree.XMLParser(resolve_entities=False, no_network=True)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["ModelName", "Validation", "Exception"])

        for file_path in iter_model_files(input_dir):
            try:
                doc = etree.parse(str(file_path), parser)
                if schema.validate(doc):
                    writer.writerow([file_path.name, "valid", ""])
                    valid_count += 1
                else:
                    error = schema.error_log.last_error
                    message = error.message if error is not None else "Schema validation failed"
                    writer.writerow([file_path.name, "invalid", normalize_message(message)])
                    invalid_count += 1
            except Exception as exc:  # noqa: BLE001
                writer.writerow([file_path.name, "invalid", normalize_message(str(exc))])
                invalid_count += 1

    return valid_count, invalid_count


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate BPMN models and write validationOutput.csv"
    )
    parser.add_argument(
        "--input-dir",
        required=True,
        type=Path,
        help="Directory containing BPMN/XML files to validate",
    )
    parser.add_argument(
        "--schema-dir",
        type=Path,
        default=Path(__file__).resolve().parent / "schema",
        help="Directory containing BPMN XSD schema files (default: ./schema)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).resolve().parent / "validationOutput.csv",
        help="Output CSV path (default: ./validationOutput.csv)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    input_dir = args.input_dir.resolve()
    schema_dir = args.schema_dir.resolve()
    output_path = args.output.resolve()

    if not input_dir.exists() or not input_dir.is_dir():
        print(f"Input directory not found: {input_dir}", file=sys.stderr)
        return 2
    if not schema_dir.exists() or not schema_dir.is_dir():
        print(f"Schema directory not found: {schema_dir}", file=sys.stderr)
        return 2

    schema = build_schema(schema_dir)
    valid_count, invalid_count = validate_files(input_dir, schema, output_path)
    print(
        f"Validation complete: {valid_count} valid, {invalid_count} invalid. "
        f"CSV written to {output_path}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
