#!/usr/bin/env python3
"""Run local inference using the project's bundled model loader.

This script imports `model.deployment.model_server` (which attempts to load `model.joblib` or
an XGBoost model from `model/output/model.tar.gz`) and exposes a small CLI to predict one or
multiple URLs without starting the FastAPI server.

Usage:
  python scripts/run_inference_local.py --url "http://example.com/login"
  python scripts/run_inference_local.py --file urls.txt

Outputs JSON lines with fields: url, prediction, confidence
"""

import argparse
import json
from typing import Iterable

import importlib
import importlib.util
from pathlib import Path

# Try a normal package import first, but fall back to loading the file directly if the
# repository is not installed as a package (no __init__.py under model/).
try:
    from model.deployment import model_server
except Exception:
    # fallback: load model/deployment/model_server.py as a module
    ms_path = Path(__file__).resolve().parents[1] / 'model' / 'deployment' / 'model_server.py'
    if not ms_path.exists():
        raise SystemExit(f"model_server not found at expected path: {ms_path}")
    spec = importlib.util.spec_from_file_location('model_server', str(ms_path))
    model_server = importlib.util.module_from_spec(spec)
    loader = spec.loader
    assert loader is not None
    loader.exec_module(model_server)


def extract_features(url: str):
    # Keep the same featurization as model_server
    return [len(url), url.count('.'), url.count('-'), url.count('@'), int('https' in url), int('login' in url)]


def predict_single(model, url: str):
    X = extract_features(url)
    import numpy as np
    X_arr = np.array(X).reshape(1, -1)

    if model is None:
        return {'url': url, 'prediction': 'error', 'confidence': 0.0}

    if hasattr(model, 'predict_proba'):
        proba = model.predict_proba(X_arr)
        # assume second column is positive class
        score = float(proba[0,1]) if proba.shape[1] > 1 else float(proba[0,0])
        label = 'phishing' if score > 0.5 else 'legit'
    else:
        pred = model.predict(X_arr)
        label = 'phishing' if int(pred[0]) == 1 else 'legit'
        score = float(pred[0])

    return {'url': url, 'prediction': label, 'confidence': round(score, 6)}


def urls_from_file(path: str) -> Iterable[str]:
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            u = line.strip()
            if u:
                yield u


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--url', '-u', action='append', help='URL to predict (can be passed multiple times)')
    p.add_argument('--file', '-f', help='File with one URL per line')
    args = p.parse_args()

    urls = []
    if args.url:
        urls.extend(args.url)
    if args.file:
        urls.extend(list(urls_from_file(args.file)))

    if not urls:
        p.print_help()
        raise SystemExit(1)

    model = model_server.model

    for u in urls:
        out = predict_single(model, u)
        print(json.dumps(out))


if __name__ == '__main__':
    main()
