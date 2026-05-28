"""CoinGecko_Tracker static-site builder."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
TEMPLATES_DIR = ROOT / "templates"
DIST_DIR = ROOT / "dist"
ENV_FILE = ROOT / ".env"


def render_template(path: Path, **vars: str) -> str:
    text = Path(path).read_text(encoding="utf-8")
    for k, v in vars.items():
        text = text.replace("{{" + k + "}}", v)
    return text


def load_env(path: Path = ENV_FILE) -> dict[str, str]:
    if not path.exists():
        return {}
    env: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def load_config() -> dict:
    return {
        "brand_name": "CoinGecko Tracker",
        "default_currency": "usd",
        "top_n": 100,
        "currency_list": ["usd", "eur", "btc"],
    }


def main() -> None:
    cfg = load_config()
    DIST_DIR.mkdir(exist_ok=True)

    pages = [
        ("index.html", {
            "top_n": str(cfg["top_n"]),
        }),
        ("coin.html", {}),
    ]
    common = {
        "brand_name": cfg["brand_name"],
        "default_currency": cfg["default_currency"],
        "currency_list_json": json.dumps(cfg["currency_list"]),
    }
    for name, extra in pages:
        html = render_template(TEMPLATES_DIR / name, **common, **extra)
        (DIST_DIR / name).write_text(html, encoding="utf-8")
        print(f"Wrote {DIST_DIR / name}")


if __name__ == "__main__":
    main()
