import React, { useEffect, useState } from 'react'
import { useI18n } from '../i18n.js'
import { api, speak } from '../api.js'

// Every place a teacher can start from. Order matches the left nav.
const TILES = [
  ['translate', '🎙️', 'quickVoice', 'quickVoiceSub'],
  ['text', '⌨️', 'quickText', 'quickTextSub'],
  ['pdf', '📄', 'quickPdf', 'quickPdfSub'],
  ['lessons', '📚', 'quickLesson', 'quickLessonSub'],
  ['flashcards', '🃏', 'quickFlashcards', 'quickFlashcardsSub'],
  ['worksheets', '🖨️', 'quickWorksheet', 'quickWorksheetSub'],
  ['dictionary', '📖', 'nav_dictionary', 'quickDictSub'],
  ['vocab', '🔤', 'vocabTitle', 'quickVocabSub'],
]

const THEME_HI = {
  general: 'सामान्य', body: 'शरीर', family: 'परिवार', food: 'खाना-पानी',
  animals: 'जानवर', time: 'समय', nature: 'प्रकृति', school: 'विद्यालय', colours: 'रंग',
}

export default function Dashboard({ go, health }) {
  const { t, lang } = useI18n()
  const [phrases, setPhrases] = useState([])
  const [lesson, setLesson] = useState(null)
  const [newWords, setNewWords] = useState([])
  const [dictInfo, setDictInfo] = useState(null)
  const [langs, setLangs] = useState([])

  useEffect(() => {
    api.phrases().then((d) => setPhrases(d.items.slice(0, 5))).catch(() => {})
    api.lessons().then((d) => setLesson(d.lessons[0])).catch(() => {})
    // a spread of the words that came out of the school's own dictionary files
    api.dictionary().then((d) => {
      // classroom themes only - the panel is for words a teacher can use tomorrow,
      // not for the language and people names the same files also contain
      const THEMES = ['body', 'family', 'food', 'animals', 'school', 'colours', 'nature', 'time']
      const items = (d.items || []).filter((e) => e.sat && THEMES.includes(e.theme))
      const step = Math.max(1, Math.floor(items.length / 8))
      setNewWords(items.filter((_, i) => i % step === 0).slice(0, 8))
    }).catch(() => {})
    api.dictionaryFiles().then(setDictInfo).catch(() => {})
    api.languages().then((d) => setLangs(d.items || [])).catch(() => {})
  }, [])

  const c = health?.counts || {}
  const words = lesson?.words?.slice(0, 6) || []

  return (
    <>
      <div className="hero">
        <h2>{t('welcome')}</h2>
        <p>{t('welcomeSub')}</p>
        <div className="row">
          <button className="btn" onClick={() => go('translate')}>🎙️ {t('quickVoice')}</button>
          <button className="btn ghost" onClick={() => go('text')}>⌨️ {t('quickText')}</button>
          <button className="btn ghost" onClick={() => go('pdf')}>📄 {t('quickPdf')}</button>
        </div>
      </div>

      <div className="grid g4" style={{ marginBottom: 16 }}>
        {TILES.map(([id, ico, k1, k2]) => (
          <div key={id} className="card card-pad tile" onClick={() => go(id)}>
            <div className="ico">{ico}</div>
            <h3>{t(k1)}</h3>
            <p>{t(k2)}</p>
          </div>
        ))}
      </div>

      <div className="grid g4" style={{ marginBottom: 16 }}>
        <div className="card card-pad stat"><div className="n">{c.vocab ?? '–'}</div><div className="l">{t('statWords')}</div></div>
        <div className="card card-pad stat"><div className="n">{c.phrases ?? '–'}</div><div className="l">{t('statPhrases')}</div></div>
        <div className="card card-pad stat"><div className="n">{c.dictionary_entries ?? '–'}</div><div className="l">{t('statDictWords')}</div></div>
        <div className="card card-pad stat"><div className="n">{c.dictionary_numbers ?? '–'}</div><div className="l">{t('statNumbers')}</div></div>
      </div>

      <div className="grid g4" style={{ marginBottom: 16 }}>
        <div className="card card-pad stat"><div className="n">{c.verbs ?? '–'}</div><div className="l">{t('statAttested')}</div></div>
        <div className="card card-pad stat"><div className="n">{c.sentence_memory?.toLocaleString?.() ?? '–'}</div><div className="l">{t('statMemory')}</div></div>
        <div className="card card-pad stat"><div className="n">{c.dictionary_sentences ?? '–'}</div><div className="l">{t('dict_sentences')}</div></div>
        <div className="card card-pad stat"><div className="n">{health?.verified_overrides ?? 0}</div><div className="l">{t('statVerified')}</div></div>
      </div>

      <div className="grid g2">
        <div className="card card-pad">
          <div className="label">{t('todaysPlan')} · {t('phrases')}</div>
          {phrases.map((p) => (
            <div key={p.hindi} className="wordrow" style={{ marginBottom: 8 }}>
              <div className="grow">
                <div className="hi bold">{p.hindi}</div>
                <div className="ol" style={{ fontSize: 18, color: 'var(--indigo)', marginTop: 3 }}>{p.sat}</div>
                <div className="small muted">{p.english}</div>
              </div>
              <span className={`badge ${p.confidence}`}>{t(p.confidence)}</span>
              <button className="speaker" title={t('playSat')} onClick={() => speak(p.sat, 'sat')}>🔊</button>
            </div>
          ))}
          <button className="btn ghost small wide" style={{ marginTop: 6 }} onClick={() => go('lessons')}>
            {t('nav_lessons')} →
          </button>
        </div>

        <div className="card card-pad">
          <div className="label">{lesson ? `${lesson.emoji} ${lesson.hi} · ${lesson.en}` : t('loading')}</div>
          <div className="grid g2">
            {words.map((w) => (
              <div key={w.hindi} className="wordrow" onClick={() => speak(w.sat, 'sat')} role="button">
                <div className="emoji">{w.emoji}</div>
                <div className="grow">
                  <div className="hi bold">{w.hindi}</div>
                  <div className="ol" style={{ fontSize: 17, color: 'var(--indigo)' }}>{w.sat}</div>
                  <div className="xsmall muted">{w.sat_roman}</div>
                </div>
              </div>
            ))}
          </div>
          <button className="btn ghost small wide" style={{ marginTop: 10 }} onClick={() => go('flashcards')}>
            🃏 {t('flashcardsTitle')} →
          </button>
        </div>
      </div>

      {langs.length > 0 && (
        <div className="card card-pad" style={{ marginTop: 16 }}>
          <div className="label">🌐 {t('langPanelTitle')}</div>
          <div className="small muted" style={{ marginBottom: 10 }}>{t('langPanelNote')}</div>
          <div className="grid g4">
            {langs.map((l) => (
              <div key={l.code} className="card card-pad" style={{ boxShadow: 'none', border: '1px solid var(--line, #e6e9f0)' }}>
                <div className="bold">{l.language}</div>
                <div className="xsmall muted">{l.script}</div>
                <div className="small" style={{ marginTop: 6 }}>
                  {(l.layers?.attested_sentences ?? l.counts?.sentence_memory ?? 0).toLocaleString()}{' '}
                  {t('langSentences')}
                </div>
                {l.layers?.machine_augmented_sentences ? (
                  <div className="xsmall muted">
                    + {l.layers.machine_augmented_sentences.toLocaleString()} 🧪 {t('synthBadge')}
                  </div>
                ) : null}
                {l.layers?.dictionary_en ? (
                  <div className="xsmall muted">{l.layers.dictionary_en} {t('langWords')}</div>
                ) : null}
                {l.layers?.hindi_reachable_words ? (
                  <div className="xsmall muted">
                    {l.layers.hindi_reachable_words} {t('langWords')} · {t('langHindiIn')}
                  </div>
                ) : null}
                <div className="xsmall muted">
                  {t('langHindiIn')}: {l.hindi_supported}
                </div>
                <div className="xsmall" style={{ marginTop: 4 }}>
                  {l.tts?.available
                    ? (l.tts.approx ? `🔊 ${t('ttsApprox')}` : `🔊 ${l.tts.engine}`)
                    : `🔇 ${t('ttsNone')}`}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="card card-pad" style={{ marginTop: 16 }}>
        <div className="label">{t('dictRowTitle')}</div>
        <div className="grid g4">
          {newWords.map((e) => (
            <div key={e.hi + e.sat} className="wordrow" onClick={() => speak(e.sat, 'sat')} role="button">
              <div className="grow">
                <div className="hi bold">{e.hi}</div>
                <div className="ol" style={{ fontSize: 17, color: 'var(--indigo)' }}>{e.sat}</div>
                <div className="xsmall muted">
                  {lang === 'hi' ? THEME_HI[e.theme] || e.theme : e.theme} · {e.en}
                </div>
              </div>
              <span className={`badge ${e.confidence}`}>{t(e.confidence)}</span>
            </div>
          ))}
        </div>
        <div className="row" style={{ marginTop: 8 }}>
          <button className="btn ghost small" onClick={() => go('dictionary')}>
            📖 {t('nav_dictionary')} →
          </button>
          {dictInfo ? (
            <span className="small muted" style={{ alignSelf: 'center' }}>
              {dictInfo.files_used}/{dictInfo.files_supplied} {t('dict_files_used')} ·{' '}
              {dictInfo.totals.proper_names} {t('dict_names')} ·{' '}
              {dictInfo.totals.dictionary_sentences} {t('dict_sentences')}
            </span>
          ) : null}
        </div>
      </div>
    </>
  )
}
