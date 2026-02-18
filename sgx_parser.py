import argparse

import tempfile
from pathlib import Path
from collections.abc import Sequence
from zipfile import ZipFile
from tqdm import tqdm

from converter.signavio_to_bpmn import convert_file


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
        json_files: set[Path] = {*json_root.rglob("model_*.json")} - {
            *json_root.rglob("*model_meta*.json")
        }

        # Call converter function directly
        for i, json_file in tqdm(enumerate(json_files)):
            output_file = out_dir / f"{json_file.stem}_{i}.bpmn"
            assert convert_file(
                json_file, output_file
            ), f"Conversion failed for {json_file}"

    print(f"Done, BPMN written to: {out_dir.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
