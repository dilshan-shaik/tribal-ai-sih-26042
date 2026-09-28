# Raw data provenance

Downloaded for the SIH 26042 prototype. Re-download with the commands below.

| File | Source | Rows | Download |
|---|---|---|---|
| `en_sat_webscrap_v2.parquet` | Hugging Face `aiswarya9302/english-santali-webscrap-combined-v2` (not gated) | 73,206 raw → 71,303 after the Ol-Chiki filter, of which **248 lines were new (0.3%)** | `curl -L -o en_sat_webscrap_v2.parquet https://huggingface.co/api/datasets/aiswarya9302/english-santali-webscrap-combined-v2/parquet/default/train/0.parquet` |
| `en_sat.parquet` | Hugging Face `aiswarya9302/english-santali-combined` | 72,977 (71,106 kept after Ol Chiki filter) | `curl -L -o en_sat.parquet https://huggingface.co/api/datasets/aiswarya9302/english-santali-combined/parquet/default/train/0.parquet` |
| `gatitos_sat_en.jsonl` | Hugging Face `google/smol` (`gatitos/sat_en.jsonl`) | 3,395 Santhali word → English gloss entries | `curl -L -o gatitos_sat_en.jsonl https://huggingface.co/datasets/google/smol/resolve/main/gatitos/sat_en.jsonl` |
| `gatitos_sat_latn_en.jsonl` | `google/smol` (`gatitos/sat-Latn_en.jsonl`) | 3,503 Latin-script entries | `curl -L -o gatitos_sat_latn_en.jsonl https://huggingface.co/datasets/google/smol/resolve/main/gatitos/sat-Latn_en.jsonl` |
| `smolsent_sat_en.jsonl` | `google/smol` (`smolsent/sat_en.jsonl`) | 863 sentence pairs | `curl -L -o smolsent_sat_en.jsonl https://huggingface.co/datasets/google/smol/resolve/main/smolsent/sat_en.jsonl` |
| `hoc_wara_en.jsonl` | `google/smol` (`smoldoc/hoc-Wara_en.jsonl`) | 457 Ho-language documents (Wara Chiti script) — reserved for the Ho pack | `curl -L -o hoc_wara_en.jsonl https://huggingface.co/datasets/google/smol/resolve/main/smoldoc/hoc-Wara_en.jsonl` |
| `santali-train.csv` | **Team-supplied** Tatoeba/Wikipedia-style corpus (columns: index, English, Santali) | 19,999 rows · 19,821 kept · **19,832 lines new to the pack** | already in place; supplied with the project |
| `hi_sat_wikidata.json` | Wikidata Query Service, sat.wikipedia ↔ hi.wikipedia sitelinks | 7,549 pairs (6,911 usable after filtering) | SPARQL (POST, `Accept: application/sparql-results+json`), query in commit history / see below |

Wikidata query used:

```sparql
SELECT ?sat ?hi WHERE {
  ?satUrl schema:about ?item ; schema:isPartOf <https://sat.wikipedia.org/> ; schema:name ?sat .
  ?hiUrl  schema:about ?item ; schema:isPartOf <https://hi.wikipedia.org/>  ; schema:name ?hi .
} LIMIT 2000 OFFSET 0     -- paged; the endpoint rate-limits, retry on 502
```

Datasets evaluated and **rejected** (kept out of the pack):

- `HuggingFaceFW/finetranslations` (`sat_Latn`) — rows are English web text, not Santhali.
- `Maitreyajayaraj/data_santhali_Agrade_v1_01.json` — content is romanised Bengali medical Q&A.
- `wikimedia/wikipedia` (`20231101.sat`) — usable later for extra monolingual Santhali text/TTS training.
- `ai4bharat/Bhasha-Abhijnaanam`, `ai4bharat/IN22-Gen` — Indic benchmarks, no Santhali-Hindi parallel text.

No Santhali TTS/ASR checkpoint exists on the Hub; `XKaab/ASR-santali_100hrs` exists for future ASR work.

---

## The nine Santhali dictionary files (and how they became Hindi → Santhali)

`uploads/` was supplied as **English ↔ Santhali**. The platform answers Hindi →
Santhali, so every headword was given a Hindi side first. That Hindi is the Hindi a
teacher speaks in class, not encyclopaedia Hindi.

| File (in `uploads/`) | Rows read | Headwords | Shows up as | How the Hindi was written |
|---|---|---|---|---|
| `Santali Open dictionary.csv` | 365 | 348 | 257 words | hand-written (`pipelines/dict_hi.py`) + the project word list |
| `Glossary (eng-sat).csv` + `Glossary(eng-sat).txt` | 721 | 345 | 254 words | same |
| `Glossary (sat-eng).csv` | 1,277 | 1,245 | 465 words | same |
| `Body Parts.csv` | 50 | 50 | 48 words | same |
| `Relation.csv` | 37 | 35 | 35 words | same |
| `Eatables.csv` | 55 | 47 | 46 words | same |
| `Name Translation.csv` | (554 rows) | — | 554 proper names | names are transliterated, not translated |
| `T General (0.06k).csv` | 59 rows | — | 34 sentences | hand-written from the Santhali (`pipelines/dict_sentences.py`) |

