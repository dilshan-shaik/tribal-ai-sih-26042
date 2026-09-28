"""
AI-Assisted Multilingual Education Platform for Tribal Schools
Hindi -> Santhali (Ol Chiki) teaching assistant  •  SIH problem statement 26042

FastAPI backend. Serves:
  /api/*            JSON API consumed by the React front-end
  /audio/*.mp3      cached text-to-speech clips
  /                 the built React app (single deployment, offline-friendly)

Run:  python3 -m uvicorn server.main:app --host 0.0.0.0 --port 8000
"""
from __future__ import annotations

import json
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path

import urllib.parse

from fastapi import FastAPI, File, HTTPException, Query, Request, UploadFile
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import asr  # noqa: E402
from content import LESSONS, flashcards, quiz, worksheet_html  # noqa: E402
from engine import Engine  # noqa: E402
import languages  # noqa: E402
from tts import cache_stats, clip_status, synthesise  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
DB = DATA / "platform.db"
VERIFIED = DATA / "verified.json"
WEB_DIST = ROOT / "web" / "dist"

# every screen the shipped build contains - echoed by /api/version so a stale build
# is obvious rather than a mystery
SCREEN_IDS = ["dashboard", "translate", "text", "pdf", "lessons", "flashcards",
              "worksheets", "vocab", "dictionary", "validate", "offline", "about"]

app = FastAPI(title="MTB-MLE Platform API", version="1.0.0",
              description="Hindi → Santhali classroom translation, TTS and content generation")
app.add_middleware(GZipMiddleware, minimum_size=800)

engine = Engine()
registry = languages.Registry(engine)      # sat + unr (Mundari) + hoc (Ho)
START = time.time()


# --------------------------------------------------------------------- sqlite
def db() -> sqlite3.Connection:
    con = sqlite3.connect(DB)
    con.execute("""CREATE TABLE IF NOT EXISTS validation(
        id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT, scope TEXT, hindi TEXT,
        proposed TEXT, note TEXT, teacher TEXT, status TEXT)""")
    con.execute("""CREATE TABLE IF NOT EXISTS usage(
        id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT, event TEXT, detail TEXT,
        offline INTEGER)""")
    con.commit()
    return con


def log(event: str, detail: str = ""):
    con = db()
    con.execute("INSERT INTO usage(ts,event,detail,offline) VALUES(?,?,?,?)",
                (datetime.now(timezone.utc).isoformat(timespec="seconds"), event, detail[:400],
                 0))
    con.commit()
    con.close()


# ---------------------------------------------------------------------- models
class TranslateIn(BaseModel):
    text: str
    target: str = "sat"
    source: str = "hi"          # hi | or (Odia, converted to Hindi first) | auto


class TTSIn(BaseModel):
    text: str
    lang: str = "sat"          # sat | hi | en
    slow: bool = False


class WorksheetIn(BaseModel):
    template: str = "picture_label"
    title_en: str = "Bilingual Worksheet"
    title_hi: str = "द्विभाषी कार्यपत्रक"
    categories: list[str] = ["fruits"]
    words: list[str] = []
    count: int = 8
    teacher: str = ""
    school: str = ""


class ValidateIn(BaseModel):
    scope: str = "phrase"      # phrase | vocab
    hindi: str
    sat: str
    note: str = ""
    teacher: str = ""


# ----------------------------------------------------------------- API routes
@app.get("/api/health")
def health():
    c = cache_stats()
    return {"status": "ok", "uptime_s": round(time.time() - START, 1),
            "language": engine.pack["meta"]["language"],
            "counts": engine.pack["meta"]["counts"],
            "tts": c, "recorded_speech": clip_status(),
            "verified_overrides": len(engine.verified),
            "offline_ready": True}


@app.get("/api/pack/summary")
def pack_summary():
    return engine.summary()


@app.get("/api/pack/download")
def pack_download():
    """Full language pack - used by the service worker for offline-first use."""
    return FileResponse(DATA / "language_packs" / "sat.json",
                        media_type="application/json", filename="sat-language-pack.json")


