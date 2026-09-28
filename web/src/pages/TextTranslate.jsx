import React, { useEffect, useRef, useState } from 'react'
import { useI18n } from '../i18n.js'
import { api } from '../api.js'
import { store } from '../store.js'
import LanguageSelect from '../components/LanguageSelect.jsx'

// typing-only screen: no microphone and no playback on purpose. The target language
// still matters, and it still says plainly when a language is words-only.
const outOf = (res) => res?.target
  || (res?.sat ? { text: res.sat.olchiki, script: 'Ol Chiki', roman: res.sat.roman,
                   devanagari: res.sat.devanagari, language: 'Santhali' } : null)

// Text -> text only. No microphone, no recording, no audio playback: a teacher typing
// on a laptop with no permission prompts can translate Hindi to Santhali and copy the
// result straight into a worksheet, a WhatsApp message or the register.
const EXAMPLES = [
  'किताब बंद करो।',
  'यह एक पेड़ है।',
  'आज हम गिनती सीखेंगे।',
  'मेरा नाम रवि है।',
  'खोपड़ी',
  '25',
]

const METHOD_KEY = {
  phrase: 'methodPhrase',
  vocab: 'methodVocab',
  dictionary: 'methodDictionary',
  number: 'methodNumber',
  template: 'methodTemplate',
  wikidata: 'methodWikidata',
  wordbank: 'methodWordbank',
  'word-combo': 'methodWordCombo',
  'sentence-memory-aug': 'methodSentenceAug',
  'sentence-memory-en': 'methodSentenceEn',
  'sentence-memory-en-fuzzy': 'methodSentenceEnFuzzy',
}

