import React, { useEffect, useMemo, useState } from 'react'
import { useI18n } from '../i18n.js'
import { api, speak } from '../api.js'

// हिन्दी → संताली शब्दकोश
// The nine English→Santhali files the school supplied, re-based to Hindi. Every row
// here is answerable by the translator, because each one carries a Hindi side.
const THEME_HI = {
  general: 'सामान्य', body: 'शरीर', family: 'परिवार', food: 'खाना-पानी',
  animals: 'जानवर', time: 'समय', nature: 'प्रकृति', school: 'विद्यालय',
  colours: 'रंग',
}

export default function Dictionary() {
  const { t, lang } = useI18n()
  const [items, setItems] = useState([])
  const [themes, setThemes] = useState({})
  const [sources, setSources] = useState({})
  const [files, setFiles] = useState(null)
  const [numbers, setNumbers] = useState([])
  const [q, setQ] = useState('')
  const [theme, setTheme] = useState('all')
  const [src, setSrc] = useState('all')
  const [tab, setTab] = useState('words')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      api.dictionary('all'),
      api.dictionaryFiles(),
      api.dictionaryNumbers(),
    ])
      .then(([d, f, n]) => {
        setItems(d.items || [])
        setThemes(d.themes || {})
        setSources(d.sources || {})
        setFiles(f)
        setNumbers(n.items || [])
      })
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  const shown = useMemo(() => {
    let s = items
    if (theme !== 'all') s = s.filter((e) => (e.theme || 'general') === theme)
    if (src !== 'all') s = s.filter((e) => (e.found_in || [e.source]).includes(src))
    if (q.trim()) {
      const n = q.trim().toLowerCase()
      s = s.filter(
        (e) =>
          (e.hi || '').includes(n) ||
          (e.en || '').toLowerCase().includes(n) ||
          (e.sat || '').includes(n) ||
          (e.sat_roman || '').toLowerCase().includes(n),
      )
    }
    return s
  }, [items, theme, src, q])

  const themeKeys = useMemo(() => ['all', ...Object.keys(themes)], [themes])
  const srcKeys = useMemo(() => ['all', ...Object.keys(sources)], [sources])

  return (
    <>
      <div className="page-head">
        <div>
          <h1 style={{ margin: 0, fontSize: 24 }}>{t('dict_title')}</h1>
          <p className="muted small" style={{ maxWidth: 720, marginTop: 6 }}>
            {t('dict_sub')}
          </p>
        </div>
      </div>

      <div className="chipbar" style={{ marginBottom: 12 }}>
        <button className={`chip ${tab === 'words' ? 'active' : ''}`} onClick={() => setTab('words')}>
          🔤 {t('dict_tab_words')} · {items.length}
        </button>
        <button className={`chip ${tab === 'numbers' ? 'active' : ''}`} onClick={() => setTab('numbers')}>
          🔢 {t('dict_tab_numbers')} · {numbers.length}
        </button>
        <button className={`chip ${tab === 'files' ? 'active' : ''}`} onClick={() => setTab('files')}>
          🗂️ {t('dict_tab_files')}
        </button>
      </div>

      {tab === 'words' && (
        <>
          <div className="chipbar" style={{ marginBottom: 10 }}>
            <input
              className="field"
              style={{ maxWidth: 330 }}
              placeholder={t('dict_search')}
              value={q}
              onChange={(e) => setQ(e.target.value)}
            />
          </div>
          <div className="chipbar" style={{ marginBottom: 10 }}>
            {themeKeys.map((c) => (
              <button key={c} className={`chip ${theme === c ? 'active' : ''}`} onClick={() => setTheme(c)}>
                {c === 'all' ? t('allCategories') : lang === 'hi' ? THEME_HI[c] || c : c}
                {c !== 'all' ? ` ${themes[c]}` : ''}
              </button>
            ))}
          </div>
          <div className="chipbar" style={{ marginBottom: 14 }}>
            {srcKeys.map((c) => (
              <button key={c} className={`chip ${src === c ? 'active' : ''}`} onClick={() => setSrc(c)}>
                {c === 'all' ? t('dict_allSources') : `${c} ${sources[c]}`}
              </button>
            ))}
          </div>

          {loading ? (
            <div className="card card-pad muted">{t('loading')}</div>
          ) : (
            <div className="card card-pad">
              <div className="small muted" style={{ marginBottom: 8 }}>
                {shown.length} / {items.length} {t('dict_words')}
              </div>
              <table className="simple">
                <thead>
                  <tr>
                    <th style={{ width: 40 }} />
                    <th>हिन्दी</th>
                    <th>{lang === 'hi' ? 'अंग्रेज़ी' : 'English'}</th>
                    <th>ᱥᱟᱱᱛᱟᱲᱤ</th>
                    <th>{t('dict_roman')}</th>
                    <th>{t('dict_theme')}</th>
                  </tr>
                </thead>
                <tbody>
                  {shown.slice(0, 400).map((e, i) => (
                    <tr key={`${e.hi}-${e.sat}-${i}`}>
                      <td>
                        <button className="icon-btn" title={t('speak')} onClick={() => speak(e.sat, 'sat')}>
                          🔊
                        </button>
                      </td>
                      <td style={{ fontWeight: 600 }}>{e.hi}</td>
                      <td className="muted">{e.en}</td>
                      <td className="sat-cell">{e.sat}</td>
                      <td className="muted">{e.sat_roman || '—'}</td>
                      <td>
                        <span className="pill">{lang === 'hi' ? THEME_HI[e.theme] || e.theme : e.theme}</span>
                        {e.confidence !== 'high' ? <span className="pill warn">?</span> : null}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {shown.length > 400 ? (
                <div className="small muted" style={{ marginTop: 8 }}>
                  {t('dict_showing400')}
                </div>
              ) : null}
            </div>
          )}

          <div className="card card-pad" style={{ marginTop: 14 }}>
            <h3 style={{ marginTop: 0, fontSize: 15 }}>{t('dict_precedence_t')}</h3>
            <p className="small muted" style={{ margin: 0 }}>{t('dict_precedence')}</p>
          </div>
        </>
      )}

      {tab === 'numbers' && (
        <div className="card card-pad">
          <p className="small muted" style={{ maxWidth: 700 }}>{t('dict_numbers_note')}</p>
          <div className="num-grid">
            {numbers.map((n) => (
              <button
                key={n.key}
                className="num-cell"
                title={n.hi}
                onClick={() => speak(n.sat, 'sat')}
              >
                <span className="num-hi">{n.hi}</span>
                <span className="num-digits">{n.key}</span>
                <span className="num-sat">{n.sat}</span>
                <span className="num-roman">{n.sat_roman || ''}</span>
              </button>
            ))}
          </div>
        </div>
      )}

      {tab === 'files' && files && (
        <>
          <div className="statrow" style={{ marginBottom: 14 }}>
            <div className="card card-pad stat">
              <div className="stat-num">{files.files_used}/{files.files_supplied}</div>
              <div className="muted small">{t('dict_files_used')}</div>
            </div>
            <div className="card card-pad stat">
              <div className="stat-num">{files.totals.dictionary_entries}</div>
              <div className="muted small">{t('dict_words')}</div>
            </div>
            <div className="card card-pad stat">
              <div className="stat-num">{files.totals.numbers}</div>
              <div className="muted small">{t('dict_tab_numbers')}</div>
            </div>
            <div className="card card-pad stat">
              <div className="stat-num">{files.totals.proper_names}</div>
              <div className="muted small">{t('dict_names')}</div>
            </div>
            <div className="card card-pad stat">
              <div className="stat-num">{files.totals.dictionary_sentences}</div>
              <div className="muted small">{t('dict_sentences')}</div>
            </div>
          </div>

          <div className="card card-pad">
            <h3 style={{ marginTop: 0, fontSize: 15 }}>{t('dict_files_t')}</h3>
            <table className="simple">
              <thead>
                <tr>
                  <th>{t('dict_file')}</th>
                  <th>{t('dict_rows')}</th>
                  <th>{t('dict_words')}</th>
                  <th>{t('dict_numbers_short')}</th>
                  <th>{t('dict_sentences')}</th>
                  <th>{t('dict_names')}</th>
                  <th>{t('dict_used_for')}</th>
                </tr>
              </thead>
              <tbody>
                {files.items.map((f) => (
                  <tr key={f.file}>
                    <td style={{ fontWeight: 600 }}>{f.file}</td>
                    <td>{f.records || '—'}</td>
                    <td>{f.in_dictionary}</td>
                    <td>{f.numbers || '—'}</td>
                    <td>{f.sentences || '—'}</td>
                    <td>{f.names || '—'}</td>
                    <td>
                      <span className="pill">{f.used_for}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="card card-pad" style={{ marginTop: 14 }}>
            <h3 style={{ marginTop: 0, fontSize: 15 }}>{t('dict_notes_t')}</h3>
            <ul className="small muted" style={{ margin: 0, paddingLeft: 18 }}>
              {files.notes.map((n, i) => (
                <li key={i} style={{ marginBottom: 6 }}>{n}</li>
              ))}
              <li>
                {Object.keys(files.skipped || {}).length} {t('dict_skipped_note')}
              </li>
            </ul>
          </div>
        </>
      )}
    </>
  )
}
