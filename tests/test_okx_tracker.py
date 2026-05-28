"""Verify the umbrella build produces the new 2-page okx-tracker case."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import build  # noqa: E402


def test_discover_includes_okx_tracker():
    slugs = [c["slug"] for c in build.discover_cases()]
    assert "okx-tracker" in slugs


def test_build_produces_index_and_trade_for_okx_tracker():
    build.DIST.mkdir(exist_ok=True)
    case = next(c for c in build.discover_cases() if c["slug"] == "okx-tracker")
    build.build_case(case)

    out_dir = build.DIST / "okx-tracker"
    index = (out_dir / "index.html").read_text(encoding="utf-8")
    trade = (out_dir / "trade.html").read_text(encoding="utf-8")

    # Index: markets list + Spot/USDT-Swap toggle.
    assert "OKX Tracker" in index
    assert 'data-mode="spot"' in index and 'data-mode="swap"' in index
    assert "loadMarkets" in index
    assert "./trade.html?symbol=" in index
    assert "#00b6e8" in index  # OKX cyan
    # Default symbol lives in trade.html (not index — index lists all pairs).
    assert '"BTC-USDT"' in trade

    # Trade: chart + book + trades + mode pill + back link + perp-only stats.
    assert 'id="chart"' in trade
    assert 'id="symbol"' in trade
    assert 'id="asks"' in trade and 'id="bids"' in trade
    assert 'id="trades"' in trade
    assert 'id="mode-pill"' in trade
    assert "back-link" in trade
    assert "perp-only" in trade
    assert "INSTTYPE()" in trade
    assert "loadFundingSwap" in trade
    assert "CandlestickSeries" in trade and "HistogramSeries" in trade
