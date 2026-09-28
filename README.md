# 🪶 PALASH MTB-MLE — AI-Assisted Multilingual Education Platform

**SIH problem statement 26042** · Hindi-speaking teachers → Santhali-speaking students (Jharkhand tribal schools)

A **website** (not an Android app, per the prototype requirement) where a teacher speaks or types Hindi
and the classroom immediately sees and hears the lesson in **Santhali (Ol Chiki)** — plus auto-generated
flashcards, bilingual worksheets and assessments.

```
            ┌──────────────────────────────────────────────────────────┐
 Teacher ─► │ 🎙 Hindi voice / ⌨ text                                   │
            │        ↓ Web Speech API (hi-IN)                          │
            │   Hindi sentence                                         │
            │        ↓ 5-step translation engine (never invents Santhali)│
            │   ᱥᱟᱱᱛᱟᱲᱤ Ol Chiki  +  Devanagari (for the voice)  +  Roman │
            │        ↓                                                 │
 Students ◄ │ 🔊 audio · 🃏 flashcards · 🖨️ worksheets · 📚 lesson board │
            └──────────────────────────────────────────────────────────┘
                 ↑ teacher/native-speaker validation improves the pack
```




## Languages: Santhali, Mundari and Ho

The language selector on **Translate**, **Text → Text** and **PDF translation** offers three
target languages, and each one states what backs it (`GET /api/languages`):

| | Santhali (sat) | Mundari (unr) | Ho (hoc) |
|---|---|---|---|
| script | Ol Chiki | Devanagari | Warang Citi (roman also present) |
| Hindi input | sentences + words | **words only** | **words only** |
| English input | sentences + words | sentences | sentences |
| attested sentences | 12,000 | 6,020 | 7,557 |
| machine-augmented pairs (flagged, medium confidence) | — | — | 32,544 |
| English→word lexicon | 220 vocab + 469 dict | 1,271 | 1,310 |
| cognate forms (comparative Munda) | — | 103 | 99 |
| audio | Hindi voice via Devanagari transliteration (approximate) | same route, labelled approximate | none — refused with a reason |

Mundari and Ho are **English-facing** because no Hindi↔Mundari or Hindi↔Ho parallel corpus
exists publicly (the full search is in `MUNDARI_HO_REPORT.md`). English input therefore gets
real attested sentences; Hindi input gets the **combination of known words**, each one
showing its bridge (`पानी → water → दअ:`), and never a generated sentence.

Rebuild the packs at any time:

```
python3 pipelines/build_multi_lang_packs.py
```

## The confidence rule: a low-confidence answer is never a sentence

A wrong sentence cannot be un-read. So the translator is only allowed to answer with a
sentence when it can say where that sentence came from and how sure it is:

| Confidence | What the teacher gets |
|---|---|
| **high** | the Santhali sentence, with the method and its evidence |
| **medium** | the Santhali sentence, marked for validation |
| **low / none** | **never a sentence** — instead the combination of the words we know, in the order they appear, with `known/total`, a coverage %, and a spoken rendering of that combination |

Check it live:

```
curl -s -X POST localhost:8100/api/translate -H 'Content-Type: application/json' \
  -d '{"text":"आज मौसम बहुत अच्छा है।","source":"hi"}' | python3 -m json.tool
```

```json
{
  "ok": false, "method": "word-combo", "confidence": "low",
  "combination": "ᱛᱮᱦᱮᱧ ᱱᱟᱯᱟᱭ", "known": 2, "total": 5, "coverage": 0.4,
  "words": [{"hindi": "आज", "sat": "ᱛᱮᱦᱮᱧ", "english": "today"},
            {"hindi": "अच्छा", "sat": "ᱱᱟᱯᱟᱭ", "english": "good"}],
  "skipped": ["है"],
  "note": "no confident sentence for this text - these are the words we know, in order"
}
```

Two more things the rule does:

- **Nothing is thrown away silently.** If the cascade had produced a low-confidence
  sentence, it is moved into `suppressed` (with the reason) so a teacher can still see and
  correct it, and it still goes to the validation queue.
- **Function words are excluded from the list and named.** The corpus aligned है to ᱠᱤᱱ
  (a dual marker) and हैं to ᱠᱚ (a plural marker). Teaching those in a word list would be
  teaching a mistake, so they are left out and listed under `skipped` instead. The coverage
  percentage counts them as unknown, so the number never flatters itself.

The PDF screen has always worked this way (paragraphs it cannot translate are shown as
words-only); it now shares the same wording as the two text screens.

