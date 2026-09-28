"""
Build Mundari (unr) and Ho (hoc) language packs for the MTB-MLE platform.

Sources (all fetched from public datasets, licences recorded in meta.sources):

  Mundari   google/smol  smoldoc/en_unr-Deva.jsonl   CC-BY-4.0      (sentence-aligned)
  Ho        google/smol  smoldoc/en_hoc-Wara.jsonl   CC-BY-4.0      (sentence-aligned, Warang Citi)
  Ho        sicsoc/eng-hoc-Tatoeba-Wiki              Apache-2.0     (Tatoeba + Wikipedia, roman)
  both      en.wiktionary.org  Category:<X> lemmas  CC-BY-SA       (curated glosses)

The packs use the same schema as sat.json so one engine serves every language.
The English pivot is deliberate - it is how the project was designed (see
pipelines/lexicon.py) and it is the only honest route here: there is no published
Hindi<->Mundari or Hindi<->Ho parallel corpus. Hindi input therefore reaches these
languages as *word combinations* through the pivot, never as generated sentences.

Run:  python3 pipelines/build_multi_lang_packs.py
"""
from __future__ import annotations

import bz2
import csv
import json
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "pipelines"))
from lexicon import N, INSTRUCTION_PHRASES  # noqa: E402

SRC = Path("/tmp/lang")
RAW = ROOT / "data" / "raw"          # staged sources (git-friendly); /tmp is only a cache
OUT = ROOT / "data" / "language_packs"

EN_STOP = set("""the a an is are was were be been being am do does did of to in on at by for with
from as and or but if then than that this these those it its he she they them his her their we our
you your i my me will would shall should may might must can could have has had not no so such there
here when while during however therefore also more most much many some any all each every other into
over under about after before between based using used via per etc e g ie eg one two three also part
known called name names people person state states world country countries city town area years year
first second new old great small large long high low same different such other her his their them
which who whom whose what when where why how""".split())

LETTER_RE = re.compile(r"[^\W\d_]", re.UNICODE)


def norm_key(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip().lower())


def script_of(text: str, lo: int, hi: int) -> int:
    return sum(1 for c in text if lo <= ord(c) <= hi)


def script_label(text: str, deva_range=(0x0900, 0x097F), wara_range=(0x118A0, 0x118FF)) -> str:
    """Which script a sentence is actually written in (Ho arrives in two)."""
    if script_of(text, *wara_range):
        return "Warang Citi"
    if script_of(text, *deva_range):
        return "Devanagari"
    if script_of(text, 0x1C50, 0x1C7F):
        return "Ol Chiki"
    return "roman"


def has_script(text: str, lo: int, hi: int, frac: float = 0.5) -> bool:
    letters = [c for c in text if LETTER_RE.match(c) or script_of(c, lo, hi)]
    if not letters:
        return False
    return script_of(text, lo, hi) / len(letters) >= frac


def tokens_en(text: str) -> list[str]:
    words = re.findall(r"[a-zA-Z']{3,}", text.lower())
    return [w for w in words if w not in EN_STOP]


def tokens_tgt(text: str) -> list[str]:
    # target tokens: Devanagari / Warang Citi / romanised words
    return [w for w in re.split(r"[^\w\u0900-\u097F\u118A0-\u118FF\u1C50-\u1C7F]+", text)
            if len(w) > 2]


def load_smol(path: Path) -> list[tuple[str, str]]:
    pairs = []
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        d = json.loads(line)
        srcs, trgs = d.get("srcs") or [], d.get("trgs") or []
        for en, tgt in zip(srcs, trgs):
            en, tgt = (en or "").strip(), (tgt or "").strip()
            if 3 <= len(en) <= 300 and 2 <= len(tgt) <= 300:
                pairs.append((en, tgt))
    return pairs


def load_sicsoc() -> list[tuple[str, str]]:
    out = []
    for name in ("tatoeba-train-data_eng-hoc.jsonl", "tatoeba-validation-data_eng-hoc.jsonl",
                 "tatoeba-test-data_eng-hoc.jsonl"):
        p = (RAW / "sicsoc" / name) if (RAW / "sicsoc" / name).exists() else (SRC / name.replace("tatoeba-","").replace(".jsonl",".json"))
        if not p.exists():
            continue
        for line in open(p, encoding="utf-8"):
            line = line.strip()
            if not line:
                continue
            t = json.loads(line).get("translation", {})
            en, hoc = (t.get("eng") or "").strip(), (t.get("hoc") or "").strip()
            if en and hoc:
                out.append((en, hoc))
    return out


