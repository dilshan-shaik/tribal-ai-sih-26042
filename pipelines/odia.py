"""
Odia  ->  Hindi  ->  Santhali  bridge.

Why this exists
---------------
The training file `data/raw/odia_train.txt` is an Odia <-> Santhali resource, and both
sides are written in Odia script. Santhali has its own script (Ol Chiki, 1925), but the
mission-era texts that this corpus comes from were printed in Odia script, which is why
the Santhali half looks like Odia.

Our platform answers Hindi -> Santhali, so this module does the two conversions the
corpus needs:

  1. Odia  -> Hindi            (so the Odia half can drive the Hindi engine)
       - a curated Odia -> Hindi lexicon for the words this corpus actually uses
         (Odia is SOV and shares its Sanskritic layer, so word order survives the swap)
       - an Odia -> Devanagari transliterator for everything else, so an unmapped word
         still comes out readable to a Hindi speaker instead of being dropped
  2. Odia script -> Ol Chiki   (so the Santhali half becomes usable Santhali text)
       - Odia has an inherent vowel, Ol Chiki does NOT, and this old orthography
         writes both ᱟ and ᱚ with the same Odia letters. So a straight letter swap
         cannot work: we emit every plausible spelling of a word and keep the one that
         is an existing Santhali word (see build_odia_corpus.py, which feeds in the
         known-form index).

Nothing here is guessed into the app silently: everything carries a `mode`
('lexicon' / 'translit' / 'decoded') and a resolution score.
"""

import re

# ---------------------------------------------------------------- Odia -> Devanagari
INDEPENDENT = {
    "ଅ": "अ", "ଆ": "आ", "ଇ": "इ", "ଈ": "ई", "ଉ": "उ", "ଊ": "ऊ", "ଋ": "ऋ",
    "ଏ": "ए", "ଐ": "ऐ", "ଓ": "ओ", "ଔ": "औ",
}
CONSONANTS = {
    "କ": "क", "ଖ": "ख", "ଗ": "ग", "ଘ": "घ", "ଙ": "ङ",
    "ଚ": "च", "ଛ": "छ", "ଜ": "ज", "ଝ": "झ", "ଞ": "ञ",
    "ଟ": "ट", "ଠ": "ठ", "ଡ": "ड", "ଢ": "ढ", "ଣ": "ण",
    "ତ": "त", "ଥ": "थ", "ଦ": "द", "ଧ": "ध", "ନ": "न",
    "ପ": "प", "ଫ": "फ", "ବ": "ब", "ଭ": "भ", "ମ": "म",
    "ଯ": "य", "ର": "र", "ଲ": "ल", "ଳ": "ल", "ୱ": "व", "ଵ": "व",
    "ଶ": "श", "ଷ": "ष", "ସ": "स", "ହ": "ह", "ୟ": "य",
    "ଡ଼": "ड़", "ଢ଼": "ढ़",
}
MATRAS = {
    "ା": "ा", "ି": "ि", "ୀ": "ी", "ୁ": "ु", "ୂ": "ू", "ୃ": "ृ",
    "େ": "े", "ୈ": "ै", "ୋ": "ो", "ୌ": "ौ", "\u0b4d": "\u094d",
}
SIGNS = {"ଂ": "ं", "ଃ": "ः", "ଁ": "ँ"}
DIGITS = {chr(0x0B66 + i): "०१२३४५६७८९"[i] for i in range(10)}

# Odia letters that stand for an Ol Chiki letter (Santhali side)
OL_CONS = {
    "କ": "ᱠ", "ଖ": "ᱠᱷ", "ଗ": "ᱜ", "ଘ": "ᱜᱷ", "ଙ": "ᱝ",
    "ଚ": "ᱪ", "ଛ": "ᱪᱷ", "ଜ": "ᱡ", "ଝ": "ᱡᱷ", "ଞ": "ᱧ",
    "ଟ": "ᱴ", "ଠ": "ᱴᱷ", "ଡ": "ᱰ", "ଢ": "ᱰᱷ", "ଣ": "ᱬ",
    "ତ": "ᱛ", "ଥ": "ᱛᱷ", "ଦ": "ᱫ", "ଧ": "ᱫᱷ", "ନ": "ᱱ",
    "ପ": "ᱯ", "ଫ": "ᱯᱷ", "ବ": "ᱵ", "ଭ": "ᱵᱷ", "ମ": "ᱢ",
    "ଯ": "ᱭ", "ର": "ᱨ", "ଲ": "ᱞ", "ଳ": "ᱞ", "ୱ": "ᱶ", "ଵ": "ᱶ",
    "ଶ": "ᱥ", "ଷ": "ᱥ", "ସ": "ᱥ", "ହ": "ᱦ", "ୟ": "ᱭ",
    "ଡ଼": "ᱲ", "ଢ଼": "ᱲ",
}
OL_VOW = {"ଅ": "ᱚ", "ଆ": "ᱟ", "ଇ": "ᱤ", "ଈ": "ᱤ", "ଉ": "ᱩ", "ଊ": "ᱩ",
          "ଏ": "ᱮ", "ଐ": "ᱟᱭ", "ଓ": "ᱳ", "ଔ": "ᱟᱣ"}
