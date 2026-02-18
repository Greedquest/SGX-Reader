#!/usr/bin/env python3
"""Analyze how many BPMN JSON files contain Signavio-specific elements."""

import json
import argparse
from pathlib import Path
from collections import defaultdict

DEFAULT_JSON_DIR = Path(__file__).parent / "json"

# Signavio-specific stencils that don't map to standard BPMN 2.0
SIGNAVIO_SPECIFIC_STENCILS = {
    'ITSystem',
    'processparticipant',
}

def collect_stencils_and_properties(data, stencils, has_glossary):
    """Recursively collect stencil IDs and check for glossary links."""
    if isinstance(data, dict):
        # Check stencil
        if 'stencil' in data and 'id' in data['stencil']:
            stencils.add(data['stencil']['id'])

        # Check for glossary links in properties
        if 'properties' in data:
            props = data['properties']
            for key, value in props.items():
                if 'glossary' in key.lower():
                    has_glossary[0] = True
                # Check if value contains glossary reference
                if isinstance(value, str) and 'glossary' in value.lower():
                    has_glossary[0] = True

        # Recurse into childShapes
        if 'childShapes' in data:
            for child in data['childShapes']:
                collect_stencils_and_properties(child, stencils, has_glossary)

def main():
    parser = argparse.ArgumentParser(
        description="Analyze Signavio-specific element usage in BPMN JSON files."
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

    json_files = list(json_dir.glob('*.json'))
    print(f"Analyzing {len(json_files)} BPMN JSON files...\n")

    # Track files by which Signavio elements they contain
    files_with_signavio = defaultdict(list)
    files_with_any_signavio = []
    clean_files = []

    for filepath in json_files:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            stencils = set()
            has_glossary = [False]
            collect_stencils_and_properties(data, stencils, has_glossary)

            # Check for Signavio-specific elements
            signavio_found = stencils & SIGNAVIO_SPECIFIC_STENCILS

            if signavio_found or has_glossary[0]:
                files_with_any_signavio.append(filepath)
                for stencil in signavio_found:
                    files_with_signavio[stencil].append(filepath)
                if has_glossary[0]:
                    files_with_signavio['glossary_links'].append(filepath)
            else:
                clean_files.append(filepath)

        except Exception as e:
            print(f"Error processing {filepath.name}: {e}")

    # Print results
    print("=" * 60)
    print("SIGNAVIO-SPECIFIC ELEMENTS ANALYSIS")
    print("=" * 60)

    print(f"\nFiles with Signavio-specific elements: {len(files_with_any_signavio)}")
    print(f"Clean BPMN files (no Signavio-specific): {len(clean_files)}")

    print("\nBreakdown by element type:")
    for element, files in sorted(files_with_signavio.items(), key=lambda x: -len(x[1])):
        print(f"  {element:25} : {len(files):4} files")

    # Show some example files with Signavio elements
    if files_with_any_signavio:
        print("\nExample files with Signavio-specific elements:")
        for f in files_with_any_signavio[:5]:
            print(f"  - {f.name}")

    print("\n" + "=" * 60)

    # Calculate overlap
    it_system_files = set(files_with_signavio.get('ITSystem', []))
    participant_files = set(files_with_signavio.get('processparticipant', []))
    glossary_files = set(files_with_signavio.get('glossary_links', []))

    if len(files_with_signavio) > 1:
        print("\nOverlap analysis:")
        if it_system_files and participant_files:
            overlap = it_system_files & participant_files
            print(f"  Files with both ITSystem AND processparticipant: {len(overlap)}")

        all_signavio = it_system_files | participant_files | glossary_files
        print(f"  Total unique files with any Signavio element: {len(all_signavio)}")

if __name__ == '__main__':
    main()
