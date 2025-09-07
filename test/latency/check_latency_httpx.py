from __future__ import annotations

import json
import time
import argparse
from statistics import mean
from typing import Dict, Iterable, List

import httpx


def measure_httpx_latency(client: httpx.Client, url: str) -> Dict[str, str | float | int]:
    start = time.monotonic()
    try:
        response = client.get(url)
        latency_ms = (time.monotonic() - start) * 1000.0
        http_version = getattr(response, "http_version", "1.1")
        return {
            "url": url,
            "status": response.status_code,
            "latency_ms": round(latency_ms, 1),
            "http": http_version,
        }
    except Exception as exc:  # noqa: BLE001
        latency_ms = (time.monotonic() - start) * 1000.0
        return {
            "url": url,
            "status": -1,
            "latency_ms": round(latency_ms, 1),
            "error": f"{type(exc).__name__}: {exc}",
        }


def run_once(endpoints: Iterable[str]) -> List[Dict[str, str | float | int]]:
    # Force HTTP/1.1 for consistent latency measurements
    client = httpx.Client(
        http2=False,
        timeout=httpx.Timeout(2.0, read=2.0),
        limits=httpx.Limits(max_keepalive_connections=100, max_connections=200),
    )
    return [measure_httpx_latency(client, e) for e in endpoints]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trials", type=int, default=1, help="Number of requests per endpoint")
    args = parser.parse_args()

    endpoints = [
        # Binance
        "https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT",
        "https://api.binance.com/api/v3/depth?symbol=BTCUSDT&limit=5",
        # Bybit
        "https://api.bybit.com/v5/market/tickers?category=linear&symbol=BTCUSDT",
        "https://api.dydx.exchange/v3/orderbook/BTC-USD",
    ]

    if args.trials <= 1:
        print(json.dumps(run_once(endpoints), indent=2))
        return

    # Aggregate over multiple trials
    series: Dict[str, List[float]] = {e: [] for e in endpoints}
    statuses: Dict[str, List[int]] = {e: [] for e in endpoints}
    for _ in range(args.trials):
        results = run_once(endpoints)
        for res in results:
            series[res["url"]].append(float(res["latency_ms"]))
            statuses[res["url"]].append(int(res["status"]))

    summary = []
    for url in endpoints:
        values = series[url]
        codes = statuses[url]
        successes = sum(1 for c in codes if c == 200)
        summary.append({
            "url": url,
            "trials": len(values),
            "avg_ms": round(mean(values), 1) if values else None,
            "min_ms": round(min(values), 1) if values else None,
            "max_ms": round(max(values), 1) if values else None,
            "success_rate": round(100.0 * successes / len(values), 1) if values else 0.0,
        })

    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()


