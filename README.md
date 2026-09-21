# Raqib Fraud Detection Service — Lab 4 Starter (SDA-AIE-113)

## What this is

This is the **starting point for Lab 4** — "Build a Three-Level Test
Suite." It already contains a **complete, working Lab 1 + Lab 2a + Lab 3
solution**: the FastAPI service and the Docker/compose setup are both
fully implemented and working.

If you finished Lab 3 yourself with a working result, keep using your
own repo instead of this one. This starter exists so nobody falls behind
— everyone begins Lab 4 from the same known-good baseline.

## What already works (Lab 1 + Lab 2a + Lab 3, done for you)

```
src/fraud_service/         # domain/service/adapters/api — all implemented, tested
Dockerfile                  # multi-stage build, ≤ 450 MB, non-root user
.dockerignore                 #
docker-compose.yml             # fraud-api + Redis, gated on service_healthy
requirements.lock               # pinned runtime deps for the image
scripts/startup_time.sh          # measures container time-to-ready
Makefile                          # install, run-batch, lint, test, serve, up, down, image-size, smoke
payloads/malformed/                 # 40-file malformed-payload corpus (Day 1)
BENCHMARKS.md                        # Day 1 + Lab 3 numbers already filled in
```

```
$ make up
$ docker compose ps
NAME              STATUS
fraud-api         Up (healthy)
feature-cache     Up (healthy)

$ make smoke
{"status":"ok","service":"fraud-service"}
{"status":"ready"}
```

## What you build today (Lab 4)

```
tests/conftest.py                        # TODO — ConstantModel, client_factory, real_model, sample_txn
tests/unit/test_policies.py               # tighten — add the boundary edge cases (0.849999 / 0.85)
tests/integration/test_api.py             # TODO — complete, or add tests/integration/test_predict_api.py
tests/behavioural/test_model_behaviour.py   # TODO — invariance, directional, and golden-file tests
pyproject.toml                                # extend — pytest markers + coverage settings (fail_under = 80)
```

Full step-by-step instructions, expected results, and a troubleshooting
table are in the Day 2 Lab Guide (Lab 4 section) — work through it in
order; this README is just the starting-point map.

**Before you start**, know this: `decide(fraud_probability, block_threshold)`
in `domain/policies.py` returns a plain string (`"block"`, `"review"`, or
`"allow"`), and `Model.predict_proba(features)` returns a bare `float`
— not a wrapped object. Every test in Lab 4 depends on this.

## Quick start

```
pip install -e ".[dev,api]"
pip install pytest-cov
make test              # existing tests, all green
pytest -m unit -v      # once Step 2 is done
```
