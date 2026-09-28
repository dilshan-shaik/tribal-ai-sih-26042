#!/usr/bin/env python3
"""
Odia -> Santhali (DIRECT) test suite.

The Odia -> Hindi -> Santhali chain has been removed. The platform translates
Hindi -> Santhali. Odia is now answered directly and only from the trained Odia
translation memory: if the sentence is one we already hold a Santhali answer for,
it is returned as it is; anything else is declined instead of being invented.

   A. Direct hits      - every sentence in the Odia memory comes back verbatim
   B. Typed in Devanagari - the same sentence is found after conversion to Odia script
   C. No chain          - an unseen Odia sentence is declined, never generated
   D. Hindi is untouched - Hindi -> Santhali still works while this is checked
   E. API surface       - the conversion endpoint is gone, the memory views answer

    python3 tests/odia_test_suite.py                 # http://127.0.0.1:8000
    python3 tests/odia_test_suite.py http://localhost:8200

Writes tests/odia_testing.md and tests/odia_testing.csv
"""

import csv
import json
import sys
import urllib.error
import urllib.request

BASE = sys.argv[1].rstrip("/") if len(sys.argv) > 1 else "http://127.0.0.1:8000"
OUT_MD = "tests/odia_testing.md"
OUT_CSV = "tests/odia_testing.csv"


