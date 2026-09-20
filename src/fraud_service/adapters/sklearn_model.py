"""The ONLY file in this service allowed to import sklearn/joblib.

Moves the `joblib.load(...)` call out of import-time global scope
(legacy notebook Cell 1: SMELL 1 & 2) into an explicit, failable
classmethod called only from a composition root — batch.py here, the
FastAPI lifespan in Lab 2.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import joblib
import pandas as pd


class SklearnModel:
    """Adapter satisfying `fraud_service.service.interfaces.Model`."""

    def __init__(self, pipeline: Any, model_version: str) -> None:
        self._pipeline = pipeline
        self.model_version = model_version

    @classmethod
    def load(cls, path: str | Path) -> SklearnModel:
        """Load the artifact bundle: {"pipeline": ..., "version": "v3.2.0"}.

        Fails loudly with an absolute path if the artifact is missing —
        the notebook's silent `../` fallback hid this class of bug.
        """
        artifact_path = Path(path)
        if not artifact_path.is_file():
            raise FileNotFoundError(f"Model artifact not found: {artifact_path.resolve()}")
        artifact = joblib.load(artifact_path)
        return cls(artifact["pipeline"], artifact.get("version", "unknown"))

    def predict_proba(self, features: dict[str, float | int]) -> float:
        frame = pd.DataFrame([features])
        return float(self._pipeline.predict_proba(frame)[0, 1])