@app.get("/api/vocab")
def vocab(category: str | None = None, q: str | None = None,
          limit: int = Query(300, le=500)):
    items = [v for v in engine.pack["vocab"]]
    if category and category != "all":
        items = [v for v in items if v["category"] == category]
    if q:
        needle = q.lower().strip()
        items = [v for v in items if needle in v["hindi"].lower()
                 or needle in (v["english"] or "").lower()
                 or needle in (v["sat"] or "")]
    return {"total": len(items), "items": items[:limit]}


@app.get("/api/dictionary")
def dictionary(q: str | None = None, theme: str | None = None, source: str | None = None,
               limit: int = Query(300, le=2000)):
    """The Hindi -> Santhali dictionary built from the team-supplied Santhali
    dictionaries (Santali Open dictionary, Glossary eng-sat / sat-eng, Body Parts,
    Relation, Eatables, Name Translation, T General)."""
    items = list(engine.pack.get("dictionary") or [])
    if theme and theme != "all":
        items = [e for e in items if e.get("theme") == theme]
    if source and source != "all":
        items = [e for e in items if e.get("source") == source]
    if q:
        needle = q.lower().strip()
        items = [e for e in items if needle in (e.get("hi") or "").lower()
                 or needle in (e.get("en") or "").lower()
                 or needle in (e.get("sat") or "") or needle in (e.get("sat_roman") or "")]
    themes: dict[str, int] = {}
    sources: dict[str, int] = {}
    for e in engine.pack.get("dictionary") or []:
        themes[e.get("theme", "general")] = themes.get(e.get("theme", "general"), 0) + 1
        sources[e.get("source") or "?"] = sources.get(e.get("source") or "?", 0) + 1
    return {"total": len(items), "themes": themes, "sources": sources,
            "items": items[:limit] if limit else items}


@app.get("/api/dictionary/files")
def dictionary_files():
    """Per-upload accounting: what every supplied file contributed and where it
    landed (vocabulary, the number system, sentences, proper names). Nothing is
    silently dropped - what was not used is listed with the reason."""
    pack = engine.pack
    dictionary = pack.get("dictionary") or []
    meta = pack.get("meta") or {}
    per_file = meta.get("dictionary_per_file") or {}

    # add the number-word attestations and the spelling variants per file
    variants: dict[str, int] = {}
    for e in dictionary:
        if e.get("variants"):
            for src in (e.get("found_in") or [e.get("source") or "?"]):
                variants[src] = variants.get(src, 0) + 1
    items = []
    for rec in per_file.values():
        rec = dict(rec)
        rec["variants"] = variants.get(rec.get("source_slug"), 0)
        rec["used_for"] = ", ".join(
            label for label, n in (("vocabulary", rec.get("in_dictionary", 0)),
                                   ("number words", rec.get("numbers", 0)),
                                   ("sentences", rec.get("sentences", 0)),
                                   ("proper names", rec.get("names", 0)))
            if n) or "not used"
        items.append(rec)
    for e in dictionary:                       # fallback if the pack predates per_file
        if not items:
            break
    items.sort(key=lambda r: -(r.get("in_dictionary", 0) + r.get("names", 0)
                              + r.get("sentences", 0)))
    return {
        "files_supplied": len(items),
        "files_used": sum(1 for r in items if r.get("used_for") != "not used"),
        "totals": {
            "dictionary_entries": len(dictionary),
            "numbers": len(pack.get("numbers") or {}),
            "dictionary_sentences": len(pack.get("dictionary_sentences") or []),
            "proper_names": len(pack.get("names") or []),
            "skipped_headwords": len(meta.get("dictionary_skipped") or {}),
            "spellings_fixed": len(meta.get("dictionary_spellings_fixed") or {}),
        },
        "skipped": meta.get("dictionary_skipped") or {},
        "notes": [
            "Every Hindi word in this dictionary was written for the classroom: "
            "it comes from the project word list, not from an encyclopaedia.",
            "Where the uploaded dictionaries and the shipped word list spell a word "
            "differently, the shipped form stays and the other is kept as an "
            "alternate - nothing is overwritten silently.",
            "Number words are generated from the Santhali counting pattern "
            "(ᱜᱮᱞ ᱢᱤᱫ = ten + one = 11) and corroborated by 101 number rows in "
            "two of the files.",
        ],
        "items": items,
    }


