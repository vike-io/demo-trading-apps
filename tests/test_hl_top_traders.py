"""Verify the hl-top-traders case wires up correctly."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import build  # noqa: E402


def test_discover_includes_hl_top_traders():
    slugs = [c["slug"] for c in build.discover_cases()]
    assert "hl-top-traders" in slugs


def test_build_produces_hl_top_traders_index():
    build.DIST.mkdir(exist_ok=True)
    case = next(c for c in build.discover_cases() if c["slug"] == "hl-top-traders")
    build.build_case(case)

    out = build.DIST / "hl-top-traders" / "index.html"
    assert out.exists()
    html = out.read_text(encoding="utf-8")

    assert "Hyperliquid Top Traders" in html
    # JSON-RPC envelope hitting this case's own Vike route.
    assert "/api/hl-top-traders/vike/mcp" in html
    assert 'jsonrpc: "2.0"' in html
    assert '"hl_perp_top_traders"' in html
    # Filter controls.
    assert 'id="window"' in html and 'id="sort"' in html
    assert 'id="min-trades"' in html and 'id="min-win"' in html
    # Render hooks.
    assert 'id="rows"' in html and "renderRows" in html


def test_routing_manifest_has_vike_upstream_for_hl():
    cases = build.discover_cases()
    build.write_routing_manifest(cases)
    routes = json.loads((build.DIST / "manifest.json").read_text())["routes"]
    hl = next(r for r in routes if r["slug"] == "hl-top-traders")
    assert hl["upstreams"]["vike"]["base"] == "https://vike.io"
    assert hl["api_key_env"] == "VIKE_API_KEY"
    assert hl["api_key_header"] == "X-API-KEY"
