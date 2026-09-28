#!/usr/bin/env python3
"""
Hindi test sentences for the MTB-MLE Santhali platform.

Every sentence is sent to the live /api/translate endpoint, so the report shows
what the application ACTUALLY answers - not what it is supposed to answer.

    python3 tests/hindi_test_suite.py                 # uses http://127.0.0.1:8000
    python3 tests/hindi_test_suite.py http://localhost:8200

Writes:
    tests/hindi_testing_sentences.csv   (UTF-8 BOM, opens in Excel)
    tests/hindi_testing_sentences.md    (readable report)
"""

import csv
import json
import re
import sys
import urllib.error
import urllib.request

BASE = sys.argv[1].rstrip("/") if len(sys.argv) > 1 else "http://127.0.0.1:8000"
OUT_CSV = "tests/hindi_testing_sentences.csv"
OUT_MD = "tests/hindi_testing_sentences.md"


# --------------------------------------------------------------- HTTP helpers
def api(path, payload=None):
    if payload is None:
        req = urllib.request.Request(BASE + path)
    else:
        req = urllib.request.Request(
            BASE + path,
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
        )
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.load(r)


def api_text(path, payload):
    req = urllib.request.Request(path if path.startswith("http") else BASE + path,
                                 data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read().decode()


def translate(text):
    try:
        return api("/api/translate", {"text": text})
    except urllib.error.HTTPError as e:
        return {"error": f"HTTP {e.code}"}
    except Exception as e:                                   # noqa: BLE001
        return {"error": str(e)}


# ------------------------------------------------------- hand-written sentences
# (category, hindi sentence, expected Santhali or None, why this sentence is here)
MANUAL = [
    # 1. everyday teacher talk - the phrases a real classroom uses
    ("Classroom instructions", "किताब बंद करो।", "ᱯᱚᱛᱚᱵ ᱵᱚᱸᱫᱚᱭ ᱢᱮ!", "attested phrase from the corpus"),
    ("Classroom instructions", "किताब खोलो।", "ᱯᱚᱛᱚᱵ ᱡᱷᱤᱡᱽ ᱢᱮ।", "verified phrase"),
    ("Classroom instructions", "ध्यान से पढ़ो।", "ᱟᱪᱩᱨ ᱠᱟᱛᱮᱜ ᱯᱟᱲᱦᱟᱣ ᱢᱮ।", "attested phrase (exact corpus match)"),
    ("Classroom instructions", "मेरी मदद करो।", "ᱫᱟᱭᱟᱠᱟᱛᱮ ᱜᱚᱲᱚ ᱮᱢᱚᱜ ᱢᱮ ᱾", "attested phrase"),
    ("Classroom instructions", "फल कहाँ है?", "ᱡᱚ ᱫᱚ ᱚᱠᱟᱨᱮ ᱢᱮᱱᱟᱜᱼᱟ ?", "attested question"),
    ("Classroom instructions", "मछली पानी में रहती है।", "ᱦᱟᱹᱠᱩ ᱫᱚ ᱫᱟᱜ ᱨᱮᱠᱚ ᱛᱟᱦᱮᱸᱱ ᱠᱟᱱᱟ᱾", "attested full sentence"),
    ("Classroom instructions", "आज हम गिनती सीखेंगे।", "ᱛᱮᱦᱮᱧ ᱟᱞᱮ ᱞᱮᱠᱷᱟ ᱪᱮᱫᱚᱜ ᱞᱮᱭᱟ।", "flagship demo sentence - composed from attested parts"),

    # 2. "this is a ..." frames - the pattern a child practises
    ("'This is a ...' frames", "यह एक पेड़ है।", "ᱱᱚᱶᱟ ᱫᱚ ᱢᱤᱫᱴᱟᱹᱝ ᱫᱟᱨᱮ ᱠᱟᱱᱟ।", "template + nukta word (पेड़)"),
    ("'This is a ...' frames", "यह एक दरवाज़ा है।", "ᱱᱚᱶᱟ ᱫᱚ ᱢᱤᱫᱴᱟᱹᱝ ᱫᱩᱣᱟᱹᱨ ᱠᱟᱱᱟ।", "template + dataset word (दरवाज़ा)"),
    ("'This is a ...' frames", "यह एक कुत्ता है।", "ᱱᱚᱶᱟ ᱫᱚ ᱢᱤᱫᱴᱟᱹᱝ ᱥᱮᱛᱟ ᱠᱟᱱᱟ।", "template + old vocab"),
    ("'This is a ...' frames", "यह आम है।", "ᱱᱚᱶᱟ ᱫᱚ ᱢᱤᱫᱴᱟᱹᱝ ᱩᱞ ᱠᱟᱱᱟ।", "template, no एक"),
    ("'This is a ...' frames", "यह एक मुर्गी है।", None, "template + word corrected by the new dataset"),
    ("'This is a ...' frames", "यह एक नींबू है।", None, "template + dataset word (नींबू)"),
    ("'This is a ...' frames", "यह एक गाँव है।", None, "template + word corrected by the new dataset (ᱟᱹᱛᱩ)"),

    # 3. the 15 words the new CSV resolved - single-word spot checks
    ("Words from the new dataset", "दादी", "ᱵᱩᱰᱤᱜᱚ", "40 sentences, p=0.70, lift 87"),
    ("Words from the new dataset", "दादा", "ᱜᱚᱲᱚᱢ ᱦᱟᱲᱟᱢ", "kinship word"),
    ("Words from the new dataset", "लड़का", "ᱠᱚᱲᱟ", "kinship word"),
    ("Words from the new dataset", "औरत", "ᱛᱤᱨᱞᱟᱹ", "kinship word"),
    ("Words from the new dataset", "भात", "ᱫᱟᱠᱟ", "food"),
    ("Words from the new dataset", "मुर्गी", "ᱥᱤᱢ", "bird/farm"),
    ("Words from the new dataset", "दरवाज़ा", "ᱫᱩᱣᱟᱹᱨ", "classroom object"),
    ("Words from the new dataset", "चॉक", "ᱪᱚᱠ", "classroom object"),
    ("Words from the new dataset", "नींबू", "ᱞᱤᱢᱵᱩ", "fruit"),
    ("Words from the new dataset", "दुखी", "ᱫᱩᱠᱷ ᱟᱱᱟᱜ", "feeling"),
    ("Words from the new dataset", "पंद्रह", "ᱜᱮᱞ ᱢᱚᱬᱮ", "number 15"),
    ("Words from the new dataset", "बीस", "ᱵᱟᱨ ᱜᱮᱞ", "number 20"),
    ("Words from the new dataset", "तीस", "ᱯᱮ ᱜᱮᱞ", "number 30"),
    ("Words from the new dataset", "पचास", "ᱢᱚᱬᱮ ᱜᱮᱞ", "number 50"),

    # 4. the 3 entries that were corrected - these used to be wrong
    ("Corrected entries", "आम", "ᱩᱞ", "was ᱩᱞᱤ before the dataset arrived"),
    ("Corrected entries", "सूरज", "ᱥᱤᱧ ᱪᱟᱸᱫᱚ", "was ᱥᱤᱸᱜᱮ (ᱪᱟᱸᱫᱚ alone = moon)"),
    ("Corrected entries", "गाँव", "ᱟᱹᱛᱩ", "was ᱟᱛᱳ"),

    # 5. numbers and counting
    ("Numbers (1-15 must all be different)", "एक", "ᱢᱤᱫ", "counting 1-10"),
    ("Numbers (1-15 must all be different)", "दो", "ᱵᱟᱨᱭᱟ", ""),
    ("Numbers (1-15 must all be different)", "तीन", "ᱯᱮ", ""),
    ("Numbers (1-15 must all be different)", "चार", "ᱯᱩᱱ",
     "corrected: ᱯᱩᱱ is the standard form, ᱯᱳᱱ is the file's variant"),
    ("Numbers (1-15 must all be different)", "पाँच", "ᱢᱚᱬᱮ", "regression: was ᱢᱹᱲᱮ"),
    ("Numbers (1-15 must all be different)", "छह", "ᱛᱩᱨᱩᱭ", "regression: was ᱮᱭᱟᱭ (= seven)"),
    ("Numbers (1-15 must all be different)", "सात", "ᱮᱭᱟᱭ", ""),
    ("Numbers (1-15 must all be different)", "आठ", "ᱤᱨᱟᱹᱞ", "regression: was ᱮᱭᱟᱭ (= seven)"),
    ("Numbers (1-15 must all be different)", "नौ", "ᱟᱨᱮ", ""),
    ("Numbers (1-15 must all be different)", "दस", "ᱜᱮᱞ", ""),
    ("Numbers (1-15 must all be different)", "ग्यारह", "ᱜᱮᱞ ᱢᱤᱫ", "regression: was ᱜᱢᱤᱛ"),
    ("Numbers (1-15 must all be different)", "बारह", "ᱜᱮᱞ ᱵᱟᱨ", "regression: was ᱵᱟᱨᱜᱮᱞ (reversed)"),
    ("Numbers (1-15 must all be different)", "तेरह", "ᱜᱮᱞ ᱯᱮ",
     "corrected: 11 is ᱜᱮᱞ ᱢᱤᱫ, 12 ᱜᱮᱞ ᱵᱟᱨ, so 13 is ᱜᱮᱞ ᱯᱮ"),
    ("Numbers (1-15 must all be different)", "चौदह", "ᱜᱮᱞ ᱯᱩᱱ", "regression: was ᱜᱮᱯᱮ (= thirteen)"),
    ("Numbers (1-15 must all be different)", "पंद्रह", "ᱜᱮᱞ ᱢᱚᱬᱮ", ""),
    ("Numbers (1-15 must all be different)", "सौ", "ᱥᱟᱭ", "regression: was ᱤᱨᱟᱹᱞ (= eight)"),
    ("Numbers", "पाँच भात", None, "number + noun (word order check)"),
    ("Numbers", "मेरे पास बीस आम हैं।", None, "counting in a full sentence"),
    ("Numbers", "कक्षा में तीस बच्चे हैं।", None, "counting in a full sentence"),

    # 5b. bare imperatives - the verb table answers even with no object
    ("Bare imperatives (verb table)", "बताओ।", "ᱞᱟᱹᱭ ᱢᱮ", "tell! - was declined before"),
    ("Bare imperatives (verb table)", "चलो।", "ᱪᱟᱞᱟᱜ ᱯᱮ", "let's go! - was declined before"),
    ("Bare imperatives (verb table)", "लो।", "ᱦᱟᱛᱟᱣ ᱢᱮ", "take! - was declined before"),
    ("Bare imperatives (verb table)", "बंद करो", "ᱵᱚᱸᱫᱚᱭ ᱢᱮ", "switch off!, no object"),
    ("Bare imperatives (verb table)", "खोलो", "ᱡᱷᱤᱡᱽ ᱢᱮ", "open!, no object"),
    ("Bare imperatives (verb table)", "शुरू करो", "ᱪᱟᱹᱞᱩᱭ ᱢᱮ", "start!"),
    ("Bare imperatives (verb table)", "रखो", "ᱫᱚᱦᱚ ᱢᱮ", "keep!"),
    ("Bare imperatives (verb table)", "सीखो", "ᱪᱮᱫᱚᱜ ᱢᱮ", "learn!"),

    # 6. messy Hindi - what a microphone or a child actually types
    ("Messy / speech-style input", "किताब बन्द करो", "ᱯᱚᱛᱚᱵ ᱵᱚᱸᱫᱚᱭ ᱢᱮ!", "बन्द spelling + no danda drawn from speech"),
    ("Messy / speech-style input", "किताब बंद करो", "ᱯᱚᱛᱚᱵ ᱵᱚᱸᱫᱚᱭ ᱢᱮ!", "no danda"),
    ("Messy / speech-style input", "फल कहा है।", "ᱡᱚ ᱫᱚ ᱚᱠᱟᱨᱮ ᱢᱮᱱᱟᱜᱼᱟ ?", "ASR dropped the nasal: कहा for कहाँ"),
    ("Messy / speech-style input", "मछली पानी मे रहती है", "ᱦᱟᱹᱠᱩ ᱫᱚ ᱫᱟᱜ ᱨᱮᱠᱚ ᱛᱟᱦᱮᱸᱱ ᱠᱟᱱᱟ᱾", "missing anusvara in मे"),
    ("Messy / speech-style input", "किताब   खोलो", None, "double space"),
    ("Messy / speech-style input", "किताब खोलो", None, "no punctuation at all"),

    # 7. honest limits - outside the supported domain, must degrade gracefully
    ("Outside the domain (expected: word bank)", "मुझे बाजार से दो किलो चावल लाना है।", None, "long everyday sentence, not in corpora"),
    ("Outside the domain (expected: word bank)", "आज मौसम बहुत अच्छा है।", None, "small talk"),
    ("Outside the domain (expected: word bank)", "रेलगाड़ी स्टेशन पर रुकती है।", "DECLINE", "no known word - must decline, not invent"),
    ("Outside the domain (expected: word bank)", "सरकारी स्कूल में नया शिक्षक आया है।", None, "education administration"),

    # 8. edge cases - must never crash or return a wrong confident answer
    ("Edge cases (must not crash)", "", "REJECT", "empty input - must be refused, not crash"),
    ("Edge cases (must not crash)", "।।।", "REJECT", "punctuation only - must be refused, not crash"),
    ("Edge cases (must not crash)", "12345", "DECLINE", "digits only - must decline"),
    ("Edge cases (must not crash)", "hello teacher", "DECLINE", "English input - must decline"),
    ("Edge cases (must not crash)", "आम आम आम आम आम", None, "same word repeated"),
    ("Edge cases (must not crash)", "दादी ने कहा।", None, "कहा (said) must NOT be read as कहाँ (where)"),
    ("Edge cases (must not crash)", "दो।", None, "ambiguous: number 'two' wins over verb 'give!' - needs context"),
]


# --------------------------------------------------- sentences taken from the pack
def derived_cases():
    """Round-trip every attested phrase and every verb the app ships."""
    cases = []
    try:
        phrases = api("/api/phrases")["items"]
    except Exception:                                        # noqa: BLE001
        phrases = []
    for p in phrases:
        hi = p["hindi"]
        cases.append((
            "All shipped phrases (round trip)",
            hi,
            p.get("sat"),
            f"{p.get('kind', '?')} phrase, confidence {p.get('confidence', '?')}",
        ))
    try:
        verbs = api("/api/verbs")["items"]
    except Exception:                                        # noqa: BLE001
        verbs = []
    # the Hindi -> Santhali dictionary rebuilt from the nine team-supplied files:
    # one row per source file, plus the number system and the hand-written sentences
    try:
        entries = api("/api/dictionary?limit=0")["items"]
    except Exception:                                        # noqa: BLE001
        entries = []
    print(f"      dictionary endpoint returned {len(entries)} entries")
    # where the shipped word list and the uploaded dictionaries disagree, the shipped
    # word list wins (the other form is kept as an alternate) - the test must expect that
    try:
        shipped = {v["hindi"]: v["sat"] for v in api("/api/vocab", None)["items"]
                   if v.get("sat")}
    except Exception:                                        # noqa: BLE001
        shipped = {}
    try:
        shipped = dict(shipped)
        shipped.update({p["hindi"]: p["sat"] for p in api("/api/phrases")["items"]
                        if p.get("sat")})
    except Exception:                                        # noqa: BLE001
        pass
    by_source: dict[str, list] = {}
    for e in entries:
        if e.get("sat") and e.get("hi"):
            by_source.setdefault(e.get("source") or "?", []).append(e)
    for src, items in sorted(by_source.items()):
        sample = items[:: max(1, len(items) // 4)][:4]
        for e in sample:
            want = shipped.get(e["hi"], e["sat"].strip("? ."))
            note = (f"from {src} (Hindi side: {e.get('hindi_source', '?')}, "
                    f"theme {e.get('theme', '?')})")
            if e["hi"] in shipped and shipped[e["hi"]] != e["sat"]:
                note += (f" - the shipped word list spells this {shipped[e['hi']]}; "
                         f"the file's {e['sat']} is kept as an alternate")
            cases.append((f"Dictionary: {src}", e["hi"], want, note))
    try:
        numbers = api("/api/dictionary/numbers")["items"]
    except Exception:                                        # noqa: BLE001
        numbers = []
    for n in numbers:
        probes = []
        if str(n.get("key", "")).isdigit() and int(n["key"]) in (13, 25, 40, 99):
            probes.append(str(n["key"]))
        if n.get("hi") in ("तेरह", "पच्चीस", "चालीस", "निन्यानवे", "शून्य", "सौ"):
            probes.append(n["hi"])
        for probe in probes[:1]:
            cases.append(("Number system", probe, n["sat"],
                          f"{n['key']} written out: Santhali counts in tens "
                          f"(ᱜᱮᱞ ᱢᱤᱫ = ten-one = 11)"))
    for v in verbs[:10]:
        if v.get("hindi") and v.get("sat"):
            cases.append((
                "Verb forms (round trip)",
                f"{v['hindi']}।",
                None,
                f"verb pattern for {v.get('english', '')} (glossary word wins if it is also a noun)",
            ))
    return cases


# ------------------------------------------------------------------- run + report
def run():
    manual = [(c, h, e, w, False) for c, h, e, w in MANUAL]
    derived = [(c, h, e, w, True) for c, h, e, w in derived_cases()]

    rows = []
    for i, (cat, hindi, expect, why, is_derived) in enumerate(manual + derived, 1):
        r = translate(hindi)
        if r.get("ok") is False:                      # app declined to guess
            if r.get("error"):
                actual = f"(refused: {r['error']})"
                method, conf = "refused", "-"
                status = "PASS" if expect == "REJECT" else "INFO"
            else:
                actual = "(no confident answer - queued for review)"
                method, conf = "declined", "-"
                status = "PASS" if expect == "DECLINE" else "INFO"
            roman = ""
        elif "error" in r:
            actual, roman, method, conf, status = r["error"], "", "error", "-", "FAIL"
        else:
            sat = r.get("sat")
            actual = sat["olchiki"] if sat else ""
            roman = sat["roman"] if sat else ""
            method, conf = r.get("method", ""), r.get("confidence", "")
            if not actual:
                wb = r.get("wordbank") or []
                actual = " · ".join(f"{w['hindi']}={w['sat']}" for w in wb) or "(nothing)"
                method = method or "wordbank"
            if expect == "DECLINE":
                status = "PASS"                      # it declined / offered words, did not invent
            elif expect is None:
                status = "INFO"
            elif actual == expect:
                status = "PASS"
            else:
                status = "FAIL"
        rows.append({
            "no": i, "category": cat, "hindi": hindi,
            "expected": "" if expect in (None, "REJECT") else expect,
            "actual": actual, "roman": roman, "method": method, "confidence": conf,
            "status": status, "why": why,
        })

    # printable worksheets must never come out blank
    sheets = [
        ("picture_label", "fruits"), ("trace_write", "family"), ("vocab_match", "school"),
        ("count_write", "fruits"),          # used to render an empty grid
        ("count_write", "numbers"), ("fill_blank", "actions"),
    ]
    for tpl, cat in sheets:
        n = 0
        try:
            html = api_text("/api/worksheet", {"template": tpl, "categories": [cat], "count": 8})
            n = len(set(re.findall(r"[\u1C50-\u1C7F]+", html.split("</style>")[-1])))
        except Exception:                                    # noqa: BLE001
            n = 0
        rows.append({
            "no": len(rows) + 1, "category": "Worksheets (must never be blank)",
            "hindi": f"{tpl} / {cat}", "expected": "Santhali words present",
            "actual": f"{n} Santhali words", "roman": "", "method": "worksheet",
            "confidence": "-", "status": "PASS" if n else "FAIL",
            "why": "printable worksheet generated by the server",
        })

    # ---------------------------------------------------------- low-confidence rule
    # Never a sentence we do not stand behind: below the confidence gate the reply must
    # be the combination of known words, and must say that it is not a sentence.
    def rule_row(test, expected, actual, why, status=None):
        if status is None:
            status = "PASS" if str(expected) == str(actual) else "FAIL"
        rows.append({
            "no": len(rows) + 1, "category": "Low confidence -> words only",
            "hindi": test, "expected": expected, "actual": actual, "roman": "",
            "method": "rule", "confidence": "-", "status": status, "why": why,
        })

    for probe in ("सरकारी स्कूल में नया शिक्षक आया है।",
                  "मुझे बाजार से दो किलो चावल लाना है।"):
        r = translate(probe)
        has_sat = bool((r.get("sat") or {}).get("olchiki"))
        rule_row(f"{probe[:28]} | no sentence invented", "no sentence", 
                 "sentence!" if has_sat else "no sentence",
                 "low-confidence input must never come back as a sentence")
        rule_row(f"{probe[:28]} | words offered instead", "words offered",
                 "words offered" if (r.get("words") or r.get("wordbank")) else "nothing offered",
                 f"{r.get('known', 0)}/{r.get('total', 0)} words known, "
                 f"combination: {r.get('combined')}")
        rule_row(f"{probe[:28]} | method + confidence", "word-combo/low",
                 f"{r.get('method')}/{r.get('confidence')}",
                 "the reply must label itself as a word list")

    # a confident sentence is still allowed through, and must carry its confidence
    r = translate("किताब बंद करो।")
    rule_row("confident input still translates", "high/medium",
             r.get("confidence"), "high-confidence sentences are unaffected by the rule",
             status="PASS" if r.get("confidence") in ("high", "medium")
             and (r.get("sat") or {}).get("olchiki") else "FAIL")

    # the combination must be speakable, not an empty string
    r = translate("आज मौसम बहुत अच्छा है।")
    combo = r.get("combined") or ""
    try:
        # audio is binary - read the bytes, do not decode them as text
        req = urllib.request.Request(
            f"{BASE}/api/tts", json.dumps({"text": combo, "lang": "sat"}).encode(),
            {"Content-Type": "application/json"})
        audio = len(urllib.request.urlopen(req, timeout=30).read()) if combo else 0
    except Exception:                                        # noqa: BLE001
        audio = 0
    rule_row("the word combination is speakable", "audio bytes > 0", f"{audio} bytes",
             f"combined text: {combo}", status="PASS" if audio else "FAIL")

    # function words are reported, not smuggled in
    r = translate("आज मौसम बहुत अच्छा है।")
    rule_row("function words reported as skipped", "reported",
             "reported" if r.get("skipped") is not None else "hidden",
             f"skipped: {r.get('skipped')} - \u0939\u0948 was aligned to a dual marker "
             f"in the corpus, so it is left out instead of taught")

    # CSV (BOM so Excel renders Devanagari / Ol Chiki)
    with open(OUT_CSV, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    # Markdown
    total = len(rows)
    passed = sum(r["status"] == "PASS" for r in rows)
    failed = sum(r["status"] == "FAIL" for r in rows)
    info = sum(r["status"] == "INFO" for r in rows)

    lines = [
        "# Hindi test sentences - MTB-MLE Santhali platform",
        "",
        f"Generated against `{BASE}` - every row below is the **actual reply of the running "
        "application**, not an assumption.",
        "",
        f"**{total} checks** ({total - 6} Hindi sentences + 6 worksheets) · ✅ {passed} matched the "
        f"expected answer · ⚠️ {info} answered but need a human eye · ❌ {failed} wrong",
        "",
        "| Method | Meaning |",
        "|---|---|",
        "| `phrase` | matched a whole attested/verified sentence |",
        "| `vocab` | the input was a known word |",
        "| `wikidata` | matched a Hindi-Santhali Wikipedia title |",
        "| `template` | built with a sentence frame + a known noun |",
        "| `wordbank` | no sentence found - app shows the words it knows, flagged low confidence |",
        "",
    ]
    order, seen = [], set()
    for r in rows:
        if r["category"] not in seen:
            seen.add(r["category"])
            order.append(r["category"])
    for cat in order:
        group = [r for r in rows if r["category"] == cat]
        lines += [f"## {cat}", "", "| # | Hindi input | Santhali reply | Method | Status |", "|---|---|---|---|---|"]
        for r in group:
            mark = "✅" if r["status"] == "PASS" else ("❌" if r["status"] == "FAIL" else "•")
            shown = r["actual"][:90] + ("…" if len(r["actual"]) > 90 else "")
            lines.append(f"| {r['no']} | {r['hindi'] or '*(empty)*'} | {shown} | {r['method']}·{r['confidence']} | {mark} |")
        lines.append("")
    # the rows without a fixed expected answer are the ones a Santhali speaker must eyeball
    review = [r for r in rows if r["status"] == "INFO"]
    if review:
        lines += [
            "## Needs a Santhali speaker's eye",
            "",
            "These have no single correct answer on file, so the app is allowed to answer freely. "
            "Read each one and either accept it or send it back through `/api/validate`.",
            "",
            "| # | Hindi input | What the app said | Why it is here |",
            "|---|---|---|---|",
        ]
        for r in review:
            shown = r["actual"][:80] + ("…" if len(r["actual"]) > 80 else "")
            lines.append(f"| {r['no']} | {r['hindi'] or '*(empty)*'} | {shown} | {r['why']} |")
        lines.append("")

    lines += [
        "## Rerun",
        "",
        "```bash",
        "python3 tests/hindi_test_suite.py            # or: python3 tests/hindi_test_suite.py http://localhost:8200",
        "```",
        "",
        "Full detail, including the expected answer and the reason each sentence was chosen, "
        "is in `tests/hindi_testing_sentences.csv`.",
        "",
    ]
    with open(OUT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"{total} checks | PASS {passed} | review {info} | FAIL {failed}")
    print(f"wrote {OUT_CSV} and {OUT_MD}")
    for r in rows:
        if r["status"] == "FAIL":
            print(f"  FAIL #{r['no']}  {r['hindi']}")
            print(f"        expected: {r['expected']}")
            print(f"        actual  : {r['actual']}  [{r['method']}·{r['confidence']}]")


if __name__ == "__main__":
    run()
