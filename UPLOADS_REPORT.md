# Hindi → Santhali re-base of the uploaded files — what was actually done

**Server:** running on port 8000. **New page:** 📖 **शब्दकोश / Dictionary** in the left nav
(tabs: Words · Numbers · Supplied files).

Rebuild chain:

```
python3 pipelines/dict_hi.py          # hand-written Hindi for the English headwords
python3 pipelines/dict_sentences.py   # hand-written Hindi for the Santhali sentences
python3 pipelines/build_dictionary.py # uploads -> data/raw/hindi_sat_dictionary.json
python3 pipelines/build_language_pack.py
```

---

## 1. Every supplied file, and where it landed

The nine files were **English ↔ Santhali**. Each headword was given a Hindi side —
classroom Hindi written by hand (`dict_hi.py`, 509 words), the project's foundational-literacy
list, or (last resort, 41 words) an English→Hindi Wikipedia title marked `confidence: medium`.
Nothing was invented and nothing was dropped silently.

| File | Rows read | Headwords | Now in the app as | Used for |
|---|---|---|---|---|
| `Santali Open dictionary.csv` | 365 | 348 | 257 words | vocabulary + number-word evidence |
| `Glossary (eng-sat).csv` + `Glossary(eng-sat).txt` | 721 | 345 | 254 words | vocabulary + number-word evidence |
| `Glossary (sat-eng).csv` | 1,277 | 1,245 | 465 words | vocabulary |
| `Body Parts.csv` | 50 | 50 | 48 words | vocabulary |
| `Relation.csv` | 37 | 35 | 35 words | vocabulary |
| `Eatables.csv` | 55 | 47 | 46 words | vocabulary |
| `Name Translation.csv` | 554 rows | — | 554 proper names | names (transliteration, not translation) |
| `T General (0.06k).csv` | 59 rows | — | 34 sentences | classroom sentences, hand-translated to Hindi |

**8 / 8 file groups used.** Totals in the packaged dictionary: **469 words · 106 numbers ·
34 sentences · 554 names.** Live proof: `GET /api/dictionary/files`.

The same 469 words now also feed **flashcards, quizzes, the Lesson Board and the printable
worksheets** (body parts, food, animals, family), each marked *not yet validated* so it lands
in the teacher's validation queue.

## 2. What could not be translated, and why

- **781 headwords got no Hindi side and were left out** — mostly language/script names
  (Walloon, Syriac, …), English numbers spelled out in words (the number system covers
  those), and damaged rows.
- **9 headwords were deliberately skipped**, each with a reason stored in the pack and shown
  on the page: `panter` (typo), `hoond` (not a word), `comfit` (ambiguous), `rump`
  (दुम or कूल्हा?), `caror` (typo for crore), `O` (single letter), `velid name for a pig`
  (corrupt row), `santal` (ethnonym), `sagun` (source loanword).
- **मेहनत (hard work)** is still unanswered — none of the nine files contains it. It is the
  only gap left in the 221-word teaching list. **220 / 221.**

## 3. Spellings the files typed wrong

The dictionaries were typed on a Latin keyboard, so `.` stands in for the gicher `ᱹ`:
`ᱠᱟ.ᱦᱩ` = ᱠᱟᱹᱦᱩ, `ᱦᱟ.ᱛᱤ` = ᱦᱟᱹᱛᱤ, `ᱢᱩᱞᱟ.` = ᱢᱩᱞᱟᱹ (radish). A `.` is rewritten only when it
sits **between two Ol Chiki letters**, so real punctuation survives. 12 spellings fixed, and
the same fix now protects the pack itself (ᱯᱤᱯᱤᱲᱤᱭᱟ.ᱝ → ᱯᱤᱯᱤᱲᱤᱭᱟᱝ, ᱢᱟ.ᱪᱤ → ᱢᱟᱹᱪᱤ).

## 4. Where the files and the shipped word list disagreed — 59 words

The taught form **stays** and the file's spelling is kept as an alternate. Nothing is
overwritten silently. Six were genuine errors and were corrected because the files were right:

| Hindi | Was | Now | Why |
|---|---|---|---|
| चार | ᱯᱳᱱ | **ᱯᱩᱱ** | standard form; also composes 40 = ᱯᱩᱱ ᱜᱮᱞ |
| तेरह | ᱜᱮᱯᱮ | **ᱜᱮᱞ ᱯᱮ** | 11 = ᱜᱮᱞ ᱢᱤᱫ, 12 = ᱜᱮᱞ ᱵᱟᱨ, so 13 = ᱜᱮᱞ ᱯᱮ |
| चावल | ᱫᱟᱠᱟ | **ᱪᱟᱣᱞᱮ** | ᱫᱟᱠᱟ is *cooked* rice (भात) |
| शून्य | ᱐ | **ᱥᱩᱱᱭᱚ** | a word, not the numeral glyph |
| धरती | ᱛᱷᱟᱨᱛᱤ | **ᱚᱛ** | ᱛᱷᱟᱨᱛᱤ was Hindi-shaped |
| उँगली | ᱠᱟᱛᱩᱵ | **ᱠᱟᱹᱴᱩᱵ** | all five rows of four files write ᱠᱟ.ᱴᱩᱵ |

Two words that were unanswered before are now answered by these files: **अनार → ᱟᱱᱟᱨ**
(four files agree) and **नारंगी → ᱜᱮᱨᱩᱣᱟ** (the files tag it `Category=Colour`; ᱠᱚᱢᱞᱟ/ᱡᱟᱹᱢᱵᱤᱨ
is the fruit).

## 5. Numbers

Two files carry **101 spelled-out number rows each**. They were used as *evidence*, not
copied, because they disagree with each other on several numbers (ᱟᱨᱮᱞ/ᱟᱨᱮ, ᱯᱤᱱ/ᱯᱩᱱ,
ᱢᱚᱸᱬᱮ/ᱢᱚᱬᱮ). The composition rule is what ships: ᱜᱮᱞ ᱢᱤᱫ = ten-one = 11, ᱵᱟᱨ ᱜᱮᱞ = two-ten = 20,
ᱯᱩᱱ ᱜᱮᱞ = four-ten = 40. Digits (`25`), Devanagari digits and Hindi words (`पच्चीस`) all
answer. 0–100 plus हज़ार / लाख / करोड़ — 106 entries.

## 6. Test results on the running server

| Suite | Result |
|---|---|
| `tests/hindi_test_suite.py` | **169 checks · PASS 145 · review 24 · FAIL 0** |
| `tests/odia_test_suite.py` | **20 checks · PASS 20 · FAIL 0** |

The 24 *review* rows are sentences outside the trained domain — the app answers with a word
bank and says so, instead of inventing a sentence. The Hindi suite now also round-trips the
dictionary (one sample per source file) and the number system.
Reports: `tests/hindi_testing_sentences.md` / `.csv`, `tests/odia_testing.md` / `.csv`.

Audio: the offline cache was re-generated for the new words — **1,142 clips (10.6 MB)**, so a
classroom with no internet still hears every word and number.
