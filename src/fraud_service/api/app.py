"""Application factory with lifespan model loading, trace/timing
middleware, and a global exception handler that never leaks a stack
trace to the client.

The model loads in `lifespan`, ONCE, with a warm-up call — never at
import time, never per-request.
"""
import logging
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from fraud_service.adapters.sklearn_model import SklearnModel
from fraud_service.api.schemas import ErrorBody, ErrorEnvelope
from fraud_service.config import Settings
from fraud_service.service.scorer import FraudScorer

logger = logging.getLogger("fraud_service.api")

# HTTP status -> stable error code. Clients branch on the code, not the prose.
ERROR_CODES = {
    404: "NOT_FOUND",
    405: "METHOD_NOT_ALLOWED",
    503: "MODEL_NOT_READY",
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = Settings()
    app.state.settings = settings

    t0 = time.perf_counter()
    model = SklearnModel.load(settings.model_path)
    load_seconds = time.perf_counter() - t0

    # Warm-up: pay the lazy-init cost (BLAS threads, numpy/pandas code paths)
    # now, at startup, instead of on the first real user request.
    t1 = time.perf_counter()
    model.predict_proba({"amount_log": 0.0, "is_night": 0})
    warmup_seconds = time.perf_counter() - t1

    # ORDERING MATTERS: only now is the process safe to receive traffic.
    # /v1/ready keys off app.state.scorer, so it must be set last.
    app.state.scorer = FraudScorer(model=model, block_threshold=settings.block_threshold)
    print(
        f"model_loaded version={model.model_version} "
        f"load_seconds={load_seconds:.3f} warmup_seconds={warmup_seconds:.3f}",
        flush=True,
    )

    yield

    # Teardown: stop answering /v1/ready with 200 while we drain.
    app.state.scorer = None


def _error_response(
    status_code: int,
    code: str,
    message: str,
    request: Request,
    details: list | None = None,
    headers: dict | None = None,
) -> JSONResponse:
    """One envelope builder so every error in the service looks identical."""
    trace_id = getattr(request.state, "trace_id", "unknown")
    envelope = ErrorEnvelope(
        error=ErrorBody(code=code, message=message, trace_id=trace_id, details=details)
    )
    response_headers = {"X-Trace-Id": trace_id, **(headers or {})}
    return JSONResponse(
        status_code=status_code,
        content=envelope.model_dump(exclude_none=True),
        headers=response_headers,
    )


def create_app() -> FastAPI:
    settings = Settings()
    # Composition root owns logging config; nothing else in the package calls
    # basicConfig, so library users keep their own handlers.
    logging.basicConfig(
        level=settings.log_level.upper(),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    app = FastAPI(
        title="Fraud Scoring Service",
        version="1.0.0",
        lifespan=lifespan,
    )

    from fraud_service.api.routes import debug_router, router

    app.include_router(router, prefix="/v1")

    # Deliberate crash endpoint for the stack-trace-leak drill. Off by default;
    # enable with FRAUD_ENABLE_DEBUG_ENDPOINTS=true, never in production.
    if settings.enable_debug_endpoints:
        app.include_router(debug_router, prefix="/v1")

    @app.middleware("http")
    async def trace_and_time(request: Request, call_next):
        trace_id = request.headers.get("X-Trace-Id", uuid.uuid4().hex[:16])
        request.state.trace_id = trace_id
        t0 = time.perf_counter()
        response = await call_next(request)
        response.headers["X-Trace-Id"] = trace_id
        response.headers["X-Response-Time-Ms"] = str(round((time.perf_counter() - t0) * 1000, 1))
        return response

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError):
        # 422 with the offending fields named — this is the firewall working.
        return _error_response(
            422,
            "VALIDATION_ERROR",
            "Request failed validation; see details",
            request,
            details=jsonable_encoder(exc.errors()),
        )

    @app.exception_handler(HTTPException)
    async def http_error(request: Request, exc: HTTPException):
        return _error_response(
            exc.status_code,
            ERROR_CODES.get(exc.status_code, f"HTTP_{exc.status_code}"),
            str(exc.detail),
            request,
            headers=exc.headers,  # keeps Retry-After on 503s
        )

    @app.exception_handler(Exception)
    async def unhandled(request: Request, exc: Exception):
        # Nothing is swallowed: the FULL traceback is logged against the same
        # trace_id the client receives, so support can join the two.
        logger.error(
            "unhandled_error trace_id=%s method=%s path=%s",
            getattr(request.state, "trace_id", "unknown"),
            request.method,
            request.url.path,
            exc_info=exc,
        )
        # The traceback goes to the server log; the client gets a trace_id only.
        return _error_response(
            500,
            "INTERNAL_ERROR",
            "Unexpected error; contact support with trace_id",
            request,
        )

    return app


app = create_app()
