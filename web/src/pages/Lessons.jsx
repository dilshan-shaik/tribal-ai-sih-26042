import React, { useEffect, useState } from 'react'
import { useI18n } from '../i18n.js'
import { api, speak } from '../api.js'

export default function Lessons({ notify }) {
  const { t } = useI18n()
  const [lessons, setLessons] = useState([])
  const [active, setActive] = useState(null)
  const [present, setPresent] = useState(false)
  const [idx, setIdx] = useState(0)

  useEffect(() => {
    api.lessons().then((d) => { setLessons(d.lessons); setActive(d.lessons[0]) }).catch(() => {})
  }, [])

  const items = active ? [...active.phrases.map((p) => ({ kind: 'phrase', ...p })), ...active.words.map((w) => ({ kind: 'word', ...w }))] : []

  useEffect(() => {
    if (!present) return
    const h = (e) => {
      if (e.key === 'ArrowRight') setIdx((i) => Math.min(i + 1, items.length - 1))
      if (e.key === 'ArrowLeft') setIdx((i) => Math.max(i - 1, 0))
      if (e.key === 'Escape') setPresent(false)
      if (e.key === ' ') { e.preventDefault(); play() }
    }
    window.addEventListener('keydown', h)
    return () => window.removeEventListener('keydown', h)
  }, [present, items, idx])

  function play() {
    const it = items[idx]
    if (it?.sat) speak(it.sat, 'sat')
  }

  return (
    <>
      <div className="chipbar" style={{ marginBottom: 16 }}>
        {lessons.map((l) => (
          <button key={l.id} className={`chip ${active?.id === l.id ? 'active' : ''}`}
            onClick={() => { setActive(l); setIdx(0) }}>
            {l.emoji} <span className="hi">{l.hi}</span> · {l.word_count}
          </button>
        ))}
      </div>

      {active && (
        <>
          <div className="card card-pad" style={{ marginBottom: 16, display: 'flex', gap: 14, alignItems: 'center', flexWrap: 'wrap' }}>
            <div style={{ fontSize: 40 }}>{active.emoji}</div>
            <div className="grow">
              <div className="bold hi" style={{ fontSize: 19 }}>{active.hi} <span className="muted small">/ {active.en}</span></div>
              <div className="small muted">आज का निर्देश · <span className="hi">{active.instruction_hi}</span></div>
            </div>
            <button className="btn" onClick={() => { setPresent(true); setIdx(0); play() }}>▶ {t('present')}</button>
          </div>

          <div className="grid g2">
            <div className="card card-pad">
              <div className="label">{t('phrases')}</div>
              {active.phrases.map((p) => (
                <div key={p.hindi} className="wordrow" style={{ marginBottom: 8 }}>
                  <div className="grow">
                    <div className="hi bold">{p.hindi}</div>
                    <div className="ol" style={{ fontSize: 19, color: 'var(--indigo)' }}>{p.sat}</div>
                    <div className="xsmall muted">{p.sat_roman}</div>
                  </div>
                  <span className={`badge ${p.confidence}`}>{t(p.confidence)}</span>
                  <button className="speaker" onClick={() => speak(p.sat, 'sat')}>🔊</button>
                </div>
              ))}
            </div>

            <div className="card card-pad">
              <div className="label">{t('words')}</div>
              <div className="grid g2">
                {active.words.map((w) => (
                  <div key={w.hindi} className="wordrow" onClick={() => speak(w.sat, 'sat')} role="button">
                    <div className="emoji">{w.emoji}</div>
                    <div className="grow">
                      <div className="hi bold">{w.hindi}</div>
                      <div className="ol" style={{ fontSize: 18, color: 'var(--indigo)' }}>{w.sat}</div>
                      <div className="xsmall muted">{w.sat_roman}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </>
      )}

      {present && items[idx] && (
        <div className="presenter">
          <div className="bar">
            <span className="pill" style={{ background: 'rgba(255,255,255,.12)', color: '#fff', borderColor: 'transparent' }}>
              {active.emoji} <span className="hi">{active.hi}</span>
            </span>
            <div className="spacer" />
            <span className="small" style={{ color: '#c7c9f5' }}>{t('presentHint')}</span>
            <button className="btn ghost small" onClick={() => setPresent(false)}>{t('exitPresent')} ✕</button>
          </div>
          <div className="stage" onClick={() => setIdx((i) => Math.min(i + 1, items.length - 1))}>
            {items[idx].kind === 'word' && <div className="emoji">{items[idx].emoji}</div>}
            {items[idx].kind === 'phrase' && <div className="emoji">🗣️</div>}
            <div className="hi">{items[idx].kind === 'word' ? items[idx].hindi : items[idx].hindi}</div>
            <div className="ol">{items[idx].sat}</div>
            <div className="roman">{items[idx].sat_roman}</div>
            <button className="btn" onClick={(e) => { e.stopPropagation(); play() }}>🔊 {t('listenSat')}</button>
          </div>
          <div className="bar" style={{ justifyContent: 'center' }}>
            <button className="btn ghost small" onClick={() => setIdx((i) => Math.max(0, i - 1))}>← {t('prev')}</button>
            <div className="dots">
              {items.map((_, i) => <i key={i} className={i === idx ? 'on' : ''} />)}
            </div>
            <button className="btn ghost small" onClick={() => setIdx((i) => Math.min(items.length - 1, i + 1))}>{t('next')} →</button>
          </div>
        </div>
      )}
    </>
  )
}
