# Mundari and Ho: what the search found, and what got added

Your words: *"add the languages mundari and ho as the multilingual application search the
language data sets and add in this application as the selection should be in select method"*.

Live on **http://localhost:8100** — Translate, Text → Text and PDF translation each have a
**language `<select>`**: Santhali · Mundari · Ho.

---

## 1. Everywhere I looked (and what was there)

| Source searched | Mundari (`unr`) | Ho (`hoc`) |
|---|---|---|
| HF `api/datasets?search=` mundari / munda / ho / hoc / austroasiatic / jharkhand | only `jash0803/mun-dataset-hf` — **Model-UN debate prompts**, not the language | `sicsoc/eng-hoc-Tatoeba-Wiki` (1,606 pairs) |
| HF datasets by `language:` tag | `google/smol` (smoldoc en_unr-Deva) | `google/smol`, `sicsoc/*`, `project-boli/ho` (speech only) |
| Tatoeba per-language export | **404 — no Mundari export exists** | ✔ 2,450 sentences |
| Wikipedia | **no mun.wikipedia** | **no hoc.wikipedia** |
| Wikidata sitelinks (the trick that gave Santhali 7,549 pairs) | 0 pairs (no wiki = no sitelinks) | 0 pairs |
| Wiktionary lemma categories | 8 lemmas, ~5 usable | 53 lemmas, ~3 usable (mostly letters) |
| `HimangY/CoRil-Parallel` (125 files) | not covered | not covered |
| `ltrciiith/bhashik-parallel-corpora-generic` (231 GB) | not covered | listed, but **gated** — no access |
| MUNTTS paper (arXiv 2401.15579) — 27.5 h Mundari corpus "translated from a Hindi corpus of 100,000 sentences" | **corpus not published**; no HF dataset, no model card releasing it | — |
| GitHub `Nightmare-22/AI-Translator-Tool-for-Tribal-Languages` ("Ministry of Tribal Affairs" Hindi–Mundari IndicTrans2 fine-tune) | README + `main.py` only — **the parallel corpus and weights are not in the repo** | — |
| archive.org: `mundarienglishdi00bhad` (Mundari–English dictionary 1983) | **lending-restricted** (401 on the OCR) | — |
| archive.org: `dli.language.0668` मुण्डारी मुहावरा कोश (Hindi) | OCR is Latin gibberish — unusable | — |
| archive.org: `in.gov.tribals.74104` Munda primer, `…74112` Ho primer (Odisha Govt trilingual primers) | Odia-script page scan OCR collapses to noise | same |
| archive.org: Mundari Genesis 1961, Hoffmann's Mundari Grammar 1903, Ho grammar in Hindi | Genesis OCR is ~60% readable with no reliable verse numbers; grammar is English prose | Ho grammar in Hindi: partial, not clean enough to mine |
| HF model cards (`Piranav/whisper-*-mundari`, `tona3738/…mundari-hindi…`) | fine-tuned on **private** data; no dataset published | — |

**The finding, stated plainly: there is no published Hindi↔Mundari or Hindi↔Ho parallel
corpus, and no usable Hindi-side text of any kind.** That is the whole constraint this
feature had to be designed around — and it is why Mundari and Ho are *English-facing* in
this build. Anything else would have been invention.

## 2. What was actually added

Both packs are built by `pipelines/build_multi_lang_packs.py` (re-runnable, ~3 s) and use
the same schema as the Santhali pack, so one engine serves all three languages.

| | Mundari | Ho |
|---|---|---|
| attested sentence pairs | **6,020** | **7,557** (5,999 Warang Citi + 1,558 roman) |
| English→word lexicon (mined, mutual-best, dice ≥ 0.50) | **902** | **1,065** |
| Hindi→word entries through the English pivot | **39** | **36** |
| script shown | Devanagari | Warang Citi (roman tagged per sentence) |
| audio | yes — Hindi voice reads the Devanagari, labelled **approximate** | **none offered** (501 + reason) |
| Hindi words with no attested target word | 182 — declared, never guessed | 185 — declared |

