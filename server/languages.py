"""
Multi-language layer: Santhali (sat) + Mundari (unr) + Ho (hoc).

Why the architecture looks like this
------------------------------------
Santhali has a Hindi-facing pack (Hindi words, phrases, sentence memory, numbers).
Mundari and Ho do not: there is no published Hindi<->Mundari or Hindi<->Ho parallel
corpus, and the reconnaissance behind MUNDARI_HO_REPORT.md found none. What does
exist is English-facing parallel text (google/smol smoldoc, Tatoeba via sicsoc).

So the two new languages are served by a single rule that matches the platform's
honesty contract:

  English in   -> a real, attested sentence can be returned (high confidence)
  Hindi in     -> never a sentence. Words are carried across the English pivot
                  (hi -> en -> target) and returned as a *word combination* with
                  coverage, labelled `pivot-en`, confidence capped at `medium`.
  nothing hits -> decline (word combo with 0 known, or "nothing known")

Every word carries its chain ("पानी → water → दअ:"), so a teacher can see exactly
what was bridged and how.
"""
from __future__ import annotations

import difflib
import json
import re
import unicodedata
from difflib import SequenceMatcher
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PACKS = ROOT / "data" / "language_packs"

# Hindi words with no standalone meaning. Same principle as the Santhali engine:
# they cannot be concatenated into a word list, and corpus alignments for them are
# junk. They are counted as unknown and named in `skipped`.
HI_FUNCTION_WORDS = {
    "है", "हैं", "हो", "हूँ", "हूं", "था", "थी", "थे", "होगा", "होगी", "होंगे",
    "का", "की", "के", "को", "से", "में", "मे", "पर", "और", "या", "तो", "भी", "ही",
    "एक", "यह", "वह", "ये", "वे", "इस", "उस", "इन", "उन", "मैं", "हम", "तुम", "आप",
    "कि", "जो", "ने", "न", "ना", "नहीं", "but", "a", "an", "the",
}

EN_STOP = {
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being", "am", "do",
    "does", "did", "of", "to", "in", "on", "at", "by", "for", "with", "from", "as",
    "and", "or", "but", "if", "then", "than", "that", "this", "these", "those",
    "it", "its", "he", "she", "they", "them", "his", "her", "their", "we", "our",
    "you", "your", "i", "my", "me", "will", "would", "shall", "should", "may",
    "might", "must", "can", "could", "have", "has", "had", "not", "no", "so",
    "such", "there", "here", "when", "while", "during", "however", "therefore",
    "also", "more", "most", "much", "many", "some", "any", "all", "each", "every",
    "other", "into", "over", "under", "about", "after", "before", "between",
}

PUNCT = "।,.!?;:\"'()[]{}—–-…“”‘’"


def token_script(text: str) -> str:
    if any(0x118A0 <= ord(c) <= 0x118FF for c in text):
        return "Warang Citi"
    if any(0x0900 <= ord(c) <= 0x097F for c in text):
        return "Devanagari"
    if any(0x1C50 <= ord(c) <= 0x1C7F for c in text):
        return "Ol Chiki"
    return "roman"


def norm(s: str) -> str:
    s = unicodedata.normalize("NFC", (s or "").strip())
    s = s.replace("\u200b", "").replace("\ufeff", "")
    return re.sub(r"\s+", " ", s)


def key(s: str) -> str:
    """Comparison key: case-folded, punctuation-stripped."""
    s = norm(s).lower()
    return re.sub(r"\s+", " ", s.strip(PUNCT + " ")).strip()


def words_of(text: str, lang: str) -> list[str]:
    if lang == "hi":
        toks = [t.strip(PUNCT) for t in re.split(r"[\s\u0964]+", norm(text))]
    elif lang == "en":
        toks = [t.strip(PUNCT).lower() for t in norm(text).split()]
    else:
        toks = [t.strip(PUNCT) for t in norm(text).split()]
    return [t for t in toks if t]


