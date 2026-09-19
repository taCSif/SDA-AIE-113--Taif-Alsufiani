"""Domain entities: the vocabulary of the fraud problem.

Rules for this file:
- imports from stdlib + pydantic ONLY
- no I/O, no framework types, no ML library types (no sklearn, no joblib)

TODO (Lab 1, step 3 — ~15 min):
Move the feature-engineering logic that lives in the legacy notebook
(notebooks/fraud_exploration.ipynb, Cell 4: SMELL 3 — the in-place
dataframe mutation) into a `to_features()` method on an entity here.
This is the single source of truth for feature computation, shared by
every future consumer (API, batch job, tests) — the #1 defence against
training/serving skew (see INSTRUCTOR_PACKAGE.md, Module 1, section 5).

Suggested shape:

    from pydantic import BaseModel, Field

    class Transaction(BaseModel):
        transaction_id: str
        amount_sar: float = Field(gt=0)
        is_night: int = Field(ge=0, le=1)

        def to_features(self) -> "FeatureVector":
            import math
            return FeatureVector(values={
                "amount_log": math.log1p(self.amount_sar),
                "is_night": self.is_night,
            })

    class FeatureVector(BaseModel):
        values: dict[str, float | int]
"""

# TODO: implement Transaction, FeatureVector (and RawScore / Decision /
# FraudScore if you want the full contract from INSTRUCTOR_PACKAGE.md).
