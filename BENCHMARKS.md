# BENCHMARKS — Lab 2b hardening pass

Every number here was measured on this machine, in the project's own
virtualenv. Where a result contradicts the expected lab outcome it is reported
as measured, with the cause investigated rather than smoothed over.

## Environment

| | |
|---|---|
| OS / CPU | Windows 10 Pro (10.0.19045), 4 logical cores |
| Python | 3.11.4, project venv at `.venv/` |
| Package | `fraud_service` resolved from `C:\Users\HP\Desktop\lab2sol\fraud-service\src\fraud_service` |
| FastAPI / uvicorn | 0.141.1, single worker, `--host 127.0.0.1` |
| scikit-learn | 1.8.0 (matches the pickled artifact — see README) |
| Model | `models/fraud_model.joblib`, version `v3.2.0`, LogisticRegression on 2 features |
| Load generator | `scripts/loadtest.py` |

**Isolation matters here:** the machine also holds `C:\Users\HP\Desktop\lab1sol`,
and an editable install can silently make `import fraud_service` resolve to the
other project. All numbers below come from `.venv/Scripts/python.exe`, whose
import path was checked before measuring.

**Caveat on every RPS number:** the load generator is Python and runs on the
same 4 cores as the server, so absolute RPS is client-limited. Comparisons
between arms are valid (identical client, identical load, exactly one variable
changed); the absolute figures are not a capacity statement.

`hey` is not installed on this machine, so the equivalent generator was written
and committed at `scripts/loadtest.py`; the matching `hey` command line is in
its docstring. It also probes `/v1/health` every 50 ms during the run, because
liveness latency is what gets a merely-busy pod restarted.

## 1. Model load and warm-up timing

Startup line printed by `lifespan`:

```
model_loaded version=v3.2.0 load_seconds=4.649 warmup_seconds=0.012
```

Cost breakdown in a fresh process, two runs:

| | run 1 | run 2 |
|---|---|---|
| `joblib.load` | 3520.6 ms | 2248.7 ms |
| first `predict_proba` (cold) | 6.3 ms | 2.2 ms |
| warm p50 | 2.16 ms | 1.62 ms |
| warm p95 | 6.22 ms | 3.86 ms |
| cold-call penalty | **2.9x** | **1.4x** |

First-request latency over HTTP — warmed app versus the same app with the
warm-up call deleted, four paired runs (fresh server process each time):

| run | with warm-up | without warm-up |
|---|---|---|
| 1 | 26.2 ms | **101.0 ms** |
| 2 | 20.9 ms | **330.4 ms** |
| 3 | 14.4 ms | 12.4 ms |
| 4 | 16.5 ms | **161.3 ms** |
| median | **18.7 ms** | **131.2 ms** |

The warm-up removes a first-request penalty of roughly **7x at the median**,
but the effect is high-variance: one of four runs showed no penalty at all.
That variance is honest lazy-init behaviour, not a clean constant, and an
earlier measurement of the same pair outside the venv showed no difference
(11.1 ms versus 11.1 ms). Two things are nevertheless solid: the warmed arm is
consistently fast (14–26 ms across every run) while the unwarmed arm is
unpredictable (12–330 ms), and `joblib.load` costs **2.2–4.6 seconds** every
time. The seconds-scale load is what the readiness gate exists for; the warm-up
is what keeps the first customer request off the slow path.

## 2. Readiness gate — `app.state.scorer` is set only after warm-up

Server started with `--lifespan off`, which reproduces "process listening,
model not loaded":

| request | status | headers / body |
|---|---|---|
| `GET /v1/health` | **200** | `{"status":"ok","service":"fraud-service"}` — liveness never touches the model |
| `GET /v1/ready` | **503** | `retry-after: 5`, `{"error":{"code":"MODEL_NOT_READY","message":"warming up",...}}` |
| `POST /v1/predict` | **503** | `retry-after: 5`, `{"error":{"code":"MODEL_NOT_READY","message":"Model not ready",...}}` |

