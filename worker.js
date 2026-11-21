/**
 * ChatVault shared-link retrieval Worker
 * Deploy as a Cloudflare Worker. No data is stored.
 */
const ALLOWED = new Set(["chatgpt.com", "chat.openai.com"]);
function cors() {
  return {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
    "Cache-Control": "no-store"
  };
}
export default {
  async fetch(request) {
    const url = new URL(request.url);
    if (request.method === "OPTIONS") return new Response(null, { headers: cors() });
    if (url.pathname === "/") return new Response("ChatVault retrieval Worker is running.", { headers: { ...cors(), "Content-Type": "text/plain; charset=utf-8" } });
    if (request.method !== "GET" || url.pathname !== "/fetch") {
      return Response.json({ error: "Use GET /fetch?url=https://chatgpt.com/share/..." }, { status: 404, headers: cors() });
    }
    const target = url.searchParams.get("url");
    if (!target) return Response.json({ error: "Missing shared conversation URL." }, { status: 400, headers: cors() });
    let parsed;
    try { parsed = new URL(target); } catch {
      return Response.json({ error: "Invalid URL." }, { status: 400, headers: cors() });
    }
    if (!ALLOWED.has(parsed.hostname) || !/^\/share\/[A-Za-z0-9-]+/.test(parsed.pathname) || parsed.protocol !== "https:") {
      return Response.json({ error: "Only public ChatGPT shared links are allowed." }, { status: 400, headers: cors() });
    }
    try {
      const upstream = await fetch(parsed.toString(), {
        method: "GET",
        redirect: "follow",
        headers: {
          "Accept": "text/html,application/xhtml+xml",
          "User-Agent": "Mozilla/5.0 (compatible; ChatVault/1.0; +https://github.com/projectxwatchathome-max/ChatVault)"
        }
      });
      if (!upstream.ok) {
        return Response.json({ error: "ChatGPT returned HTTP " + upstream.status + ". The link may be unavailable or require access." }, { status: 502, headers: cors() });
      }
      const contentType = upstream.headers.get("content-type") || "";
      if (!contentType.includes("text/html")) {
        return Response.json({ error: "The shared link did not return an HTML page." }, { status: 502, headers: cors() });
      }
      const body = await upstream.text();
      if (body.length > 12_000_000) return Response.json({ error: "The shared page is too large to process." }, { status: 413, headers: cors() });
      return new Response(body, {
        status: 200,
        headers: { ...cors(), "Content-Type": "text/html; charset=utf-8" }
      });
    } catch (error) {
      return Response.json({ error: "Could not retrieve the ChatGPT shared page: " + (error?.message || "upstream error") }, { status: 502, headers: cors() });
    }
  }
};