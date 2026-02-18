#!/usr/bin/env python3
"""
Extract all unique stencil types from Signavio BPMN JSON files.

This script scans all JSON files in the json/ directory and extracts
every unique stencil ID used, helping ensure complete BPMN mapping coverage.
"""

import json
import argparse
from pathlib import Path
from collections import Counter


def extract_stencils_recursive(shape, stencils: Counter, parent_stencil=None):
    """Recursively extract stencil IDs from a shape and its children."""
    if not isinstance(shape, dict):
        return

    # Extract stencil ID
    stencil = shape.get('stencil', {})
    if isinstance(stencil, dict):
        stencil_id = stencil.get('id')
        if stencil_id:
            stencils[stencil_id] += 1

    # Process child shapes
    children = shape.get('childShapes', [])
    if isinstance(children, list):
        for child in children:
            extract_stencils_recursive(child, stencils, stencil_id)


def main():
    parser = argparse.ArgumentParser(
        description="Extract all unique stencil IDs from Signavio BPMN JSON files."
    )
    parser.add_argument(
        "json_dir",
        nargs="?",
        type=Path,
        default=Path(__file__).parent / "json",
        help="Directory containing Signavio JSON files (default: ./json)",
    )
    args = parser.parse_args()
    json_dir = args.json_dir

    if not json_dir.exists():
        print(f"Error: Directory {json_dir} does not exist")
        return

    all_stencils = Counter()
    files_processed = 0
    files_with_errors = 0

    json_files = list(json_dir.glob('*.json'))
    print(f"Found {len(json_files)} JSON files to process...\n")

    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            extract_stencils_recursive(data, all_stencils)
            files_processed += 1

        except Exception as e:
            files_with_errors += 1
            print(f"Error processing {json_file.name}: {e}")

    # Sort by frequency (most common first)
    sorted_stencils = sorted(all_stencils.items(), key=lambda x: (-x[1], x[0]))

    print(f"Processed {files_processed} files ({files_with_errors} errors)\n")
    print(f"Found {len(all_stencils)} unique stencil types:\n")
    print("=" * 60)
    print(f"{'Stencil ID':<45} {'Count':>10}")
    print("=" * 60)

    for stencil_id, count in sorted_stencils:
        print(f"{stencil_id:<45} {count:>10,}")

    print("=" * 60)
    print(f"\nTotal stencil occurrences: {sum(all_stencils.values()):,}")

    # Also output as a simple list for easy copying
    print("\n\n--- Plain list (for mapping) ---\n")
    for stencil_id, _ in sorted_stencils:
        print(stencil_id)

    # Save to file
    output_file = Path(__file__).parent / 'stencil_types.txt'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# Unique Signavio Stencil Types\n")
        f.write(f"# Extracted from {files_processed} JSON files\n")
        f.write(f"# Total unique types: {len(all_stencils)}\n\n")

        f.write("# Format: stencil_id, occurrence_count\n\n")
        for stencil_id, count in sorted_stencils:
            f.write(f"{stencil_id},{count}\n")

    print(f"\nResults saved to: {output_file}")


if __name__ == '__main__':
    main()
