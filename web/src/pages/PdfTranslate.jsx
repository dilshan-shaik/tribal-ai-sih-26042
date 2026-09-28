import React, { useRef, useState } from 'react'
import { useI18n } from '../i18n.js'
import { api } from '../api.js'
import LanguageSelect from '../components/LanguageSelect.jsx'

// PDF → Santhali. A teacher drops in a textbook page (Hindi or English), gets a
// bilingual page back, and prints it. Nothing is invented: every paragraph says which
// method produced it, and anything we could only do word-by-word is shown as such.
const METHOD_LABEL = {
  phrase: 'mPhrase', vocab: 'mVocab', dictionary: 'mDictionary', number: 'mNumber',
  'en-memory': 'mEnMemory', 'en-lexicon': 'mEnLexicon',
  template: 'mTemplate', wikidata: 'mWikidata', 'already-santhali': 'mAlready',
  'words-only': 'mWordsOnly',
}

export default function PdfTranslate({ notify }) {
  const { t } = useI18n()
  const fileRef = useRef(null)
  const frameRef = useRef(null)
  const [busy, setBusy] = useState(false)
  const [doc, setDoc] = useState(null)
  const [err, setErr] = useState(null)
  const [pages, setPages] = useState(5)
  const [target, setTarget] = useState('sat')
  const [teacher, setTeacher] = useState('')
  const [school, setSchool] = useState('')
  const [drag, setDrag] = useState(false)

  async function upload(file) {
    if (!file) return
    if (!/\.pdf$/i.test(file.name)) { setErr(t('pdfOnly')); return }
    setBusy(true); setErr(null); setDoc(null)
    try {
      setDoc(await api.pdfTranslate(file, pages, target))
    } catch (e) {
      setErr(String(e.message || e))
    } finally {
      setBusy(false)
    }
  }

  async function printDoc() {
    const html = await api.pdfReport(doc, teacher, school)
    if (frameRef.current) {
      frameRef.current.srcdoc = html
      setTimeout(() => {
        try { frameRef.current.contentWindow.focus(); frameRef.current.contentWindow.print() }
        catch { notify?.(t('pdfPrintBlocked')) }
      }, 400)
    }
  }

  async function downloadText() {
    try {
      const r = await api.pdfText(doc)
      const url = URL.createObjectURL(new Blob([r.text], { type: 'text/plain;charset=utf-8' }))
      const a = document.createElement('a')
      a.href = url; a.download = r.filename; a.click()
      URL.revokeObjectURL(url)
      notify?.(t('pdfSaved'))
    } catch { notify?.(t('error')) }
  }

  const st = doc?.stats || {}
  const cov = st.blocks ? Math.round((100 * (st.translated || 0)) / st.blocks) : 0

  return (
    <>
      <div className="card card-pad" style={{ marginBottom: 14 }}>
        <div className="label">{t('pdfPick')}</div>
        <div
          className={`dropzone ${drag ? 'over' : ''}`}
          onDragOver={(e) => { e.preventDefault(); setDrag(true) }}
          onDragLeave={() => setDrag(false)}
          onDrop={(e) => { e.preventDefault(); setDrag(false); upload(e.dataTransfer.files?.[0]) }}
          onClick={() => fileRef.current?.click()}
        >
          <div style={{ fontSize: 34 }}>📄</div>
          <div className="bold" style={{ marginTop: 6 }}>{t('pdfDrop')}</div>
          <div className="small muted">{t('pdfDropSub')}</div>
          <input ref={fileRef} type="file" accept="application/pdf,.pdf" hidden
            onChange={(e) => upload(e.target.files?.[0])} />
        </div>

        <div className="chipbar" style={{ marginTop: 12, alignItems: 'center' }}>
          <span className="small muted">{t('pdfPages')}</span>
          <LanguageSelect value={target} onChange={setTarget} compact />
          {[3, 5, 10].map((n) => (
            <button key={n} className={`chip ${pages === n ? 'active' : ''}`} onClick={() => setPages(n)}>{n}</button>
          ))}
          <input className="field" style={{ maxWidth: 180 }} placeholder={t('pdfTeacher')}
            value={teacher} onChange={(e) => setTeacher(e.target.value)} />
          <input className="field" style={{ maxWidth: 200 }} placeholder={t('pdfSchool')}
            value={school} onChange={(e) => setSchool(e.target.value)} />
          {doc && (
            <button className="btn ghost" onClick={() => { setDoc(null); setErr(null) }}>✕ {t('ttClear')}</button>
          )}
        </div>

        {busy && <div className="small muted" style={{ marginTop: 10 }}>⏳ {t('pdfWorking')}</div>}
        {err && <div className="small" style={{ marginTop: 10, color: '#b91c1c' }}>⚠ {err}</div>}
      </div>

      {doc && (
        <>
          <div className="statrow" style={{ marginBottom: 14 }}>
            <div className="card card-pad stat"><div className="stat-num">{st.blocks}</div>
              <div className="muted small">{t('pdfParagraphs')}</div></div>
            <div className="card card-pad stat"><div className="stat-num">{st.translated}</div>
              <div className="muted small">{t('pdfTranslated')}</div></div>
            <div className="card card-pad stat"><div className="stat-num">{st.words_only}</div>
              <div className="muted small">{t('pdfWordsOnly')}</div></div>
            <div className="card card-pad stat"><div className="stat-num">{cov}%</div>
              <div className="muted small">{t('pdfCoverage')}</div></div>
            <div className="card card-pad stat"><div className="stat-num">{doc.info.pages_read}</div>
              <div className="muted small">{t('pdfPagesRead')}</div></div>
          </div>

          {!doc.info.has_text_layer && (
            <div className="card card-pad" style={{ marginBottom: 14, borderColor: '#f59e0b' }}>
              ⚠ {t('pdfScanned')}
            </div>
          )}

          <div className="chipbar" style={{ marginBottom: 14 }}>
            <button className="btn" onClick={printDoc}>🖨️ {t('pdfPrint')}</button>
            <button className="btn ghost" onClick={downloadText}>⬇️ {t('pdfDownload')}</button>
            <span className="small muted" style={{ alignSelf: 'center' }}>{t('pdfPrintHint')}</span>
          </div>

          <div className="card card-pad">
            <table className="simple">
              <thead>
                <tr>
                  <th style={{ width: 34 }}>pg</th>
                  <th>{t('pdfOriginal')}</th>
                  <th>{t('pdfSanthali')}</th>
                </tr>
              </thead>
              <tbody>
                {doc.blocks.map((b, i) => (
                  <tr key={`${b.page}-${i}`}>
                    <td className="muted">{b.page}</td>
                    <td className="hi" style={{ fontSize: 13.5 }}>{b.src}</td>
                    <td>
                      {b.sat ? (
                        <>
                          <div className="ol" style={{ fontSize: 17 }}>{b.sat}</div>
                          {b.roman ? <div className="small muted">{b.roman}</div> : null}
                        </>
                      ) : (
                        <>
                          <div className="small muted">
                            {t('pdfWordsOnlyNote')} — {Math.round((b.coverage || 0) * 100)}%
                          </div>
                          <div className="small" style={{ marginTop: 4 }}>
                            {b.words.map((w) => (
                              <span key={w.word + w.sat} className="chip" style={{ marginRight: 4 }}>
                                {w.word} = <span className="ol">{w.sat}</span>
                                {w.check ? ' ?' : ''}
                              </span>
                            ))}
                          </div>
                        </>
                      )}
                      <div className="badge" style={{ marginTop: 6 }}>
                        {t(METHOD_LABEL[b.method] || b.method)}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="card card-pad" style={{ marginTop: 14 }}>
            <p className="small muted" style={{ margin: 0 }}>{t('pdfHonest')}</p>
          </div>
        </>
      )}

      {!doc && !busy && (
        <div className="card card-pad">
          <p className="small muted" style={{ margin: 0 }}>{t('pdfHow')}</p>
        </div>
      )}

      {/* the printable bilingual page is rendered here and handed to the printer */}
      <iframe ref={frameRef} title="pdf-report" style={{ width: '100%', height: 0, border: 0 }} />
    </>
  )
}
