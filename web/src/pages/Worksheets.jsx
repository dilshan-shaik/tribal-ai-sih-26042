import React, { useEffect, useRef, useState } from 'react'
import { useI18n, CATEGORY_HI } from '../i18n.js'
import { api } from '../api.js'

const TEMPLATES = ['picture_label', 'trace_write', 'vocab_match', 'count_write', 'fill_blank']
const CATS = ['fruits', 'numbers', 'animals', 'birds', 'colours', 'body', 'family', 'school', 'food', 'nature', 'actions']

export default function Worksheets({ notify }) {
  const { t, lang } = useI18n()
  const [spec, setSpec] = useState({
    template: 'picture_label', title_en: 'Fruits — Bilingual Practice', title_hi: 'फल — द्विभाषी अभ्यास',
    categories: ['fruits'], count: 8, teacher: '', school: 'Government Primary School',
  })
  const [html, setHtml] = useState('')
  const [busy, setBusy] = useState(false)
  const frame = useRef(null)

  const set = (k, v) => setSpec((s) => ({ ...s, [k]: v }))

  async function generate() {
    setBusy(true)
    try {
      const h = await api.worksheet(spec)
      setHtml(h)
      notify('✅ worksheet ready')
    } catch (e) {
      notify(`${t('error')}: ${e.message}`)
    } finally { setBusy(false) }
  }

  useEffect(() => { generate() }, [])

  function print() {
    const w = frame.current?.contentWindow
    if (w) { w.focus(); w.print() }
  }

  function openTab() {
    const blob = new Blob([html], { type: 'text/html' })
    window.open(URL.createObjectURL(blob), '_blank')
  }

  return (
    <div className="grid g2">
      <div className="card card-pad">
        <span className="label">{t('template')}</span>
        <div className="chipbar" style={{ marginBottom: 16 }}>
          {TEMPLATES.map((tp) => (
            <button key={tp} className={`chip ${spec.template === tp ? 'active' : ''}`} onClick={() => set('template', tp)}>
              {t(`tpl_${tp}`)}
            </button>
          ))}
        </div>

        <span className="label">{t('category')}</span>
        <div className="chipbar" style={{ marginBottom: 16 }}>
          {CATS.map((c) => (
            <button key={c} className={`chip ${spec.categories.includes(c) ? 'active' : ''}`}
              onClick={() => set('categories', [c])}>
              {lang === 'hi' ? CATEGORY_HI[c] || c : c}
            </button>
          ))}
        </div>

        <div className="grid g2">
          <div>
            <span className="label">{t('titleEn')}</span>
            <input className="field" value={spec.title_en} onChange={(e) => set('title_en', e.target.value)} />
          </div>
          <div>
            <span className="label">{t('titleHi')}</span>
            <input className="field hi" value={spec.title_hi} onChange={(e) => set('title_hi', e.target.value)} />
          </div>
          <div>
            <span className="label">{t('teacherName')}</span>
            <input className="field" value={spec.teacher} onChange={(e) => set('teacher', e.target.value)} placeholder="—" />
          </div>
          <div>
            <span className="label">{t('schoolName')}</span>
            <input className="field" value={spec.school} onChange={(e) => set('school', e.target.value)} />
          </div>
          <div>
            <span className="label">{t('wordsCount')}</span>
            <input className="field" type="number" min={4} max={20} value={spec.count}
              onChange={(e) => set('count', Number(e.target.value))} />
          </div>
        </div>

        <div className="chipbar" style={{ marginTop: 18 }}>
          <button className="btn" onClick={generate} disabled={busy}>
            {busy ? <span className="spin" /> : '⚙️'} {busy ? t('generating') : t('generate')}
          </button>
          <button className="btn ghost" onClick={print} disabled={!html}>🖨️ {t('print')}</button>
          <button className="btn ghost" onClick={openTab} disabled={!html}>↗ {t('openTab')}</button>
        </div>
      </div>

      <div className="card card-pad">
        <span className="label">A4 · Hindi + Santhali (Ol Chiki)</span>
        <div className="frame-wrap">
          <iframe ref={frame} title="worksheet" srcDoc={html} />
        </div>
        <div className="small muted" style={{ marginTop: 10 }}>
          {t('worksheetsSub')} — {t('playHi')}: {spec.categories.join(', ')}
        </div>
      </div>
    </div>
  )
}
