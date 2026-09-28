"""
Hindi -> Santhali translation engine for the MTB-MLE platform.

Design principle: **never invent Santhali.** Every output carries the method it
came from and how trustworthy it is, and anything composed rather than attested
is pushed into the native-speaker validation queue (PS section 17).

Cascade (first hit wins):
  1. phrase        exact Hindi hit in the classroom phrase book (attested)
  2. vocab         exact Hindi hit in the 193-word curated glossary
  3. title         exact Hindi hit in 6,900 Wikidata Hindi->Santhali titles
  4. template      instruction parsed as (verb, object) and realised in an
                   attested Santhali frame, e.g. "किताब बंद करो" ->
                   ᱯᱚᱛᱚᱵ ᱵᱚᱸᱫᱚᱭ ᱢᱮ!  (frame attested by ᱯᱚᱛᱚᱵ ᱵᱚᱸᱫᱚᱭ ᱢᱮ!)
  5. wordbank      no full sentence possible -> per-word Santhali glossary
                   ("vocabulary assist"), flagged needs_validation=true

Everything returns Ol Chiki + Devanagari (for the Hindi voice model) + Roman
(for teachers who read Latin script).
"""
from __future__ import annotations

import json
import re
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "pipelines"))
from translit import to_devanagari, to_roman  # noqa: E402
from odia import hindi_to_odia, is_odia, odia_key  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
PACK_PATH = ROOT / "data" / "language_packs" / "sat.json"
VERIFIED_PATH = ROOT / "data" / "verified.json"

DANDA = "।.?!᱾"


# English function words carry no usable meaning in a word-by-word gloss, and their
# corpus alignments are unreliable ("is" aligned to a dual marker, "during" to "child").
EN_STOPWORDS = {
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being", "am", "do",
    "does", "did", "of", "to", "in", "on", "at", "by", "for", "with", "from", "as",
    "and", "or", "but", "if", "then", "than", "that", "this", "these", "those",
    "it", "its", "he", "she", "they", "them", "his", "her", "their", "we", "our",
    "you", "your", "i", "my", "me", "will", "would", "shall", "should", "may",
    "might", "must", "can", "could", "have", "has", "had", "not", "no", "so",
    "such", "there", "here", "when", "while", "during", "however", "therefore",
    "also", "more", "most", "much", "many", "some", "any", "all", "each", "every",
    "other", "into", "over", "under", "about", "after", "before", "between",
    "based", "using", "used", "via", "per", "etc", "e", "g", "ie", "eg",
}


def fix_gicher(s: str) -> str:
    """Sources typed on a Latin keyboard write "." where Ol Chiki needs the gicher ᱹ
    (ᱜᱤᱫᱽᱨᱟ. is ᱜᱤᱫᱽᱨᱟᱹ). Only a "." between two Ol Chiki letters is rewritten."""
    if not isinstance(s, str):
        return s
    s = re.sub(r"(?<=[\u1C50-\u1C7F])\.(?=[\u1C50-\u1C7F])", "\u1c79", s)
    # a single word may also end with the dropped gicher: ᱜᱤᱫᱽᱨᱟ. is ᱜᱤᱫᱽᱨᱟᱹ
    if " " not in s:
        s = re.sub(r"(?<=[\u1C50-\u1C7F])\.$", "\u1c79", s)
    return s


# Hindi copulas and postpositions. They carry no standalone meaning a teacher can
# concatenate, and the corpus alignments for them are unreliable (है -> ᱠᱤᱱ is a dual
# marker, not "is"). They are excluded from a word list and counted as unknown.
HI_FUNCTION_WORDS = {
    "\u0939\u0948", "\u0939\u0948\u0902", "\u0939\u094b", "\u0939\u0941\u0906",
    "\u0925\u093e", "\u0925\u0940", "\u0925\u0947",
    "\u0915\u093e", "\u0915\u0940", "\u0915\u0947", "\u0915\u094b",
    "\u092e\u0947\u0902", "\u0938\u0947", "\u092a\u0930", "\u0928\u0947",
    "\u0915\u093e\u0915\u093e", "\u0935\u093e\u0932\u093e", "\u0935\u093e\u0932\u0940",
}


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFC", s or "").strip()
    s = re.sub(r"\s+", " ", s)
    # Devanagari nukta/composed-form normalisation so teacher typing always matches
    s = s.replace("ऩ", "न").replace("क़", "क").replace("ख़", "ख")
    s = s.replace("ज़", "ज").replace("फ़", "फ").replace("य़", "य")
    # the same word spelled two accepted ways in Hindi - teachers type either
    s = s.replace("कुहनी", "कोहनी").replace("कोहनी", "कोहनी")
    return s.strip(DANDA + " ")