OL_MATRA = {"ା": "ᱟ", "ି": "ᱤ", "ୀ": "ᱤ", "ୁ": "ᱩ", "ୂ": "ᱩ", "ୃ": "ᱨᱩ",
            "େ": "ᱮ", "ୈ": "ᱟᱭ", "ୋ": "ᱚ", "ୌ": "ᱟᱣ"}
VIRAMA = "\u0b4d"
OLCHIKI_RE = re.compile(r"[\u1C50-\u1C7F]+")
ODIA_RE = re.compile(r"[\u0B00-\u0B7F]+")
ODIA_TOKEN_RE = re.compile(r"[\u0B00-\u0B7F]+|[0-9]+")


def is_odia(text: str) -> bool:
    """True when the text looks like Odia script rather than Devanagari/Ol Chiki."""
    odia = len(ODIA_RE.findall(text.replace(" ", "")))
    if not odia:
        return False
    deva = sum(1 for c in text if "\u0900" <= c <= "\u097F")
    return odia > deva


def odia_to_devanagari(text: str) -> str:
    """ଓଡ଼ିଶା -> ओड़िशा. Mechanical script conversion, no translation."""
    out = []
    for ch in text:
        if ch in INDEPENDENT:
            out.append(INDEPENDENT[ch])
        elif ch in CONSONANTS:
            out.append(CONSONANTS[ch])
        elif ch in MATRAS:
            out.append(MATRAS[ch])
        elif ch in SIGNS:
            out.append(SIGNS[ch])
        elif ch in DIGITS:
            out.append(DIGITS[ch])
        elif ch == "\u0b70":                      # Odia isshar
            out.append("\u0970")
        else:
            out.append(ch)
    return "".join(out)


def devanagari_to_olchiki_flexible(word: str):
    """
    Every plausible Ol Chiki spelling of an Odia-script word.

    The ambiguity is real: this orthography writes ᱟ (a) and ᱚ (ɔ) with the same Odia
    letters, and Ol Chiki consonants carry no inherent vowel, so କ can be ᱠ, ᱠᱚ or ᱠᱟ.
    The caller keeps whichever candidate is an attested Santhali word.
    """
    slots = []
    i, n = 0, len(word)
    while i < n:
        ch = word[i]
        if ch in OL_CONS:
            cons = OL_CONS[ch]
            if i + 1 < n and word[i + 1] == VIRAMA:          # explicit bare consonant
                slots.append([cons])
                i += 2
                continue
            if i + 1 < n and word[i + 1] in OL_MATRA:
                slots.append([cons + OL_MATRA[word[i + 1]]])
                i += 2
                continue
            slots.append([cons, cons + "ᱚ", cons + "ᱟ"])    # inherent vowel: unknown
            i += 1
            continue
        if ch in OL_VOW:
            slots.append([OL_VOW[ch]])
            i += 1
            continue
        i += 1
    if not slots:
        return []
    out = [""]
    for options in slots:                                     # small cartesian product
        out = [a + b for a in out for b in options]
        if len(out) > 4000:
            break
    return out


def decode_odia_word(word: str, known_forms):
    """
    -> (olchiki, how)   how = 'known' (an attested Santhali word matched),
                            'default' (letter-for-letter fallback)
    """
    cands = devanagari_to_olchiki_flexible(word)
    if not cands:
        return "", "empty"
    for c in cands:
        if c in known_forms:
            return c, "known"
    # fall back to the most common spelling convention in this corpus:
    # inherent vowel = ᱚ, ା = ᱟ, ୋ = ᱚ
    cons, i, n, out = OL_CONS, 0, len(word), []
    while i < n:
        ch = word[i]
        if ch in cons:
            if i + 1 < n and word[i + 1] == VIRAMA:
                out.append(cons[ch]); i += 2; continue
            if i + 1 < n and word[i + 1] in OL_MATRA:
                out.append(cons[ch] + OL_MATRA[word[i + 1]]); i += 2; continue
            out.append(cons[ch] + "ᱚ"); i += 1; continue
        if ch in OL_VOW:
            out.append(OL_VOW[ch]); i += 1; continue
        i += 1
    return "".join(out), "default"


