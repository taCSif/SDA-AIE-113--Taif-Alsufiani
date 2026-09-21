"""Routes with readiness semantics.

CRITICAL: the predict route MUST be a plain `def`, not `async def`.
sklearn inference is CPU-bound; FastAPI runs plain `def` routes in a
thread pool. `async def` here blocks the event loop for every other
request — this is the #1 cause of "FastAPI is slow" complaints, and
the trap planted in this lab.
"""
from fastapi import APIRouter, Depends, HTTPException, Request

from fraud_service.api.schemas import HealthResponse, PredictRequest, PredictResponse
from fraud_service.service.scorer import FraudScorer

router = APIRouter()


def get_scorer(request: Request) -> FraudScorer:
    scorer = getattr(request.app.state, "scorer", None)
    if scorer is None:
        raise HTTPException(status_code=503, detail="Model not ready",
                             headers={"Retry-After": "5"})
    return scorer


@router.post("/predict", response_model=PredictResponse)
def predict(body: PredictRequest, request: Request,
            scorer: FraudScorer = Depends(get_scorer)):
    result = scorer.score(body.to_domain())
    return PredictResponse(
        transaction_id=result["transaction_id"],
        fraud_probability=round(result["probability"], 6),
        decision=result["decision"],
        model_version=result["model_version"],
        trace_id=request.state.trace_id,
    )


@router.get("/health", response_model=HealthResponse)
def health():
    # Liveness: process is up. NO I/O here.
    return HealthResponse(status="ok", service="fraud-service")


@router.get("/ready")
def ready(request: Request):
    # Readiness: safe to receive traffic. Checks the model is loaded.
    if getattr(request.app.state, "scorer", None) is None:
        raise HTTPException(status_code=503, detail="warming up")
    return {"status": "ready"}