Two of the files also carry **101 spelled-out number rows** each; those were used as
evidence for the compositional number system (ᱜᱮᱞ ᱢᱤᱫ = ten-one = 11, ᱵᱟᱨ ᱜᱮᱞ =
two-ten = 20) rather than copied, because the files spell several numbers differently
(ᱟᱨᱮᱞ/ᱟᱨᱮ for nine, ᱯᱤᱱ/ᱯᱩᱱ for four, ᱢᱚᱸᱬᱮ/ᱢᱚᱬᱮ for five).

Rebuild with:

```
python3 pipelines/dict_hi.py
python3 pipelines/dict_sentences.py
python3 pipelines/build_dictionary.py
python3 pipelines/build_language_pack.py
```

Result: `data/raw/hindi_sat_dictionary.json` — 2,505 records → 1,250 unique headwords
→ **469 Hindi → Santhali entries** (428 hand-curated or from the project word list, 41
from English→Hindi Wikipedia titles as a last resort and marked `confidence: medium`),
106 numbers, 34 sentences, 554 names. 781 headwords could not be given an honest Hindi
side and were **left out**, never guessed.

### Spellings the files typed wrong, and what was done

The dictionaries were typed on a Latin keyboard, so `.` appears where Ol Chiki needs
the gicher `ᱹ`: `ᱠᱟ.ᱦᱩ` = ᱠᱟᱹᱦᱩ, `ᱦᱟ.ᱛᱤ` = ᱦᱟᱹᱛᱤ, `ᱢᱩᱞᱟ.` = ᱢᱩᱞᱟᱹ (radish). A `.`
is only rewritten when it sits **between two Ol Chiki letters**, so real punctuation
and real full stops survive. 12 spellings were normalised this way.

### Where the uploaded files and the shipped word list disagree (59 words)

The taught form **stays** and the other spelling is kept as an alternate. Nothing is
overwritten silently. Seven of them were real errors, now corrected because the files
were right:

| Hindi | Was | Now | Why |
|---|---|---|---|
| चार | ᱯᱳᱱ | **ᱯᱩᱱ** | ᱯᱩᱱ is the standard form and composes 40 = ᱯᱩᱱ ᱜᱮᱞ |
| तेरह | ᱜᱮᱯᱮ | **ᱜᱮᱞ ᱯᱮ** | 11 is ᱜᱮᱞ ᱢᱤᱫ, 12 ᱜᱮᱞ ᱵᱟᱨ — so 13 is ᱜᱮᱞ ᱯᱮ |
| चावल | ᱫᱟᱠᱟ | **ᱪᱟᱣᱞᱮ** | ᱫᱟᱠᱟ is *cooked* rice (भात); चावल is uncooked |
| शून्य | ᱐ | **ᱥᱩᱱᱭᱚ** | a word, not the numeral glyph |
| धरती | ᱛᱷᱟᱨᱛᱤ | **ᱚᱛ** | ᱛᱷᱟᱨᱛᱤ was Hindi-shaped; ᱚᱛ is the Santhali word |
| उँगली | ᱠᱟᱛᱩᱵ | **ᱠᱟᱹᱴᱩᱵ** | all five rows of four files write ᱠᱟ.ᱴᱩᱵ (gicher dropped by the corpus) |
| नारंगी | ᱡᱟᱢᱵᱤᱨ | **ᱜᱮᱨᱩᱣᱟ** | ᱜᱮᱨᱩᱣᱟ is the colour; ᱡᱟᱹᱢᱵᱤᱨ/ᱠᱚᱢᱞᱟ is the fruit |

Two words that were listed as unresolved earlier are now answered from these files:
**अनार → ᱟᱱᱟᱨ** (four files agree) and **नारंगी → ᱜᱮᱨᱩᱣᱟ**. Only **मेहनत** (hard
work) is still unanswered — none of the nine files has it, and it is not worth
inventing a word for a concept the dictionary does not cover.

Everything that was left out is listed with a reason in the package (`meta.skipped_headwords`,
surfaced at `/api/dictionary/files`) — mostly language and script names, English
spelled-out numbers (the number system covers those), and damaged rows such as
`velid name for a pig`, `Small leguminous plant`, `panter`, `hoond`.

---

## `odia_train.txt` (team-supplied, Odia script) — how it is used now

782 lines, two monolingual streams: 398 Odia sentences and 384 Santhali sentences printed in
mission-era Odia script. The two halves are **not aligned**, so they cannot be used as a
translation memory. What was salvaged:

| Output | Count | How |
|---|---|---|
| Santhali sentences recovered in Ol Chiki | 116 | `pipelines/build_odia_corpus.py` decodes each word and keeps only forms attested elsewhere in the pack |
| Odia-script spellings of those words | 212 | the same decode, kept as evidence |
| Odia sentences + their Hindi reading | 398 | `pipelines/odia.py` (`ODIA_HINDI` lexicon first, transliteration for the rest) — **reference only, they have no Santhali counterpart**, so they are never used to answer |

Build with:

```
python3 pipelines/build_odia_corpus.py
python3 pipelines/build_language_pack.py
```

**What the app does with it:** Odia → Santhali is a *direct* memory lookup — paste a sentence
that is in the 116 and the Santhali comes back verbatim, no Hindi step and no generation.
Anything else is declined. The Odia → Hindi → Santhali chain and `POST /api/odia/convert` were
removed on request; Hindi → Santhali is now the only translation the platform performs.
