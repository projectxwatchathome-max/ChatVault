# ChatVault — ChatGPT Shared Conversation Downloader

A lightweight browser app for retrieving **public ChatGPT shared links** and copying/exporting the retrieved conversation as TXT, HTML, or PDF (via the browser print dialog).

## Files
- `index.html` — static frontend; deploy with GitHub Pages.
- `worker.js` — Cloudflare Worker retrieval endpoint. It fetches only public ChatGPT share URLs and does not store conversations.

## Deployment

### 1. Publish the frontend
In GitHub: **Settings → Pages → Build and deployment → Deploy from a branch**. Select `main` and `/ (root)`, then Save. The website URL will be:
`https://projectxwatchathome-max.github.io/ChatVault/`

### 2. Deploy the retrieval Worker
In Cloudflare Dashboard, open **Workers & Pages → Create → Worker**. Name it `chatvault-retrieval`, replace the starter code with the contents of `worker.js`, and Deploy.

The Worker URL will look like:
`https://chatvault-retrieval.<your-subdomain>.workers.dev`

### 3. Connect the frontend
Open the ChatVault website. Expand **Retrieval connection settings**, paste the Worker URL, and save. The URL is stored only in your browser's local storage.

## Important limitations
- Only public `https://chatgpt.com/share/...` and legacy `https://chat.openai.com/share/...` links are accepted.
- Private chats, deleted links, and links requiring sign-in cannot be retrieved.
- ChatGPT can change its shared-page HTML/data structure. If its format changes, the message extractor may need updating.
- The Worker is a simple fetch proxy, not an official OpenAI API. It forwards the public shared page without storing it.
- PDF export uses the browser's print dialog; choose **Save as PDF** on mobile/desktop.

## Privacy
The Worker does not persist fetched pages or conversation text. The browser keeps only the Worker URL setting. Do not use this for sensitive conversations unless you are comfortable retrieving a public shared link through your own Worker.
