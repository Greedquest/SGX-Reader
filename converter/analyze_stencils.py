#!/usr/bin/env python3
"""Analyze all stencil types used in BPMN JSON files."""

import json
import argparse
from pathlib import Path
from collections import Counter

DEFAULT_JSON_DIR = Path(__file__).parent / "json"

def collect_stencils(data, stencils):
    """Recursively collect all stencil IDs from shapes."""
    if isinstance(data, dict):
        if 'stencil' in data and 'id' in data['stencil']:
            stencils.append(data['stencil']['id'])
        if 'childShapes' in data:
            for child in data['childShapes']:
                collect_stencils(child, stencils)

def main():
    parser = argparse.ArgumentParser(
        description="Analyze stencil type frequencies in Signavio BPMN JSON files."
    )
    parser.add_argument(
        "json_dir",
        nargs="?",
        type=Path,
        default=DEFAULT_JSON_DIR,
        help="Directory containing Signavio JSON files (default: ./json)",
    )
    args = parser.parse_args()
    json_dir = args.json_dir

    if not json_dir.exists() or not json_dir.is_dir():
        print(f"Error: JSON directory not found: {json_dir}")
        return

    stencil_counter = Counter()

    for filepath in json_dir.glob('*.json'):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            stencils = []
            collect_stencils(data, stencils)
            stencil_counter.update(stencils)
        except Exception as e:
            print(f"Error processing {filepath.name}: {e}")

    print("=" * 60)
    print("STENCIL TYPES FOUND IN BPMN FILES")
    print("=" * 60)

    for stencil, count in stencil_counter.most_common():
        print(f"{stencil:45} : {count:6}")

    print("=" * 60)
    print(f"Total unique stencil types: {len(stencil_counter)}")

if __name__ == '__main__':
    main()
