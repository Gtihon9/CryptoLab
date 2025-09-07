#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
import time
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional

import httpx
from pathlib import Path
from dotenv import load_dotenv


@dataclass
class SpreadSample:
    base: str
    symbol: str
    binance_bid: Optional[float]
    binance_ask: Optional[float]
    bybit_bid: Optional[float]
    bybit_ask: Optional[float]
    mid_binance: Optional[float]
    mid_bybit: Optional[float]
    spread_abs: Optional[float]
    spread_bps: Optional[float]


def client() -> httpx.Client:
    return httpx.Client(
        http2=False,
        timeout=httpx.Timeout(5.0, read=5.0),
        limits=httpx.Limits(max_keepalive_connections=50, max_connections=100),
        headers={"User-Agent": "CryptoLab/spread-loop"},
    )


def binance_ob_top(c: httpx.Client, symbol: str) -> Dict[str, Optional[float]]:
    url = f"https://fapi.binance.com/fapi/v1/depth?symbol={symbol}&limit=5"
    try:
        r = c.get(url)
        r.raise_for_status()
        d = r.json()
        bids = d.get("bids", [])
        asks = d.get("asks", [])
        return {
            "bid": float(bids[0][0]) if bids else None,
            "ask": float(asks[0][0]) if asks else None,
        }
    except Exception:
        return {"bid": None, "ask": None}


def bybit_ob_top(c: httpx.Client, symbol: str) -> Dict[str, Optional[float]]:
    url = f"https://api.bybit.com/v5/market/orderbook?category=linear&symbol={symbol}&limit=5"
    try:
        r = c.get(url)
        r.raise_for_status()
        data = r.json()
        bids = data.get("result", {}).get("b", [])
        asks = data.get("result", {}).get("a", [])
        return {
            "bid": float(bids[0][0]) if bids else None,
            "ask": float(asks[0][0]) if asks else None,
        }
    except Exception:
        return {"bid": None, "ask": None}


def mid(bid: Optional[float], ask: Optional[float]) -> Optional[float]:
    if bid is None or ask is None:
        return None
    return (bid + ask) / 2.0


def compute_spreads(
    candidates_path: str = "data/candidates.json",
    min_bps: Optional[float] = None,
    max_bps: Optional[float] = None,
) -> List[SpreadSample]:
    if not os.path.exists(candidates_path):
        return []
    with open(candidates_path, "r") as f:
        candidates = json.load(f)

    c = client()
    out: List[SpreadSample] = []
    for cand in candidates:
        base = cand.get("symbol", "").split("/")[0]
        b_symbol = cand.get("binance_symbol_raw")
        y_symbol = cand.get("bybit_symbol_raw")
        if not b_symbol or not y_symbol:
            continue

        ob_b = binance_ob_top(c, b_symbol)
        ob_y = bybit_ob_top(c, y_symbol)
        mid_b = mid(ob_b["bid"], ob_b["ask"]) if ob_b else None
        mid_y = mid(ob_y["bid"], ob_y["ask"]) if ob_y else None

        if mid_b is None or mid_y is None:
            spread_abs = None
            spread_bps = None
        else:
            spread_abs = mid_b - mid_y
            denom = (mid_b + mid_y) / 2.0
            spread_bps = (spread_abs / denom) * 10_000.0 if denom else None

        # Apply thresholds and signal immediately if within range
        include = True
        if min_bps is not None or max_bps is not None:
            if spread_bps is None:
                include = False
            else:
                v = abs(spread_bps)
                if min_bps is not None and v < min_bps:
                    include = False
                if max_bps is not None and v > max_bps:
                    include = False
            if include:
                print("\a", end="")
                print(f"[Signal] {base}/USDT within range: {round(spread_bps, 2) if spread_bps is not None else None} bps")

                out.append(SpreadSample(
                    base=base,
                    symbol=f"{base}/USDT",
                    binance_bid=ob_b["bid"],
                    binance_ask=ob_b["ask"],
                    bybit_bid=ob_y["bid"],
                    bybit_ask=ob_y["ask"],
                    mid_binance=mid_b,
                    mid_bybit=mid_y,
                    spread_abs=spread_abs,
                    spread_bps=round(spread_bps, 2) if spread_bps is not None else None,
                ))

        if not include:
            print(f"{base}")
            continue

    return out


def write_spreads(path: str, samples: Iterable[SpreadSample]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    payload = [s.__dict__ for s in samples]
    with open(path, "w") as f:
        json.dump(payload, f, indent=2)


def main() -> None:
    # Load variables from .env at repo root
    project_root_env = Path(__file__).resolve().parents[1] / ".env"
    load_dotenv(dotenv_path=project_root_env)
    out_path = os.environ.get("SPREADS_OUT", "data/spreads.json")
    interval = float(os.environ.get("SPREADS_INTERVAL", "30"))
    min_bps_env = os.environ.get("SPREADS_MIN_BPS")
    max_bps_env = os.environ.get("SPREADS_MAX_BPS")
    min_bps = float(min_bps_env) if min_bps_env not in (None, "") else None
    max_bps = float(max_bps_env) if max_bps_env not in (None, "") else None
    print(f"[SpreadLoop] Starting. Interval={interval}s, out={out_path}, min_bps={min_bps}, max_bps={max_bps}")
    try:
        while True:
            print(f"[SpreadLoop] Run at {time.strftime('%Y-%m-%d %H:%M:%S')}")
            samples = compute_spreads(min_bps=min_bps, max_bps=max_bps)
            write_spreads(out_path, samples)
            top = sorted([x for x in samples if x.spread_bps is not None], key=lambda x: abs(x.spread_bps), reverse=True)[:5]
            print(f"[SpreadLoop] Saved {len(samples)} samples. Top (bps):",
                  [{"symbol": t.symbol, "bps": t.spread_bps} for t in top])
            time.sleep(interval)
    except KeyboardInterrupt:
        print("[SpreadLoop] Stopped")


if __name__ == "__main__":
    main()


