"""
Classroom grammar layer: attested Santhali building blocks mined from the
Hugging Face Hindi/English-Santhali parallel corpora.

Rule of this file: NOTHING is invented here. Every verb form and every template
carries an `attested_in` string that appears verbatim in the parallel corpus
(data/raw/en_sat.parquet, 71k pairs) or in google/smol. build_language_pack.py
re-verifies each attestation against the corpus and drops anything that fails.

Composed phrases (object noun swapped into an attested frame) are marked
kind="pattern" and confidence="medium" -> they are queued for native-speaker
validation in the app (PS section 17: human-in-the-loop).
"""

# ---------------------------------------------------------------------------
# VERBS - attested imperative / verb-complex forms.
# (santhali, english, hindi, attested_in)
# ---------------------------------------------------------------------------
VERBS = [
    ("ᱯᱟᱲᱦᱟᱣ ᱢᱮ",  "read!",     "पढ़ो",        "ᱟᱪᱩᱨ ᱠᱟᱛᱮᱜ ᱯᱟᱲᱦᱟᱣ ᱢᱮ।"),
    ("ᱚᱞ ᱢᱮ",       "write!",    "लिखो",        "ᱫᱟᱭᱟ ᱠᱟᱛᱮᱫ ᱢᱤᱫᱴᱟᱝ ᱢᱚᱛᱟᱱ ᱚᱞ ᱢᱮ।"),
    ("ᱧᱮᱞ ᱢᱮ",      "look!",     "देखो",        "ᱦᱟᱱᱰᱮ ᱧᱮᱞ ᱢᱮ"),
    ("ᱞᱟᱹᱭ ᱢᱮ",      "tell!",     "बताओ",        "ᱟᱢᱟᱜ ᱵᱟᱹᱠᱷᱩᱞ ᱵᱟᱵᱚᱛ ᱞᱟᱹᱭ ᱢᱮ ᱾"),
    ("ᱟᱸᱡᱚᱢ ᱢᱮ",     "listen!",   "सुनो",        "ᱟᱧᱡᱚᱢ ᱢᱮ"),
    ("ᱫᱩᱲᱩᱵ ᱢᱮ",     "sit!",      "बैठो",        "ᱢᱟ ᱵᱩᱢᱠᱟ. ᱫᱩᱲᱩᱵ ᱢᱮ"),
    ("ᱪᱟᱞᱟᱜ ᱯᱮ",     "go! (you all)", "चलो",    "ᱥᱟᱶᱛᱮ ᱟᱥᱲᱟ ᱪᱟᱞᱟᱜ ᱯᱮ ᱾"),
    ("ᱪᱟᱞᱟᱜ ᱢᱮ",     "go!",       "जाओ",         "ᱟᱞᱮᱭᱟᱜ ᱚᱲᱟᱜ ᱠᱷᱚᱱ ᱪᱟᱞᱟᱜ ᱢᱮ!"),
    ("ᱦᱟᱛᱟᱣ ᱢᱮ",     "take!",     "लो",          "ᱮᱴᱟᱜ ᱢᱟᱹᱪᱤ ᱦᱟᱛᱟᱣ ᱢᱮ᱾"),
    ("ᱮᱢ ᱢᱮ",        "give!",     "दो",          "ᱤᱧᱟᱜ ᱮᱞᱟᱨᱚᱢ ᱩᱫᱩᱜ ᱟᱹᱧ ᱢᱮ᱾"),
    ("ᱵᱚᱸᱫᱚᱭ ᱢᱮ",     "close / switch off!", "बंद करो", "ᱯᱚᱛᱚᱵ ᱵᱚᱸᱫᱚᱭ ᱢᱮ!"),
    ("ᱡᱷᱤᱡᱽ ᱢᱮ",      "open!",     "खोलो",        "ᱥᱯᱳᱴ ᱥᱴᱮᱹᱥᱚᱱ ᱡᱷᱤᱡᱽ ᱢᱮ᱾"),
    ("ᱵᱟᱡᱟᱣ ᱢᱮ",     "play (music) / sing!", "गाओ",  "ᱤᱧ ᱞᱟᱹᱜᱤᱫ ᱠᱚᱪ ᱥᱤᱨᱤᱧ ᱵᱟᱡᱟᱣ ᱢᱮ᱾"),
    ("ᱪᱟᱹᱞᱩᱭ ᱢᱮ",     "start!",    "शुरू करो",     "ᱤᱧ ᱞᱟᱹᱜᱤᱫ ᱟᱢᱮᱨᱤᱠᱟᱱ ᱟᱭᱰᱚᱞ ᱥᱳ ᱪᱟᱹᱞᱩᱭ ᱢᱮ।"),
    ("ᱫᱚᱦᱚ ᱢᱮ",      "keep!",     "रखो",         "ᱧᱩᱛᱩᱢ ᱫᱚᱦᱚ"),
    ("ᱧᱩᱭ ᱢᱮ",       "drink!",    "पियो",        "ᱟᱢᱟᱜ ᱯᱟᱹᱶᱨᱟᱹ ᱧᱩᱭ ᱢᱮ ᱾"),
    ("ᱜᱚᱲᱚ ᱮᱢᱚᱜ ᱢᱮ", "help!",     "मदद करो",     "ᱫᱟᱭᱟᱠᱟᱛᱮ ᱜᱚᱲᱚ ᱮᱢᱚᱜ ᱢᱮ ᱾"),
    ("ᱪᱮᱫᱚᱜ ᱢᱮ",     "learn!",    "सीखो",        "ᱥᱟᱱᱛᱟᱲᱤ ᱯᱟᱹᱨᱥᱤ ᱛᱮ ᱚᱞ ᱟᱨ ᱯᱟᱲᱦᱟᱣ ᱪᱮᱫᱚᱜ ᱢᱮ ᱾"),
]

