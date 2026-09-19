"""Batch entrypoint — the composition root for offline scoring.

This is the ONE place concrete implementations get wired together
(the model adapter, the settings, the scorer). Compare this file to
the messy Cell 6 loop in notebooks/fraud_exploration.ipynb: same
outcome (read CSV, score every row, write scored.csv), but every piece
is now swappable and testable in isolation.

TODO (Lab 1, step 4 — ~10 min):
    1. Load settings.
    2. Load the model via SklearnModel.load(settings.model_path).
    3. Construct FraudScorer(model=..., block_threshold=...).
    4. Read data/transactions_sample.csv into Transaction objects.
    5. Score each one, collect results, write scored.csv.
    6. Print a summary count (block / review / allow) like the notebook did.

Run with:  make run-batch   (after implementing this file)
"""
# TODO: import time, Settings, SklearnModel, FraudScorer, Transaction, pandas


def main() -> None:
    raise NotImplementedError(
        "Wire Settings -> SklearnModel -> FraudScorer here, "
        "then read data/transactions_sample.csv and write scored.csv."
    )


if __name__ == "__main__":
    main()
