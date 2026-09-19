"""The ONLY file in this service allowed to import sklearn/joblib.

If the team ever moves to ONNX or a remote model server, they add a
sibling adapter and change one line in the composition root — the
service layer never notices.

TODO (Lab 1, step 3 — ~15 min):
Move the `joblib.load(...)` call out of global/import-time scope
(legacy notebook Cell 2: SMELL 1 & 2) into an explicit, failable
classmethod called ONLY from the composition root (batch.py here;
the FastAPI lifespan in Lab 2).

Suggested shape:

    from pathlib import Path
    import joblib
    import pandas as pd

    class SklearnModel:
        def __init__(self, pipeline, model_version: str) -> None:
            self._pipeline = pipeline
            self.model_version = model_version

        @classmethod
        def load(cls, path: str | Path) -> "SklearnModel":
            bundle = joblib.load(path)          # {"pipeline": ..., "version": "v3.2.0"}
            return cls(bundle["pipeline"], bundle["version"])

        def predict_proba(self, features: dict) -> float:
            frame = pd.DataFrame([features])
            return float(self._pipeline.predict_proba(frame)[0, 1])
"""

# TODO: implement SklearnModel.