# --------------------------------------------------------------- Odia -> Hindi words
# Curated for the words this corpus actually uses (checked against its frequency list),
# plus the school / everyday vocabulary the app cares about. Odia and Hindi are both
# SOV and share the Sanskritic layer, so a word-level swap keeps the sentence order.
ODIA_HINDI = {
    # --- grammar, connectors, pronouns ---
    "ଏହି": "यह", "ଏହା": "यह", "ଏ": "यह", "ଓ": "और", "ଏବଂ": "और", "ଆଉ": "और",
    "ପାଇଁ": "के लिए", "ଲାଗି": "के लिए", "ପରେ": "बाद", "କରି": "कर के", "ସେ": "वह",
    "ମଧ୍ୟ": "भी", "ବି": "भी", "ସହ": "के साथ", "ସହିତ": "के साथ", "ଏକ": "एक",
    "ତେବେ": "तब", "କିନ୍ତୁ": "लेकिन", "ବା": "या", "ଯଦି": "अगर", "ଯେ": "कि",
    "ବୋଲି": "कि", "ଏବେ": "अब", "ଆଜି": "आज", "ଉପରେ": "पर", "ପ୍ରତି": "प्रति",
    "ପର୍ଯ୍ୟନ୍ତ": "तक", "କୌଣସି": "कोई", "ସମସ୍ତ": "सभी", "ଅନ୍ୟ": "अन्य",
    "ବିଭିନ୍ନ": "विभिन्न", "ଅନେକ": "कई", "ଉଭୟ": "दोनों", "ନିଜ": "खुद", "କିଛି": "कुछ",
    "ଜଣେ": "एक व्यक्ति", "ଜଣ": "लोग", "ଲୋକ": "लोग", "ଲୋକେ": "लोग", "ସେମାନେ": "वे",
    "ମୁଁ": "मैं", "ତାଙ୍କ": "उनके", "ତାଙ୍କର": "उनका", "ତାଙ୍କୁ": "उन्हें",
    "ଏହାର": "इसका", "ଏହାକୁ": "इसे", "ତାହା": "वह", "ପକ୍ଷରୁ": "की ओर से",
    "ବେଳେ": "समय", "ମଧ୍ୟରେ": "के बीच", "ରେ": "में", "କୁ": "को", "ର": "का",
    "ନାହିଁ": "नहीं", "ପୁଣି": "फिर", "ପ୍ରଥମ": "पहला", "ପ୍ରତ୍ୟକ୍ଷ": "सीधे",
    "ପରୋକ୍ଷ": "अप्रत्यक्ष", "ସମ୍ପର୍କରେ": "के बारे में", "ଅବସରରେ": "के अवसर पर",
    "ସ୍ଥାନରେ": "स्थान पर", "କ୍ଷେତ୍ରରେ": "मामले में", "ମାଧ୍ୟମରେ": "के माध्यम से",
    # --- verbs / verb forms ---
    "କରିଛନ୍ତି": "किया है", "କରିଥିଲେ": "किया था", "କରିବା": "करना", "କରିବାକୁ": "करने के लिए",
    "କରାଯାଇଛି": "किया गया है", "କରାଯାଇ": "किया गया", "କରିଛି": "किया है",
    "କରିବେ": "करेंगे", "କରୁଛି": "कर रहा है", "କରିଲେ": "किया",
    "ହୋଇଛି": "हुआ है", "ହୋଇଥିବା": "हुआ", "ହୋଇଛନ୍ତି": "हुए हैं", "ହୋଇ": "हो कर",
    "ହେବା": "होना", "ହେବ": "होगा", "ହେଲେ": "हुआ", "ହେଉଛି": "हो रहा है",
    "ଥିଲେ": "थे", "ଥିବା": "हुआ", "ରହିଛି": "है", "ରଖି": "रख कर", "ରଖିଛି": "रखा है",
    "ରଖିବାକୁ": "रखने के लिए", "ଦେଇଛନ୍ତି": "दिया है", "ଦିଆଯାଇଛି": "दिया गया है",
    "କହିଛନ୍ତି": "कहा है", "କହିଲେ": "कहा", "ପହଞ୍ଚି": "पहुँच कर", "ନେଇ": "ले कर",
    "ଆରମ୍ଭ": "शुरू", "ଗ୍ରହଣ": "ग्रहण", "ଦେଖିବାକୁ": "देखने के लिए",
    # --- people, places, public life ---
    "ପୋଲିସ": "पुलिस", "ପୁଲିସ": "पुलिस", "ପୁଲିସ୍": "पुलिस", "ତଦନ୍ତ": "जाँच",
    "ଭାବେ": "रूप में", "ପ୍ରଧାନମନ୍ତ୍ରୀ": "प्रधानमंत्री", "ମୁଖ୍ୟମନ୍ତ୍ରୀ": "मुख्यमंत्री",
    "ମନ୍ତ୍ରୀ": "मंत्री", "ମୁଖ୍ୟ": "मुख्य", "ସୂଚନା": "जानकारी", "ଭାରତ": "भारत",
    "ଭାରତୀୟ": "भारतीय", "ଦେଶ": "देश", "ସରକାର": "सरकार", "ରାଜ୍ୟ": "राज्य",
    "ଜିଲ୍ଲା": "जिला", "ନିର୍ବାଚନ": "चुनाव", "ଘଟଣା": "घटना",
    "ଘଟଣାସ୍ଥଳରେ": "घटनास्थल पर", "ଘଟଣାର": "घटना के", "ମହିଳା": "महिला",
    "ଜବତ": "जब्त", "ଉଦ୍ଧାର": "बरामद", "ଅଭିଯୋଗ": "शिकायत", "ମୃତ୍ୟୁ": "मृत्यु",
    "ଦାବି": "दावा", "ଫିଲ୍ମ": "फिल्म", "ଫିଲ୍ମରେ": "फिल्म में", "ଶବ": "शव",
    "ଗ୍ରାମ": "गाँव", "ନିର୍ଦ୍ଦେଶ": "निर्देश", "ଖବର": "खबर", "ପ୍ରାର୍ଥୀ": "उम्मीदवार",
    "ପୂର୍ବତନ": "पूर्व", "ଗିରଫ": "गिरफ्तार", "ଅଭିନେତା": "अभिनेता",
    "ସୁରକ୍ଷା": "सुरक्षा", "ପ୍ରଶାସନ": "प्रशासन", "ମାମଲା": "मामला",
    "ପଦକ୍ଷେପ": "कदम", "ଆଲୋଚନା": "चर्चा", "ସ୍ପଷ୍ଟ": "स्पष्ट", "ବର୍ତ୍ତମାନ": "अभी",
    "ବ୍ୟବହାର": "उपयोग", "କେନ୍ଦ୍ର": "केंद्र", "କାର୍ଯ୍ୟ": "काम", "ସ୍ଥାନୀୟ": "स्थानीय",
    "ପରୀକ୍ଷା": "परीक्षा", "ରିପୋର୍ଟ": "रिपोर्ट", "ସହଯୋଗ": "सहयोग", "ଜାରି": "जारी",
    "ମା": "माँ", "ମା’": "माँ", "ନାମ": "नाम", "ବ୍ୟକ୍ତି": "व्यक्ति", "ଗୋଷ୍ଠୀ": "समूह",
    "ବିଜେପି": "भाजपा", "କଂଗ୍ରେସ": "कांग्रेस", "ମୋଦୀ": "मोदी", "ଟ୍ରମ୍ପ": "ट्रंप",
    "ବାଇଡେନ": "बाइडेन", "ଅମେରିକା": "अमेरिका", "ଆମେରିକା": "अमेरिका",
    "ରୁଷ": "रूस", "ଚୀନ": "चीन", "ପାକିସ୍ତାନ": "पाकिस्तान", "ଦିଲ୍ଲୀ": "दिल्ली",
    "ଓଡ଼ିଶା": "ओडिशा", "ଭୁବନେଶ୍ୱର": "भुवनेश्वर", "ପଟ୍ଟନାୟକ": "पटनायक",
    # --- numbers ---
    "ଏକ": "एक", "ଦୁଇ": "दो", "ତିନି": "तीन", "ଚାରି": "चार", "ପାଞ୍ଚ": "पाँच",
    "ଛଅ": "छह", "ସାତ": "सात", "ଆଠ": "आठ", "ନଅ": "नौ", "ଦଶ": "दस",
    "ଶହ": "सौ", "ହଜାର": "हजार", "ଲକ୍ଷ": "लाख", "କୋଟି": "करोड़",
    # --- school + everyday (the app's real subject area) ---
    "ପାଣି": "पानी", "ଜଳ": "पानी", "ଘର": "घर", "ମାଛ": "मछली", "ଭାତ": "भात",
    "ଅନ୍ନ": "अन्न", "ଚାଉଳ": "चावल", "ଗଛ": "पेड़", "ଫୁଲ": "फूल", "ଫଳ": "फल",
    "ଭାଷା": "भाषा", "ପାଠ": "पाठ", "ସ୍କୁଲ": "स्कूल", "ବିଦ୍ୟାଳୟ": "विद्यालय",
    "ଶିକ୍ଷକ": "शिक्षक", "ଶିକ୍ଷୟିତ୍ରୀ": "शिक्षिका", "ଛାତ୍ର": "छात्र",
    "ପିଲା": "बच्चा", "ପିଲାଏ": "बच्चे", "ବହି": "किताब", "ପାଠଶାଳା": "पाठशाला",
    "ହାତ": "हाथ", "ମୁଣ୍ଡ": "सिर", "ଆଖି": "आँख", "କାନ": "कान", "ପାଟି": "मुँह",
    "ଦିନ": "दिन", "ରାତି": "रात", "ବର୍ଷ": "साल", "ମାସ": "महीना", "ସମୟ": "समय",
    "କାମ": "काम", "ଦୁଃଖ": "दुख", "ସୁଖ": "सुख", "ମାଟି": "मिट्टी", "ଆକାଶ": "आकाश",
    "ସୂର୍ଯ୍ୟ": "सूरज", "ଚନ୍ଦ୍ର": "चाँद", "ବର୍ଷା": "बारिश", "ନଦୀ": "नदी",
    "ଜଙ୍ଗଲ": "जंगल", "ପଥର": "पत्थर", "ରାସ୍ତା": "रास्ता", "ବଜାର": "बाजार",
}
# Second pass: every word that was still unmapped in the corpus frequency report of
# `pipelines/build_odia_corpus.py`, so the Odia half converts to real Hindi instead of
# coming out as raw transliteration.
ODIA_HINDI.update({
    # adverbs, quantifiers, connectors
    "ଅଧିକ": "अधिक", "କି": "कि", "ଅଲଗା": "अलग", "ନା": "नहीं", "କାରଣ": "कारण",
    "ସବୁ": "सब", "ଏନେଇ": "इस पर", "କେବଳ": "केवल", "ଏଥିରେ": "इसमें", "ବହୁ": "कई",
    "ଏଭଳି": "ऐसा", "ସାରା": "पूरे", "ଏଥିପାଇଁ": "इसलिए", "ବାରମ୍ବାର": "बार-बार",
    "ମୋ": "मेरा", "କେତେ": "कितने", "ଆଗକୁ": "आगे", "ଥରେ": "एक बार", "ସମେତ": "सहित",
    "ପ୍ରାୟ": "लगभग", "ସମ୍ପୂର୍ଣ୍ଣ": "पूरा", "ଉଚିତ": "उचित", "ଅଧିକାଂଶ": "अधिकांश",
    # verb forms
    "ଅଛି": "है", "ଅଛନ୍ତି": "हैं", "ଥିଲା": "था", "ହୋଇଥିଲା": "हुआ था", "କଲେ": "किया",
    "ଚାଲିଥିବା": "चल रहा", "ଆସିବା": "आना", "ଦେବା": "देना", "ମିଳିଛି": "मिला है",
    "ଆସିବେ": "आएंगे", "ପାଇ": "पा कर", "ଦେଇଥିଲେ": "दिया था", "ଦେଇ": "दे कर",
    "ଦେଇଛି": "दिया है", "କରାଯାଇଥିଲା": "किया गया था", "କରିଥିବା": "किया हुआ",
    "କୁହାଯାଉଛି": "कहा जा रहा है", "ଦେବାକୁ": "देने के लिए", "ଯାଇଛି": "गया है",
    "ଆସିଛି": "आया है", "ଗଲା": "गया", "ନେଲେ": "लिया", "ଦେଲେ": "दिया",
    "ରହିଥିଲା": "था", "ବଢ଼ିଛି": "बढ़ा है", "ହୋଇଯାଇଛି": "हो गया है",
    "ଚାଲିଛି": "चल रहा है", "ଆସି": "आ कर", "ଯାଇ": "जा कर", "ଫେରି": "लौट कर",
    "ଉଠି": "उठ कर", "ଖାଇ": "खा कर", "ପିଇ": "पी कर", "ଶୋଇ": "सो कर",
    "ଲେଖି": "लिख कर", "ପଢ଼ି": "पढ़ कर", "କହି": "कह कर", "ଦେଖି": "देख कर",
    "ଶୁଣି": "सुन कर", "ମିଳିବ": "मिलेगा", "ଦେବେ": "देंगे", "ପାଇବେ": "पाएंगे",
    # nouns
    "ସିଂହ": "सिंह", "ପୁରୀ": "पुरी", "ସ୍ଥଳରେ": "स्थान पर", "ନରେନ୍ଦ୍ର": "नरेंद्र",
    "ବ୍ୟବଚ୍ଛେଦ": "पोस्टमार्टम", "ଦେଶରେ": "देश में", "ବାହିନୀ": "वाहिनी",
    "ତାର": "उसका", "ରୁଜୁ": "दर्ज", "ସ୍ୱାସ୍ଥ୍ୟ": "स्वास्थ्य", "ବିଜେଡି": "बीजेडी",
    "ଘୋଷଣା": "घोषणा", "ପ୍ରଦର୍ଶନ": "प्रदर्शन", "ଜୀବନ": "जीवन", "ମୁତୟନ": "तैनात",
    "କାର୍ଯ୍ୟକ୍ରମରେ": "कार्यक्रम में", "ମିଡିଆରେ": "मीडिया में", "ଆହତ": "घायल",
    "ଅଧ୍ୟକ୍ଷ": "अध्यक्ष", "ବରିଷ୍ଠ": "वरिष्ठ", "ନେତା": "नेता", "ବିଶ୍ୱାସ": "विश्वास",
    "ବୃଦ୍ଧି": "वृद्धि", "ଆକ୍ରମଣ": "हमला", "ଶକ୍ତି": "शक्ति", "କଟକ": "कटक",
    "କାର୍ଯ୍ୟାନୁଷ୍ଠାନ": "कार्रवाई", "ଶେଷ": "अंत", "ପ୍ରଦେଶ": "प्रदेश", "ଭଦ୍ରକ": "भद्रक",
    "ଆମ": "हम", "ନୂଆ": "नया", "ପୁରୁଷ": "पुरुष", "ନଜର": "नज़र", "ରାଜ୍ୟପାଳ": "राज्यपाल",
    "ଯୋଗ": "योग", "ପରିବେଶ": "माहौल", "ବିଶ୍ୱରେ": "दुनिया में", "ରାଜ୍ୟର": "राज्य के",
    "ସୃଷ୍ଟି": "रचना", "ଜଣକ": "एक व्यक्ति", "କୋର୍ଟ": "अदालत", "କମିଟି": "समिति",
    "ଉପସ୍ଥିତ": "मौजूद", "ଟଙ୍କା": "रुपये", "ହାର": "दर", "ଦଳର": "दल के",
    "ନିକଟରେ": "पास", "କ୍ରିକେଟ": "क्रिकेट", "ଅଧିନାୟକ": "कप्तान", "ବିରାଟ": "विराट",
    "ସଂଯୋଗ": "संयोग", "ମହିଳାଙ୍କ": "महिलाओं", "ମୃତଦେହ": "शव", "ଆତଙ୍କବାଦୀ": "आतंकवादी",
    "ନଷ୍ଟ": "नष्ट", "ହତ୍ୟା": "हत्या", "ଆବଶ୍ୟକ": "ज़रूरी", "ଅଧିକାରୀଙ୍କ": "अधिकारियों",
    "ନୂଆଦିଲ୍ଲୀ": "नई दिल्ली", "କୋଲକାତା": "कोलकाता", "ମୁମ୍ବାଇ": "मुंबई",
    "ଗୋଟିଏ": "एक", "ଯାହାକୁ": "जिसको", "ଗୁରୁତର": "गंभीर", "ବ୍ୟାପକ": "व्यापक",
    "ମୂଲ୍ୟ": "कीमत", "ଉଚ୍ଚ": "ऊँचा", "ନିମ୍ନ": "नीचा", "ସର୍ବନିମ୍ନ": "सबसे कम",
    # present-tense verb endings: Odia "-e / -anti" -> Hindi "-tā hai / -te haiN",
    # so a converted sentence matches the classroom phrase book instead of stopping
    # at "रहे" / "खाए"
    "ରହେ": "रहती है", "ରହନ୍ତି": "रहते हैं", "ଖାଏ": "खाता है", "ଖାଆନ୍ତି": "खाते हैं",
    "ପିଏ": "पीता है", "ପିଅନ୍ତି": "पीते हैं", "ଯାଏ": "जाता है", "ଯାଆନ୍ତି": "जाते हैं",
    "ଆସେ": "आता है", "ଆସନ୍ତି": "आते हैं", "କରେ": "करता है", "କରନ୍ତି": "करते हैं",
    "ଦିଏ": "देता है", "ନିଏ": "लेता है", "ଶୁଣେ": "सुनता है", "ଦେଖେ": "देखता है",
    "ପଢ଼େ": "पढ़ता है", "ଲେଖେ": "लिखता है", "ଗାଏ": "गाता है", "ନାଚେ": "नाचता है",
    "ବସେ": "बैठता है", "ଉଠେ": "उठता है", "ଶୁଏ": "सोता है", "ଧୋଏ": "धोता है",
    "ଖେଳେ": "खेलता है", "ଚାଲେ": "चलता है", "ବଢ଼େ": "बढ़ता है",
    "କର": "करो", "ଦିଅ": "दो", "ନିଅ": "लो", "ଯାଅ": "जाओ", "ଆସ": "आओ",
    "ପଢ଼": "पढ़ो", "ଲେଖ": "लिखो", "ଶୁଣ": "सुनो", "ଦେଖ": "देखो", "ଖାଅ": "खाओ",
    "ପିଅ": "पियो", "ବସ": "बैठो", "ଉଠ": "उठो", "ଗାଅ": "गाओ", "ଖେଳ": "खेलो",
})
ODIA_HINDI["ଏହି"] = "इस"          # "this X" before a noun reads as इस in Hindi
ODIA_HINDI.update({
    # question words, copula, and the ବ -> व words Hindi spells with व
    "କାହିଁ": "कहाँ", "କାହାକୁ": "किसको", "କେଉଁ": "कौन", "କେମିତି": "कैसे",
    "କାହିଁକି": "क्यों", "କେତେବେଳେ": "कब", "କେଉଁଠି": "कहाँ", "କେତେକ": "कुछ",
    "ଅଟେ": "है", "ଅଟନ୍ତି": "हैं", "ହେଉ": "हो",
    "ରବି": "रवि", "ବିଦ୍ୟା": "विद्या", "ବିଷୟ": "विषय", "ବିଜ୍ଞାନ": "विज्ञान",
    "ବିକାଶ": "विकास", "ବିଶେଷ": "विशेष", "ବିଚାର": "विचार", "ବିଦେଶ": "विदेश",
    # plural present tense + the adjectives/pronouns the demo sentences need
    "ପଢ଼ନ୍ତି": "पढ़ते हैं", "ଲେଖନ୍ତି": "लिखते हैं", "ଶୁଣନ୍ତି": "सुनते हैं",
    "ଦେଖନ୍ତି": "देखते हैं", "ଖେଳନ୍ତି": "खेलते हैं", "ଗାଆନ୍ତି": "गाते हैं",
    "ନାଚନ୍ତି": "नाचते हैं", "ବସନ୍ତି": "बैठते हैं", "ଉଠନ୍ତି": "उठते हैं",
    "ଶୁଅନ୍ତି": "सोते हैं", "ଧୋଉଛନ୍ତି": "धो रहे हैं", "ପଢ଼ାନ୍ତି": "पढ़ाते हैं",
    "ଛୋଟ": "छोटा", "ବଡ଼": "बड़ा", "ନୀଳ": "नीला", "ଲାଲ": "लाल", "ସବୁଜ": "हरा",
    "ଧଳା": "सफ़ेद", "କଳା": "काला", "ପିତା": "पीला", "ଲମ୍ବା": "लंबा", "ଅଳ୍ପ": "थोड़ा",
    "ଆମର": "हमारा", "ତୁମ": "तुम", "ତୁମର": "तुम्हारा", "ମୋର": "मेरा",
    "ଶିକ୍ଷକଙ୍କୁ": "शिक्षक को", "ପିଲାଙ୍କୁ": "बच्चों को", "ପିଲାମାନେ": "बच्चे",
    "ଅଙ୍କ": "अंक", "ଅକ୍ଷର": "अक्षर", "ଗଣିତ": "गणित", "ଚିତ୍ର": "चित्र",
    "ରଙ୍ଗ": "रंग", "ଖେଳ": "खेल", "ଗୀତ": "गीत", "କବିତା": "कविता",
    # more imperatives (the classroom's main verb mood)
    "ଖୋଲ": "खोलो", "ବନ୍ଦ": "बंद", "ଧର": "पकड़ो", "ଛାଡ଼": "छोड़ो", "ଆଣ": "लाओ",
    "ଦେଖାଅ": "दिखाओ", "ଶିଖ": "सीखो", "ଗଣ": "गिनो", "ରଖ": "रखो", "ମିଶାଅ": "जोड़ो",
    "ଚିହ୍ନାଅ": "पहचानो", "ପଚାର": "पूछो", "କୁହ": "कहो", "ଡାକ": "बुलाओ",
})

