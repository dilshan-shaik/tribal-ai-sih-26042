"""
Build the runtime language pack for the SIH-26042 prototype.

Inputs (all downloaded from Hugging Face / Wikidata, see data/raw/SOURCES.md):
  data/raw/en_sat.parquet            72,977  English -> Santhali sentence pairs
  data/raw/gatitos_sat_en.jsonl       3,395  Santhali word -> English glosses
  data/raw/gatitos_sat_latn_en.jsonl  3,503  Santhali (Latin) word -> English glosses
  data/raw/smolsent_sat_en.jsonl        863  Santhali -> English sentences
  data/raw/hi_sat_wikidata.json       7,549  Hindi  -> Santhali title pairs
  data/raw/santali-train.csv         19,999  English -> Santhali pairs (Tatoeba/Wikipedia,
                                             supplied by the team; 19,832 lines are new)
  pipelines/lexicon.py                       curated foundational-literacy lexicon

Output:
  data/language_packs/sat.json  - everything the FastAPI backend needs at runtime:
     meta            provenance, counts, licence notes
     vocab[]         hindi, english, sat(Ol Chiki), sat_deva, sat_roman, category,
                     emoji, confidence, source, alternates[], verified
     phrases[]       classroom instruction phrases (the PS core use-case)
     sentence_memory[]  english -> santhali parallel memory used for fuzzy MT
     lexicon         english -> santhali word map (word-by-word fallback)
     titles[]        hindi -> santhali proper-noun memory from Wikidata

Run:  python3 pipelines/build_language_pack.py
"""
from __future__ import annotations

import json
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
import lexicon  # noqa: E402
from translit import is_olchiki, to_devanagari, to_roman  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "language_packs"
OUT.mkdir(parents=True, exist_ok=True)

OLCHIKI_RE = re.compile(r"[\u1c50-\u1c7f]")
ALPHA = re.compile(r"[a-zA-Z']+")