After a normal start, once lifespan has completed:

| request | status | body |
|---|---|---|
| `GET /v1/ready` | **200** | `{"status":"ready","model_version":"v3.2.0"}` |

Also covered by `test_ready_is_503_with_retry_after_before_warmup`,
`test_predict_is_503_before_warmup` and `test_ready_is_200_after_warmup`.

## 3. Status-code discipline (live server)

| request | status | body |
|---|---|---|
| valid | **200** | `{"transaction_id":"TXN-2026-00042","fraud_probability":0.645215,"decision":"allow","model_version":"v3.2.0","trace_id":"b2e23e33836e46ab"}` |
| `amount_sar: -5` | **422** | `VALIDATION_ERROR`, `loc: ["body","amount_sar"]`, "Input should be greater than 0" |
| unknown field `currency` | **422** | `VALIDATION_ERROR`, `type: extra_forbidden`, `loc: ["body","currency"]` |
| `is_night: 7` | **422** | `VALIDATION_ERROR`, `type: less_than_equal` |
| `GET /v1/health` | **200** | `{"status":"ok","service":"fraud-service"}` |
| `GET /v1/ready` | **200** | `{"status":"ready","model_version":"v3.2.0"}` |

Every response also carries `X-Trace-Id` and `X-Response-Time-Ms`.

## 4. Stack-trace leak test (`/v1/boom`)

`/v1/boom` raises `RuntimeError("deliberate failure: SELECT secret FROM vault
-- leak test")`. It is registered only when `FRAUD_ENABLE_DEBUG_ENDPOINTS=true`,
so it cannot exist in a default deploy.

Client sees (request sent with `X-Trace-Id: leaktest-venv-01`):

```
HTTP/1.1 500 Internal Server Error
{"error":{"code":"INTERNAL_ERROR","message":"Unexpected error; contact support with trace_id","trace_id":"leaktest-venv-01"}}
```

Server log holds the whole traceback, keyed by the same trace id:

```
2026-09-20 16:55:02,022 ERROR fraud_service.api unhandled_error trace_id=leaktest-venv-01 method=GET path=/v1/boom
Traceback (most recent call last):
  ...
RuntimeError: deliberate failure: SELECT secret FROM vault -- leak test
```

Checks performed:

- grep of the response body for `Traceback|RuntimeError|vault|File "` → **0 matches**
- the exception message (`vault`) appears **only** in the log, never on the wire
- `GET /v1/ready` immediately after the crash → **200**; the worker survives

## 5. Load test — the `async def` trap

Protocol: one uvicorn worker per arm, arms differing **only** in `def` versus
`async def` on `/v1/predict`, same client, two runs per cell.

### 5a. Real model (`v3.2.0`) — the trap does NOT appear

`--n 600`:

| arm | c | RPS run 1 | RPS run 2 | predict p50 (r1/r2) | health p50 (r1/r2) |
|---|---|---|---|---|---|
| plain `def` | 1 | 82.9 | 22.9 * | 11.4 / 11.5 ms | 10.0 / 9.0 ms |
| `async def` | 1 | 90.0 | 104.4 | 10.2 / 8.8 ms | 11.6 / 9.5 ms |
| plain `def` | 25 | 92.4 | 119.2 | 248.6 / 206.6 ms | 177.9 / 143.3 ms |
| `async def` | 25 | 114.1 | 153.3 | 213.4 / 156.1 ms | 214.7 / 153.4 ms |

\* one client-side stall (1 non-200, `health_max` 980 ms); the arm's other run
is representative.

There is no RPS collapse at c=25 — `async def` is if anything marginally
faster. Rather than report a difference that is not there, the cause was
measured directly: **how much of a request's work actually releases the GIL.**
Thread-scaling probe, serial versus 4 threads:

