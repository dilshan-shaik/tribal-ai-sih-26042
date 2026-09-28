"""
Pre-generate the audio clips a school would download with the language pack,
so a classroom with no internet still hears every word (PS section 7).

Called at build/sync time:  python3 pipelines/prewarm_audio.py [--limit N]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "server"))
from tts import cache_stats, synthesise  # noqa: E402

pack = json.load(open(ROOT / "data" / "language_packs" / "sat.json", encoding="utf-8"))
limit = None
if "--limit" in sys.argv:
    limit = int(sys.argv[sys.argv.index("--limit") + 1])

targets: list[tuple[str, str]] = []
for v in pack["vocab"]:
    if v.get("sat"):
        targets.append((v["sat"], "sat"))
        targets.append((v["hindi"], "hi"))
for p in pack["phrases"]:
    if p.get("sat"):
        targets.append((p["sat"], "sat"))
        targets.append((p["hindi"], "hi"))
for v in pack["verbs"][:20]:
    targets.append((v["sat"], "sat"))
# the Hindi->Santhali dictionary + number table: words and numerals a worksheet needs
for e in pack.get("dictionary", []):
    if e.get("sat"):
        targets.append((e["sat"], "sat"))
for k, n in (pack.get("numbers") or {}).items():
    targets.append((n["sat"], "sat"))
    targets.append((n["hi"], "hi"))

if limit:
    targets = targets[:limit]

print(f"pre-generating {len(targets)} clips ...")
made = 0
for i, (text, lang) in enumerate(targets, 1):
    try:
        out = synthesise(text, lang)
        made += not out["cached"]
        if i % 50 == 0:
            print(f"  {i}/{len(targets)}  (new {made})", flush=True)
    except Exception as exc:                       # noqa: BLE001
        print(f"  skip {text[:20]!r}: {exc}")
print("cache:", cache_stats())