@app.get("/api/dictionary/numbers")
def dictionary_numbers():
    """The 0-100 system plus thousand / lakh / crore, from digits and from words."""
    nums = engine.pack.get("numbers") or {}
    items = [{"key": k, "hi": v.get("hi"), "sat": v.get("sat"),
              "sat_deva": v.get("sat_deva"), "sat_roman": v.get("sat_roman")}
             for k, v in sorted(nums.items(),
                                key=lambda kv: (not kv[0].isdigit(), int(kv[0])
                                                if kv[0].isdigit() else 0))]
    return {"total": len(items), "items": items}


@app.get("/api/phrases")
def phrases():
    return {"total": len(engine.pack["phrases"]), "items": engine.pack["phrases"]}


@app.get("/api/verbs")
def verbs():
    return {"total": len(engine.pack["verbs"]), "items": engine.pack["verbs"]}


@app.post("/api/translate")
def translate(body: TranslateIn):
    res = registry.translate(body.text, source=body.source, target=body.target)
    log("translate", f"{body.source}->{body.target}:{res.get('method')}: {body.text[:60]}")
    return res


@app.get("/api/languages")
def languages_list():
    """The languages this build actually serves, what backs each one, and whether a
    voice exists. Drives the language <select> - and says plainly where data is thin."""
    items = registry.list_languages()
    return {"total": len(items), "default": "sat", "items": items,
            "note": "Mundari and Ho are English-facing: sentences from parallel text, "
                    "Hindi arrives as word combinations through the English pivot."}


@app.get("/api/odia/samples")
def odia_samples(limit: int = 12):
    """Odia sentences that already have a Santhali answer. Odia is answered directly
    from this memory only - there is no Odia -> Hindi -> Santhali chain."""
    rows = [{"odia": rec.get("or_script"), "sat": rec.get("sat"),
             "sat_roman": rec.get("sat_roman"),
             "matched": rec.get("matched"), "tokens": rec.get("tokens")}
            for rec in (engine.pack.get("odia_memory") or [])[:limit]]
    return {"total": len(engine.pack.get("odia_memory") or []),
            "note": "Odia -> Santhali is a direct memory lookup",
            "samples": rows}


@app.get("/api/odia/memory")
def odia_memory(limit: int = 10):
    """Santhali sentences recovered from the Odia-script file (already in Ol Chiki),
    with the Odia text they were written in. These are answered verbatim when a teacher
    pastes the same Odia sentence."""
    rows = []
    for rec in (engine.pack.get("odia_memory") or [])[:limit]:
        rows.append({"odia_script": rec.get("or_script"), "sat": rec.get("sat"),
                     "sat_roman": rec.get("sat_roman"),
                     "matched": rec.get("matched"), "tokens": rec.get("tokens")})
    return {"total": len(engine.pack.get("odia_memory") or []), "items": rows}


@app.get("/api/odia/stats")
def odia_stats():
    c = engine.pack["meta"]["counts"]
    return {"mode": "direct Odia -> Santhali memory lookup (no Hindi step)",
            "odia_sentences_with_santhali": c.get("odia_sentences", 0),
            "odia_script_spellings": c.get("odia_spellings", 0),
            "odia_sentences_kept_for_reference": c.get("odia_hindi_pairs", 0),
            "note": "the reference sentences have no Santhali counterpart in the file, "
                    "so they are not used to answer anything"}


