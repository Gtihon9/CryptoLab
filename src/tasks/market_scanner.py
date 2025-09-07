from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Dict, List, Set

import httpx


EXCLUDED_PREFIXES = ("1000",)  # exclude tokens like 1000PEPE
USDT = "USDT"


@dataclass
class MarketCandidate:
    symbol: str
    binance_volume_usd: float
    bybit_volume_usd: float
    binance_symbol_raw: str
    bybit_symbol_raw: str


def _httpx_client() -> httpx.Client:
    return httpx.Client(
        http2=False,
        timeout=httpx.Timeout(5.0, read=5.0),
        limits=httpx.Limits(max_keepalive_connections=50, max_connections=100),
        headers={"User-Agent": "CryptoLab/market-scanner"},
    )


def _fetch_binance_perp_usdt_bases(client: httpx.Client) -> Set[str]:
    # Binance Futures exchange info (USDT perpetuals)
    url = "https://fapi.binance.com/fapi/v1/exchangeInfo"
    resp = client.get(url)
    resp.raise_for_status()
    data = resp.json()
    bases: Set[str] = set()
    for sym in data.get("symbols", []):
        if sym.get("status") != "TRADING":
            continue
        if sym.get("contractType") != "PERPETUAL":
            continue
        if sym.get("quoteAsset") != USDT:
            continue
        base = sym.get("baseAsset", "")
        if base.startswith(EXCLUDED_PREFIXES):
            continue
        bases.add(base)
    return bases


def _fetch_binance_24h_map(client: httpx.Client) -> Dict[str, float]:
    # Map e.g. BTCUSDT -> quoteVolume (USD-ish)
    url = "https://fapi.binance.com/fapi/v1/ticker/24hr"
    resp = client.get(url)
    resp.raise_for_status()
    tickers = resp.json()
    vol_map: Dict[str, float] = {}
    for t in tickers:
        sym = t.get("symbol", "")
        qv = t.get("quoteVolume")
        try:
            vol_map[sym] = float(qv) if qv is not None else 0.0
        except Exception:
            vol_map[sym] = 0.0
    return vol_map


def _fetch_bybit_linear_usdt_tickers(client: httpx.Client) -> Dict[str, Dict[str, str]]:
    # Bybit v5 linear tickers (USDT/USDC). We'll filter to USDT.
    url = "https://api.bybit.com/v5/market/tickers?category=linear"
    resp = client.get(url)
    resp.raise_for_status()
    data = resp.json()
    result: Dict[str, Dict[str, str]] = {}
    for t in data.get("result", {}).get("list", []):
        symbol = t.get("symbol", "")  # e.g., BTCUSDT
        if not symbol.endswith(USDT):
            continue
        result[symbol] = t
    return result


def _binance_symbol_from_base(base: str) -> str:
    return f"{base}{USDT}"


def _bybit_base_from_symbol(symbol: str) -> str:
    return symbol[:-len(USDT)] if symbol.endswith(USDT) else symbol


def _safe_float(value: object) -> float:
    try:
        return float(value)
    except Exception:
        return 0.0


def find_common_high_volume_futures(min_volume_usd: float = 300_000.0) -> List[MarketCandidate]:
    print("[Scanner] Loading exchanges and markets via HTTP...")
    client = _httpx_client()

    binance_bases = _fetch_binance_perp_usdt_bases(client)
    binance_24h = _fetch_binance_24h_map(client)

    bybit_tickers = _fetch_bybit_linear_usdt_tickers(client)
    bybit_bases: Set[str] = set(_bybit_base_from_symbol(s) for s in bybit_tickers.keys())

    commons: Set[str] = binance_bases & bybit_bases

    candidates: List[MarketCandidate] = []
    print(f"[Scanner] Common bases found: {len(commons)}. Fetching 24h volumes...")
    for base in sorted(commons):
        b_symbol = _binance_symbol_from_base(base)  # BTC -> BTCUSDT
        y_symbol = f"{base}{USDT}"

        vol_b = _safe_float(binance_24h.get(b_symbol))
        bybit_rec = bybit_tickers.get(y_symbol, {})
        vol_y = _safe_float(bybit_rec.get("turnover24h"))  # USD turnover 24h

        if vol_b >= min_volume_usd and vol_y >= min_volume_usd:
            candidates.append(
                MarketCandidate(
                    symbol=f"{base}/{USDT}",
                    binance_volume_usd=round(vol_b, 2),
                    bybit_volume_usd=round(vol_y, 2),
                    binance_symbol_raw=b_symbol,
                    bybit_symbol_raw=y_symbol,
                )
            )

    print(f"[Scanner] Candidates meeting volume threshold: {len(candidates)}")
    return candidates


def write_candidates(path: str, candidates: List[MarketCandidate]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    payload = [c.__dict__ for c in candidates]
    with open(path, "w") as f:
        json.dump(payload, f, indent=2)
    print(f"[Scanner] Wrote {len(candidates)} candidates to {path}")


if __name__ == "__main__":
    cs = find_common_high_volume_futures()
    write_candidates("data/candidates.json", cs)


