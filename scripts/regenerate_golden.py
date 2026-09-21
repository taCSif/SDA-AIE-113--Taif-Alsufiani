"""Regenerate tests/behavioural/golden_scores.csv from the CURRENT model.

Only run this after a reviewed, intentional model or feature change.
Never run it just to silence a failing golden-file test.
"""
import sys

sys.path.insert(0, "tests/behavioural")

from fraud_service.adapters.sklearn_model import SklearnModel  # noqa: E402
from test_model_behaviour import GOLDEN, score_dataset  # noqa: E402

model = SklearnModel.load("models/fraud_model.joblib")
df = score_dataset(model)
df.to_csv(GOLDEN, index=False, float_format="%.10f")
print(f"wrote {len(df)} rows to {GOLDEN} (model {model.model_version})")
