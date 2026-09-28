"""
English -> Hindi for the team-supplied Santhali dictionaries.

Why this file exists
--------------------
`uploads/*.csv|txt` are English <-> Santhali resources. The platform answers
Hindi -> Santhali, so every one of them needs a Hindi side before it can be used.

Two machine routes were tried first and both were rejected as *primary* sources:

  * Wikipedia interlanguage links resolved only 21% of the headwords, and the register
    is encyclopedic (blood -> रक्त, mother -> माता, bone -> अस्थि). Nobody teaches a
    Class-2 child माता; the app says माँ.
  * Our own curated pivot only covers the 218 foundational-literacy words.

So the Hindi side below is hand-written, prioritising exactly the topics a
foundational-literacy classroom uses: body, family, food, animals, time, numbers.
Every entry is one a Hindi-speaking teacher would actually write on a blackboard.

Words where the English headword in the source file is itself unclear
("panter", "comfit", "hoond", "rump") are deliberately left out rather than guessed -
see `SKIPPED` at the bottom for the list and the reason.
"""

# ---------------------------------------------------------------- human body
BODY = {
    "hair": "बाल", "head": "सिर", "skull": "खोपड़ी", "spinal cord": "रीढ़ की हड्डी",
    "back of head": "सिर का पिछला भाग", "brain": "दिमाग", "forehead": "माथा",
    "face": "चेहरा", "eyelid": "पलक", "cheek": "गाल", "lip": "होंठ", "palate": "तालू",
    "shoulder": "कंधा", "arm": "बाँह", "skin": "चमड़ी", "elbow": "कोहनी",
    "palm": "हथेली", "nail": "नाखून", "thumb": "अंगूठा",
    "middle finger": "बीच की उँगली", "ring finger": "अनामिका",
    "little finger": "छोटी उँगली", "chest": "छाती", "lungs": "फेफड़ा",
    "heart": "दिल", "navel": "नाभि", "back": "पीठ", "waist": "कमर",
    "genital": "जननांग", "buttock": "कूल्हा", "bone": "हड्डी", "thigh": "जाँघ",
    "knee": "घुटना", "foot": "पैर", "feet": "पैर", "heel": "एड़ी",
    "eye": "आँख", "ear": "कान", "nose": "नाक", "mouth": "मुँह", "tooth": "दाँत",
    "tongue": "जीभ", "neck": "गर्दन", "finger": "उँगली", "hand": "हाथ",
    "leg": "टाँग", "stomach": "पेट", "blood": "खून", "beard": "दाढ़ी",
    "moustache": "मूँछ", "eyebrow": "भौंह", "eyelash": "पलक का बाल",
    "throat": "गला", "wrist": "कलाई", "chin": "ठुड्डी", "palm of hand": "हथेली",
}

# ------------------------------------------------------------- family / relations
FAMILY = {
    "father": "पिता", "mother": "माँ", "son": "बेटा", "daughter": "बेटी",
    "brother": "भाई", "sister": "बहन", "husband": "पति", "wife": "पत्नी",
    "grand father": "दादा", "grand mother": "दादी",
    "maternal grandfather": "नाना", "maternal grandmother": "नानी",
    "uncle": "चाचा", "aunt": "चाची", "maternal uncle": "मामा",
    "maternal aunt": "मामी", "mother's sister": "मौसी",
    "father in law": "ससुर", "mother in law": "सास", "son in law": "दामाद",
    "daughter in law": "बहू", "sister in law": "ननद", "brother in law": "देवर",
    "step father": "सौतेला पिता", "step mother": "सौतेली माँ",
    "step brother": "सौतेला भाई", "step sister": "सौतेली बहन",
    "step son": "सौतेला बेटा", "step daughter": "सौतेली बेटी",
    "maternal sister": "मौसेरी बहन", "relative": "रिश्तेदार", "guest": "मेहमान",
    "preceptor": "गुरु", "love": "प्यार", "own": "अपना", "boy": "लड़का",
    "girl": "लड़की", "child": "बच्चा", "children": "बच्चे", "man": "आदमी",
    "woman": "औरत", "people": "लोग", "friend": "दोस्त", "family": "परिवार",
}