export default function TextTranslate({ notify }) {
  const { t, lang } = useI18n()
  const [text, setText] = useState('')
  const [res, setRes] = useState(null)
  const [busy, setBusy] = useState(false)
  const [target, setTarget] = useState('sat')
  const [history, setHistory] = useState(() => store.get('mtb-text-history') || [])
  const box = useRef(null)

  useEffect(() => { box.current?.focus() }, [])

  async function run(value) {
    const q = (value ?? text).trim()
    if (!q) return
    setBusy(true)
    try {
      const r = await api.translate(q, 'hi', target)
      setRes(r)
      const o = outOf(r)
      if (r.ok && o) {
        const row = { hi: q, sat: o.text, roman: o.roman, method: r.method }
        const next = [row, ...history.filter((h) => h.hi !== q)].slice(0, 8)
        setHistory(next)
        store.set('mtb-text-history', next)
      }
    } catch (e) {
      setRes({ ok: false, error: t('error') })
    } finally {
      setBusy(false)
    }
  }

  async function copy(s) {
    try {
      await navigator.clipboard.writeText(s)
      notify?.(t('ttCopied'))
    } catch {
      notify?.(t('ttCopyFailed'))
    }
  }

  function clear() {
    setText('')
    setRes(null)
    box.current?.focus()
  }

  const out = outOf(res)
  const sat = (out && res?.ok) ? out.text : ''

  return (
    <>
      <div className="card card-pad" style={{ marginBottom: 14 }}>
        <LanguageSelect value={target} onChange={setTarget} />
        <div className="label">{t('ttInLabel')}</div>
        <textarea
          ref={box}
          className="field hi"
          rows={5}
          value={text}
          placeholder={t('typeHindi')}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => { if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) run() }}
        />
        <div className="chipbar" style={{ marginTop: 12 }}>
          <button className="btn" onClick={() => run()} disabled={busy || !text.trim()}>
            {busy ? '⏳' : '➡️'} {t('ttTranslate')}
          </button>
          <button className="btn ghost" onClick={clear} disabled={!text && !res}>✕ {t('ttClear')}</button>
          <span className="small muted" style={{ alignSelf: 'center' }}>{t('ttShortcut')}</span>
        </div>
      </div>

      <div className="card card-pad" style={{ marginBottom: 14 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8 }}>
          <span className="label" style={{ margin: 0 }}>{t('ttOutLabel')}</span>
          {sat ? (
            <button className="btn ghost small" onClick={() => copy(sat)}>📋 {t('ttCopy')}</button>
          ) : null}
        </div>

        {!res && (
          <>
            <div className="small muted" style={{ marginBottom: 10 }}>{t('ttEmpty')}</div>
            <div className="chipbar">
              {EXAMPLES.map((e) => (
                <button key={e} className="chip hi" onClick={() => { setText(e); run(e) }}>{e}</button>
              ))}
            </div>
          </>
        )}

        {res && !res.ok && res.method === 'word-combo' && (
          <>
            {/* low confidence: never a sentence - the combination of known words instead */}
            <div className="combo-head">
              <span className="badge low">🧩 {t('comboBadge')}</span>
              {res.target?.language ? (
                <span className="small muted">{res.target.language} · {res.target.script}</span>
              ) : null}
              <span className="small muted">
                {res.known ?? 0}/{res.total ?? 0} {t('words')}
                {res.coverage ? ` · ${Math.round(res.coverage * 100)}%` : ''}
              </span>
            </div>
            {res.combined ? (
              <>
                <div className="ol big-sat" style={{ marginTop: 10 }}>{res.combined}</div>
                {res.combined_roman ? (
                  <div className="small muted" style={{ marginTop: 6 }}>{res.combined_roman}</div>
                ) : null}
                <div className="chipbar" style={{ marginTop: 10 }}>
                  <button className="btn ghost small" onClick={() => copy(res.combined)}>
                    📋 {t('ttCopy')}
                  </button>
                </div>
              </>
            ) : (
              <div className="bold" style={{ marginTop: 8 }}>{t('comboNothing')}</div>
            )}
            <div className="small muted" style={{ marginTop: 10 }}>{t('comboNote')}</div>
            {res.skipped?.length ? (
              <div className="xsmall muted" style={{ marginTop: 6 }}>
                {t('comboSkipped')}: {res.skipped.join(' · ')}
              </div>
            ) : null}
          </>
        )}

        {res && !res.ok && res.method !== 'word-combo' && (
          <div className="empty">
            <div style={{ fontSize: 30 }}>🤔</div>
            <div className="bold" style={{ marginTop: 6 }}>{res.error || t('ttDeclined')}</div>
            {res.hint ? <div className="small muted" style={{ marginTop: 6 }}>{res.hint}</div> : null}
          </div>
        )}

        {res && res.ok && (
          <>
            <div className="chipbar" style={{ marginBottom: 10 }}>
              <span className={`badge ${res.confidence}`}>{t('confidence')}: {t(res.confidence)}</span>
              {res.synthetic && <span className="badge medium">🧪 {t('synthBadge')}</span>}
              <span className="small muted">{t(METHOD_KEY[res.method] || res.method)}</span>
            </div>
            {out?.language ? (
              <div className="small muted" style={{ marginBottom: 6 }}>
                {out.language} · {out.script}{res.tts?.available === false ? ` · ${t('ttsNone')}` : ''}
              </div>
            ) : null}
            <div className="ol big-sat">{sat}</div>
            {out?.roman ? <div className="small muted" style={{ marginTop: 6 }}>{out.roman}</div> : null}
            {out?.devanagari ? (
              <div className="hi" style={{ marginTop: 8, fontSize: 17 }}>{out.devanagari}</div>
            ) : null}
            {res.english_gloss ? (
              <div className="small muted" style={{ marginTop: 8 }}>English: {res.english_gloss}</div>
            ) : null}
            {res.synthetic ? (
              <div className="small" style={{ marginTop: 8, color: '#92400e' }}>🧪 {t('synthNote')}</div>
            ) : null}
            {(res.wordbank?.length || res.words?.length) ? (
              <div style={{ marginTop: 14 }}>
                <div className="label">{t('ttWordBank')}</div>
                <div className="chipbar">
                  {(res.wordbank || res.words).map((w) => (
                    <span key={(w.hindi || w.english) + (w.sat || w.tgt)} className="chip">
                      {w.hindi || w.english} = <span className="ol">{w.sat || w.tgt}</span>
                    </span>
                  ))}
                </div>
              </div>
            ) : null}
          </>
        )}
      </div>

      {history.length > 0 && (
        <div className="card card-pad">
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <span className="label" style={{ margin: 0 }}>{t('ttHistory')}</span>
            <button className="btn ghost small" onClick={() => { setHistory([]); store.set('mtb-text-history', []) }}>
              {t('ttClearHistory')}
            </button>
          </div>
          <table className="simple" style={{ marginTop: 8 }}>
            <tbody>
              {history.map((h) => (
                <tr key={h.hi} onClick={() => { setText(h.hi); run(h.hi) }} style={{ cursor: 'pointer' }}>
                  <td className="hi" style={{ fontWeight: 600 }}>{h.hi}</td>
                  <td className="ol">{h.sat}</td>
                  <td className="muted small">{h.roman || ''}</td>
                  <td style={{ width: 40 }}>
                    <button className="icon-btn" onClick={(e) => { e.stopPropagation(); copy(h.sat) }}>📋</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {lang === 'hi' ? <div className="small muted" style={{ marginTop: 8 }}>{t('ttHistoryNote')}</div> : null}
        </div>
      )}
    </>
  )
}
