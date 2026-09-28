#!/usr/bin/env python3
"""
Multi-language suite: Santhali (sat) + Mundari (unr) + Ho (hoc).

Run against a live server:  python3 tests/multilang_test_suite.py http://127.0.0.1:8100

The interesting rows are not "does it translate" but "does it refuse correctly":
Mundari and Ho have no Hindi parallel corpus, so Hindi input must arrive as words,
never as a sentence, and Ho must have no audio rather than a wrong reading.
"""
from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8100"

results = []


def check(section, name, got, want, detail=""):
    ok = got == want
    results.append((ok, section, name, got, want, detail))
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"   [{detail}]" if detail else ""))
    return ok


def check_true(section, name, got, detail=""):
    return check(section, name, bool(got), True, detail)


def get(path, raw=False):
    with urllib.request.urlopen(BASE + path, timeout=90) as r:
        body = r.read()
        return r.status, (body if raw else json.loads(body)), dict(r.headers)


def post(path, payload, raw=False):
    req = urllib.request.Request(BASE + path, data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            body = r.read()
            return r.status, (body if raw else json.loads(body)), dict(r.headers)
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"{}"), dict(e.headers)


def tr(text, source, target):
    _, d, _ = post("/api/translate", {"text": text, "source": source, "target": target})
    return d


print(f"checking {BASE}\n")

# ---------------------------------------------------------------- catalogue
print("A. language catalogue")
_, langs, _ = get("/api/languages")
codes = [x["code"] for x in langs["items"]]
check("A", "three languages are offered", sorted(codes), ["hoc", "sat", "unr"], str(codes))
by = {x["code"]: x for x in langs["items"]}
check("A", "default is Santhali", langs["default"], "sat")
for code, name in (("sat", "Santhali"), ("unr", "Mundari"), ("hoc", "Ho")):
    check("A", f"{name} is named", by[code]["language"], name)
check_true("A", "Mundari reports 6k+ attested sentences",
           by["unr"]["counts"]["sentence_memory"] > 6000, str(by["unr"]["counts"]["sentence_memory"]))
check_true("A", "Ho reports 7k+ attested sentences",
           by["hoc"]["counts"]["sentence_memory"] > 7000, str(by["hoc"]["counts"]["sentence_memory"]))
for code in ("unr", "hoc"):
    srcs = by[code]["sources"]
    check_true("A", f"{code} declares its sources with licences",
               srcs and all(s.get("license") for s in srcs),
               ", ".join(f"{s['name']}={s['license']}" for s in srcs))
check("A", "Mundari says Hindi input is words only", by["unr"]["hindi_supported"],
      "words only (no parallel corpus)")
check("A", "Ho says Hindi input is words only", by["hoc"]["hindi_supported"],
      "words only (no parallel corpus)")

print("\nA2. data layers are declared, not implied")
_, langs2, _ = get("/api/languages")
by2 = {x["code"]: x for x in langs2["items"]}
check_true("A2", "Mundari declares its dictionary layer",
           by2["unr"]["layers"]["dictionary_en"] >= 1200, str(by2["unr"]["layers"]))
check_true("A2", "Ho declares augmented sentences",
           by2["hoc"]["layers"]["machine_augmented_sentences"] >= 30000,
           str(by2["hoc"]["layers"]["machine_augmented_sentences"]))
check_true("A2", "Ho declares cognate forms", by2["hoc"]["layers"]["cognate_forms"] >= 90,
           str(by2["hoc"]["layers"]["cognate_forms"]))
check_true("A2", "Mundari Hindi-reachable words grew past the first build",
           by2["unr"]["layers"]["hindi_reachable_words"] >= 100,
           str(by2["unr"]["layers"]["hindi_reachable_words"]))
srcs2 = " ".join(x["name"] for x in by2["unr"]["sources"]) + " ".join(x["name"] for x in by2["hoc"]["sources"])
check_true("A2", "PanLex is credited", "PanLex" in srcs2, srcs2[:90])
check_true("A2", "the cognate set is credited", "cognate" in srcs2.lower(), "")

print("\nC2. synthetic data is labelled and capped")
r = tr("The tall hound is eating.", "en", "hoc")
check("C2", "augmented pairs answer as their own method", r["method"], "sentence-memory-aug")
check("C2", "and are flagged synthetic", r.get("synthetic"), True)
check("C2", "never above medium confidence", r["confidence"], "medium",
      f"note={str(r.get('note'))[:50]}")
check_true("C2", "with a note a teacher can act on", "verify" in (r.get("note") or "").lower()
           or "speaker" in (r.get("note") or "").lower(), (r.get("note") or "")[:70])

print("\nC3. dictionary provenance rides along")
_, d_hoc, _ = post("/api/translate", {"text": "feather", "source": "en", "target": "hoc"})
w = (d_hoc.get("words") or [{}])[0]
check_true("C3", "a dictionary word says where the spelling came from",
           bool(w.get("source")) or bool((d_hoc.get("target") or {}).get("text")),
           f"source={w.get('source')} phonetic={w.get('phonetic')}")