Sources and licences (every one is recorded in `/api/languages` and in the pack `meta`):
`google/smol` smoldoc **CC-BY-4.0**, `sicsoc/eng-hoc-Tatoeba-Wiki` **Apache-2.0**,
English Wiktionary lemmas **CC-BY-SA-4.0**.

## 3. How the three languages behave

```
ENGLISH → full sentences (attested, high confidence)
   “Christianity is a religion based on the life and teachings of Jesus Christ.”
      → ईसाई धर्म ईसा मसीहअः जीबोन ओड़ोः इनितुको चेतन रे बइअकन धर्म तनअः।     [unr · high]
   “Hello, how are you?”     → Chia, cheleka menaḱpea?                     [hoc · high]
   “water”                   → दअ:                                          [unr · medium, dictionary]

HINDI → words through the English pivot, never a sentence
   पानी लाओ।                 → दअ:              1/2 words,  पानी → water → दअ:
   आम और अंडा                → 𑣇𑣚𑣂 𑣎𑣁𑣜𑣉𑣖    2/3 words,  आम → mango → 𑣇𑣚𑣂
   बकवास जुमला अजीब          → declined: “no Ho word for those Hindi words yet —
                                36 Hindi words are covered”
```

This is the rule you asked for, applied per language: **a low-confidence result is the
combination of the words we know, never a sentence.** For Mundari and Ho the pivot is
capped below *high* on purpose — two hops through English can be right about words and
wrong about sentences, so the platform only offers words and says which bridge it used
(`पानी → water → दअ:` under every single word).

The `<select>` itself carries the honest metadata: script, how many attested sentences
back the language, whether its audio is real or approximate or absent, and what Hindi vs
English input gets you. Switch it and the whole screen follows — including the PDF screen.

## 4. Checked, not asserted

```
tests/multilang_test_suite.py     46 checks | PASS 46 | FAIL 0
tests/hindi_test_suite.py        178 checks | PASS 154 | review 24 | FAIL 0   (no regression)
tests/odia_test_suite.py          31 checks | PASS 31 | FAIL 0               (no regression)
```

The new suite asserts the refusals as hard as the successes: Hindi into Mundari/Ho must
never populate a sentence field, Ho audio must return 501 with a readable reason, an
unknown target must be refused with the language list, and every PDF row must carry a
method.

## 5. What would move the needle next

1. **MUNTTS** (27.5 h Mundari, built from 15,656 Hindi sentences) — the authors' corpus, if
   they release it, would give Hindi→Mundari *sentences* immediately. Worth an email.
2. **Odisha / Jharkhand primers and the 1983 Mundari–English dictionary** — scan the OD
   pages properly (the archive OCR fails on Odia script); a teacher-assisted word list of
   300–500 classroom words per language would be worth more than another 10k wiki sentences.
3. **Bible parallel text** — Mundari Genesis 1961 + Mark 1876 are public domain; verse
   alignment to a Hindi/English Genesis is mechanical once the verse numbers are hand-checked.
4. **A validation pass with Ho/Mundari speakers** on the 75 pivot words already in the
   app — they are labelled `low`, so they never appear as sentences, but a teacher's ✓
   would promote them.

---

# Round 2 — Ho voice + more Mundari (what a second search turned up)

Live on **http://localhost:8100**, build **s3QewWZh**. Suites after this round:
**multilang 57/57**, **Hindi 178 | PASS 154 | review 24 | FAIL 0**, **Odia 31/31**.

## 2.1 New data — added

| Source | Licence | What it added |
|---|---|---|
| **PanLex** (`cointegrated/panlex-meanings`, `data/unr.tsv`, `data/hoc.tsv`, joined to `data/eng.tsv` for glosses) | **CC0-1.0** | **Mundari +369 new headwords** (427 glosses total, 3,132 meanings had English glosses available); **Ho +245 new headwords** (278 glosses). PanLex's Mundari comes largely from *A Mundari-English dictionary* (1983). Spellings are the dictionary's own **phonetic notation** and are kept verbatim, flagged `phonetic` |
| **Munda cognate set** (Zenodo `10.5281/zenodo.3380874`) | **CC0-1.0** | **103 Mundari + 99 Ho comparative forms** with the published source reference for each (BMED, HOGV, DHED …) and a proto-Munda reconstruction — a citable layer, kept separate |
| **`sicsoc/eng-hoc_aug2` + `eng-hoc_aug5`** | Apache-2.0 | **32,544 machine-augmented English–Ho pairs** (template + noun substitution) as a **separate, flagged layer**, never mixed into attested data |
| **`espnet/mms_ulab_v2`** | see dataset | tagged `language:hoc` **and** `language:unr` — real speech, but **no transcripts** (see 2.3) |

