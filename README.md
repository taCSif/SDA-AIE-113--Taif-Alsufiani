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
