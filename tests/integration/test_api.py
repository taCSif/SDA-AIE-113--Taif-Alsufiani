"""TODO (Lab 4, Step 3):
Complete this file (or create tests/integration/test_predict_api.py)
with a proper integration suite: a contract test that steers the test
double toward a specific decision branch, a parametrised test that
walks every file in payloads/malformed/ and confirms it's rejected
with a 4xx, and a test proving a 500 never leaks the internal
exception name to the client.

A minimal smoke version, for reference — this already works against
the real app and lifespan:

    from fastapi.testclient import TestClient
    from fraud_service.api.app import app

    def test_health():
        with TestClient(app) as client:
            response = client.get("/v1/health")
            assert response.status_code == 200

See the Day 2 Lab Guide, Lab 4 Step 3, for the full suggested shape
(client_factory, MALFORMED corpus, monkeypatch on FraudScorer.score).
"""
