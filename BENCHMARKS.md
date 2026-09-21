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

## Day 2 — Lab 3 (Docker)

_Fill in as you complete each step:_

| Metric | Value |
|---|---|
| Naive build — image size | **1.01 GB** (0.94 GiB; 287 MB compressed) |
| Naive build — cold build time | **9 min 54 s** (594 s, cold cache) |
| Multi-stage build — image size | **771 MB** (736 MiB; 176 MB compressed) — target ≤ 450 MB **not met** |
| Multi-stage build — cold build time | **13 min 47 s** (827.6 s, cold cache) |
| Warm rebuild (one-line code change) | **182.7 s** — dependency layer `CACHED` ✓, but target < 30 s **not met** |
| p99 — bare metal (Lab 2, no container) | 38 ms |
| p99 — containerised | **183.5 ms** @ c=10 (65.7 ms @ c=4, 16.2 ms @ c=1) — custom load script, see notes |
| Time-to-ready (`scripts/startup_time.sh`) | **12.8 s** warm (37.3 s on first run after a Docker restart); target < 10 s **not met** |

**Naive build breakdown** (`Dockerfile.naive`, `python:3.12-slim`, amd64, 7 layers):

| Step | Time |
|---|---|
| `FROM` base image pull | 23.3 s |
| `COPY . .` | 0.7 s |
| `RUN pip install ".[dev,api]"` | 370.3 s |
| export + unpack layers | 192.0 s |
| **total** | **~594 s** |

- Build context sent to the daemon: **31.45 kB** (`.dockerignore` excludes `.git`,
  `data/`, `notebooks/`, `tests/` and `.env`).
- Lab handout predicts ~2.41 GB / 6 min 12 s. This machine measured roughly
  **half the size** and **1.6x the time** — resolved dependency versions,
  network speed and disk differ from the reference laptop. Per the note at the
  top of this file, the shape is what matters; the multi-stage comparison below
  is against 1.01 GB / 594 s, not against the handout's figures.

**Multi-stage measurements and caveats** (`Dockerfile`, `requirements.lock` = 54 runtime-only packages):

- Image: 771 MB vs 1.01 GB naive (~24 % smaller). Runs as `appuser`, health check hits `/v1/ready`.
  The lock resolved to current majors (pandas 3.0.6, numpy 2.5.3, scipy 1.18.1, scikit-learn 1.9.1),
  which is why 450 MB is out of reach without changing the dependency set.
- Warm rebuild breakdown: `pip install --no-deps .` 29.6 s, `COPY --from=builder /opt/venv` 28.8 s,
  export 51.3 s, unpack 37.7 s. The venv layer is re-copied because the builder stage changed;
  Docker Desktop on WSL2 makes export/unpack expensive.
- `docker compose ps`: `fraud-api` and `feature-cache` both `(healthy)`; fraud-api started only after
  Redis reported healthy. `feature-cache` uses the default 30 s health interval, so `compose up -d`
  itself takes ~45-60 s before it returns.
- Time-to-ready is measured from the moment `compose up -d` returns; model load inside the container
  took 4.7 s (log line `model_loaded`).
- Load test: `hey` is not installed and no public image exists, so `scripts/loadtest.py`
  (keep-alive `http.client`, run on the compose network) was used. c=10, 30 s: 3,664 requests,
  all 200, 122 req/s, p50 65.7 ms, p95 121.1 ms, p99 183.5 ms. Throughput stays ~150 req/s at any
  concurrency (two independent client processes gave the same ceiling), so the limit is the server:
  one uvicorn worker, CPU-bound inference behind the GIL. No `--workers` / memory limit is set, so
  the exit-137 OOM scenario from the lab could not occur with this compose file.
- Bare-metal p99 (38 ms) is the Lab 2 figure already in this file (measured with `hey`). It was not
  re-measured here: the host venv (Python 3.11.4) fails at startup with a `SystemError` in
  `copy.deepcopy`. The two p99 values therefore come from different tools and are not a
  like-for-like comparison.

## Day 2 — Lab 4 (Tests)

_Fill in after Lab 4 Step 6:_

| Metric | Value |
|---|---|
| `pytest -m "not slow"` — pass count / duration | |
| `pytest -m slow` — pass count / duration | |
| Branch coverage (domain + service + api) | |