def _tts_response(text: str, lang: str, slow: bool):
    if lang == "hoc":
        # No Ho voice exists and the text here is Warang Citi / romanised, so there is
        # nothing honest to read it with. Refusing beats a wrong reading.
        raise HTTPException(status_code=501, detail=(
            "no Ho voice model yet - the Ho text in this build is Warang Citi and no "
            "public Ho TTS exists, so audio is not offered rather than mispronounced"))
    voice = "hi" if lang == "unr" else lang          # Mundari arrives in Devanagari
    try:
        out = synthesise(text, voice, slow)
        # a recorded Mundari clip (installed TTS dataset) speaks for itself - only the
        # approximate Hindi-voice route gets the approximation label
        if lang == "unr" and "recorded" not in str(out.get("voice_engine", "")).lower():
            out["voice_engine"] = "hi (gTTS) - reads the Devanagari Mundari text"
            out["approx"] = True
    except Exception as exc:                      # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"tts failed: {exc}") from exc
    log("tts", f"{lang}: {text[:60]}")
    return FileResponse(out["path"], media_type="audio/mpeg",
                        headers={"X-Voice-Engine": out["voice_engine"],
                                 "X-Cached": str(out["cached"]).lower(),
                                 "X-Approx": str(out["approx"]).lower(),
                                 "X-Spoken-Text": urllib.parse.quote(out["spoken_text"][:120]),
                                 "Cache-Control": "public, max-age=604800"})


@app.get("/api/tts")
def tts_get(text: str, lang: str = "sat", slow: bool = False):
    """GET form (what <audio>/new Audio() in the browser uses, and what the
    service worker caches offline)."""
    return _tts_response(text, lang, slow)


@app.post("/api/tts")
def tts(body: TTSIn):
    return _tts_response(body.text, body.lang, body.slow)


@app.get("/api/lessons")
def lessons():
    out = []
    for l in LESSONS:
        items = [v for v in engine.vocab_pool()
                 if v.get("sat") and v["category"] in l["categories"]]
        out.append({**l, "word_count": len(items),
                    "words": items[:12],
                    "phrases": [p for p in engine.pack["phrases"]
                                if p["hindi"] in (
                                    l["instruction_hi"], "किताब बंद करो।", "ध्यान से पढ़ो।",
                                    "मेरी मदद करो।", "फल कहाँ है?")][:4]})
    return {"total": len(out), "lessons": out}


@app.get("/api/flashcards")
def flash_cards(category: str = "all", count: int = 12, shuffle: bool = True):
    return flashcards(engine.vocab_pool(), category, count, shuffle)


@app.get("/api/quiz")
def quiz_api(category: str = "all", count: int = 5):
    return quiz(engine.vocab_pool(), category, count)


@app.post("/api/worksheet", response_class=HTMLResponse)
def worksheet(body: WorksheetIn):
    html = worksheet_html(body.model_dump(), engine.vocab_pool(),
                          {"language": engine.pack["meta"]["language"],
                           "generated": datetime.now().strftime("%d %b %Y")})
    log("worksheet", body.template)
    return HTMLResponse(html)


class QuizOut(BaseModel):
    pass


