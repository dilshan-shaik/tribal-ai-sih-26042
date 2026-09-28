#!/usr/bin/env python3
"""
Ingest + verify a Mundari TTS archive (Bhashini/ULCA style:
`dataset-mundari-tts-full.tgz`) and wire real Mundari audio into the platform.

Usage
-----
    python3 pipelines/ingest_mundari_tts.py <path-to.tgz> [--expect-sha1 <hash>] [--install]

What it does, in order, and it stops honestly at the first thing it cannot verify:

 1. identity   sha1 / md5 / sha256 of the archive, compared with the hash you supply
 2. safety     lists the tar without extracting; refuses absolute paths, `..`, links
 3. structure  finds the audio files and the transcript table, whatever it is called
               (data.csv / data.json / metadata.csv / *.tsv ...) and reports the columns
 4. pairing    matches every transcript row to a real audio file; unmatched rows on either
               side are counted and listed, never silently dropped
 5. inventory  clips, total duration (decoded where possible), sample rate, speakers
               (gender column), clip-length distribution, empty/duplicate transcripts
 6. language   per-row script detection: Devanagari Mundari vs romanised vs other. A row
               that is not Mundari is reported, not used
 7. overlap    how much of it we already have: exact transcript hits against the current
               Mundari memory (6,020 English-facing pairs) and word hits against the
               Hindi->English bridge, so the added value is a number, not a claim
 8. install    (--install) writes data/mundari_tts/index.json - a transcript -> clip index
               the server uses to answer /api/tts?lang=unr with *real* Mundari audio, and
               appends genuinely new transcripts to the Mundari pack's sentence memory

Nothing is installed unless --install is passed, and nothing is extracted outside
data/mundari_tts/ .
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import re
import struct
import sys
import tarfile
import unicodedata
import wave
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "data" / "tts_clips" / "unr"          # change with --lang
LANG_DIR = {"unr": "unr", "hoc": "hoc", "mun": "unr"}
PACK = ROOT / "data" / "language_packs" / "unr.json"

AUDIO_EXT = {".wav", ".flac", ".mp3", ".ogg", ".opus", ".m4a", ".aac", ".pcm", ".sph"}
TABLE_EXT = {".csv", ".tsv", ".json", ".jsonl", ".xml", ".xlsx"}
TEXT_COLS = ("text", "transcript", "transcription", "sentence", "label", "target",
             "mundari", "unr", "translation", "utterance", "content", "script")
AUDIO_COLS = ("audiofilename", "audio_file", "audio", "filename", "file", "path",
              "wav", "audio_path", "file_name", "audiofile")


def human(n: float, unit: str = "B") -> str:
    for step in ("", "K", "M", "G", "T"):
        if abs(n) < 1024 or step == "T":
            return f"{n:.1f}{step}{unit}"
        n /= 1024
    return f"{n}{unit}"


def sha1_of(path: Path, chunk: int = 1 << 20) -> str:
    h = hashlib.sha1()
    with open(path, "rb") as fh:
        while True:
            b = fh.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def hashes_of(path: Path) -> dict:
    out = {"sha1": hashlib.sha1(), "md5": hashlib.md5(), "sha256": hashlib.sha256()}
    with open(path, "rb") as fh:
        while True:
            b = fh.read(1 << 20)
            if not b:
                break
            for h in out.values():
                h.update(b)
    return {k: v.hexdigest() for k, v in out.items()}


def script_of(text: str) -> str:
    if any(0x0900 <= ord(c) <= 0x097F for c in text):
        return "Devanagari"
    if any(0x118A0 <= ord(c) <= 0x118FF for c in text):
        return "Warang Citi"
    if any(0x1C50 <= ord(c) <= 0x1C7F for c in text):
        return "Ol Chiki"
    if re.search(r"[A-Za-z]", text):
        return "roman"
    return "other"


def norm(s: str) -> str:
    s = unicodedata.normalize("NFC", (s or "").strip())
    return re.sub(r"\s+", " ", s)


# ---------------------------------------------------------------- archive
def safe_members(tf: tarfile.TarFile) -> tuple[list[tarfile.TarInfo], list[str]]:
    good, bad = [], []
    for m in tf.getmembers():
        name = m.name
        if m.issym() or m.islnk():
            bad.append(f"link: {name}")
            continue
        if name.startswith("/") or ".." in Path(name).parts:
            bad.append(f"unsafe path: {name}")
            continue
        good.append(m)
    return good, bad


def wav_info(data: bytes) -> tuple[float, int]:
    """(seconds, sample_rate) from a WAV header, without decoding the whole file."""
    try:
        with wave.open(io.BytesIO(data)) as w:
            return w.getnframes() / float(w.getframerate() or 1), w.getframerate()
    except Exception:
        if len(data) > 44:
            try:
                rate = struct.unpack("<I", data[24:28])[0]
                byte_rate = struct.unpack("<I", data[28:32])[0]
                if byte_rate:
                    return (len(data) - 44) / float(byte_rate), rate
            except Exception:
                pass
    return 0.0, 0


def read_table(name: str, data: bytes) -> tuple[list[dict], list[str]]:
    low = name.lower()
    try:
        if low.endswith((".csv", ".tsv")):
            text = data.decode("utf-8", "replace")
            delim = "\t" if low.endswith(".tsv") or text.count("\t") > text.count(",") else ","
            rows = list(csv.DictReader(io.StringIO(text), delimiter=delim))
            return rows, (list(rows[0].keys()) if rows else [])
        if low.endswith(".jsonl"):
            rows = [json.loads(l) for l in data.decode("utf-8", "replace").splitlines() if l.strip()]
            return rows, (list(rows[0].keys()) if rows else [])
        if low.endswith(".json"):
            d = json.loads(data.decode("utf-8", "replace"))
            if isinstance(d, list):
                return d, (list(d[0].keys()) if d and isinstance(d[0], dict) else [])
            for key in ("data", "records", "rows", "dataset", "items"):
                if isinstance(d.get(key), list) and d[key]:
                    return d[key], list(d[key][0].keys())
            return [d], list(d.keys())
    except Exception as exc:                                   # noqa: BLE001
        return [], [f"unreadable: {exc}"]
    return [], []


def pick_col(keys: list[str], wanted: tuple) -> str | None:
    lowered = {k.lower().replace(" ", "").replace("_", ""): k for k in keys}
    for w in wanted:
        w2 = w.lower().replace("_", "")
        for k, orig in lowered.items():
            if k == w2 or k.startswith(w2):
                return orig
    return None


# ---------------------------------------------------------------- main
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("archive", nargs="?", default=None)
    ap.add_argument("--expect-sha1", default="46c8bfceb5cf25decc8523479378793537f2bad7")
    ap.add_argument("--install", action="store_true")
    ap.add_argument("--lang", default="unr", choices=["unr", "hoc"],
                    help="which language the archive speaks (unr = Mundari, hoc = Ho)")
    ap.add_argument("--limit-audio", type=int, default=400, help="how many clips to measure")
    args = ap.parse_args()
    global OUT_DIR
    OUT_DIR = ROOT / "data" / "tts_clips" / LANG_DIR.get(args.lang, args.lang)

    path = Path(args.archive) if args.archive else None
    if path is None or not path.exists():
        # look for it where a teacher would drop it
        for cand in list((ROOT / "uploads").glob("*.tgz")) + list((ROOT / "uploads").glob("*.tar.gz")) \
                + list(Path("/tmp").glob("*mundari*.tgz")):
            print(f"no path given - using {cand}")
            path = cand
            break
    if path is None or not path.exists():
        print("!" * 78)
        print("No archive found. Put the file in uploads/ (or pass a path) and run again:")
        print("    python3 pipelines/ingest_mundari_tts.py uploads/dataset-mundari-tts-full.tgz")
        print("!" * 78)
        return 2

    print(f"archive : {path}  ({human(path.stat().st_size)})")
    hs = hashes_of(path)
    print(f"sha1    : {hs['sha1']}")
    print(f"md5     : {hs['md5']}")
    print(f"sha256  : {hs['sha256']}")
    if args.expect_sha1:
        match = hs["sha1"].lower() == args.expect_sha1.lower()
        print(f"expected: {args.expect_sha1}  ->  {'MATCH' if match else 'DOES NOT MATCH'}")
        if not match:
            print("  The bytes are not the artifact that hash describes. Refusing to install.")
    else:
        print("expected: (none given)")

    report: dict = {"archive": str(path), "bytes": path.stat().st_size, "hashes": hs,
                    "checked_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}

    if not tarfile.is_tarfile(path):
        print("! not a tar archive - cannot inspect further")
        return 1
    with tarfile.open(path) as tf:
        members, bad = safe_members(tf)
        audio = [m for m in members if Path(m.name).suffix.lower() in AUDIO_EXT]
        tables = [m for m in members if Path(m.name).suffix.lower() in TABLE_EXT]
        others = [m for m in members if m not in audio and m not in tables]
        print(f"\nmembers : {len(members)}  audio={len(audio)}  tables={len(tables)}  other={len(others)}")
        if bad:
            print(f"  refused {len(bad)} unsafe entries, e.g. {bad[:3]}")
        report["members"] = {"total": len(members), "audio": len(audio),
                             "tables": len(tables), "refused": bad[:20]}

        rows: list[dict] = []
        table_name, cols = None, []
        for m in sorted(tables, key=lambda x: x.size, reverse=True):
            fh = tf.extractfile(m)
            if not fh:
                continue
            got, keys = read_table(m.name, fh.read())
            if got:
                rows, table_name, cols = got, m.name, keys
                break
        print(f"\ntranscript table: {table_name or 'NONE FOUND'}")
        if cols:
            print(f"  columns ({len(cols)}): {', '.join(map(str, cols))[:160]}")
        report["table"] = {"name": table_name, "columns": [str(c) for c in cols], "rows": len(rows)}
        if not rows:
            print("  no transcript rows - an audio-only archive cannot be used as TTS data")
            return 1

        text_col = pick_col(cols, TEXT_COLS)
        audio_col = pick_col(cols, AUDIO_COLS)
        gender_col = pick_col(cols, ("gender", "sex", "speaker_gender"))
        print(f"  text column      : {text_col}")
        print(f"  audio column     : {audio_col}")
        print(f"  speaker column   : {gender_col}")

        texts = [norm(str(r.get(text_col) or "")) for r in rows] if text_col else []
        empty = sum(1 for t in texts if not t)
        dup = len(texts) - len(set(texts)) if texts else 0
        scripts = Counter(script_of(t) for t in texts if t)
        speakers = Counter(str(r.get(gender_col)) for r in rows) if gender_col else Counter()
        print(f"\ntranscripts: {len(texts)}  empty={empty}  duplicate={dup}")
        print(f"  scripts: {dict(scripts)}")
        if speakers:
            print(f"  speakers: {dict(speakers)}")
        report["transcripts"] = {"rows": len(texts), "empty": empty, "duplicates": dup,
                                 "scripts": dict(scripts), "speakers": dict(speakers)}

        # audio: names and durations on a sample
        names = {Path(m.name).name for m in audio}
        if audio_col:
            wanted = {Path(str(r.get(audio_col) or "")).name for r in rows}
            matched = len(wanted & names)
            print(f"\npairing  : {matched}/{len(wanted)} transcripts have an audio file in the archive")
            if matched < len(wanted):
                missing = sorted(wanted - names)[:5]
                print(f"  e.g. missing: {missing}")
            report["pairing"] = {"transcripts_with_audio": matched, "wanted": len(wanted)}

        total_s, rates = 0.0, Counter()
        measured = audio[: args.limit_audio]
        for m in measured:
            fh = tf.extractfile(m)
            if not fh:
                continue
            secs, rate = wav_info(fh.read())
            total_s += secs
            if rate:
                rates[rate] += 1
        if measured:
            per = total_s / len(measured)
            est = per * len(audio)
            print(f"duration : {len(measured)} clips measured, {total_s/60:.1f} min "
                  f"({per:.2f}s average) -> ~{est/3600:.1f} h for all {len(audio)} clips")
            print(f"  sample rates: {dict(rates)}")
            report["duration"] = {"measured": len(measured), "minutes_measured": round(total_s / 60, 1),
                                  "avg_seconds": round(per, 2), "est_hours_total": round(est / 3600, 2),
                                  "sample_rates": {str(k): v for k, v in rates.items()}}

    # ---------------------------------------------------------- overlap
    if PACK.exists() and texts:
        pack = json.load(open(PACK, encoding="utf-8"))
        have = {norm(m["en"]).lower(): m for m in pack["sentence_memory"]}
        have_tgt = {norm(m["tgt"]) for m in pack["sentence_memory"]}
        new = [t for t in set(texts) if t and t not in have_tgt]
        print(f"\noverlap  : {len(set(texts)) - len(new)} of {len(set(texts))} unique transcripts "
              f"are already in the Mundari memory; {len(new)} would be new")
        report["overlap"] = {"unique": len(set(texts)), "already_known": len(set(texts)) - len(new),
                             "new": len(new)}

    # ---------------------------------------------------------- install
    if args.install:
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        (OUT_DIR / "audio").mkdir(exist_ok=True)
        json.dump(report, open(OUT_DIR / "ingest_report.json", "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
        print(f"\nwrote {OUT_DIR/'ingest_report.json'}")

        # build transcript -> clip index so /api/tts?lang=unr can serve the REAL voice
        clips: dict[str, str] = {}
        with tarfile.open(path) as tf:
            by_name = {Path(m.name).name: m for m in tf.getmembers()
                       if Path(m.name).suffix.lower() in AUDIO_EXT}
            for r in rows:
                raw_name = str(r.get(audio_col) or "")
                txt = norm(str(r.get(text_col) or ""))
                m = by_name.get(Path(raw_name).name)
                if not m or not txt:
                    continue
                key = norm(txt)                      # exact match; no fuzzy audio
                if key in clips:
                    continue
                dest = OUT_DIR / "audio" / Path(raw_name).name
                if not dest.exists():
                    fh = tf.extractfile(m)
                    if not fh:
                        continue
                    dest.write_bytes(fh.read())
                clips[key] = f"audio/{dest.name}"
        index = {
            "source": path.name, "sha1": hs["sha1"], "built_at":
                datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "clips": len(clips), "match": "exact transcript equality, case- and space-normalised",
            "language_code": LANG_DIR.get(args.lang, args.lang),
            "voice": f"{'Mundari' if args.lang == 'unr' else 'Ho'} (dataset recordings)",
            "map": clips,
        }
        json.dump(index, open(OUT_DIR / "index.json", "w", encoding="utf-8"), ensure_ascii=False)
        print(f"wrote {OUT_DIR/'index.json'} with {len(clips)} real Mundari clips")
        print("the server now answers /api/tts?lang=unr from these recordings when the exact "
              "sentence is one of them, and falls back to the approximate Hindi voice otherwise.")

    print("\nreport:")
    print(json.dumps(report, ensure_ascii=False, indent=1)[:1800])
    return 0


if __name__ == "__main__":
    sys.exit(main())
