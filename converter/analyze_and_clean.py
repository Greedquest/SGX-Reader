#!/usr/bin/env python3
"""
Analyze Signavio JSON files and filter to standard BPMN process diagrams.

Deletes non-BPMN files (DMN, EPC, etc.) and unsupported BPMN subtypes
(Choreography, Conversation) after confirmation. These subtypes require
different XML structures that aren't fully supported by the converter.
"""

import json
import os
import argparse
from pathlib import Path
from collections import defaultdict

DEFAULT_JSON_DIR = Path(__file__).parent / "json"

def get_diagram_type(filepath):
    """Determine diagram type from stencilset namespace.

    Note: BPMN Choreography and Conversation diagrams are categorized separately
    because they require different XML structure that isn't fully supported.
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        stencilset = data.get('stencilset', {})
        namespace = stencilset.get('namespace', '')
        namespace_lower = namespace.lower()

        # Check for BPMN subtypes first (more specific matches)
        if 'bpmn2.0choreography' in namespace_lower or 'bpmn2.0chor' in namespace_lower:
            return 'BPMN_Choreography'
        elif 'bpmn2.0conversation' in namespace_lower or 'bpmn2.0conv' in namespace_lower:
            return 'BPMN_Conversation'
        elif 'bpmn2.0' in namespace_lower or 'bpmn' in namespace_lower:
            return 'BPMN'
        elif 'dmn' in namespace_lower:
            return 'DMN'
        elif 'epc' in namespace_lower:
            return 'EPC'
        elif 'uml' in namespace_lower:
            return 'UML'
        elif 'archimate' in namespace_lower:
            return 'ArchiMate'
        elif 'organigram' in namespace_lower or 'orgchart' in namespace_lower:
            return 'OrgChart'
        elif 'valuechain' in namespace_lower:
            return 'ValueChain'
        else:
            # Return the namespace for unknown types
            return f'Other ({namespace})'
    except Exception as e:
        return f'Error ({str(e)[:50]})'

def main():
    parser = argparse.ArgumentParser(
        description="Analyze Signavio JSON files and keep only standard BPMN process diagrams."
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

    # Collect all JSON files
    json_files = list(json_dir.glob('*.json'))
    total_files = len(json_files)

    print(f"Analyzing {total_files} JSON files in {json_dir}\n")

    # Categorize files
    categories = defaultdict(list)

    for filepath in json_files:
        diagram_type = get_diagram_type(filepath)
        categories[diagram_type].append(filepath)

    # Print summary
    print("=" * 60)
    print("DIAGRAM TYPE SUMMARY")
    print("=" * 60)

    for dtype, files in sorted(categories.items(), key=lambda x: -len(x[1])):
        print(f"{dtype:40} : {len(files):5} files")

    print("=" * 60)
    print(f"{'TOTAL':40} : {total_files:5} files")
    print("=" * 60)

    # Identify files to keep (only standard BPMN process diagrams)
    # BPMN_Choreography and BPMN_Conversation are excluded because they require
    # different XML structure (participantRef, conversation elements) not fully supported
    bpmn_files = categories.get('BPMN', [])
    files_to_delete = []
    for dtype, files in categories.items():
        if dtype != 'BPMN':
            files_to_delete.extend(files)

    print(f"\nBPMN process files to KEEP: {len(bpmn_files)}")
    print(f"Files to DELETE: {len(files_to_delete)}")

    if files_to_delete:
        print("\nFiles to delete by type:")
        for dtype, files in sorted(categories.items()):
            if dtype != 'BPMN':
                note = " (unsupported BPMN subtype)" if dtype.startswith('BPMN_') else ""
                print(f"  {dtype}: {len(files)} files{note}")

        # Ask for confirmation
        response = input("\nDelete all non-standard BPMN files? (yes/no): ").strip().lower()

        if response == 'yes':
            deleted_count = 0
            for filepath in files_to_delete:
                try:
                    os.remove(filepath)
                    deleted_count += 1
                except Exception as e:
                    print(f"Error deleting {filepath.name}: {e}")

            print(f"\nDeleted {deleted_count} files.")
            print(f"Remaining BPMN process files: {len(bpmn_files)}")
        else:
            print("\nNo files were deleted.")
    else:
        print("\nAll files are standard BPMN process diagrams - nothing to delete.")

if __name__ == '__main__':
    main()
