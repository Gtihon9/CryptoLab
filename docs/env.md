# Environment variables

Copy `.env.example` to `.env` and fill values. For ccxt-based checks, set:

- `BINANCE_API_KEY`, `BINANCE_API_SECRET`
- `BYBIT_API_KEY`, `BYBIT_API_SECRET`
- `OKX_API_KEY`, `OKX_API_SECRET`, `OKX_API_PASSWORD` (for OKX)
- Optional: `CCXT_SYMBOL` (default: `BTC/USDT`)

These are used by `test/latency/check_latency_ccxt.py`. Keys are only required for private endpoints, but ccxt may still need them for some markets/configs.
