"""Umbrella build orchestrator for demo-trading-apps.

For each `<slug>/manifest.json` it finds at the repo root, this script reads
the manifest, renders every template under that case's `templates/` directory
with the manifest's `config` substituted, and writes the result to
`dist/<slug>/<page>.html`.

It also renders the landing page (`landing/templates/index.html`) into
`dist/index.html`, and writes a routing manifest at `dist/manifest.json` that
the local server and the Cloudflare Worker both read at startup to know
which slugs proxy where.

Standard library only.
"""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DIST = ROOT / "dist"
LANDING = ROOT / "landing"


def render_template(path: Path, **vars: str) -> str:
    text = path.read_text(encoding="utf-8")
    for k, v in vars.items():
        text = text.replace("{{" + k + "}}", v)
    return text


def discover_cases() -> list[dict]:
    """Find every immediate-child folder that has a manifest.json."""
    cases = []
    for manifest_path in sorted(ROOT.glob("*/manifest.json")):
        case_dir = manifest_path.parent
        if case_dir.name in {"landing", "dist", "tests"}:
            continue
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["_dir"] = case_dir
        cases.append(manifest)
    return cases


def stringify(value) -> str:
    """Substituting into {{placeholder}} requires strings. JSON-encode
    arrays/objects so they paste into JS as literals; otherwise str(value)."""
    if isinstance(value, (list, dict)):
        return json.dumps(value)
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def build_case(manifest: dict) -> None:
    slug = manifest["slug"]
    case_dir: Path = manifest["_dir"]
    templates_dir = case_dir / "templates"
    out_dir = DIST / slug
    out_dir.mkdir(parents=True, exist_ok=True)

    vars: dict[str, str] = {k: stringify(v) for k, v in manifest.get("config", {}).items()}
    vars["slug"] = slug
    vars["api_base"] = f"/api/{slug}"
    # JSON-encoded form for JS:
    for k, v in list(manifest.get("config", {}).items()):
        if isinstance(v, list):
            vars[f"{k}_json"] = json.dumps(v)

    pages = manifest.get("pages", ["index"])
    for page in pages:
        tpl = templates_dir / f"{page}.html"
        if not tpl.exists():
            raise FileNotFoundError(f"Missing template: {tpl}")
        html = render_template(tpl, **vars)
        (out_dir / f"{page}.html").write_text(html, encoding="utf-8")
        print(f"  wrote dist/{slug}/{page}.html")


def build_landing(cases: list[dict]) -> None:
    tpl = LANDING / "templates" / "index.html"
    if not tpl.exists():
        print("  (no landing template; skipping)")
        return
    def _sort_key(c: dict):
        tag = (c.get("tag") or "").lower()
        is_planned = "coming" in tag or "planned" in tag
        return (is_planned, c["slug"])

    cards = [
        {
            "slug": c["slug"],
            "name": c.get("name", c["slug"]),
            "tagline": c.get("tagline", ""),
            "tag": c.get("tag", ""),
        }
        for c in sorted(cases, key=_sort_key)
    ]
    html = render_template(tpl, cards_json=json.dumps(cards))
    DIST.mkdir(exist_ok=True)
    (DIST / "index.html").write_text(html, encoding="utf-8")
    print("  wrote dist/index.html")


def write_routing_manifest(cases: list[dict]) -> None:
    routes = []
    for c in cases:
        route: dict = {
            "slug": c["slug"],
            "name": c.get("name", c["slug"]),
            "upstream_base": c.get("upstream_base"),
        }
        if c.get("api_key_env") and c.get("api_key_header"):
            route["api_key_env"] = c["api_key_env"]
            route["api_key_header"] = c["api_key_header"]
        routes.append(route)
    (DIST / "manifest.json").write_text(
        json.dumps({"routes": routes}, indent=2), encoding="utf-8"
    )
    print("  wrote dist/manifest.json")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--case", help="Build only this slug (else build all)")
    ap.add_argument("--clean", action="store_true", help="Wipe dist/ first")
    args = ap.parse_args()

    if args.clean and DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir(exist_ok=True)

    cases = discover_cases()
    if args.case:
        cases = [c for c in cases if c["slug"] == args.case]
        if not cases:
            raise SystemExit(f"No case named {args.case!r}")

    for c in cases:
        print(f"Building {c['slug']}…")
        build_case(c)

    all_cases = discover_cases()  # for the landing + manifest, always all
    print("Building landing…")
    build_landing(all_cases)
    write_routing_manifest(all_cases)
    print(f"\nDone. Built {len(cases)} case(s).")


if __name__ == "__main__":
    main()
