"""
Curated foundational-literacy lexicons (Hindi -> English gloss).

These are the words a Jharkhand tribal-school teacher actually needs for
Class 1-5 foundational literacy & numeracy (NIPUN Bharat / PALASH MTB-MLE
themes). Each entry is glossed to English only; the Santhali surface form is
resolved from the Hugging Face-parallel data (see build_language_pack.py).
Keeping Hindi->English separate from English->Santhali lets us re-use one
English pivot across the Santhali / Ho / Mundari language packs.

Entry: (hindi, english, category, emoji)
"""

N = [
    # ---- numbers -----------------------------------------------------------
    ("एक", "one", "numbers", "1️⃣"), ("दो", "two", "numbers", "2️⃣"),
    ("तीन", "three", "numbers", "3️⃣"), ("चार", "four", "numbers", "4️⃣"),
    ("पाँच", "five", "numbers", "5️⃣"), ("छह", "six", "numbers", "6️⃣"),
    ("सात", "seven", "numbers", "7️⃣"), ("आठ", "eight", "numbers", "8️⃣"),
    ("नौ", "nine", "numbers", "9️⃣"), ("दस", "ten", "numbers", "🔟"),
    ("ग्यारह", "eleven", "numbers", "1️⃣1️⃣"), ("बारह", "twelve", "numbers", "1️⃣2️⃣"),
    ("तेरह", "thirteen", "numbers", "1️⃣3️⃣"), ("चौदह", "fourteen", "numbers", "1️⃣4️⃣"),
    ("पंद्रह", "fifteen", "numbers", "1️⃣5️⃣"), ("बीस", "twenty", "numbers", "2️⃣0️⃣"),
    ("तीस", "thirty", "numbers", "3️⃣0️⃣"),
    ("पचास", "fifty", "numbers", "5️⃣0️⃣"), ("सौ", "hundred", "numbers", "💯"),
    ("शून्य", "zero", "numbers", "0️⃣"),
    # ---- fruits ------------------------------------------------------------
    ("आम", "mango", "fruits", "🥭"), ("केला", "banana", "fruits", "🍌"),
    ("सेब", "apple", "fruits", "🍎"), ("संतरा", "orange", "fruits", "🍊"),
    ("अंगूर", "grapes", "fruits", "🍇"), ("अनार", "pomegranate", "fruits", "🍎"),
    ("पपीता", "papaya", "fruits", "🍈"), ("तरबूज", "watermelon", "fruits", "🍉"),
    ("नींबू", "lemon", "fruits", "🍋"), ("खीरा", "cucumber", "fruits", "🥒"),
    ("कटहल", "jackfruit", "fruits", "🍈"), ("इमली", "tamarind", "fruits", "🫘"),
    # ---- vegetables & food -------------------------------------------------
    ("सब्जी", "vegetable", "food", "🥦"), ("आलू", "potato", "food", "🥔"),
    ("टमाटर", "tomato", "food", "🍅"), ("प्याज", "onion", "food", "🧅"),
    ("चावल", "rice", "food", "🍚"), ("दाल", "dal", "food", "🍛"),
    ("रोटी", "bread", "food", "🫓"), ("दूध", "milk", "food", "🥛"),
    ("अंडा", "egg", "food", "🥚"), ("नमक", "salt", "food", "🧂"),
    ("चीनी", "sugar", "food", "🍬"), ("पानी", "water", "food", "💧"),
    ("मछली", "fish", "food", "🐟"), ("मांस", "meat", "food", "🍖"),
    ("तेल", "oil", "food", "🫗"), ("हल्दी", "turmeric", "food", "🟡"),
    ("मिर्च", "chilli", "food", "🌶️"), ("भात", "cooked rice", "food", "🍚"),
    # ---- animals -----------------------------------------------------------
    ("कुत्ता", "dog", "animals", "🐕"), ("बिल्ली", "cat", "animals", "🐈"),
    ("गाय", "cow", "animals", "🐄"), ("बकरी", "goat", "animals", "🐐"),
    ("भैंस", "buffalo", "animals", "🐃"), ("घोड़ा", "horse", "animals", "🐎"),
    ("हाथी", "elephant", "animals", "🐘"), ("बंदर", "monkey", "animals", "🐒"),
    ("शेर", "lion", "animals", "🦁"), ("बाघ", "tiger", "animals", "🐅"),
    ("साँप", "snake", "animals", "🐍"), ("चूहा", "mouse", "animals", "🐁"),
    ("हिरण", "deer", "animals", "🦌"), ("भालू", "bear", "animals", "🐻"),
    ("सूअर", "pig", "animals", "🐖"), ("मुर्गी", "hen", "animals", "🐓"),
    # ---- birds & insects ---------------------------------------------------
    ("पक्षी", "bird", "birds", "🐦"), ("कौआ", "crow", "birds", "🐦‍⬛"),
    ("मोर", "peacock", "birds", "🦚"), ("तोता", "parrot", "birds", "🦜"),
    ("कबूतर", "pigeon", "birds", "🕊️"), ("मच्छर", "mosquito", "birds", "🦟"),
    ("चींटी", "ant", "birds", "🐜"), ("मक्खी", "fly", "birds", "🪰"),
    ("तितली", "butterfly", "birds", "🦋"),
    # ---- colours -----------------------------------------------------------
    ("लाल", "red", "colours", "🔴"), ("हरा", "green", "colours", "🟢"),
    ("नीला", "blue", "colours", "🔵"), ("पीला", "yellow", "colours", "🟡"),
    ("काला", "black", "colours", "⚫"), ("सफ़ेद", "white", "colours", "⚪"),
    ("नारंगी", "orange colour", "colours", "🟠"), ("भूरा", "brown", "colours", "🟤"),
    # ---- body --------------------------------------------------------------
    ("आँख", "eye", "body", "👁️"), ("कान", "ear", "body", "👂"),
    ("नाक", "nose", "body", "👃"), ("मुँह", "mouth", "body", "👄"),
    ("हाथ", "hand", "body", "✋"), ("पैर", "leg", "body", "🦶"),
    ("सिर", "head", "body", "🧠"), ("बाल", "hair", "body", "💇"),
    ("दाँत", "tooth", "body", "🦷"), ("जीभ", "tongue", "body", "👅"),
    ("पेट", "stomach", "body", "🫃"), ("गर्दन", "neck", "body", "🧣"),
    ("उँगली", "finger", "body", "👆"), ("खून", "blood", "body", "🩸"),
    # ---- family ------------------------------------------------------------
    ("माँ", "mother", "family", "👩"), ("पिता", "father", "family", "👨"),
    ("भाई", "brother", "family", "🧑"), ("बहन", "sister", "family", "👧"),
    ("दादा", "grandfather", "family", "👴"), ("दादी", "grandmother", "family", "👵"),
    ("बेटा", "son", "family", "👦"), ("बेटी", "daughter", "family", "👧"),
    ("परिवार", "family", "family", "👨‍👩‍👧"), ("बच्चा", "child", "family", "🧒"),
    ("दोस्त", "friend", "family", "🤝"), ("लड़का", "boy", "family", "👦"),
    ("लड़की", "girl", "family", "👧"), ("आदमी", "man", "family", "🧑"),
    ("औरत", "woman", "family", "👩"),
    # ---- school & classroom ------------------------------------------------
    ("स्कूल", "school", "school", "🏫"), ("किताब", "book", "school", "📚"),
    ("कलम", "pen", "school", "🖊️"), ("पेंसिल", "pencil", "school", "✏️"),
    ("कागज", "paper", "school", "📄"), ("बोर्ड", "board", "school", "📋"),
    ("शिक्षक", "teacher", "school", "👩‍🏫"), ("छात्र", "student", "school", "🧑‍🎓"),
    ("कुर्सी", "chair", "school", "🪑"), ("मेज", "table", "school", "🪑"),
    ("दरवाज़ा", "door", "school", "🚪"), ("खिड़की", "window", "school", "🪟"),
    ("थैला", "bag", "school", "🎒"), ("चॉक", "chalk", "school", "🖍️"),
    ("घंटी", "bell", "school", "🔔"), ("खेल", "game", "school", "⚽"),
    ("गीत", "song", "school", "🎵"), ("चित्र", "picture", "school", "🖼️"),
    ("अक्षर", "letter", "school", "🔤"), ("शब्द", "word", "school", "🔠"),
    ("संख्या", "number", "school", "🔢"), ("कहानी", "story", "school", "📖"),
    # ---- nature ------------------------------------------------------------
    ("पेड़", "tree", "nature", "🌳"), ("पत्ता", "leaf", "nature", "🍃"),
    ("फूल", "flower", "nature", "🌸"), ("सूरज", "sun", "nature", "☀️"),
    ("चाँद", "moon", "nature", "🌙"), ("तारा", "star", "nature", "⭐"),
    ("आकाश", "sky", "nature", "🌌"), ("बादल", "cloud", "nature", "☁️"),
    ("बारिश", "rain", "nature", "🌧️"), ("हवा", "wind", "nature", "🌬️"),
    ("नदी", "river", "nature", "🏞️"), ("पहाड़", "mountain", "nature", "⛰️"),
    ("जंगल", "forest", "nature", "🌲"), ("मिट्टी", "soil", "nature", "🟫"),
    ("पत्थर", "stone", "nature", "🪨"), ("आग", "fire", "nature", "🔥"),
    ("धरती", "earth", "nature", "🌍"), ("घर", "house", "nature", "🏠"),
    ("गाँव", "village", "nature", "🏘️"), ("रास्ता", "road", "nature", "🛣️"),
    # ---- actions -----------------------------------------------------------
    ("खाओ", "eat", "actions", "🍽️"), ("पियो", "drink", "actions", "🥤"),
    ("जाओ", "go", "actions", "🚶"), ("आओ", "come", "actions", "👋"),
    ("दौड़ो", "run", "actions", "🏃"), ("बैठो", "sit", "actions", "🪑"),
    ("खड़े होओ", "stand", "actions", "🧍"), ("पढ़ो", "read", "actions", "📖"),
    ("लिखो", "write", "actions", "✍️"), ("सुनो", "listen", "actions", "👂"),
    ("बोलो", "speak", "actions", "🗣️"), ("देखो", "see", "actions", "👀"),
    ("गाओ", "sing", "actions", "🎤"), ("नाचो", "dance", "actions", "💃"),
    ("हँसो", "laugh", "actions", "😄"), ("सोओ", "sleep", "actions", "😴"),
    ("खेलो", "play", "actions", "⚽"), ("दोहराओ", "repeat", "actions", "🔁"),
    ("गिनो", "count", "actions", "🔢"), ("काम करो", "work", "actions", "🛠️"),
    # ---- describing words --------------------------------------------------
    ("बड़ा", "big", "describing", "🔺"), ("छोटा", "small", "describing", "🔻"),
    ("अच्छा", "good", "describing", "👍"), ("बुरा", "bad", "describing", "👎"),
    ("गरम", "hot", "describing", "🔥"), ("ठंडा", "cold", "describing", "❄️"),
    ("नया", "new", "describing", "🆕"), ("पुराना", "old", "describing", "🗿"),
    ("सुंदर", "beautiful", "describing", "✨"), ("मीठा", "sweet", "describing", "🍯"),
    ("खट्टा", "sour", "describing", "🍋"), ("लंबा", "long", "describing", "📏"),
    ("भारी", "heavy", "describing", "🏋️"), ("हल्का", "light", "describing", "🎈"),
    ("साफ़", "clean", "describing", "🧼"), ("गंदा", "dirty", "describing", "🧹"),
    ("खुश", "happy", "describing", "😊"), ("दुखी", "sad", "describing", "😢"),
    # ---- pronouns & question words -----------------------------------------
    ("मैं", "I", "grammar", "🙋"), ("तुम", "you", "grammar", "👉"),
    ("हम", "we", "grammar", "👥"), ("वह", "he", "grammar", "🧑"),
    ("यह", "this", "grammar", "👇"), ("क्या", "what", "grammar", "❓"),
    ("कौन", "who", "grammar", "🤔"), ("कहाँ", "where", "grammar", "📍"),
    ("कितना", "how much", "grammar", "🔢"), ("क्यों", "why", "grammar", "❔"),
    # ---- greetings ---------------------------------------------------------
    ("नमस्ते", "hello", "greetings", "🙏"), ("धन्यवाद", "thank you", "greetings", "🙏"),
    ("हाँ", "yes", "greetings", "✅"), ("नहीं", "no", "greetings", "❌"),
    ("ठीक है", "okay", "greetings", "👌"), ("अलविदा", "goodbye", "greetings", "👋"),
    ("कृपया", "please", "greetings", "🤲"),
    # ---- high-frequency classroom words (attested in the HF corpora) ------
    ("बच्चे", "children", "family", "🧒"), ("हम", "we", "grammar", "👥"),
    ("आप", "you", "grammar", "👉"), ("आज", "today", "grammar", "📅"),
    ("साथ", "together", "grammar", "🤝"), ("ध्यान", "attention", "school", "👀"),
    ("पढ़ाई", "study", "school", "📖"), ("गिनती", "counting", "school", "🔢"),
    ("अभ्यास", "practice", "school", "🔁"), ("मेहनत", "hard work", "describing", "💪"),
    ("शब्द", "word", "school", "🔠"), ("रंग", "colour", "colours", "🎨"),
]

