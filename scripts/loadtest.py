"""Minimal load generator — a stand-in for `hey` on machines without it.

    python scripts/loadtest.py --n 2000 --c 25

Equivalent hey invocation (use it if you have hey installed):

    hey -n 2000 -c 25 -m POST -T application/json \
        -d '{"transaction_id":"TXN-2026-00042","amount_sar":500,"is_night":0}' \
        http://127.0.0.1:8000/v1/predict

While the load runs it also probes /v1/health from a separate thread. That
probe is the tell for the `async def` trap: if the predict route blocks the
event loop, liveness latency explodes and Kubernetes restarts a pod that is
merely busy.
"""
import argparse
import json
import math
import statistics
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor

PAYLOAD = json.dumps(
    {"transaction_id": "TXN-2026-00042", "amount_sar": 500.0, "is_night": 0}
).encode()


def one_request(url: str) -> tuple[float, int]:
    req = urllib.request.Request(url, data=PAYLOAD, headers={"content-type": "application/json"})
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            response.read()
            status = response.status
    except urllib.error.HTTPError as exc:
        status = exc.code
    except OSError:
        status = 0
    return (time.perf_counter() - t0) * 1000, status


def pct(values: list[float], p: float) -> float:
    ordered = sorted(values)
    return ordered[min(int(len(ordered) * p / 100), len(ordered) - 1)]


def health_probe(base: str, stop: threading.Event, out: list[float]) -> None:
    while not stop.is_set():
        t0 = time.perf_counter()
        try:
            urllib.request.urlopen(f"{base}/v1/health", timeout=30).read()
            out.append((time.perf_counter() - t0) * 1000)
        except OSError:
            out.append(math.nan)
        time.sleep(0.05)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="http://127.0.0.1:8000")
    parser.add_argument("--n", type=int, default=2000)
    parser.add_argument("--c", type=int, default=25)
    args = parser.parse_args()

    url = f"{args.base}/v1/predict"
    one_request(url)  # discard one request so the client side is warm too

    stop = threading.Event()
    health_ms: list[float] = []
    probe = threading.Thread(target=health_probe, args=(args.base, stop, health_ms), daemon=True)
    probe.start()

    t0 = time.perf_counter()
    with ThreadPoolExecutor(max_workers=args.c) as pool:
        results = list(pool.map(lambda _: one_request(url), range(args.n)))
    elapsed = time.perf_counter() - t0

    stop.set()
    probe.join(timeout=2)

    latencies = [ms for ms, _ in results]
    ok = sum(1 for _, status in results if status == 200)
    healthy = [ms for ms in health_ms if not math.isnan(ms)]

    print(f"concurrency      {args.c}")
    print(f"requests         {args.n} ({ok} x 200, {args.n - ok} non-200)")
    print(f"duration_s       {elapsed:.2f}")
    print(f"rps              {args.n / elapsed:.1f}")
    print(f"predict_p50_ms   {statistics.median(latencies):.1f}")
    print(f"predict_p95_ms   {pct(latencies, 95):.1f}")
    print(f"predict_p99_ms   {pct(latencies, 99):.1f}")
    if healthy:
        print(f"health_p50_ms    {statistics.median(healthy):.1f}")
        print(f"health_max_ms    {max(healthy):.1f}   <- liveness probe under load")


if __name__ == "__main__":
    main()