# very common inflections that would otherwise fall through to transliteration
# ---------------------------------------------------------------- Devanagari -> Odia
# The inverse of the tables above, so Hindi text can be turned into Odia script and
# checked against the Odia sentences we already hold a Santhali answer for.
DEVA_TO_ODIA_INDEPENDENT = {v: k for k, v in INDEPENDENT.items()}
DEVA_TO_ODIA_CONSONANT = {v: k for k, v in CONSONANTS.items()}
DEVA_TO_ODIA_MATRA = {v: k for k, v in OL_MATRA.items()}     # Ol Chiki signs -> reuse names
DEVA_TO_ODIA_SIGN = {v: k for k, v in SIGNS.items()}


def devanagari_to_odia(text: str) -> str:
    """Letter-level Hindi -> Odia script. Used for lookups, not for display."""
    out = []
    for ch in text:
        if ch in DEVA_TO_ODIA_CONSONANT:
            out.append(DEVA_TO_ODIA_CONSONANT[ch])
        elif ch in DEVA_TO_ODIA_INDEPENDENT:
            out.append(DEVA_TO_ODIA_INDEPENDENT[ch])
        elif ch in DEVA_TO_ODIA_SIGN:
            out.append(DEVA_TO_ODIA_SIGN[ch])
        elif ch == "\u094d":                                     # virama
            out.append(VIRAMA)
        elif "\u093e" <= ch <= "\u094c":                        # dependent vowel signs
            out.append(DEVA_VOWEL_SIGN.get(ch, ""))
        elif "\u0966" <= ch <= "\u096f":                        # digits
            out.append(chr(0x0B66 + ord(ch) - 0x0966))
        else:
            out.append(ch)
    return "".join(out)