def load_panlex(code: str) -> dict[str, list[dict]]:
    """PanLex (CC0) expressions for this language, joined to English glosses.

    PanLex records the source dictionary's own spelling, which here is phonetic
    (IPA-ish: "ʧaːr", "paːɲʧ"). That is kept verbatim and flagged `phonetic`, because
    silently respelling someone else's dictionary entry is how errors enter a lexicon.
    """
    tsvin = ROOT / "data" / "raw" / "panlex" / f"panlex_{code}.tsv"
    glossin = ROOT / "data" / "raw" / "panlex" / "panlex_gloss.json"
    if not tsvin.exists() or not glossin.exists():
        print(f"    panlex {code}: not staged in data/raw/panlex/")
        return {}
    gloss = json.load(open(glossin, encoding="utf-8"))
    strip = dict.fromkeys(map(ord, "ˈˌ˺ˑʔʕʰʲˀˤ꞊=[]()\u27e8\u27e9/"), None)
    by_en: dict[str, list[dict]] = {}
    for row in csv.DictReader(open(tsvin, encoding="utf-8"), delimiter="\t"):
        gs = [g.strip().lower() for g in gloss.get(row["meaning"], [])]
        gs = [g for g in gs if re.fullmatch(r"[a-z][a-z' -]{1,28}", g)]
        if not gs:
            continue
        raw = row["txt"].strip()
        form = re.sub(r"\s+", " ", raw.translate(strip)).strip(" .-–")
        if not form or len(form) > 32:
            continue
        if not re.search(r"[A-Za-z\u0900-\u097F\u118A0-\u118FF]", form):
            continue
        for g in gs[:2]:
            by_en.setdefault(g, [])
            if len(by_en[g]) < 4 and all(form != c["form"] for c in by_en[g]):
                by_en[g].append({"form": form, "raw": raw, "langvar": row["langvar_uid"],
                                 "phonetic": bool(re.search(r"[\u02b0-\u02ff\u0250-\u02af\u02c8]", raw))})
    return by_en


def load_cognates(code: str) -> list[dict]:
    """Munda cognate set (Zenodo 10.5281/zenodo.3380874, CC0): comparative forms with
    the published source abbreviation for each language (BMED, HOGV, DHED ...)."""
    src = ROOT / "data" / "raw" / "zenodo" / "munda_cognates.csv"
    if not src.exists():
        return []
    col, scaff = ("mu_form", "mu_source") if code == "unr" else ("ho_form", "ho_source")
    out = []
    for row in csv.DictReader(open(src, encoding="utf-8")):
        form = (row.get(col) or "").strip()
        gloss = (row.get("gloss") or "").strip()
        if not form or not gloss or form in (",", "—") or form.startswith("("):
            continue
        if not re.search(r"[A-Za-z\u0900-\u097F]", form):
            continue
        out.append({"en": gloss, "form": form, "source_ref": (row.get(scaff) or "").strip(),
                    "proto_munda": (row.get("pmunda") or "").strip()})
    return out


def load_aug(code: str) -> list[dict]:
    """sicsoc augmented Ho (Apache-2.0): machine-augmented English-Ho pairs.
    Synthetic by construction, so they are a separate layer and never 'attested'."""
    if code != "hoc":
        return []
    try:
        import pyarrow.parquet as pq
    except Exception:
        print("    aug: pyarrow not installed - skipping the augmented layer")
        return []
    import ast
    seen, out = set(), []
    for f in sorted((ROOT / "data" / "raw" / "sicsoc").glob("aug*_*.parquet")):
        for r in pq.read_table(f).to_pylist():
            v = r.get("translation")
            if isinstance(v, str):
                try:
                    v = ast.literal_eval(v)
                except Exception:
                    continue
            if not isinstance(v, dict):
                continue
            en = (v.get("eng") or v.get("eng_Latn") or "").strip()
            tgt = (v.get("hoc") or v.get("hoc_Latn") or "").strip()
            if not en or not tgt or (en, tgt) in seen:
                continue
            seen.add((en, tgt))
            out.append({"en": en, "tgt": tgt, "source": "sicsoc-aug", "synthetic": True})
    return out


