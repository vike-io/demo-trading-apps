"""Verify the umbrella build produces a working coingecko-tracker case."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import build  # noqa: E402


def test_render_template_substitutes_placeholders(tmp_path):
    tpl = tmp_path / "tpl.html"
    tpl.write_text("Hello {{name}}, welcome to {{place}}.", encoding="utf-8")
    assert build.render_template(tpl, name="Alex", place="vike-io") == "Hello Alex, welcome to vike-io."


def test_discover_cases_finds_coingecko_tracker():
    slugs = [c["slug"] for c in build.discover_cases()]
    assert "coingecko-tracker" in slugs


def test_build_produces_index_and_coin_for_coingecko_tracker():
    build.DIST.mkdir(exist_ok=True)
    cgt = next(c for c in build.discover_cases() if c["slug"] == "coingecko-tracker")
    build.build_case(cgt)

    out = build.DIST / "coingecko-tracker"
    assert (out / "index.html").exists()
    assert (out / "coin.html").exists()

    index = (out / "index.html").read_text(encoding="utf-8")
    coin = (out / "coin.html").read_text(encoding="utf-8")

    # API prefix substituted with the slug.
    assert 'const API = "/api/coingecko-tracker"' in index
    assert 'const API = "/api/coingecko-tracker"' in coin

    # Brand + currency list substituted.
    assert "CoinGecko Tracker" in index
    assert '"usd"' in index and '"eur"' in index and '"btc"' in index

    # Home page expectations carried over from prior tests.
    assert '<table' in index
    assert 'id="rows"' in index
    assert "./coin.html?id=" in index
    assert "#0d1421" in index and "#16c784" in index and "#ea3943" in index

    # Detail page expectations.
    assert 'id="chart"' in coin
    assert 'id="timeframes"' in coin
    assert 'id="s-mcap"' in coin
    assert 'id="s-ath"' in coin
    assert "lightweight-charts" in coin
    assert "BaselineSeries" in coin


def test_landing_and_manifest_get_written():
    cases = build.discover_cases()
    build.build_landing(cases)
    build.write_routing_manifest(cases)

    assert (build.DIST / "index.html").exists()
    landing = (build.DIST / "index.html").read_text(encoding="utf-8")
    assert "demo-trading-apps" in landing
    assert "coingecko-tracker" in landing  # at least one card

    manifest = json.loads((build.DIST / "manifest.json").read_text(encoding="utf-8"))
    slugs = [r["slug"] for r in manifest["routes"]]
    assert "coingecko-tracker" in slugs
    cgt = next(r for r in manifest["routes"] if r["slug"] == "coingecko-tracker")
    assert cgt["upstream_base"] == "https://api.coingecko.com/api/v3"
    assert cgt["api_key_env"] == "COINGECKO_API_KEY"
    assert cgt["api_key_header"] == "x-cg-demo-api-key"
