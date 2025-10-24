from fastapi import FastAPI
from pydantic import BaseModel
import joblib
import numpy as np

class InputSchema(BaseModel):
    url: str

class OutputSchema(BaseModel):
    url: str
    prediction: str
    confidence: float

app = FastAPI()

MODEL_PATH = 'model.joblib'

try:
    model = joblib.load(MODEL_PATH)
except Exception:
    model = None

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
