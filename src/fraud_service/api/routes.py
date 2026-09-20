"""Routes with readiness semantics.

CRITICAL: the predict route is a plain `def`, not `async def`. sklearn
inference is CPU-bound; FastAPI runs plain `def` routes in a thread pool.
`async def` here would block the event loop for every other request — the
#1 cause of "FastAPI is slow" complaints.
"""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request

from fraud_service.api.schemas import (
    ErrorEnvelope,
    HealthResponse,
    PredictRequest,
    PredictResponse,
    ReadyResponse,
)
from fraud_service.service.scorer import FraudScorer

router = APIRouter()

# Registered only when FRAUD_ENABLE_DEBUG_ENDPOINTS=true (see app.create_app).
debug_router = APIRouter()

RETRY_AFTER = {"Retry-After": "5"}


def get_scorer(request: Request) -> FraudScorer:
    """Composition root lookup. 503 (not 500) while the model is still
    loading: the request is fine, the server just isn't ready yet."""
    scorer = getattr(request.app.state, "scorer", None)
    if scorer is None:
        raise HTTPException(status_code=503, detail="Model not ready", headers=RETRY_AFTER)
    return scorer


@router.post(
    "/predict",
    response_model=PredictResponse,
    responses={
        422: {"model": ErrorEnvelope},
        500: {"model": ErrorEnvelope},
        503: {"model": ErrorEnvelope},
    },
)
def predict(
    body: PredictRequest,
    request: Request,
    scorer: Annotated[FraudScorer, Depends(get_scorer)],
) -> PredictResponse:
    result = scorer.score(body.to_domain())
    return PredictResponse(
        transaction_id=result["transaction_id"],
        fraud_probability=round(result["probability"], 6),
        decision=result["decision"],
        model_version=result["model_version"],
        trace_id=request.state.trace_id,
    )


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Liveness: the process is up. NO I/O here — if this touches the model,
    a slow model restarts a perfectly healthy pod."""
    return HealthResponse(status="ok", service="fraud-service")


@router.get(
    "/ready",
    response_model=ReadyResponse,
    responses={503: {"model": ErrorEnvelope}},
)
def ready(request: Request) -> ReadyResponse:
    """Readiness: safe to receive traffic. 503 + Retry-After until the model
    is loaded AND warmed up, so the load balancer holds traffic back."""
    scorer = getattr(request.app.state, "scorer", None)
    if scorer is None:
        raise HTTPException(status_code=503, detail="warming up", headers=RETRY_AFTER)
    return ReadyResponse(status="ready", model_version=scorer.model.model_version)


@debug_router.get("/boom", include_in_schema=False)
def boom() -> dict:
    """Leak test: an unhandled exception must return the 500 envelope with a
    trace_id and nothing else — the traceback belongs in the logs."""
    raise RuntimeError("deliberate failure: SELECT secret FROM vault -- leak test")
