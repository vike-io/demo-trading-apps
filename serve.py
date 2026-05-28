"""Umbrella local dev server.

Serves `dist/` and forwards `/api/<slug>/<rest>` to the upstream declared in
`dist/manifest.json` for that slug, attaching any key header configured for
the case from the root `.env`.

    python build.py    # regenerate dist/
    python serve.py    # http://localhost:8000

Stdlib only.
"""

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import quote


ROOT = Path(__file__).resolve().parent
DIST = ROOT / ".dist"
ENV_FILE = ROOT / ".env"
PORT = 8000


def load_env(path: Path = ENV_FILE) -> dict[str, str]:
    if not path.exists():
        return {}
    out: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        out[k.strip()] = v.strip().strip('"').strip("'")
    return out


def load_routes() -> dict[str, dict]:
    manifest_path = DIST / "manifest.json"
    if not manifest_path.exists():
        sys.stderr.write("dist/manifest.json not found. Run: python build.py\n")
        sys.exit(1)
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    return {r["slug"]: r for r in data.get("routes", [])}


ENV = load_env()
ROUTES = load_routes()


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, directory=str(DIST), **kwargs)

    def do_GET(self) -> None:  # noqa: N802
        # /api/<slug>/<rest>?query
        if self.path.startswith("/api/"):
            self.proxy()
            return
        super().do_GET()

    def proxy(self) -> None:
        # Strip leading "/api/" then peel slug.
        rest = self.path[len("/api/"):]
        slug, sep, tail = rest.partition("/")
        if not sep:
            tail = ""
        route = ROUTES.get(slug)
        if not route or not route.get("upstream_base"):
            self._json(404, {"error": f"unknown case: {slug!r}"})
            return

        # Split tail into path and query.
        if "?" in tail:
            path, _, query = tail.partition("?")
            upstream = f"{route['upstream_base']}/{quote(path, safe='/')}?{query}"
        else:
            upstream = f"{route['upstream_base']}/{quote(tail, safe='/')}"

        req = urllib.request.Request(upstream)
        req.add_header("accept", "application/json")
        key_env = route.get("api_key_env")
        key_hdr = route.get("api_key_header")
        if key_env and key_hdr and ENV.get(key_env):
            req.add_header(key_hdr, ENV[key_env])

        try:
            with urllib.request.urlopen(req, timeout=15) as res:
                body = res.read()
                self.send_response(res.status)
                self.send_header(
                    "Content-Type",
                    res.headers.get("Content-Type", "application/json"),
                )
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
        except urllib.error.HTTPError as e:
            body = e.read() if e.fp else b""
            self.send_response(e.code)
            self.send_header(
                "Content-Type",
                (e.headers.get("Content-Type", "application/json") if e.headers else "application/json"),
            )
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except urllib.error.URLError as e:
            self._json(502, {"error": "upstream unreachable", "detail": str(e.reason)})

    def _json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt: str, *args) -> None:
        sys.stderr.write(f"[serve] {self.address_string()} {fmt % args}\n")


def main() -> None:
    if not (DIST / "index.html").exists():
        sys.stderr.write("dist/index.html not found. Run: python build.py\n")
        sys.exit(1)
    print(f"Serving demo-trading-apps on http://localhost:{PORT}")
    print(f"  routes: {', '.join(ROUTES) or '(none)'}")
    keys_have = [r["api_key_env"] for r in ROUTES.values() if r.get("api_key_env") and ENV.get(r["api_key_env"])]
    if keys_have:
        print(f"  keys loaded: {', '.join(keys_have)}")
    print("Ctrl+C to stop.")
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()


if __name__ == "__main__":
    main()
