"""Wire contract. These models exist for consumers; keep them stable.
They convert to/from domain entities in routes.py — never let them leak
inward into domain or service code.

TODO (Lab 2a, Part A1 — ~10 min):
Define PredictRequest, PredictResponse, and an error envelope, matching
the contract discussed in Module 2 (status-code discipline + the
pydantic-as-firewall slides).

Suggested shape:

    from pydantic import BaseModel, ConfigDict, Field
    from fraud_service.domain.entities import Transaction

    class PredictRequest(BaseModel):
        model_config = ConfigDict(extra="forbid")  # reject unknown fields loudly

        transaction_id: str = Field(min_length=8, max_length=64)
        amount_sar: float = Field(gt=0, le=1_000_000)
        is_night: int = Field(ge=0, le=1)

        def to_domain(self) -> Transaction:
            return Transaction(**self.model_dump())

    class PredictResponse(BaseModel):
        transaction_id: str
        fraud_probability: float = Field(ge=0, le=1)
        decision: str
        model_version: str
        trace_id: str

    class ErrorBody(BaseModel):
        code: str        # stable machine-readable contract
        message: str     # human-readable, may change
        trace_id: str

    class ErrorEnvelope(BaseModel):
        error: ErrorBody

    class HealthResponse(BaseModel):
        status: str
        service: str
"""

# TODO: implement PredictRequest, PredictResponse, ErrorBody, ErrorEnvelope, HealthResponse.
