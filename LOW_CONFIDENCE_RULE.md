# Low confidence = words, never a sentence

Live on **http://localhost:8100** · build **BN97rGbS** · both suites green.

## The rule you asked for

| Confidence | What the teacher gets |
|---|---|
| **high** | the Santhali sentence + the method and its evidence |
| **medium** | the Santhali sentence, marked for validation |
| **low / none** | **never a sentence** — the combination of the words we know, in order, with a spoken rendering and a `known/total` count |

## What it looks like now

```
SENTENCE  किताब बंद करो।              ᱯᱚᱛᱚᱵ ᱵᱚᱸᱫᱚᱭ ᱢᱮ!        [high]
SENTENCE  खोपड़ी                      ᱠᱷᱟᱯᱨᱤ                [high]
SENTENCE  25                          ᱵᱟᱨ ᱜᱮᱞ ᱢᱚᱬᱮ          [high]
WORDS     सरकारी स्कूल में नया शिक्षक आया है।  ᱥᱠᱩᱞ ᱱᱟᱣᱟ ᱢᱟᱪᱮᱫ ᱦᱮᱡ    4/7 words
WORDS     आज मौसम बहुत अच्छा है।      ᱛᱮᱦᱮᱧ ᱱᱟᱯᱟᱭ          2/5 words
WORDS     मुझे बाजार से दो किलो चावल…  ᱵᱟᱨᱭᱟ ᱪᱟᱣᱞᱮ           2/8 words
```

On screen the word case shows a card headed **“no confident sentence”** with:
- the combination in Ol Chiki, large, with its roman reading
- 🔊 and 🐢 buttons to hear the combination
- `2/5 words · 40%`
- a plain explanation: *a wrong sentence cannot be un-read — read these out and build the
  sentence the way you would say it in class*
- the function words that were left out, named, so nothing is hidden

Same rule on **Text → Text** (copy button included) and on **PDF translation**, which
already worked this way.

## Two details worth knowing

1. **Nothing is thrown away.** If the cascade had produced a low-confidence sentence, it moves
   into a `suppressed` field with the reason — still visible to a teacher, still sent to the
   validation queue — it is just never shown as *the answer*.

2. **Function words are excluded and named.** The corpus had aligned है → ᱠᱤᱱ (a dual
   marker) and हैं → ᱠᱚ (a plural marker). Putting those in a word list teaches a mistake,
   so they are left out and listed under `skipped`; the coverage % counts them as unknown so
   the number never flatters itself.

## Tested

The rule is now locked in by the suite, not just described:

```
178 checks | PASS 154 | review 24 | FAIL 0      (Hindi suite, +9 rule rows)
 31 checks | PASS  31 | review  0 | FAIL 0      (Odia suite)
```

The new rows assert, against the running server: a low-confidence input returns **no
sentence**, returns **words instead**, labels itself `word-combo/low`, that a confident input
is still translated as before, that the **combination is speakable** (real audio bytes
returned), and that function words are **reported rather than smuggled in**.

Reports: `tests/hindi_testing_sentences.md` / `.csv`, `tests/odia_testing.md` / `.csv`.
