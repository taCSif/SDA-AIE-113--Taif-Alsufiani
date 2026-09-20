"""Wire contract. These models exist for consumers; keep them stable.
They convert to/from domain entities in routes.py — never let them leak
inward into domain or service code.

Contract table (status-code discipline):

    POST /v1/predict  200 -> PredictResponse
                      422 -> ErrorEnvelope(code="VALIDATION_ERROR")
                      503 -> ErrorEnvelope(code="MODEL_NOT_READY") + Retry-After
                      500 -> ErrorEnvelope(code="INTERNAL_ERROR")
    GET  /v1/health   200 -> HealthResponse   (liveness — never fails on I/O)
    GET  /v1/ready    200 -> ReadyResponse
                      503 -> ErrorEnvelope(code="MODEL_NOT_READY") + Retry-After
"""
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from fraud_service.domain.entities import Transaction


class PredictRequest(BaseModel):
    """Pydantic as a firewall: whatever reaches the service layer is already
    valid, so the scorer never has to defend itself against junk input."""

    model_config = ConfigDict(extra="forbid")  # reject unknown fields loudly

    transaction_id: str = Field(min_length=8, max_length=64, examples=["TXN-2026-00042"])
    amount_sar: float = Field(gt=0, le=1_000_000, examples=[500.0])
    is_night: int = Field(ge=0, le=1, examples=[0])

    def to_domain(self) -> Transaction:
        """The single crossing point from wire model to domain entity."""
        return Transaction(**self.model_dump())


class PredictResponse(BaseModel):
    # `model_` is a protected pydantic namespace, but model_version is part of
    # the published contract — opt out of the warning rather than rename it.
    model_config = ConfigDict(protected_namespaces=())

    transaction_id: str
    fraud_probability: float = Field(ge=0, le=1)
    decision: Literal["allow", "review", "block"]
    model_version: str
    trace_id: str


class ErrorBody(BaseModel):
    code: str       # stable machine-readable contract — clients branch on this
    message: str    # human-readable, may change without notice
    trace_id: str
    details: list[dict[str, Any]] | None = None  # field-level validation info


class ErrorEnvelope(BaseModel):
    """Every non-2xx response in this service has exactly this shape."""

    error: ErrorBody


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"
    service: str = "fraud-service"


class ReadyResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    status: Literal["ready"] = "ready"
    model_version: str