## PDF translation

Drop a PDF on the **📄 PDF translation** screen (or `POST /api/pdf/translate`) and you get back
a bilingual, printable page: each paragraph of the original on the left, Santhali on the right,
with the method that produced it underneath.

```
POST /api/pdf/translate        multipart file=@page.pdf   -> JSON (blocks, stats)
POST /api/pdf/report           the JSON above              -> printable A4 HTML
POST /api/pdf/text             the JSON above              -> plain-text download
GET  /api/pdf/status                                       -> is pypdf installed
```

How a paragraph is handled:

1. text is pulled out with `pypdf` (pure Python — nothing to install but the package),
2. the script it is written in decides the route: **Hindi** → the normal Hindi → Santhali
   engine, **English** → the English sentence memory, the uploaded dictionaries and the
   aligned corpus lexicon, **Odia** → the attested Odia memory only,
3. a paragraph that fails is split into **sentences** and each sentence is tried again,
   because the phrase book and the memories work at sentence level,
4. whatever is left is reported as **words only**, with a coverage % and the known words.

Nothing is invented, and a scanned PDF (no text layer) is reported as such instead of
producing an empty translation. Words that come from automatic corpus alignment are marked
with a `?` in the printout so a teacher knows which ones to check with a speaker.

Measured on the uploaded `SIH-Problem-Statement-26042.pdf` (English, 3 of 30 pages):
26 paragraphs, 0 translated as sentences, 26 word-by-word at 33% average word coverage
(82 of those words flagged as machine-aligned). English prose has no sentence-level
translation in this build — an English *page* gives a glossary, not a translation, and the
screen says so. Hindi pages do much better, because that is the direction the platform was
trained for.

## Odia (ଓଡ଼ିଆ) — direct from memory, no chain

**The translator is Hindi → Santhali only.** There is no Odia → Hindi → Santhali chain any
more, and no Odia input switch on the Translate page.

Odia is still understood, but in one narrow way: if a teacher pastes an Odia sentence that is
already in the trained Odia memory (`data/raw/odia_train.txt`), the Santhali that was written
in that file comes back **directly** — no Hindi step, nothing generated. Anything else is
declined, so Odia can never produce an invented sentence.

```
ଏକି ଜୋମ ଆକଗ_ଏ          →  ᱮᱠᱤ ᱡᱚᱢ ᱟᱠᱟᱜ ᱮ            [odia-direct]
ଆଜି ଆମେ ସ୍କୁଲରେ ଗଣିତ ଶିଖିବା →  declined: "not in the trained Odia translations"
```

Two probes, both exact:

1. the sentence as pasted,
2. the same sentence typed in Devanagari — it is converted to Odia script first and looked
   up again (5/5 of the memory sentences are recovered this way).

`source: "or"` forces the lookup, `source: "auto"` detects Odia script. A Hindi sentence is
never mistaken for Odia.

```bash
curl -s -X POST localhost:8100/api/translate \
  -H 'Content-Type: application/json' \
  -d '{"text":"ଏକି ଜୋମ ଆକଗ_ଏ","source":"or"}' | python3 -m json.tool
```

- `GET /api/odia/memory` — the Odia → Santhali pairs that can be answered
- `GET /api/odia/samples` — the same pairs, for a demo
- `GET /api/odia/stats` — says so in one line: *direct Odia → Santhali memory lookup (no Hindi step)*
- `POST /api/odia/convert` — **removed**

The Hindi engine also tries one more thing before giving up on a sentence: it converts the
Hindi to Odia and looks it up in that memory. Measured honestly — **0 of the 398** reference
sentences in the file can reach a memory answer this way, because the two halves of
`odia_train.txt` are not aligned. The probe stays because it costs nothing and would start
working if an aligned file arrives.

## Testing

```bash
python3 tests/hindi_test_suite.py                  # against http://127.0.0.1:8100
python3 tests/hindi_test_suite.py http://localhost:8200
```

169 checks: 117 Hindi sentences across every feature (classroom phrases, "this is a ..." frames,
all 220 words from the dataset, numbers 1-15, speech-style misspellings, out-of-domain
sentences, edge cases) plus 6 printable worksheets, plus a round trip over the
Hindi → Santhali dictionary and the number system. The report is written to
`tests/hindi_testing_sentences.md` and `.csv`, and it lists the actual reply of the running
application, so it doubles as a demo script.

```bash
python3 tests/odia_test_suite.py                   # direct Odia -> Santhali memory, 31 checks
```

