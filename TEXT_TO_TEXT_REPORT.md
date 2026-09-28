# Text → Text — the new text-only translation screen

Server running on port 8000 with the new build (`index-Ciud18U3.js`).

## What was added

**A new screen in the left nav: ⌨️ पाठ → पाठ / Text → Text** — and a matching tile plus a hero
button on the Dashboard (`quickText` → `quickTextSub`), so it is reachable from the dashboard
the way you asked.

It is translation by **typing only**:

| On this screen | Not on this screen |
|---|---|
| Hindi textarea, auto-focused on open | ❌ microphone / dictation |
| ➡️ Translate (or **Ctrl + Enter**) | ❌ recording button |
| Santhali in Ol Chiki, big and copyable | ❌ any audio playback |
| Roman reading + Devanagari reading under it | ❌ no permission prompts, nothing to allow |
| 📋 Copy Santhali → straight into a worksheet, register or WhatsApp | |
| "Words it knows" chips when it cannot translate the whole sentence | |
| Recent translations list (kept on this device, clearable) | |

Files touched: `web/src/pages/TextTranslate.jsx` (new), `web/src/App.jsx` (nav + route + title),
`web/src/pages/Dashboard.jsx` (tile + hero button), `web/src/i18n.js` (18 new keys in English
**and** Hindi), `web/src/styles.css`.

Everything is bilingual, and every key used by the page is present in both language blocks —
checked programmatically, `missing: none`.

## Verified against the running server

| Typed on the new screen | Result | Method |
|---|---|---|
| किताब बंद करो। | ᱯᱚᱛᱚᱵ ᱵᱚᱸᱫᱚᱭ ᱢᱮ! | phrase |
| मेरा नाम रवि है। | ᱤᱧᱟᱜ ᱧᱩᱛᱩᱢ ᱫᱚ ᱨᱚᱵᱤ ᱠᱟᱱᱟ ᱾ | phrase |
| खोपड़ी | ᱠᱷᱟᱯᱨᱤ | dictionary (from your uploaded files) |
| 25 | ᱵᱟᱨ ᱜᱮᱞ ᱢᱚᱬᱮ | number system |
| बकवास जुमला अजीब | declined — lists the words it does know | — |

## Suites still green after the change

| Suite | Result |
|---|---|
| `tests/hindi_test_suite.py` | 169 checks · PASS 145 · review 24 · FAIL 0 |
| `tests/odia_test_suite.py` | 31 checks · PASS 31 · FAIL 0 |

The two screens now sit side by side: **🎙️ Voice Translator** for speaking (Hindi mic → translate
→ Santhali audio, all three voice paths still intact) and **⌨️ Text → Text** for typing when a
microphone is not available or not wanted.
