// Umbrella Cloudflare Worker for demo-trading-apps.
//
// Reads the routing table from dist/manifest.json (bundled into the ASSETS
// binding), proxies /api/<slug>/<rest> to that slug's upstream_base with the
// configured key header pulled from env.<api_key_env>, and falls through to
// env.ASSETS.fetch for static files.
//
// Local dev:    wrangler dev
// Deploy:       wrangler deploy
// Set secret:   wrangler secret put COINGECKO_API_KEY  (and so on per case)

let routes = null;

async function loadRoutes(env) {
  if (routes) return routes;
  const res = await env.ASSETS.fetch(new Request("https://internal/manifest.json"));
  if (!res.ok) throw new Error("dist/manifest.json missing in ASSETS bundle");
  const data = await res.json();
  routes = Object.fromEntries((data.routes || []).map(r => [r.slug, r]));
  return routes;
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    if (url.pathname.startsWith("/api/")) {
      return proxy(url, env);
    }

    return env.ASSETS.fetch(request);
  }
};

async function proxy(url, env) {
  const after = url.pathname.slice("/api/".length);
  const slash = after.indexOf("/");
  const slug = slash === -1 ? after : after.slice(0, slash);
  const rest = slash === -1 ? "" : after.slice(slash + 1);

  let table;
  try {
    table = await loadRoutes(env);
  } catch (e) {
    return jsonError(500, "routing manifest unavailable", String(e));
  }
  const route = table[slug];
  if (!route) return jsonError(404, `unknown case: ${slug}`);

  // Resolve the upstream base. Cases can declare either:
  //   route.upstream_base (single host) → use rest directly
  //   route.upstreams (per-mode hosts)   → first segment of rest is the mode
  let base;
  let upstreamPath;
  if (route.upstreams) {
    const restSlash = rest.indexOf("/");
    const mode = restSlash === -1 ? rest : rest.slice(0, restSlash);
    const tail = restSlash === -1 ? "" : rest.slice(restSlash + 1);
    const modeCfg = route.upstreams[mode];
    if (!modeCfg) return jsonError(404, `unknown mode for ${slug}: ${mode || "(none)"}`);
    base = modeCfg.base;
    upstreamPath = tail;
  } else if (route.upstream_base) {
    base = route.upstream_base;
    upstreamPath = rest;
  } else {
    return jsonError(500, `case ${slug} has no upstream configured`);
  }

  const upstream = `${base}/${upstreamPath}${url.search}`;
  const headers = { accept: "application/json" };
  if (route.api_key_env && route.api_key_header && env[route.api_key_env]) {
    headers[route.api_key_header] = env[route.api_key_env];
  }

  try {
    const upRes = await fetch(upstream, { headers, cf: { cacheTtl: 30 } });
    return new Response(upRes.body, {
      status: upRes.status,
      headers: {
        "content-type": upRes.headers.get("content-type") ?? "application/json",
        "cache-control": "public, max-age=30"
      }
    });
  } catch (err) {
    return jsonError(502, "upstream unreachable", String(err));
  }
}

function jsonError(status, error, detail) {
  return new Response(JSON.stringify({ error, detail }), {
    status,
    headers: { "content-type": "application/json" }
  });
}
