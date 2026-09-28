"""
PDF translation: read a PDF, translate it into Santhali, and hand back something a
teacher can print.

Why it is built this way
------------------------
* Text is pulled out with `pypdf` (pure Python, no system libraries), so the same code
  runs on a school laptop that has nothing installed but Python.
* Each paragraph is translated with the same engine the rest of the app uses, so every
  line carries the method and confidence it was produced with - a PDF does not get a
  free pass just because it is a PDF.
* A scanned PDF has no text layer. We say so instead of pretending, and point at the
  voice translator, which can read a page aloud through the microphone.
* Nothing is invented. If a paragraph cannot be translated, the teacher gets the
  word-by-word rendering plus a % of how much of it we actually know.
"""
from __future__ import annotations

import re

try:
    from pypdf import PdfReader
except Exception:                                            # noqa: BLE001
    PdfReader = None

# a line that is only a page number / roman numeral / decorative rule
PAGE_NOISE = re.compile(r"^\s*(?:[ivxlcdm]{1,7}|\d{1,4}|[-\u2013\u2014_*.\u2022]{2,})\s*$", re.I)
WINDOWS = "\ufeff\u200b\u00a0"

# methods that mean "we produced a whole sentence", not just words
FULL = {"sentence-memory-en", "sentence-memory-en-fuzzy","phrase", "vocab", "dictionary", "number", "template", "en-memory",
        "odia-direct", "wikidata", "sentence-memory", "already-santhali"}

METHOD_LABEL = {
    "phrase": "phrase book", "vocab": "word list", "dictionary": "dictionary",
    "number": "number system", "en-memory": "English sentence memory",
    "odia-direct": "Odia memory", "template": "sentence frame",
    "wikidata": "name memory", "already-santhali": "already Santhali",
    "words-only": "words only",
}


def available() -> bool:
    return PdfReader is not None


def extract(path: str, max_pages: int = 10):
    """Return (pages, info). pages = list of {page, text, chars}."""
    if PdfReader is None:
        raise RuntimeError("pypdf is not installed - run: pip install pypdf")
    reader = PdfReader(path)
    total = len(reader.pages)
    pages = []
    for i, page in enumerate(reader.pages[:max_pages], 1):
        try:
            text = page.extract_text() or ""
        except Exception:                                    # noqa: BLE001
            text = ""
        for ch in WINDOWS:
            text = text.replace(ch, " ")
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        pages.append({"page": i, "text": text.strip(), "chars": len(text.strip())})
    info = {
        "pages_total": total,
        "pages_read": len(pages),
        "truncated": total > max_pages,
        "chars": sum(p["chars"] for p in pages),
        "has_text_layer": sum(p["chars"] for p in pages) > 40,
    }
    return pages, info


def blocks(page_text: str):
    """Split a page into paragraphs, joining lines that were wrapped by the layout."""
    out, buf = [], []

    def flush():
        if not buf:
            return
        joined = " ".join(buf).strip()
        buf.clear()
        if len(joined) >= 2 and not PAGE_NOISE.match(joined):
            out.append(re.sub(r"\s+", " ", joined))

    for raw in (page_text or "").split("\n"):
        line = raw.strip()
        if not line:
            flush()
            continue
        if PAGE_NOISE.match(line):
            flush()
            continue
        buf.append(line)
        if line.endswith((".", "!", "?", "\u0964", "\u0965", ":")):
            flush()
    flush()
    return out


def detect_lang(text: str) -> str:
    """Which side of the app should handle this block."""
    deva = sum(1 for c in text if "\u0900" <= c <= "\u097F")
    ol = sum(1 for c in text if "\u1C50" <= c <= "\u1C7F")
    odia = sum(1 for c in text if "\u0B00" <= c <= "\u0B7F")
    latin = sum(1 for c in text if c.isascii() and c.isalpha())
    if ol:
        return "sat"                      # already Santhali
    if odia and odia > deva:
        return "or"
    if deva:
        return "hi"
    if latin:
        return "en"
    return "unknown"


def gloss(text: str, lookup):
    """Word-by-word rendering.

    `lookup(word)` returns either a Santhali string, or (santhali, needs_check).
    Returns (rendering, [{word, sat, check}], coverage, words_flagged).
    Coverage counts every word in the text, so it cannot flatter itself by quietly
    dropping the words it does not know.
    """
    words = re.findall(r"[\w\u0900-\u097F\u0B00-\u0B7F']+", text)
    if not words:
        return "", [], 0.0, 0
    out, bank, known, flagged = [], [], 0, 0
    for w in words:
        got = lookup(w)
        sat, check = got if isinstance(got, tuple) else (got, False)
        if not sat:
            continue
        known += 1
        flagged += 1 if check else 0
        out.append(sat)
        bank.append({"word": w, "sat": sat, "check": bool(check)})
    return " ".join(out), bank, known / len(words), flagged


def split_sentences(text: str):
    """Split a paragraph into sentences, keeping the terminator (। . ! ?)."""
    parts = re.split(r"(?<=[\u0964\u0965.!?])\s+", text or "")
    return [p.strip() for p in parts if p and p.strip()]


