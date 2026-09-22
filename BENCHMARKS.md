# Benchmarks

Numbers measured against the reference course laptop. Record your own
measurements in the same table — your machine will differ, and that is
expected; what matters is the *shape* of the result (which row is faster,
and by roughly how much), not matching these numbers exactly.

## Day 1 — Module 2 (FastAPI hardening)

| Metric | `async def` (bug) | plain `def` (fixed) |
|---|---|---|
| p50 latency | — | 15 ms |
| p99 latency | 2.4 s | 38 ms |
| Throughput (c=25) | 118 req/s | 1,410 req/s |

- Load test: `hey -n 2000 -c 25 -m POST -D sample.json`
- Malformed corpus: 40/40 payloads rejected with 4xx (`payloads/malformed/`)
- Valid-traffic error rate: 0 non-2xx responses

## Day 2 — Lab 3 (Docker) — done

| Metric | Value |
|---|---|
| Naive build — image size | 2.41 GB |
| Naive build — cold build time | 6 min 12 s |
| Multi-stage build — image size | 412 MB (target ≤ 450 MB) |
| Multi-stage build — cold build time | ~1 min (varies by machine) |
| Warm rebuild (one-line code change) | 22 s, `CACHED` on the dependency layer |
| p99 — bare metal (Lab 2, no container) | 38 ms |
| p99 — containerised | 41 ms |
| Time-to-ready (`scripts/startup_time.sh`) | 6.8 s (target: under 10 s) |

Image ships as a non-root `appuser`, healthcheck on `/v1/ready`,
`docker compose ps` shows both `fraud-api` and `feature-cache` as
`(healthy)`.

## Day 2 — Lab 4 (Tests) — done

| Metric | Value |
|---|---|
| `pytest -m "not slow"` — pass count / duration | 52 passed in ~2.1 s |
| `pytest -m slow` — pass count / duration | 3 passed in ~5.9 s (includes the 5,000-row golden-file check) |
| Branch coverage (domain + service + api) | ~99% (target ≥ 80%) |
| Malformed corpus | 40/40 rejected with 4xx |

## Day 3 — Lab 5 (CI/CD pipeline) — done

| Metric | Value |
|---|---|
| lint job duration | ~40 s |
| test job duration | ~48 s |
| image-smoke — cold run | 1 min 49 s |
| image-smoke — warm run (GHA cache) | 30 s (~3.6x faster) |
| bad-pr: blocked by branch protection? | yes — `lint` (import-linter) and `test` (boundary case) both failed, merge button stayed greyed out until fixed |

Two real bugs the pipeline itself surfaced on first push, fixed via
[github.com/taCSif/SDA-AIE-113--Taif-Alsufiani](https://github.com/taCSif/SDA-AIE-113--Taif-Alsufiani):
`lint-imports` had no `[tool.importlinter]` config to read yet, and
`pytest -m "behavioural and not slow"` always selects zero tests in
this repo's suite (every behavioural test in Lab 4 is also marked
`slow`), which silently tripped the global `--cov-fail-under=80`
instead of testing anything.

## Day 3 — Lab 6 (Config, Secrets & Logs)

_Fill in after Lab 6 Step 3:_

| Metric | Value |
|---|---|
| p50 latency computed from JSON logs via `jq` | |
| Fail-fast startup error (bad `FRAUD_MODEL_PATH`) confirmed? | yes / no |
| `gitleaks` clean on final commit? | yes / no |
