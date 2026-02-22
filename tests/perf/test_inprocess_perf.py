import time
from fastapi.testclient import TestClient
from statistics import quantiles
from app.main import app

client = TestClient(app)

def test_healthz_p95_under_50ms():
    durations = []
    for _ in range(100):
        t0 = time.perf_counter()
        r = client.get("/healthz")
        assert r.status_code == 200
        durations.append((time.perf_counter() - t0) * 1000.0)
    p95 = quantiles(durations, n=20)[-1]
    assert p95 < 50.0
