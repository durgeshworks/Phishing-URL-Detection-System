
#python -m pytest -q tests/test_model_server_json_pref.py -q
import importlib.util
import sys
import tarfile
from pathlib import Path
import types
import io


def test_model_server_prefers_json(tmp_path, monkeypatch):
    # Prepare a temporary project cwd
    proj = tmp_path / "proj"
    out = proj / "model" / "output"
    out.mkdir(parents=True)

    # Create a dummy model.json
    json_path = out / "model.json"
    json_path.write_text('{"dummy": true}')

    # Create a tar.gz containing a xgboost-model file (legacy artifact)
    tar_path = out / "model.tar.gz"
    with tarfile.open(tar_path, "w:gz") as tf:
        # create a small temporary file to add
        tfinfo = tarfile.TarInfo("xgboost-model")
        data = b"legacy-binary"
        tfinfo.size = len(data)
        tf.addfile(tfinfo, io.BytesIO(data))

    # Create a dummy model.joblib so joblib.load will fail (we want to reach JSON loader)
    (proj / "model.joblib").write_bytes(b"not a pickle")

    # Fake xgboost module to capture which path is loaded
    class FakeBooster:
        last_loaded = None

        def load_model(self, path):
            FakeBooster.last_loaded = path

        def predict(self, dmat):
            return [0.1]

    fake_xgb = types.SimpleNamespace(Booster=FakeBooster, DMatrix=lambda x: x)

    # Inject fake xgboost into sys.modules
    monkeypatch.setitem(sys.modules, "xgboost", fake_xgb)

    # Change cwd to the temp project so relative paths inside model_server resolve there
    monkeypatch.chdir(proj)

    # Load the target model_server.py from the repository (do not import package)
    repo_model_server = None
    this_file = Path(__file__).resolve()
    for p in this_file.parents:
        candidate = p / "model" / "deployment" / "model_server.py"
        if candidate.exists():
            repo_model_server = candidate
            break
    assert repo_model_server is not None, "could not locate model_server.py in repo parents"
    spec = importlib.util.spec_from_file_location("ms_test", str(repo_model_server))
    module = importlib.util.module_from_spec(spec)
    loader = spec.loader
    assert loader is not None
    loader.exec_module(module)

    # Assert that FakeBooster.load_model was called with the JSON path (preferred)
    assert FakeBooster.last_loaded is not None
    loaded = Path(FakeBooster.last_loaded)
    # If relative path was used, resolve it against temp project
    if not loaded.is_absolute():
        loaded = (proj / loaded).resolve()
    assert loaded == json_path.resolve()
