# Odia removed — Hindi → Santhali is now the only translation

Server is running on port 8000 with the new build (`index-D24PYFLl.js`).

## What was removed

| Removed | Where |
|---|---|
| The **Odia → Hindi → Santhali chain** | `server/engine.py` — `translate()` no longer converts Odia to Hindi and no longer feeds it into the cascade |
| `POST /api/odia/convert` (the Odia → Hindi step) | `server/main.py` — the route is gone |
| The **Odia input switch** on the Translate page | `web/src/pages/Translate.jsx` — only हिन्दी (Hindi) is offered |
| The **"Odia → Hindi" step card** in the result panel | `web/src/pages/Translate.jsx` |
| The Odia UI strings (`langOdia`, `typeOdia`, `odiaHint`, `chainOdiaHindi`, `odiaLexicon`) | `web/src/i18n.js` — 0 occurrences left in the bundle |
| The `odia_to_hindi` conversion inside the engine | no longer imported on the translation path |

Verified in the shipped bundle: `typeOdia` 0, `odiaHint` 0, `chainOdia` 0, `Odia → Hindi` 0.

## What Odia does now — direct only

Paste an Odia sentence that is already in the trained Odia memory and the Santhali comes back
**as it was written in your file** — no Hindi step, and nothing generated:

```
ଏକି ଜୋମ ଆକଗ_ଏ                     →  ᱮᱠᱤ ᱡᱚᱢ ᱟᱠᱟᱜ ᱮ              [odia-direct]
କୋଜ଼ କୁଜ଼ୀ ମଇଦ ଟକୋ ଏନଏଜ aସେ      →  ᱠᱚᱡᱚ ᱠᱩᱡᱚ ᱢᱤᱫ ᱴᱚᱠᱚ ᱮᱱᱮᱡ ᱥᱮ    [odia-direct]
ଆଜି ଆମେ ସ୍କୁଲରେ ଗଣିତ ଶିଖିବା       →  declined — "not in the trained Odia translations"
```

Two exact probes, no generation:

1. **as pasted** — an Odia sentence from the memory,
2. **converted to Odia first** — the same sentence typed in Devanagari letters is converted and
   looked up again. Measured: **5/5** of the sampled memory sentences are recovered this way.

A Hindi sentence is never mistaken for Odia, and `source: "auto"` still detects Odia script
without the teacher choosing anything.

## Sentences that used to go through the chain

These previously produced a Santhali sentence via the Hindi step. They now decline, because
the file's Odia half is not in memory — this is the behaviour you asked for:

| Odia input | Before (chain) | Now |
|---|---|---|
| ମାଛ ପାଣିରେ ରହେ | ᱦᱟᱹᱠᱩ ᱫᱚ ᱫᱟᱜ ᱨᱮᱠᱚ ᱛᱟᱦᱮᱸᱱ ᱠᱟᱱᱟ᱾ | declined |
| କିତାବ ବନ୍ଦ କର | ᱯᱚᱛᱚᱵ ᱵᱚᱸᱫᱚᱭ ᱢᱮ! | declined |
| ଫଳ କାହିଁ ଅଛି | ᱡᱚ ᱫᱚ ᱚᱠᱟᱨᱮ ᱢᱮᱱᱟᱜᱼᱟ ? | declined |

Paste the **Hindi** (मछली पानी में रहती है। / किताब बंद करो। / फल कहाँ है?) and all three answer
exactly as before — the Hindi side was not touched.

## The one extra probe you asked for

The Hindi engine now also converts the Hindi input to Odia and checks whether that Odia string
is present in the Odia translations. Measured honestly: **0 of the 398** reference sentences in
`odia_train.txt` can reach a memory answer this way, because the file's two halves (398 Odia
sentences, 116 recoverable Santhali sentences) do **not** overlap — I checked all
398 → 0 intersections. The probe stays in the cascade because it costs nothing and would start
working the moment an aligned file arrives; it is not something I can claim is carrying weight today.

## Test results on the running server

| Suite | Result |
|---|---|
| `tests/hindi_test_suite.py` | **169 checks · PASS 145 · review 24 · FAIL 0** |
| `tests/odia_test_suite.py` (rewritten) | **31 checks · PASS 31 · FAIL 0** |

The rewritten Odia suite now proves the *absence* of the chain: memory sentences come back
verbatim with no `conversion` block, an unseen Odia sentence is declined with a reason and invents
no Santhali, the three formerly-chained sentences produce nothing, `/api/odia/convert` no longer
returns a Hindi conversion, and Hindi → Santhali is still checked in the same run.
Reports: `tests/odia_testing.md` / `.csv`, `tests/hindi_testing_sentences.md` / `.csv`.