| workload | serial | 4 threads | speedup |
|---|---|---|---|
| real `SklearnModel.predict_proba` | 0.37 s | 0.34 s | **1.08x** |
| `numpy.linalg.svd(360)` | 1.33 s | 2.70 s | 0.49x |
| `time.sleep(25 ms)` | 1.56 s | 0.40 s | 3.92x |

A request in this service is dominated by `pd.DataFrame([features])` plus a
2-feature LogisticRegression — pure-Python work that **holds the GIL**. The
thread pool cannot parallelize it, so moving the call off the event loop buys
no throughput *on this model*. The trap is real; this model is simply too small
and too GIL-bound to trigger it.

### 5b. Control — identical service, inference that releases the GIL

Same app, same routes, same client; `predict_proba` replaced with 25 ms of
GIL-releasing work, which is how a real tree ensemble, a larger sklearn
pipeline or an ONNX session behaves. `--n 300`:

| arm | c | RPS run 1 | RPS run 2 | predict p50 (r1/r2) | health p50 (r1/r2) |
|---|---|---|---|---|---|
| plain `def` | 1 | 27.1 | 26.3 | 34.3 / 34.9 ms | 6.9 / 7.4 ms |
| `async def` | 1 | 24.0 | 25.4 | 38.5 / 35.2 ms | 29.5 / 20.8 ms |
| plain `def` | **25** | **122.6** | **126.0** | 203.3 / 141.3 ms | 121.5 / 84.8 ms |
| `async def` | **25** | **29.2** | **29.2** | 862.8 / 848.9 ms | 793.9 / 815.3 ms |

**The trap, in numbers.** At concurrency 25:

- throughput collapses **4.3x** — 126.0 → 29.2 RPS (the `async def` arm hit
  29.2 on both runs: it is pinned at one request at a time, 1/0.025 s ≈ 40/s
  minus overhead)
- predict p50 degrades **6.0x** — 141 ms → 849 ms
- the liveness probe degrades **9.6x** — 84.8 ms → 815.3 ms, peaking at 1025 ms

At concurrency 1 the two arms are indistinguishable (26.3 versus 25.4 RPS).
**The damage exists only under concurrency** — which is exactly why this bug
passes local testing and ships.

Mechanism: `async def` runs the blocking call *on* the event loop, so requests
serialize and `/v1/health` queues behind them. Plain `def` hands the call to
FastAPI's thread pool, the loop stays free, and liveness keeps answering.

### Conclusion

`/v1/predict` stays a plain `def`. On today's 2-feature model it costs nothing
measurable; the moment the model gets heavier — the normal direction of travel
— it is the difference between 126 RPS and 29 RPS, and between a healthy pod
and one Kubernetes restarts for failing its liveness probe.

## 6. Result parity with the batch path

`test_api_probability_matches_direct_scorer` scores the same transaction through
`POST /v1/predict` and through `FraudScorer` directly, asserting probability,
decision and model version match exactly. It passes: both paths go through
`Transaction.to_features()`, so there is one feature implementation, not two.
The live API returns `0.645215` for the reference transaction, and `make
run-batch` over 5,000 rows gives `{'allow': 4746, 'review': 199, 'block': 55}`
— a model that discriminates, not the all-`allow`/0.0 signature of a broken
artifact load.

## 7. Reproducing these measurements

```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev,api]"
python -c "import fraud_service, os; print(os.path.dirname(fraud_service.__file__))"  # must be under lab2sol

# terminal 1 — the service (debug endpoint on, for the leak test only)
$env:FRAUD_ENABLE_DEBUG_ENDPOINTS="true"; python -m uvicorn fraud_service.api.app:app --port 8000

# terminal 2
python scripts/loadtest.py --n 600 --c 1
python scripts/loadtest.py --n 600 --c 25
curl -i localhost:8000/v1/boom

# readiness before warm-up
python -m uvicorn fraud_service.api.app:app --port 8005 --lifespan off
curl -i localhost:8005/v1/ready     # 503 + Retry-After
```
