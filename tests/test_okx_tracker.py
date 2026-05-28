"""Verify the umbrella build produces a working okx-tracker case."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import build  # noqa: E402


def test_discover_includes_okx_tracker():
    slugs = [c["slug"] for c in build.discover_cases()]
    assert "okx-tracker" in slugs


def test_build_produces_okx_tracker_index():
    build.DIST.mkdir(exist_ok=True)
    case = next(c for c in build.discover_cases() if c["slug"] == "okx-tracker")
    build.build_case(case)

    out = build.DIST / "okx-tracker" / "index.html"
    assert out.exists()
    html = out.read_text(encoding="utf-8")

    assert 'const API = "/api/okx-tracker"' in html
    assert "OKX Tracker" in html
    # OKX uses hyphenated instIds (BTC-USDT not BTCUSDT).
    assert '"BTC-USDT"' in html

    # SPOT pill in header.
    assert "SPOT" in html

    # Standard chart + book + trades + markets skeleton.
    assert 'id="chart"' in html
    assert 'id="symbol"' in html
    assert 'id="asks"' in html and 'id="bids"' in html
    assert 'id="trades"' in html
    assert 'id="pairs-tbody"' in html
    assert "CandlestickSeries" in html
    assert "HistogramSeries" in html

    # OKX cyan accent.
    assert "#00b6e8" in html
