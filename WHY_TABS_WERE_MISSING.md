# Found it: your browser was serving a cached old build

## What was actually wrong

The two screens **were** built and **were** being served by the server. Your browser was
showing an older copy of the app, and it was not your fault:

The app ships a **service worker** (`web/public/sw.js`) so it keeps working when a school
loses internet. That worker was **cache-first for the app shell** — once a browser had opened
the app, it served its own saved copy of `index.html` and the JS bundle for ever, without ever
asking the server. So no matter what I deployed, your browser kept opening the old build.

**The proof is in the server log.** Your browser asked for:

```
GET /api/odia/samples?limit=6      <-- an endpoint of the build BEFORE the Odia removal
GET /api/vocab?category=all&q=
GET /api/quiz?category=fruits&count=4
```

`/api/odia/samples` is only fetched by the old Translate page that still had the Odia input
switch. Your tab was running a build two releases old.

## What I changed so this cannot happen again

| Fix | Where |
|---|---|
| Service worker is now **network-first** for pages and API calls; cache-first only for content-hashed `/assets/*` and audio clips | `web/public/sw.js` (v3) |
| Cache name bumped `mtb-shell-v2` → **`mtb-shell-v3`**, so the old offline cache is deleted on activation | same file |
| New worker calls `skipWaiting()` + `clients.claim()`; the page reloads itself once when the new worker takes over | `web/public/sw.js`, `web/src/main.jsx` |
| Worker script registered with `updateViaCache: 'none'` and an update check on every load | `web/src/main.jsx` |
| **Self-repair in the page**: `index.html` compares its own build against `GET /api/version`; if they differ it clears caches, unregisters the worker and reloads once | `web/index.html` |
| **`GET /api/version`** returns the build the server is serving plus the 12 screen ids | `server/main.py` |
| **♻️ Refresh app** button on the Offline screen — drops all caches, unregisters the worker, reloads | `web/src/pages/Offline.jsx` |
| Sidebar footer now shows the **build id**, so a stale tab is obvious instead of a mystery | `web/src/App.jsx` |

## What to do (once)

Your tab still runs the old worker, so give it two refreshes:

1. **Ctrl + Shift + R** — the browser picks up the new `sw.js` and installs it
2. **Reload again** (F5) — now the new worker serves the current build

If it still looks old, the certain way is a **private/incognito window** (no worker, no cache),
or DevTools → Application → *Unregister* the service worker.

**How to confirm you are on the current build:** the sidebar footer now reads
`संस्करण/build: DgJOWbU9 · 34 वाक्य`. If it says `DgJOWbU9`, you are current.

## Where the two screens are

Left nav, top to bottom — 12 entries:

```
🏠 Dashboard
🎙️ Voice Translator
⌨️ पाठ → पाठ / Text → Text      <-- here
📄 पीडीएफ अनुवाद / PDF translation  <-- and here
📚 Lesson Board
🃏 Flashcards
🖨️ Worksheets
🔤 Vocabulary
📖 Dictionary
✅ Validation
📶 Offline & Sync
🌏 About & Impact
```

Both are also tiles on the Dashboard (8 tiles) and buttons in the Dashboard hero row:
`🎙️ Voice Translator · ⌨️ Text → Text · 📄 PDF translation`.

## Verified on the running server just now

```
GET /api/version  -> {"build":"DgJOWbU9","screens":12,
                      "screens_available":["dashboard","translate","text","pdf","lessons",
                      "flashcards","worksheets","vocab","dictionary","validate","offline","about"]}
GET /sw.js        -> cache-control: no-cache, no-store   (worker file always revalidated)
                     contains mtb-shell-v3, networkFirst
bundle check      -> nav_text ✓  nav_pdf ✓  ttTranslate ✓  pdfTranslate ✓
                     quickText ✓  quickPdf ✓  Odia chain removed ✓
suites            -> Hindi 169 · PASS 145 · review 24 · FAIL 0
                     Odia  31 · PASS 31 · FAIL 0
```

Server is running on port 8000, serving build **DgJOWbU9**, 12 screens.
