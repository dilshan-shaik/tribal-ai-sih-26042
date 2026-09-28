#!/usr/bin/env python3
"""
Turn the team-supplied English <-> Santhali dictionaries into Hindi -> Santhali data.

Inputs (uploads/, all English <-> Santhali, all in Ol Chiki)
    Santali Open dictionary.csv     466 rows, categorised, with part of speech
    Glossary (eng-sat).csv / .txt   923 rows (same content twice)
    Glossary (sat-eng).csv         1,277 rows, Santhali -> English + an Ol Chiki note
    Body Parts.csv / Relation.csv / Eatables.csv   142 themed rows
    T General (0.06k).csv             59 English -> Santhali sentences
    Name Translation.csv             554 proper names
    (the remaining ~700 general headwords are language and script names)

What it does
    1. parses every file into (english, santhali) records
    2. normalises the OCR spelling variants in the Santhali column
       (ᱢᱚᱸᱬᱮ -> ᱢᱚᱬᱮ, ᱤᱨᱟ.ᱞ -> ᱤᱨᱟᱹᱞ, ᱟᱨᱮᱞ -> ᱟᱨᱮ ...)
    3. gives each headword a Hindi side: curated (pipelines/dict_hi.py) first, then our
       curated vocabulary, then the Wikipedia interlanguage link as a last resort
    4. generates the whole number system 0-100 in both languages from the compositional
       pattern the dictionary itself uses (ᱜᱮᱞ ᱢᱤᱫ = ten-one = eleven, ᱵᱟᱨ ᱜᱮᱞ = two-tens)
    5. hands the 33 hand-translated classroom sentences to the phrase list
    6. reports what got a Hindi side and what did not

Run: python3 pipelines/build_dictionary.py
Writes data/raw/hindi_sat_dictionary.json
"""

import collections
import csv
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pipelines import dict_hi, dict_sentences
from pipelines.lexicon import N

UP = "uploads"
OUT = "data/raw/hindi_sat_dictionary.json"

OL = re.compile(r"[\u1C50-\u1C7F]")


def olchiki_ratio(s: str) -> float:
    """Share of letters that are Ol Chiki. Counted per character - findall() with a
    '+' quantifier returns runs, which silently inflates short words."""
    s = re.sub(r"\s", "", s or "")
    return len(OL.findall(s)) / len(s) if s else 0.0


# --------------------------------------------------------------- OCR normalisation
# The dictionaries were typed by hand and the same word appears several ways. These are
# the variants that matter, each one confirmed by the canonical spelling elsewhere in
# the same file (e.g. ᱢᱚᱬᱮ appears correctly 20+ times).
FIX = {
    "ᱢᱚᱸᱬᱮ": "ᱢᱚᱬᱮ",   # five          (ᱸ + ᱬ are both wrong here)
    "ᱢᱚᱸᱮ": "ᱢᱚᱬᱮ",    # five, second variant
    "ᱤᱨᱟ.ᱞ": "ᱤᱨᱟᱹᱞ",  # eight         (the ASCII full stop stands in for ᱹ)
    "ᱮᱨᱟ.ᱞ": "ᱤᱨᱟᱹᱞ",  # eight, second variant
    "ᱟᱨᱮᱞ": "ᱟᱨᱮ",    # nine
    "ᱯᱤᱱ": "ᱯᱩᱱ",      # four, inside ᱜᱮᱞ ᱯᱤᱱ
    "ᱥᱮᱞᱥᱟᱭ": "ᱥᱮᱞ ᱥᱟᱭ", "ᱜᱮᱞᱥᱟᱥᱟᱭ": "ᱜᱮᱞ ᱥᱟᱭ", "ᱜᱮᱞᱢᱚᱲᱚᱭ": "ᱜᱮᱞ ᱢᱚᱲᱚᱭ",
    "ᱵᱚᱲᱚᱭ": "ᱠᱚᱲᱚᱭ",   # crore
    "ᱩᱞᱤ ᱟᱢ": "ᱩᱞ", "ᱟᱹᱛᱳ": "ᱟᱹᱛᱩ",
}
# canonical spellings for the numbers the rest of the system composes from
UNITS = ["", "ᱢᱤᱫ", "ᱵᱟᱨ", "ᱯᱮ", "ᱯᱩᱱ", "ᱢᱚᱬᱮ", "ᱛᱩᱨᱩᱭ", "ᱮᱭᱟᱭ", "ᱤᱨᱟᱹᱞ", "ᱟᱨᱮ"]
TEN = "ᱜᱮᱞ"

HI_UNITS = ["", "एक", "दो", "तीन", "चार", "पाँच", "छह", "सात", "आठ", "नौ"]


