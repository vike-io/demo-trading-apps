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


def test_build_produces_side_by_side_implementations():
    build.DIST.mkdir(exist_ok=True)
    case = next(c for c in build.discover_cases() if c["slug"] == "perp-funding-spread")
    build.build_case(case)

    out = build.DIST / "perp-funding-spread" / "index.html"
    assert out.exists()
    html = out.read_text(encoding="utf-8")

    # Brand substituted.
    assert "Perp Funding Spread" in html

    # DIY column reuses the existing exchange proxies — relative URLs, no new key.
    assert "/api/binance-tracker/perp/premiumIndex" in html
    assert "/api/bybit-tracker/market/tickers?category=linear" in html

    # Vike column hits this case's own /vike/mcp route — Worker adds the key.
    assert "/api/perp-funding-spread/vike/mcp" in html
    # JS object literal — key is unquoted, value is the string "2.0".
    assert 'jsonrpc: "2.0"' in html
    assert 'tools/call' in html
    assert '"perp_funding"' in html

    # Both tbody hooks present (DIY + Vike).
    assert 'id="rows-diy"' in html and 'id="rows-vike"' in html
    assert "renderDiy" in html and "renderVike" in html
    assert "Math.abs(b.spread) - Math.abs(a.spread)" in html


def test_routing_manifest_has_vike_upstream_with_key_header():
    cases = build.discover_cases()
    build.write_routing_manifest(cases)
    routes = json.loads((build.DIST / "manifest.json").read_text())["routes"]
    spread = next(r for r in routes if r["slug"] == "perp-funding-spread")

    assert "upstreams" in spread
    assert spread["upstreams"]["vike"]["base"] == "https://vike.io"
    assert spread["api_key_env"] == "VIKE_API_KEY"
    assert spread["api_key_header"] == "X-API-KEY"