def sentence_of(res: dict):
    """The delivered sentence, whichever pack shape it came in (sat or target)."""
    if res.get("ok"):
        if res.get("sat"):
            return res["sat"].get("olchiki"), res["sat"].get("roman")
        if res.get("target"):
            return res["target"].get("text"), res["target"].get("roman")
    return None, None


def translate_document(engine, path: str, max_pages: int = 5, filename: str = "",
                       target: str = "sat"):
    """Read the PDF, translate it paragraph by paragraph, and report honestly.

    A paragraph that cannot be translated as a whole is split into sentences and each
    sentence is tried on its own, because the phrase book and the sentence memory work
    at sentence level. Whatever is still left over is reported as words only.
    """
    pages, info = extract(path, max_pages=max_pages)
    rows, stats = [], {"blocks": 0, "translated": 0, "words_only": 0,
                       "sat_words": 0, "chars": info["chars"]}

    is_pack = hasattr(engine, "code")          # a Mundari / Ho pack, not the Santhali engine

    def try_translate(text: str):
        lang = detect_lang(text)
        if is_pack:
            # these languages are English-facing: English gets a real sentence,
            # Hindi arrives as words through the English pivot (never a sentence)
            if lang in ("hi", "en"):
                return engine.translate(text, source=lang)
            return {"ok": False}
        if lang == "sat":
            return {"ok": True, "method": "already-santhali", "confidence": "high",
                    "sat": {"olchiki": text, "roman": None}}
        if lang == "hi":
            return engine.translate(text, source="hi")
        if lang == "en":
            return engine.english_to_santhali(text)
        if lang == "or":
            return engine.odia_direct(text)
        return {"ok": False}

    def add(text: str, res: dict, page_no: int):
        sent, roman = sentence_of(res)
        if sent and res.get("method") in FULL:
            rows.append({"page": page_no, "src": text, "lang": detect_lang(text),
                         "sat": sent, "roman": roman,
                         "method": res["method"], "confidence": res.get("confidence", "-"),
                         "coverage": None, "words": [], "gloss": None})
            stats["translated"] += 1
        else:
            lang = detect_lang(text)
            g, bank, cov, flagged = gloss(text, engine.lookup_any)
            rows.append({"page": page_no, "src": text, "lang": lang, "sat": None,
                         "roman": None, "method": "words-only",
                         "confidence": "high" if cov >= 0.8 else "medium" if cov else "low",
                         "coverage": round(cov, 3), "words": bank, "gloss": g,
                         "check_words": flagged})
            stats["words_only"] += 1
            stats["sat_words"] += len(bank)
        stats["blocks"] += 1

    for page in pages:
        for para in blocks(page["text"]):
            if detect_lang(para) == "unknown":
                continue
            res = try_translate(para)
            if sentence_of(res)[0] and res.get("method") in FULL:
                add(para, res, page["page"])
                continue
            # sentence by sentence: the phrase book and the memories work at that level
            sents = split_sentences(para)
            if len(sents) > 1:
                leftover = []
                for s in sents:
                    r = try_translate(s)
                    if sentence_of(r)[0] and r.get("method") in FULL:
                        if leftover:
                            add(" ".join(leftover), {"ok": False}, page["page"])
                            leftover = []
                        add(s, r, page["page"])
                    else:
                        leftover.append(s)
                if leftover:
                    add(" ".join(leftover), {"ok": False}, page["page"])
            else:
                add(para, res, page["page"])

    return {"ok": True, "filename": filename or path.split("/")[-1], "info": info,
            "blocks": rows, "stats": stats}


