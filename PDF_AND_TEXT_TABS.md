# Where Text → Text is, and the new PDF translation

## 1. Where Text → Text lives

It is the **3rd item in the left nav**: `🎙️ Voice Translator`, then **`⌨️ पाठ → पाठ / Text → Text`**,
and it is also a **tile on the Dashboard** plus a button in the Dashboard hero row.

If you could not see it, the browser was holding an old copy of the app shell. **Fixed for good:**
`index.html` is now served with `Cache-Control: no-cache, no-store, must-revalidate`
(verified in the response headers), while the content-hashed `/assets/*.js` files are cached
forever. A tab added today can no longer be invisible because of a stale shell.

Serving the current build: **`index-DQw1vAVa.js`** — it contains `nav_text` and `nav_pdf`.

---

## 2. New: 📄 PDF translation

A **new screen in the nav** (4th item) *and* a new Dashboard tile — same place as the others.

### How a teacher uses it

1. Drop or choose a PDF (a textbook page, a circular, a question paper) — Hindi, English or Odia.
2. Pick how many pages to read (3 / 5 / 10) and optionally type the teacher and school name.
3. Read the bilingual table: each paragraph on the left, ᱥᱟᱱᱛᱟᱲᱤ on the right, with the method
   that produced it underneath.
4. **🖨️ Print / Save as PDF** — a clean A4 bilingual sheet, Ol Chiki intact.
   Or **⬇️ Download bilingual text** for pasting into anything else.

### What it does with each paragraph

| Step | Detail |
|---|---|
| Read | text extracted with `pypdf` — pure Python, no system libraries |
| Route by script | **Hindi** → the Hindi → Santhali engine · **English** → English sentence memory + your uploaded dictionaries + the aligned corpus lexicon · **Odia** → the attested Odia memory only |
| Retry | a paragraph that fails is split into sentences and each sentence is tried again, because the phrase book and the memories work at sentence level |
| Be honest | whatever is left is shown as **words only**, with a coverage % and the known words |

Two honesty features worth knowing:

- a **scanned PDF** (no text layer) is reported as such — it does not silently produce nothing;
- words that come from **automatic corpus alignment** carry a `?` in the printout, so a teacher
  knows which ones to confirm with a speaker.

### Measured, on your own uploaded PDF

`uploads/SIH-Problem-Statement-26042 (1).pdf` — English, 3 of its 30 pages:

```
pages 3/30 · text layer: yes
26 paragraphs · 0 translated as sentences · 26 word-by-word
average word coverage 33% · 82 words flagged as machine-aligned
```

**English prose does not get a sentence-level translation in this build** — there is no English
MT model, so an English page yields a glossary, not a translation, and the screen says exactly
that. Hindi is the direction this platform was trained for. Through the same pipeline a Hindi
page hits the phrase book directly:

```
आज हम गिनती सीखेंगे।      -> ᱛᱮᱦᱮᱧ ᱟᱞᱮ ᱞᱮᱠᱷᱟ ᱪᱮᱫᱚᱜ ᱞᱮᱭᱟ।     [phrase]
किताब बंद करो।            -> ᱯᱚᱛᱚᱵ ᱵᱚᱸᱫᱚᱭ ᱢᱮ!                    [phrase]
यह एक पेड़ है।            -> ᱱᱚᱶᱟ ᱫᱚ ᱢᱤᱫᱴᱟᱹᱝ ᱫᱟᱨᱮ ᱠᱟᱱᱟ।        [template]
सरकारी स्कूल में नया शिक्षक आया है।  -> words only, 85% of the words known
खोपड़ी, बत्तख, गाजर और चावल …        -> words only, 70%  (all from your uploaded files)
```

### API

```
GET  /api/pdf/status          -> {"ready": true, …}
POST /api/pdf/translate       multipart file=@page.pdf&max_pages=5  -> JSON
POST /api/pdf/report          the JSON back -> printable A4 HTML
POST /api/pdf/text            the JSON back -> plain-text download
```

Tested live: upload → 26 blocks returned, report HTML 25.7 KB with the print button, text
download 8.2 KB, a bad upload gets a 4xx instead of a crash.

### Install note

PDF reading needs one package. It is now in `RUN.md` in both places:

```
pip install fastapi "uvicorn[standard]" gtts python-multipart pypdf
```

Suites after all of this: **Hindi 169 · PASS 145 · review 24 · FAIL 0**,
**Odia 31 · PASS 31 · FAIL 0**.
