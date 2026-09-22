"""Batch entrypoint — the composition root for offline scoring.

This is the ONE place concrete implementations get wired together.
Compare this file to the messy Cell 6 loop in
notebooks/fraud_exploration.ipynb: same outcome (read CSV, score every
row, write scored.csv), but every piece here is swappable and testable
in isolation.
"""
import time

import pandas as pd

from fraud_service.adapters.sklearn_model import SklearnModel
from fraud_service.config import Settings
from fraud_service.domain.entities import Transaction
from fraud_service.logging_setup import configure_logging, get_logger
from fraud_service.service.scorer import FraudScorer

log = get_logger(__name__)


def main() -> None:
    settings = Settings()
    configure_logging(settings.log_level)

    t0 = time.perf_counter()
    model = SklearnModel.load(settings.model_path)
    load_duration = time.perf_counter() - t0
    log.info("model_loaded", version=model.model_version, seconds=round(load_duration, 2))

    scorer = FraudScorer(model=model, block_threshold=settings.block_threshold)

    df = pd.read_csv("data/transactions_sample.csv")

    t1 = time.perf_counter()
    results = []
    for _, row in df.iterrows():
        txn = Transaction(
            transaction_id=row["transaction_id"],
            amount_sar=float(row["amount_sar"]),
            is_night=int(row["is_night"]),
        )
        results.append(scorer.score(txn))
    batch_duration = time.perf_counter() - t1

    out_df = pd.DataFrame(results)
    out_df.to_csv("scored.csv", index=False)

    counts = {str(k): v for k, v in out_df["decision"].value_counts().to_dict().items()}
    log.info("batch_scored", rows=len(out_df), seconds=round(batch_duration, 2),
              output="scored.csv", **counts)


if __name__ == "__main__":
    main()
