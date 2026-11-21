import json
import re
import os
from html.parser import HTMLParser
from urllib.parse import urlparse

import requests
from flask import Flask, jsonify, request, send_from_directory

app = Flask(__name__, static_folder=".", static_url_path="")
app.config["MAX_CONTENT_LENGTH"] = 8 * 1024

ALLOWED_HOSTS = {"chatgpt.com", "chat.openai.com"}
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://chatgpt.com/",
}

class ScriptCollector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.scripts = []
        self.active = False
        self.attrs = {}
        self.parts = []
    def handle_starttag(self, tag, attrs):
        if tag.lower() == "script":
            self.active = True
            self.attrs = dict(attrs)
            self.parts = []
    def handle_data(self, data):
        if self.active:
            self.parts.append(data)
    def handle_endtag(self, tag):
        if tag.lower() == "script" and self.active:
            self.scripts.append((self.attrs, "".join(self.parts)))
            self.active = False

def valid_share_url(value):
    try:
        parsed = urlparse(value)
        share_id = parsed.path.strip("/").split("/")
        return (parsed.scheme == "https" and parsed.hostname in ALLOWED_HOSTS
                and len(share_id) == 2 and share_id[0] == "share"
                and re.fullmatch(r"[A-Za-z0-9-]+", share_id[1]))
    except Exception:
        return False

def extract_flight(scripts):
    decoder = json.JSONDecoder()
    for _attrs, body in scripts:
        if "streamController.enqueue(" not in body:
            continue
        pos = 0
        while True:
            start = body.find("streamController.enqueue(", pos)
            if start < 0:
                break
            start += len("streamController.enqueue(")
            quote = body.find('"', start)
            close = body.find(");", start)
            if quote >= 0 and (close < 0 or quote < close):
                try:
                    chunk, end = decoder.raw_decode(body, quote)
                    pos = end
                except json.JSONDecodeError:
                    pos = start + 1
                    continue
            else:
                end = body.find(");", start)
                if end < 0:
                    break
                chunk = body[start:end].strip().strip("()")
                pos = end + 2
            if isinstance(chunk, str):
                try:
                    value = json.loads(chunk.strip())
                    if isinstance(value, list):
                        return value
                except json.JSONDecodeError:
                    pass
    return None

def decode_flight(loader):
    cache = {}
    def resolve(value, depth=0):
        if depth > 80:
            return value
        if isinstance(value, int) and not isinstance(value, bool):
            if value in cache:
                return cache[value]
            if 0 <= value < len(loader):
                cache[value] = None
                cache[value] = resolve(loader[value], depth + 1)
                return cache[value]
            return value
        if isinstance(value, list):
            return [resolve(x, depth + 1) for x in value]
        if isinstance(value, dict):
            out = {}
            for key, item in value.items():
                decoded_key = key
                if isinstance(key, str) and re.fullmatch(r"_\d+", key):
                    idx = int(key[1:])
                    if 0 <= idx < len(loader) and isinstance(loader[idx], str):
                        decoded_key = loader[idx]
                out[decoded_key] = resolve(item, depth + 1)
            return out
        return value
    result = {}
    it = iter(loader[1:])
    for key in it:
        try:
            value = next(it)
        except StopIteration:
            break
        if isinstance(key, str) and key not in result:
            result[key] = resolve(value)
    return result

def text_from_content(content):
    if not isinstance(content, dict):
        return ""
    parts = content.get("parts")
    output = []
    if isinstance(parts, list):
        for part in parts:
            if isinstance(part, str) and part.strip():
                output.append(part)
            elif isinstance(part, dict):
                txt = part.get("text") or part.get("content")
                if isinstance(txt, str) and txt.strip():
                    output.append(txt)
                elif part.get("content_type") in ("image", "image_asset_pointer"):
                    output.append("[Image attachment]")
                elif part.get("content_type") in ("file", "file_attachment"):
                    output.append("[File attachment]")
    for key in ("text", "transcript"):
        value = content.get(key)
        if isinstance(value, str) and value.strip() and not output:
            output.append(value)
    return "\n\n".join(output).strip()