# ------------------------------------------------------------------- food / eatables
FOOD = {
    "grain": "अनाज", "rice": "चावल", "cooked rice": "भात", "flour": "आटा",
    "maida": "मैदा", "semolina": "सूजी", "wheat": "गेहूँ", "maiz": "मक्का",
    "gram": "चना", "pulse": "दाल", "pickle": "अचार", "ghee": "घी",
    "mustard oil": "सरसों का तेल", "mustard": "सरसों", "salt": "नमक",
    "sugar": "चीनी", "sugar candy": "मिश्री", "honey": "शहद", "milk": "दूध",
    "curd": "दही", "butter": "मक्खन", "cheese": "पनीर", "tea": "चाय",
    "coffee": "कॉफ़ी", "ice": "बर्फ़", "ice-cream": "आइसक्रीम",
    "biscuit": "बिस्कुट", "sauce": "चटनी", "tomato sauce": "टमाटर की चटनी",
    "syrup": "शरबत", "wine": "शराब", "beef": "गोमांस", "mutton": "मटन",
    "pork": "सूअर का मांस", "fish": "मछली", "meat": "मांस", "egg": "अंडा",
    "vegetables": "सब्ज़ियाँ", "brinjal": "बैंगन", "carrot": "गाजर",
    "cauliflower": "फूलगोभी", "cabbage": "पत्तागोभी", "pea": "मटर",
    "bitter gourd": "करेला", "raddish": "मूली", "bottle gourd": "लौकी",
    "ginger": "अदरक", "spinach": "पालक", "turnip": "शलगम",
    "lady finger": "भिंडी", "mint": "पुदीना", "coriender": "धनिया",
    "jack fruit": "कटहल", "onion": "प्याज", "potato": "आलू", "tomato": "टमाटर",
    "cashew": "काजू", "date": "खजूर", "grape": "अंगूर", "lychee": "लीची",
    "mango": "आम", "banana": "केला", "apple": "सेब", "pomegranate": "अनार",
    "water": "पानी",
}

# ------------------------------------------------------------------ animals / birds
ANIMALS = {
    "dog": "कुत्ता", "cat": "बिल्ली", "cow": "गाय", "ox": "बैल", "bull": "साँड",
    "calf": "बछड़ा", "buffalo": "भैंस", "goat": "बकरी", "he goat": "बकरा",
    "she goat": "बकरी", "kid": "बकरी का बच्चा", "sheep": "भेड़", "lamb": "मेमना",
    "horse": "घोड़ा", "mare": "घोड़ी", "colt": "बछेड़ा", "ass": "गधा",
    "camel": "ऊँट", "pig": "सूअर", "boar": "जंगली सूअर", "dog female": "कुतिया",
    "bitch": "कुतिया", "kitten": "बिल्ली का बच्चा", "rabbit": "खरगोश",
    "fox": "लोमड़ी", "hyena": "लकड़बग्घा", "fawn": "हिरण का बच्चा",
    "squirrel": "गिलहरी", "rhinoceros": "गैंडा", "gorilla": "गोरिल्ला",
    "panther": "तेंदुआ", "tiger": "बाघ", "lion": "शेर", "elephant": "हाथी",
    "monkey": "बंदर", "bear": "भालू", "deer": "हिरण", "snake": "साँप",
    "frog": "मेंढक", "rat": "चूहा", "mouse": "चूहा", "squirrel animal": "गिलहरी",
    "hen": "मुर्गी", "cock": "मुर्गा", "chicken": "मुर्गी",
    "duck": "बत्तख", "swan": "हंस", "eagle": "चील", "vulture": "गिद्ध",
    "owl": "उल्लू", "sparrow": "गौरैया", "myna": "मैना", "crow": "कौआ",
    "parrot": "तोता", "peacock": "मोर", "pigeon": "कबूतर", "cuckoo": "कोयल",
    "insect": "कीड़ा", "mosquito": "मच्छर", "fly": "मक्खी", "ant": "चींटी",
    "spider": "मकड़ी", "butterfly": "तितली", "bee": "मधुमक्खी",
}

# ------------------------------------------------------------------------- nature
NATURE = {
    "tree": "पेड़", "flower": "फूल", "fruit": "फल", "leaf": "पत्ता",
    "root": "जड़", "seed": "बीज", "grass": "घास", "forest": "जंगल",
    "mountain": "पहाड़", "hill": "पहाड़ी", "river": "नदी", "pond": "तालाब",
    "well": "कुआँ", "stone": "पत्थर", "soil": "मिट्टी", "sand": "रेत",
    "sky": "आकाश", "sun": "सूरज", "moon": "चाँद", "full moon": "पूर्णिमा",
    "star": "तारा", "cloud": "बादल", "rain": "बारिश", "wind": "हवा",
    "fire": "आग", "smoke": "धुआँ", "water body": "जलाशय", "sea": "समुद्र",
    "sea shell": "सीप", "weather": "मौसम", "season": "मौसम", "village": "गाँव",
    "field": "खेत", "road": "रास्ता", "house": "घर", "door": "दरवाज़ा",
    "wall": "दीवार", "roof": "छत", "floor": "फर्श", "courtyard": "आँगन",
    "market": "बाजार", "world": "दुनिया", "universe": "ब्रह्मांड",
    "earth": "धरती", "day": "दिन", "night": "रात", "morning": "सुबह",
    "evening": "शाम", "yesterday": "बीता कल", "today": "आज", "tomorrow": "आने वाला कल",
    "hour": "घंटा", "minute": "मिनट", "second": "सेकंड", "week": "हफ्ता",
    "month": "महीना", "year": "साल", "time": "समय",
}

