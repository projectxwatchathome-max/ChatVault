# ChatVault — ChatGPT Shared Conversation Downloader

ChatVault accepts public ChatGPT shared links and lets the user copy or export the retrieved conversation as TXT, HTML, or PDF (through the browser print dialog).

## Deployment
The production Cloudflare Worker serves both the static app and the retrieval endpoint from one origin:
- `/` serves the ChatVault interface.
- `/fetch?url=<encoded-public-chatgpt-share-url>` retrieves the public shared page for browser-side extraction.

The source files are `index.html` and `worker.js`. The deployed Worker bundle embeds the current `index.html` so there is no separate hosting or CORS configuration step.

## Supported links and limits
- Public `https://chatgpt.com/share/...` and legacy `https://chat.openai.com/share/...` only.
- Private chats, deleted links, and links requiring sign-in cannot be retrieved.
- ChatGPT may change its shared-page HTML/data structure; the extractor may need maintenance if that happens.
- PDF export opens the browser print dialog; choose **Save as PDF**.
- The Worker does not persist conversation content. It forwards the public shared page to the user's browser.

## Privacy
No ChatVault account, database, or conversation archive is used. The Worker fetches a public shared URL on request and returns its page to the browser without storing it.
