# Raqib Fraud Detection Service — Lab 2a Starter (SDA-AIE-113)

## What this is

This is the **starting point for Lab 2a** — "Build the Prediction API."
It already contains a **working Lab 1 solution**: the domain, service and
adapter layers are fully implemented, `make run-batch` works, and
`make lint` / `make test` are clean. Lab 2a adds an HTTP face
(`src/fraud_service/api/`) on top of this existing, working core —
you are NOT starting from scratch.

If you finished Lab 1 yourself with a working result, you can keep
using your own repo instead of this one — just add the same
`src/fraud_service/api/` folder to it. This starter exists so nobody
falls behind: everyone begins Lab 2a from the same known-good baseline.

## What already works (Lab 1, done for you)

```
src/fraud_service/
├── domain/
│   ├── entities.py       # Transaction, FeatureVector  ✅ implemented
│   └── policies.py       # decide()                    ✅ implemented
├── service/
│   ├── interfaces.py     # Model protocol              ✅ implemented
│   └── scorer.py         # FraudScorer                 ✅ implemented
├── adapters/
│   └── sklearn_model.py  # SklearnModel                ✅ implemented
├── config.py              # Settings                    ✅ implemented
└── batch.py                # composition root            ✅ implemented — try `make run-batch`
```

## What you build today (Lab 2a)

```
src/fraud_service/api/
├── schemas.py   # TODO — PredictRequest/Response + error envelope
├── app.py       # TODO — FastAPI factory + lifespan (model load + warm-up)
└── routes.py    # TODO — /v1/predict, /v1/health, /v1/ready
```

Every file above has a `TODO` block with a suggested shape drawn
directly from the Module 2 slides — you are filling in real, working
code, not guessing from scratch.

## Lab 2a — step by step

**Part A (50 min):**
1. **(10 min)** Fill in `api/schemas.py` — `PredictRequest`, `PredictResponse`, error envelope. Use `extra="forbid"` and `Field()` constraints.
2. **(15 min)** Fill in `api/app.py` — the app factory, `lifespan` (load model once, warm it up), trace/timing middleware, global exception handler.
3. **(15 min)** Fill in `api/routes.py` — `/v1/predict` (⚠️ plain `def`, not `async def` — see the warning in that file), `/v1/health`, `/v1/ready`.
4. **(10 min)** Run `make serve`, open `/docs`, and try: one valid request, one with a negative `amount_sar`, one with an unknown field. All three should behave exactly as discussed in class.

**Part B (Day 2, Hour 1)** — hardening pass: warm-up timing, the `/v1/boom` stack-trace-leak test, load testing with `hey`. Covered separately.

## Expected output

```
$ make serve
INFO:     Uvicorn running on http://127.0.0.1:8000

$ curl -s localhost:8000/v1/predict -d '{"transaction_id":"TXN-2026-00042","amount_sar":500,"is_night":0}' -H "content-type: application/json"
{"transaction_id":"TXN-2026-00042","fraud_probability":0.0317,"decision":"allow","model_version":"v3.2.0","trace_id":"a1b2c3d4e5f60718"}
```

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| RPS collapses under load / first requests feel slow one at a time | Route declared `async def` around the sklearn call | Change to plain `def` — FastAPI thread-pools it |
| `/ready` returns 200 before the model is actually loaded | `app.state.scorer` set before warm-up completes | Set it only AFTER the warm-up `predict_proba` call in `lifespan` |
| 422 on a request that looks valid | `extra="forbid"` + a typo'd field name | Read the 422 body — it names the exact field. This is the feature working, not a bug |
| First request ~1s, rest fast | Warm-up isn't running | Check for the `model_loaded` print line at startup |

---

# Lab 2 — the HTTP face (implemented on this branch)

## Endpoints

| method | path | success | failure |
|---|---|---|---|
| POST | `/v1/predict` | 200 `PredictResponse` | 422 validation, 503 model not ready, 500 internal |
| GET | `/v1/health` | 200 always — **liveness**, touches nothing | — |
| GET | `/v1/ready` | 200 once the model is loaded **and** warmed up | 503 + `Retry-After: 5` |

Every response carries `X-Trace-Id` (echoed from the request if the caller
supplies one) and `X-Response-Time-Ms`.

## Error envelope — design assumption

The brief allowed RFC 9457 Problem Details (`application/problem+json`) when no
contract table is available. A contract table *was* available: the suggested
shape in the starter's `api/schemas.py` docstring. This service therefore
implements **that** envelope, not RFC 9457:

```json
{"error": {"code": "VALIDATION_ERROR", "message": "...", "trace_id": "...", "details": [...]}}
```

- `code` is the stable, machine-readable half of the contract; clients branch on
  it. `message` is human-readable and may change.
- `details` is added on 422 and carries pydantic's field-level errors, so the
  response names the exact offending field.
- **Every** non-2xx response uses this one envelope — 422, 503 and 500 alike,
  built in a single place (`_error_response()` in `api/app.py`). If the team
  later standardises on RFC 9457, that one function is the only thing to change.

## Layer discipline

`PredictRequest` is an HTTP object and `Transaction` is a domain object; they
meet only in `PredictRequest.to_domain()`, called at the route boundary. The
domain and service packages import neither FastAPI, sklearn, joblib nor
pydantic-settings — verified by grep, not by eye:

```bash
grep -rn "^\s*\(import\|from\)\s\+\(fastapi\|sklearn\|joblib\|pydantic_settings\)"      src/fraud_service/domain src/fraud_service/service --include=*.py   # must be empty
```

## Why `/v1/predict` is a plain `def`

sklearn inference is blocking CPU work. A plain `def` route runs in FastAPI's
thread pool; `async def` would run it on the event loop and serialize every
concurrent request. Measured cost of getting this wrong: **4.3x throughput loss
(126 -> 29 RPS) and a 9.6x slower liveness probe at concurrency 25** — see
[BENCHMARKS.md](BENCHMARKS.md) section 5, which also reports the case where the
trap does *not* show and explains why.

## Running it

```bash
python -m venv .venv             # isolate: another course repo on this machine
.\.venv\Scripts\Activate.ps1     # can otherwise capture `import fraud_service`
pip install -e ".[dev,api]"      # src-layout: the package must be installed
make serve                       # fastapi dev -> http://127.0.0.1:8000/docs
make test                        # 15 tests
make lint
```

The deliberate crash endpoint used for the stack-trace-leak drill is off unless
you ask for it, and must never be enabled in a deployment:

```bash
FRAUD_ENABLE_DEBUG_ENDPOINTS=true python -m uvicorn fraud_service.api.app:app --port 8000
curl -i localhost:8000/v1/boom   # 500 envelope + trace_id; traceback stays in the log
```

## Environment note (Windows)

`models/fraud_model.joblib` is pickled by scikit-learn 1.8.0. With 1.7.2
installed, the warm-up raises `AttributeError: 'LogisticRegression' object has
no attribute 'multi_class'` and startup fails. Fixed here by installing the
matching version, which keeps the instructor's artifact byte-identical:

```bash
pip install "scikit-learn==1.8.0"
```

Regenerating the artifact with `python scripts/generate_baseline_assets.py` also
works, but it rewrites a committed file, so it was avoided.
