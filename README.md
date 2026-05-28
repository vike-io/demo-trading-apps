# vike-io / demo-trading-apps

A growing collection of self-contained, web-based clones of popular crypto trading & data apps.
Each one is a working demo you can run locally with Python or deploy to a Cloudflare Worker.

## Cases

| Slug | What it clones | Data source | Status |
|---|---|---|---|
| [`coingecko-tracker/`](./coingecko-tracker/) | CoinGecko-style market tracker | CoinGecko v3 | ✅ live |
| `coinmarketcap/` | CoinMarketCap-style market tracker | TBD | planned |
| `binance/` | Binance spot UI | Binance public API | planned |
| `bybit/` | Bybit perpetuals UI | Bybit v5 | planned |
| `okx/` | OKX exchange UI | OKX v5 | planned |

## Shared shape

Every case is the same shape so they're easy to navigate and deploy together:

```
<slug>/
├── build.py             # generates dist/ from templates/
├── serve.py             # local Python proxy: serves dist/ and forwards /api/* to upstream
├── templates/           # source HTML with {{placeholders}}
├── tests/test_build.py  # pytest for the build step
├── worker.js            # Cloudflare Worker: same proxy + static assets
├── wrangler.jsonc       # Worker config
├── README.md            # case-specific docs
├── .env.example         # which secrets the case needs
└── .env                 # gitignored
```

## Run a case locally

```bash
cd coingecko-tracker
python build.py
python serve.py     # then open http://localhost:8000
```

## Deploy a case

```bash
cd coingecko-tracker
python build.py
wrangler secret put COINGECKO_API_KEY    # one-time
wrangler deploy
```

## Tech choices

- **Python stdlib** for the build step and local proxy — no `pip install` needed.
- **Vanilla JS** in the browser, no framework.
- **TradingView Lightweight Charts** for price/volume charts (CDN, ~80 KB).
- **Cloudflare Workers + Static Assets** for deploy (free tier, edge, no cold start).
- **Dark theme by default**, light theme toggle.

## License

MIT (see individual cases for any third-party assets).
