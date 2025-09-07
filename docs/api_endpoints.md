# API endpoints for target exchanges/DEXes

## Binance (Spot/CEX)
- Docs: `https://binance-docs.github.io/apidocs`

### Public market data
- Ticker price (last):
  - GET `https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT`
- Order book (depth):
  - GET `https://api.binance.com/api/v3/depth?symbol=BTCUSDT&limit=5`

### Trading (requires API key + HMAC)
- Place order: POST `/api/v3/order``
- Cancel order: DELETE `/api/v3/order`
- Account info/balances: GET `/api/v3/account`

Rate limits: request-weight based, per-minute buckets. See docs for exact weights per endpoint.

---

## Bybit (Perp/CEX)
- Docs: `https://bybit-exchange.github.io/docs`

### Public market data (v5)
- Tickers:
  - GET `https://api.bybit.com/v5/market/tickers?category=linear&symbol=BTCUSDT`
- Order book:
  - GET `https://api.bybit.com/v5/market/orderbook?category=linear&symbol=BTCUSDT`

### Trading (requires API key + signature)
- Place order: POST `/v5/order/create`
- Cancel order: POST `/v5/order/cancel`
- Wallet balance: GET `/v5/account/wallet-balance`

Rate limits: per-endpoint limits with IP/key buckets. Check docs for latest numbers.

---

## Uniswap V3 (DEX, The Graph)
- Subgraph: `https://thegraph.com/hosted-service/subgraph/uniswap/uniswap-v3`

### Example GraphQL query (recent swaps for a pool)
```graphql
{
  swaps(first: 5, orderBy: timestamp, orderDirection: desc,
        where: { pool: "0x8ad599c3a0ff1de082011efddc58f1908eb6e6d8" }) {
    id
    amount0
    amount1
    amountUSD
    timestamp
  }
}
```

Rate limits: subject to The Graph hosted service policies. Consider retries/backoff.

---

## dYdX (Perp DEX)
- Docs: `https://docs.dydx.exchange`

### Public market data (v3)
- Markets: GET `https://api.dydx.exchange/v3/markets`
- Order book: GET `https://api.dydx.exchange/v3/orderbook/BTC-USD`

### Trading (requires auth & signature)
- Orders: POST `/v3/orders`
- Cancel: DELETE `/v3/orders/{id}`
- Account: GET `/v3/accounts/{address}`

Rate limits: endpoint-specific; use backoff and idempotency keys where available.

---

## Notes
- Start with public data endpoints for health checks and latency baselines.
- Production trading requires authenticated flows, clock sync, and robust error handling.

---

## Latency benchmarks (50 trials)

Artifacts:
- `test/latency/results/httpx_50.json`
- `test/latency/results/requests_50.json`
- `test/latency/results/ccxt_50.json`

These contain aggregated avg/min/max and success rate per endpoint/exchange from local runs.