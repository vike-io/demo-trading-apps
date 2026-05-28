"""Binance klines → CSV. Standard library only.

Usage:
    python download.py BTCUSDT 1h 2024-01-01 2024-06-30 out.csv

  symbol     Binance spot pair (e.g. BTCUSDT, ETHUSDT)
  interval   1m | 5m | 15m | 1h | 4h | 1d | 1w  (any Binance interval)
  start_date YYYY-MM-DD (inclusive, UTC midnight)
  end_date   YYYY-MM-DD (exclusive, UTC midnight)
  out_csv    output path

Binance caps klines at 1000 rows/request, so this script paginates
by chunking the date window. Same CSV shape as the browser version
in templates/index.html.
"""

from __future__ import annotations

import csv
import json
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone


BINANCE = "https://api.binance.com/api/v3/klines"
LIMIT = 1000

# Stay aligned with the JS schema in templates/index.html.
CSV_COLUMNS = [
    "open_time",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "close_time",
    "quote_volume",
    "trade_count",
    "taker_buy_volume",
    "taker_buy_quote_volume",
]

INTERVAL_MS = {
    "1m": 60_000,
    "3m": 180_000,
    "5m": 300_000,
    "15m": 900_000,
    "30m": 1_800_000,
    "1h": 3_600_000,
    "2h": 7_200_000,
    "4h": 14_400_000,
    "6h": 21_600_000,
    "8h": 28_800_000,
    "12h": 43_200_000,
    "1d": 86_400_000,
    "3d": 259_200_000,
    "1w": 604_800_000,
    "1M": 2_592_000_000,
}


def parse_date(s: str) -> int:
    """YYYY-MM-DD → epoch milliseconds at UTC midnight."""
    dt = datetime.strptime(s, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    return int(dt.timestamp() * 1000)


def fetch_chunk(symbol: str, interval: str, start_ms: int, end_ms: int) -> list[list]:
    qs = urllib.parse.urlencode({
        "symbol": symbol,
        "interval": interval,
        "startTime": start_ms,
        "endTime": end_ms,
        "limit": LIMIT,
    })
    req = urllib.request.Request(f"{BINANCE}?{qs}", headers={"accept": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as res:
        return json.loads(res.read())


def stream(symbol: str, interval: str, start_ms: int, end_ms: int):
    if interval not in INTERVAL_MS:
        raise SystemExit(f"unsupported interval: {interval!r}")
    step = INTERVAL_MS[interval] * LIMIT
    cursor = start_ms
    page = 0
    while cursor < end_ms:
        page += 1
        chunk_end = min(cursor + step, end_ms)
        rows = fetch_chunk(symbol, interval, cursor, chunk_end)
        if not rows:
            break
        sys.stderr.write(f"  page {page}: {len(rows)} rows, {datetime.fromtimestamp(rows[0][0]/1000, tz=timezone.utc):%Y-%m-%d}…{datetime.fromtimestamp(rows[-1][0]/1000, tz=timezone.utc):%Y-%m-%d}\n")
        for r in rows:
            # Binance returns 12 columns; we keep the first 11 (drop the "ignore" field).
            yield r[:11]
        # Advance past the last row we received (avoid re-fetching it).
        cursor = rows[-1][0] + INTERVAL_MS[interval]
        # Be polite — Binance public limit is generous but throttle anyway.
        time.sleep(0.15)


def main() -> None:
    if len(sys.argv) != 6:
        sys.stderr.write(__doc__)
        sys.exit(2)
    _, symbol, interval, start_s, end_s, out_path = sys.argv
    start_ms = parse_date(start_s)
    end_ms = parse_date(end_s)
    if start_ms >= end_ms:
        raise SystemExit("start_date must be before end_date")

    sys.stderr.write(f"Fetching {symbol} {interval} {start_s} → {end_s}\n")
    n = 0
    with open(out_path, "w", encoding="utf-8", newline="") as fp:
        w = csv.writer(fp)
        w.writerow(CSV_COLUMNS)
        for row in stream(symbol, interval, start_ms, end_ms):
            w.writerow(row)
            n += 1
    sys.stderr.write(f"Wrote {n} rows → {out_path}\n")


if __name__ == "__main__":
    main()