def wiktionary_lemmas(category: str) -> list[tuple[str, str]]:
    """Return (headword, english gloss) from an English Wiktionary category."""
    import urllib.parse
    import urllib.request

    out: list[tuple[str, str]] = []
    url = ("https://en.wiktionary.org/w/api.php?action=query&generator=categorymembers"
           f"&gcmtitle=Category:{urllib.parse.quote(category)}&gcmlimit=500&prop=extracts"
           "&explaintext=1&exchars=300&format=json")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "MTB-MLE-Research/1.0"})
        with urllib.request.urlopen(req, timeout=45) as r:
            d = json.load(r)
    except Exception as exc:  # network is optional - the pack still builds without it
        print(f"    wiktionary {category}: {exc}")
        return out
    for page in (d.get("query", {}).get("pages", {}) or {}).values():
        title = page.get("title") or ""
        text = (page.get("extract") or "")
        m = re.search(r"\bEnglish\b(.{0,400}?)(?:\n\n|$)", text, re.S)
        gloss = ""
        if m:
            m2 = re.search(r"^(.{3,80}?)(?:\.|$)", m.group(1).strip(), re.M)
            gloss = (m2.group(1).strip() if m2 else "").strip()
        if title and gloss:
            out.append((title, gloss))
    return out


def mine_lexicon(pairs: list[tuple[str, str]], min_count: int = 2, min_dice: float = 0.50,
                 per_en: int = 2) -> dict[str, dict]:
    """Mutual-best English<->target word alignment from sentence pairs."""
    co: Counter = Counter()
    en_c: Counter = Counter()
    tgt_c: Counter = Counter()
    for en, tgt in pairs:
        es = sorted(set(tokens_en(en)))
        ts = sorted(set(tokens_tgt(tgt)))
        for e in es:
            en_c[e] += 1
            for t in ts:
                co[(e, t)] += 1
        for t in ts:
            tgt_c[t] += 1
    scored = []
    for (e, t), c in co.items():
        if c < min_count:
            continue
        dice = 2 * c / (en_c[e] + tgt_c[t])
        if dice < min_dice:
            continue
        scored.append((dice, c, e, t))
    scored.sort(reverse=True)
    best_en: dict[str, list] = defaultdict(list)
    best_tgt: dict[str, tuple] = {}
    for dice, c, e, t in scored:
        best_en[e].append((dice, c, t))
        if t not in best_tgt or dice > best_tgt[t][0]:
            best_tgt[t] = (dice, c, e)
    out: dict[str, dict] = {}
    for e, cands in best_en.items():
        kept = []
        for dice, c, t in cands[:per_en * 2]:
            if best_tgt.get(t, (0, 0, ""))[2] != e:
                continue                      # not mutual-best -> drop
            kept.append({"tgt": t, "score": round(dice, 3), "count": c})
            if len(kept) >= per_en:
                break
        if kept:
            out[e] = {"alts": kept, "best": kept[0]["tgt"], "score": kept[0]["score"]}
    return out


