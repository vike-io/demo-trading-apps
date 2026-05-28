"""Verify the umbrella build produces a working binance-tracker case."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import build  # noqa: E402


def test_discover_includes_binance_tracker():
    slugs = [c["slug"] for c in build.discover_cases()]
    assert "binance-tracker" in slugs


def test_build_produces_index_for_binance_tracker():
    build.DIST.mkdir(exist_ok=True)
    case = next(c for c in build.discover_cases() if c["slug"] == "binance-tracker")
    build.build_case(case)

    out = build.DIST / "binance-tracker" / "index.html"
    assert out.exists()
    html = out.read_text(encoding="utf-8")

    # API prefix substituted with the slug.
    assert 'const API = "/api/binance-tracker"' in html

    # Brand + symbol substituted.
    assert "Binance Tracker" in html
    assert '"BTCUSDT"' in html

    # Intervals list substituted as JSON.
    assert '"1m"' in html and '"1h"' in html and '"1d"' in html

    # Skeleton checks: candle chart, order book, trades, symbol picker.
    assert 'id="chart"' in html
    assert 'id="symbol"' in html
    assert 'id="asks"' in html and 'id="bids"' in html
    assert 'id="trades"' in html
    assert 'id="spread"' in html
    assert "CandlestickSeries" in html
    assert "HistogramSeries" in html

    # Theme + dark palette + Binance yellow accent.
    assert "#0d1421" in html  # bg
    assert "#f0b90b" in html  # binance accent

    # Polling logic present.
    assert "startPolling" in html and "stopPolling" in html

    # Markets table below the chart with click-to-switch.
    assert 'id="pairs-tbody"' in html
    assert "renderPairs" in html
    assert "Markets · USDT" in html


def test_routing_manifest_includes_binance_tracker_with_no_key():
    cases = build.discover_cases()
    build.write_routing_manifest(cases)
    import json
    routes = json.loads((build.DIST / "manifest.json").read_text())["routes"]
    bt = next(r for r in routes if r["slug"] == "binance-tracker")
    assert bt["upstream_base"] == "https://api.binance.com/api/v3"
    assert "api_key_env" not in bt  # Binance public is keyless