def _strip_diacritics(s: str) -> str:
    return s.replace("ं", "").replace("ँ", "").replace("़", "").strip()


# Devanagari nasal-conjunct spellings people (and ASR models) mix up:
# बन्द / बंद, ठण्ड / ठंड, अन्त / अंत ...
_NASAL_FOLD = [("न्द", "ंद"), ("न्त", "ंत"), ("म्ब", "ंब"), ("ण्ड", "ंड"),
               ("ञ्च", "ंच"), ("ञ्ज", "ंज"), ("ङ्क", "ंक"), ("ङ्ग", "ंग"),
               ("ऩ", "न"), ("ॉ", "ो")]


def _fold(s: str) -> str:
    """Aggressive, symmetric normalisation used for matching only.
    Both the query and the stored phrase get folded, so an ASR transcript like
    "फल कहा है" still matches the stored "फल कहाँ है?"."""
    s = _norm(s)
    for a, b in _NASAL_FOLD:
        s = s.replace(a, b)
    return _strip_diacritics(s)


class Engine:
    def __init__(self, pack_path: Path = PACK_PATH):
        self.pack = json.load(open(pack_path, encoding="utf-8"))
        self.reload_indexes()

    # ------------------------------------------------------------------ indexes
    def reload_indexes(self):
        p = self.pack
        # Exact spellings live in their own index. Diacritic-stripped aliases live in a
        # SEPARATE index that is only consulted for words of 4+ characters - so
        # बन्द/बंद unify, while कहाँ -> कहा can never shadow the real word कहा (said).
        items = [v for v in p["vocab"] if v.get("sat")]
        self.vocab_hi = {_norm(v["hindi"]): v for v in items}
        self.vocab_alias = {}
        for v in items:
            key = _norm(v["hindi"])
            alias = _strip_diacritics(key)
            if alias != key and alias not in self.vocab_hi:
                self.vocab_alias.setdefault(alias, v)
        self.phrases_hi = {_norm(x["hindi"]): x for x in p["phrases"]}
        self.phrases_fold = {}
        for x in p["phrases"]:
            self.phrases_fold.setdefault(_fold(x["hindi"]), x)
        self.vocab_fold = {}
        for v in p["vocab"]:
            if v.get("sat"):
                self.vocab_fold.setdefault(_fold(v["hindi"]), v)
        self.titles_hi = {}
        for t in p["titles"]:
            self.titles_hi.setdefault(_norm(t["hi"]), t["sat"])
        self.lex = p["lexicon"]
        self.templates = {t["id"]: t for t in p["templates"]}
        self.verbs = p["verbs"]
        self.verbs_hi = {_norm(v["hindi"]): v for v in p["verbs"]
                         if v.get("hindi") and v.get("sat")}
        # Odia side: Santhali sentences that came out of the Odia-script training file
        # (already decoded to Ol Chiki) plus the Odia->Hindi sentences it produced.
        # Hindi -> Santhali dictionary from the team-supplied Santhali dictionaries
        self.dictionary = {}
        for e in p.get("dictionary") or []:
            key = _norm(e.get("hi", ""))
            if key and e.get("sat"):
                e = dict(e)
                # same shape as the curated vocabulary, so the word bank and the
                # flashcard/worksheet builders can use these rows too
                e["hindi"] = e.get("hi")
                e["english"] = e.get("en")
                e["emoji"] = e.get("emoji") or ""
                self.dictionary.setdefault(key, e)
        self.dictionary_fold = {}
        for key, e in self.dictionary.items():
            self.dictionary_fold.setdefault(_fold(key), e)
        # 0-100 + thousands, both directions
        self.numbers = p.get("numbers") or {}
        self.numbers_by_hi = {_norm(v["hi"]): k for k, v in self.numbers.items()
                              if v.get("hi")}
        self.odia_memory = {}
        for rec in p.get("odia_memory") or []:
            self.odia_memory[_norm(rec.get("or_script", ""))] = rec
        self.odia_memory_key = {odia_key(r.get("or_script", "")): r
                                for r in p.get("odia_memory") or []
                                if r.get("sat") and r.get("or_script")}
        self.odia_spellings = p.get("odia_script") or {}
        # English -> Santhali: the corpus sentence memory is English-keyed, and the
        # uploaded dictionaries carry an English headword for every entry, so an
        # English-medium page can be handled without going through Hindi at all.
        self.memory_en = {}
        for rec in p.get("sentence_memory") or []:
            key = _norm(rec.get("en", "")).lower()
            if key and rec.get("sat"):
                self.memory_en.setdefault(key, rec)
        self.memory_en_fold = {_fold(k): v for k, v in self.memory_en.items()}
        self.dictionary_en = {}
        for e in self.dictionary.values():
            key = _norm(e.get("english") or "").lower()
            if key:
                self.dictionary_en.setdefault(key, e)
        # the aligned English<->Santhali lexicon (17k surface forms). Only the solid
        # entries are kept: a clean alphabetic headword and a decent alignment score.
        self.lexicon_en = {}
        for w, rec in (p.get("lexicon") or {}).items():
            key = (w or "").strip().lower()
            if (not key or not key.isalpha() or len(key) < 2
                    or not rec.get("sat") or (rec.get("score") or 0) < 0.90):
                continue
            self.lexicon_en.setdefault(key, rec)
        self.gloss_en = {}
        for v in p.get("vocab") or []:
            key = _norm(v.get("english") or "").lower()
            if key and v.get("sat"):
                self.gloss_en.setdefault(key, v)
        self.odia_hindi = p.get("odia_hindi") or []
        self.odia_hindi_index = {_norm(r["or"]): r for r in self.odia_hindi if r.get("or")}
        # teacher-verified overrides (human-in-the-loop, PS section 17)
        self.verified = json.load(open(VERIFIED_PATH, encoding="utf-8")) if VERIFIED_PATH.exists() else {}
        for k, v in self.verified.items():
            if v.get("sat") and v.get("scope") == "phrase":
                self.phrases_hi[_norm(k)] = {**self.phrases_hi.get(_norm(k), {}),
                                             "hindi": k, "sat": v["sat"], "kind": "verified",
                                             "confidence": "high", "verified": True,
                                             "sat_deva": to_devanagari(v["sat"]),
                                             "sat_roman": to_roman(v["sat"]),
                                             "source": "native-speaker"}
            elif v.get("sat") and v.get("scope") == "vocab" and _norm(k) in self.vocab_hi:
                self.vocab_hi[_norm(k)].update(sat=v["sat"], verified=True, confidence="high",
                                               source="native-speaker",
                                               sat_deva=to_devanagari(v["sat"]),
                                               sat_roman=to_roman(v["sat"]))

    # ------------------------------------------------------------- hi->en gloss
    def gloss(self, word: str):
        w = _norm(word)
        hit = self.vocab_hi.get(w)
        if hit is None and len(w) >= 4:
            hit = self.vocab_alias.get(w) or self.vocab_alias.get(_strip_diacritics(w))
        return hit

    # ------------------------------------------------------------------ helpers
    @staticmethod
    def wrap(sat: str) -> dict:
        sat = fix_gicher(sat or "")
        return {"olchiki": sat, "devanagari": to_devanagari(sat), "roman": to_roman(sat)}

    # a sentence below this confidence is not shown at all - see word_combo()
    MIN_CONFIDENCE = "medium"
    _WEAK = ("low", "none", "-", "")

    def _gate(self, out: dict, src: str):
        """Never hand back a sentence we do not stand behind.

        Anything that came out of the cascade with low confidence is replaced by the
        word combination, and the discarded sentence is kept in `suppressed` (and sent to
        the validation queue) so nothing is lost - it just is not shown as an answer.
        """
        if not out or out.get("method") == "word-combo":
            return out
        conf = out.get("confidence")
        weak = conf in self._WEAK
        if not weak:
            return out
        combo = self.word_combo(src)
        if out.get("sat"):
            combo["suppressed"] = {"method": out.get("method"), "confidence": conf,
                                   "sat": (out.get("sat") or {}).get("olchiki"),
                                   "why": "below the confidence a sentence needs to be shown"}
        return combo

    def word_combo(self, text: str):
        """The words we know for this text, in the order they appear.

        This is what a teacher gets whenever we cannot offer a *confident* sentence.
        A guessed sentence is worse than an honest word list: a word list can be read
        out and completed by the teacher, a wrong sentence cannot be un-read.
        """
        bank = self.wordbank(text)
        tokens = [_norm(t) for t in re.split(r"[\s,\u0964]+", text) if _norm(t)]
        combined = " ".join(w["sat"] for w in bank)
        roman = " ".join(w.get("sat_roman") or "" for w in bank).strip()
        return {
            "ok": False, "method": "word-combo", "kind": "words",
            "confidence": "low" if bank else "none", "verified": False,
            "sat": None, "component": None,
            "words": bank, "wordbank": bank,
            "combined": combined or None, "combined_roman": roman or None,
            "known": len(bank), "total": len(tokens),
            "skipped": list(getattr(self, "_last_skipped", [])),
            "coverage": round(len(bank) / len(tokens), 3) if tokens else 0.0,
            "hindi_gloss": None, "english_gloss": None,
            "evidence": None, "needs_validation": True,
            "note": "no confident sentence for this text - these are the words we know, "
                    "in order; read them out and build the sentence yourself",
        }

    def wordbank(self, text: str):
        """Per-word Santhali glossary for anything we cannot render as a sentence."""
        tokens = [_norm(t) for t in re.split(r"[\s,।]+", text) if _norm(t)]
        out, skipped = [], []
        for t in tokens:
            if t in HI_FUNCTION_WORDS:
                skipped.append(t)
                continue
            v = (self.gloss(t) or self.dictionary.get(t)
                 or self.dictionary_fold.get(_fold(t))
                 or self.dictionary.get(t.replace("\u0941", "").replace("\u0942", "")))
            if v is None:                      # try trimming Hindi case endings
                for suf in ("\u094b\u0902", "\u093f\u092f\u094b\u0902", "\u0947\u0902", "\u0947",
                            "\u0940", "\u093e", "\u0915\u094b", "\u0928\u0947",
                            "\u0938\u0947", "\u092e\u0947\u0902", "\u092a\u0930",
                            "\u0915\u093e", "\u0915\u0940", "\u0915\u0947"):
                    if t.endswith(suf) and len(t) > len(suf) + 1:
                        v = (self.gloss(t[: -len(suf)])
                             or self.dictionary.get(t[: -len(suf)])
                             or self.dictionary_fold.get(_fold(t[: -len(suf)])))
                        if v:
                            break
            if v is None:                      # a number written as a word or in digits
                num = self.lookup_number(t)
                if num:
                    v = {"hindi": t, "english": None, "sat": num["sat"],
                         "sat_deva": None, "sat_roman": None, "emoji": "\U0001F522",
                         "verified": False}
            if v:
                out.append({"hindi": v["hindi"], "english": v["english"], "sat": v["sat"],
                            "sat_deva": v["sat_deva"], "sat_roman": v["sat_roman"],
                            "emoji": v.get("emoji"), "verified": v.get("verified", False)})
        self._last_skipped = skipped
        return out

    # ------------------------------------------------------- instruction parsing
    VERB_PATTERNS = [
        ("where",    r"(.*?)\s*(कहाँ|कहां)\s*(है|हैं)\s*$"),
        ("howmany",  r"कितने\s+(.+?)\s*(हैं|है)\s*$"),
        ("thisis",   r"^यह\s+(?:एक\s+)?(.+?)\s*(है|हैं)\s*$"),
        ("myname",   r"^मेरा\s+नाम\s+(.+?)\s+है\s*$"),
        ("close",    r"(.*?)\s*बंद\s+करो\s*$"),
        ("open",     r"(.*?)\s*खोलो\s*$"),
        ("read",     r"(.*?)\s*पढ़ो\s*$"),
        ("write",    r"(.*?)\s*लिखो\s*$"),
        ("look",     r"(.*?)\s*देखो\s*$"),
        ("take",     r"(.*?)\s*(?:ले\s+लो|लो)\s*$"),
        ("give",     r"(.*?)\s*दो\s*$"),
        ("drink",    r"(.*?)\s*पियो\s*$"),
        ("play",     r"(.*?)\s*गाओ\s*$"),
    ]

    def try_template(self, text: str):
        # Patterns are matched on the folded text (so ASR spellings like "बन्द" work),
        # but the object noun is re-read from the ORIGINAL text as well, because
        # folding drops nukta/matras and would stop पेड़ from matching its entry.
        t = _fold(text)
        raw = _norm(text)
        for tid, pat in self.VERB_PATTERNS:
            m = re.match(pat, t)
            if not m or tid not in self.templates:
                continue
            obj_hi = _norm(m.group(1)) if m.lastindex else ""
            if obj_hi:
                m_raw = re.match(pat, raw) or re.match(pat.replace("है|हैं", "है|हैं"), raw)
                if m_raw and m_raw.lastindex:
                    raw_obj = _norm(m_raw.group(1))
                    if self.gloss(raw_obj):
                        obj_hi = raw_obj
            tmpl = self.templates[tid]
            # "where is X" / "this is a X" only need the noun
            v = self.gloss(obj_hi) if obj_hi else None
            if v is None and obj_hi:
                for extra in [obj_hi + "?", obj_hi]:
                    v = self.gloss(extra)
                    if v:
                        break
            if v is None and tid not in ("thisis", "myname", "howmany"):
                return None                      # cannot fill the frame -> word bank
            if tid in ("thisis",) and v is None:
                return None
            sat = tmpl["frame"].replace("{obj}", v["sat"] if v else "")
            return {
                "sat": sat,
                "hindi_gloss": tmpl["hindi_frame"].format(hi=v["hindi"] if v else ""),
                "english_gloss": tmpl["english_frame"].format(en=v["english"] if v else ""),
                "template": tid,
                "evidence": tmpl["evidence"],
                "confidence": tmpl["confidence"],
                "component": v,
            }
        return None

    # ------------------------------------------------------------------- public
    def translate(self, text: str, target: str = "sat", source: str = "hi"):
        """
        source = 'hi'   Hindi  -> Santhali   (the translation this platform does)
                 'or'   Odia   -> Santhali   DIRECT, and only when that exact sentence
                        is already in the trained Odia translation memory. There is no
                        Odia -> Hindi -> Santhali chain any more: Odia never generates a
                        Santhali sentence, it only returns one we already hold.
                 'auto' detect Odia script and do the direct lookup

        The Odia half of `odia_train.txt` is old mission-era print, so a sentence that is
        not in memory is declined honestly instead of being invented.
        """
        src = _norm(text)
        if not src:
            return {"ok": False, "error": "empty input"}

        if source == "or" or (source == "auto" and is_odia(text)):
            return self._gate(self.odia_direct(text), src)
        return self._gate(self._cascade(src), src)

    def odia_direct(self, text: str):
        """Direct Odia -> Santhali: look the sentence up in the Odia translation memory.

        Two probes, both exact - nothing is generated:
          1. the input as pasted
          2. the input converted to Odia script first (the same sentence typed in
             Devanagari, or with different punctuation/spacing)
        """
        src = _norm(text)

        def answer(rec, how):
            return {"ok": True, "method": "odia-direct", "confidence": "medium",
                    "kind": "sentence-memory", "verified": False,
                    "sat": self.wrap(rec["sat"]), "english_gloss": None,
                    "hindi_gloss": rec.get("hindi") or None,
                    "evidence": f"odia_train.txt - already-decoded Santhali sentence "
                                f"(matched {how}); no Hindi step, no generation",
                    "component": None, "wordbank": [], "needs_validation": True,
                    "source_language": "or"}

        rec = self.odia_memory.get(src) or self.odia_memory_key.get(odia_key(src))
        if rec and rec.get("sat"):
            return answer(rec, "as pasted")

        # the same sentence written in Devanagari (a teacher may type Hindi letters)
        if not is_odia(text):
            as_odia = hindi_to_odia(src)
            rec = (self.odia_memory.get(_norm(as_odia))
                   or self.odia_memory_key.get(odia_key(as_odia)))
            if rec and rec.get("sat"):
                return answer(rec, "after conversion to Odia script")

        return {"ok": False,
                "error": "this sentence is not in the trained Odia translations",
                "method": "declined", "source_language": "or",
                "hint": "Odia is answered directly from memory only; for anything new, "
                        "type the Hindi and it will be translated to Santhali.",
                "wordbank": []}

    def _cascade(self, src: str):
        # 1. classroom phrase book (attested / teacher-verified)
        ph = self.phrases_hi.get(src) or self.phrases_fold.get(_fold(src))
        if ph:
            ph = dict(ph)
            return {"ok": True, "method": "phrase", "confidence": ph.get("confidence", "medium"),
                    "kind": ph.get("kind"), "verified": ph.get("verified", False),
                    "sat": self.wrap(ph["sat"]), "english_gloss": ph.get("english"),
                    "hindi_gloss": ph["hindi"], "evidence": ph.get("evidence"),
                    "component": None, "wordbank": [],
                    "needs_validation": ph.get("confidence") != "high"}

        # 2. curated glossary (single word)
        v = self.gloss(src)
        if v:
            return {"ok": True, "method": "vocab", "confidence": v["confidence"],
                    "kind": "word", "verified": v.get("verified", False),
                    "sat": self.wrap(v["sat"]), "english_gloss": v["english"],
                    "hindi_gloss": v["hindi"], "emoji": v.get("emoji"),
                    "evidence": v.get("source"), "component": v, "wordbank": [],
                    "needs_validation": v["confidence"] != "high"}

        # 2b. numeric input - digits or a Hindi number word, answered from the
        #     compositional number table (ᱜᱮᱞ ᱢᱤᱫ = ten-one = eleven)
        num = self.lookup_number(src)
        if num:
            return {"ok": True, "method": "number", "confidence": "high",
                    "kind": "number", "verified": False, "sat": self.wrap(num["sat"]),
                    "english_gloss": num.get("en"), "hindi_gloss": num["hi"],
                    "evidence": "compositional Santhali numerals (ᱜᱮᱞ ᱢᱤᱫ = 11, "
                                "ᱵᱟᱨ ᱜᱮᱞ = 20), confirmed by the team dictionaries",
                    "component": None, "wordbank": [], "needs_validation": False}

        # 2c. the Hindi -> Santhali dictionary built from the team-supplied
        #     English<->Santhali files (every entry has a Hindi side)
        d = self.dictionary.get(src) or self.dictionary_fold.get(_fold(src))
        if d:
            return {"ok": True, "method": "dictionary",
                    "confidence": d.get("confidence", "medium"),
                    "kind": "word", "verified": False, "sat": self.wrap(d["sat"]),
                    "english_gloss": d.get("en"), "hindi_gloss": d.get("hi"),
                    "emoji": None,
                    "evidence": f"{d.get('source')} (Hindi side: {d.get('hindi_source')})",
                    "component": None, "wordbank": [],
                    "needs_validation": d.get("confidence") != "high"}

        # 2d. the sentence is not one the Hindi side knows, but it may be one the
        #     Odia half already gave us a Santhali answer for: convert the Hindi to
        #     Odia and look it up in the Odia translation memory (attested only)
        for candidate in {hindi_to_odia(src), src}:
            key = odia_key(candidate)
            rec = self.odia_memory.get(_norm(candidate)) or self.odia_memory_key.get(key)
            if rec and rec.get("sat"):
                return {"ok": True, "method": "odia-direct", "confidence": "medium",
                        "kind": "sentence-memory", "verified": False,
                        "sat": self.wrap(rec["sat"]), "english_gloss": None,
                        "hindi_gloss": rec.get("hindi") or None,
                        "evidence": "odia_train.txt - already-decoded Santhali sentence "
                                    "found after converting the Hindi input to Odia; "
                                    "no Hindi translation step, no generation",
                        "component": None, "wordbank": [], "needs_validation": True}

        # 3. Wikidata Hindi->Santhali title memory (names, places, concepts)
        if src in self.titles_hi:
            sat = self.titles_hi[src]
            return {"ok": True, "method": "wikidata", "confidence": "medium",
                    "kind": "name", "verified": False, "sat": self.wrap(sat),
                    "english_gloss": None, "hindi_gloss": src,
                    "evidence": "wikidata sat.wikipedia <-> hi.wikipedia sitelink",
                    "component": None, "wordbank": [], "needs_validation": True}

        # 4. instruction template inside an attested Santhali frame
        tpl = self.try_template(src)
        if tpl:
            return {"ok": True, "method": "template", "confidence": tpl["confidence"],
                    "kind": "instruction", "verified": False,
                    "sat": self.wrap(tpl["sat"]), "english_gloss": tpl["english_gloss"],
                    "hindi_gloss": tpl["hindi_gloss"], "evidence": tpl["evidence"],
                    "component": tpl["component"], "wordbank": [],
                    "needs_validation": tpl["confidence"] != "high"}

        # 4b. bare imperative that is attested in the verb table, e.g. "बताओ",
        #     "चलो", "लो", "बंद करो" with no object. Deliberately AFTER the
        #     glossary so "दो" stays the number two and "देखो" stays ᱧᱮᱞ.
        vb = self.verbs_hi.get(src) or self.verbs_hi.get(_fold(src))
        if vb:
            return {"ok": True, "method": "verb", "confidence": "high",
                    "kind": "instruction", "verified": False,
                    "sat": self.wrap(vb["sat"]), "english_gloss": vb.get("english"),
                    "hindi_gloss": vb["hindi"], "evidence": vb.get("evidence"),
                    "component": None, "wordbank": [], "needs_validation": False}

        # 5. nothing confident: the combination of the words we know
        return self.word_combo(src)

    def vocab_pool(self) -> list[dict]:
        """Everything the classroom material may draw from: the curated word list
        first (it keeps its category names), then the Hindi -> Santhali dictionary
        rebuilt from the school's files, mapped onto the same shape so flashcards,
        quizzes and worksheets can use it. Dictionary rows are marked unverified -
        they still go through the teacher's validation queue."""
        pool = list(self.pack["vocab"])
        seen = {(v.get("hindi"), v.get("sat")) for v in pool}
        for e in self.dictionary.values():
            if not e.get("sat") or (e["hindi"], e["sat"]) in seen:
                continue
            seen.add((e["hindi"], e["sat"]))
            pool.append({
                "hindi": e["hindi"], "english": e.get("english"),
                "sat": e["sat"], "sat_deva": e.get("sat_deva"),
                "sat_roman": e.get("sat_roman"),
                "category": e.get("theme") or "general",
                "emoji": e.get("emoji") or "",
                "source": e.get("source"), "confidence": e.get("confidence", "medium"),
                "alternates": e.get("variants") or [], "verified": False,
                "from_dictionary": True,
            })
        return pool

    def english_to_santhali(self, text: str):
        """English -> Santhali. Used for English-medium pages in a PDF: the corpus
        sentence memory first, then the uploaded dictionaries, then the Hindi pivot."""
        src = _norm(text)
        key = src.lower()
        rec = self.memory_en.get(key) or self.memory_en_fold.get(_fold(key))
        # the corpus memory also holds fragments like "Mouth water." - a fragment is not
        # a translation, so a memory hit has to look like a sentence
        if rec and len(key.split()) < 4:
            rec = None
        if rec:
            return {"ok": True, "method": "en-memory", "confidence": "medium",
                    "kind": "sentence-memory", "verified": False,
                    "sat": self.wrap(rec["sat"]), "english_gloss": rec.get("en"),
                    "hindi_gloss": None,
                    "evidence": "English sentence memory built from the parallel corpora",
                    "component": None, "wordbank": [], "needs_validation": True}
        d = self.dictionary_en.get(key)
        if d:
            return {"ok": True, "method": "dictionary", "confidence": "high",
                    "kind": "word", "verified": False, "sat": self.wrap(d["sat"]),
                    "english_gloss": d.get("english"), "hindi_gloss": d.get("hindi"),
                    "evidence": f"{d.get('source')} (English headword)",
                    "component": None, "wordbank": [], "needs_validation": False}
        v = self.gloss_en.get(key)
        if v:
            return {"ok": True, "method": "vocab", "confidence": v["confidence"],
                    "kind": "word", "verified": v.get("verified", False),
                    "sat": self.wrap(v["sat"]), "english_gloss": v["english"],
                    "hindi_gloss": v["hindi"], "evidence": "project vocabulary",
                    "component": None, "wordbank": [], "needs_validation": False}
        lex = self.lexicon_en.get(key)
        if lex and lex.get("sat"):
            return {"ok": True, "method": "en-lexicon",
                    "confidence": "medium",
                    "kind": "word", "verified": False, "needs_check": True,
                    "sat": self.wrap(lex["sat"]), "english_gloss": src,
                    "hindi_gloss": None,
                    "evidence": "aligned English-Santhali parallel corpora "
                                f"(alignment score {lex.get('score')})",
                    "component": None, "wordbank": [], "needs_validation": True}
        return self.word_combo(text)

    def lookup_any(self, word: str):
        """One word, from any side, for word-by-word glossing.

        Returns (santhali, needs_check). Confirmed sources first (the uploaded
        dictionaries, the project word list, the number system); the machine-aligned
        corpus lexicon last, and only at a high score, marked for the teacher to check.
        """
        w = _norm(word)
        if not w or w.lower() in EN_STOPWORDS:
            return None, False
        for key in (w, w.lower()):
            for table in (self.vocab_hi, self.dictionary, self.dictionary_en,
                          self.gloss_en, self.memory_en):
                rec = table.get(key) or table.get(_fold(key))
                if rec and rec.get("sat"):
                    return fix_gicher(rec["sat"]), False
        rec = self.lexicon_en.get(w.lower())
        if rec and rec.get("sat"):
            return fix_gicher(rec["sat"]), True
        # numbers typed as digits ("5" -> ᱢᱚᱬᱮ) belong to the number system
        num = self.lookup_number(w)
        if num:
            return num["sat"], False
        return None, False

    def lookup_number(self, text: str):
        """'25', '२५' or 'पच्चीस' -> the Santhali number word."""
        t = _norm(text)
        digits = {"०": "0", "१": "1", "२": "2", "३": "3", "४": "4", "५": "5",
                  "६": "6", "७": "7", "८": "8", "९": "9"}
        for a, b in digits.items():
            t = t.replace(a, b)
        t = t.replace("᱐", "0").replace("᱑", "1").replace("᱒", "2").replace("᱓", "3") \
             .replace("᱔", "4").replace("᱕", "5").replace("᱖", "6") \
             .replace("᱗", "7").replace("᱘", "8").replace("᱙", "9")
        t = t.strip("।.?! ")
        key = t if t in self.numbers else self.numbers_by_hi.get(t)
        if key is None:
            return None
        rec = dict(self.numbers[key])
        rec["en"] = self._number_english(int(key)) if key.isdigit() else None
        return rec

    @staticmethod
    def _number_english(n: int) -> str:
        units = ["zero", "one", "two", "three", "four", "five", "six", "seven",
                 "eight", "nine", "ten", "eleven", "twelve", "thirteen", "fourteen",
                 "fifteen", "sixteen", "seventeen", "eighteen", "nineteen"]
        tens = {20: "twenty", 30: "thirty", 40: "forty", 50: "fifty", 60: "sixty",
                70: "seventy", 80: "eighty", 90: "ninety"}
        if n < 20:
            return units[n]
        if n in tens:
            return tens[n]
        if n < 100:
            return f"{tens[n // 10 * 10]} {units[n % 10]}"
        return {100: "hundred", 1000: "thousand", 10000: "ten thousand",
                100000: "one lakh", 1000000: "ten lakh", 10000000: "one crore"}.get(n, str(n))

    def odia_hindi_lexicon_size(self):
        """How many Odia words the curated Odia->Hindi lexicon covers."""
        try:
            from odia import ODIA_HINDI
            return len(ODIA_HINDI)
        except Exception:                                    # noqa: BLE001
            return 0

    # ---------------------------------------------------------------- reporting
    def summary(self):
        p = self.pack
        return {"meta": p["meta"], "counts": p["meta"]["counts"],
                "verified_overrides": len(self.verified),
                "categories": sorted({v["category"] for v in p["vocab"]})}
