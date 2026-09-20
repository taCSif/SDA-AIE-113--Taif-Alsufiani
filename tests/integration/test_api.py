"""API-level tests: status-code discipline, the readiness contract, the
error envelope, and parity between the HTTP path and the batch path.
"""
import pytest
from fastapi.testclient import TestClient

from fraud_service.adapters.sklearn_model import SklearnModel
from fraud_service.api.app import app
from fraud_service.config import Settings
from fraud_service.domain.entities import Transaction
from fraud_service.service.scorer import FraudScorer

VALID_BODY = {"transaction_id": "TXN-2026-00042", "amount_sar": 500.0, "is_night": 0}


@pytest.fixture(scope="module")
def client():
    # The context manager runs lifespan: model load + warm-up.
    with TestClient(app) as running_client:
        yield running_client


def test_health_is_liveness_only():
    # No lifespan here: /health must answer 200 even with no model loaded.
    assert TestClient(app).get("/v1/health").status_code == 200


def test_ready_is_503_with_retry_after_before_warmup():
    response = TestClient(app).get("/v1/ready")  # lifespan never ran
    assert response.status_code == 503
    assert response.headers["Retry-After"] == "5"
    assert response.json()["error"]["code"] == "MODEL_NOT_READY"


def test_predict_is_503_before_warmup():
    response = TestClient(app).post("/v1/predict", json=VALID_BODY)
    assert response.status_code == 503
    assert response.headers["Retry-After"] == "5"


def test_ready_is_200_after_warmup(client):
    response = client.get("/v1/ready")
    assert response.status_code == 200
    assert response.json()["status"] == "ready"


def test_predict_valid(client):
    response = client.post("/v1/predict", json=VALID_BODY)
    assert response.status_code == 200
    body = response.json()
    assert 0.0 <= body["fraud_probability"] <= 1.0
    assert body["decision"] in {"allow", "review", "block"}
    assert body["model_version"] == "v3.2.0"
    assert body["trace_id"] == response.headers["X-Trace-Id"]


def test_predict_rejects_negative_amount(client):
    response = client.post("/v1/predict", json={**VALID_BODY, "amount_sar": -5})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
    assert response.json()["error"]["details"][0]["loc"] == ["body", "amount_sar"]


def test_predict_rejects_unknown_field(client):
    response = client.post("/v1/predict", json={**VALID_BODY, "currency": "SAR"})
    assert response.status_code == 422
    detail = response.json()["error"]["details"][0]
    assert detail["type"] == "extra_forbidden"
    assert detail["loc"] == ["body", "currency"]


def test_trace_id_is_echoed_when_supplied(client):
    response = client.post("/v1/predict", json=VALID_BODY, headers={"X-Trace-Id": "abc123"})
    assert response.json()["trace_id"] == "abc123"
    assert "X-Response-Time-Ms" in response.headers


def test_boom_returns_envelope_without_stack_trace():
    # Debug router is off by default, so build an app that has it enabled.
    import fraud_service.api.app as app_module

    settings = Settings(enable_debug_endpoints=True)
    original = app_module.Settings
    app_module.Settings = lambda: settings
    try:
        debug_app = app_module.create_app()
    finally:
        app_module.Settings = original

    with TestClient(debug_app, raise_server_exceptions=False) as debug_client:
        response = debug_client.get("/v1/boom")

    assert response.status_code == 500
    assert response.json()["error"]["code"] == "INTERNAL_ERROR"
    assert response.json()["error"]["trace_id"]
    assert "Traceback" not in response.text
    assert "vault" not in response.text  # nothing from the exception message


def test_api_probability_matches_direct_scorer(client):
    """Same transaction, same number — one feature path, no duplicated logic."""
    settings = Settings()
    scorer = FraudScorer(
        model=SklearnModel.load(settings.model_path),
        block_threshold=settings.block_threshold,
    )
    direct = scorer.score(Transaction(**VALID_BODY))
    api = client.post("/v1/predict", json=VALID_BODY).json()

    assert api["fraud_probability"] == round(direct["probability"], 6)
    assert api["decision"] == direct["decision"]
    assert api["model_version"] == direct["model_version"]
