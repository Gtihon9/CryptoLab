# Architecture Overview

- `src/tasks/market_scanner.py`: builds `data/candidates.json` with symbols common to Binance/Bybit USDT perpetuals with 24h volume >= $300k on both.
- `scripts/spread_loop.py`: infinite loop reading candidates, fetching top-of-book from Binance/Bybit via httpx, computing spreads and saving `data/spreads.json`. Supports env filters `SPREADS_MIN_BPS`, `SPREADS_MAX_BPS` and interval `SPREADS_INTERVAL`.
- `test/latency/`: latency tools for REST/httpx/ccxt.
- `docs/`: API references and notes.

Data flow:
1) Scanner ⇒ `data/candidates.json`
2) Spread loop ⇒ `data/spreads.json`

Run order:
- `make install`
- `make scan`
- `make run-spread`
