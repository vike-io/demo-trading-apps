"""Verify the umbrella build picks up the perp-funding-spread case."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import build  # noqa: E402


def test_discover_includes_perp_funding_spread():
    slugs = [c["slug"] for c in build.discover_cases()]
    assert "perp-funding-spread" in slugs


def test_build_produces_index():
    build.DIST.mkdir(exist_ok=True)
    case = next(c for c in build.discover_cases() if c["slug"] == "perp-funding-spread")
    build.build_case(case)

    out = build.DIST / "perp-funding-spread" / "index.html"
    assert out.exists()
    html = out.read_text(encoding="utf-8")

    # Brand + tagline substituted.
    assert "Perp Funding Spread" in html

    # Reuses the existing exchange proxies — relative URLs, no new upstream.
    assert "/api/binance-tracker/perp/premiumIndex" in html
    assert "/api/bybit-tracker/market/tickers?category=linear" in html

    # The spread + annualization math lives in the rendered file.
    assert "fmtSpread" in html and "fmtAnnualized" in html
    assert "Math.abs(b.spread) - Math.abs(a.spread)" in html


def test_routing_manifest_has_no_upstream_for_this_case():
    """The case doesn't declare its own upstream — it consumes existing
    exchange proxies. The routing manifest should reflect that."""
    cases = build.discover_cases()
    build.write_routing_manifest(cases)
    routes = json.loads((build.DIST / "manifest.json").read_text())["routes"]
    spread = next(r for r in routes if r["slug"] == "perp-funding-spread")
    assert "upstream_base" not in spread
    assert "upstreams" not in spread
