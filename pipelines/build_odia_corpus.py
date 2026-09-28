#!/usr/bin/env python3
"""
Turn the Odia-script training file into data the Hindi -> Santhali app can use.

`data/raw/odia_train.txt` is 782 lines, each  "<text>\t<tag>"  with tag = ori | sat.

Important finding (see report it prints): the file is NOT a line-aligned translation
memory. The Odia half is full news sentences (mean 78 characters, none under 20), the
Santhali half is mostly fragments (mean 20 characters, 197 of 384 under 20), and
adjacent cross-language lines share a content word only 1% of the time with zero of the
19 digit-bearing pairs agreeing. So it is two monolingual streams that were concatenated
with language tags - and it is processed as such:

  * Santhali stream  -> decoded from Odia script into Ol Chiki (the script Santhali is
    written in today), matched against the 22k attested Santhali forms we already hold.
    Output: Santhali sentences + an Odia-script -> Ol Chiki spelling dictionary.
  * Odia stream      -> converted to Hindi with a curated Odia->Hindi lexicon plus an
    Odia->Devanagari transliteration fallback (pipelines/odia.py).
    Output: Hindi sentences that the normal Hindi->Santhali engine can translate,
    and a frequency report of Odia words still needing curation.

Run:  python3 pipelines/build_odia_corpus.py
"""

import collections
import json
import os
import re
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pipelines.odia import (ODIA_HINDI, ODIA_RE, decode_odia_word, is_odia,
                            odia_to_hindi)

SRC = "data/raw/odia_train.txt"
OUT_CORPUS = "data/raw/odia_corpus.jsonl"
OUT_SCRIPT = "data/raw/odia_script_lexicon.json"
PACK = "data/language_packs/sat.json"


def known_santhali_forms():
    """Every Ol Chiki form we already trust: vocab, phrases, and 12k sentence memory."""
    if not os.path.exists(PACK):
        return set()
    pack = json.load(open(PACK, encoding="utf-8"))
    forms = set()
    for v in pack["vocab"]:
        if v.get("sat"):
            forms.add(v["sat"])
    for p in pack["phrases"]:
        for t in re.findall(r"[\u1C50-\u1C7F]+", p.get("sat") or ""):
            forms.add(t)
    for s in pack.get("sentence_memory", []):
        for t in re.findall(r"[\u1C50-\u1C7F]+", s["sat"]):
            forms.add(t)
    # NOTE: deliberately NOT using pack["odia_memory"] - that section is this script's
    # own previous output, and matching against it would let the decoder confirm itself.
    # Only independent sources count: HF corpora, Wikidata, curated lexicon.
    for s in (pack.get("lexicon") or {}).values():
        for t in re.findall(r"[\u1C50-\u1C7F]+", str(s.get("sat", ""))):
            forms.add(t)
    return {f for f in forms if len(f) > 1}


def read_lines():
    rows = []
    for raw in open(SRC, encoding="utf-8"):
        if not raw.strip():
            continue
        parts = raw.rstrip("\n").rsplit("\t", 1)
        if len(parts) != 2:
            continue
        text, tag = parts[0].strip(), parts[1].strip()
        if text and tag in ("ori", "sat"):
            rows.append((text, tag))
    return rows


def decode_santhali(text, known):
    """Odia-script Santhali -> (ol chiki, stats)."""
    out, matched, total = [], 0, 0
    for tok in re.findall(r"[\u0B00-\u0B7F]+", text):
        ol, how = decode_odia_word(tok, known)
        out.append(ol)
        total += 1
        matched += how == "known"
    sat = " ".join(w for w in out if w)
    return sat, {"tokens": total, "matched": matched,
                 "resolution": round(matched / total, 3) if total else 0.0}