class Pack:
    """One target language served through the English pivot."""

    def __init__(self, path: Path, hi_en: dict[str, str]):
        self.code = path.stem
        self.pack = json.load(open(path, encoding="utf-8"))
        self.meta = self.pack["meta"]
        self.hi_en = hi_en
        self.memory = self.pack["sentence_memory"]
        self.index = {key(m["en"]): m for m in self.memory}
        self.aug_memory = self.pack.get("sentence_memory_aug") or []
        self.aug_index = {key(m["en"]): m for m in self.aug_memory}
        self.cognates = self.pack.get("cognates") or []
        self.dict_en = {e["en"].lower(): e for e in self.pack.get("dictionary_en", [])}
        self.tgt_len = max((len(m["tgt"]) for m in self.memory), default=0)

    # ---------------------------------------------------------------- helpers
    def _target_block(self, text: str, roman: str | None = None,
                      script: str | None = None) -> dict:
        return {
            "text": text,
            "native": text,
            "script": script or token_script(text),
            "roman": roman,
            "language": self.meta["language"],
            "code": self.code,
        }

    def _decline(self, note: str, skipped: list[str] | None = None) -> dict:
        return {
            "ok": False, "method": "declined", "kind": "none", "confidence": "none",
            "verified": False, "sat": None, "target": None, "output": None,
            "words": [], "wordbank": [], "combined": None, "combined_roman": None,
            "known": 0, "total": 0, "coverage": 0.0, "skipped": skipped or [],
            "english_gloss": None, "hindi_gloss": None, "evidence": None,
            "needs_validation": False, "note": note,
            "target_language": self.meta["language"], "target_code": self.code,
            "tts": self.tts_info(),
        }

    def tts_info(self) -> dict:
        return dict(self.meta.get("tts") or {"available": False, "why": "no voice model"})

    def _combo(self, words: list[dict], total: int, skipped: list[str],
               method: str, note: str) -> dict:
        known = len(words)
        combined = " ".join(w["tgt"] for w in words) or None
        roman = " ".join(w["roman"] for w in words if w.get("roman")) or None
        coverage = round(known / total, 3) if total else 0.0
        # a two-hop bridge never earns "high"; a complete short combination earns
        # "medium", anything partial stays "low" and is shown as words, not a sentence
        conf = "medium" if (known == total and known >= 2 and method != "pivot-en") else "low"
        if method == "pivot-en" and known == total and known >= 3:
            conf = "medium"
        return {
            "ok": False, "method": method, "kind": "words", "confidence": conf,
            "verified": False, "sat": None,
            "target": self._target_block(combined) if combined else None,
            "output": self._target_block(combined) if combined else None,
            "words": words, "wordbank": words, "combined": combined,
            "combined_roman": roman, "known": known, "total": total,
            "coverage": coverage, "skipped": skipped,
            "english_gloss": None, "hindi_gloss": None, "evidence": None,
            "needs_validation": True, "note": note,
            "target_language": self.meta["language"], "target_code": self.code,
            "tts": self.tts_info(),
        }

    # ---------------------------------------------------------------- lookups
    def sentence(self, text: str) -> dict | None:
        k = key(text)
        hit = self.index.get(k)
        conf, method = "high", "sentence-memory-en"
        if not hit and len(k) >= 12:
            close = difflib.get_close_matches(k, list(self.index), n=1, cutoff=0.90)
            if close and len(close[0].split()) == len(k.split()):
                hit = self.index[close[0]]
                conf, method = "medium", "sentence-memory-en-fuzzy"
        if not hit:
            aug = self.aug_index.get(k)
            if aug:
                return {
                    "ok": True, "method": "sentence-memory-aug", "kind": "machine-augmented",
                    "confidence": "medium", "verified": False, "synthetic": True,
                    "sat": None,
                    "target": self._target_block(aug["tgt"], script=token_script(aug["tgt"])),
                    "output": self._target_block(aug["tgt"], script=token_script(aug["tgt"])),
                    "words": [], "wordbank": [], "combined": None, "combined_roman": None,
                    "known": None, "total": None, "coverage": None, "skipped": [],
                    "english_gloss": aug["en"], "hindi_gloss": None,
                    "evidence": f"{aug['en']}  [{aug.get('source', 'augmented')}]",
                    "needs_validation": True,
                    "note": "machine-augmented pair (noun substitution on an attested "
                            "template) - useful, but check it with a speaker before teaching",
                    "target_language": self.meta["language"], "target_code": self.code,
                    "tts": self.tts_info(),
                }
            return None
        return {
            "ok": True, "method": method, "kind": "attested", "confidence": conf,
            "verified": False, "sat": None,
            "target": self._target_block(hit["tgt"], script=hit.get("script")),
            "output": self._target_block(hit["tgt"], script=hit.get("script")),
            "words": [], "wordbank": [], "combined": None, "combined_roman": None,
            "known": None, "total": None, "coverage": None, "skipped": [],
            "english_gloss": hit["en"], "hindi_gloss": None,
            "evidence": f"{hit['en']}  [{hit.get('source', 'parallel corpus')}]",
            "needs_validation": conf != "high",
            "note": f"attested English–{self.meta['language']} pair from "
                    f"{hit.get('source', 'the parallel corpus')}",
            "target_language": self.meta["language"], "target_code": self.code,
            "tts": self.tts_info(),
        }

    def lookup_any(self, token: str):
        """Same contract as the Santhali engine's lookup_any: a string, or
        (string, needs_check). Used by the PDF word-by-word renderer."""
        t = (token or "").strip(PUNCT)
        if not t:
            return None
        if any(0x0900 <= ord(c) <= 0x097F for c in t):        # Hindi token
            en = self.hi_en.get(t)
            if not en:
                return None
            w = self.word(en)
            return (w["tgt"], True) if w else None             # two-hop -> flagged
        w = self.word(t.lower())
        if w and not w.get("phonetic"):
            return w["tgt"]                      # a dictionary's phonetic spelling does not
        return None                              # belong on a printed worksheet

    def word(self, en: str) -> dict | None:
        e = self.dict_en.get(en.lower().strip(PUNCT))
        if not e:
            return None
        return {"tgt": e["tgt"], "score": e.get("score"), "count": e.get("count"),
                "source": e.get("source", "corpus-alignment"),
                "phonetic": bool(e.get("phonetic")),
                "alts": [a["form"] for a in (e.get("alts") or [])][:3]}

    # ---------------------------------------------------------------- cascade
    def translate(self, text: str, source: str = "hi") -> dict:
        text = norm(text)
        if not text:
            return self._decline("nothing to translate")
        if source == "en":
            hit = self.sentence(text)
            if hit:
                return hit
            toks = [t for t in words_of(text, "en") if t not in EN_STOP]
            known, skipped = [], []
            for t in toks:
                w = self.word(t)
                if w and w["tgt"] not in [k["tgt"] for k in known]:
                    known.append({"hindi": None, "english": t, "tgt": w["tgt"],
                                  "score": w["score"], "chain": f"{t} → {w['tgt']}",
                                  "script": token_script(w["tgt"]),
                                  "source": w["source"], "phonetic": w.get("phonetic", False),
                                  "alts": w.get("alts") or []})
                else:
                    skipped.append(t)
            if not toks:
                return self._decline(
                    f"no {self.meta['language']} sentence matches that text "
                    f"({len(self.memory)} English–{self.meta['language']} pairs are indexed)")
            method = "dictionary" if toks and not skipped else "word-combo"
            total = len(toks)
            out = self._combo(known, total, skipped, method,
                              f"English words carried into {self.meta['language']} - "
                              f"attested word pairs only")
            if method == "dictionary" and len(known) == 1:
                out["confidence"] = "medium"
            return out

        # Hindi source: two hops through English, words only, always labelled
        toks = words_of(text, "hi")
        known, skipped = [], []
        for t in toks:
            if t in HI_FUNCTION_WORDS:
                skipped.append(t)
                continue
            en = self.hi_en.get(t)
            if not en:
                skipped.append(t)
                continue
            w = self.word(en)
            if not w:
                skipped.append(t)
                continue
            if any(k["tgt"] == w["tgt"] for k in known):
                skipped.append(t)
                continue
            known.append({
                "hindi": t, "english": en, "tgt": w["tgt"], "score": w["score"],
                "chain": f"{t} → {en} → {w['tgt']}",
                "script": token_script(w["tgt"]),
                "source": w["source"], "phonetic": w.get("phonetic", False),
                "alts": w.get("alts") or [],
            })
        if not known:
            return self._decline(
                f"no {self.meta['language']} word for those Hindi words yet - "
                f"{len(self.pack.get('dictionary', []))} Hindi words are covered, "
                f"and only for the words the school dictionary lists",
                skipped=skipped)
        out = self._combo(
            known, len(toks), skipped, "pivot-en",
            f"Hindi → English → {self.meta['language']}: no Hindi–{self.meta['language']} "
            f"corpus exists yet, so these are word pairs only - read them out and build "
            f"the sentence in class")
        out["note"] = out["note"]
        out["bridge"] = "hi→en→" + self.code
        return out

    # ---------------------------------------------------------------- content
    def summary(self) -> dict:
        c = self.meta["counts"]
        return {
            "layers": {
                "attested_sentences": c.get("sentence_memory", 0),
                "machine_augmented_sentences": c.get("sentence_memory_aug", 0),
                "dictionary_en": c.get("dictionary_en", 0),
                "cognate_forms": c.get("cognates", 0),
                "hindi_reachable_words": c.get("dictionary_hi_pivot", 0),
            },
            "code": self.code,
            "language": self.meta["language"],
            "script": self.meta["script"],
            "register": self.meta.get("register"),
            "pivot": self.meta.get("pivot", "en"),
            "counts": c,
            "sources": self.meta.get("sources", []),
            "tts": self.tts_info(),
            "note": self.meta.get("note"),
            "hindi_supported": "words only (no parallel corpus)",
            "english_supported": "sentences",
        }


