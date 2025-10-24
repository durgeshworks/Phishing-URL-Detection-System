
import numpy as np
from model_deploy_demo import extract_features, postprocess_proba

def test_extract_features():
    f = extract_features('http://a.b')
    assert f.shape == (1,6)

def test_postprocess():
    label, score = postprocess_proba(np.array([[0.2,0.8]]))
    assert label == 'phishing'
