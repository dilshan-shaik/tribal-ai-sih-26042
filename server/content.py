"""
Educational content generation: flashcards, bilingual worksheets, lesson packs
and assessments - all built from the validated language pack, so a teacher gets
printable mother-tongue material in one click (PS sections 5, 6, 12, 21).
"""
from __future__ import annotations

import html
import random
from typing import Iterable

LESSONS = [
    {"id": "numbers", "emoji": "🔢", "en": "Numbers 1-10", "hi": "गिनती 1-10",
     "categories": ["numbers"], "template": "count_write",
     "instruction_hi": "1 से 10 तक गिनती करो।"},
    {"id": "fruits", "emoji": "🥭", "en": "Fruits", "hi": "फल",
     "categories": ["fruits"], "template": "picture_label",
     "instruction_hi": "आज हम फलों के नाम सीखेंगे।"},
    {"id": "animals", "emoji": "🐘", "en": "Animals", "hi": "जानवर",
     "categories": ["animals", "birds"], "template": "vocab_match",
     "instruction_hi": "आज हम जानवरों के नाम सीखेंगे।"},
    {"id": "colours", "emoji": "🎨", "en": "Colours", "hi": "रंग",
     "categories": ["colours"], "template": "vocab_match",
     "instruction_hi": "आज हम रंग सीखेंगे।"},
    {"id": "body", "emoji": "🖐️", "en": "Body parts", "hi": "शरीर के अंग",
     "categories": ["body"], "template": "picture_label",
     "instruction_hi": "आज हम शरीर के अंग सीखेंगे।"},
    {"id": "family", "emoji": "👨‍👩‍👧", "en": "Family", "hi": "परिवार",
     "categories": ["family"], "template": "vocab_match",
     "instruction_hi": "आज हम परिवार के नाम सीखेंगे।"},
    {"id": "school", "emoji": "🏫", "en": "In the classroom", "hi": "कक्षा में",
     "categories": ["school"], "template": "picture_label",
     "instruction_hi": "किताब खोलो।"},
    {"id": "food", "emoji": "🍚", "en": "Food & water", "hi": "खाना-पानी",
     "categories": ["food"], "template": "picture_label",
     "instruction_hi": "पानी पीना ज़रूरी है।"},
    {"id": "nature", "emoji": "🌳", "en": "Nature around us", "hi": "आस-पास की प्रकृति",
     "categories": ["nature"], "template": "vocab_match",
     "instruction_hi": "यह एक पेड़ है।"},
    {"id": "actions", "emoji": "🏃", "en": "Action words", "hi": "क्रिया शब्द",
     "categories": ["actions"], "template": "fill_blank",
     "instruction_hi": "मेरे बाद दोहराओ।"},
]


def _by_category(vocab: list[dict], categories: Iterable[str]) -> list[dict]:
    cats = set(categories)
    return [v for v in vocab if v.get("sat") and v["category"] in cats]


def flashcards(vocab: list[dict], category: str | None = None, count: int = 12,
               shuffle: bool = False, only_verified: bool = False) -> dict:
    items = [v for v in vocab if v.get("sat")]
    if category and category != "all":
        items = [v for v in items if v["category"] == category]
    if only_verified:
        items = [v for v in items if v.get("verified")]
    if shuffle:
        random.shuffle(items)
    items = items[:count]
    return {"count": len(items), "cards": [
        {"hindi": v["hindi"], "english": v["english"], "sat": v["sat"],
         "sat_deva": v["sat_deva"], "sat_roman": v["sat_roman"],
         "category": v["category"], "emoji": v.get("emoji"),
         "confidence": v["confidence"], "verified": v.get("verified", False),
         "audio": {"hi": v["hindi"], "sat": v["sat"]}}
        for v in items]}


