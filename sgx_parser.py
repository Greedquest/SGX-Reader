from __future__ import annotations

import argparse
import json
import tempfile
from collections.abc import Sequence
from pathlib import Path
from zipfile import ZipFile

import cfgv
from converter.signavio_to_bpmn import convert_file
from tqdm import tqdm


METADATA_SCHEMA = cfgv.Map(
    "ModelMetadata", "name", cfgv.Required("name", cfgv.check_string)
)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("sgx_path", help="Path to .sgx export")
    parser.add_argument("--out", default="bpmn_xml", help="Output directory")
    args = parser.parse_args(argv)
    sgx = Path(args.sgx_path)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)

        # SGX is typically a TAR archive
        with ZipFile(sgx, "r") as tf:
            tf.extractall(td_path)

        # Find JSON model files
        json_root = td_path
        json_files = {*json_root.rglob("model_*.json")} - {
            *json_root.rglob("*model_meta*.json"),
        }

        # Call converter function directly
        for i, json_file in tqdm(enumerate(json_files), total=len(json_files)):
            metadata_path = json_file.parent / "model_meta.json"
            assert metadata_path.exists(), f"{json_file} has no associated metadata"
            metadata: dict[str, str] = cfgv.load_from_filename(
                metadata_path,
                METADATA_SCHEMA,
                json.loads,
            )

            output_file = out_dir / f"{metadata['name']}.bpmn"
            assert convert_file(
                json_file,
                output_file,
            ), f"Conversion failed for {json_file}"

    print(f"Done, BPMN written to: {out_dir.resolve().as_uri()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