# Hindi -> English classroom-instruction phrases (the heart of the PS).
INSTRUCTION_PHRASES = [
    ("बच्चों, ध्यान से सुनो।", "Children, listen carefully.", "instruction"),
    ("आज हम गिनती सीखेंगे।", "Today we will learn counting.", "instruction"),
    ("मेरे बाद दोहराओ।", "Repeat after me.", "instruction"),
    ("पढ़ो और लिखो।", "Read and write.", "instruction"),
    ("किताब खोलो।", "Open the book.", "instruction"),
    ("किताब बंद करो।", "Close the book.", "instruction"),
    ("हाथ ऊपर उठाओ।", "Raise your hand.", "instruction"),
    ("खड़े हो जाओ।", "Stand up.", "instruction"),
    ("बैठ जाओ।", "Sit down.", "instruction"),
    ("अब चुप रहो।", "Now keep quiet.", "instruction"),
    ("प्रश्न का उत्तर दो।", "Answer the question.", "instruction"),
    ("चित्र को पहचानो।", "Identify the picture.", "instruction"),
    ("सही उत्तर चुनो।", "Choose the correct answer.", "instruction"),
    ("यह क्या है?", "What is this?", "instruction"),
    ("यह कौन सा फल है?", "Which fruit is this?", "instruction"),
    ("कितने आम हैं?", "How many mangoes are there?", "instruction"),
    ("लाल रंग की वस्तु ढूँढो।", "Find a red coloured object.", "instruction"),
    ("1 से 10 तक गिनती करो।", "Count from 1 to 10.", "instruction"),
    ("अपना नाम लिखो।", "Write your name.", "instruction"),
    ("घर का काम पूरा करो।", "Complete the homework.", "instruction"),
    ("साथ में गाओ।", "Sing together.", "instruction"),
    ("कलम निकालो।", "Take out your pen.", "instruction"),
    ("कागज पर लिखो।", "Write on the paper.", "instruction"),
    ("जोड़ करो।", "Do the addition.", "instruction"),
    ("धीरे बोलो।", "Speak slowly.", "instruction"),
    ("यह एक पेड़ है।", "This is a tree.", "instruction"),
    ("पानी पीना ज़रूरी है।", "Drinking water is necessary.", "instruction"),
    ("सूरज आकाश में है।", "The sun is in the sky.", "instruction"),
    ("मछली पानी में रहती है।", "The fish lives in water.", "instruction"),
    ("आज हम फलों के नाम सीखेंगे।", "Today we will learn the names of fruits.", "instruction"),
    ("आज हम जानवरों के नाम सीखेंगे।", "Today we will learn the names of animals.", "instruction"),
    ("आज हम रंग सीखेंगे।", "Today we will learn colours.", "instruction"),
    ("आज हम शरीर के अंग सीखेंगे।", "Today we will learn body parts.", "instruction"),
    ("यह अच्छा काम है, शाबाश!", "This is good work, well done!", "praise"),
    ("बहुत बढ़िया!", "Very good!", "praise"),
    ("फिर से कोशिश करो।", "Try again.", "praise"),
    ("कोई बात नहीं, आगे बढ़ो।", "No problem, move ahead.", "praise"),
    ("क्या तुम समझ गए?", "Did you understand?", "question"),
    ("कौन बताएगा?", "Who will tell?", "question"),
    ("अपने दोस्त के साथ बात करो।", "Talk with your friend.", "activity"),
    ("जोड़ी बनाओ।", "Make a pair.", "activity"),
    ("खेल खेलेंगे।", "We will play a game.", "activity"),
    ("हाथ धोओ।", "Wash your hands.", "activity"),
]


