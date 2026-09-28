# It's running — open the preview

**http://localhost:8100**

Build on disk: **BN97rGbS** · the sidebar footer shows this same id, so if it says
something else, you are looking at a cached tab (Ctrl+Shift+R).

## What to click

| Screen | Try this |
|---|---|
| 🏠 **Dashboard** | the 8 tiles, the stat rows, "new from the school's dictionaries" |
| 🔤 **Translate** | type `किताब बंद करो।` → a sentence. Type `आज मौसम बहुत अच्छा है।` → the 🧩 word card |
| ⌨️ **Text → Text** | typing-only, same two inputs, copy button |
| 📄 **PDF translation** | drop the SIH PDF in `uploads/` → page chips, method badges, print, text download |
| 🃏 **Flashcards** | 12 cards with 🔊 |
| 📝 **Worksheets** | pick a theme → printable bilingual sheet |
| 📖 **Dictionary** · 🗂️ **Vocabulary** | 469 entries / 220 words with audio |
| 🌐 **Language** | हिंदी switches the whole UI (nav stays English) |

## Verified again just now, on the live server

- 12 screens reachable, SPA shell served for `/`, `/translate`, `/text`, `/pdf`, `/flashcards`, `/worksheets`, `/dictionary`
- 17 real API routes answering, e.g. `/api/dictionary` 469 entries, `/api/vocab` 220, `/api/lessons` 51.7 kB, `/api/pack/summary` 5.0 kB
- translation, 3 ms each:

```
किताब बंद करो।            → ᱯᱚᱛᱚᱵ ᱵᱚᱸᱫᱚᱭ ᱢᱮ!        phrase / high
खोपड़ी                    → ᱠᱷᱟᱯᱨᱤ              dictionary / high
25                        → ᱵᱟᱨ ᱜᱮᱞ ᱢᱚᱬᱮ        number / high
आज मौसम बहुत अच्छा है।    → ᱛᱮᱦᱮᱧ ᱱᱟᱯᱟᱭ          word-combo / low  2/5 words
सरकारी स्कूल में नया शिक्षक आया है। → ᱥᱠᱩᱞ ᱱᱟᱣᱟ ᱢᱟᱪᱮᱫ ᱦᱮᱡ  word-combo / low  4/7 words
```

- TTS returns real audio (11,328 bytes of MP3 for `ᱛᱮᱦᱮᱧ ᱱᱟᱯᱟᱭ`)
- printable worksheet: POST `/api/worksheet` → 5,469-byte bilingual sheet
- suites: **Hindi 178 | PASS 154 | review 24 | FAIL 0** · **Odia 31 | PASS 31 | FAIL 0**

## Two notes from this restart

1. `web/dist/` and the Python packages are not kept between sessions (build/cache folders are
   excluded), so the server was down and the bundle was gone. I reinstalled
   `fastapi uvicorn[standard] gtts python-multipart pypdf`, rebuilt the front end, and
   restarted. Nothing about the app itself changed — the rebuild produced the **same**
   `index-BN97rGbS.js`, byte for byte.
2. A small hardening while I was in there: an unknown `/api/*` path now answers with a JSON
   **404 + the live route list** instead of the HTML shell. Earlier today a wrong route name
   came back as a 200 HTML page and looked fine — that is exactly how a stale tab looks
   healthy, so it can't happen silently again.
