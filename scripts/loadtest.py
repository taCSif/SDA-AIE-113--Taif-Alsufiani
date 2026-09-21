"""Minimal load generator: keep-alive POSTs, percentile report.

Stands in for `hey` (not installed / no public image). Uses http.client so
connections are reused, the way hey does -- otherwise TCP setup dominates
the latency numbers we are trying to measure.
"""
import argparse
import http.client
import json
import statistics
import threading
import time

p = argparse.ArgumentParser()
p.add_argument("--host", default="fraud-api")
p.add_argument("--port", type=int, default=8000)
p.add_argument("--path", default="/v1/predict")
p.add_argument("--duration", type=float, default=30.0)
p.add_argument("--concurrency", type=int, default=10)
args = p.parse_args()

BODY = json.dumps({"transaction_id": "TXN-TEST-1", "amount_sar": 500, "is_night": 0})
HEADERS = {"Content-Type": "application/json"}

latencies: list[float] = []
statuses: dict[int, int] = {}
errors = 0
lock = threading.Lock()
deadline = time.time() + args.duration


def worker():
    global errors
    conn = http.client.HTTPConnection(args.host, args.port, timeout=10)
    local_lat, local_st, local_err = [], {}, 0
    while time.time() < deadline:
        t0 = time.perf_counter()
        try:
            conn.request("POST", args.path, body=BODY, headers=HEADERS)
            resp = conn.getresponse()
            resp.read()
            local_lat.append((time.perf_counter() - t0) * 1000)
            local_st[resp.status] = local_st.get(resp.status, 0) + 1
        except Exception:
            local_err += 1
            try:
                conn.close()
            except Exception:
                pass
            conn = http.client.HTTPConnection(args.host, args.port, timeout=10)
    with lock:
        latencies.extend(local_lat)
        for k, v in local_st.items():
            statuses[k] = statuses.get(k, 0) + v
        errors += local_err


threads = [threading.Thread(target=worker) for _ in range(args.concurrency)]
t_start = time.time()
for t in threads:
    t.start()
for t in threads:
    t.join()
elapsed = time.time() - t_start

latencies.sort()


def pct(p_):
    if not latencies:
        return float("nan")
    return latencies[min(len(latencies) - 1, int(len(latencies) * p_ / 100))]


print(f"requests   : {len(latencies)}")
print(f"duration   : {elapsed:.1f}s")
print(f"throughput : {len(latencies) / elapsed:.0f} req/s")
print(f"statuses   : {statuses}  errors={errors}")
print(f"p50        : {pct(50):.1f} ms")
print(f"p95        : {pct(95):.1f} ms")
print(f"p99        : {pct(99):.1f} ms")
print(f"max        : {latencies[-1]:.1f} ms" if latencies else "max: n/a")
print(f"mean       : {statistics.mean(latencies):.1f} ms" if latencies else "")
