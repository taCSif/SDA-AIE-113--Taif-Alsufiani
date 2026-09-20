"""Use-case orchestration: score one transaction.

Replaces the monolithic `score_transaction_row()` God Function from the
legacy notebook Cell 4 (SMELL 4). Note what is ABSENT: no sklearn, no
pandas, no file paths, no logging setup — just orchestration over
injected collaborators, so a test constructs it with a fake Model in
one line.

Deliberately NO `try/except Exception` around the model call (SMELL 6):
failures surface to the caller, which decides how to handle them.
"""

from __future__ import annotations

from dataclasses import dataclass

from fraud_service.domain.entities import FraudScore, Transaction
from fraud_service.domain.policies import BLOCK_THRESHOLD_DEFAULT, decide
from fraud_service.service.interfaces import Model


@dataclass(frozen=True, slots=True)
class FraudScorer:
    """Constructor dependency injection: model + policy threshold."""

    model: Model
    block_threshold: float = BLOCK_THRESHOLD_DEFAULT

    def score(self, txn: Transaction) -> FraudScore:
        features = txn.to_features()
        probability = self.model.predict_proba(features.values)
        return FraudScore(
            transaction_id=txn.transaction_id,
            probability=probability,
            decision=decide(probability, self.block_threshold),
            model_version=self.model.model_version,
        )