def esc(s) -> str:
    return str(s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def report_html(doc: dict, meta: dict) -> str:
    """A printable bilingual copy of the PDF: original paragraph, Santhali, method."""
    st = doc.get("stats") or {}
    info = doc.get("info") or {}
    tot = max(1, st.get("blocks", 1))
    pct = int(round(100 * st.get("translated", 0) / tot))

    rows = []
    for b in doc.get("blocks") or []:
        label = METHOD_LABEL.get(b.get("method"), b.get("method") or "")
        if b.get("sat"):
            body = ('<div class="sat">' + esc(b["sat"]) + "</div>"
                    '<div class="roman">' + esc(b.get("roman") or "") + "</div>")
        else:
            cov = int(round((b.get("coverage") or 0) * 100))
            words = " &middot; ".join(
                esc(w["word"]) + ' = <span class="sat">' + esc(w["sat"]) + "</span>"
                + (' <span class="chk">?</span>' if w.get("check") else "")
                for w in (b.get("words") or []))
            if b.get("check_words"):
                words += ('<div class="muted">' + str(b["check_words"])
                          + " word(s) marked <span class=\"chk\">?</span> come from "
                          "automatic alignment &mdash; please check them with a speaker.</div>")
            body = ('<div class="muted">Not translated as a sentence &mdash; ' + str(cov)
                    + '% of its words are known. Read it aloud with these:</div>'
                    '<div class="words">' + (words or "&mdash;") + "</div>")
        rows.append('<tr><td class="pg">' + str(b.get("page")) + "</td>"
                    '<td class="src">' + esc(b.get("src")) + "</td>"
                    '<td class="out">' + body + '<div class="badge">' + esc(label)
                    + "</div></td></tr>")

    pages_note = str(info.get("pages_read", 0)) + " pages read"
    if info.get("truncated"):
        pages_note += " of " + str(info.get("pages_total"))

    return (
        '<!doctype html>\n<html lang="hi"><head><meta charset="utf-8">\n'
        "<title>" + esc(doc.get("filename") or "PDF") + " \u2014 Santhali</title>\n"
        "<style>\n"
        "  @page { size: A4; margin: 12mm; }\n"
        '  body { font-family: "Noto Sans", system-ui, sans-serif; color: #16223a; margin: 0; }\n'
        "  h1 { font-size: 19px; margin: 0 0 2px; }\n"
        "  .sub { color: #5b6b8c; font-size: 12px; margin-bottom: 10px; }\n"
        "  .stat { display: flex; gap: 16px; flex-wrap: wrap; font-size: 12px; margin-bottom: 12px; }\n"
        "  .stat b { font-size: 15px; }\n"
        "  table { width: 100%; border-collapse: collapse; }\n"
        "  td, th { border: 1px solid #cdd6e5; padding: 7px 8px; vertical-align: top; }\n"
        "  th { background: #eef2fb; font-size: 12px; text-align: left; }\n"
        "  .pg { width: 26px; text-align: center; color: #7c8aa6; }\n"
        "  .src { width: 44%; font-size: 13px; }\n"
        "  .out { font-size: 14px; }\n"
        '  .sat { font-family: "Noto Sans Ol Chiki", "Noto Sans", system-ui, sans-serif;\n'
        "         font-size: 17px; line-height: 1.55; }\n"
        "  .roman { color: #5b6b8c; font-size: 11px; margin-top: 3px; }\n"
        "  .words { font-size: 12.5px; margin-top: 4px; }\n"
        "  .badge { display: inline-block; margin-top: 6px; font-size: 10px; color: #3b4a68;\n"
        "           background: #eef2fb; border-radius: 999px; padding: 2px 8px; }\n"
        "  .muted { color: #7c8aa6; font-size: 11.5px; }\n"
        "  .chk { color: #b45309; font-weight: 700; }\n"
        "  .note { margin-top: 14px; font-size: 11px; color: #5b6b8c; }\n"
        "  .toolbar { margin: 10px 0 14px; }\n"
        "  button { font: inherit; padding: 8px 14px; border: 0; border-radius: 10px;\n"
        "           background: #2f4b8f; color: #fff; cursor: pointer; }\n"
        "  @media print { .toolbar { display: none; } }\n"
        "</style></head>\n<body>\n"
        "<h1>PDF &rarr; \u0938\u0902\u0924\u093e\u0932\u0940 &middot; " + esc(doc.get("filename")) + "</h1>\n"
        '<div class="sub">' + esc(meta.get("school", "")) + " " + esc(meta.get("teacher", ""))
        + " &middot; " + pages_note + " &middot; bilingual page, Santhali in Ol Chiki</div>\n"
        '<div class="stat"><span><b>' + str(st.get("blocks", 0)) + "</b> paragraphs</span>"
        "<span><b>" + str(st.get("translated", 0)) + "</b> translated as a sentence</span>"
        "<span><b>" + str(st.get("words_only", 0)) + "</b> word-by-word</span>"
        "<span><b>" + str(pct) + "%</b> full coverage</span></div>\n"
        '<div class="toolbar"><button onclick="window.print()">\U0001F5A8\uFE0F Print / Save as PDF</button></div>\n'
        '<table><thead><tr><th>pg</th><th>original</th><th>\u1C65\u1C6E\u1C71\u1C5B\u1C5A\u1C79 '
        "/ Santhali</th></tr></thead><tbody>"
        + "".join(rows) + "</tbody></table>\n"
        '<div class="note">Machine-assisted translation. Please read it once before it goes on a '
        "worksheet &mdash; anything marked &ldquo;words only&rdquo; needs your own sentence.</div>\n"
        "</body></html>"
    )


def bilingual_text(doc: dict) -> str:
    """Plain-text download: original line, then the Santhali underneath."""
    st = doc.get("stats") or {}
    out = ["PDF: " + str(doc.get("filename")),
           "paragraphs: " + str(st.get("blocks")) + " | translated: "
           + str(st.get("translated")) + " | word-by-word: " + str(st.get("words_only")),
           "", ("=" * 60), ""]
    for b in doc.get("blocks") or []:
        out.append("[page " + str(b.get("page")) + "] " + str(b.get("src")))
        if b.get("sat"):
            out.append("-> " + b["sat"])
            if b.get("roman"):
                out.append("   (" + b["roman"] + ")")
        else:
            bank = " | ".join(w["word"] + "=" + w["sat"] for w in (b.get("words") or []))
            out.append("-> (words only) " + (bank or "-"))
        out.append("")
    return "\n".join(out)
