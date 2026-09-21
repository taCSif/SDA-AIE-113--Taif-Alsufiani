import joblib
import pytest
from sklearn.linear_model import LogisticRegression

from fraud_service.adapters.sklearn_model import SklearnModel


@pytest.mark.unit
def test_load_and_predict_proba_returns_plain_float(tmp_path):
    import pandas as pd
    X = pd.DataFrame({"amount_log": [1.0, 2.0, 8.0, 9.0], "is_night": [0, 0, 1, 1]})
    clf = LogisticRegression().fit(X, [0, 0, 1, 1])
    path = tmp_path / "m.joblib"
    joblib.dump({"pipeline": clf, "version": "tiny-1"}, path)

    model = SklearnModel.load(path)

    assert model.model_version == "tiny-1"
    p = model.predict_proba({"amount_log": 9.0, "is_night": 1})
    assert type(p) is float
    assert p > model.predict_proba({"amount_log": 1.0, "is_night": 0})