# Hindi matra -> Odia matra (Devanagari sign -> the Odia sign with the same sound)
DEVA_VOWEL_SIGN = {
    "\u093e": "\u0b3e", "\u093f": "\u0b3f", "\u0940": "\u0b40",
    "\u0941": "\u0b41", "\u0942": "\u0b42", "\u0943": "\u0b43",
    "\u0947": "\u0b47", "\u0948": "\u0b48", "\u094b": "\u0b4b",
    "\u094c": "\u0b4c",
}

# Hindi word -> the Odia word the corpus actually uses (inverse of ODIA_HINDI).
HINDI_ODIA = {}
for _or, _hi in ODIA_HINDI.items():
    _hi = _hi.strip()
    if _hi and _hi not in HINDI_ODIA:
        HINDI_ODIA[_hi] = _or


def hindi_to_odia(text: str) -> str:
    """Turn a Hindi sentence into Odia so it can be looked up in the Odia sentences we
    already hold Santhali for. Word by word through the corpus lexicon first (so मछली
    becomes the corpus form ମାଛ, not a transliteration), then letter by letter."""
    out = []
    for tok in re.split(r"(\s+)", text or ""):
        if not tok.strip():
            out.append(tok)
            continue
        bare = tok.strip(".,;:!?\u0964\u0965()[]")
        tail = tok[len(bare):] if bare else ""
        mapped = HINDI_ODIA.get(bare)
        out.append((mapped or devanagari_to_odia(bare)) + tail)
    return "".join(out)


