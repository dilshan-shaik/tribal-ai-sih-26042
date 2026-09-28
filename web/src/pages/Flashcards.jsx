import React, { useEffect, useState } from 'react'
import { useI18n, CATEGORY_HI } from '../i18n.js'
import { api, speak } from '../api.js'

const CATS = ['all', 'numbers', 'fruits', 'animals', 'birds', 'colours', 'body', 'family', 'school', 'food', 'nature', 'actions']

export default function Flashcards({ notify }) {
  const { t, lang } = useI18n()
  const [cat, setCat] = useState('fruits')
  const [cards, setCards] = useState([])
  const [i, setI] = useState(0)
  const [flip, setFlip] = useState(false)
  const [quiz, setQuiz] = useState(null)
  const [score, setScore] = useState({ right: 0, total: 0 })
  const [answered, setAnswered] = useState({})

  const load = (c = cat) => {
    api.flashcards(c, 12).then((d) => { setCards(d.cards); setI(0); setFlip(false) }).catch(() => {})
    api.quiz(c, 4).then(setQuiz).catch(() => setQuiz(null)); setAnswered({}); setScore({ right: 0, total: 0 })
  }
  useEffect(() => { load(cat) }, [cat])

  const card = cards[i]

  const step = (d) => {
    if (!cards.length) return
    const n = (i + d + cards.length) % cards.length
    setI(n); setFlip(false)
  }

  return (
    <>
      <div className="chipbar" style={{ marginBottom: 16 }}>
        {CATS.map((c) => (
          <button key={c} className={`chip ${cat === c ? 'active' : ''}`} onClick={() => setCat(c)}>
            {c === 'all' ? t('allCategories') : (lang === 'hi' ? CATEGORY_HI[c] || c : c)}
          </button>
        ))}
      </div>

      <div className="deck">
        <button className="btn ghost" onClick={() => step(-1)}>◀</button>

        {card && (
          <div className={`flipcard ${flip ? 'flipped' : ''}`} onClick={() => { setFlip(!flip); if (!flip) speak(card.sat, 'sat') }}>
            <div className="flipinner">
              <div className="face front">
                <div className="emoji">{card.emoji}</div>
                <div className="hi" style={{ fontSize: 34, fontWeight: 700, marginTop: 10 }}>{card.hindi}</div>
                <div className="small muted" style={{ marginTop: 6 }}>{card.english}</div>
                <div className="xsmall muted" style={{ marginTop: 14 }}>{t('flip')} ↻ · {i + 1}/{cards.length}</div>
              </div>
              <div className="face back">
                <div className="ol" style={{ fontSize: 44, color: 'var(--indigo)', fontWeight: 600 }}>{card.sat}</div>
                <div className="hi muted" style={{ marginTop: 10, fontSize: 16 }}>{card.sat_deva}</div>
                <div className="mono small" style={{ marginTop: 4, letterSpacing: 1 }}>{card.sat_roman}</div>
                <div style={{ display: 'flex', gap: 8, marginTop: 16 }}>
                  <span className={`badge ${card.confidence}`}>{t(card.confidence)}</span>
                  {card.verified && <span className="badge verified">✓ {t('verifiedBadge')}</span>}
                </div>
              </div>
            </div>
          </div>
        )}

        <button className="btn ghost" onClick={() => step(1)}>▶</button>
      </div>

      <div className="chipbar" style={{ justifyContent: 'center', marginTop: 16 }}>
        <button className="btn" onClick={() => card && speak(card.sat, 'sat')}>🔊 {t('playSat')}</button>
        <button className="btn ghost" onClick={() => card && speak(card.sat, 'sat', { slow: true })}>🐢 {t('playSlow')}</button>
        <button className="btn ghost" onClick={() => { setCards((c) => [...c].sort(() => Math.random() - 0.5)); setI(0); setFlip(false) }}>
          🔀 {t('shuffle')}
        </button>
      </div>

      {quiz && quiz.questions?.length > 0 && (
        <div className="card card-pad" style={{ marginTop: 22 }}>
          <div className="label">{t('quizTitle')} · {t('score')}: {score.right}/{score.total}</div>
          <div className="grid g2">
            {quiz.questions.map((q, qi) => (
              <div key={qi} className="card card-pad" style={{ boxShadow: 'none', background: '#fbfcff' }}>
                <div className="ol" style={{ fontSize: 26, color: 'var(--indigo)' }}>{q.prompt_sat}</div>
                <div className="xsmall muted" style={{ marginBottom: 10 }}>{q.prompt_roman} · <button className="speaker" style={{ width: 26, height: 26, fontSize: 12 }} onClick={() => speak(q.audio_text, 'sat')}>🔊</button></div>
                <div className="chipbar">
                  {q.options.map((o, oi) => (
                    <button key={oi} className="chip"
                      onClick={(e) => {
                        if (answered[qi]) return
                        const ok = o.correct
                        e.currentTarget.style.background = ok ? '#e8f8ee' : '#fdeaea'
                        e.currentTarget.style.borderColor = ok ? '#bfe9d2' : '#f6c9c9'
                        setAnswered((a) => ({ ...a, [qi]: true }))
                        setScore((s) => ({ right: s.right + (ok ? 1 : 0), total: s.total + 1 }))
                        notify(ok ? `✅ ${t('correct')}` : `❌ ${t('tryAgain')}`)
                      }}>
                      <span style={{ fontSize: 18 }}>{o.emoji}</span> <span className="hi">{o.hindi}</span>
                    </button>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </>
  )
}
