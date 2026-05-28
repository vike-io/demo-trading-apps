"""Local dev server: serves dist/index.html and proxies /api/* to CoinGecko.

The browser never sees the CoinGecko API key. All /api/* requests are
forwarded to https://api.coingecko.com/api/v3/* with the
x-cg-demo-api-key header attached on the server side.

Usage:
    python build.py    # generate dist/index.html
    python serve.py    # browse http://localhost:8000
"""

from __future__ import annotations

import sys
import urllib.error
import urllib.request
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import quote

from build import DIST_DIR, load_env


PORT = 8000
COINGECKO = "https://api.coingecko.com/api/v3"
ENV = load_env()
API_KEY = ENV.get("COINGECKO_API_KEY", "")


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, directory=str(DIST_DIR), **kwargs)

    def do_GET(self) -> None:  # noqa: N802
        if self.path.startswith("/api/"):
            self.proxy_to_coingecko()
        else:
            super().do_GET()

    def proxy_to_coingecko(self) -> None:
        # /api/coins/markets?... -> https://api.coingecko.com/api/v3/coins/markets?...
        upstream_path = self.path[len("/api"):]
        # Preserve query string as-is; only quote the path segment.
        if "?" in upstream_path:
            path, _, query = upstream_path.partition("?")
            upstream = f"{COINGECKO}{quote(path, safe='/')}?{query}"
        else:
            upstream = f"{COINGECKO}{quote(upstream_path, safe='/')}"

        req = urllib.request.Request(upstream)
        if API_KEY:
            req.add_header("x-cg-demo-api-key", API_KEY)
        req.add_header("accept", "application/json")

        try:
            with urllib.request.urlopen(req, timeout=15) as upstream_res:
                body = upstream_res.read()
                self.send_response(upstream_res.status)
                self.send_header("Content-Type", upstream_res.headers.get("Content-Type", "application/json"))
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
        except urllib.error.HTTPError as e:
            body = e.read() if e.fp else b""
            self.send_response(e.code)
            self.send_header("Content-Type", e.headers.get("Content-Type", "application/json") if e.headers else "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except urllib.error.URLError as e:
            msg = f'{{"error": "upstream unreachable: {e.reason}"}}'.encode("utf-8")
            self.send_response(502)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(msg)))
            self.end_headers()
            self.wfile.write(msg)

    def log_message(self, fmt: str, *args) -> None:
        # Quieter default log: one line per request, no timestamps.
        sys.stderr.write(f"[serve] {self.address_string()} {fmt % args}\n")


def main() -> None:
    if not (DIST_DIR / "index.html").exists():
        sys.stderr.write("dist/index.html not found. Run: python build.py\n")
        sys.exit(1)
    key_status = "with demo API key" if API_KEY else "no API key (public rate limit)"
    print(f"Serving on http://localhost:{PORT}  ({key_status})")
    print(f"Static root: {DIST_DIR}")
    print("Press Ctrl+C to stop.")
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()


if __name__ == "__main__":
    main()
