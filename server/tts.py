"""
Text-to-speech for the MTB-MLE platform.

Reality check (this matters for the demo): there is **no public Santhali TTS
voice model** on Hugging Face or AI4Bharat today - the Hugging Face Hub has no
`san`/`sat` TTS checkpoint, and Indic-TTS / AI4Bharat's voices cover
hi, bn, ta, te, mr, ml, kn, gu, pa, or, as ... not Santhali. So instead of
pretending, we do the honest engineering thing:

    Santhali (Ol Chiki)  ->  Devanagari transliteration  ->  Hindi voice model
                             (phonetically close; matra/virama aware)

The transliteration lives in pipelines/translit.py and is shared with the
build pipeline, so what students hear matches what is on screen. Audio is
cached on disk by content hash - the second play of a sentence is instant and
works offline (offline-first requirement).

A `sat-voice` slot is left in the API so a real Santhali voice model can drop
in later without touching the frontend (see /api/tts?voice=).
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from gtts import gTTS

import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "pipelines"))
from translit import is_olchiki, to_devanagari  # noqa: E402

CACHE = Path(__file__).resolve().parent.parent / "data" / "audio_cache"
CACHE.mkdir(parents=True, exist_ok=True)

# gTTS voice per logical language. `sat` rides on the Hindi voice via
# transliteration - documented in the response payload as `voice_engine`.
VOICE = {"hi": "hi", "en": "en", "sat": "hi"}


DATA = Path(__file__).resolve().parent.parent / "data"
# Recorded-speech indexes, one folder per language: data/tts_clips/<code>/index.json
# (the older data/mundari_tts/ location still works). Install one and that language
# speaks with its own recordings instead of the approximate Hindi voice.
CLIP_DIRS = [DATA / "tts_clips", DATA / "mundari_tts"]
_clip_maps: dict[str, dict] = {}


def recorded_clip(text: str, lang: str):
    """A real recording for this exact sentence, if a speech dataset was installed for
    that language. Exact match only: a wrong recording is worse than an approximation."""
    key = re.sub(r"\s+", " ", (text or "").strip())
    for base in CLIP_DIRS:
        code_dir = base / lang
        index = (code_dir / "index.json") if code_dir.is_dir() else (base / "index.json")
        if not index.exists():
            continue
        ck = str(index)
        if ck not in _clip_maps:
            try:
                _clip_maps[ck] = json.load(open(index, encoding="utf-8")).get("map", {})
            except Exception:                                  # noqa: BLE001
                _clip_maps[ck] = {}
        rel = _clip_maps[ck].get(key)
        if rel:
            path = index.parent / rel
            if path.exists():
                return path, index
    return None


def clip_status() -> dict:
    """Which languages have recorded speech installed (surfaced in /api/health)."""
    out = {}
    for base in CLIP_DIRS:
        if not base.is_dir():
            continue
        for idx in base.glob("*/index.json") + ([base / "index.json"] if (base / "index.json").exists() else []):
            try:
                d = json.load(open(idx, encoding="utf-8"))
                out.setdefault(d.get("language_code") or idx.parent.name,
                               {"clips": d.get("clips", len(d.get("map", {}))),
                                "source": d.get("source"), "voice": d.get("voice")})
            except Exception:                                  # noqa: BLE001
                continue
    return out


def _key(text: str, lang: str, slow: bool) -> str:
    return hashlib.sha256(f"{lang}|{slow}|{text}".encode("utf-8")).hexdigest()[:32]


def synthesise(text: str, lang: str = "hi", slow: bool = False) -> dict:
    """Return {path, cached, spoken_text, voice_engine, approx}."""
    text = re.sub(r"\s+", " ", (text or "").strip())
    if not text:
        raise ValueError("empty text")
    clip = recorded_clip(text, lang)
    if clip:
        path, index = clip
        try:
            meta = json.load(open(index, encoding="utf-8"))
            voice = meta.get("voice") or f"{lang} (recorded)"
        except Exception:                                      # noqa: BLE001
            voice = f"{lang} (recorded)"
        return {"path": path, "cached": True, "spoken_text": text,
                "voice_engine": voice, "approx": False}
    lang = lang if lang in VOICE else "hi"
    spoken = text
    approx = False
    if lang == "sat" or is_olchiki(text):
        spoken = to_devanagari(text)
        approx = True
    key = _key(spoken, lang, slow)
    path = CACHE / f"{key}.mp3"
    cached = path.exists()
    if not cached:
        gTTS(spoken, lang=VOICE[lang], slow=slow).save(str(path))
    return {
        "path": path,
        "cached": cached,
        "spoken_text": spoken,
        "voice_engine": f"gTTS-{VOICE[lang]}"
        + (" (Santhali via Devanagari transliteration)" if approx else ""),
        "approx": approx,
    }


def cache_stats() -> dict:
    files = list(CACHE.glob("*.mp3"))
    size = sum(f.stat().st_size for f in files)
    return {"clips": len(files), "bytes": size, "mb": round(size / 1e6, 2)}
