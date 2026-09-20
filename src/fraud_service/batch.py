"""Batch entrypoint — the composition root for offline scoring.

This is the ONE place concrete implementations are wired together: the
settings, the model adapter, the scorer. Compare with Cell 5 of
notebooks/fraud_exploration.ipynb — same outcome (read CSV, score every
row, write scored.csv), but every piece is now swappable and testable
in isolation.

Run with:  make run-batch
"""

from __future__ import annotations

import time
from collections import Counter
from pathlib import Path

import pandas as pd

from fraud_service.adapters.sklearn_model import SklearnModel
from fraud_service.config import Settings
from fraud_service.domain.entities import FraudScore, Transaction
from fraud_service.service.scorer import FraudScorer


def load_transactions(path: Path) -> list[Transaction]:
    """Read the CSV and validate every row through the domain entity."""
    frame = pd.read_csv(path)
    return [Transaction(**record) for record in frame.to_dict(orient="records")]


def write_scores(scores: list[FraudScore], path: Path) -> None:
    pd.DataFrame([score.model_dump() for score in scores]).to_csv(path, index=False)


def main() -> None:
    settings = Settings()

    # 1. Load the model explicitly — not at import time (SMELL 1).
    started = time.perf_counter()
    model = SklearnModel.load(settings.model_path)
    print(f"Loaded model version {model.model_version} in {time.perf_counter() - started:.2f}s")

    # 2. Wire the use case. The scorer never learns where the model came from.
    scorer = FraudScorer(model=model, block_threshold=settings.block_threshold)

    # 3. Score every transaction.
    transactions = load_transactions(settings.data_path)
    started = time.perf_counter()
    scores = [scorer.score(txn) for txn in transactions]
    elapsed = time.perf_counter() - started

    # 4. Persist and summarise.
    write_scores(scores, settings.output_path)
    counts = Counter(score.decision for score in scores)
    print(
        f"Scored {len(scores)} transactions in {elapsed:.2f}s -> {settings.output_path}  "
        f"(block: {counts['block']}, review: {counts['review']}, allow: {counts['allow']})"
    )


if __name__ == "__main__":
    main()
