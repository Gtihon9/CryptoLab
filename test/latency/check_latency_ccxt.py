from __future__ import annotations

import json
import os
import time
import argparse
from statistics import mean
from typing import Dict, List

import ccxt
from dotenv import load_dotenv


def measure_ccxt_latency(exchange_id: str, symbol: str = "BTC/USDT") -> Dict[str, float | int | str]:
    start = time.monotonic()
    try:
        exchange_class = getattr(ccxt, exchange_id)
        api_key = os.getenv(f"{exchange_id.upper()}_API_KEY", "")
        api_secret = os.getenv(f"{exchange_id.upper()}_API_SECRET", "")
        password = os.getenv(f"{exchange_id.upper()}_API_PASSWORD", "")  # e.g., for OKX

        exchange = exchange_class({
            "apiKey": api_key,
            "secret": api_secret,
            "password": password or None,
            "enableRateLimit": True,
            "options": {"defaultType": "swap"},  # better for perp symbols
        })

        # Public request (ticker) — includes network latency and exchange processing
        ticker = exchange.fetch_ticker(symbol)
        latency_ms = (time.monotonic() - start) * 1000.0
        return {
            "exchange": exchange_id,
            "symbol": symbol,
            "latency_ms": round(latency_ms, 1),
            "last": ticker.get("last"),
        }
    except Exception as exc:  # noqa: BLE001
        latency_ms = (time.monotonic() - start) * 1000.0
        return {
            "exchange": exchange_id,
            "symbol": symbol,
            "latency_ms": round(latency_ms, 1),
            "error": f"{type(exc).__name__}: {exc}",
        }


def main() -> None:
    load_dotenv()
    parser = argparse.ArgumentParser()
    parser.add_argument("--trials", type=int, default=1, help="Number of requests per exchange")
    args = parser.parse_args()
    # Choose the exchanges you want to test; add/remove as needed
    exchanges: List[str] = [
        "binance",
        "bybit",
    ]

    # Adjust symbols per exchange if needed (perp vs spot)
    symbol = os.getenv("CCXT_SYMBOL", "BTC/USDT")
    if args.trials <= 1:
        results = [measure_ccxt_latency(e, symbol) for e in exchanges]
        print(json.dumps(results, indent=2))
        return

    series: Dict[str, List[float]] = {e: [] for e in exchanges}
    errors: Dict[str, int] = {e: 0 for e in exchanges}
    for _ in range(args.trials):
        for ex in exchanges:
            res = measure_ccxt_latency(ex, symbol)
            series[ex].append(float(res["latency_ms"]))
            if "error" in res:
                errors[ex] += 1

    summary = []
    for ex in exchanges:
        values = series[ex]
        failures = errors[ex]
        successes = len(values) - failures
        summary.append({
            "exchange": ex,
            "symbol": symbol,
            "trials": len(values),
            "avg_ms": round(mean(values), 1) if values else None,
            "min_ms": round(min(values), 1) if values else None,
            "max_ms": round(max(values), 1) if values else None,
            "success_rate": round(100.0 * successes / len(values), 1) if values else 0.0,
        })

    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()


