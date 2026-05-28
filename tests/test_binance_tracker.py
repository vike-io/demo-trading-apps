"""Verify the umbrella build produces the new 2-page binance-tracker case."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import build  # noqa: E402


def test_discover_includes_binance_tracker():
    slugs = [c["slug"] for c in build.discover_cases()]
    assert "binance-tracker" in slugs


def test_build_produces_index_and_trade_for_binance_tracker():
    build.DIST.mkdir(exist_ok=True)
    case = next(c for c in build.discover_cases() if c["slug"] == "binance-tracker")
    build.build_case(case)

    out_dir = build.DIST / "binance-tracker"
    index = (out_dir / "index.html").read_text(encoding="utf-8")
    trade = (out_dir / "trade.html").read_text(encoding="utf-8")

    # Index: markets list with SPOT/PERP toggle.
    assert "Binance Tracker" in index
    assert 'id="mode-tabs"' in index
    assert 'data-mode="spot"' in index and 'data-mode="perp"' in index
    assert "loadMarkets" in index
    assert "./trade.html?symbol=" in index  # built dynamically in JS
    # Funding column is hidden by default but present in the header markup.
    assert "Funding" in index
    # Binance yellow accent + dark palette.
    assert "#f0b90b" in index
    assert "#0d1421" in index

    # Trade: chart + book + trades + symbol picker + mode pill.
    assert 'id="chart"' in trade
    assert 'id="symbol"' in trade
    assert 'id="asks"' in trade and 'id="bids"' in trade
    assert 'id="trades"' in trade
    assert 'id="mode-pill"' in trade
    assert "CandlestickSeries" in trade and "HistogramSeries" in trade
    # Perp-only stats present (hidden until mode=perp).
    assert 'id="s-funding"' in trade
    assert 'id="s-mark"' in trade
    assert 'id="s-oi"' in trade
    assert "loadFundingPerp" in trade
    # API base substituted with slug; mode is appended at call time.
    assert 'API_BASE = "/api/binance-tracker"' in trade


def test_routing_manifest_has_per_mode_upstreams_for_binance():
    cases = build.discover_cases()
    build.write_routing_manifest(cases)
    routes = json.loads((build.DIST / "manifest.json").read_text())["routes"]
    bt = next(r for r in routes if r["slug"] == "binance-tracker")

    # Binance now declares two upstreams keyed by mode.
    assert "upstreams" in bt
    assert bt["upstreams"]["spot"]["base"] == "https://api.binance.com/api/v3"
    assert bt["upstreams"]["perp"]["base"] == "https://fapi.binance.com/fapi/v1"
    # No api key needed for Binance public endpoints.
    assert "api_key_env" not in bt