def parse_conversation(html):
    collector = ScriptCollector()
    collector.feed(html)
    flight = extract_flight(collector.scripts)
    data = None
    title = "ChatGPT conversation"
    if flight:
        decoded = decode_flight(flight)
        loader_data = decoded.get("loaderData", {})
        route = loader_data.get("routes/share.$shareId.($action)", {}) if isinstance(loader_data, dict) else {}
        server_response = route.get("serverResponse", {}) if isinstance(route, dict) else {}
        data = server_response.get("data", {}) if isinstance(server_response, dict) else {}
        if not isinstance(data, dict) or not data:
            raise ValueError("The page loaded, but the shared conversation data was not present in its React payload.")
        title = data.get("title") or title
        mapping = data.get("mapping", {})
        sequence = data.get("linear_conversation", [])
        if not isinstance(sequence, list) or not sequence:
            current = data.get("current_node")
            chain, seen = [], set()
            while current and current not in seen and isinstance(mapping, dict):
                seen.add(current)
                node = mapping.get(current)
                if not isinstance(node, dict):
                    break
                chain.append({"id": current})
                current = node.get("parent")
            sequence = list(reversed(chain))
        messages = []
        for entry in sequence:
            node_id = entry.get("id") if isinstance(entry, dict) else None
            node = mapping.get(node_id) if isinstance(mapping, dict) else None
            msg = node.get("message") if isinstance(node, dict) else None
            if not isinstance(msg, dict):
                continue
            role = (msg.get("author") or {}).get("role")
            if role not in ("user", "assistant"):
                continue
            text = text_from_content(msg.get("content", {}))
            if text:
                messages.append({"role": role, "text": text})
        if messages:
            return {"title": str(title), "messages": messages}
    # Legacy Next.js share payload fallback.
    for attrs, body in collector.scripts:
        if attrs.get("id") == "__NEXT_DATA__":
            payload = json.loads(body)
            props = payload.get("props", {}).get("pageProps", {})
            data = props.get("serverResponse", {}).get("data", {})
            title = data.get("title") or title
            messages = []
            for node in data.get("linear_conversation", []):
                msg = node.get("message", {}) if isinstance(node, dict) else {}
                role = (msg.get("author") or {}).get("role")
                if role not in ("user", "assistant"):
                    continue
                text = text_from_content(msg.get("content", {}))
                if text:
                    messages.append({"role": role, "text": text})
            if messages:
                return {"title": str(title), "messages": messages}
    raise ValueError("The share page was received, but its conversation payload could not be decoded. ChatGPT may have changed its data format.")

@app.get("/")
def home():
    return send_from_directory(".", "index.html")

@app.get("/health")
def health():
    return jsonify({"ok": True, "service": "ChatVault extractor", "provider": "Render"})

@app.post("/api/extract")
def extract():
    body = request.get_json(silent=True) or {}
    share_url = body.get("url", "")
    if not isinstance(share_url, str) or not valid_share_url(share_url):
        return jsonify({"error": "Enter a valid public ChatGPT shared link."}), 400
    try:
        response = requests.get(share_url, headers=HEADERS, timeout=(15, 45), allow_redirects=True)
        if response.status_code == 403:
            return jsonify({"error": "ChatGPT refused this server request (HTTP 403). The link may still open in your phone browser; this hosting provider is also being blocked."}), 502
        if response.status_code == 404:
            return jsonify({"error": "ChatGPT says this shared conversation was not found (HTTP 404). Check that the share link is still active."}), 404
        response.raise_for_status()
        if len(response.content) > 20 * 1024 * 1024:
            return jsonify({"error": "The shared page response is unexpectedly large."}), 502
        result = parse_conversation(response.text)
        result["count"] = len(result["messages"])
        return jsonify(result)
    except requests.Timeout:
        return jsonify({"error": "ChatGPT took too long to respond. Please try again."}), 504
    except requests.RequestException as exc:
        return jsonify({"error": "Could not retrieve the shared page: " + str(exc)[:240]}), 502
    except (ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        return jsonify({"error": str(exc) or "The shared conversation could not be decoded."}), 422

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "10000")))