def odia_key(text: str) -> str:
    """Comparison key for Odia sentences: no punctuation, no spaces, no nukta variants."""
    s = text or ""
    s = re.sub(r"[\u0964\u0965.,;:!?\"'()\[\]\-]", "", s)
    s = re.sub(r"\s+", "", s)
    for a, b in (("ଂ", "ଁ"), ("ଃ", ""), ("ଯ", "ଜ"), ("ଵ", "ବ"), ("ୱ", "ବ"), ("ଣ", "ନ"), ("ଳ", "ଲ")):
        s = s.replace(a, b)
    return s


SUFFIX_HINDI = {
    "ଙ୍କୁ": "को", "ଙ୍କ": "के", "ରେ": "में", "କୁ": "को", "ର": "का",
    "ମାନଙ୍କୁ": "को", "ମାନେ": "लोग", "ଗୁଡ଼ିକ": "", "ଟି": "",
}


def odia_word_to_hindi(word: str):
    """-> (hindi, mode)   mode = 'lexicon' | 'translit'"""
    if word in ODIA_HINDI:
        return ODIA_HINDI[word], "lexicon"
    # try a known stem + common case ending (ପିଲାମାନେ -> ପିଲା + ମାନେ)
    for suf, hi in sorted(SUFFIX_HINDI.items(), key=lambda kv: -len(kv[0])):
        if word.endswith(suf) and len(word) > len(suf):
            stem = word[: -len(suf)]
            if stem in ODIA_HINDI:
                return (ODIA_HINDI[stem] + (" " + hi if hi else "")).strip(), "lexicon"
    return odia_to_devanagari(word), "translit"


