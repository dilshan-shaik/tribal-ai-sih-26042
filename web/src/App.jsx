import React, { createContext, useContext, useEffect, useMemo, useState } from 'react'
import { I18nProvider, useI18n } from './i18n.js'
import { api } from './api.js'
import Dashboard from './pages/Dashboard.jsx'
import Translate from './pages/Translate.jsx'
import TextTranslate from './pages/TextTranslate.jsx'
import PdfTranslate from './pages/PdfTranslate.jsx'
import Lessons from './pages/Lessons.jsx'
import Flashcards from './pages/Flashcards.jsx'
import Worksheets from './pages/Worksheets.jsx'
import Vocabulary from './pages/Vocabulary.jsx'
import Dictionary from './pages/Dictionary.jsx'
import Validation from './pages/Validation.jsx'
import OfflinePage from './pages/Offline.jsx'
import About from './pages/About.jsx'

// which build this page was made from - shown in the sidebar so nobody has to guess
const BUILD = (() => {
  try {
    const tag = document.querySelector('script[type="module"][src*="/assets/index-"]')
    const m = tag && tag.getAttribute('src').match(/index-([A-Za-z0-9_-]+)\.js/)
    return m ? m[1] : 'dev'
  } catch { return 'dev' }
})()

const ToastCtx = createContext(() => {})
export const useToast = () => useContext(ToastCtx)

// nav ids, icon, full label key, short label (used in the mobile strip)
const NAV = [
  ['dashboard', '🏠', 'nav_dashboard', 'short_dashboard'],
  ['translate', '🎙️', 'nav_translate', 'short_translate'],
  ['text', '⌨️', 'nav_text', 'short_text'],
  ['pdf', '📄', 'nav_pdf', 'short_pdf'],
  ['lessons', '📚', 'nav_lessons', 'short_lessons'],
  ['flashcards', '🃏', 'nav_flashcards', 'short_flashcards'],
  ['worksheets', '🖨️', 'nav_worksheets', 'short_worksheets'],
  ['vocab', '🔤', 'nav_vocab', 'short_vocab'],
  ['dictionary', '📖', 'nav_dictionary', 'short_dictionary'],
  ['validate', '✅', 'nav_validate', 'short_validate'],
  ['offline', '📶', 'nav_offline', 'short_offline'],
  ['about', '🌏', 'nav_about', 'short_about'],
]

function Shell() {
  const { t, lang, setLang } = useI18n()
  const [page, setPage] = useState('dashboard')
  const [health, setHealth] = useState(null)
  const [online, setOnline] = useState(navigator.onLine)
  const [toast, setToast] = useState(null)

  const notify = useMemo(
    () => (msg) => {
      setToast(msg)
      setTimeout(() => setToast(null), 2600)
    },
    [],
  )

  useEffect(() => {
    api.health().then(setHealth).catch(() => setHealth(null))
    const on = () => setOnline(true)
    const off = () => setOnline(false)
    window.addEventListener('online', on)
    window.addEventListener('offline', off)
    return () => {
      window.removeEventListener('online', on)
      window.removeEventListener('offline', off)
    }
  }, [])

  const go = (p) => {
    setPage(p)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  const pageProps = { go, health, notify }
  const title = {
    dashboard: [t('nav_dashboard'), t('welcomeSub')],
    translate: [t('translateTitle'), t('translateSub')],
    text: [t('textTitle'), t('textSub')],
    pdf: [t('pdfTitle'), t('pdfSub')],
    lessons: [t('lessonsTitle'), t('lessonsSub')],
    flashcards: [t('flashcardsTitle'), t('flashcardsSub')],
    worksheets: [t('worksheetsTitle'), t('worksheetsSub')],
    vocab: [t('vocabTitle'), t('vocabSub')],
    dictionary: [t('dict_title'), t('dict_tab_hint')],
    validate: [t('validateTitle'), t('validateSub')],
    offline: [t('offlineTitle'), t('offlineSub')],
    about: [t('aboutTitle'), t('aboutSub')],
  }[page]

  return (
    <ToastCtx.Provider value={notify}>
      <div className="app">
        <aside className="sidebar">
          <div className="brand">
            <div className="brand-logo">🪶</div>
            <div>
              <div className="brand-name">{t('appName')}</div>
              <div className="brand-sub">{t('appTag')}</div>
            </div>
          </div>
          <nav className="nav">
            {NAV.map(([id, ico, key, short]) => (
              <button
                key={id}
                className={`nav-item ${page === id ? 'active' : ''}`}
                onClick={() => go(id)}
                title={t(key)}
              >
                <span className="ico">{ico}</span>
                <span className="lbl">{t(key)}</span>
                <span className="lbl-short">{t(short)}</span>
              </button>
            ))}
          </nav>
          <div className="sidebar-foot">
            <div>SIH 26042 · Hindi → Santhali (Ol Chiki)</div>
            <div style={{ marginTop: 4, opacity: 0.75 }}>
              {health ? `${health.counts.vocab} words · ${health.counts.phrases} phrases · ${health.counts.dictionary_entries} dictionary · ${health.counts.dictionary_numbers} numbers` : '…'}
            </div>
            <div style={{ marginTop: 4, opacity: 0.6, fontSize: 10 }}>
              {t('build')}: {BUILD} · {health?.counts?.dictionary_sentences ?? '–'} {t('dict_sentences')}
            </div>
          </div>
        </aside>

        <main className="main">
          <header className="topbar">
            <div>
              <h1>{title[0]}</h1>
              <div className="sub">{title[1]}</div>
            </div>
            <div className="spacer" />
            <span className={`pill ${online ? 'on' : 'off'}`}>
              <span>{online ? '●' : '○'}</span>
              {online ? t('online') : t('offline')}
            </span>
            <div className="lang-toggle" role="group" aria-label="UI language">
              <button className={lang === 'en' ? 'active' : ''} onClick={() => setLang('en')}>English</button>
              <button className={lang === 'hi' ? 'active' : ''} onClick={() => setLang('hi')}>{t('langLabel')}</button>
            </div>
            {/* quick language switch: English UI <-> Hindi UI (user request) */}
          </header>

          <div className="content">
            {page === 'dashboard' && <Dashboard {...pageProps} />}
            {page === 'translate' && <Translate {...pageProps} />}
            {page === 'text' && <TextTranslate {...pageProps} />}
            {page === 'pdf' && <PdfTranslate {...pageProps} />}
            {page === 'lessons' && <Lessons {...pageProps} />}
            {page === 'flashcards' && <Flashcards {...pageProps} />}
            {page === 'worksheets' && <Worksheets {...pageProps} />}
            {page === 'vocab' && <Vocabulary {...pageProps} />}
            {page === 'dictionary' && <Dictionary {...pageProps} />}
            {page === 'validate' && <Validation {...pageProps} />}
            {page === 'offline' && <OfflinePage {...pageProps} />}
            {page === 'about' && <About {...pageProps} />}
          </div>
        </main>
      </div>
      {toast && <div className="toast">{toast}</div>}
    </ToastCtx.Provider>
  )
}

export default function App() {
  return (
    <I18nProvider>
      <Shell />
    </I18nProvider>
  )
}