# ----------------------------------------------------------------- days and months
DAYS = {
    "sunday": "रविवार", "monday": "सोमवार", "tuesday": "मंगलवार",
    "wednesday": "बुधवार", "thursday": "गुरुवार", "friday": "शुक्रवार",
    "saturday": "शनिवार",
}
MONTHS = {
    "january": "जनवरी", "february": "फ़रवरी", "march": "मार्च", "april": "अप्रैल",
    "may": "मई", "june": "जून", "july": "जुलाई", "august": "अगस्त",
    "september": "सितंबर", "october": "अक्टूबर", "november": "नवंबर",
    "december": "दिसंबर",
}

# ------------------------------------------------------------- colour and classroom
COLOURS = {
    "colour": "रंग", "red": "लाल", "green": "हरा", "blue": "नीला",
    "yellow": "पीला", "black": "काला", "white": "सफ़ेद", "brown": "भूरा",
    "pink": "गुलाबी", "orange colour": "नारंगी रंग", "these are colours": "ये रंग हैं",
}
CLASSROOM = {
    "book": "किताब", "copy/note": "कॉपी", "pen": "कलम", "pencil": "पेंसिल",
    "chalk": "चॉक", "board": "बोर्ड", "school": "स्कूल", "teacher": "शिक्षक",
    "pupil": "विद्यार्थी", "student": "छात्र", "class": "कक्षा", "lesson": "पाठ",
    "name": "नाम", "word": "शब्द", "letter": "अक्षर", "number": "संख्या",
    "picture": "चित्र", "song": "गाना", "story": "कहानी", "game": "खेल",
    "question": "सवाल", "answer": "जवाब", "count": "गिनती", "study": "पढ़ाई",
    "press": "दबाओ", "temple": "मंदिर", "puja": "पूजा", "statue": "मूर्ति",
    "sagun": "शगुन", "god": "भगवान", "angry": "गुस्सा", "anger": "गुस्सा",
    "happy": "खुश", "sad": "दुखी", "good": "अच्छा", "big": "बड़ा",
    "small": "छोटा", "little": "थोड़ा", "new": "नया", "old": "पुराना",
    "hot": "गर्म", "cold": "ठंडा", "clean": "साफ़", "dirty": "गंदा",
    "difficult": "कठिन", "easy": "आसान", "work": "काम", "hard work": "मेहनत",
}

# ----------------------------------------------------------- function words / grammar
FUNCTION = {
    "and": "और", "or": "या", "or else": "वरना", "in": "में", "into": "में",
    "is": "है", "are": "हैं", "that": "वह", "about": "के बारे में",
    "it/this": "यह", "when?": "कब", "which?": "कौन सा", "whose?": "किसका",
    "whom?": "किसे", "how?": "कैसे", "how many?": "कितने", "how much?": "कितना",
    "here": "यहाँ", "there": "वहाँ", "now": "अब", "of these": "इनमें से",
    "any one": "कोई एक", "me": "मैं", "my": "मेरा", "mine": "मेरा",
    "our": "हमारा", "ourselves": "खुद", "of us": "हमारा", "to us": "हमें",
    "by us": "हमारे द्वारा", "for us": "हमारे लिए", "from us": "हमसे",
    "with us": "हमारे साथ", "his": "उसका", "her": "उसकी", "him": "उसे",
    "us": "हमें", "them": "उन्हें", "they": "वे", "these": "ये", "those": "वे",
    "myself": "खुद", "yourself": "खुद", "himself": "खुद", "herself": "खुद",
    "yourselves": "खुद", "themselves": "खुद", "by me": "मेरे द्वारा",
    "for me": "मेरे लिए", "from me": "मुझसे", "with me": "मेरे साथ",
    "of thee": "तुम्हारा", "thou": "तू", "thee": "तुझे", "you only": "तुम",
    "your": "तुम्हारा", "he/she": "वह", "she": "वह", "we two": "हम दोनों",
    "noun": "संज्ञा", "verb": "क्रिया", "adjective": "विशेषण",
    "pronoun": "सर्वनाम", "grammar": "व्याकरण",
    "to eat": "खाना खाना", "to come": "आना", "to drink": "पानी पीना",
    "to sit": "बैठना", "carry": "ले जाना", "came": "आया",
    "carried one": "ले गया", "unwritten": "अलिखित", "unknown": "अज्ञात",
    "common": "सामान्य", "symbols": "प्रतीक", "emoji": "इमोजी",
    "multiple languages": "कई भाषाएँ",
}

