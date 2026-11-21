# ChatVault — ChatGPT Shared Conversation Extractor

ChatVault is a one-link ChatGPT shared-conversation extractor.

## User workflow
1. Paste a public `https://chatgpt.com/share/...` link.
2. Tap **Extract**.
3. Copy the full conversation or export it as TXT, Markdown, JSON, HTML, or PDF.

No user account, ChatGPT sign-in, browser extension, or bookmark setup is required.

## Architecture
- `index.html` — responsive single-page frontend and browser-side export formatters.
- `worker.js` — Cloudflare Worker. Serves the frontend at `/` and handles `POST /api/extract`.
- Cloudflare Browser Run binding `BROWSER` — opens and renders the public shared page using Chromium, then scrapes message elements in page order.

The extraction service accepts only HTTPS URLs on `chatgpt.com` or `chat.openai.com` using the `/share/` path. It does not accept arbitrary URLs.

## Privacy
ChatVault does not create a conversation archive or database. The Worker processes the public share URL for the extraction request and returns the extracted messages to the visitor's browser. Do not paste confidential conversations into public share links.

## Current limitations
- Public shared links only; private chats, deleted shares, and links requiring sign-in cannot be extracted.
- The extractor currently captures text content and role labels; image and file attachments are not included.
- The extractor relies on ChatGPT's rendered page structure. If that structure changes, the selector/extraction code may need maintenance.
- Browser Run has account-level usage limits. Monitor usage in the Cloudflare dashboard.

## Deployment
The production Worker is named `chatvault-retrieval` and uses a Browser Run binding named `BROWSER`. The frontend is served from the same Worker origin, so no manual CORS configuration or separate GitHub Pages activation is needed for the live app.
