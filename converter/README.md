# Signavio JSON to BPMN 2.0 Converter

Convert SAP Signavio BPMN JSON exports into standards-compliant BPMN 2.0 XML.

## Why this project exists

Signavio exports are useful but tool-specific. This converter makes those process models portable by translating Signavio JSON into BPMN 2.0 XML that can be opened and validated in standard BPMN tooling.

The implementation focuses on practical interoperability details that are usually the source of broken exports:
- mapping Signavio stencils to BPMN 2.0 elements
- resolving flow references and process ownership
- handling nested relative coordinates and BPMNDI bounds
- generating valid XML structure and strict BPMN element ordering

## Dataset and test context

Testing and conversion were performed on a subset of the SAP-SAM dataset (`1020000.csv`):
- https://github.com/signavio/sap-sam/tree/main

From that subset:
- `904` Signavio JSON files were converted
- `904` BPMN XML files were produced

## What is included in this package

- `signavio_to_bpmn.py`: main converter
- `extract_json_from_csv.py`: script used to extract Signavio JSON files from `1020000.csv`
- `bpmn_syntactic_validation.py`: XSD validator for generated BPMN XML files
- `schema/`: BPMN 2.0 XSD files used for validation workflows
- `bpmn/`: converted BPMN XML outputs
- helper analysis scripts:
  - `analyze_and_clean.py` filters to keep only standard BPMN process diagrams (removes DMN, EPC, Choreography, Conversation, etc.)
  - `analyze_stencils.py` analyze all stencil types used in BPMN JSON files
  - `analyze_signavio_elements.py` analyze how many BPMN JSON files contain Signavio-specific elements
  - `extract_stencils.py` extracts all unique stencil types from JSON files
  - `compare_mappings.py` compares extracted types with current mapping
  - `verify_event_definitions.py` verifies event definition coverage
- `STENCIL_MAPPING_REFERENCE.md` complete reference documentation

## What is intentionally not included

- `json/` input folder

If you want to reproduce conversions, prepare your own Signavio JSON files locally and point the converter to that directory.

## Requirements

- Python 3.9+ for conversion and analysis scripts
- `lxml` only for XSD validation (`bpmn_syntactic_validation.py`)

Install validator dependency:

```bash
pip install lxml
```

## Usage

### Extract JSON files from `1020000.csv` (script)

Use `extract_json_from_csv.py` to generate intermediate `json/` files from the SAP-SAM subset CSV.

```bash
python extract_json_from_csv.py \
  --input-csv 1020000.csv \
  --output-dir json
```

Useful optional flags:
- `--max-rows N` for quick smoke tests
- `--overwrite` to overwrite colliding filenames instead of creating suffixes
- `--quiet` to suppress per-file logs

### Convert one JSON file

```bash
python signavio_to_bpmn.py /path/to/model.json -o /path/to/model.bpmn
```

### Convert a directory of JSON files

```bash
python signavio_to_bpmn.py /path/to/json_dir -o /path/to/output_bpmn_dir
```

If `-o` is omitted for a directory input, output defaults to a sibling `bpmn_xml/` folder.

### Verbose mode

```bash
python signavio_to_bpmn.py /path/to/json_dir -v
```

## XSD Validation

Validate BPMN files against the BPMN 2.0 schema set in `schema/`:

```bash
python bpmn_syntactic_validation.py \
  --input-dir bpmn \
  --schema-dir schema \
  --output validationOutput.csv
```

CSV columns:
- `ModelName`
- `Validation` (`valid` or `invalid`)
- `Exception` (schema or XML parsing message)

Current package result (`bpmn/`):
- `901` valid
- `3` invalid

## Known scope limits

The converter is focused on standard BPMN process diagrams. Choreography and Conversation subtypes are typically filtered out before conversion because they require additional XML structures not fully covered in this implementation.