# ------------------------------------------------- language and script names (India first)
LANGUAGES = {
    "hindi": "हिंदी", "english": "अंग्रेज़ी", "bangla": "बांग्ला", "bengali": "बंगाली",
    "odia": "उड़िया", "assamese": "असमिया", "tamil": "तमिल", "telugu": "तेलुगु",
    "kannada": "कन्नड़", "malayalam": "मलयालम", "marathi": "मराठी",
    "gujarati": "गुजराती", "punjabi": "पंजाबी", "urdu": "उर्दू", "nepali": "नेपाली",
    "sanskrit": "संस्कृत", "bhojpuri": "भोजपुरी", "maithili": "मैथिली",
    "konkani": "कोंकणी", "manipuri": "मणिपुरी", "kashmiri": "कश्मीरी",
    "santali": "संताली", "santhali": "संताली", "kurukh": "कुरुख",
    "awadhi": "अवधी", "magahi": "मगही", "rajasthani": "राजस्थानी",
    "marwari": "मारवाड़ी", "braj": "ब्रज", "dogri": "डोगरी", "sindhi": "सिंधी",
    "sinhala": "सिंहली", "sindhi language": "सिंधी", "fiji hindi": "फ़िजी हिंदी",
    "chinese": "चीनी", "japanese": "जापानी", "korean": "कोरियाई",
    "arabic": "अरबी", "persian": "फ़ारसी", "russian": "रूसी", "french": "फ़्रांसीसी",
    "german": "जर्मन", "spanish": "स्पेनिश", "portuguese": "पुर्तगाली",
    "italian": "इतालवी", "dutch": "डच", "greek": "यूनानी", "latin": "लातीनी",
    "hebrew": "हिब्रू", "turkish": "तुर्की", "thai": "थाई", "vietnamese": "वियतनामी",
    "swahili": "स्वाहिली", "burmese": "बर्मी", "myanmar": "बर्मी",
    "devanagari": "देवनागरी", "ol chiki": "ओल चिकी", "gurmukhi": "गुरुमुखी",
    "cyrillic": "सिरिलिक", "braille": "ब्रेल", "hiragana": "हिरागाना",
    "katakana": "काटाकाना", "hangul": "हंगुल", "runic": "रूनिक",
    "tibetan": "तिब्बती", "kawi": "कावी", "sharada": "शारदा",
}

# merged view - one dictionary the builder consumes
EN_HI = {}
for _block in (BODY, FAMILY, FOOD, ANIMALS, NATURE, DAYS, MONTHS, COLOURS,
               CLASSROOM, FUNCTION, LANGUAGES):
    for _k, _v in _block.items():
        EN_HI.setdefault(_k, _v)

_themed = set(BODY) | set(FAMILY) | set(FOOD) | set(ANIMALS) | set(NATURE) | \
    set(DAYS) | set(MONTHS) | set(COLOURS) | set(CLASSROOM)


def theme_of(en: str) -> str:
    """Topic label for the words a lesson can be built from."""
    e = en.lower()
    if e in BODY: return "body"
    if e in FAMILY: return "family"
    if e in FOOD: return "food"
    if e in ANIMALS: return "animals"
    if e in NATURE: return "nature"
    if e in DAYS or e in MONTHS: return "time"
    if e in COLOURS: return "colours"
    if e in CLASSROOM: return "school"
    return "general"


# headwords in the source files that are too unclear to translate honestly
SKIPPED = {
    "panter": "source file has no such English word; looks like a typo for 'pointer'",
    "comfit": "ambiguous English word - could be खोई or मिठाई, not worth guessing",
    "hoond": "source file has no such English word",
    "rump": "means both दुम and कूल्हा - ambiguous without context",
    "O": "single letter, not a word",
    "caror": "typo for crore, which is already mapped",
    "velid name for a pig": "source file is corrupt here",
    "santal": "ethnonym, not standard Hindi vocabulary",
    "sagun": "loanword in the source; शगुन is the Hindi form",
}

if __name__ == "__main__":
    dups = [k for k in EN_HI if list(EN_HI).count(k) > 1]
    print(f"curated English->Hindi entries: {len(EN_HI):,}")
    print(f"  themed (body/family/food/animals/nature/time/colours/school): {len(_themed)}")
    print(f"  function words + grammar: {len(FUNCTION)}")
    print(f"  languages + scripts: {len(LANGUAGES)}")
    print(f"  deliberately skipped: {len(SKIPPED)}")
