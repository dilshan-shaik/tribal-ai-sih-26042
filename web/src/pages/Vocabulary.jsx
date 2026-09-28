import React, { useEffect, useMemo, useState } from 'react'
import { useI18n, CATEGORY_HI } from '../i18n.js'
import { api, speak } from '../api.js'

export default function Vocabulary() {
  const { t, lang } = useI18n()
  const [all, setAll] = useState([])
  const [q, setQ] = useState('')
  const [cat, setCat] = useState('all')
  const [onlyVerified, setOnlyVerified] = useState(false)
  const [playing, setPlaying] = useState(false)

  useEffect(() => { api.vocab('all').then((d) => setAll(d.items)).catch(() => {}) }, [])

  const cats = useMemo(() => ['all', ...Array.from(new Set(all.map((v) => v.category)))], [all])
  const items = useMemo(() => {
    let s = all
    if (cat !== 'all') s = s.filter((v) => v.category === cat)
    if (onlyVerified) s = s.filter((v) => v.verified)
    if (q.trim()) {
      const n = q.trim().toLowerCase()
      s = s.filter((v) => v.hindi.includes(n) || (v.english || '').toLowerCase().includes(n) || (v.sat || '').includes(n))
    }
    return s
  }, [all, cat, q, onlyVerified])

  function playAll() {
    setPlaying(true)
    const seq = items.filter((v) => v.sat).slice(0, 8)
    seq.forEach((v, i) => setTimeout(() => {
      speak(v.sat, 'sat', { onEnd: () => i === seq.length - 1 && setPlaying(false) })
    }, i * 1800))
  }

  return (
    <>
      <div className="chipbar" style={{ marginBottom: 12 }}>
        <input className="field" style={{ maxWidth: 340 }} placeholder={t('search')} value={q} onChange={(e) => setQ(e.target.value)} />
        <button className="btn" onClick={playAll} disabled={playing}>{playing ? '⏸' : '🔊'} {t('playAll')}</button>
      </div>

      <div className="chipbar" style={{ marginBottom: 10 }}>
        {cats.map((c) => (
          <button key={c} className={`chip ${cat === c ? 'active' : ''}`} onClick={() => setCat(c)}>
            {c === 'all' ? t('allCategories') : (lang === 'hi' ? CATEGORY_HI[c] || c : c)}
          </button>
        ))}
      </div>

      <label className="small muted" style={{ display: 'flex', gap: 6, alignItems: 'center', marginBottom: 14 }}>
        <input type="checkbox" checked={onlyVerified} onChange={(e) => setOnlyVerified(e.target.checked)} />
        {t('confidenceFilter')}
      </label>

      <div className="card card-pad">
        <table className="simple">
          <thead>
            <tr>
              <th style={{ width: 46 }} />
              <th>हिन्दी</th>
              <th>English</th>
              <th>{t('santhaliOut')}</th>
              <th>{t('romanOut')}</th>
              <th>{t('confidence')}</th>
              <th style={{ width: 60 }}>{t('playSat')}</th>
            </tr>
          </thead>
          <tbody>
            {items.map((v) => (
              <tr key={v.hindi}>
                <td style={{ fontSize: 20 }}>{v.emoji}</td>
                <td className="hi bold">{v.hindi}</td>
                <td className="muted">{v.english}</td>
                <td className="ol" style={{ fontSize: 20, color: 'var(--indigo)' }}>{v.sat || <span className="muted small">—</span>}</td>
                <td className="mono small">{v.sat_roman}</td>
                <td>
                  <span className={`badge ${v.confidence}`}>{t(v.confidence)}</span>{' '}
                  {v.verified && <span className="badge verified">✓</span>}
                </td>
                <td>{v.sat && <button className="speaker" onClick={() => speak(v.sat, 'sat')}>🔊</button>}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {items.length === 0 && <div className="empty">{t('noResult')}</div>}
      </div>
      <div className="small muted" style={{ marginTop: 10 }}>{items.length} / {all.length} {t('words')}</div>
    </>
  )
}
