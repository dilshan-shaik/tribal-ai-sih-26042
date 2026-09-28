# `dataset-mundari-tts-full.tgz` — what I could check, and what I need from you

You gave: `46c8bfceb5cf25decc8523479378793537f2bad7` + `dataset-mundari-tts-full.tgz`.
**The file is not in the workspace**, so I traced where it lives and what it takes to get it.

## What I checked (and the exact results)

| Check | Result |
|---|---|
| Search the hash itself | not indexed anywhere public — it is a content hash, not an address |
| `storage.googleapis.com/ulca-datasets/<hash>/…tgz` | **404** |
| `ulca-datasets.s3.amazonaws.com/…` (and `.s3.ap-south-1`) | **403 AccessDenied** — the bucket is private, listing denied |
| `bhashini.gov.in/ulca/datasets/<hash>/…tgz` | **200 — but `text/html`**, the SPA catch-all page, not a file |
| `meity-origin.ulcacontrib.org/ulca/datasets/<hash>/…tgz` | same: SPA `index.html` |
| ULCA dataset API `/ulca/apis/v0/dataset/corpus/search` | **400 `InvalidAccessException: Couldn't find public key in the request`** |
| ULCA app bundle (`ulca/static/js/main.11c647a3.chunk.js`) | confirmed the real endpoints exist — dataset search, upload, my-contribution — all behind the platform's auth |
| Zenodo / DataCite / OSF for Mundari TTS releases | no such archive published |

**Conclusion: it is a login-gated Bhashini/ULCA artifact.** I can't fetch it without your ULCA
session, and I won't try to get around an authentication wall. What I *can* do is be ready.

## Ready and tested: the ingest + verify harness

`pipelines/ingest_mundari_tts.py` — I ran it end to end against a synthetic archive built in
the same ULCA shape (audio folder + `data.csv` with `audioFileName, text, gender`), and it
worked: hash → safety → structure → pairing → duration → scripts → overlap.

When you hand me the real file it will:

1. **verify identity** — sha1 / md5 / sha256, compared against `46c8bfce…`; if the bytes don't
   match that hash, it refuses to install and says so.
2. **safety-check the tar** — absolute paths, `..` traversals and links are refused before
   anything is extracted. It never extracts outside `data/mundari_tts/`.
3. **find the transcript table** whatever it is named (`data.csv`, `data.json`, `metadata.csv`,
   `*.tsv` …) and print its columns.
4. **pair every transcript with a real clip** — and print the unmatched ones on both sides
   rather than quietly dropping them.
5. **inventory** — clips, total duration in hours, sample rates, speaker split, empty rows,
   duplicate transcripts.
6. **check the language per row** — Devanagari Mundari / Warang Citi / roman / other. Rows
   that are not Mundari are reported, never used.
7. **measure the overlap** — how many transcripts are already in the 6,020-pair Mundari memory
   and how many words the Hindi→English bridge would gain. Added value as a number, not a claim.

With `--install` it additionally writes `data/mundari_tts/index.json` (transcript → clip) and
extracts only the paired clips.

## What that unlocks — and it's the real prize

Mundari currently has **no real voice**: `मुंडारी` audio is the Hindi voice reading Devanagari,
labelled *approximate*. A TTS dataset fixes that:

```
/api/tts?lang=unr  +   a sentence that is in the dataset
    -> x-voice-engine: "Mundari (recorded, TTS dataset)"     approx: false
/api/tts?lang=unr  +   anything else
    -> x-voice-engine: "hi (gTTS) - reads the Devanagari Mundari text"   approx: true
```

**Exact-match only.** A recording of the wrong sentence is worse than an approximate voice, so
the hook (`tts.py: mundari_clip`) never fuzzies. Both paths are labelled in the response, and the
UI shows it. Suites still green after wiring: **multilang 46/46**, **Hindi 178 | PASS 154 | review
24 | FAIL 0**.

## What I need from you — pick one

1. **Upload the `.tgz`** (drag it into this chat, or drop it in `uploads/`). Best option: I verify
   it against your hash, inventory it, and install the audio index in one turn.
2. **Give me the direct download link** if it opens without a login (some ULCA links are public
   once minted with a token — a pre-signed URL would work).
3. **Tell me it's a different dataset** than I assume (e.g. text-only, or from a hackathon pack
   you have locally) and I'll adjust the harness to that shape.

One honest caveat about scale: MUNTTS reports 27.5 h / 26,868 recordings for Mundari, and a
"full" ULCA TTS package is typically hundreds of MB to a few GB, so check that it lands in the
workspace — if it's very large I'll install a bounded subset (a few thousand clips) and say
exactly which subset.