def odia_to_hindi(text: str):
    """
    Odia sentence -> (Hindi sentence, stats).

    stats = {'tokens', 'lexicon', 'translit', 'resolution'} - resolution is the share of
    words that came from the curated Hindi lexicon rather than script transliteration.
    """
    out, lex, tr = [], 0, 0
    tokens = ODIA_TOKEN_RE.findall(text)
    if not tokens:
        return text, {"tokens": 0, "lexicon": 0, "translit": 0, "resolution": 0.0}
    for tok in tokens:
        if ODIA_RE.fullmatch(tok):
            hi, mode = odia_word_to_hindi(tok)
        else:                                       # digits, punctuation
            hi, mode = tok, "keep"
        out.append(hi)
        lex += mode == "lexicon"
        tr += mode == "translit"
    words = " ".join(out)
    total = max(1, lex + tr)
    return words, {"tokens": len(tokens), "lexicon": lex, "translit": tr,
                   "resolution": round(lex / total, 3)}


def _selftest():
    print("script:", odia_to_devanagari("ପ୍ରଧାନମନ୍ତ୍ରୀ ଗ୍ରାମରେ ଅଛନ୍ତି"))
    for s in ["ପୋଲିସ ତଦନ୍ତ କରିଛନ୍ତି", "ଏହି ଗ୍ରାମରେ ଏକ ସ୍କୁଲ ଅଛି", "ମାଛ ପାଣିରେ ରହେ"]:
        hi, st = odia_to_hindi(s)
        print(f"  {s}\n    -> {hi}   {st}")
    print("decode:", decode_odia_word("ଜୋମ", {"ᱡᱚᱢ"}), decode_odia_word("ହୋପନ", {"ᱦᱚᱯᱚᱱ"}))


if __name__ == "__main__":
    _selftest()