`tests/odia_testing.md` / `.csv` check the direct path: every memory sentence returned
verbatim, auto-detection, the same sentence typed in Devanagari, an unseen Odia sentence being
declined rather than generated, and that `/api/odia/convert` is gone.

## Run it

```bash
# 1. backend (serves the API *and* the built front-end on one port)
python3 -m uvicorn server.main:app --host 0.0.0.0 --port 8000

# 2. (optional) rebuild the front-end after editing web/
cd web && npm install && npm run build

# 3. (optional) rebuild the language pack from raw data
python3 pipelines/build_language_pack.py
python3 pipelines/prewarm_audio.py        # caches every word/phrase as audio
```

Open <http://localhost:8100> → the whole platform is one service (easy to run on a
school LAN server, and a WebView wrapper makes it an Android app later).

## UI in English **and** Hindi

Every label exists in both languages; the toggle is in the top-right of the header
(`English` / `हिन्दी`) and the choice is remembered on the device. The default is Hindi,
because that is the teacher's working language in these schools.

## What is real (and what it honestly is not)

| Feature | Status |
|---|---|
| Hindi → Santhali translation | **Working** via a 5-step cascade, every answer carries `method`, `confidence`, `evidence` |
| Santhali text display | **Working** — Ol Chiki + Devanagari + Roman pronunciation |
| Santhali audio | **Working** — Hindi voice reading a matra/virama-aware Devanagari transliteration (no public Santhali TTS model exists; the API slot is ready for one) |
| Voice input (teacher) | **Working, with 3 paths** — see “Voice input” below |
| Flashcards (picture + Hindi + Santhali + audio) | **Working** — 218 words, 13 themes |
| Bilingual worksheets | **Working** — 5 print-ready A4 templates, Hindi + Ol Chiki |
| Offline-first | **Working** — service worker caches app shell, language pack and every played audio clip |
| Human-in-the-loop validation | **Working** — 94 items auto-queued; a correction instantly changes translations platform-wide |
| Free-form sentence translation of anything | **Deliberately conservative** — falls back to a flagged word-by-word glossary rather than inventing grammar |

### The translation cascade (`server/engine.py`)

1. **Phrase book** — 60 classroom instructions, each either corpus-attested or built by swapping a
   noun into an attested frame (e.g. ᱯᱚᱛᱚᱵ ᱵᱚᱸᱫᱚᱭ ᱢᱮ! → ᱫᱩᱣᱟᱹᱨ ᱵᱚᱸᱫᱚᱭ ᱢᱮ!)
2. **Curated glossary** — 220/221 foundational-literacy words (Hindi → English → Santhali pivot)
2b. **Numbers** — digits (`25`) or Hindi words (`पच्चीस`) answered from the compositional
   Santhali system (ᱜᱮᱞ ᱢᱤᱫ = ten-one = 11, ᱵᱟᱨ ᱜᱮᱞ = two-ten = 20), 0-100 + thousand/lakh/crore
2c. **Hindi → Santhali dictionary** — 469 words rebuilt from the nine Santhali dictionary
   files the school supplied (see `data/raw/SOURCES.md`). Each row carries its Hindi side,
   so a word like खोपड़ी or बत्तख is answered directly, with its source quoted as evidence
3. **Wikidata title memory** — 6,911 Hindi → Santhali forms from sat.wikipedia × hi.wikipedia
4. **Instruction templates** — 13 attested Santhali frames + 17 attested verb forms
5. **Vocabulary assist** — per-word glossary, explicitly labelled *not validated*, pushed to the queue

Nothing is emitted without provenance: `pipelines/grammar.py` re-verifies every verb form and sentence
frame against the parallel corpus at build time and drops anything it cannot find.

## Voice input — three paths, because one is never enough

Voice is the whole point of the problem statement, and a single mechanism fails in
the real world, so the translator offers three:

1. **Live dictation** — Web Speech API (`hi-IN`), instant, but Chrome/Edge only and it
   needs microphone permission for the page. *Embedded/sandboxed preview frames do not
   get that permission*, so inside the in-app preview this button is hidden and the app
   explains why instead of failing silently.
2. **Record & transcribe** — the teacher taps record, audio is POSTed to `/api/asr`, and
   **faster-whisper (small, int8)** returns Devanagari Hindi which then goes through the
   normal translation engine. Works in Firefox/Safari too, and anywhere Web Speech API
   is missing. Verified round trip: *spoken → `आज हम गिनती सीखेंगे।` → `ᱛᱮᱦᱮᱧ ᱟᱞᱮ ᱞᱮᱠᱷᱟ ᱪᱮᱫᱚᱜ ᱞᱮᱭᱟ।` → audio (200, 22 KB)*.
