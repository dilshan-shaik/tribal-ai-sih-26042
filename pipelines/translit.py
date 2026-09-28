"""
Ol Chiki (Santhali) -> Devanagari and Roman transliteration.

Why this exists
---------------
No public Santhali TTS voice model exists (checked Hugging Face + AI4Bharat).
To let Hindi-speaking teachers and Santhali students HEAR Santhali, we
transliterate Ol Chiki into Devanagari (matra/virama aware) and synthesise with
a Hindi voice model, giving a close phonetic approximation of the Santhali
sentence. The Roman form helps teachers who read Latin script.

Ol Chiki consonants have NO inherent vowel, so a consonant followed by a vowel
letter maps to consonant+matra in Devanagari, and to consonant+virama otherwise.
Reference: Unicode block U+1C50-U+1C7F (Ol Cemet' / Ol Chiki).
"""

# Ol Chiki vowel -> (independent devanagari, matra devanagari, roman)
_VOWELS = {
    "ᱚ": ("ऑ", "ॉ", "a"),    # LA      /ɔ/
    "ᱟ": ("आ", "ा", "ā"),    # LAA     /aː/
    "ᱟᱹ": ("अ", "", "a"),    # LAA+git  schwa [a]
    "ᱤ": ("इ", "ि", "i"),    # LI
    "ᱩ": ("उ", "ु", "u"),    # LU
    "ᱮ": ("ए", "े", "e"),    # LE
    "ᱳ": ("ओ", "ो", "o"),    # LO
}

# Ol Chiki consonant -> (devanagari, roman)
_CONS = {
    "ᱛ": ("त", "t"), "ᱜ": ("ग", "g"), "ᱝ": ("ङ", "ṅ"), "ᱞ": ("ल", "l"),
    "ᱠ": ("क", "k"), "ᱡ": ("ज", "j"), "ᱢ": ("म", "m"), "ᱣ": ("व", "w"),
    "ᱥ": ("स", "s"), "ᱦ": ("ह", "h"), "ᱧ": ("ञ", "ñ"), "ᱨ": ("र", "r"),
    "ᱪ": ("च", "c"), "ᱫ": ("द", "d"), "ᱬ": ("ण", "ṇ"), "ᱭ": ("य", "y"),
    "ᱯ": ("प", "p"), "ᱰ": ("ड", "ḍ"), "ᱱ": ("न", "n"), "ᱲ": ("ड़", "ṛ"),
    "ᱴ": ("ट", "ṭ"), "ᱵ": ("ब", "b"), "ᱶ": ("व", "v"), "ᱷ": ("ह", "h"),
}

_MU = "ᱸ"          # nasalisation -> anusvara
_GICHERED = "ᱹ"    # vowel shortening
_AHAD = "ᱼ"        # inherent-vowel suppression
_MUCAD = "ᱽ"       # checked/final consonant

_DIGITS = {chr(0x1C50 + i): ("०१२३४५६७८९"[i], str(i)) for i in range(10)}
_DANDA = {"᱾", "᱿"}
_VIRAMA = "\u094d"   # ्


def _core(text: str, roman: bool) -> str:
    out, i, n = [], 0, len(text)
    while i < n:
        ch = text[i]
        nxt = text[i + 1] if i + 1 < n else ""

        # vowel clusters (ᱟ / ᱟᱹ)
        if ch == "ᱟ" and nxt == _GICHERED:
            ind, mat, rom = _VOWELS["ᱟᱹ"]
            prev = out[-1] if out else ""
            if prev and _is_consonant(prev, roman):
                out.append("" if roman else mat)
            else:
                out.append(rom if roman else ind)
            i += 2
            continue

        if ch in _VOWELS:
            ind, mat, rom = _VOWELS[ch]
            prev = out[-1] if out else ""
            if prev and _is_consonant(prev, roman):
                out.append(rom if roman else mat)
            else:
                out.append(rom if roman else ind)
            i += 1
            continue

        if ch in _CONS:
            deva, rom = _CONS[ch]
            # look ahead: is a vowel letter (or ᱟᱹ) coming?
            after = text[i + 1: i + 3]
            silent = _AHAD in after[:1] or _MUCAD in after[:1] or _MU in after[:1] \
                or after == "" or (after[0] not in _VOWELS and after[:2] != "ᱟᱹ")
            if roman:
                out.append(rom)
                if silent and after[:1] in (_AHAD, _MUCAD):
                    i += 2
                    continue
            else:
                out.append(deva if silent and not after else deva)
                if silent:
                    out.append(_VIRAMA)
                if after[:1] in (_AHAD, _MUCAD):
                    i += 2
                    continue
            i += 1
            continue

        if ch == _MU:
            out.append("n" if roman else "ं")
            i += 1
            continue
        if ch == _GICHERED:
            i += 1
            continue
        if ch in (_AHAD, _MUCAD):
            i += 1
            continue
        if ch in _DIGITS:
            out.append(_DIGITS[ch][1] if roman else _DIGITS[ch][0])
            i += 1
            continue
        if ch in _DANDA:
            out.append(".")
            i += 1
            continue
        if ch == "᱾᱾":
            out.append("..")
            i += 1
            continue
        out.append(ch)
        i += 1

    s = "".join(out)
    while "  " in s:
        s = s.replace("  ", " ")
    return s.strip()