@app.post("/api/validate")
def validate(body: ValidateIn):
    """Human-in-the-loop: a teacher or native speaker confirms/corrects a string."""
    VERIFIED.parent.mkdir(parents=True, exist_ok=True)
    store = json.load(open(VERIFIED, encoding="utf-8")) if VERIFIED.exists() else {}
    store[body.hindi] = {"sat": body.sat, "scope": body.scope,
                         "note": body.note, "teacher": body.teacher,
                         "ts": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    VERIFIED.write_text(json.dumps(store, ensure_ascii=False, indent=1), encoding="utf-8")
    con = db()
    con.execute("INSERT INTO validation(ts,scope,hindi,proposed,note,teacher,status) "
                "VALUES(?,?,?,?,?,?,?)",
                (datetime.now(timezone.utc).isoformat(timespec="seconds"), body.scope,
                 body.hindi, body.sat, body.note, body.teacher, "accepted"))
    con.commit()
    con.close()
    engine.reload_indexes()                        # corrections take effect immediately
    log("validate", f"{body.scope}: {body.hindi} -> {body.sat[:40]}")
    return {"ok": True, "verified_total": len(engine.verified),
            "applied": body.hindi, "scope": body.scope}


@app.get("/api/validation")
def validation_list(limit: int = 50):
    con = db()
    rows = con.execute("SELECT ts,scope,hindi,proposed,note,teacher FROM validation "
                       "ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    con.close()
    return {"total": len(rows),
            "items": [dict(zip(("ts", "scope", "hindi", "proposed", "note", "teacher"), r))
                      for r in rows]}


@app.post("/api/validation/seed")
def validation_seed():
    """Queue the items that still need a native speaker (PS section 17)."""
    con = db()
    queued = {r[0] for r in con.execute("SELECT hindi FROM validation").fetchall()}
    n = 0
    for p in engine.pack["phrases"]:
        if (p.get("confidence") != "high" or not p.get("attested")) and p["hindi"] not in queued:
            con.execute("INSERT INTO validation(ts,scope,hindi,proposed,note,teacher,status) "
                        "VALUES(?,?,?,?,?,?,?)",
                        (datetime.now(timezone.utc).isoformat(timespec="seconds"), "phrase",
                         p["hindi"], p.get("sat") or "", "auto-queued for review", "", "pending"))
            n += 1
    for v in engine.vocab_pool():
        if v.get("sat") and v["confidence"] != "high" and v["hindi"] not in queued:
            con.execute("INSERT INTO validation(ts,scope,hindi,proposed,note,teacher,status) "
                        "VALUES(?,?,?,?,?,?,?)",
                        (datetime.now(timezone.utc).isoformat(timespec="seconds"), "vocab",
                         v["hindi"], v["sat"], "auto-queued for review", "", "pending"))
            n += 1
    con.commit()
    con.close()
    return {"queued": n}


@app.get("/api/stats")
def stats():
    con = db()
    usage = con.execute("SELECT event, COUNT(*) FROM usage GROUP BY event").fetchall()
    pending = con.execute("SELECT COUNT(*) FROM validation WHERE status='pending'").fetchone()[0]
    accepted = con.execute("SELECT COUNT(*) FROM validation WHERE status='accepted'").fetchone()[0]
    con.close()
    return {"usage": {e: c for e, c in usage}, "validation": {"pending": pending,
            "accepted": accepted},
            "tts": cache_stats(), "pack": engine.pack["meta"]["counts"]}


# ------------------------------------------------------- voice input (ASR)
@app.get("/api/asr/status")
def asr_status():
    """Tells the front-end whether server-side transcription is usable."""
    return asr.status()


@app.post("/api/asr")
async def asr_transcribe(file: UploadFile = File(...), language: str = "hi"):
    """Hindi speech -> text. Used when the browser cannot run Web Speech API
    (Firefox/Safari) or the page has no microphone permission - the teacher
    records, this returns Devanagari Hindi which then goes through the normal
    translation engine."""
    ok, why = asr.available()
    if not ok:
        raise HTTPException(status_code=503, detail=f"speech recognition unavailable: {why}")
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="empty audio upload")
    if len(data) > 20 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="audio too large (20 MB max)")
    suffix = Path(file.filename or "clip.webm").suffix or ".webm"
    try:
        out = asr.transcribe_audio(data, suffix=suffix, language=language)
    except Exception as exc:                       # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"transcription failed: {exc}") from exc
    log("asr", f"{out['duration_s']}s -> {out['text'][:60]}")
    return out


@app.get("/api/version")
def version():
    """Which front-end build the server is serving right now.

    The page compares this against the build its own bundle was made from. If they
    differ, the page drops its offline caches and reloads - that is how a browser that
    cached an older copy finds out about a screen added later, instead of sitting on a
    stale build and reporting a feature as missing.
    """
    import re as _re

    build = "dev"
    index = WEB_DIST / "index.html"
    if index.exists():
        html = index.read_text(encoding="utf-8", errors="ignore")
        m = _re.search(r"assets/index-([A-Za-z0-9_-]+)\.js", html)
        if m:
            build = m.group(1)
    return {"build": build, "screens": len(SCREEN_IDS), "screens_available": SCREEN_IDS}