3. **Tap to speak** — a board of verified classroom instructions and words. Tap a full
   sentence to translate it instantly, or tap words to build one. **Needs no microphone
   at all**, so it works in every environment including the sandboxed preview.

The Voice Translator panel also shows a live capability read-out (`SpeechRecognition`,
`MediaRecorder`, secure context, embedded frame, server ASR), a **Test microphone** button,
and an **Open in a new tab** button — opening the app in its own tab is what actually
unlocks the microphone when the preview frame blocks it.

### Enabling server-side speech recognition

```bash
pip install faster-whisper python-multipart      # model downloads on first request (~480 MB, cached)
```

Without it the API reports `package_available: false` at `/api/asr/status`, the record
button hides itself, and everything else keeps working. **Hindi only** — Santhali speech
recognition has no public model; `XKaab/ASR-santali_100hrs` on Hugging Face is the future
training set.

### ASR-tolerant matching

Whisper drops nasal marks (`कहाँ है` → `कहा है`) and mixes up conjunct spellings
(`बंद` / `बन्द`), so the engine folds both the query and the stored phrases
(nasal marks, nukta, `न्द → ंद`, `ण्ड → ंड`, …) before matching. A raw ASR transcript
still resolves to the attested classroom phrase, not to a word list.

## Data (all from Hugging Face + Wikidata, see `data/raw/SOURCES.md`)

| Source | Rows | Use |
|---|---|---|
| `aiswarya9302/english-santali-combined` (HF) | 72,977 pairs | sentence memory, word alignment, attestation |
| `google/smol` — `smolsent/sat_en`, `gatitos/sat_en`, `gatitos/sat-Latn_en` (HF) | 3,395 + 3,503 + 863 | word lexicon + romanisation |
| `google/smol` — `smoldoc/hoc-Wara_en` (HF) | 457 docs | Ho language pack (next phase) |
| `santali-train.csv` (team-supplied Tatoeba/Wikipedia corpus) | 19,999 rows (19,832 new) | sentence memory + attestation + consensus mining; corrected 3 entries and resolved 15 more words |
| `odia_train.txt` (team-supplied, Odia script) | 782 lines · 398 Odia + 384 Santhali | Santhali half decoded Ol Chiki (116 sentences, 212 spellings); Odia half converted to Hindi and wired to the Odia input box |
| Wikidata sitelinks (sat.wikipedia ↔ hi.wikipedia) | 7,549 → 6,911 clean | Hindi → Santhali names/concepts |
| `uploads/` — nine Santhali dictionary files (team-supplied) | 2,505 records → 1,250 headwords | 469 words + 106 numbers + 34 sentences + 554 names, re-based to Hindi; per-file accounting at `/api/dictionary/files` |
| Project lexicon `pipelines/lexicon.py` | 221 words + 43 instructions | educational pivot + vetted core |

## Layout

```
server/      FastAPI app: engine.py (translation), tts.py (audio + cache), content.py (worksheets/flashcards), main.py (API)
web/         React 18 + Vite app (bilingual UI, 12 screens)
pipelines/   translit.py (Ol Chiki ↔ Devanagari/Roman), lexicon.py, grammar.py, build_language_pack.py, prewarm_audio.py
data/raw/    downloaded corpora     data/language_packs/sat.json    data/audio_cache/ (1,142 clips, 10.6 MB)
```

## Screens

Teacher Dashboard · Voice Translator · **Text → Text** (typing only: no microphone, no
audio — translate, copy the Ol Chiki, use it in a worksheet or a message) · **PDF → Santhali**
(drop a PDF, get a bilingual printable page) · Lesson Board (full-screen presenter, ←/→ keys) · Flashcards
(+ quick comprehension check) · Worksheet Generator (live A4 preview → print/PDF) · Vocabulary Bank ·
Hindi → Santhali Dictionary (search, theme and file filters, tap-to-hear number grid, per-file report) ·
Validation (human-in-the-loop) · Offline & Sync · About & Impact.

## Roadmap (matches the problem statement's phases)

- **Phase 1 (this build):** Hindi text + voice, Hindi → Santhali, Santhali audio, worksheets, flashcards, offline caching
- **Phase 2:** richer educational vocabulary, teacher analytics, better speech models
- **Phase 3:** fully offline translation + on-device speech models
- **Phase 4:** Ho & Mundari packs (Ho data is already wired up), then other states