def main():
    rows = read_lines()
    ori = [t for t, g in rows if g == "ori"]
    sat = [t for t, g in rows if g == "sat"]
    known = known_santhali_forms()

    print(f"source: {SRC}")
    print(f"  {len(rows)} lines  ->  {len(ori)} Odia, {len(sat)} Santhali (all in Odia script)")
    print(f"  attested Santhali forms available for matching: {len(known)}")

    # ---------------------------------------------------------------- sanity of pairing
    cross = [(a, b) for a, b in zip(rows, rows[1:]) if a[1] != b[1]]
    shared = sum(1 for a, b in cross
                 if set(re.findall(r"[\u0B00-\u0B7F]+", a[0])) & set(re.findall(r"[\u0B00-\u0B7F]+", b[0])))
    digits = [(a, b) for a, b in cross if re.search(r"\d", a[0] + b[0])]
    agree = sum(1 for a, b in digits if set(re.findall(r"\d+", a[0])) & set(re.findall(r"\d+", b[0])))
    print(f"\n  alignment check: {len(cross)} adjacent cross-language pairs")
    print(f"    share a token: {shared} ({100 * shared / max(1, len(cross)):.1f}%)"
          f"   digit-agreeing: {agree}/{len(digits)}")
    print(f"    length medians: Odia {statistics.median(len(t) for t in ori):.0f} chars, "
          f"Santhali {statistics.median(len(t) for t in sat):.0f} chars"
          f"   (under 20 chars: {sum(1 for t in ori if len(t) < 20)} vs "
          f"{sum(1 for t in sat if len(t) < 20)})")
    print("    => not a translation memory; both halves are used as monolingual data")

    # ------------------------------------------------------ Santhali -> Ol Chiki decode
    spelling, sat_records = {}, []
    res_all, new_sentences = [], 0
    for text in sat:
        ol, st = decode_santhali(text, known)
        res_all.append(st["resolution"])
        if st["resolution"] >= 0.5 and st["matched"] >= 2:
            new_sentences += 1
        sat_records.append({"tag": "sat", "script_source": text, "sat": ol,
                            "sat_roman": None, "decode": st})
        for tok in re.findall(r"[\u0B00-\u0B7F]+", text):
            cand, how = decode_odia_word(tok, known)
            if how == "known":
                spelling.setdefault(tok, {"olchiki": cand, "n": 0, "matched": True})
                spelling[tok]["n"] += 1
    usable = [r for r in sat_records if r["decode"]["resolution"] >= 0.5 and r["decode"]["matched"] >= 2]

    # ------------------------------------------------------------- Odia -> Hindi
    hi_records, unmapped = [], collections.Counter()
    lex_hits = tr_hits = 0
    for text in ori:
        hi, st = odia_to_hindi(text)
        lex_hits += st["lexicon"]
        tr_hits += st["translit"]
        hi_records.append({"tag": "ori", "or": text, "hi": hi, "conversion": st})
        for tok in re.findall(r"[\u0B00-\u0B7F]+", text):
            if tok not in ODIA_HINDI:
                unmapped[tok] += 1

    with open(OUT_CORPUS, "w", encoding="utf-8") as f:
        for r in sat_records + hi_records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    with open(OUT_SCRIPT, "w", encoding="utf-8") as f:
        json.dump({"note": "Odia-script spelling -> Ol Chiki, recovered by matching every "
                           "plausible vowel reading against attested Santhali forms",
                   "pairs": spelling}, f, ensure_ascii=False, indent=1)

    tot = max(1, lex_hits + tr_hits)
    print(f"\n  Santhali half -> Ol Chiki")
    print(f"    token resolution: {100 * sum(res_all) / max(1, len(res_all)):.1f}% average, "
          f"{sum(1 for r in res_all if r >= 0.5)}/{len(sat)} lines at 50%+")
    print(f"    sentences usable as Santhali text: {len(usable)}")
    print(f"    Odia-script spellings recovered : {len(spelling)}")
    print(f"\n  Odia half -> Hindi")
    print(f"    words from the curated lexicon: {lex_hits} ({100 * lex_hits / tot:.1f}%)")
    print(f"    words via transliteration     : {tr_hits} ({100 * tr_hits / tot:.1f}%)")
    print(f"    distinct Odia words still unmapped: {len(unmapped)}")
    print(f"\n  wrote {OUT_CORPUS} ({len(sat_records) + len(hi_records)} records)")
    print(f"  wrote {OUT_SCRIPT} ({len(spelling)} spellings)")

    print("\n  sample: Santhali in Odia script -> Ol Chiki")
    for r in sat_records[:6]:
        if r["decode"]["matched"]:
            print(f"    {r['script_source'][:44]:46} -> {r['sat'][:40]}"
                  f"  ({r['decode']['matched']}/{r['decode']['tokens']})")
    print("\n  sample: Odia -> Hindi")
    for r in hi_records[:4]:
        print(f"    {r['or'][:52]:54} -> {r['hi'][:52]}")
    print("\n  top Odia words still needing curation (add to pipelines/odia.py):")
    print("   ", ", ".join(f"{w}({n})" for w, n in unmapped.most_common(12)))


if __name__ == "__main__":
    main()