# ---------------------------------------------------------------------------
# VETTED - core foundational words the project team confirms against standard
# Santhali usage / corpus evidence. These override the automated pick and are
# labelled source="curated-vetted" so reviewers can tell them apart. Everything
# here can still be corrected in-app (PS 17: human-in-the-loop validation).
# (hindi, santhali)
# ---------------------------------------------------------------------------
VETTED = {
    # -- corrected against data/raw/santali-train.csv (19,999 new parallel pairs) --
    "आम": "ᱩᱞ",              # ul  - mango    (ᱵᱤᱞᱤ ᱩᱞ, ᱩᱞ ᱫᱟᱨᱮᱨᱮ, ᱩᱞᱼᱮ)
    "सूरज": "ᱥᱤᱧ ᱪᱟᱸᱫᱚ",    # siñ cando - sun (ᱥᱤᱧ ᱪᱟᱸᱫᱚ ᱥᱮᱡ x2)
    "गाँव": "ᱟᱹᱛᱩ",           # atu - village  (ᱟᱹᱛᱩ ᱡᱤᱭᱚᱱ, ᱢᱤᱫᱴᱟᱝ ᱟᱹᱛᱩ x3)
    # -- newly resolved by that dataset --
    "दरवाज़ा": "ᱫᱩᱣᱟᱹᱨ",      # duwar - door   (ᱥᱟᱢᱟᱝ ᱫᱩᱣᱟᱹᱨ ᱡᱷᱤᱡ, ᱩᱱᱠᱩᱣᱟᱜ ᱫᱩᱣᱟᱹᱨ ᱨᱮ)
    "दादा": "ᱜᱚᱲᱚᱢ ᱦᱟᱲᱟᱢ",   # goraam haram - grandfather (ᱜᱚᱲᱚᱢ ᱦᱟᱲᱟᱢ ᱴᱷᱮᱱ, ᱟᱡᱽ ᱦᱟᱲᱟᱢᱵᱟ)
    "दादी": "ᱵᱩᱰᱤᱜᱚ",        # budigo - grandmother (ᱟᱡ ᱵᱩᱰᱤᱜᱚ)
    "लड़का": "ᱠᱚᱲᱟ",          # kora - boy     (ᱵᱮᱥ ᱠᱚᱲᱟ!, ᱠᱚᱲᱟ ᱜᱤᱫᱽᱨᱟᱹ ᱠᱚ)
    "औरत": "ᱛᱤᱨᱞᱟᱹ",         # tirlâ - woman  (40 sentences, p=0.70, lift 87)
    "भात": "ᱫᱟᱠᱟ",           # daka - cooked rice (x10)
    "मुर्गी": "ᱥᱤᱢ",          # sim - hen/chicken (ᱥᱤᱢ ᱠᱤᱢᱟ)
    "पंद्रह": "ᱜᱮᱞ ᱢᱚᱬᱮ",     # gel mone = ten-five
    "बीस": "ᱵᱟᱨ ᱜᱮᱞ",        # bar gel = two tens
    "तीस": "ᱯᱮ ᱜᱮᱞ",         # pe gel = three tens
    "पचास": "ᱢᱚᱬᱮ ᱜᱮᱞ",      # mone gel = five tens
    "चॉक": "ᱪᱚᱠ",            # cak - chalk (x4, loanword)
    "नींबू": "ᱞᱤᱢᱵᱩ",        # limbụ - lemon (loanword, single attestation)
    "दुखी": "ᱫᱩᱠᱷ ᱟᱱᱟᱜ",     # dukh anag - sad (ᱫᱩᱠᱷ ᱟᱱᱟᱜ ᱟᱨ ᱦᱤᱲᱤᱡ ᱟᱱᱟᱜ)
    "धन्यवाद": "ᱥᱟᱨᱦᱟᱣ",      # sarhaw - thanks
    # -- numbers: three entries were wrong, four had broken spellings -- #
    #     caught by tests/hindi_test_suite.py, fixed against the CSV corpus
    "पाँच": "ᱢᱚᱬᱮ",           # mone - five  (26 sentences; our own १५ ᱜᱮᱞ ᱢᱚᱬᱮ uses it)
    "छह": "ᱛᱩᱨᱩᱭ",            # turuy - six  (17 sentences; was ᱮᱭᱟᱭ, which is seven)
    "आठ": "ᱤᱨᱟᱹᱞ",            # iral - eight (7 sentences; was ᱮᱭᱟᱭ, which is seven)
    "सौ": "ᱥᱟᱭ",              # say - hundred (ᱥᱟᱭ x3; was ᱤᱨᱟᱹᱞ, which is eight)
    "ग्यारह": "ᱜᱮᱞ ᱢᱤᱫ",      # gel mid - eleven (source latin "gel mit̕", was ᱜᱢᱤᱛ)
    "बारह": "ᱜᱮᱞ ᱵᱟᱨ",        # gel bar - twelve (source latin "gel bar", was ᱵᱟᱨᱜᱮᱞ - reversed)
    "चौदह": "ᱜᱮᱞ ᱯᱩᱱ",        # gel pun - fourteen (was ᱜᱮᱯᱮ, which is thirteen)
    # -- confirmed / corrected against the team-supplied Santhali dictionaries -- #
    #     (Santali Open dictionary.csv + Glossary eng-sat/sat-eng + Eatables.csv)
    "अनार": "ᱟᱱᱟᱨ",            # anar - pomegranate  (ᱚᱱᱟᱨ ᱯᱮᱞ; 4 independent files)  RESOLVED
    "नारंगी": "ᱜᱮᱨᱩᱣᱟ",        # geruwa - orange (the colour; the dictionary files tag it
                              #                     Category=Colour). ᱠᱚᱢᱞᱟ/ᱡᱟᱹᱢᱵᱤᱨ is the fruit
    "चार": "ᱯᱩᱱ",              # pun - four  (standard form; needed so 40 = ᱯᱩᱱ ᱜᱮᱞ composes)
    "तेरह": "ᱜᱮᱞ ᱯᱮ",          # gel pe - thirteen (matches ᱑᱑ ᱜᱮᱞ ᱢᱤᱫ and ᱑᱒ ᱜᱮᱞ ᱵᱟᱨ)
    "शून्य": "ᱥᱩᱱᱭᱚ",          # sunyo - zero (a word, not the numeral glyph ᱐)
    "चावल": "ᱪᱟᱣᱞᱮ",           # cawle - uncooked rice; ᱫᱟᱠᱟ is COOKED rice (भात)
    "धरती": "ᱚᱛ",              # ot - earth/ground (ᱛᱷᱟᱨᱛᱤ was a Hindi-style spelling)
    "उँगली": "ᱠᱟᱹᱴᱩᱵ",         # katub - finger. All five rows of the uploaded files
                              # (Santali Open dictionary + Body Parts + Glossary
                              #  eng-sat x2 + sat-eng) write ᱠᱟ.ᱴᱩᱵ, i.e. ᱠᱟᱹᱴᱩᱵ;
                              # the corpus-mined ᱠᱟᱛᱩᱵ was missing the gicher
    # high-frequency classroom words - attested in the parallel corpora
    "बच्चे": "ᱜᱤᱫᱽᱨᱟᱹ",       # gidra - children      (ᱜᱤᱫᱽᱨᱟᱹ ᱚᱠᱛᱚ)
    "हम": "ᱟᱞᱮ",             # ale - we              (ᱟᱞᱮ ᱟᱧᱡᱚᱢᱟ ᱞᱮ)
    "मैं": "ᱤᱧ",             # iñ - I / me           (google/smol gatitos lexicon)
    "आप": "ᱟᱢ",              # am - you              (ᱟᱢ ᱫᱚ ᱪᱮᱫ ᱮᱢ ᱪᱤᱠᱟᱹᱭᱟ)
    "आज": "ᱛᱮᱦᱮᱧ",           # teheñ - today         (ᱛᱮᱦᱮᱧ ᱫᱷᱟᱹᱵᱤᱡ)
    "साथ": "ᱥᱟᱶᱛᱮ",          # sawnte - together     (ᱥᱟᱶᱛᱮ ᱟᱥᱲᱟ ᱪᱟᱞᱟᱜ ᱯᱮ)
    "पढ़ाई": "ᱯᱟᱲᱦᱟᱣ",        # parhaw - study/reading
    "गिनती": "ᱞᱮᱠᱷᱟ",        # lekha - count
    "शब्द": "ᱟᱹᱲᱟᱹ",          # arra - word           (ᱟᱹᱲᱟᱹ ᱢᱩᱨᱟᱹᱭ)
    "रंग": "ᱨᱚᱝ",             # rong - colour         (ᱪᱤᱱᱦᱟᱹ ᱟᱨ ᱨᱚᱝ)
    "ध्यान": "ᱫᱷᱮᱭᱟᱱ",        # dheyan - attention
}