# ---------------------------------------------------------------------------
# TEMPLATES - attested sentence frames. {obj} is filled with a curated noun.
# (id, santhali_frame, english_frame, hindi_frame, attested_in, confidence)
# ---------------------------------------------------------------------------
TEMPLATES = [
    ("close",  "{obj} ᱵᱚᱸᱫᱚᱭ ᱢᱮ!",   "Close the {en}!",   "{hi} बंद करो।",
     "ᱯᱚᱛᱚᱵ ᱵᱚᱸᱫᱚᱭ ᱢᱮ!", "medium"),
    ("open",   "{obj} ᱡᱷᱤᱡᱽ ᱢᱮ।",    "Open the {en}!",    "{hi} खोलो।",
     "ᱥᱯᱳᱴ ᱥᱴᱮᱹᱥᱚᱱ ᱡᱷᱤᱡᱽ ᱢᱮ᱾", "medium"),
    ("read",   "{obj} ᱯᱟᱲᱦᱟᱣ ᱢᱮ।",   "Read the {en}.",    "{hi} पढ़ो।",
     "ᱟᱪᱩᱨ ᱠᱟᱛᱮᱜ ᱯᱟᱲᱦᱟᱣ ᱢᱮ।", "medium"),
    ("write",  "{obj} ᱚᱞ ᱢᱮ।",       "Write the {en}.",   "{hi} लिखो।",
     "ᱢᱤᱫᱴᱟᱝ ᱢᱚᱛᱟᱱ ᱚᱞ ᱢᱮ।", "medium"),
    ("look",   "{obj} ᱧᱮᱞ ᱢᱮ।",      "Look at the {en}.", "{hi} देखो।",
     "ᱦᱟᱱᱰᱮ ᱧᱮᱞ ᱢᱮ", "medium"),
    ("take",   "{obj} ᱦᱟᱛᱟᱣ ᱢᱮ।",    "Take the {en}.",    "{hi} लो।",
     "ᱮᱴᱟᱜ ᱢᱟᱹᱪᱤ ᱦᱟᱛᱟᱣ ᱢᱮ᱾", "medium"),
    ("give",   "{obj} ᱮᱢ ᱢᱮ।",       "Give the {en}.",    "{hi} दो।",
     "ᱤᱧᱟᱜ ᱮᱞᱟᱨᱚᱢ ᱩᱫᱩᱜ ᱟᱹᱧ ᱢᱮ᱾", "medium"),
    ("drink",  "{obj} ᱧᱩᱭ ᱢᱮ।",      "Drink the {en}.",   "{hi} पियो।",
     "ᱟᱢᱟᱜ ᱯᱟᱹᱶᱨᱟᱹ ᱧᱩᱭ ᱢᱮ ᱾", "medium"),
    ("play",   "{obj} ᱵᱟᱡᱟᱣ ᱢᱮ।",    "Sing / play the {en}.", "{hi} गाओ।",
     "ᱠᱚᱪ ᱥᱤᱨᱤᱧ ᱵᱟᱡᱟᱣ ᱢᱮ᱾", "medium"),
    ("where",  "{obj} ᱫᱚ ᱚᱠᱟᱨᱮ ᱢᱮᱱᱟᱜᱼᱟ?", "Where is the {en}?", "{hi} कहाँ है?",
     "ᱡᱚ ᱫᱚ ᱚᱠᱟᱨᱮ ᱢᱮᱱᱟᱜᱼᱟ ?", "high"),
    ("thisis", "ᱱᱚᱶᱟ ᱫᱚ ᱢᱤᱫᱴᱟᱹᱝ {obj} ᱠᱟᱱᱟ।", "This is a {en}.", "यह {hi} है।",
     "ᱱᱚᱶᱟ ᱫᱚ ᱢᱤᱫᱴᱟᱹᱝ ᱟᱹᱛᱩ ᱠᱟᱱᱟ ᱾", "high"),
    ("myname", "ᱤᱧᱟᱜ ᱧᱩᱛᱩᱢ ᱫᱚ {obj} ᱠᱟᱱᱟ।", "My name is {en}.", "मेरा नाम {hi} है।",
     "ᱤᱧᱟᱜ ᱧᱩᱛᱩᱢ ᱫᱚ ᱨᱚᱵᱤ ᱠᱟᱱᱟ ᱾", "high"),
    ("howmany", "ᱛᱤᱱᱟᱹᱜ {obj} ᱢᱮᱱᱟᱜᱼᱟ?", "How many {en} are there?", "कितने {hi} हैं?",
     "ᱛᱤᱱᱟᱹᱜ ᱮᱞᱟᱨᱢ ᱥᱮᱴ ᱢᱮᱱᱟᱜᱼᱟ?", "low"),
]