_DEVA_CONS = {v[0] for v in _CONS.values()} | {v[0] for v in _VOWELS.values()}


def _is_consonant(prev: str, roman: bool) -> bool:
    if roman:
        return prev.isalpha() and prev.lower() not in "aeiouā"
    return prev in _DEVA_CONS and prev not in "अआइईउऊएऐओऔ"


def to_devanagari(olchiki: str) -> str:
    """ᱫᱟᱨᱮ -> दारे"""
    return _core(olchiki, roman=False)


def to_roman(olchiki: str) -> str:
    """ᱫᱟᱨᱮ -> dāre"""
    return _core(olchiki, roman=True)


def is_olchiki(text: str) -> bool:
    return any("\u1c50" <= c <= "\u1c7f" for c in text)


# --- reverse direction, used to emit Ol Chiki for curated content ------------
_DEVA_IND_TO_OL = {v[0]: k for k, v in _VOWELS.items() if len(k) == 1}
_DEVA_CONS_TO_OL = {v[0]: k for k, v in _CONS.items()}


def devanagari_to_olchiki(text: str) -> str:
    """Best-effort reverse transliteration (दारे -> ᱫᱟᱨᱮ). Curated content only."""
    out, i, n = [], 0, len(text)
    while i < n:
        ch = text[i]
        if ch in _DEVA_CONS_TO_OL:
            cons = _DEVA_CONS_TO_OL[ch]
            j = i + 1
            if j < n and text[j] == _VIRAMA:
                out.append(cons)
                i += 2
                continue
            if j < n:
                for matra, ol in _MATRA_TO_OL.items():
                    if matra and text.startswith(matra, j):
                        out.append(cons + ol)
                        i = j + len(matra)
                        break
                else:
                    out.append(cons + "ᱚ")
                    i += 1
                    continue
                continue
            out.append(cons)
            i += 1
            continue
        if ch in _DEVA_IND_TO_OL:
            out.append(_DEVA_IND_TO_OL[ch])
            i += 1
            continue
        i += 1
    return "".join(out)


_MATRA_TO_OL = {"ा": "ᱟ", "": "", "ि": "ᱤ", "ु": "ᱩ", "े": "ᱮ", "ो": "ᱳ", "ॉ": "ᱚ"}


if __name__ == "__main__":
    samples = ["ᱫᱟᱨᱮ", "ᱥᱤᱸ", "ᱩᱞᱤ", "ᱤᱠᱟᱹ", "ᱟᱞᱮ ᱟᱧᱡᱚᱢᱟ ᱞᱮ",
               "ᱢᱤᱫᱴᱟᱹᱝ ᱯᱤᱴᱷᱟᱹ ᱾", "ᱫᱟ", "ᱚᱠᱟ", "ᱟᱢ ᱫᱚ ᱪᱮᱫ ᱧᱩᱛᱩᱢ"]
    for s in samples:
        print(f"{s:26} -> {to_devanagari(s):24} | {to_roman(s)}")
    print("\nreverse:", devanagari_to_olchiki("दारे"), devanagari_to_olchiki("पानी"))