Resulting shape of the two packs:

| | Mundari | Ho |
|---|---|---|
| attested sentence pairs | 6,020 | 7,557 |
| machine-augmented pairs (flagged) | 0 | **32,544** |
| English→word lexicon | **1,271** (was 902) | **1,310** (was 1,065) |
| cognate forms | 103 | 99 |
| Hindi-reachable words | **148** (was 39) | **116** (was 36) |

The augmented Ho pairs are served as their own method, `sentence-memory-aug`, **capped at
medium confidence**, flagged `synthetic: true`, with a note telling the teacher to check it
with a speaker before teaching it. A synthetic sentence never masquerades as an attested one.

## 2.2 Hindi reach: measured, and the honest number

I joined PanLex **Hindi** (`data/hin.tsv`, 57.9 MB, 822,211 rows) to the same meanings: only
**12** of the 3,267 meanings have a Hindi expression in PanLex that overlaps these two
dictionaries. So PanLex does not widen the Hindi bridge — what widened Hindi reach from 39→148
(Mundari) and 36→116 (Ho) is the new *English* headwords meeting the existing Hindi→English
bridge. Hindi input still returns **words only**, via the pivot, exactly as before.

## 2.3 Ho voice — what I could and could not get

Attempted, in order:

1. **`project-boli/ho`** (17.8 MB, real Ho speech, CC-BY-NC-SA) — **gated**: the parquet files
   return a 125-byte "Access restricted" stub. Needs a HF account with access granted.
2. **`espnet/mms_ulab_v2`** — the only open Ho *and* Mundari speech. Its schema is
   `id, iso3, audio` with **no transcript column**, i.e. audio for listening, not TTS. Getting
   at it also proved impractical: the viewer API returned *"dataset index is loading"* then
   **503**, `/search` returned **502/504**, `/filter` rejected and then 503, and my fallback —
   reading parquet footers over HTTP — showed the 115 shards (~600 MB each, 69 GB total) are
   shuffled across the alphabet, so the Ho rows could be anywhere.
3. **Vaani Jharkhand** (131 MB, audio + transcript + language) — downloaded and inspected:
   **1,020 Hindi / 14 Bhojpuri / 2 Bengali, zero Ho or Mundari**. The Ho-speaking districts
   (West Singhbhum, Seraikela) are not in the Vaani set.
4. **ULCA/Bhashini Ho TTS** — still behind the login wall documented in `MUNDARI_TTS_CHECK.md`.
5. Ho ASR/TTS models on HF: **none** (`models?search=hoc asr` → empty; no `warang citi` model).

**So Ho still has no voice, and the app keeps saying so** (HTTP 501 with the reason, never a
wrong reading). What changed is that the platform is now *ready* for one:

```
data/tts_clips/<lang>/index.json      # any language, exact-match transcripts -> recordings
pipelines/ingest_mundari_tts.py --lang hoc|unr   # verifies, inventories, installs
```

Drop in an archive and that language speaks with its own recordings (`x-voice-engine:
"Ho (dataset recordings)"`); /api/health reports `recorded_speech` per language. Mundari
remains on the approximate Hindi voice until a Mundari TTS pack is installed.

## 2.4 What would still unlock Ho/Mundari voice

1. **The ULCA `dataset-mundari-tts-full.tgz`** you mentioned — upload it and the harness runs
   (`MUNDARI_TTS_CHECK.md`). Same for any ULCA Ho TTS archive.
2. **`project-boli/ho`** — request access on HF; 17.8 MB of real Ho speech with transcripts.
3. **Vaani-style collection in a Ho district** (Chaibasa/West Singhbhum) — the corpus design
   already works; the district list just doesn't include one.
