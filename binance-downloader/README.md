# binance-downloader

Pick a symbol, an interval, and a date range; get Binance klines back as a CSV.

## Browser version (deployed)

[demo.vike.io/binance-downloader/](https://demo.vike.io/binance-downloader/)

Fills out a form, streams paginated requests through this monorepo's `/api/binance-downloader/` Cloudflare Worker proxy, assembles the CSV in memory, and triggers a browser download via Blob + `<a download>`. No backend processing involved.

## Python CLI (local)

Same column layout, runs on your machine, writes the CSV directly to disk:

```bash
cd binance-downloader
python download.py BTCUSDT 1h 2024-01-01 2024-06-30 btc-1h.csv
```

Standard library only. Paginates Binance's 1000-row limit transparently and reports progress on stderr.

| Arg | Meaning |
|---|---|
| `symbol` | Binance spot pair (e.g. `BTCUSDT`, `ETHUSDT`) |
| `interval` | `1m` `5m` `15m` `1h` `4h` `1d` `1w` etc. |
| `start_date` | `YYYY-MM-DD` (inclusive, UTC midnight) |
| `end_date` | `YYYY-MM-DD` (exclusive, UTC midnight) |
| `out_csv` | Path to write |

## CSV schema

| Column | Source field |
|---|---|
| `open_time` | row[0] (ms epoch) |
| `open` | row[1] |
| `high` | row[2] |
| `low` | row[3] |
| `close` | row[4] |
| `volume` | row[5] |
| `close_time` | row[6] (ms epoch) |
| `quote_volume` | row[7] |
| `trade_count` | row[8] |
| `taker_buy_volume` | row[9] |
| `taker_buy_quote_volume` | row[10] |

(Binance's 12th "ignore" field is dropped from both versions.)