def clean_sat(s: str, word: bool = True) -> str:
    """Normalise an Ol Chiki string. `word=True` for headwords/phrases, `word=False`
    for full sentences (where a trailing "." is a real full stop)."""
    s = re.sub(r"\s+", " ", s or "").strip()
    # the dictionaries were typed on a Latin keyboard and use "." where Ol Chiki needs
    # the gicher ᱹ (ᱠᱟ.ᱦᱩ is really ᱠᱟᱹᱦᱩ). Only fix it between Ol Chiki letters, so
    # punctuation and the genuine full stops survive.
    s = re.sub(r"(?<=[\u1C50-\u1C7F])\.(?=[\u1C50-\u1C7F])", "\u1c79", s)
    for bad, good in FIX.items():
        s = s.replace(bad, good)
    if word:
        # a trailing "." after an Ol Chiki letter is the same dropped gicher:
        # ᱢᱩᱞᱟ. is ᱢᱩᱞᱟᱹ (radish), ᱜᱤᱫᱽᱨᱟ. is ᱜᱤᱫᱽᱨᱟᱹ (child)
        s = re.sub(r"(?<=[\u1C50-\u1C7F])\.$", "\u1c79", s)
    return re.sub(r"\s+", " ", s).strip(" ,")


# ------------------------------------------------------------------- parsing
def parse() -> list[dict]:
    recs = []

    def add(en, sat, src, cat=""):
        en = re.sub(r"\s+", " ", str(en or "")).strip()
        sat = clean_sat(sat)
        if en and sat and olchiki_ratio(sat) > 0.5 and not re.fullmatch(r"[\d.,]+", en):
            recs.append({"en": en, "sat": sat, "source": src, "category": cat})

    with open(f"{UP}/Santali Open dictionary.csv", encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            add(r.get("English"), r.get("Santali"), "santali-open-dictionary",
                (r.get("Category") or "").strip())
    for fn, cat in [("Body Parts.csv", "body"), ("Relation.csv", "family"),
                    ("Eatables.csv", "food")]:
        with open(f"{UP}/{fn}", encoding="utf-8-sig") as f:
            for row in csv.reader(f):
                if len(row) >= 2:
                    add(row[0], row[1], fn.replace(".csv", "").lower(), cat)
    for fn in ["Glossary (eng-sat).csv", "Glossary(eng-sat).txt"]:
        with open(f"{UP}/{fn}", encoding="utf-8-sig") as f:
            for row in csv.reader(f, delimiter="\t" if fn.endswith(".txt") else ","):
                if len(row) >= 2:
                    add(row[0], row[1], "glossary-eng-sat")
    with open(f"{UP}/Glossary (sat-eng).csv", encoding="utf-8-sig") as f:
        for i, row in enumerate(csv.reader(f)):
            if i and len(row) >= 2:
                add(row[1], row[0], "glossary-sat-eng")
    return recs


def parse_sentences():
    out = []
    with open(f"{UP}/T General (0.06k).csv", encoding="utf-8-sig") as f:
        for i, row in enumerate(csv.reader(f)):
            if i and len(row) >= 2 and olchiki_ratio(row[0]) > 0.4:
                out.append({"sat": clean_sat(row[0]), "en": row[1].strip()})
    return out


def parse_names():
    out = []
    with open(f"{UP}/Name Translation.csv", encoding="utf-8-sig") as f:
        for i, row in enumerate(csv.reader(f)):
            if i and len(row) >= 2 and olchiki_ratio(row[0]) > 0.4:
                out.append({"sat": clean_sat(row[0]), "en": row[1].strip()})
    return out


# ------------------------------------------------------------------- numbers
HI_21_99 = {
    21: "इक्कीस", 22: "बाईस", 23: "तेईस", 24: "चौबीस", 25: "पच्चीस", 26: "छब्बीस",
    27: "सत्ताईस", 28: "अट्ठाईस", 29: "उनतीस", 31: "इकतीस", 32: "बत्तीस",
    33: "तैंतीस", 34: "चौंतीस", 35: "पैंतीस", 36: "छत्तीस", 37: "सैंतीस",
    38: "अड़तीस", 39: "उनतालीस", 41: "इकतालीस", 42: "बयालीस", 43: "तैंतालीस",
    44: "चवालीस", 45: "पैंतालीस", 46: "छियालीस", 47: "सैंतालीस", 48: "अड़तालीस",
    49: "उनचास", 51: "इक्यावन", 52: "बावन", 53: "तिरपन", 54: "चौवन", 55: "पचपन",
    56: "छप्पन", 57: "सत्तावन", 58: "अट्ठावन", 59: "उनसठ", 61: "इकसठ", 62: "बासठ",
    63: "तिरसठ", 64: "चौंसठ", 65: "पैंसठ", 66: "छियासठ", 67: "सड़सठ", 68: "अड़सठ",
    69: "उनहत्तर", 71: "इकहत्तर", 72: "बहत्तर", 73: "तिहत्तर", 74: "चौहत्तर",
    75: "पचहत्तर", 76: "छिहत्तर", 77: "सतहत्तर", 78: "अठहत्तर", 79: "उनासी",
    81: "इक्यासी", 82: "बयासी", 83: "तिरासी", 84: "चौरासी", 85: "पचासी",
    86: "छियासी", 87: "सत्तासी", 88: "अट्ठासी", 89: "नवासी", 91: "इक्यानवे",
    92: "बानवे", 93: "तिरानवे", 94: "चौरानवे", 95: "पचानवे", 96: "छियानवे",
    97: "सत्तानवे", 98: "अट्ठानवे", 99: "निन्यानवे",
}
HI_TENS = {10: "दस", 20: "बीस", 30: "तीस", 40: "चालीस", 50: "पचास",
           60: "साठ", 70: "सत्तर", 80: "अस्सी", 90: "नब्बे", 100: "सौ"}
HI_TEENS = {11: "ग्यारह", 12: "बारह", 13: "तेरह", 14: "चौदह", 15: "पंद्रह",
            16: "सोलह", 17: "सत्रह", 18: "अठारह", 19: "उन्नीस"}


def hi_number(n: int) -> str:
    if n == 0:
        return "शून्य"
    if n <= 9:
        return HI_UNITS[n]
    if n in HI_TENS:
        return HI_TENS[n]
    if n in HI_TEENS:
        return HI_TEENS[n]
    if n in HI_21_99:
        return HI_21_99[n]
    if 21 <= n <= 99:                      # regular tens + unit (31 = इकतीस handled above)
        t, u = divmod(n, 10)
        return {2: "बीस", 3: "तीस", 4: "चालीस", 5: "पचास",
                6: "साठ", 7: "सत्तर", 8: "अस्सी", 9: "नब्बे"}[t] + " " + HI_UNITS[u]
    return str(n)


def sat_number(n: int) -> str:
    """Santhali numerals are decimal and compositional, exactly as the dictionary shows:
    ᱜᱮᱞ ᱢᱤᱫ = ten+one = 11, ᱵᱟᱨ ᱜᱮᱞ = two tens = 20, ᱵᱟᱨ ᱜᱮᱞ ᱢᱤᱫ = 21."""
    if n == 0:
        return "ᱥᱩᱱᱭᱚ"
    if n < 10:
        return UNITS[n]
    if n == 10:
        return TEN
    if n in (100,):
        return "ᱥᱟᱭ"
    if n % 10 == 0:
        return f"{UNITS[n // 10]} {TEN}"
    if n < 20:
        return f"{TEN} {UNITS[n % 10]}"
    return f"{UNITS[n // 10]} {TEN} {UNITS[n % 10]}"


def build_numbers():
    num = {}
    for n in range(0, 101):
        num[str(n)] = {"hi": hi_number(n), "sat": sat_number(n)}
    big = {"1000": ("हज़ार", "ᱥᱮᱞ ᱥᱟᱭ"), "10000": ("दस हज़ार", "ᱜᱮᱞ ᱥᱟᱭ"),
           "100000": ("एक लाख", "ᱢᱚᱲᱚᱭ"), "1000000": ("दस लाख", "ᱜᱮᱞ ᱢᱚᱲᱚᱭ"),
           "10000000": ("एक करोड़", "ᱠᱚᱲᱚᱭ")}
    for k, (h, s) in big.items():
        num[k] = {"hi": h, "sat": s}
    return num


def _conflicts(entries):
    """Same Hindi word, but the new dictionaries and the shipped pack disagree.
    Reported, never auto-merged - a human decides which form a classroom sees."""
    path = "data/language_packs/sat.json"
    if not os.path.exists(path):
        return []
    pack = json.load(open(path, encoding="utf-8"))
    have = {v["hindi"]: v["sat"] for v in pack["vocab"] if v.get("sat")}
    out = []
    for e in entries:
        cur = have.get(e["hi"])
        if cur and cur != e["sat"]:
            out.append({"hindi": e["hi"], "english": e["en"], "pack": cur,
                        "dictionary": e["sat"], "source": e["source"]})
    return out


# ------------------------------------------------------------------------- main
def main():
    raw = parse()
    sentences = parse_sentences()
    names = parse_names()
    wiki = json.load(open("data/raw/en_hi_wikipedia.json", encoding="utf-8")) \
        if os.path.exists("data/raw/en_hi_wikipedia.json") else {}

    # Hindi sources, in order of trust
    curated_hi = dict(dict_hi.EN_HI)
    n_pivot = {}
    for hindi, english, _, _ in N:
        n_pivot.setdefault(english.lower(), hindi)
    for hindi, english, _, _ in N:
        pass
    # include the curated vocabulary from the pack as well (it is richer than N alone)
    pack_hi = {}
    if os.path.exists("data/language_packs/sat.json"):
        pack = json.load(open("data/language_packs/sat.json", encoding="utf-8"))
        for v in pack["vocab"]:
            if v.get("english") and v.get("hindi"):
                pack_hi[v["english"].lower()] = v["hindi"]

    # one entry per English headword, preferring the richest source
    by_en = collections.OrderedDict()
    for r in raw:
        key = r["en"].lower()
        cur = by_en.get(key)
        if cur is None or (r["category"] and not cur["category"]):
            by_en[key] = dict(r)

    # every file that attests a headword, so each upload can be traced in the report
    attested_by: dict[str, list[str]] = {}
    spellings: dict[str, set] = {}
    for r in raw:
        key = r["en"].lower()
        attested_by.setdefault(key, [])
        if r["source"] not in attested_by[key]:
            attested_by[key].append(r["source"])
        spellings.setdefault(key, set()).add(r["sat"])

    entries, stats = [], collections.Counter()
    for key, r in by_en.items():
        hi, how = None, None
        # numeric headwords ("31") are handled by the number system, not the lexicon
        if re.fullmatch(r"\d+", key):
            continue
        if key in curated_hi:
            hi, how = curated_hi[key], "curated"
        elif key in n_pivot:
            hi, how = n_pivot[key], "curated-vocabulary"
        elif key in pack_hi:
            hi, how = pack_hi[key], "pack-vocabulary"
        elif key in wiki:
            hi, how = wiki[key], "wikipedia"
        stats[how or "no-hindi"] += 1
        if not hi:
            continue
        entries.append({
            "hi": hi, "en": r["en"], "sat": r["sat"],
            "theme": dict_hi.theme_of(key),
            "category": r["category"],
            "source": r["source"],
            "found_in": attested_by.get(key, [r["source"]]),
            "variants": sorted(spellings.get(key, {r["sat"]}) - {r["sat"]}),
            "hindi_source": how,
            "confidence": "high" if how.startswith(("curated", "pack")) else "medium",
        })

    entries.sort(key=lambda e: (e["theme"], e["en"]))

    # sentences: only the ones with a hand-written Hindi
    known = {clean_sat(s["sat"], word=False): s for s in sentences}
    sents = []
    for sat, hi in dict_sentences.SENTENCES.items():
        sents.append({"hi": hi, "sat": clean_sat(sat, word=False),
                      "en": (known.get(clean_sat(sat)) or {}).get("en", ""),
                      "note": dict_sentences.NOTES.get(sat, "")})

    numbers = build_numbers()

    # how many number words each file attests. parse() deliberately drops numeric
    # headwords (the number system is generated compositionally), so count them here:
    # they are the evidence that ᱜᱮᱞ ᱢᱤᱫ = 11 and ᱵᱟᱨ ᱜᱮᱞ = 20.
    num_by_file: dict[str, int] = collections.Counter()
    with open(f"{UP}/Santali Open dictionary.csv", encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            if re.fullmatch(r"\d+", (r.get("English") or "").strip()):
                num_by_file["santali-open-dictionary"] += 1
    for fn in ["Glossary (eng-sat).csv", "Glossary (sat-eng).csv"]:
        with open(f"{UP}/{fn}", encoding="utf-8-sig") as f:
            for i, row in enumerate(csv.reader(f)):
                if len(row) >= 2:
                    col = 1 if "sat-eng" in fn else 0
                    if re.fullmatch(r"\d+", row[col].strip()):
                        num_by_file["glossary-sat-eng" if "sat-eng" in fn
                                    else "glossary-eng-sat"] += 1
    for fn, slug in [("Body Parts.csv", "body parts"), ("Relation.csv", "relation"),
                     ("Eatables.csv", "eatables")]:
        with open(f"{UP}/{fn}", encoding="utf-8-sig") as f:
            for row in csv.reader(f):
                if len(row) >= 2 and re.fullmatch(r"\d+", row[0].strip()):
                    num_by_file[slug] += 1

    # ---- per-file accounting: what each supplied file contributed and where ----
    SLUG_FILE = {
        "santali-open-dictionary": "Santali Open dictionary.csv",
        "glossary-eng-sat": "Glossary (eng-sat).csv + Glossary(eng-sat).txt",
        "glossary-sat-eng": "Glossary (sat-eng).csv",
        "body parts": "Body Parts.csv",
        "relation": "Relation.csv",
        "eatables": "Eatables.csv",
        "name-translation": "Name Translation.csv",
        "t-general": "T General (0.06k).csv",
    }
    per_file = {f: {"file": f, "records": 0, "headwords": 0, "in_dictionary": 0,
                    "hindi_curated": 0, "numbers": 0, "sentences": 0, "names": 0}
                for f in SLUG_FILE.values()}
    for r in raw:
        per_file[SLUG_FILE[r["source"]]]["records"] += 1
    for key in attested_by:
        for slug in attested_by[key]:
            per_file[SLUG_FILE[slug]]["headwords"] += 1
    for e in entries:
        for slug in e.get("found_in", []):
            pf = per_file[SLUG_FILE[slug]]
            pf["in_dictionary"] += 1
            pf["hindi_curated"] += 1 if e["hindi_source"].startswith("curated") else 0
    # numbers and names are parsed from their own files
    for slug in ("santali-open-dictionary", "glossary-eng-sat", "glossary-sat-eng",
                 "eatables", "body parts", "relation"):
        per_file[SLUG_FILE[slug]]["numbers"] = num_by_file.get(slug, 0)
    per_file[SLUG_FILE["t-general"]]["sentences"] = len(sents)
    per_file[SLUG_FILE["name-translation"]]["names"] = len(names)

    payload = {
        "conflicts_with_pack": _conflicts(entries),
        "meta": {
            "purpose": "Hindi -> Santhali dictionary built from the team-supplied "
                       "English <-> Santhali files, so the Hindi engine can use them",
            "counts": {
                "entries": len(entries),
                "headwords_seen": len(by_en),
                "with_hindi": len(entries),
                "curated_hindi": stats["curated"] + stats["curated-vocabulary"]
                                 + stats["pack-vocabulary"],
                "wikipedia_hindi": stats["wikipedia"],
                "no_hindi": stats["no-hindi"],
                "numbers": len(numbers),
                "sentences": len(sents),
            },
            "hindi_source_legend": {
                "curated": "hand-written in pipelines/dict_hi.py",
                "curated-vocabulary": "from the project's foundational-literacy list",
                "pack-vocabulary": "already in the language pack",
                "wikipedia": "English Wikipedia -> Hindi Wikipedia interlanguage link",
            },
            "normalised_spellings": FIX,
            "skipped_headwords": dict_hi.SKIPPED,
            "per_file": per_file,
            "files": ["Santali Open dictionary.csv", "Glossary (eng-sat).csv",
                      "Glossary(eng-sat).txt", "Glossary (sat-eng).csv", "Body Parts.csv",
                      "Relation.csv", "Eatables.csv", "T General (0.06k).csv",
                      "Name Translation.csv"],
        },
        "entries": entries,
        "numbers": numbers,
        "sentences": sents,
        "names": names,
        "raw_sentences": sentences,
    }
    os.makedirs("data/raw", exist_ok=True)
    json.dump(payload, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    c = payload["meta"]["counts"]
    print(f"source records parsed      : {len(raw):,}")
    print(f"unique English headwords   : {c['headwords_seen']:,}")
    print(f"  with a Hindi side        : {c['with_hindi']:,}")
    print(f"    hand-curated Hindi     : {c['curated_hindi']:,}")
    print(f"    Wikipedia-derived      : {c['wikipedia_hindi']:,}")
    print(f"  without Hindi (skipped)  : {c['no_hindi']:,}")
    print(f"numbers 0-100 + big numbers: {c['numbers']}")
    print(f"hand-translated sentences  : {c['sentences']}")
    print(f"proper names               : {len(names):,}")
    print(f"\nwrote {OUT}")
    print("\nby theme:")
    for t, n in collections.Counter(e["theme"] for e in entries).most_common():
        print(f"   {t:10} {n:5}")
    print("\nsample entries:")
    for e in entries[:6] + [x for x in entries if x["theme"] == "body"][:4] + \
             [x for x in entries if x["theme"] == "family"][:3]:
        print(f"   {e['hi']:12} <- {e['en']:16} -> {e['sat']:16} [{e['hindi_source']}]")
    print("\nnumbers 1-20:")
    print("   " + ", ".join(f"{k}:{v['hi']}/{v['sat']}" for k, v in
                            list(numbers.items())[1:21]))


if __name__ == "__main__":
    main()