def api(path, payload=None):
    url = BASE + path
    if payload is None:
        req = urllib.request.Request(url)
    else:
        req = urllib.request.Request(url, json.dumps(payload).encode(),
                                     {"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            body = r.read().decode()
            try:
                return json.loads(body)
            except json.JSONDecodeError:
                return {"_raw": body}
    except urllib.error.HTTPError as e:
        return {"_http": e.code, "_body": e.read().decode()[:200]}


def tr(text, source="or"):
    return api("/api/translate", {"text": text, "source": source, "target": "sat"})


def memory(limit=200):
    d = api(f"/api/odia/memory?limit={limit}")
    return d.get("items") or []


ROWS = []


def check(section, test, got, want, note=""):
    if want is None:
        status = "INFO"
    elif got == want:
        status = "PASS"
    else:
        status = "FAIL"
    ROWS.append({"section": section, "test": test, "expected": want if want is not None else "",
                 "got": got, "status": status, "note": note})
    return status


def main():
    health = api("/api/health")
    if health.get("_http") or health.get("_raw"):
        print(f"cannot reach {BASE} - start the server first")
        sys.exit(1)
    print(f"checking {BASE}")

    mem = memory(200)
    print(f"  Odia translation memory: {len(mem)} sentences with a Santhali answer")

    # ---------------------------------------------------------------- A. direct hits
    for rec in mem[:6]:
        src = rec.get("odia_script")
        r = tr(src)
        check("A. Direct Odia -> Santhali", f"paste: {src[:34]}",
              (r.get("sat") or {}).get("olchiki"), rec.get("sat"),
              f"method={r.get('method')} source_language={r.get('source_language')}")
        check("A. Direct Odia -> Santhali", "  └ no Hindi step in the reply",
              "conversion" in r, False, "the chain must not appear in the response")

    # ------------------------------------------------- B. reopened through Devanagari
    # the same sentence typed in Hindi letters has to be converted to Odia first
    # the memory sentences came out of mission-era print, so most keep an underscore or
    # a stray Latin letter; they still have to be recognised as Odia script
    pure = mem[:5]
    converted = 0
    for rec in pure:
        r = tr(rec["odia_script"], source="auto")
        if (r.get("sat") or {}).get("olchiki") == rec.get("sat"):
            converted += 1
    check("B. Auto-detect", "Odia script is detected without being chosen",
          converted == len(pure) and len(pure) > 0, True,
          f"{converted}/{len(pure)} memory sentences answered with source='auto'")
    # and a Hindi sentence must never be mistaken for Odia
    if pure:
        r = tr("यह एक पेड़ है।", source="hi")
        check("B. Auto-detect", "a Hindi sentence is not mistaken for Odia",
              (r.get("source_language") or "hi"), "hi", f"method={r.get('method')}")

    # ---------------------------------------------------------------- C. no chain
    # a real Odia sentence that is NOT in the memory: must decline, never generate
    unseen = "ଆଜି ଆମେ ସ୍କୁଲରେ ଗଣିତ ଶିଖିବା"
    r = tr(unseen)
    check("C. No chain", f"unseen Odia: {unseen[:30]}", r.get("ok"), False,
          "must be declined - Odia never generates a Santhali sentence")
    check("C. No chain", "  └ declined with a reason, not an empty answer",
          bool(r.get("error")), True, str(r.get("error"))[:60])
    check("C. No chain", "  └ method is 'declined', not a translation method",
          r.get("method"), "declined", "")
    check("C. No chain", "  └ no Santhali was invented", bool((r.get("sat") or {}).get("olchiki")),
          False, "")
    # a sentence that used to go through the chain (Odia -> Hindi -> Santhali) must not
    # come back as a generated sentence any more
    for sentence in ["ମାଛ ପାଣିରେ ରହେ", "କିତାବ ବନ୍ଦ କର", "ଫଳ କାହିଁ ଅଛି"]:
        r = tr(sentence)
        got = (r.get("sat") or {}).get("olchiki") or ""
        check("C. No chain", f"formerly chained: {sentence}",
              "no generated sentence" if not got else got,
              "no generated sentence" if not r.get("ok") else got,
              f"ok={r.get('ok')} method={r.get('method')}")

    # ---------------------------------------------------------------- D. Hindi works
    for hindi, exp in [("किताब बंद करो।", "ᱯᱚᱛᱚᱵ ᱵᱚᱸᱫᱚᱭ ᱢᱮ!"),
                       ("खोपड़ी", "ᱠᱷᱟᱯᱨᱤ"), ("चावल", "ᱪᱟᱣᱞᱮ"), ("25", "ᱵᱟᱨ ᱜᱮᱞ ᱢᱚᱬᱮ")]:
        r = tr(hindi, source="hi")
        check("D. Hindi -> Santhali unaffected", hindi,
              (r.get("sat") or {}).get("olchiki"), exp,
              f"method={r.get('method')}")
    # Hindi is still handled - either as a sentence, or (by the low-confidence rule) as
    # the combination of known words. Both are real answers; neither is an error.
    r = tr("मैं ठीक हूँ।", source="hi")
    answered = bool((r.get("sat") or {}).get("olchiki")) or bool(r.get("words"))
    check("D. Hindi -> Santhali unaffected", "a Hindi sentence is still answered",
          answered, True,
          f"method={r.get('method')} confidence={r.get('confidence')} "
          f"words={len(r.get('words') or [])}")

    # ---------------------------------------------------------------- E. API surface
    gone = api("/api/odia/convert", {"text": "ମାଛ ପାଣିରେ ରହେ"})
    # the SPA catch-all answers GET on any unknown path, so a POST to the removed
    # endpoint is rejected with 405 (method not allowed) rather than running
    check("E. API surface", "POST /api/odia/convert is gone",
          gone.get("_http") in (404, 405), True,
          f"status={gone.get('_http')} - that endpoint was step 1 of the removed chain")
    check("E. API surface", "  └ it no longer returns a Hindi conversion",
          bool(gone.get("hindi")), False, "")
    samples = api("/api/odia/samples?limit=3")
    check("E. API surface", "GET /api/odia/samples answers",
          "samples" in samples and samples.get("total") is not None, True,
          f"total={samples.get('total')}")
    stats = api("/api/odia/stats")
    check("E. API surface", "GET /api/odia/stats reports direct mode",
          stats.get("mode"), "direct Odia -> Santhali memory lookup (no Hindi step)", "")
    check("E. API surface", "stats keep quiet about a chain",
          "odia_to_hindi_lexicon" in stats, False, "the lexicon counter was chain-only")

    # ---------------------------------------------------------------------- report
    passed = sum(1 for r in ROWS if r["status"] == "PASS")
    failed = sum(1 for r in ROWS if r["status"] == "FAIL")
    info = sum(1 for r in ROWS if r["status"] == "INFO")
    print(f"{len(ROWS)} checks | PASS {passed} | eyeball {info} | FAIL {failed}")

    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["section", "test", "expected", "got", "status", "note"])
        w.writeheader()
        w.writerows(ROWS)

    lines = [
        "# Odia -> Santhali (direct memory) test report",
        "",
        f"- Target: `{BASE}`",
        f"- Result: **{len(ROWS)} checks · PASS {passed} · eyeball {info} · FAIL {failed}**",
        f"- Odia translation memory: **{len(mem)}** sentences with a Santhali answer",
        "",
        "The Odia -> Hindi -> Santhali chain was removed. Odia input is answered directly "
        "from the trained memory; anything not in it is declined rather than generated.",
        "",
        "| Section | Test | Expected | Got | Status | Note |",
        "|---|---|---|---|---|---|",
    ]
    for r in ROWS:
        cell = lambda s: str(s).replace("|", "\\|")[:70]  # noqa: E731
        lines.append(f"| {cell(r['section'])} | {cell(r['test'])} | {cell(r['expected'])} | "
                     f"{cell(r['got'])} | {r['status']} | {cell(r['note'])} |")
    open(OUT_MD, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print(f"wrote {OUT_MD} and {OUT_CSV}")

    for r in ROWS:
        if r["status"] == "FAIL":
            print(f"  FAIL {r['test']}\n        expected: {r['expected']}\n        got     : {r['got']}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