def build(lang: dict, smol_pairs, extra_pairs, wiki_cat, hi_en: dict) -> dict:
    code, name = lang["code"], lang["name"]
    lo, hi = lang["range"]
    print(f"\n=== {name} ({code}) ===")
    print(f"  smol pairs          {len(smol_pairs)}")

    pairs: list[tuple[str, str, str]] = []
    for en, tgt in smol_pairs:
        if not has_script(tgt, lo, hi):
            continue
        if en.strip().lower().strip(".") == tgt.strip().lower().strip("."):
            continue
        pairs.append((en, tgt, "smol-smoldoc"))
    print(f"  after script filter {len(pairs)}")

    for en, tgt in extra_pairs:
        pairs.append((en, tgt, "sicsoc-eng-hoc-tatoeba"))
    print(f"  + extra pairs       {len(pairs)}")

    # dedupe on the target side (same translation twice adds nothing)
    seen, memory = set(), []
    for en, tgt, src in pairs:
        k = tgt.strip()
        if k in seen:
            continue
        seen.add(k)
        memory.append({"en": en.strip(), "tgt": tgt.strip(), "source": src,
                       "script": script_label(tgt)})
    print(f"  sentence memory     {len(memory)}")

    lex = mine_lexicon([(m["en"], m["tgt"]) for m in memory])
    print(f"  mined en->{code}     {len(lex)} words")

    panlex = load_panlex(code)
    added_pl = 0
    for en, cands in panlex.items():
        entry = lex.get(en)
        forms = [{"form": c["form"], "phonetic": c["phonetic"], "langvar": c["langvar"],
                  "source": "panlex"} for c in cands]
        if entry:
            entry["alts"] = entry.get("alts", []) + forms          # keep, labelled
        else:
            lex[en] = {"best": cands[0]["form"], "score": None, "count": 0,
                       "alts": forms, "source": "panlex-phonetic", "phonetic": cands[0]["phonetic"]}
            added_pl += 1
    print(f"  + panlex            {len(panlex)} glosses ({added_pl} new headwords, rest added as alternates)")

    cognates = load_cognates(code)
    print(f"  + cognate set       {len(cognates)} forms (comparative Munda, Zenodo CC0)")

    aug = load_aug(code)
    if aug:
        known = {norm_key(m["tgt"]) for m in memory}
        aug = [a for a in aug if norm_key(a["tgt"]) not in known]
        print(f"  + augmented pairs   {len(aug)} synthetic English–{name} pairs (separate layer)")

    wiki = wiktionary_lemmas(wiki_cat)
    wiki_ok = [(w, g) for w, g in wiki if re.search(r"[A-Za-z]{3}", g)]
    print(f"  wiktionary lemmas   {len(wiki_ok)}")
    for head, gloss in wiki_ok:
        e = gloss.lower().strip().split()[0].strip(".,;:")
        if e and e not in lex:
            lex[e] = {"alts": [{"tgt": head, "score": 1.0, "count": 1}],
                      "best": head, "score": 1.0, "source": "wiktionary"}

    # Hindi -> target, through the English pivot, for the curated classroom list only
    dictionary, skipped = [], []
    for hiw, enw, theme, emoji in N:
        hit = lex.get(enw.lower())
        if not hit:
            skipped.append({"hindi": hiw, "english": enw, "why": f"no attested {name} word"})
            continue
        dictionary.append({
            "hi": hiw, "en": enw, "tgt": hit["best"], "theme": theme, "emoji": emoji,
            "confidence": "low", "method": "pivot-en",
            "chain": f"{hiw} → ({enw}) → {hit['best']}",
            "evidence": (
                f"English–{name} alignment, dice {hit['score']} over "
                f"{hit['alts'][0].get('count')} sentence pairs"
                if hit.get("score") is not None and hit.get("alts")
                else f"from the {name} dictionary (source: {hit.get('source')}, "
                     f"spelling as published)")
        })
    print(f"  hi->{code} dictionary {len(dictionary)}  (no attested word: {len(skipped)})")

    memory_en = {m["en"].strip().lower(): m for m in memory}
    return {
        "meta": {
            "language": name,
            "language_code": code,
            "script": lang["script"],
            "pivot": "en",
            "register": lang["register"],
            "built_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "counts": {"sentence_memory": len(memory), "dictionary_en": len(lex),
                       "dictionary_hi_pivot": len(dictionary), "skipped": len(skipped),
                       "cognates": len(cognates), "sentence_memory_aug": len(aug),
                       "panlex_glosses": len(panlex)},
            "sources": lang["sources"],
            "tts": lang["tts"],
            "note": lang["note"],
        },
        "sentence_memory": memory,
        "sentence_memory_aug": aug,
        "cognates": cognates,
        "dictionary_en": [{"en": e, "tgt": v["best"], "score": v.get("score"),
                           "count": (v["alts"][0].get("count") or 0) if v.get("alts") else 0,
                           "source": v.get("source", "corpus-alignment"),
                           "phonetic": v.get("phonetic", False),
                           "alts": [a for a in v.get("alts", []) if a.get("source") == "panlex"][:3]}
                          for e, v in lex.items()],
        "dictionary": dictionary,
        "skipped": skipped[:400],
    }