class Registry:
    """Routes a request to the pack for `target`."""

    def __init__(self, santhali_engine):
        self.sat = santhali_engine
        hi_en = self._hi_en_bridge(santhali_engine)
        self.hi_en_pairs = len(hi_en)
        self.packs = {p.code: p for p in (
            Pack(PACKS / "unr.json", hi_en),
            Pack(PACKS / "hoc.json", hi_en),
        )}

    @staticmethod
    def _hi_en_bridge(santhali_engine) -> dict[str, str]:
        """Hindi -> English from the curated classroom list and the Santhali pack.
        This is the same bridge the Santhali pack was designed around."""
        import sys
        sys.path.insert(0, str(ROOT / "pipelines"))
        from lexicon import N  # noqa: E402

        bridge = {hiw: enw.lower() for hiw, enw, _, _ in N}
        p = santhali_engine.pack
        for e in p.get("dictionary", []):
            if e.get("hi") and e.get("en"):
                bridge.setdefault(e["hi"], e["en"].lower())
        for e in p.get("vocab", []):
            if e.get("hindi") and e.get("english"):
                bridge.setdefault(e["hindi"], e["english"].lower())
        for e in p.get("phrases", []):
            if e.get("hindi") and e.get("english"):
                bridge.setdefault(e["hindi"], e["english"].lower())
        return bridge

    def has(self, code: str) -> bool:
        return code in self.packs or code == "sat"

    def get(self, code: str):
        return self.sat if code == "sat" else self.packs.get(code)

    def translate(self, text: str, source: str = "hi", target: str = "sat") -> dict:
        target = (target or "sat").strip()
        if target == "sat":
            return self.sat.translate(text, target="sat", source=source)
        pack = self.packs.get(target)
        if pack is None:
            return {"ok": False, "method": "declined", "kind": "none",
                    "confidence": "none", "sat": None, "target": None, "output": None,
                    "note": f"'{target}' is not a language this build serves",
                    "languages": [k for k in self.packs] + ["sat"]}
        if source not in ("hi", "en"):
            return pack._decline(f"source '{source}' is not accepted for "
                                 f"{pack.meta['language']}; use Hindi or English")
        return pack.translate(text, source=source)

    def list_languages(self) -> list[dict]:
        c = self.sat.pack["meta"]["counts"]
        sat = {
            "code": "sat", "language": "Santhali", "script": "Ol Chiki",
            "register": "classroom register (school dictionaries + parallel corpora)",
            "pivot": None,
            "counts": {"sentence_memory": c.get("sentence_memory", 0),
                       "vocab": c.get("vocab", 0), "phrases": c.get("phrases", 0),
                       "dictionary": c.get("dictionary_entries", c.get("dictionary", 0)),
                       "numbers": len(self.sat.pack.get("numbers") or {})},
            "layers": {"attested_sentences": c.get("sentence_memory", 0),
                       "machine_augmented_sentences": 0,
                       "dictionary_en": c.get("dictionary_entries", 0),
                       "cognate_forms": 0, "hindi_reachable_words": c.get("dictionary_entries", 0)},
            "sources": [{"name": "aiswarya9302/english-santali-combined", "license": "see dataset"},
                        {"name": "school dictionaries (uploads)", "license": "school material"}],
            "tts": {"available": True, "engine": "hi (gTTS)", "approx": True,
                    "why": "Ol Chiki -> Devanagari transliteration read by the Hindi voice"},
            "hindi_supported": "sentences and words",
            "english_supported": "sentences and words",
            "note": "full pack: Hindi-facing phrases, vocabulary, numbers, templates",
        }
        return [sat] + [p.summary() for p in self.packs.values()]
