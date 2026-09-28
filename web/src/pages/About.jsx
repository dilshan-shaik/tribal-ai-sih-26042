import React from 'react'
import { useI18n } from '../i18n.js'

const MAP = [
  ['Shortage of teachers who can teach tribal languages', 'AI-assisted Hindi → Santhali translation with attested, corpus-verified phrases'],
  ['Lack of digital resources for Santhali / Ho / Mundari', 'Language packs built from Hugging Face parallel corpora + Wikidata; pack format is language-agnostic'],
  ['No tribal-language speech recognition or TTS', 'Voice input via hi-IN ASR; Santhali audio through transliteration + cached clips (real Santhali TTS model drops into the same slot)'],
  ['Poor internet in rural schools', 'Offline-first: language pack, audio clips and app shell cached on device'],
  ['Teachers cannot prepare multilingual material', 'One-click bilingual worksheets and flashcards, print-ready A4'],
  ['Risk of wrong translation confusing students', 'Human-in-the-loop validation: every string carries confidence + evidence, teachers correct and it applies platform-wide'],
]

const STACK = [
  ['Frontend', 'React 18 + Vite — English/Hindi UI toggle, works on low-end Android browsers'],
  ['Backend', 'FastAPI (Python) — translation API, TTS, worksheet generator, validation queue'],
  ['Data layer', 'SQLite for validation/usage, JSON language pack for offline'],
  ['AI / NLP', 'HF parallel corpora, Wikidata sitelinks, attested pattern grammar, Ol Chiki ↔ Devanagari transliteration'],
  ['Speech', 'Web Speech API (hi-IN) for teacher input; gTTS Hindi voice for students'],
  ['Deployable as', 'Single service — an Android wrapper (WebView) or a school LAN server both work'],
]

const ROADMAP = [
  ['Phase 1 — Hackathon MVP', 'Hindi text + voice input, Hindi → Santhali translation, Santhali audio, worksheets, flashcards, offline caching. ✅ this build'],
  ['Phase 2', 'More educational vocabulary, teacher dashboard analytics, better speech models'],
  ['Phase 3', 'Fully offline translation + offline ASR/TTS models on device'],
  ['Phase 4', 'Ho and Mundari language packs, other states'],
]

export default function About() {
  const { t } = useI18n()
  return (
    <div className="grid g2">
      <div className="card card-pad" style={{ gridColumn: '1 / -1' }}>
        <div className="label">{t('impacts')} — problem → solution mapping</div>
        <table className="simple">
          <thead><tr><th>Barrier in the problem statement</th><th>What this prototype does</th></tr></thead>
          <tbody>
            {MAP.map(([a, b]) => (
              <tr key={a}><td style={{ width: '38%' }}>{a}</td><td>{b}</td></tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="card card-pad">
        <div className="label">{t('arch')}</div>
        <div className="small" style={{ lineHeight: 2 }}>
          <div>🎙️ <b>Teacher speaks Hindi</b> → browser speech recognition (hi-IN)</div>
          <div style={{ marginLeft: 18 }}>↓</div>
          <div>🧠 <b>Translation engine</b> — 5-step cascade that never invents Santhali</div>
          <div style={{ marginLeft: 18 }}>↓</div>
          <div className="small muted" style={{ marginLeft: 18 }}>
            1. classroom phrase book (corpus-attested)<br />
            2. curated 208-word educational glossary<br />
            3. Wikidata Hindi → Santhali title memory (6,911 forms)<br />
            4. instruction templates inside attested Santhali frames<br />
            5. word-by-word vocabulary assist (clearly flagged)
          </div>
          <div style={{ marginLeft: 18 }}>↓</div>
          <div>🔊 <b>Santhali audio</b> for students + big Ol Chiki text on screen</div>
          <div style={{ marginLeft: 18 }}>↓</div>
          <div>🖨️ <b>Worksheets &amp; flashcards</b> generated in Hindi + Santhali</div>
          <div style={{ marginLeft: 18 }}>↓</div>
          <div>✅ <b>Teacher/native-speaker validation</b> improves the pack for everyone</div>
        </div>
      </div>

      <div className="card card-pad">
        <div className="label">{t('stack')}</div>
        <table className="simple">
          <tbody>{STACK.map(([a, b]) => <tr key={a}><td className="bold" style={{ width: 130 }}>{a}</td><td>{b}</td></tr>)}</tbody>
        </table>
      </div>

      <div className="card card-pad" style={{ gridColumn: '1 / -1' }}>
        <div className="label">{t('phase')}</div>
        <div className="grid g4">
          {ROADMAP.map(([a, b]) => (
            <div key={a} className="cell" style={{ border: '1px solid var(--line)', borderRadius: 14, padding: 14 }}>
              <div className="bold small">{a}</div>
              <div className="small muted" style={{ marginTop: 6, lineHeight: 1.6 }}>{b}</div>
            </div>
          ))}
        </div>
      </div>

      <div className="card card-pad" style={{ gridColumn: '1 / -1' }}>
        <div className="label">Honest limitations (and why they matter)</div>
        <ul className="small" style={{ lineHeight: 1.8, margin: 0, paddingLeft: 20 }}>
          <li>There is still no public Santhali TTS voice — audio is a Hindi voice reading a
            phonetically close Devanagari transliteration. Pronunciation is approximate; the
            API slot for a real Santhali voice is ready.</li>
          <li>Free-form sentence translation is not reliable in low-resource languages. This build
            shows the evidence behind every answer instead of hiding uncertainty, and routes
            anything unverified to teachers and native speakers.</li>
          <li>15 of the 208 curated words still have no confident Santhali form; they are shown as
            blank and queued for validation rather than guessed.</li>
        </ul>
      </div>
    </div>
  )
}