CSS = """
:root{--ink:#12203a;--muted:#5b6b86;--line:#d9e0ee;--accent:#6d28d9}
*{box-sizing:border-box}
body{font-family:'Noto Sans','Segoe UI',system-ui,'Noto Sans Devanagari',sans-serif;
     color:var(--ink);margin:0;padding:26px 30px;background:#fff;line-height:1.5}
h1{font-size:24px;margin:0 0 2px}
.sub{color:var(--muted);font-size:13px;margin-bottom:16px}
.school{display:flex;justify-content:space-between;font-size:12px;color:var(--muted);
        border-bottom:2px solid var(--ink);padding-bottom:8px;margin-bottom:18px}
.grid{display:grid;grid-template-columns:repeat(2,1fr);gap:14px}
.grid.g3{grid-template-columns:repeat(3,1fr)}
.cell{border:1.5px solid var(--line);border-radius:12px;padding:12px 14px;min-height:96px}
.cell .emoji{font-size:30px;line-height:1}
.hi{font-size:20px;font-weight:600;margin-top:6px}
.sat{font-size:22px;color:var(--accent);margin-top:2px;font-family:'Noto Sans Ol Chiki',sans-serif}
.roman{font-size:12px;color:var(--muted);letter-spacing:.3px}
.dots{border-bottom:2px dotted #9aa7bd;height:30px;margin-top:8px}
table{width:100%;border-collapse:collapse;margin-top:6px}
th,td{border:1px solid var(--line);padding:10px;font-size:15px;text-align:left}
th{background:#f3f5fb;font-size:12px;text-transform:uppercase;letter-spacing:.5px;color:var(--muted)}
.big{font-size:30px;letter-spacing:10px;color:var(--accent)}
.bank{border:1.5px dashed var(--accent);border-radius:12px;padding:12px;margin-top:14px}
.bank b{font-size:12px;text-transform:uppercase;color:var(--muted);letter-spacing:.6px}
.chip{display:inline-block;border:1.5px solid var(--line);border-radius:999px;
      padding:5px 12px;margin:5px 6px 0 0;font-size:17px}
.q{margin:14px 0;font-size:17px}
.opts{display:flex;gap:10px;flex-wrap:wrap;margin-top:6px}
.opt{border:1.5px solid var(--line);border-radius:10px;padding:7px 14px;min-width:110px}
footer{margin-top:22px;border-top:1px dashed var(--line);padding-top:10px;
       font-size:11px;color:var(--muted);display:flex;justify-content:space-between}
@media print{body{padding:10mm}.noprint{display:none}}
@page{margin:12mm}
"""


def _head(title_en: str, title_hi: str, teacher: str, school: str) -> str:
    return f"""<div class="school"><span>{html.escape(school or 'Government Primary School')}</span>
<span>Class / कक्षा: ______ &nbsp; Date / दिनांक: __________</span></div>
<h1>{html.escape(title_en)} <span style="color:#6d28d9">/ {html.escape(title_hi)}</span></h1>
<div class="sub">Teacher / शिक्षक: {html.escape(teacher or '____________')} &nbsp;•&nbsp;
Name / नाम: ______________________________</div>"""


def _foot(meta: dict) -> str:
    return (f'<footer><span>🪶 पलाश MTB-MLE • Generated by AI-Assisted Multilingual Education '
            f'Platform (SIH 26046 prototype)</span><span>Hindi → {meta.get("language","Santhali")} '
            f'(Ol Chiki) • {meta.get("generated","")}</span></footer>')