LANGS = [
    {
        "code": "unr", "name": "Mundari", "script": "Devanagari",
        "range": (0x0900, 0x097F),
        "smol": "en_unr-Deva.jsonl",
        "wiki_cat": "Mundari_lemmas",
        "register": "document / wiki register, sentence-aligned",
        "sources": [
            {"name": "google/smol (smoldoc en_unr-Deva)", "license": "CC-BY-4.0",
             "url": "https://huggingface.co/datasets/google/smol"},
            {"name": "English Wiktionary Mundari lemmas", "license": "CC-BY-SA-4.0",
             "url": "https://en.wiktionary.org/wiki/Category:Mundari_lemmas"},
            {"name": "PanLex (incl. A Mundari-English dictionary, 1983)", "license": "CC0-1.0",
             "url": "https://huggingface.co/datasets/cointegrated/panlex-meanings"},
            {"name": "Munda cognate set with proto-Munda reconstructions", "license": "CC0-1.0",
             "url": "https://zenodo.org/records/3380874"},
            {"name": "espnet/mms_ulab_v2 (Ho audio, no transcript)", "license": "see dataset",
             "url": "https://huggingface.co/datasets/espnet/mms_ulab_v2"},
        ],
        "tts": {"available": True, "engine": "hi (gTTS)",
                "approx": True,
                "why": "Mundari data here is Devanagari, so the same transliteration-free "
                       "route as Santhali works: Hindi voice reads the Devanagari text."},
        "note": "No Hindi–Mundari parallel corpus exists publicly; search results and the "
                "datasets inspected are listed in MUNDARI_HO_REPORT.md.",
    },
    {
        "code": "hoc", "name": "Ho", "script": "Warang Citi",
        "range": (0x118A0, 0x118FF),
        "smol": "en_hoc-Wara.jsonl",
        "wiki_cat": "Ho_lemmas",
        "register": "document register (SMOL) + everyday sentences (Tatoeba)",
        "sources": [
            {"name": "google/smol (smoldoc en_hoc-Wara)", "license": "CC-BY-4.0",
             "url": "https://huggingface.co/datasets/google/smol"},
            {"name": "sicsoc/eng-hoc-Tatoeba-Wiki", "license": "Apache-2.0",
             "url": "https://huggingface.co/datasets/sicsoc/eng-hoc-Tatoeba-Wiki"},
            {"name": "English Wiktionary Ho lemmas", "license": "CC-BY-SA-4.0",
             "url": "https://en.wiktionary.org/wiki/Category:Ho_lemmas"},
            {"name": "PanLex Ho expressions", "license": "CC0-1.0",
             "url": "https://huggingface.co/datasets/cointegrated/panlex-meanings"},
            {"name": "sicsoc/eng-hoc_aug2 + aug5 (machine-augmented)", "license": "Apache-2.0",
             "url": "https://huggingface.co/datasets/sicsoc/eng-hoc_aug5"},
            {"name": "Munda cognate set (Ho forms)", "license": "CC0-1.0",
             "url": "https://zenodo.org/records/3380874"},
            {"name": "espnet/mms_ulab_v2 (Ho audio, no transcript)", "license": "see dataset",
             "url": "https://huggingface.co/datasets/espnet/mms_ulab_v2"},
        ],
        "tts": {"available": False, "engine": None, "approx": False,
                "why": "Ho here is Warang Citi / romanised. There is no Ho voice model and no "
                       "Devanagari spelling to route through the Hindi voice, so no audio is "
                       "offered rather than a wrong reading."},
        "note": "Tatoeba Ho is romanised; the two scripts are labelled per sentence.",
    },
]


def main():
    sat = json.load(open(OUT / "sat.json", encoding="utf-8"))

    # Hindi -> English bridge, assembled from the curated list and the Santhali pack
    hi_en: dict[str, str] = {hiw: enw.lower() for hiw, enw, _, _ in N}
    for e in sat.get("dictionary", []):
        if e.get("hi") and e.get("en"):
            hi_en.setdefault(e["hi"], e["en"].lower())
    for e in sat.get("vocab", []):
        if e.get("hindi") and e.get("english"):
            hi_en.setdefault(e["hindi"], e["english"].lower())
    for e in sat.get("phrases", []):
        if e.get("hindi") and e.get("english"):
            hi_en.setdefault(e["hindi"], e["english"].lower())
    print(f"Hindi->English bridge: {len(hi_en)} pairs "
          f"(curated classroom list {len(N)} + Santhali pack)")

    for lang in LANGS:
        staged = RAW / "smol" / f"smoldoc_{lang['smol']}"
        smol = load_smol(staged if staged.exists() else SRC / lang["smol"])
        extra = load_sicsoc() if lang["code"] == "hoc" else []
        pack = build(lang, smol, extra, lang["wiki_cat"], hi_en)
        path = OUT / f"{lang['code']}.json"
        json.dump(pack, open(path, "w", encoding="utf-8"), ensure_ascii=False)
        print(f"  -> wrote {path}  ({path.stat().st_size/1024:.0f} KB)")


if __name__ == "__main__":
    main()
