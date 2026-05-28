"""Verify the umbrella build produces the new 2-page bybit-tracker case."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import build  # noqa: E402


def test_discover_includes_bybit_tracker():
    slugs = [c["slug"] for c in build.discover_cases()]
    assert "bybit-tracker" in slugs


def test_build_produces_index_and_trade_for_bybit_tracker():
    build.DIST.mkdir(exist_ok=True)
    case = next(c for c in build.discover_cases() if c["slug"] == "bybit-tracker")
    build.build_case(case)

    out_dir = build.DIST / "bybit-tracker"
    index = (out_dir / "index.html").read_text(encoding="utf-8")
    trade = (out_dir / "trade.html").read_text(encoding="utf-8")

    # Index: markets list + Spot/USDT-Perp toggle.
    assert "Bybit Tracker" in index
    assert 'data-mode="spot"' in index and 'data-mode="perp"' in index
    assert "loadMarkets" in index
    assert "./trade.html?symbol=" in index
    assert "Funding" in index
    assert "#ffce3a" in index  # Bybit yellow

    # Trade: chart + book + trades + mode pill + back link + perp-only stats.
    assert 'id="chart"' in trade
    assert 'id="symbol"' in trade
    assert 'id="asks"' in trade and 'id="bids"' in trade
    assert 'id="trades"' in trade
    assert 'id="mode-pill"' in trade
    assert "back-link" in trade
    assert "CandlestickSeries" in trade and "HistogramSeries" in trade
    assert "perp-only" in trade
    assert "CATEGORY()" in trade  # category param resolved dynamically per mode