# Other forms that are equally attested for the same Hindi word, from the dictionaries.
# Shown in the app as alternates rather than replacing what is already taught.
ALTERNATES = {
    "गाय": ["ᱜᱟᱹᱭ"], "बंदर": ["ᱦᱟᱹᱬᱩ"], "चूहा": ["ᱪᱩᱴᱩ"], "माँ": ["ᱟᱭᱳ"],
    "दादी": ["ᱜᱚᱲᱚᱢ ᱵᱩᱲᱷᱤ"], "शेर": ["ᱠᱟᱴᱟᱣᱟ ᱛᱟᱹᱨᱩᱵ"], "कबूतर": ["ᱯᱟᱨᱣᱟ"],
    "पैर": ["ᱡᱟᱝᱜᱟ"], "बेटा": ["ᱵᱮᱴᱟ"], "बेटी": ["ᱵᱤᱴᱤ"], "सेब": ["ᱥᱮᱣᱚ"],
    "प्याज": ["ᱯᱮᱭᱟᱡ"], "मीठा": ["ᱥᱤᱵᱤᱞ"], "हरा": ["ᱦᱟᱹᱨᱤᱭᱟᱹᱲ"],
    "सफ़ेद": ["ᱯᱩᱸᱰ"], "भूरा": ["ᱢᱟᱴᱤᱭᱟᱲ"], "क्यों": ["ᱪᱮᱫᱟᱜ"], "दो": ["ᱵᱟᱨ"],
    "मुर्गी": ["ᱥᱤᱢ ᱮᱸᱜᱟ"], "बकरी": ["ᱮᱸᱜᱟ ᱢᱮᱨᱚᱢ"], "सूअर": ["ᱥᱩᱠᱨᱤ"],
    "संतरा": ["ᱠᱚᱢᱞᱟ"], "कौआ": ["ᱠᱟᱹᱦᱩ"], "बाल": ["ᱩᱵᱽ"], "पेट": ["ᱞᱟᱡᱽ"],
    "गर्दन": ["ᱦᱚᱴᱚᱜᱽ"], "उँगली": ["ᱠᱟᱹᱴᱩᱵ"], "टमाटर": ["ᱵᱤᱞᱟᱹᱛᱤ"],
    "मिर्च": ["ᱢᱟᱹᱨᱤᱪ"], "तेल": ["ᱥᱩᱱᱩᱢ"], "शिक्षक": ["ᱢᱟᱪᱮᱛ"],
    "उँगली": ["ᱠᱟᱛᱩᱵ"], "कहाँ": ["ᱚᱠᱟᱨᱮ ᱨᱮ"], "चार": ["ᱯᱳᱱ"], "तेरह": ["ᱜᱮᱯᱮ"],
}

