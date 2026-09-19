"""TODO (Lab 2a, optional check / Lab 4 preview):
Once src/fraud_service/api/app.py exports `app`, you can test it
without running a live server, e.g.:

    from fastapi.testclient import TestClient
    from fraud_service.api.app import app

    client = TestClient(app)

    def test_health():
        response = client.get("/v1/health")
        assert response.status_code == 200

    def test_predict_valid():
        response = client.post("/v1/predict", json={
            "transaction_id": "TXN-TEST-0001",
            "amount_sar": 500.0,
            "is_night": 0,
        })
        assert response.status_code == 200
        assert "fraud_probability" in response.json()
"""
