// Cloudflare Worker: proxies /api/* to CoinGecko with the demo key
// from a secret, and falls through to the static assets binding
// (dist/) for everything else. The key never leaves the Worker.
//
// Local dev:   wrangler dev
// Deploy:      wrangler deploy
// Set secret:  wrangler secret put COINGECKO_API_KEY

const COINGECKO = "https://api.coingecko.com/api/v3";

export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    if (url.pathname.startsWith("/api/")) {
      return proxyToCoinGecko(url, env);
    }

    return env.ASSETS.fetch(request);
  }
};

async function proxyToCoinGecko(url, env) {
  const upstream = COINGECKO + url.pathname.slice("/api".length) + url.search;
  const headers = { accept: "application/json" };
  if (env.COINGECKO_API_KEY) {
    headers["x-cg-demo-api-key"] = env.COINGECKO_API_KEY;
  }
  try {
    const res = await fetch(upstream, { headers, cf: { cacheTtl: 30 } });
    return new Response(res.body, {
      status: res.status,
      headers: {
        "content-type": res.headers.get("content-type") ?? "application/json",
        "cache-control": "public, max-age=30"
      }
    });
  } catch (err) {
    return new Response(JSON.stringify({ error: "upstream unreachable", detail: String(err) }), {
      status: 502,
      headers: { "content-type": "application/json" }
    });
  }
}
