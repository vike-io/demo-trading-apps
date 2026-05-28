import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import build


def test_render_template_substitutes_placeholders(tmp_path):
    tpl = tmp_path / "tpl.html"
    tpl.write_text("Hello {{name}}, welcome to {{place}}.", encoding="utf-8")

    result = build.render_template(tpl, name="Alex", place="CMC")

    assert result == "Hello Alex, welcome to CMC."


def test_load_config_returns_expected_keys():
    cfg = build.load_config()
    assert cfg["brand_name"] == "CoinGecko Tracker"
    assert cfg["default_currency"] == "usd"
    assert cfg["top_n"] == 100
    assert cfg["currency_list"] == ["usd", "eur", "btc"]


def test_main_writes_dist_index_html():
    dist = build.ROOT / "dist" / "index.html"
    if dist.exists():
        dist.unlink()

    build.main()

    assert dist.exists()
    html = dist.read_text(encoding="utf-8")
    assert "CoinGecko Tracker" in html
    # Currency options must be embedded as a JSON array string in the template output:
    assert '"usd"' in html
    assert '"eur"' in html
    assert '"btc"' in html
    # Top-N value must be embedded:
    assert "100" in html


def test_built_html_contains_skeleton_markers():
    build.main()
    html = (build.ROOT / "dist" / "index.html").read_text(encoding="utf-8")
    assert '<table' in html
    assert 'id="rows"' in html
    assert 'id="search"' in html
    assert 'id="currency"' in html
    assert 'id="error"' in html
    # Row clicks navigate to coin.html rather than opening a modal
    assert "./coin.html?id=" in html


def test_built_html_has_dark_theme_palette():
    build.main()
    html = (build.ROOT / "dist" / "index.html").read_text(encoding="utf-8")
    assert "#0d1421" in html  # bg
    assert "#16c784" in html  # green
    assert "#ea3943" in html  # red
    assert "position: sticky" in html  # sticky header


def test_main_writes_coin_html():
    dist_coin = build.ROOT / "dist" / "coin.html"
    if dist_coin.exists():
        dist_coin.unlink()

    build.main()

    assert dist_coin.exists()
    html = dist_coin.read_text(encoding="utf-8")
    # Detail page must contain the chart container, timeframe buttons,
    # stats panel ids, and the Lightweight Charts CDN.
    assert 'id="chart"' in html
    assert 'id="timeframes"' in html
    assert 'id="s-mcap"' in html
    assert 'id="s-ath"' in html
    assert "lightweight-charts" in html
    assert "BaselineSeries" in html
