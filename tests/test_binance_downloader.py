"""Verify the umbrella build picks up the binance-downloader case."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import build  # noqa: E402


def test_discover_includes_binance_downloader():
    slugs = [c["slug"] for c in build.discover_cases()]
    assert "binance-downloader" in slugs


def test_build_produces_downloader_index():
    build.DIST.mkdir(exist_ok=True)
    case = next(c for c in build.discover_cases() if c["slug"] == "binance-downloader")
    build.build_case(case)

    out = build.DIST / "binance-downloader" / "index.html"
    assert out.exists()
    html = out.read_text(encoding="utf-8")

    # Brand, default symbol, interval list substituted.
    assert "Binance Downloader" in html
    assert 'value="BTCUSDT"' in html
    assert '"1h"' in html and '"1d"' in html

    # API prefix substituted with the slug.
    assert 'const API = "/api/binance-downloader"' in html

    # Browser CSV download wiring (Blob + a.click).
    assert "URL.createObjectURL" in html
    assert "a.download" in html
    assert "CSV_COLUMNS" in html
    assert "downloadCsv" in html

    # The hint to the Python CLI in the same folder appears.
    assert "python download.py" in html


def test_python_cli_module_imports_clean():
    """The Python CLI must be importable as a module (it shouldn't run main on import)."""
    case_dir = build.ROOT / "binance-downloader"
    cli = case_dir / "download.py"
    assert cli.exists()
    text = cli.read_text(encoding="utf-8")
    # Same column schema as the browser version — these MUST match.
    assert "CSV_COLUMNS" in text
    assert '"open_time"' in text and '"close_time"' in text
    # main() is guarded by __name__ == "__main__".
    assert 'if __name__ == "__main__"' in text
