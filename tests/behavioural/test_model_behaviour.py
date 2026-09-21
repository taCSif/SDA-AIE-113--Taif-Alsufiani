import pathlib

import pandas as pd
import pytest

from fraud_service.domain.entities import Transaction

pytestmark = [pytest.mark.behavioural, pytest.mark.slow]

GOLDEN = pathlib.Path(__file__).parent / "golden_scores.csv"
DATA = pathlib.Path("data/transactions_sample.csv")


def _score(model, txn):
    return model.predict_proba(txn.to_features().values)


def score_dataset(model, csv_path=DATA):
    """Score every row of the sample CSV through the serving feature path."""
    df = pd.read_csv(csv_path)
    scores = [
        _score(model, Transaction(transaction_id=r.transaction_id,
                                  amount_sar=r.amount_sar, is_night=r.is_night))
        for r in df.itertuples()
    ]
    return pd.DataFrame({"transaction_id": df["transaction_id"], "score": scores})


def test_invariance_to_transaction_id_casing(real_model, sample_txn):
    a = _score(real_model, sample_txn)
    b = _score(real_model, sample_txn.model_copy(
        update={"transaction_id": sample_txn.transaction_id.lower()}))
    assert a == pytest.approx(b, abs=1e-9)


def test_directional_amount(real_model, sample_txn):
    small = _score(real_model, sample_txn.model_copy(
        update={"amount_sar": 50.0}))
    large = _score(real_model, sample_txn.model_copy(
        update={"amount_sar": 50_000.0}))
    assert large >= small - 1e-6


def test_probabilities_are_valid(real_model, sample_txn):
    for amount in (0.01, 1.0, 500.0, 1_000_000.0):
        for night in (0, 1):
            p = _score(real_model, sample_txn.model_copy(
                update={"amount_sar": amount, "is_night": night}))
            assert 0.0 <= p <= 1.0


def test_golden_scores_unchanged(real_model):
    """Drift here = model changed OR training/serving skew. Investigate;
    do NOT just regenerate the file (see scripts/regenerate_golden.py)."""
    golden = pd.read_csv(GOLDEN)
    current = score_dataset(real_model)
    assert len(golden) == len(current) == 5000
    assert (golden["transaction_id"] == current["transaction_id"]).all()
    diff = (golden["score"] - current["score"]).abs()
    assert diff.max() <= 1e-6, f"{(diff > 1e-6).sum()} rows drifted, max {diff.max():.3g}"
