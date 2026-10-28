"""Quick load test without k6 (same traffic as tools/load/chart.js).

    uv run python tools/load/quick_load.py --url http://localhost:8000 --rate 50 --seconds 30

Prints p50, p95 and p99 latency and the error count. Every request uses a new
birth moment, so the chart cache does not help.
"""

import argparse
import asyncio
import statistics
import time
from datetime import date, timedelta

import httpx


def body(i: int) -> dict:
    d = date(1950, 1, 1) + timedelta(days=i % 30000)
    return {
        "birth": {
            "birth_date": d.isoformat(),
            "birth_time": f"{i % 24:02d}:{(i * 7) % 60:02d}",
            "latitude": 8 + i % 25,
            "longitude": 68 + i % 29,
            "tz_name": "Asia/Kolkata",
        },
        "vargas": ["D1", "D9"],
    }


async def main(url: str, rate: int, seconds: int) -> int:
    lat: list[float] = []
    errors = 0
    seed = int(time.time())

    async with httpx.AsyncClient(base_url=url, timeout=10, limits=httpx.Limits(max_connections=200)) as client:

        async def one(i: int) -> None:
            nonlocal errors
            t0 = time.perf_counter()
            try:
                r = await client.post("/v1/charts", json=body(seed + i), headers={"X-CSRF": "1"})
                if r.status_code != 200:
                    errors += 1
            except httpx.HTTPError:
                errors += 1
            lat.append((time.perf_counter() - t0) * 1000)

        tasks = []
        start = time.perf_counter()
        for i in range(rate * seconds):
            await asyncio.sleep(max(0.0, start + i / rate - time.perf_counter()))
            tasks.append(asyncio.create_task(one(i)))
        await asyncio.gather(*tasks)

    q = statistics.quantiles(lat, n=100)
    print(f"requests={len(lat)} errors={errors} p50={q[49]:.0f}ms p95={q[94]:.0f}ms p99={q[98]:.0f}ms max={max(lat):.0f}ms")
    return 0 if q[94] < 300 and errors <= len(lat) * 0.01 else 1


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://localhost:8000")
    ap.add_argument("--rate", type=int, default=50)
    ap.add_argument("--seconds", type=int, default=30)
    a = ap.parse_args()
    raise SystemExit(asyncio.run(main(a.url, a.rate, a.seconds)))
