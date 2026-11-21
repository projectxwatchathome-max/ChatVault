# ChatVault — ChatGPT Shared Conversation Extractor

ChatVault extracts text from public ChatGPT shared-conversation links.

## Current architecture
- `index.html`: responsive one-link frontend with Copy All and TXT, Markdown, JSON, HTML, and PDF export.
- `server.py`: Python/Flask API; fetches the public share page and parses its embedded React Flight conversation payload, with legacy Next.js fallback.
- `render.yaml`: one-click Render Blueprint for a free Python web service.
- No database or conversation archive is used.

## Deploy on Render (free tier)
1. Open https://render.com/deploy?repo=https://github.com/projectxwatchathome-max/ChatVault
2. Sign in to Render and authorize access to the ChatVault GitHub repository.
3. Review the Blueprint. Confirm the service plan is **Free**.
4. Tap **Apply** to create and deploy `chatvault-extractor`.
5. After deployment, open the generated `https://chatvault-extractor.onrender.com` service URL.

The service serves the frontend and API from the same origin, so the existing frontend's `/api/extract` request works without a separate API URL.

## Free-tier note
Render Free web services spin down after 15 minutes without inbound traffic. The first request after sleep may take about a minute to wake the service. See https://render.com/docs/free.

## Extraction behavior and limits
- Accepts only HTTPS public share links on `chatgpt.com` or `chat.openai.com` at `/share/<id>`.
- Extracts user/assistant messages from the embedded conversation payload in sequence order.
- Includes text and visible attachment placeholders; does not download binary image/file attachments.
- No login, user account, persistent storage, or conversation history database.
- ChatGPT may change its shared-page format or block a hosting provider's server IP. A successful Render deployment does not guarantee ChatGPT will allow extraction; test with a real public share link before treating the service as operational.