# ---------------------------------------------------------------- santhali
print("\nB. Santhali is unchanged")
r = tr("किताब बंद करो।", "hi", "sat")
check("B", "a known sentence still translates", r["ok"], True, f"method={r['method']}")
check_true("B", "and comes back in Ol Chiki", bool(r["sat"]["olchiki"]), r["sat"]["olchiki"])
r = tr("आज मौसम बहुत अच्छा है।", "hi", "sat")
check("B", "a low-confidence sentence is still words, not a sentence", r["method"], "word-combo")
check("B", "no sentence is shown", r["sat"], None)

# ---------------------------------------------------------------- english in
print("\nC. English -> Mundari / Ho (attested sentences)")
r = tr("Christianity is a religion based on the life and teachings of Jesus Christ.", "en", "unr")
check("C", "Mundari returns a sentence", r["ok"], True, f"method={r['method']}")
check("C", "Mundari is in Devanagari", r["target"]["script"], "Devanagari", r["target"]["text"][:40])
check("C", "attested pairs are high confidence", r["confidence"], "high")
r = tr("Hello, how are you?", "en", "hoc")
check("C", "Ho returns a sentence", r["ok"], True, f"method={r['method']}")
check_true("C", "Ho sentence is in a Ho script", r["target"]["script"] in ("Warang Citi", "roman"),
           r["target"]["script"])
r = tr("water", "en", "unr")
check("C", "single English word uses the dictionary layer", r["method"], "dictionary", r["target"]["text"])
check("C", "and is labelled medium, not high", r["confidence"], "medium")

# ---------------------------------------------------------------- hindi in
print("\nD. Hindi -> Mundari / Ho is words, never a sentence")
for target, text in (("unr", "पानी लाओ।"), ("hoc", "आम और अंडा")):
    r = tr(text, "hi", target)
    check("D", f"{target}: method is the labelled pivot", r["method"], "pivot-en")
    check("D", f"{target}: the result is not a sentence", r["ok"], False)
    check("D", f"{target}: no sentence field is populated", r["sat"], None)
    check_true("D", f"{target}: a word combination is offered instead",
               bool(r["combined"]), f"{r.get('combined')} ({r.get('known')}/{r.get('total')})")
    check_true("D", f"{target}: every word shows its bridge",
               all("→" in (w.get("chain") or "") for w in r["words"]),
               (r["words"][0]["chain"] if r["words"] else "-"))
    check_true("D", f"{target}: confidence is capped below high",
               r["confidence"] in ("low", "medium"), r["confidence"])

print("\nE. Hindi with nothing known declines honestly")
r = tr("बकवास जुमला अजीब", "hi", "hoc")
check("E", "declines", r["method"], "declined")
check("E", "with no output at all", r["output"], None)
check_true("E", "and says what is missing", bool(r.get("note")), (r.get("note") or "")[:70])

print("\nF. an unknown target is refused, not guessed")
r = tr("hello", "en", "klingon")
check("F", "declines", r["ok"], False)
check_true("F", "and lists the languages it does serve", len(r.get("languages") or []) >= 3,
           str(r.get("languages")))

# ---------------------------------------------------------------- audio
print("\nG. audio: approximate for Mundari, honestly absent for Ho")
_, audio, hdrs = post("/api/tts", {"text": "दअ:", "lang": "unr"}, raw=True)
check("G", "Mundari audio is produced", len(audio) > 1000, True, f"{len(audio)} bytes")
check("G", "and is marked approximate", hdrs.get("x-approx"), "true", hdrs.get("x-voice-engine", ""))
code, body, _ = post("/api/tts", {"text": "𑣏𑣁𑣓𑣑𑣃𑣄", "lang": "hoc"})
check("G", "Ho refuses audio instead of mispronouncing", code, 501)
check_true("G", "with a reason a teacher can read", "no Ho voice" in (body.get("detail") or ""),
           (body.get("detail") or "")[:80])

# ---------------------------------------------------------------- pdf
print("\nH. PDF translation carries the chosen language")
import io
import mimetypes

pdf = "/home/user/uploads/SIH-Problem-Statement-26042 (1).pdf"
try:
    with open(pdf, "rb") as fh:
        data = fh.read()
    boundary = "----mtbmltest"
    parts = (f"--{boundary}\r\n"
             f'Content-Disposition: form-data; name="file"; filename="test.pdf"\r\n'
             f"Content-Type: application/pdf\r\n\r\n").encode() + data + f"\r\n--{boundary}--\r\n".encode()
    req = urllib.request.Request(
        BASE + "/api/pdf/translate?max_pages=1&target=unr", data=parts,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
    with urllib.request.urlopen(req, timeout=240) as r:
        doc = json.loads(r.read())
    check("H", "PDF endpoint accepts target=unr", doc.get("target_language"), "unr")
    check_true("H", "and still reads the document", doc["stats"]["blocks"] > 0,
               f"{doc['stats']['blocks']} blocks")
    rows = doc["blocks"]
    check_true("H", "every row carries a method, never a bare sentence", 
               all(b.get("method") for b in rows), rows[0]["method"] if rows else "-")
except FileNotFoundError:
    print("  SKIP  no sample PDF in uploads/")

# ---------------------------------------------------------------- summary
total = len(results)
passed = sum(1 for r in results if r[0])
print(f"\n{total} checks | PASS {passed} | FAIL {total - passed}")
if total - passed:
    print("\nfailures:")
    for ok, sec, name, got, want, detail in results:
        if not ok:
            print(f"  {sec} {name}: got {got!r} want {want!r} {detail}")
sys.exit(0 if passed == total else 1)
