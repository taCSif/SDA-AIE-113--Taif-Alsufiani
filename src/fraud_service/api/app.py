"""Application factory with lifespan model loading, trace/timing
middleware, and a global exception handler that never leaks a stack
trace to the client.
"""
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from fraud_service.adapters.sklearn_model import SklearnModel
from fraud_service.config import Settings
from fraud_service.service.scorer import FraudScorer


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = Settings()
    t0 = time.perf_counter()
    model = SklearnModel.load(settings.model_path)
    # warm-up: pay lazy-init cost now, not on the first user request
    model.predict_proba({"amount_log": 0.0, "is_night": 0})
    print(f"model_loaded version={model.model_version} "
          f"seconds={time.perf_counter() - t0:.3f}")

    app.state.scorer = FraudScorer(model=model, block_threshold=settings.block_threshold)
    app.state.settings = settings
    yield
    # teardown (nothing to close here yet)


def create_app() -> FastAPI:
    app = FastAPI(title="Fraud Scoring Service", version="1.0.0", lifespan=lifespan)

    from fraud_service.api.routes import router
    app.include_router(router, prefix="/v1")

    @app.middleware("http")
    async def trace_and_time(request: Request, call_next):
        trace_id = request.headers.get("X-Trace-Id", uuid.uuid4().hex[:16])
        request.state.trace_id = trace_id
        t0 = time.perf_counter()
        response = await call_next(request)
        response.headers["X-Trace-Id"] = trace_id
        response.headers["X-Response-Time-Ms"] = str(round((time.perf_counter() - t0) * 1000, 1))
        return response

    @app.exception_handler(Exception)
    async def unhandled(request: Request, exc: Exception):
        trace_id = getattr(request.state, "trace_id", "unknown")
        return JSONResponse(status_code=500, content={"error": {
            "code": "INTERNAL_ERROR",
            "message": "Unexpected error; contact support with trace_id",
            "trace_id": trace_id}})

    return app


app = create_app()
