"""Service-layer interfaces (ports).

The service depends on THIS protocol, never on a concrete ML framework.
Swapping sklearn for XGBoost, ONNX or a remote model server means adding
a sibling adapter and changing one line in the composition root.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class Model(Protocol):
    """Anything that can turn a feature mapping into a fraud probability."""

    model_version: str

    def predict_proba(self, features: dict[str, float | int]) -> float:
        """Return P(fraud) in [0.0, 1.0]."""
        ...
