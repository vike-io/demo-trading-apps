# demo-trading-apps

A collection of self-contained, web-based clones of popular crypto trading & data apps. One umbrella monorepo, one Python build, one Cloudflare Worker, one URL.

[![Deploy](https://github.com/vike-io/demo-trading-apps/actions/workflows/deploy.yml/badge.svg)](https://github.com/vike-io/demo-trading-apps/actions/workflows/deploy.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](#license)

**Live:** [demo.vike.io](https://demo.vike.io/)

## Cases

| Case | Demo | Data source | Status |
|---|---|---|---|
| [`coingecko-tracker/`](./coingecko-tracker/) | [demo.vike.io/coingecko-tracker/](https://demo.vike.io/coingecko-tracker/) | CoinGecko v3 (`x-cg-demo-api-key`) | ✅ live |
| [`coinmarketcap-tracker/`](./coinmarketcap-tracker/) | [demo.vike.io/coinmarketcap-tracker/](https://demo.vike.io/coinmarketcap-tracker/) | CoinGecko v3 (CMC-styled) | ✅ live |
| [`binance-tracker/`](./binance-tracker/) | [demo.vike.io/binance-tracker/](https://demo.vike.io/binance-tracker/) | Binance v3 public | ✅ live |
| [`bybit-tracker/`](./bybit-tracker/) | [demo.vike.io/bybit-tracker/](https://demo.vike.io/bybit-tracker/) | Bybit v5 public | ✅ live |
| [`okx-tracker/`](./okx-tracker/) | [demo.vike.io/okx-tracker/](https://demo.vike.io/okx-tracker/) | OKX v5 public | ✅ live |

## Architecture

```
demo-trading-apps/
├── build.py                     # orchestrator: discovers cases, renders, writes .dist/
├── serve.py                     # local proxy: serves .dist/, proxies /api/<slug>/*
├── worker.js + wrangler.jsonc   # Cloudflare Worker: same routing in production
├── .env                         # all API keys (gitignored)
│
├── landing/templates/index.html # showcase landing page
├── coingecko-tracker/
│   ├── manifest.json            # { slug, name, config, upstream_base, api_key_env, ... }
│   └── templates/{index,coin}.html
├── binance-tracker/             # same shape
├── bybit-tracker/
├── coinmarketcap-tracker/
├── okx-tracker/
│
└── .dist/                       # build output (gitignored, served to browsers)
```

**Add a new case** = drop a folder with `manifest.json` + `templates/`. The orchestrator finds it, the Worker routes `/api/<slug>/*` automatically, the landing card appears.

## URL routing (local & production)

| Request | Resolves to |
|---|---|
| `GET /` | landing |
| `GET /<slug>/` | case home (e.g. `binance-tracker`) |
| `GET /api/<slug>/<path>` | proxied to that case's `upstream_base` + `<path>`, with optional auth header |

## Run locally

```bash
python build.py
python serve.py        # http://localhost:8000
```

That's it — no `pip install` needed (stdlib only). To use the CoinGecko demo tier, drop `COINGECKO_API_KEY=...` into `.env`. Binance / Bybit / OKX work keyless.

## Deploy

Deployment is automatic on push to `main` via GitHub Actions ([`.github/workflows/deploy.yml`](.github/workflows/deploy.yml)). Required repo secrets:

- `CLOUDFLARE_API_TOKEN` — token with **Workers Scripts: Edit** + **Workers R2 Storage: Edit** + **Account Settings: Read**
- `CLOUDFLARE_ACCOUNT_ID`

To deploy manually:

```bash
python build.py
wrangler secret put COINGECKO_API_KEY   # one-time, per Worker
wrangler deploy
```

## Tech choices

- **Python stdlib** — no `pip install` for the build or local server.
- **Vanilla JS + Fetch** in the browser — no framework, no bundler.
- **TradingView Lightweight Charts** (CDN, ~80 KB) for all candle / line / volume charts.
- **Cloudflare Workers + Static Assets** — single Worker handles routing + proxy + static delivery.
- **Dark theme by default**, light theme toggle, persisted to `localStorage`.

## License

MIT.