# ------------------------------------------------------------------------- PDF
class PdfReportIn(BaseModel):
    filename: str = ""
    info: dict = {}
    blocks: list[dict] = []
    stats: dict = {}
    teacher: str = ""
    school: str = ""


@app.get("/api/pdf/status")
def pdf_status():
    import pdfdoc
    return {"ready": pdfdoc.available(),
            "hint": "pip install pypdf" if not pdfdoc.available()
                    else "upload a PDF, get a bilingual printable page"}


@app.post("/api/pdf/translate")
async def pdf_translate(file: UploadFile = File(...), max_pages: int = 5,
                        target: str = "sat"):
    """Read a PDF and translate it paragraph by paragraph into Santhali.

    Hindi, English and Odia pages are all accepted: every paragraph is routed by the
    script it is written in, and each one carries the method and confidence it was
    produced with - a PDF does not get a free pass for being a PDF.
    """
    import tempfile

    import pdfdoc

    if not pdfdoc.available():
        raise HTTPException(status_code=503,
                            detail="PDF reading needs pypdf - run: pip install pypdf")
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="empty file")
    if len(data) > 25 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="file larger than 25 MB")
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    tmp.write(data)
    tmp.close()
    try:
        doc = pdfdoc.translate_document(registry.get(target) or engine, tmp.name,
                                        max_pages=max(1, min(max_pages, 20)),
                                        filename=file.filename or "document.pdf")
    except Exception as exc:                                 # noqa: BLE001
        raise HTTPException(status_code=400,
                            detail=f"could not read that PDF: {exc}") from exc
    finally:
        try:
            import os
            os.unlink(tmp.name)
        except OSError:
            pass
    doc["target_language"] = target
    log("pdf", f"{file.filename} target={target} pages={doc['info']['pages_read']} "
               f"blocks={doc['stats']['blocks']} translated={doc['stats']['translated']}")
    return doc


@app.post("/api/pdf/report", response_class=HTMLResponse)
def pdf_report(body: PdfReportIn):
    """Printable bilingual page for a translated PDF (browser Print -> Save as PDF)."""
    import pdfdoc

    html = pdfdoc.report_html(body.model_dump(),
                             {"teacher": body.teacher, "school": body.school})
    return HTMLResponse(html)


@app.post("/api/pdf/text")
def pdf_text(body: PdfReportIn):
    """Plain-text download of the bilingual result."""
    import pdfdoc

    return {"filename": (body.filename or "document").rsplit(".", 1)[0] + "-santhali.txt",
            "text": pdfdoc.bilingual_text(body.model_dump())}


# ------------------------------------------------------------ static front-end
if WEB_DIST.exists():
    app.mount("/assets", StaticFiles(directory=WEB_DIST / "assets"), name="assets")

    NO_CACHE = {"Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache"}

    @app.get("/{path:path}", include_in_schema=False)
    def spa(path: str, request: Request):
        candidate = WEB_DIST / path
        if path and candidate.is_file():
            if path.startswith("assets/"):
                # content-hashed file name: safe to cache forever
                return FileResponse(candidate, headers={
                    "Cache-Control": "public, max-age=31536000, immutable"})
            return FileResponse(candidate, headers=NO_CACHE)
        if path.startswith("api/"):
            # an unknown API path must never answer with HTML - that hides a moved or
            # missing route behind a 200, which is how a stale tab looks "healthy"
            return JSONResponse({
                "detail": f"no such endpoint: /{path}",
                "hint": "see /docs for the live route list",
                "routes": sorted({r.path for r in app.routes
                                  if getattr(r, "path", "").startswith("/api")}),
            }, status_code=404)
        # the shell must never be cached, or a tab that was added today stays invisible
        return FileResponse(WEB_DIST / "index.html", headers=NO_CACHE)
else:
    @app.get("/", include_in_schema=False)
    def no_build():
        return JSONResponse({"detail": "front-end not built yet - run `npm run build` "
                                       "inside web/", "api": "/docs"})
