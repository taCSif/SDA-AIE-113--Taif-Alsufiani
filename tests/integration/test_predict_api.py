import json
import pathlib

import pytest

MALFORMED = sorted(
    pathlib.Path("payloads/malformed").glob("*.json"))


@pytest.mark.integration
def test_predict_contract(client_factory, sample_txn):
    client = client_factory(probability=0.93)  # forces block
    r = client.post("/v1/predict",
                    json=json.loads(sample_txn.model_dump_json()))
    assert r.status_code == 200
    assert r.json()["decision"] == "block"


@pytest.mark.integration
def test_malformed_corpus_is_not_empty():
    assert MALFORMED, "payloads/malformed is missing or empty"


@pytest.mark.integration
@pytest.mark.parametrize("payload_file", MALFORMED, ids=lambda p: p.name)
def test_malformed_corpus_rejected(client_factory, payload_file):
    r = client_factory().post("/v1/predict",
                              content=payload_file.read_bytes(),
                              headers={"content-type": "application/json"})
    assert 400 <= r.status_code < 500, payload_file.name


@pytest.mark.integration
def test_predict_500_hides_stack_trace(client_factory, sample_txn, monkeypatch):
    client = client_factory()

    def boom(self, txn):
        raise ZeroDivisionError("seeded failure")

    monkeypatch.setattr(
        "fraud_service.service.scorer.FraudScorer.score", boom)
    r = client.post("/v1/predict",
                    json=json.loads(sample_txn.model_dump_json()))
    assert r.status_code == 500
    assert "ZeroDivisionError" not in r.text
    assert r.json()["error"]["code"] == "INTERNAL_ERROR"


@pytest.mark.integration
def test_health_and_ready(client_factory):
    client = client_factory()
    assert client.get("/v1/health").status_code == 200
    # no lifespan run and scorer only overridden => app.state has no scorer
    assert client.get("/v1/ready").status_code == 503


@pytest.mark.integration
def test_ready_when_scorer_loaded(client_factory):
    client = client_factory()
    client.app.state.scorer = object()  # simulate lifespan having loaded a scorer
    assert client.get("/v1/ready").status_code == 200


@pytest.mark.integration
def test_get_scorer_503_when_not_ready():
    from fastapi.testclient import TestClient

    from fraud_service.api.app import create_app
    client = TestClient(create_app(), raise_server_exceptions=False)
    r = client.post("/v1/predict",
                    json={"transaction_id": "TXN-TEST-00001",
                          "amount_sar": 10.0, "is_night": 0})
    assert r.status_code == 503
    assert r.headers["retry-after"] == "5"


@pytest.mark.integration
def test_get_scorer_returns_loaded_scorer(client_factory, sample_txn):
    from fraud_service.service.scorer import FraudScorer
    from tests.conftest import ConstantModel

    client = client_factory()
    client.app.dependency_overrides.clear()  # exercise the real get_scorer
    client.app.state.scorer = FraudScorer(ConstantModel(0.75), 0.85)
    r = client.post("/v1/predict",
                    json=json.loads(sample_txn.model_dump_json()))
    assert r.status_code == 200
    assert r.json()["decision"] == "review"
    assert r.json()["model_version"] == "test-1"


@pytest.mark.integration
def test_lifespan_loads_model_into_app_state(monkeypatch, sample_txn):
    """Startup wiring, with the disk load stubbed so it stays fast."""
    from fastapi.testclient import TestClient

    from fraud_service.api import app as app_module
    from tests.conftest import ConstantModel

    monkeypatch.setattr(app_module.SklearnModel, "load",
                        classmethod(lambda cls, path: ConstantModel(0.2, "stub-9")))
    with TestClient(app_module.create_app()) as client:
        assert client.get("/v1/ready").status_code == 200
        r = client.post("/v1/predict",
                        json=json.loads(sample_txn.model_dump_json()))
        assert r.json()["model_version"] == "stub-9"
        assert r.json()["decision"] == "allow"
