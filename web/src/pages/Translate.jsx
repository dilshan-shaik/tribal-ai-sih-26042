import React, { useEffect, useMemo, useRef, useState } from 'react'
import { useI18n } from '../i18n.js'
import { api, speak } from '../api.js'
import LanguageSelect from '../components/LanguageSelect.jsx'

// One shape for every target language: Santhali answers arrive in `sat`, Mundari and
// Ho in `target`. The screens should not care which.
function outOf(res) {
  if (!res) return null
  if (res.target) return res.target
  if (res.sat) return { text: res.sat.olchiki, script: 'Ol Chiki', roman: res.sat.roman,
                        devanagari: res.sat.devanagari, language: 'Santhali', code: 'sat' }
  return null
}
const codeOf = (res) => (res && (res.target_code || (res.sat ? 'sat' : 'sat'))) || 'sat'
import { voiceCapabilities } from '../store.js'

const EXAMPLES = [
  'किताब बंद करो।',
  'किताब खोलो।',
  'मेरा नाम रवि है।',
  'यह एक पेड़ है।',
  'फल कहाँ है?',
  'पानी पियो।',
  'मेरी मदद करो।',
  'आम',
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

// SpeechRecognition error -> i18n key (so the teacher learns *why* it stopped)
const SR_ERR = {
  'not-allowed': 'micBlocked',
  'service-not-allowed': 'micBlocked',
  'audio-capture': 'micMissing',
  network: 'micNetwork',
  'no-speech': 'micNoSpeech',
  aborted: 'micAborted',
}

export default function Translate({ notify }) {
  const { t } = useI18n()
  const [text, setText] = useState('')
  const [src] = useState('hi')                  // Hindi or English in
  const [target, setTarget] = useState('sat')   // Santhali | Mundari | Ho out
  const [res, setRes] = useState(null)
  const [busy, setBusy] = useState(false)
  const [history, setHistory] = useState([])

  // voice state
  const caps = useMemo(() => voiceCapabilities(), [])
  const [listening, setListening] = useState(false)
  const [recording, setRecording] = useState(false)
  const [asrBusy, setAsrBusy] = useState(false)
  const [asrReady, setAsrReady] = useState(null)   // null | true | false
  const [voiceErr, setVoiceErr] = useState(null)
  const [micTest, setMicTest] = useState(null)
  const [showHelp, setShowHelp] = useState(false)

  const recRef = useRef(null)        // SpeechRecognition
  const mediaRef = useRef(null)      // MediaRecorder
  const chunksRef = useRef([])
  const streamRef = useRef(null)
  const textRef = useRef('')
  textRef.current = text

  // ---- is the server-side (record -> transcribe) path usable? --------------
  useEffect(() => {
    api.asrStatus().then((s) => setAsrReady(!!s.package_available)).catch(() => setAsrReady(false))
  }, [])

  // ---- live dictation via Web Speech API (Chrome / Edge) -------------------
  useEffect(() => {
    if (!caps.SR) return
    const rec = new caps.SR()
    rec.lang = 'hi-IN'
    rec.interimResults = true
    rec.continuous = false
    rec.maxAlternatives = 1
    rec.onresult = (e) => {
      const txt = Array.from(e.results).map((r) => r[0].transcript).join(' ')
      setText(txt)
      if (e.results[e.results.length - 1].isFinal) run(txt)
    }
    rec.onerror = (e) => {
      setListening(false)
      setVoiceErr(SR_ERR[e.error] || 'micUnknown')
    }
    rec.onend = () => setListening(false)
    recRef.current = rec
    return () => { try { rec.stop() } catch { /* noop */ } }
  }, [caps.SR])

  useEffect(() => {
  }, [])

  async function run(value) {
    const q = (value ?? textRef.current).trim()
    if (!q) return
    setBusy(true)
    try {
      const r = await api.translate(q, src, target)
      setRes(r)
      setHistory((h) => [{ q, r }, ...h.filter((x) => x.q !== q)].slice(0, 6))
      const o = outOf(r)
      // students hear it immediately - but only where a voice actually exists
      if (o && r.tts?.available !== false) speak(o.text, codeOf(r))
    } catch (e) {
      notify(`${t('error')}: ${e.message}`)
    } finally {
      setBusy(false)
    }
  }

  // ---- path A: browser dictation -------------------------------------------
  function toggleMic() {
    setVoiceErr(null)
    if (!recRef.current) { setVoiceErr('micUnsupported'); return }
    if (listening) { try { recRef.current.stop() } catch { /* noop */ } setListening(false); return }
    try {
      setText('')
      setRes(null)
      recRef.current.start()
      setListening(true)
    } catch (e) {
      setListening(false)
      setVoiceErr(e.name === 'NotAllowedError' ? 'micBlocked' : 'micUnknown')
    }
  }

  // ---- path B: record -> POST /api/asr (works in Firefox/Safari too) -------
  async function toggleRecord() {
    setVoiceErr(null)
    if (!caps.getUserMedia) { setVoiceErr('micUnsupported'); return }
    if (recording) { mediaRef.current?.stop(); return }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      streamRef.current = stream
      chunksRef.current = []
      const mime = MediaRecorder.isTypeSupported('audio/webm') ? 'audio/webm' : ''
      const mr = new MediaRecorder(stream, mime ? { mimeType: mime } : undefined)
      mr.ondataavailable = (e) => e.data.size && chunksRef.current.push(e.data)
      mr.onstop = async () => {
        setRecording(false)
        streamRef.current?.getTracks().forEach((tr) => tr.stop())
        const blob = new Blob(chunksRef.current, { type: 'audio/webm' })
        if (!blob.size) { setVoiceErr('micNoSpeech'); return }
        setAsrBusy(true)
        try {
          const out = await api.asr(blob)
          if (out.text) { setText(out.text); run(out.text) }
          else setVoiceErr('micNoSpeech')
        } catch (e) {
          setVoiceErr('asrFailed')
          notify(`${t('error')}: ${e.message}`)
        } finally { setAsrBusy(false) }
      }
      mr.start()
      mediaRef.current = mr
      setRecording(true)
    } catch (e) {
      setRecording(false)
      setVoiceErr(e.name === 'NotAllowedError' ? 'micBlocked'
        : e.name === 'NotFoundError' ? 'micMissing' : 'micUnknown')
    }
  }

  // ---- microphone self-test (definitive answer about this environment) -----
  async function testMic() {
    if (!caps.getUserMedia) { setMicTest('fail:Unsupported'); setVoiceErr('micUnsupported'); return }
    setMicTest('testing')
    try {
      const st = await navigator.mediaDevices.getUserMedia({ audio: true })
      st.getTracks().forEach((tr) => tr.stop())
      setMicTest('ok')
      setVoiceErr(null)
    } catch (e) {
      setMicTest(`fail:${e.name}`)
      setVoiceErr(e.name === 'NotAllowedError' ? 'micBlocked'
        : e.name === 'NotFoundError' ? 'micMissing' : 'micUnknown')
    }
  }

  const canDictate = caps.speechRecognition && caps.secure
  const canRecord = caps.mediaRecorder && caps.getUserMedia && asrReady
  const micBroken = (micTest && micTest !== 'ok' && micTest !== 'testing') || !!voiceErr

  function sendValidation() {
    if (!res) return
    api.validate({
      scope: res.method === 'vocab' ? 'vocab' : 'phrase',
      hindi: res.hindi_gloss || text,
      sat: res.sat?.olchiki || '',
      note: 'flagged from translator', teacher: '',
    })
    notify(t('sentToValidation'))
  }

  const errText = {
    micBlocked: t('micBlocked'),
    micUnsupported: t('micUnsupported'),
    micMissing: t('micMissingMsg'),
    micNetwork: t('micNetworkMsg'),
    micNoSpeech: t('micNoSpeechMsg'),
    micAborted: t('micAbortedMsg'),
    micUnknown: t('micUnknownMsg'),
    asrFailed: t('asrFailedMsg'),
  }

  function addWord(w) {
    setText((v) => (v ? `${v.replace(/\s+$/, '')} ${w}` : w))
    setRes(null)
  }

  return (
    <div className="grid g2">
      <div>
        {/* ------------------------------------------------ voice status box */}
        {(micBroken || !canDictate) && (
          <div className="card card-pad" style={{
            marginBottom: 14, borderColor: '#f6d5a8', background: 'linear-gradient(180deg,#fffaf2,#fff)',
          }}>
            <div style={{ display: 'flex', gap: 10, alignItems: 'flex-start' }}>
              <div style={{ fontSize: 24 }}>🎙️</div>
              <div className="grow">
                <div className="bold">{t('voiceNotAvailable')}</div>
                <div className="small muted" style={{ marginTop: 4, lineHeight: 1.55 }}>
                  {voiceErr ? errText[voiceErr] : t('voiceBlockedWhy')}
                </div>

                {micTest === 'ok' && (
                  <div className="small" style={{ marginTop: 6, color: '#0f7b46', fontWeight: 700 }}>
                    ✅ {t('micTestOk')}
                  </div>
                )}
                {micTest && micTest.startsWith('fail:') && (
                  <div className="small" style={{ marginTop: 6, color: '#a51f2f', fontWeight: 700 }}>
                    ❌ {t('micTestFail')} · {micTest.replace('fail:', '')}
                  </div>
                )}

                <div className="chipbar" style={{ marginTop: 12 }}>
                  <button className="btn small" onClick={() => window.open(location.href, '_blank', 'noopener')}>
                    🔗 {t('openNewTab')}
                  </button>
                  <button className="btn ghost small" onClick={testMic} disabled={micTest === 'testing'}>
                    {micTest === 'testing' ? <span className="spin" style={{ borderTopColor: '#333' }} /> : '🔍'} {t('testMic')}
                  </button>
                  <button className="btn ghost small" onClick={() => setShowHelp(!showHelp)}>
                    ⓘ {t('whyTitle')}
                  </button>
                </div>

                {showHelp && (
                  <div className="small muted" style={{ marginTop: 10, lineHeight: 1.7 }}>
                    <b>{t('whyTitle')}</b>
                    <ul style={{ margin: '6px 0 0', paddingLeft: 18 }}>
                      <li>{t('why1')}</li>
                      <li>{t('why2')}</li>
                      <li>{t('why3')}</li>
                      <li>{t('why4')}</li>
                    </ul>
                    <div style={{ marginTop: 6 }}>
                      {t('envDetected')}: SpeechRecognition = <b>{String(caps.speechRecognition)}</b>,
                      MediaRecorder = <b>{String(caps.mediaRecorder)}</b>,
                      secure context = <b>{String(caps.secure)}</b>,
                      embedded frame = <b>{String(caps.inFrame)}</b>,
                      server ASR = <b>{asrReady === null ? '…' : String(asrReady)}</b>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* ------------------------------------------------------------ input */}
        <div className="card card-pad">
          <LanguageSelect value={target} onChange={setTarget} />
          <span className="label">{t('inputLanguage')}</span>
          <div className="chipbar" style={{ marginBottom: 12 }}>
            <button className="chip active">{t('langHi')}</button>
          </div>
          <span className="label">{t('typeHindi')}</span>
          <textarea
            className="field hi"
            rows={4}
            value={text}
            placeholder={t('typeHindi')}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={(e) => { if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) run() }}
          />

          <div className="chipbar" style={{ marginTop: 12 }}>
            {canDictate && (
              <button className={`btn rec ${listening ? 'live' : ''}`} onClick={toggleMic}>
                {listening ? `⏹ ${t('micStop')}` : `🎙️ ${t('micStart')}`}
              </button>
            )}
            {canRecord && (
              <button className={`btn ${recording ? 'rec live' : 'ghost'}`} onClick={toggleRecord} disabled={asrBusy}>
                {asrBusy ? <span className="spin" style={{ borderTopColor: '#333' }} />
                  : recording ? '⏹' : '⏺'}{' '}
                {asrBusy ? t('transcribing') : recording ? t('recordingStop') : t('recordBtn')}
              </button>
            )}
            <button className="btn" onClick={() => run()} disabled={busy || !text.trim()}>
              {busy ? <span className="spin" /> : '➜'} {t('translateBtn')}
            </button>
            <button className="btn ghost" onClick={() => { setText(''); setRes(null); setVoiceErr(null) }}>
              {t('clear')}
            </button>
          </div>

          {/* ------------------------------------------- tap-to-speak board */}
          <div className="label" style={{ marginTop: 18 }}>{t('tapSpeak')}</div>
          <div className="small muted" style={{ marginBottom: 8 }}>{t('tapSpeakHint')}</div>
          <TapBoard onPick={addWord} onRun={(v) => { setText(v); run(v) }} />
        </div>

        {/* --------------------------------------------------------- history */}
        {history.length > 0 && (
          <div className="card card-pad" style={{ marginTop: 14 }}>
            <div className="label">{t('todaysPlan')} · latest</div>
            {history.map((h) => (
              <div key={h.q} className="wordrow" style={{ marginBottom: 8 }}>
                <div className="grow">
                  <div className="hi">{h.q}</div>
                  <div className="ol" style={{ fontSize: 17, color: 'var(--indigo)' }}>
                    {(outOf(h.r) || {}).text || h.r.combined || '—'}
                  </div>
                </div>
                <span className={`badge ${h.r.confidence}`}>{t(h.r.confidence)}</span>
                {outOf(h.r) && <button className="speaker" onClick={() => speak(outOf(h.r).text, codeOf(h.r))}>🔊</button>}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* ------------------------------------------------------------ output */}
      <div>
        {!res && (
          <div className="card card-pad empty">
            <div style={{ fontSize: 44 }}>🗣️</div>
            <div className="bold" style={{ marginTop: 8 }}>{t('translateSub')}</div>
            <div className="label" style={{ marginTop: 20 }}>{t('examples')}</div>
            <div className="chipbar" style={{ justifyContent: 'center' }}>
              {EXAMPLES.map((e) => (
                <button key={e} className="chip hi" onClick={() => { setText(e); run(e) }}>{e}</button>
              ))}
            </div>
          </div>
        )}

        {res && (
          <>
            <div className="card card-pad">
              <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center', marginBottom: 10 }}>
                <span className={`badge ${res.confidence}`}>{t('confidence')}: {t(res.confidence)}</span>
                {res.verified && <span className="badge verified">✓ {t('verifiedBadge')}</span>}
                {res.kind === 'attested' && <span className="badge attested">corpus-attested</span>}
                {res.synthetic && <span className="badge medium">🧪 {t('synthBadge')}</span>}
                {res.needs_validation && <span className="badge medium">⚠ {t('needsValidation')}</span>}
                <span className="small muted">{t(METHOD_KEY[res.method] || res.method)}</span>
              </div>

              {outOf(res) ? (
                <>
                  <div className="label">
                    {outOf(res).language} · {outOf(res).script}
                    {res.tts?.available === false ? ` · ${t('ttsNone')}` : ''}
                  </div>
                  <div className="ol big-sat">{outOf(res).text}</div>
                  {outOf(res).devanagari ? (
                    <>
                      <div className="small muted" style={{ marginTop: 10 }}>{t('devanagariOut')}</div>
                      <div className="hi" style={{ fontSize: 17 }}>{outOf(res).devanagari}</div>
                    </>
                  ) : null}
                  {outOf(res).roman ? (
                    <>
                      <div className="small muted" style={{ marginTop: 8 }}>{t('romanOut')}</div>
                      <div className="mono" style={{ fontSize: 14, letterSpacing: 0.5 }}>{outOf(res).roman}</div>
                    </>
                  ) : null}
                  <div className="chipbar" style={{ marginTop: 14 }}>
                    {res.tts?.available !== false ? (
                      <>
                        <button className="btn" onClick={() => speak(outOf(res).text, codeOf(res))}>🔊 {t('playSat')}</button>
                        <button className="btn ghost" onClick={() => speak(outOf(res).text, codeOf(res), { slow: true })}>🐢 {t('playSlow')}</button>
                      </>
                    ) : (
                      <span className="small muted">🔇 {t('ttsUnavailable')}</span>
                    )}
                    <button className="btn ghost" onClick={() => speak(res.hindi_gloss || text, 'hi')}>🔉 {t('playHi')}</button>
                  </div>
                </>
              ) : (
                <div>
                  {/* No confident sentence: give the combination of known words, in order,
                      instead of a guess. A wrong sentence cannot be un-read. */}
                  <div className="combo-head">
                    <span className="badge low">🧩 {t('comboBadge')}</span>
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
                      <div className="chipbar" style={{ marginTop: 12 }}>
                        {res.tts?.available !== false ? (
                          <>
                            <button className="btn" onClick={() => speak(res.combined, codeOf(res))}>
                              🔊 {t('playSat')}
                            </button>
                            <button className="btn ghost" onClick={() => speak(res.combined, codeOf(res), { slow: true })}>
                              🐢 {t('playSlow')}
                            </button>
                          </>
                        ) : (
                          <span className="small muted">🔇 {t('ttsUnavailable')}</span>
                        )}
                      </div>
                    </>
                  ) : (
                    <div className="bold" style={{ marginTop: 8 }}>{t('comboNothing')}</div>
                  )}
                  <div className="small muted" style={{ marginTop: 10 }}>{t('comboNote')}</div>
                  {res.words?.some((w) => w.phonetic) && (
                    <div className="xsmall muted" style={{ marginTop: 6 }}>⚠ {t('phoneticNote')}</div>
                  )}
                  {res.skipped?.length ? (
                    <div className="xsmall muted" style={{ marginTop: 6 }}>
                      {t('comboSkipped')}: {res.skipped.join(' · ')}
                    </div>
                  ) : null}
                </div>
              )}
            </div>

            {res.wordbank?.length > 0 && (
              <div className="card card-pad" style={{ marginTop: 14 }}>
                <div className="label">{t('wordbankTitle')}</div>
                <div className="grid g2">
                  {res.wordbank.map((w) => (
                    <div key={(w.tgt || w.sat) + (w.hindi || w.english || '')} className="wordrow"
                      onClick={() => speak(w.tgt || w.sat, codeOf(res))} role="button">
                      <div className="emoji">{w.emoji || '🔹'}</div>
                      <div className="grow">
                        <div className="hi bold">{w.hindi || w.english}</div>
                        <div className="ol" style={{ fontSize: 18, color: 'var(--indigo)' }}>{w.tgt || w.sat}</div>
                        <div className="xsmall muted">
                          {w.sat_roman || w.roman || ''}
                          {w.english ? ` · ${w.english}` : ''}
                          {w.chain ? ` · ${t('pivotNote')}: ${w.chain}` : ''}
                        </div>
                      </div>
                      <button className="speaker">🔊</button>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {(res.english_gloss || res.evidence) && (
              <div className="card card-pad" style={{ marginTop: 14 }}>
                <div className="label">{t('backGloss')}</div>
                {res.english_gloss && <div className="small"><span className="muted">EN:</span> {res.english_gloss}</div>}
                {res.hindi_gloss && <div className="small hi" style={{ marginTop: 4 }}><span className="muted">HI:</span> {res.hindi_gloss}</div>}
                {res.synthetic && (
                  <div className="small" style={{ marginTop: 8, color: '#92400e' }}>🧪 {t('synthNote')}</div>
                )}
                {res.evidence && (
                  <div className="small muted" style={{ marginTop: 8 }}>
                    <b>{t('evidence')}:</b> <span className="ol">{res.evidence}</span>
                  </div>
                )}
                {res.needs_validation && (
                  <button className="btn ghost small" style={{ marginTop: 12 }} onClick={sendValidation}>
                    ✅ {t('requestValidation')}
                  </button>
                )}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}

/* Tap-to-speak: build the Hindi instruction without a microphone.
   Comes straight from the verified phrase book + glossary, so every chip is a
   sentence the platform can translate with high confidence. */
function TapBoard({ onPick, onRun }) {
  const { t } = useI18n()
  const [phrases, setPhrases] = useState([])
  const [words, setWords] = useState([])

  useEffect(() => {
    api.phrases().then((d) => setPhrases(d.items.slice(0, 10))).catch(() => {})
    api.vocab('all').then((d) => setWords(d.items.filter((v) => v.sat).slice(0, 14))).catch(() => {})
  }, [])

  return (
    <>
      <div className="chipbar" style={{ marginBottom: 8 }}>
        {phrases.map((p) => (
          <button key={p.hindi} className="chip hi" title={p.english} onClick={() => onRun(p.hindi)}>
            {p.hindi}
          </button>
        ))}
      </div>
      <div className="chipbar">
        {words.map((w) => (
          <button key={w.hindi} className="chip" onClick={() => onPick(w.hindi)} title={`${w.english} → ${w.sat}`}>
            {w.emoji} <span className="hi">{w.hindi}</span>
          </button>
        ))}
      </div>
      <div className="small muted" style={{ marginTop: 8 }}>{t('tapToAdd')} · {t('tapToRun')}</div>
    </>
  )
}
