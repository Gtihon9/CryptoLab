def main() -> None:
    import httpx

    try:
        client = httpx.Client(
            http2=True,
            timeout=httpx.Timeout(2.0, read=2.0),
            limits=httpx.Limits(max_keepalive_connections=100, max_connections=200),
        )
    except Exception:
        client = httpx.Client(
            http2=False,
            timeout=httpx.Timeout(2.0, read=2.0),
            limits=httpx.Limits(max_keepalive_connections=100, max_connections=200),
        )
    r = client.get("https://api.binance.com/api/v3/depth?symbol=BTCUSDT&limit=5")
    print(r.json())


if __name__ == "__main__":
    main()


