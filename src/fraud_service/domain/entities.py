"""Domain entities: the vocabulary of the fraud problem.

Rules for this file:
- imports from stdlib + pydantic ONLY
- no I/O, no framework types, no ML library types (no sklearn, no joblib)

`Transaction.to_features()` replaces the legacy notebook's Cell 3
(SMELL 3: in-place mutation of a global dataframe) and the duplicate
feature maths inlined in Cell 4's God Function. It is now the single
source of truth for feature computation, shared by every consumer
(batch job, API, tests) — the primary defence against training/serving
skew.
"""

from __future__ import annotations

import math
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Decision = Literal["block", "review", "allow"]


class FeatureVector(BaseModel):
    """Model-ready features, keyed by the names the estimator expects."""

    model_config = ConfigDict(frozen=True)

    values: dict[str, float | int]


class Transaction(BaseModel):
    """A single transaction as it arrives from the source system."""

    model_config = ConfigDict(frozen=True)

    transaction_id: str
    amount_sar: float = Field(gt=0)
    channel: str = "unknown"
    is_night: int = Field(ge=0, le=1)

    def to_features(self) -> FeatureVector:
        """Derive model features. Mirrors notebook Cell 3 exactly:

        amount_log = log1p(amount_sar);  is_night = int(is_night)

        Key order matches the estimator's ``feature_names_in_``.
        """
        return FeatureVector(
            values={
                "amount_log": math.log1p(self.amount_sar),
                "is_night": int(self.is_night),
            }
        )


class FraudScore(BaseModel):
    """The result contract returned by the scoring use case."""

    model_config = ConfigDict(frozen=True, protected_namespaces=())

    transaction_id: str
    probability: float = Field(ge=0.0, le=1.0)
    decision: Decision
    model_version: str