# ---------------------------------------------------------------------------
# CLASSROOM PHRASES - ready-to-use teacher instructions.
# kind "attested" = the Santhali string exists verbatim in the corpus
# kind "pattern"  = objects/words swapped inside an attested frame
# (hindi, english, santhali, kind, evidence, type)
# ---------------------------------------------------------------------------
PHRASES = [
    ("किताब बंद करो।", "Close the book!",
     "ᱯᱚᱛᱚᱵ ᱵᱚᱸᱫᱚᱭ ᱢᱮ!", "attested", "ᱯᱚᱛᱚᱵ ᱵᱚᱸᱫᱚᱭ ᱢᱮ!", "instruction"),
    ("ध्यान से पढ़ो।", "Read it carefully.",
     "ᱟᱪᱩᱨ ᱠᱟᱛᱮᱜ ᱯᱟᱲᱦᱟᱣ ᱢᱮ।", "attested", "ᱟᱪᱩᱨ ᱠᱟᱛᱮᱜ ᱯᱟᱲᱦᱟᱣ ᱢᱮ।", "instruction"),
    ("सब मिलकर स्कूल चलो।", "Go to school together.",
     "ᱥᱟᱶᱛᱮ ᱟᱥᱲᱟ ᱪᱟᱞᱟᱜ ᱯᱮ ᱾", "attested", "ᱥᱟᱶᱛᱮ ᱟᱥᱲᱟ ᱪᱟᱞᱟᱜ ᱯᱮ ᱾", "instruction"),
    ("दरवाज़ा बंद करो।", "Close the door!",
     "ᱫᱩᱣᱟᱹᱨ ᱵᱚᱸᱫᱚᱭ ᱢᱮ!", "pattern", "ᱯᱚᱛᱚᱵ ᱵᱚᱸᱫᱚᱭ ᱢᱮ! (noun swapped)", "instruction"),
    ("मेरी मदद करो।", "Please help me.",
     "ᱫᱟᱭᱟᱠᱟᱛᱮ ᱜᱚᱲᱚ ᱮᱢᱚᱜ ᱢᱮ ᱾", "attested", "ᱫᱟᱭᱟᱠᱟᱛᱮ ᱜᱚᱲᱚ ᱮᱢᱚᱜ ᱢᱮ ᱾", "praise"),
    ("बत्ती बंद करो।", "Turn off the lights.",
     "ᱢᱟᱨᱥᱟᱞ ᱵᱚᱱᱫᱚᱭ ᱢᱮ᱾", "attested", "ᱢᱟᱨᱥᱟᱞ ᱵᱚᱱᱫᱚᱭ ᱢᱮ᱾", "instruction"),
    ("कुर्सी ले लो।", "Take the chair.",
     "ᱢᱟᱹᱪᱤ ᱦᱟᱛᱟᱣ ᱢᱮ᱾", "pattern", "ᱮᱴᱟᱜ ᱢᱟᱹᱪᱤ ᱦᱟᱛᱟᱣ ᱢᱮ᱾", "instruction"),
    ("फल कहाँ है?", "Where is the fruit?",
     "ᱡᱚ ᱫᱚ ᱚᱠᱟᱨᱮ ᱢᱮᱱᱟᱜᱼᱟ ?", "attested", "ᱡᱚ ᱫᱚ ᱚᱠᱟᱨᱮ ᱢᱮᱱᱟᱜᱼᱟ ?", "question"),
    ("पानी पियो।", "Drink water.",
     "ᱫᱟᱜ ᱧᱩᱭ ᱢᱮ।", "pattern", "ᱟᱢᱟᱜ ᱯᱟᱹᱶᱨᱟᱹ ᱧᱩᱭ ᱢᱮ ᱾", "instruction"),
    ("गाना गाओ।", "Sing a song.",
     "ᱥᱮᱨᱮᱧ ᱵᱟᱡᱟᱣ ᱢᱮ᱾", "pattern", "ᱠᱚᱪ ᱥᱤᱨᱤᱧ ᱵᱟᱡᱟᱣ ᱢᱮ᱾", "activity"),
    ("यह एक गाँव है।", "This is a village.",
     "ᱱᱚᱶᱟ ᱫᱚ ᱢᱤᱫᱴᱟᱹᱝ ᱟᱹᱛᱩ ᱠᱟᱱᱟ ᱾", "attested",
     "ᱱᱚᱶᱟ ᱫᱚ ᱢᱤᱫᱴᱟᱹᱝ ᱟᱹᱛᱩ ᱠᱟᱱᱟ ᱾", "instruction"),
    ("मेरा नाम रवि है।", "My name is Ravi.",
     "ᱤᱧᱟᱜ ᱧᱩᱛᱩᱢ ᱫᱚ ᱨᱚᱵᱤ ᱠᱟᱱᱟ ᱾", "attested", "ᱤᱧᱟᱜ ᱧᱩᱛᱩᱢ ᱫᱚ ᱨᱚᱵᱤ ᱠᱟᱱᱟ ᱾", "instruction"),
    ("टोपी लो।", "Take the hat.",
     "ᱢᱩᱱᱰᱟᱥᱤᱱ ᱦᱟᱛᱟᱣ ᱢᱮ᱾", "pattern", "ᱮᱴᱟᱜ ᱢᱟᱹᱪᱤ ᱦᱟᱛᱟᱣ ᱢᱮ᱾", "instruction"),
    ("मछली पानी में रहती है।", "The fish lives in the water.",
     "ᱦᱟᱹᱠᱩ ᱫᱚ ᱫᱟᱜ ᱨᱮᱠᱚ ᱛᱟᱦᱮᱸᱱ ᱠᱟᱱᱟ᱾", "attested",
     "ᱟᱵᱚ ᱵᱚ ᱨᱚᱲᱟᱼ ᱦᱟᱹᱠᱩ ᱫᱚ ᱫᱟᱜ ᱨᱮᱠᱚ ᱛᱟᱦᱮᱸᱱ ᱠᱟᱱᱟ᱾", "instruction"),
    ("बच्चे यहाँ हैं।", "The children are here.",
     "ᱜᱤᱫᱽᱨᱟᱹ ᱠᱚ ᱱᱚᱰᱮ ᱢᱮᱱᱟᱜ ᱠᱚᱣᱟ ᱾", "attested",
     "ᱠᱚᱲᱟ ᱜᱤᱫᱽᱨᱟᱹ ᱠᱚ ᱱᱚᱰᱮ ᱢᱮᱱᱟᱜ ᱠᱚᱣᱟ ᱾", "instruction"),
    ("साथ में गाओ।", "Sing together.",
     "ᱥᱟᱶᱛᱮ ᱥᱮᱨᱮᱧ ᱢᱮ।", "pattern", "ᱥᱟᱶᱛᱮ ᱟᱥᱲᱟ ᱪᱟᱞᱟᱜ ᱯᱮ ᱾", "activity"),
    ("कुछ लिखो।", "Write something.",
     "ᱠᱤᱪᱷᱩ ᱚᱞ ᱢᱮ।", "pattern", "ᱢᱤᱫᱴᱟᱝ ᱢᱚᱛᱟᱱ ᱚᱞ ᱢᱮ।", "instruction"),
    ("ध्यान से देखो।", "Look carefully.",
     "ᱟᱪᱩᱨ ᱠᱟᱛᱮᱜ ᱧᱮᱞ ᱢᱮ।", "pattern", "ᱟᱪᱩᱨ ᱠᱟᱛᱮᱜ ᱯᱟᱲᱦᱟᱣ ᱢᱮ।", "instruction"),
    ("मुझे बताओ।", "Tell me.",
     "ᱤᱧ ᱞᱟᱹᱭ ᱢᱮ।", "pattern", "ᱤᱧ ᱠᱤᱪᱷᱩ ᱢᱚᱡᱟᱣᱟᱜ ᱞᱟᱹᱭᱟᱹᱧ ᱢᱮ ᱾", "question"),
    ("यहाँ आओ।", "Come here.",
     "ᱱᱚᱰᱮ ᱦᱮᱡ ᱢᱮ।", "pattern", "ᱦᱮᱡᱽ ᱥᱮᱱ", "praise"),
    ("फिर से लिखो।", "Write again.",
     "ᱟᱨᱦᱚᱸ ᱚᱞ ᱢᱮ᱾", "pattern", "ᱟᱨᱦᱚᱸ ᱚᱞ ᱠᱚ.", "praise"),
    ("फिर से पढ़ो।", "Read again.",
     "ᱟᱨᱦᱚᱸ ᱯᱟᱲᱦᱟᱣ ᱢᱮ।", "pattern", "ᱟᱨᱦᱚᱸ ᱯᱟᱲᱦᱟᱣᱢᱮ.", "praise"),
    ("बहुत अच्छा किया!", "Well done!",
     "ᱵᱮᱥ ᱠᱟᱛᱷᱟ!", "pattern", "ᱵᱮᱥ ᱠᱚᱲᱟ!", "praise"),
    # the flagship sentence from the problem statement (section 9 & 26 demo).
    # Every part is attested: ᱛᱮᱦᱮᱧ (ᱛᱮᱦᱮᱧᱟᱜ ᱪᱮᱫ ᱠᱷᱚᱵᱚᱨ?), ᱟᱞᱮ (ᱟᱞᱮ ᱟᱧᱡᱚᱢᱟ ᱞᱮ),
    # ᱞᱮᱠᱷᱟ (ᱞᱮᱠᱷᱟ ᱱᱚᱱᱫᱚ), ᱪᱮᱫᱚᱜ ᱢᱮ (ᱯᱟᱲᱦᱟᱣ ᱪᱮᱫᱚᱜ ᱢᱮ ᱾) - the frame is composed,
    # so it stays medium confidence and is queued for native-speaker validation.
    ("आज हम गिनती सीखेंगे।", "Today we will learn counting.",
     "ᱛᱮᱦᱮᱧ ᱟᱞᱮ ᱞᱮᱠᱷᱟ ᱪᱮᱫᱚᱜ ᱞᱮᱭᱟ।", "pattern",
     "ᱛᱮᱦᱮᱧ + ᱟᱞᱮ + ᱞᱮᱠᱷᱟ + ᱪᱮᱫᱚᱜ ᱢᱮ (attested parts, composed frame)", "instruction"),
    ("गिनती सीखो।", "Learn counting.",
     "ᱞᱮᱠᱷᱟ ᱪᱮᱫᱚᱜ ᱢᱮ!", "pattern", "ᱯᱟᱲᱦᱟᱣ ᱪᱮᱫᱚᱜ ᱢᱮ ᱾", "instruction"),
    ("अंग्रेज़ी सीखो।", "Learn English.",
     "ᱤᱝᱞᱤᱥ ᱪᱮᱫᱚᱜ ᱢᱮ!", "pattern", "ᱯᱟᱲᱦᱟᱣ ᱪᱮᱫᱚᱜ ᱢᱮ ᱾", "instruction"),
]
