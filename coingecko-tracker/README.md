# CoinGecko Tracker

A single-page CoinMarketCap-style tracker. Python generates a self-contained
HTML file; the browser fetches live prices from the public CoinGecko API.

## Build

```bash
python build.py
```

This writes `dist/index.html`. Open that file in any modern browser.

## What you get

- Top-100 coins by market cap, with 24h % change and 7d sparkline.
- Search filter (by name or symbol), currency switcher (USD / EUR / BTC).
- Click any row for a 30-day chart and extra stats.

## Requirements

- Python 3.10+ (standard library only — no `pip install` needed).
- Internet at view time, for CoinGecko and the Lightweight Charts CDN.
- CoinGecko's free tier is rate-limited (~10–30 req/min). The page shows
  a retry banner if you hit it.

## Run the tests

```bash
python -m pytest tests/ -v
```
