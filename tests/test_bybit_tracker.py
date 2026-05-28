"""Verify the umbrella build produces a working bybit-tracker case."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import build  # noqa: E402


def test_discover_includes_bybit_tracker():
    slugs = [c["slug"] for c in build.discover_cases()]
    assert "bybit-tracker" in slugs


def test_build_produces_bybit_tracker_index():
    build.DIST.mkdir(exist_ok=True)
    case = next(c for c in build.discover_cases() if c["slug"] == "bybit-tracker")
    build.build_case(case)

    out = build.DIST / "bybit-tracker" / "index.html"
    assert out.exists()
    html = out.read_text(encoding="utf-8")

    assert 'const API = "/api/bybit-tracker"' in html
    assert "Bybit Tracker" in html
    assert '"BTCUSDT"' in html

    # Perp-specific UI hooks: funding rate, mark, OI prominently shown.
    assert 'id="s-funding"' in html
    assert 'id="s-mark"' in html
    assert 'id="s-oi"' in html
    assert "USDT-Perp" in html  # the perp pill in the header

    # Standard chart + book + trades + markets skeleton.
    assert 'id="chart"' in html
    assert 'id="symbol"' in html
    assert 'id="asks"' in html and 'id="bids"' in html
    assert 'id="trades"' in html
    assert 'id="pairs-tbody"' in html
    assert "CandlestickSeries" in html
    assert "HistogramSeries" in html

    # Bybit yellow accent.
    assert "#ffce3a" in html
