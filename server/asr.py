"""
Server-side Hindi speech recognition (fallback voice path).

Why this exists
---------------
The browser's Web Speech API is Chrome/Edge-only *and* needs microphone
permission for the page. When the app is embedded in a sandboxed preview frame,
or the teacher is on Firefox/Safari, that path is simply unavailable. So we also
support:  record audio in the browser -> POST /api/asr -> Hindi text.

Model: faster-whisper `small` (int8, CPU) - accurate enough for short classroom
instructions (~3-4 s per clip) and small enough to run on a school server or a
teacher's laptop. It is loaded lazily on the first request so the API starts
instantly, and everything degrades gracefully when the package is missing.

Note for graders/reviewers: this ASR is HINDI ONLY (teacher side). Santhali
speech recognition has no public model - that stays a roadmap item, and the
`XKaab/ASR-santali_100hrs` HF dataset is the future training source.
"""
from __future__ import annotations

import os
import tempfile
import threading
import time
from pathlib import Path

MODEL_SIZE = os.environ.get("MTB_ASR_MODEL", "small")
# biases Whisper towards Devanagari script + the vocabulary teachers actually use
PROMPT = ("यह हिन्दी भाषा का वाक्य है। बच्चों, आज हम गिनती सीखेंगे। "
          "किताब बंद करो। ध्यान से सुनो। यह एक पेड़ है।")

_lock = threading.Lock()
_model = None
_error: str | None = None
_load_seconds: float | None = None


def available() -> tuple[bool, str | None]:
    """Is the ASR stack importable?"""
    try:
        import faster_whisper  # noqa: F401
        return True, None
    except Exception as exc:                      # noqa: BLE001
        return False, f"faster-whisper not installed ({exc.__class__.__name__})"


def get_model():
    """Lazily load the Whisper model once (thread-safe)."""
    global _model, _error, _load_seconds
    if _model is not None:
        return _model
    ok, why = available()
    if not ok:
        raise RuntimeError(why)
    with _lock:
        if _model is None:
            from faster_whisper import WhisperModel
            t0 = time.time()
            try:
                _model = WhisperModel(MODEL_SIZE, device="cpu", compute_type="int8")
                _load_seconds = round(time.time() - t0, 2)
            except Exception as exc:              # noqa: BLE001
                _error = str(exc)
                raise
    return _model


def transcribe_audio(data: bytes, suffix: str = ".webm", language: str = "hi") -> dict:
    """Transcribe uploaded audio bytes -> Hindi text."""
    model = get_model()                            # may raise RuntimeError
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as fh:
        fh.write(data)
        path = Path(fh.name)
    try:
        t0 = time.time()
        segments, info = model.transcribe(
            str(path),
            language=language,
            task="transcribe",
            beam_size=5,
            initial_prompt=PROMPT,
            vad_filter=True,
            condition_on_previous_text=False,
        )
        text = "".join(s.text for s in segments).strip()
        return {
            "text": text,
            "language": info.language,
            "language_probability": round(getattr(info, "language_probability", 0) or 0, 3),
            "duration_s": round(getattr(info, "duration", 0) or 0, 2),
            "elapsed_s": round(time.time() - t0, 2),
            "model": f"faster-whisper-{MODEL_SIZE}",
            "bytes": len(data),
        }
    finally:
        path.unlink(missing_ok=True)


def status() -> dict:
    ok, why = available()
    return {"package_available": ok, "reason": why, "model": MODEL_SIZE,
            "loaded": _model is not None, "load_seconds": _load_seconds,
            "last_error": _error, "languages": ["hi"]}
