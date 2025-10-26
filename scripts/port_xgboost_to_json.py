#!/usr/bin/env python3
"""Port an XGBoost model packaged in a SageMaker-style tar.gz to JSON (and UBJ if supported).

This script will:
- If given a tar.gz artifact, extract it and look for `xgboost-model`.
- Load the xgboost Booster and re-save it as JSON.
- Optionally attempt to save as UBJ if XGBoost in this environment supports it.

Usage (PowerShell):
  python .\scripts\port_xgboost_to_json.py --artifact model\output\model.tar.gz --out model\output\model.json

Requirements: xgboost installed in the Python environment where this runs.
"""

import argparse
from pathlib import Path
import tarfile
import sys


def extract_artifact(artifact: Path, extract_to: Path) -> Path:
    """Extract tar.gz artifact and return path to xgboost-model file if found."""
    if not artifact.exists():
        raise FileNotFoundError(f"Artifact not found: {artifact}")
    extract_to.mkdir(parents=True, exist_ok=True)
    with tarfile.open(artifact, 'r:gz') as tf:
        tf.extractall(path=extract_to)
    candidate = extract_to / 'xgboost-model'
    if candidate.exists():
        return candidate
    # fallback: find any file in extract_to
    files = list(extract_to.iterdir())
    if files:
        return files[0]
    raise FileNotFoundError(f"No files found in extracted artifact {artifact}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--artifact', required=True, help='Path to model artifact (tar.gz) or xgboost-model file')
    parser.add_argument('--out', required=True, help='Output path for JSON model (e.g. model/output/model.json)')
    parser.add_argument('--ubj', action='store_true', help='Also attempt to save UBJ (if supported by xgboost)')
    args = parser.parse_args()

    artifact = Path(args.artifact)
    out_path = Path(args.out)

    try:
        import xgboost as xgb
    except Exception as e:
        print("ERROR: xgboost is not installed in this environment. Install it first:")
        print("  pip install xgboost")
        raise SystemExit(1)

    # Determine input model file
    if artifact.suffixes[-2:] == ['.tar', '.gz'] or artifact.suffix == '.tgz':
        extracted = extract_artifact(artifact, artifact.parent)
        model_file = extracted
    else:
        model_file = artifact

    print(f"Loading XGBoost model from: {model_file}")
    booster = xgb.Booster()
    try:
        booster.load_model(str(model_file))
    except Exception as e:
        print(f"Failed to load model: {e}")
        raise

    # Save JSON
    out_path.parent.mkdir(parents=True, exist_ok=True)
    json_path = out_path
    print(f"Saving JSON model to: {json_path}")
    booster.save_model(str(json_path))

    # Optionally attempt UBJ
    if args.ubj:
        ubj_path = out_path.with_suffix('.ubj')
        try:
            print(f"Attempting to save UBJ model to: {ubj_path}")
            # Some xgboost builds understand .ubj extension in save_model; try it.
            booster.save_model(str(ubj_path))
            print("UBJ save attempted (check file).")
        except Exception as e:
            print(f"UBJ save failed: {e}")

    print("Done.")


if __name__ == '__main__':
    main()
