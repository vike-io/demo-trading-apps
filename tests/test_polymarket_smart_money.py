"""Verify the polymarket-smart-money case wires up correctly."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import build  # noqa: E402


def test_discover_includes_polymarket_smart_money():
    slugs = [c["slug"] for c in build.discover_cases()]
    assert "polymarket-smart-money" in slugs


def test_build_produces_polymarket_smart_money_index():
    build.DIST.mkdir(exist_ok=True)
    case = next(c for c in build.discover_cases() if c["slug"] == "polymarket-smart-money")
    build.build_case(case)

    out = build.DIST / "polymarket-smart-money" / "index.html"
    assert out.exists()
    html = out.read_text(encoding="utf-8")

    assert "Polymarket Smart Money" in html
    # Vike proxy route.
    assert "/api/polymarket-smart-money/vike/mcp" in html
    assert 'jsonrpc: "2.0"' in html
    assert '"polymarket_smart_money"' in html
    # Flows / Mispricings toggle.
    assert 'data-mode="flows"' in html and 'data-mode="mispricings"' in html
    assert "applyMode" in html
    # Hours + category inputs.
    assert 'id="hours"' in html
    assert 'id="category"' in html


def test_routing_manifest_has_vike_upstream_for_polymarket():
    cases = build.discover_cases()
    build.write_routing_manifest(cases)
    routes = json.loads((build.DIST / "manifest.json").read_text())["routes"]
    pm = next(r for r in routes if r["slug"] == "polymarket-smart-money")
    assert pm["upstreams"]["vike"]["base"] == "https://vike.io"
    assert pm["api_key_env"] == "VIKE_API_KEY"
    assert pm["api_key_header"] == "X-API-KEY"
