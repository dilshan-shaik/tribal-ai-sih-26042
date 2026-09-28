# Fresh link — both features are live, Odia option removed

## 👉 Open the NEW preview (port 8100)

**http://localhost:8100** — or click the new LIVE PREVIEW panel labelled
**“PALASH MTB-MLE (Hindi → Santhali)”**.

### Why you need the new link, not the old one

Your browser was pinned to an old copy of the app by its **service worker**. That worker was
cache-first for the page itself, so it kept handing back the old `index.html` from cache — and
because my self-repair code lives *inside* `index.html`, it could never run. No amount of
reloading could fix it.

A **new port is a new origin**, so there is no cached worker and no cached page: port 8100 loads
the current build on the first try. The old server on port 8000 has been stopped.

---

## The two features — code and API, both verified on port 8100

### ⌨️ Text → Text  (3rd item in the left nav, and a Dashboard tile)
```
किताब बंद करो।   ->  ᱯᱚᱛᱚᱵ ᱵᱚᱸᱫᱚᱭ ᱢᱮ!              [phrase]
खोपड़ी           ->  ᱠᱷᱟᱯᱨᱤ                        [dictionary]
25               ->  ᱵᱟᱨ ᱜᱮᱞ ᱢᱚᱬᱮ                  [number]
यह एक पेड़ है।   ->  ᱱᱚᱶᱟ ᱫᱚ ᱢᱤᱫᱴᱟᱹᱝ ᱫᱟᱨᱮ ᱠᱟᱱᱟ।  [template]
```
Type Hindi → Santhali in Ol Chiki → 📋 copy. No microphone, no audio on that page.

### 📄 PDF translation  (4th item in the left nav, and a Dashboard tile)
```
upload                 -> 16 paragraphs read, 16 word-by-word
POST /api/pdf/report   -> HTTP 200, 19,287 bytes printable bilingual page
POST /api/pdf/text     -> HTTP 200, 6,274 bytes plain text
```
Drop a PDF → bilingual table → 🖨️ Print / Save as PDF, or ⬇️ download the text.

---

## Odia: gone from the app

Checked in the actual shipped bundle (`index-BZyrw4lW.js`):

| | |
|---|---|
| Odia input switch (`typeOdia`) | **gone** |
| Odia → Hindi chain card (`chainOdiaHindi`) | **gone** |
| Odia language chip (ଓଡ଼ିଆ) | **gone** |
| Odia samples call (`/api/odia/samples`) | **gone** |
| Odia method label | **gone** |

Also removed this round: the unused Odia helper functions in `web/src/api.js`, the “Hindi,
English or Odia” wording on the PDF screen, and the Odia mentions in the page copy. The
translator is Hindi → Santhali only.

---

## Screens in this build (12)

```
🏠 Dashboard             ⌨️  Text → Text          🃏 Flashcards      📖 Dictionary
🎙️ Voice Translator      📄  PDF translation      🖨️ Worksheets      ✅ Validation
📚 Lesson Board                                                  📶 Offline   🌏 About
```

The sidebar footer shows **build: BZyrw4lW** — if you ever see a different id, that tab is old.

## Verified on port 8100

- `/api/version` → `{"build":"BZyrw4lW","screens":12}` with `text` and `pdf` in the list
- bundle contains `nav_text`, `nav_pdf`, `ttTranslate`, `pdfTranslate`, `quickPdf` — all YES
- Hindi suite **169 · PASS 145 · review 24 · FAIL 0**
- Odia suite **31 · PASS 31 · FAIL 0**
- `RUN.md`, `run.sh`, `run.bat` now all use port **8100** too