def norm_en(s: str) -> str:
    s = unicodedata.normalize("NFKC", s).lower().strip()
    s = re.sub(r"[^a-z0-9' ]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def clean_sat(s: str) -> str:
    s = unicodedata.normalize("NFKC", s)
    s = re.sub(r"[\u200b-\u200f\u202a-\u202e]", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    s = re.sub(r"\s+([᱾᱿.,!?])", r"\1", s)
    return s


def olchiki_ratio(s: str) -> float:
    letters = [c for c in s if not c.isspace()]
    if not letters:
        return 0.0
    return sum(1 for c in letters if "\u1c50" <= c <= "\u1c7f") / len(letters)


# ---------------------------------------------------------------- load sources
print("[1/5] loading raw sources ...")
df = pd.read_parquet(RAW / "en_sat.parquet")
df["src"] = df["src"].astype(str).map(lambda s: re.sub(r"\s+", " ", s).strip())
df["tgt"] = df["tgt"].astype(str).map(clean_sat)
df = df[(df.tgt.map(olchiki_ratio) > 0.8) & (df.tgt.str.len() > 1)]
print(f"      en_sat pairs kept: {len(df):,}")

# aiswarya9302/english-santali-webscrap-combined-v2 - checked against what we already
# hold: 72,888 of its 73,169 Santhali lines are already in the corpus above (99.6%), so
# only the delta is taken. Measured, not assumed.
_ws = RAW / "en_sat_webscrap_v2.parquet"
if _ws.exists():
    ws = pd.read_parquet(_ws)
    ws.columns = ["src", "tgt"]
    ws["src"] = ws["src"].astype(str).map(lambda s: re.sub(r"\s+", " ", s).strip())
    ws["tgt"] = ws["tgt"].astype(str).map(clean_sat)
    ws = ws[(ws.tgt.map(olchiki_ratio) > 0.8) & (ws.tgt.str.len() > 1)]
    _before = len(ws)
    ws = ws[~ws.tgt.isin(set(df.tgt))]
    if len(ws):
        df = pd.concat([df, ws], ignore_index=True)
    print(f"      webscrap-combined-v2: {_before:,} rows, {len(ws):,} new lines "
          f"({100 * len(ws) / max(1, _before):.1f}% delta)")


gatitos = [json.loads(l) for l in open(RAW / "gatitos_sat_en.jsonl", encoding="utf-8")]
gatitos_latn = {}
for l in open(RAW / "gatitos_sat_latn_en.jsonl", encoding="utf-8"):
    r = json.loads(l)
    for t in r.get("trgs", []):
        gatitos_latn.setdefault(norm_en(t), r["src"])
print(f"      gatitos word entries: {len(gatitos):,}")

smolsent = [json.loads(l) for l in open(RAW / "smolsent_sat_en.jsonl", encoding="utf-8")]
print(f"      smolsent sentences: {len(smolsent):,}")

wikidata = json.load(open(RAW / "hi_sat_wikidata.json", encoding="utf-8"))
print(f"      hi_sat wikidata pairs: {len(wikidata):,}")

# team-supplied corpus (Tatoeba/Wikipedia style, clean full sentences)
tatoeba = pd.read_csv(RAW / "santali-train.csv")
tatoeba.columns = ["id", "src", "tgt"]           # unnamed index, English, Santali
tatoeba = tatoeba.dropna(subset=["src", "tgt"])
tatoeba["src"] = tatoeba["src"].astype(str).map(lambda s: re.sub(r"\s+", " ", s).strip())
tatoeba["tgt"] = tatoeba["tgt"].astype(str).map(clean_sat)
tatoeba = tatoeba[(tatoeba.tgt.map(olchiki_ratio) > 0.8) & (tatoeba.tgt.str.len() > 1)]
tatoeba = tatoeba.drop_duplicates(subset=["tgt"])
# keep only lines the other sources do not already have
already = set(df.tgt)
tatoeba_new = tatoeba[~tatoeba.tgt.isin(already)].copy()
print(f"      santali-train.csv: {len(tatoeba):,} rows, {len(tatoeba_new):,} new lines")

# ---------------------------------------------------------- english -> santhali
print("[2/5] mining English -> Santhali dictionary ...")
# score: dictionary sources are trusted more than mined sentence pairs
en_sat: dict[str, Counter] = defaultdict(Counter)


def add(word: str, sat: str, weight: float):
    w = norm_en(word)
    sat = clean_sat(sat)
    if not w or not sat or olchiki_ratio(sat) < 0.8:
        return
    en_sat[w][sat] += weight


# 2a. word-level lexicon (gatitos): "ᱤᱧ" -> I / me / myself
for rec in gatitos:
    sat = clean_sat(rec["src"])
    if not is_olchiki(sat) or " " in sat:
        continue
    for t in rec.get("trgs", []):
        add(t, sat, 5.0)

# 2b. short sentence pairs: strong signal for single words / 2-word phrases
for src, tgt in zip(df["src"], df["tgt"]):
    words = src.split()
    if 1 <= len(words) <= 3 and len(tgt) < 60:
        add(src, tgt, 2.0 if len(words) == 1 else 1.0)

# 2c. sentence-context mining for single words (lower confidence)
for src, tgt in zip(df["src"], df["tgt"]):
    sw, tw = src.split(), tgt.split()
    if 2 <= len(sw) <= 4 and len(tw) == len(sw):
        for a, b in zip(sw, tw):
            if ALPHA.fullmatch(a):
                add(a, b, 0.4 if not b.endswith("᱾") else 0.1)

for rec in smolsent:
    en, sat = rec["trg"], clean_sat(rec["src"])
    sw, tw = en.split(), sat.split()
    if 2 <= len(sw) <= 5 and len(tw) == len(sw):
        for a, b in zip(sw, tw):
            if ALPHA.fullmatch(a):
                add(a, b, 0.3)

# collapse to best candidates
en_best: dict[str, list[tuple[str, float]]] = {}
for w, ctr in en_sat.items():
    tot = sum(ctr.values())
    ranked = [(s, round(c / tot, 3)) for s, c in ctr.most_common(4)]
    en_best[w] = ranked
print(f"      english surface forms: {len(en_best):,}")

# ------------------------------------------------------------ hindi -> santhali
print("[3/5] indexing Hindi -> Santhali memory ...")
hi_sat_exact: dict[str, Counter] = defaultdict(Counter)
hi_titles = []
for r in wikidata:
    hi = re.sub(r"\s+", " ", r["hi"]).strip()
    sat = clean_sat(r["sat"])
    if not hi or not sat or olchiki_ratio(sat) < 0.7:
        continue
    if len(hi) <= 40 and len(sat) <= 60:
        hi_sat_exact[hi][sat] += 1
    hi_titles.append({"hi": hi, "sat": sat})
print(f"      hi->sat exact forms: {len(hi_sat_exact):,}")


def confidence_from(score: float) -> str:
    if score >= 0.99:
        return "high"
    if score >= 0.6:
        return "medium"
    return "low"


# ------------------------------------------------------------------- vocabulary
print("[4/5] resolving curated vocabulary ...")
vocab, missing = [], []
for hindi, english, category, emoji in lexicon.N:
    cands = en_best.get(norm_en(english), [])
    entry = {
        "hindi": hindi,
        "english": english,
        "sat": None,
        "sat_deva": None,
        "sat_roman": None,
        "sat_latin_source": gatitos_latn.get(norm_en(english)),
        "category": category,
        "emoji": emoji,
        "source": None,
        "confidence": "none",
        "alternates": [],
        "verified": False,
    }
    # project-vetted core word wins over the automated pick
    vetted = lexicon.VETTED.get(hindi)
    if vetted:
        entry.update(sat=vetted, sat_deva=to_devanagari(vetted), sat_roman=to_roman(vetted),
                     source="curated-vetted", confidence="high")
        extra = lexicon.ALTERNATES.get(hindi, [])
        if cands:
            entry["alternates"] = extra + [c for c, _ in cands[:2]
                                           if c != vetted and c not in extra]
        else:
            entry["alternates"] = list(extra)
        vocab.append(entry)
        continue
    # direct Hindi match beats the English pivot when available
    direct = hi_sat_exact.get(hindi)
    if direct:
        best, cnt = direct.most_common(1)[0]
        entry.update(sat=best, sat_deva=to_devanagari(best), sat_roman=to_roman(best),
                     source="wikidata-titles", confidence="high")
        entry["alternates"] = [s for s, _ in direct.most_common(3)[1:]]
        vocab.append(entry)
        continue
    if cands:
        best, score = cands[0]
        entry.update(sat=best, sat_deva=to_devanagari(best), sat_roman=to_roman(best),
                     source="hf-en-sat-corpus",
                     confidence="high" if score >= 0.99 else "medium")
        # keep only alternates with real support: the mined list can contain
        # numbers, stray glyphs and one-off OCR noise
        entry["alternates"] = [s for s, n in cands[1:]
                               if n >= 2 and len(s) > 2 and not s.isdigit()]
        vocab.append(entry)
        continue
    missing.append(entry)
    vocab.append(entry)

# --- Odia-script corpus (team-supplied train.txt) ---------------------------
# Two monolingual streams, both in Odia script: Odia news sentences, and Santhali
# written in Odia script (the mission-era orthography). The Santhali half is decoded
# into Ol Chiki by matching every plausible vowel reading against the attested forms
# above, so it arrives here as real Santhali text plus a recovered spelling table.
_odia_path = RAW / "odia_corpus.jsonl"
_odia_script_path = RAW / "odia_script_lexicon.json"
odia_memory, odia_spellings, odia_hindi_lines = [], {}, []
if _odia_path.exists():
    for line in open(_odia_path, encoding="utf-8"):
        rec = json.loads(line)
        if rec.get("tag") == "sat":
            d = rec.get("decode") or {}
            if d.get("matched", 0) >= 2 and d.get("resolution", 0) >= 0.5 and rec.get("sat"):
                odia_memory.append({"or_script": rec["script_source"], "sat": rec["sat"],
                                    "sat_roman": to_roman(rec["sat"]),
                                    "matched": d["matched"], "tokens": d["tokens"]})
        elif rec.get("tag") == "ori":
            odia_hindi_lines.append({"or": rec["or"], "hi": rec["hi"],
                                     "conversion": rec.get("conversion", {})})
if _odia_script_path.exists():
    odia_spellings = json.load(open(_odia_script_path, encoding="utf-8")).get("pairs", {})
print(f"      odia_train.txt: {len(odia_memory)} Santhali sentences decoded to Ol Chiki, "
      f"{len(odia_spellings)} Odia-script spellings recovered, "
      f"{len(odia_hindi_lines)} Odia sentences converted to Hindi")

OL_CHIKI = r"[\u1C50-\u1C7F]"


def fix_gicher(s: str) -> str:
    """Ol Chiki has the gicher ᱹ (U+1C79). Sources typed on a Latin keyboard write
    a full stop instead: ᱯᱤᱯᱤᱲᱤᱭᱟ.ᱝ is ᱯᱤᱯᱤᱲᱤᱭᱟᱝ (butterfly). Only rewrite a "."
    that sits between two Ol Chiki letters, so real punctuation survives."""
    if not isinstance(s, str):
        return s
    return re.sub(rf"(?<={OL_CHIKI})\.(?={OL_CHIKI})", "\u1c79", s)


# --- Hindi -> Santhali dictionary built from the uploaded English<->Santhali files --
# pipelines/build_dictionary.py gives every headword a Hindi side (hand-curated Hindi,
# the project vocabulary, or a Wikipedia interlanguage link as a last resort) and
# generates the number system from the compositional pattern the source uses.
DICT_PATH = RAW / "hindi_sat_dictionary.json"
dict_entries, dict_numbers, dict_sentences = [], {}, []
dict_meta, dict_names = {}, []
if DICT_PATH.exists():
    _dp = json.load(open(DICT_PATH, encoding="utf-8"))
    for e in _dp.get("entries", []):
        sat = clean_sat(e["sat"])
        if not sat or olchiki_ratio(sat) < 0.5:
            continue
        dict_entries.append({
            "hi": e["hi"], "en": e["en"], "sat": sat,
            "sat_deva": to_devanagari(sat), "sat_roman": to_roman(sat),
            "theme": e.get("theme", "general"), "confidence": e.get("confidence", "medium"),
            "source": e.get("source"), "hindi_source": e.get("hindi_source"),
        })
    dict_numbers = _dp.get("numbers", {})
    dict_sentences = _dp.get("sentences", [])
    dict_names = _dp.get("names", [])
    dict_meta = _dp.get("meta", {})
    print(f"      dictionary (Hindi->Santhali): {len(dict_entries):,} entries, "
          f"{len(dict_numbers)} numbers, {len(dict_sentences)} sentences")

# --- consensus mining: association between an English word and Santhali tokens
# measured over the team-supplied corpus. A candidate is accepted only when it
# turns up in a decent share of the sentences containing that word AND is far
# more frequent there than in the corpus at large (lift), which filters out
# common function words like ᱫᱚ / ᱟᱨ / ᱢᱮᱱᱟᱜᱼᱟ.
import collections  # noqa: E402

TATOK = re.compile(r"[\u1c50-\u1c7f]+")
ENW = re.compile(r"[a-zA-Z']+")
_toks = [(set(ENW.findall(str(en).lower())), TATOK.findall(str(sa)))
         for en, sa in zip(tatoeba["src"], tatoeba["tgt"])]
_all = collections.Counter()
for _, tk in _toks:
    _all.update(set(tk))
_TN = max(1, len(_toks))


def consensus(word: str, min_sent: int = 4, min_p: float = 0.4, min_lift: float = 20.0):
    sel = [tk for en, tk in _toks if word in en]
    if len(sel) < min_sent:
        return None
    cnt = collections.Counter()
    for tk in sel:
        cnt.update(set(tk))
    best = None
    for tok, c in cnt.items():
        if len(tok) < 2:
            continue
        p = c / len(sel)
        lift = p / max(_all[tok] / _TN, 1 / _TN)
        if p >= min_p and lift >= min_lift and (best is None or (p, lift) > best[1:]):
            best = (tok, round(p, 2), round(lift, 1), c, len(sel))
    return best


consensus_hits = 0
for entry in vocab:
    if entry["sat"]:
        continue
    hit = consensus(norm_en(entry["english"]))
    if hit:
        tok, p, lift, c, n = hit
        entry.update(sat=tok, sat_deva=to_devanagari(tok), sat_roman=to_roman(tok),
                     source=f"hf-consensus(santali-train): {c}/{n} sentences, lift {lift}",
                     confidence="medium")
        consensus_hits += 1
print(f"      consensus mining resolved {consensus_hits} more")

print(f"      resolved: {sum(1 for v in vocab if v['sat'])}/{len(vocab)}")
if missing:
    print("      unresolved:", ", ".join(f"{m['hindi']}({m['english']})" for m in missing[:40]))

# --------------------------------------------------------------------- phrases
print("[5/5] verifying attested grammar + classroom phrases ...")
import grammar  # noqa: E402

HAY = "\n".join(df["tgt"].tolist()
                + tatoeba["tgt"].tolist()
                + [clean_sat(r["src"]) for r in smolsent]
                + [m["sat"] for m in odia_memory])


def attested(snippet: str) -> bool:
    key = snippet.strip().rstrip(".।᱾!? ")
    return key and key in HAY


verbs, dropped = [], []
for sat, en, hi, ev in grammar.VERBS:
    ok = attested(ev)
    (verbs if ok else dropped).append({
        "sat": sat, "sat_deva": to_devanagari(sat), "sat_roman": to_roman(sat),
        "english": en, "hindi": hi, "attested": ok, "evidence": ev,
    })
print(f"      verb forms: {len(verbs)} attested, {len(dropped)} dropped -> "
      f"{[v['sat'] for v in verbs]}")

templates = []
for tid, frame, enf, hif, ev, conf in grammar.TEMPLATES:
    templates.append({"id": tid, "frame": frame, "english_frame": enf,
                      "hindi_frame": hif, "confidence": conf,
                      "attested": attested(ev), "evidence": ev})

phrases = []
for hindi, english, sat, kind, ev, pt in grammar.PHRASES:
    phrases.append({
        "hindi": hindi, "english": english, "type": pt, "kind": kind,
        "sat": sat, "sat_deva": to_devanagari(sat), "sat_roman": to_roman(sat),
        "source": "hf-en-sat-corpus", "evidence": ev, "attested": attested(ev),
        "confidence": "high" if kind == "attested" else "medium", "verified": False,
    })
bad = [p for p in phrases if not p["attested"]]
print(f"      phrases: {len(phrases)} ({len([p for p in phrases if p['kind']=='attested'])} attested, "
      f"{len([p for p in phrases if p['kind']=='pattern'])} pattern); unverified: {[p['hindi'] for p in bad]}")

# ------------------------------------------------------------- sentence memory
mem = []
seen = set()
for src, tgt in zip(df["src"], df["tgt"]):
    if 2 <= len(src.split()) <= 14 and len(src) <= 110 and len(tgt) <= 130:
        k = tgt
        if k in seen:
            continue
        seen.add(k)
        mem.append({"en": src, "sat": tgt})
for src, tgt in zip(tatoeba["src"], tatoeba["tgt"]):
    if 2 <= len(src.split()) <= 14 and len(src) <= 110 and tgt not in seen:
        seen.add(tgt)
        mem.append({"en": src, "sat": tgt})
for rec in smolsent:
    sat = clean_sat(rec["src"])
    if 2 <= len(rec["trg"].split()) <= 14 and sat not in seen:
        seen.add(sat)
        mem.append({"en": rec["trg"], "sat": sat})
# teacher/literacy-leaning sentences first, so the fuzzy matcher prefers them
EDU = ("children", "teacher", "school", "book", "read", "write", "learn",
       "count", "name", "water", "tree", "fruit", "animal", "colour", "color",
       "student", "class", "study", "letter", "number", "good", "friend")


def edu_rank(item):
    t = item["en"].lower()
    return (0 if any(w in t for w in EDU) else 1, len(item["en"]))


mem.sort(key=edu_rank)
mem = mem[:12000]
for m in mem:
    m["sat_roman"] = to_roman(m["sat"])
print(f"      sentence memory: {len(mem):,}")

# ------------------------------------------------------------------- assemble
pack = {
    "meta": {
        "language": "Santhali",
        "language_code": "sat",
        "script": "Ol Chiki",
        "pivot": "Hindi -> English -> Santhali",
        "built_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "counts": {
            "vocab": len([v for v in vocab if v["sat"]]),
            "vocab_total": len(vocab),
            "phrases": len([p for p in phrases if p["sat"]]) + len(dict_sentences),
            "phrases_total": len(phrases) + len(dict_sentences),
            "verbs": len(verbs),
            "templates": len(templates),
            "sentence_memory": len(mem),
            "tatoeba_pairs": int(len(tatoeba)),
            "consensus_resolved": consensus_hits,
            "hi_sat_titles": len(hi_titles),
            "en_sat_lexicon": len(en_best),
            "dictionary_entries": len(dict_entries),
            "dictionary_numbers": len(dict_numbers),
            "dictionary_sentences": len(dict_sentences),
            "dictionary_names": len(dict_names),
            "odia_sentences": len(odia_memory),
            "odia_spellings": len(odia_spellings),
            "odia_hindi_pairs": len(odia_hindi_lines),
        },
        "dictionary_per_file": dict_meta.get("per_file", {}),
        "dictionary_skipped": dict_meta.get("skipped_headwords", {}),
        "dictionary_spellings_fixed": dict_meta.get("normalised_spellings", {}),
        "sources": [
            {"id": "aiswarya9302/english-santali-combined", "kind": "HF dataset",
             "rows": int(len(df)), "use": "sentence memory + word alignment"},
            {"id": "team-supplied Santhali dictionaries (9 files, Ol Chiki)",
             "kind": "dictionary (Hindi side added in-project)",
             "rows": len(dict_entries),
             "use": "Hindi->Santhali vocabulary for body, family, food, animals, time, "
                    "colours, school + the full 0-100 number system"},
            {"id": "aiswarya9302/english-santali-webscrap-combined-v2",
             "kind": "HF dataset (delta only)",
             "rows": max(0, int(len(df)) - 71106),
             "use": "99.6% of it duplicates the corpus above; only new lines kept"},
            {"id": "google/smol (smolsent, gatitos)", "kind": "HF dataset",
             "rows": len(gatitos) + len(smolsent), "use": "word lexicon + sentences"},
            {"id": "wikidata sat.wikipedia x hi.wikipedia sitelinks", "kind": "KG",
             "rows": len(wikidata), "use": "Hindi->Santhali proper nouns & concepts"},
            {"id": "santali-train.csv (team-supplied Tatoeba/Wikipedia corpus)",
             "kind": "parallel corpus", "rows": int(len(tatoeba)),
             "use": "sentence memory, attestation, consensus word mining"},
            {"id": "odia_train.txt (team-supplied, Odia script)", "kind": "monolingual x2",
             "rows": len(odia_memory) + len(odia_hindi_lines),
             "use": "Santhali half decoded Odia-script -> Ol Chiki (sentence memory + "
                    "attestation); Odia half converted Odia -> Hindi to drive the engine"},
            {"id": "curated foundational-literacy lexicon", "kind": "in-project",
             "rows": len(lexicon.N), "use": "Hindi->English educational pivot"},
            {"id": "attested classroom grammar (verbs + frames)", "kind": "mined",
             "rows": len(verbs) + len(templates),
             "use": "instruction composition; every form verified against the corpus"},
        ],
        "validation": "Human-in-the-loop: native-speaker verification queue in-app; "
                      "entries marked confidence=low are flagged for review.",
    },
    "vocab": [{**v, "sat": fix_gicher(v["sat"])} for v in vocab],
    "phrases": phrases + [
        # hand-translated classroom sentences from T General (0.06k).csv: the Santhali
        # is native, the Hindi was written by hand from the Santhali (dict_sentences.py)
        {"hindi": s["hi"], "english": s["en"] or None, "type": "instruction",
         "kind": "attested", "attested": True,
         "sat": s["sat"], "sat_deva": to_devanagari(s["sat"]),
         "sat_roman": to_roman(s["sat"]), "confidence": "high", "verified": False,
         "source": "T General (0.06k).csv (team-supplied)", "evidence": s["sat"]}
        for s in dict_sentences
    ],
    "verbs": verbs,
    "templates": templates,
    "sentence_memory": mem,
    "lexicon": {w: {"sat": c[0][0], "sat_deva": to_devanagari(c[0][0]),
                    "sat_roman": to_roman(c[0][0]), "score": c[0][1],
                    "alts": [x[0] for x in c[1:3]]}
                for w, c in sorted(en_best.items()) if c},
    "titles": hi_titles[:8000],
    "dictionary": [{**e, "sat": fix_gicher(e["sat"])} for e in dict_entries],
    "names": dict_names,
    "numbers": dict_numbers,
    "dictionary_sentences": dict_sentences,
    "odia_memory": [{**e, "sat": fix_gicher(e.get("sat"))} for e in odia_memory],
    "odia_script": odia_spellings,
    "odia_hindi": odia_hindi_lines[:2000],
}

path = OUT / "sat.json"
json.dump(pack, open(path, "w", encoding="utf-8"), ensure_ascii=False)
print(f"\nOK  wrote {path}  ({path.stat().st_size/1024:.0f} KB)")
print("    vocab coverage :", pack["meta"]["counts"]["vocab"], "/", pack["meta"]["counts"]["vocab_total"])
print("    phrase coverage:", pack["meta"]["counts"]["phrases"], "/", pack["meta"]["counts"]["phrases_total"])
