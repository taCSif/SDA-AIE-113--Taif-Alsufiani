"""Use-case orchestration: score one transaction.

Note what must be ABSENT here once you're done: no FastAPI, no sklearn,
no file paths, no logging configuration. Pure orchestration = trivially
testable (construct with a fake Model in one line, no mocking framework
needed).

TODO (Lab 1, step 3 — ~15 min):
Replace the monolithic `score_transaction_row()` God Function from the
legacy notebook (Cell 5: SMELL 4) with a small orchestration class that
uses constructor dependency injection.

Suggested shape:

    from dataclasses import dataclass
    from fraud_service.domain.entities import Transaction
    from fraud_service.domain.policies import decide
    from fraud_service.service.interfaces import Model

    @dataclass
    class FraudScorer:
        model: Model
        block_threshold: float

        def score(self, txn: Transaction):
            features = txn.to_features()
            raw_prob = self.model.predict_proba(features.values)
            decision = decide(raw_prob, self.block_threshold)
            return {
                "transaction_id": txn.transaction_id,
                "probability": raw_prob,
                "decision": decision,
                "model_version": self.model.model_version,
            }

IMPORTANT: do NOT wrap the model call in a bare `except Exception: pass`
(that was SMELL 6 in the notebook) — let failures surface; the caller
(batch.py or the API layer) decides how to handle them.
"""

# TODO: implement FraudScorer.