def worksheet_html(spec: dict, vocab: list[dict], meta: dict) -> str:
    """spec = {template, title_en, title_hi, categories[], count, teacher, school, words[]}"""
    tpl = spec.get("template", "picture_label")
    cats = spec.get("categories") or ["fruits"]
    words = spec.get("words") or []
    items = [v for v in vocab if v.get("sat") and (v["hindi"] in words or (not words and v["category"] in cats))]
    items = items[: spec.get("count", 8)]
    title_en = spec.get("title_en") or "Bilingual Worksheet"
    title_hi = spec.get("title_hi") or "द्विभाषी कार्यपत्रक"
    head = _head(title_en, title_hi, spec.get("teacher", ""), spec.get("school", ""))
    body = ""

    if tpl == "picture_label":
        cells = "".join(
            f'<div class="cell"><div class="emoji">{v.get("emoji","")}</div>'
            f'<div class="hi">{v["hindi"]}</div><div class="dots"></div>'
            f'<div class="roman" style="margin-top:6px">Santhali / संताली लिखो:</div></div>'
            for v in items)
        body = (f'<div class="sub" style="margin:14px 0 6px">चित्र देखो, हिन्दी पढ़ो और संताली (Ol Chiki) '
                f'में नाम लिखो। Look at the picture, read the Hindi word and write the Santhali word.</div>'
                f'<div class="grid">{cells}</div>')

    elif tpl == "trace_write":
        rows = "".join(
            f'<tr><td style="font-size:22px">{v.get("emoji","")} {v["hindi"]}</td>'
            f'<td class="sat">{v["sat"]}</td>'
            f'<td style="color:#9aa7bd;font-size:19px">{v["sat_roman"]}</td>'
            f'<td class="dots" style="height:22px"></td></tr>'
            for v in items)
        body = ('<div class="sub" style="margin:14px 0 6px">संताली शब्द पढ़ो, रोमन उच्चारण देखो और '
                'दो बार लिखो। Read the Santhali word, look at the pronunciation, write it twice.</div>'
                '<table><tr><th>हिन्दी / Picture</th><th>संताली (Ol Chiki)</th>'
                '<th>Pronunciation</th><th>Write here</th></tr>' + rows + '</table>')

    elif tpl == "vocab_match":
        left = [f'<div class="cell" style="min-height:56px"><b>{v["hindi"]}</b> '
                f'<span style="font-size:20px">{v.get("emoji","")}</span></div>' for v in items]
        right = [f'<div class="cell" style="min-height:56px"><span class="sat">{v["sat"]}</span></div>'
                 for v in random.sample(items, len(items))]
        body = ('<div class="sub" style="margin:14px 0 6px">हिन्दी शब्द को संताली शब्द से मिलाओ। '
                'Match the Hindi word with the Santhali word (draw a line).</div>'
                '<div class="grid"><div>' + "".join(left) + '</div><div>' + "".join(right) + '</div></div>')

    elif tpl == "count_write":
        nums = [v for v in items if v["category"] == "numbers"][:10]
        if not nums:
            # "Count and write" was picked while the category is something else
            # (e.g. fruits, the default). Fall back to the number words so the
            # sheet is never an empty grid, and let the word bank match.
            nums = [v for v in vocab if v.get("sat") and v["category"] == "numbers"][:10]
            items = nums
        boxes = "".join(f'<div class="cell" style="text-align:center"><div class="big">{i+1}</div>'
                        f'<div class="roman" style="margin-top:4px">{"{}".format(n["hindi"])}</div>'
                        f'<div class="dots"></div></div>'
                        for i, n in enumerate(nums))
        dots = " ".join(str(i) for i in range(1, 11))
        body = (f'<div class="sub" style="margin:14px 0 6px">गिनती बोलो और संताली में लिखो। '
                f'Count aloud and write the Santhali number word.</div>'
                f'<div class="grid g3">{boxes}</div>'
                f'<div class="bank"><b>Count and write / गिनो और लिखो</b>'
                f'<div class="big" style="font-size:22px;letter-spacing:6px">{dots}</div>'
                f'<div style="margin-top:8px">1 से 10 तक गिनती करो → ᱢᱤᱫ, ᱵᱟᱨ, ᱯᱮ ...</div></div>')

    elif tpl == "fill_blank":
        rows = ""
        for v in items:
            rows += (f'<div class="q">____ {v["hindi"]} ____ '
                     f'<span style="color:#5b6b86;font-size:13px">({v["english"]})</span>'
                     f'<div class="opts"><span class="opt sat">{v["sat"]}</span>'
                     f'<span class="opt sat">{random.choice(items)["sat"]}</span>'
                     f'<span class="opt sat">{random.choice(items)["sat"]}</span></div></div>')
        body = ('<div class="sub" style="margin:14px 0 6px">सही संताली शब्द पर गोला लगाओ। '
                'Circle the correct Santhali word.</div>' + rows)

    wordbank = "".join(f'<span class="chip">{v["hindi"]} • <b class="sat">{v["sat"]}</b></span>'
                       for v in items)
    bank = (f'<div class="bank"><b>Word bank / शब्द भंडार</b><div>{wordbank}</div></div>'
            if tpl in ("picture_label", "trace_write", "count_write") else "")

    return (f'<!doctype html><html lang="hi"><head><meta charset="utf-8">'
            f'<title>{html.escape(title_en)} / {html.escape(title_hi)}</title>'
            f'<style>{CSS}</style></head><body>{head}{body}{bank}{_foot(meta)}</body></html>')


def quiz(vocab: list[dict], category: str | None = None, count: int = 5) -> dict:
    """Mother-tongue comprehension check: Santhali word -> pick the picture/meaning."""
    items = [v for v in vocab if v.get("sat")]
    if category and category != "all":
        items = [v for v in items if v["category"] == category]
    random.shuffle(items)
    qs = []
    for v in items[:count]:
        pool = random.sample([x for x in items if x["hindi"] != v["hindi"]], min(2, len(items) - 1))
        opts = [{"emoji": v.get("emoji"), "hindi": v["hindi"], "correct": True}]
        opts += [{"emoji": o.get("emoji"), "hindi": o["hindi"], "correct": False} for o in pool]
        random.shuffle(opts)
        qs.append({"prompt_sat": v["sat"], "prompt_deva": v["sat_deva"],
                   "prompt_roman": v["sat_roman"], "answer": v["hindi"],
                   "answer_english": v["english"], "audio_text": v["sat"], "options": opts})
    return {"count": len(qs), "questions": qs}
