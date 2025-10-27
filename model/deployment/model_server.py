""""Model server for phishing URL detection using FastAPI.
# if venv is set up
.\.venv\Scripts\python -m uvicorn model.deployment.model_server:app --host 127.0.0.1 --port 8000
# PowerShell
Invoke-RestMethod -Uri http://127.0.0.1:8000/predict -Method POST -ContentType 'application/json' -Body '{"url":"http://example.com/login"}'
"""

from fastapi import FastAPI
from pydantic import BaseModel
import joblib
import numpy as np
import tarfile
from pathlib import Path
import logging
try:
    import xgboost as xgb
except Exception:
    xgb = None

LOG = logging.getLogger(__name__)


class InputSchema(BaseModel):
    url: str


class OutputSchema(BaseModel):
    url: str
    prediction: str
    confidence: float


app = FastAPI()

MODEL_PATH = 'model.joblib'
JSON_MODEL = Path('model/output/model.json')
DEFAULT_SAGEMAKER_MODEL = Path('model/output/model.tar.gz')


class XGBWrapper:
    """Wrap an xgboost.Booster to provide predict / predict_proba like sklearn."""
    def __init__(self, booster):
        self.booster = booster

    def predict(self, X):
        dmat = xgb.DMatrix(X)
        preds = self.booster.predict(dmat)
        return (preds > 0.5).astype(int)

    def predict_proba(self, X):
        dmat = xgb.DMatrix(X)
        preds = self.booster.predict(dmat)
        probs = np.vstack([1 - preds, preds]).T
        return probs


def _load_xgboost_from_s3_artifact(artifact_path: Path):
    """If artifact_path contains an xgboost-model file (SageMaker convention), extract and load it."""
    if not artifact_path.exists():
        return None
    tmp_dir = Path('model/output')
    try:
        with tarfile.open(artifact_path, 'r:gz') as tf:
            # extract files into model/output
            tf.extractall(path=tmp_dir)
    except Exception:
        return None

    xgb_model_file = tmp_dir / 'xgboost-model'
    if xgb is None or not xgb_model_file.exists():
        return None

    booster = xgb.Booster()
    booster.load_model(str(xgb_model_file))
    return XGBWrapper(booster)


def _load_xgboost_from_json(json_path: Path):
    """Load an XGBoost model saved as JSON (preferred, forward-compatible)."""
    if xgb is None:
        LOG.warning('xgboost not available in environment; cannot load JSON model')
        return None
    if not json_path.exists():
        return None
    try:
        booster = xgb.Booster()
        booster.load_model(str(json_path))
        return XGBWrapper(booster)
    except Exception:
        LOG.exception('Failed to load XGBoost JSON model: %s', json_path)
        return None


try:
    model = joblib.load(MODEL_PATH)
except Exception:
    # Try preferred JSON model first (created by scripts/port_xgboost_to_json.py)
    model = None
    try:
        model = _load_xgboost_from_json(JSON_MODEL)
    except Exception:
        model = None

    # Fallback: try to load an xgboost model from the SageMaker tar.gz artifact
    if model is None:
        model = _load_xgboost_from_s3_artifact(DEFAULT_SAGEMAKER_MODEL)


@app.get('/health')
async def health():
    return {'status':'ok', 'model_loaded': model is not None}


@app.post('/predict', response_model=OutputSchema)
async def predict(payload: InputSchema):
    url = payload.url
    # feature extraction - same as training
    X = np.array([len(url), url.count('.'), url.count('-'), url.count('@'), int('https' in url), int('login' in url)]).reshape(1,-1)
    if model is None:
        return {'url': url, 'prediction': 'error', 'confidence': 0.0}
    if hasattr(model,'predict_proba'):
        proba = model.predict_proba(X)
        score = float(proba[0,1]) if proba.shape[1]>1 else float(proba[0,0])
        label = 'phishing' if score>0.5 else 'legit'
    else:
        pred = model.predict(X)
        label = 'phishing' if int(pred[0])==1 else 'legit'
        score = float(pred[0])
    return {'url': url, 'prediction': label, 'confidence': round(score,4)}
