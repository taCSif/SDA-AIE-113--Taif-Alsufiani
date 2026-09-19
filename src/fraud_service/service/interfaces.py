"""Service-layer interfaces (ports). The service depends on THESE, never
on a concrete ML framework.

TODO (Lab 1, step 3):
Define a `Model` Protocol with one method: `predict_proba(features) -> float`.
This is what lets you swap sklearn for XGBoost, ONNX or a remote model
server later by changing exactly one adapter file (see
INSTRUCTOR_PACKAGE.md, Module 1, section 4).

Suggested shape:

    from typing import Protocol

    class Model(Protocol):
        model_version: str

        def predict_proba(self, features: dict) -> float: ...
"""

# TODO: implement the Model protocol.
