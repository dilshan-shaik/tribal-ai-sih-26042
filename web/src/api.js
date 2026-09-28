// Relative URLs only - the API is served by the same origin as the app, which
// also makes the whole thing work behind the preview proxy and offline.

async function j(url, opts) {
  const r = await fetch(url, opts)
  if (!r.ok) throw new Error(`${r.status} ${r.statusText}`)
  return r.json()
}

export const api = {
  health: () => j('/api/health'),
  summary: () => j('/api/pack/summary'),
  stats: () => j('/api/stats'),
  vocab: (category = 'all', q = '') =>
    j(`/api/vocab?category=${encodeURIComponent(category)}&q=${encodeURIComponent(q)}`),
  phrases: () => j('/api/phrases'),
  dictionary: (theme = 'all', q = '', source = 'all') =>
    j(`/api/dictionary?theme=${encodeURIComponent(theme)}&q=${encodeURIComponent(q)}&source=${encodeURIComponent(source)}&limit=0`),
  dictionaryFiles: () => j('/api/dictionary/files'),
  dictionaryNumbers: () => j('/api/dictionary/numbers'),
  verbs: () => j('/api/verbs'),
  lessons: () => j('/api/lessons'),
  flashcards: (category = 'all', count = 12) =>
    j(`/api/flashcards?category=${encodeURIComponent(category)}&count=${count}`),
  quiz: (category = 'all', count = 5) =>
    j(`/api/quiz?category=${encodeURIComponent(category)}&count=${count}`),
  pdfTranslate: async (file, maxPages = 5, target = 'sat') => {
    const fd = new FormData()
    fd.append('file', file)
    const r = await fetch(`/api/pdf/translate?max_pages=${maxPages}&target=${encodeURIComponent(target)}`, { method: 'POST', body: fd })
    if (!r.ok) {
      let detail = `${r.status} ${r.statusText}`
      try { detail = (await r.json()).detail || detail } catch { /* keep the status */ }
      throw new Error(detail)
    }
    return r.json()
  },
  pdfReport: async (doc, teacher = '', school = '') => {
    const r = await fetch('/api/pdf/report', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ...doc, teacher, school }),
    })
    if (!r.ok) throw new Error(`${r.status}`)
    return r.text()
  },
  pdfText: (doc, teacher = '', school = '') =>
    j('/api/pdf/text', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ...doc, teacher, school }),
    }),
  languages: () => j('/api/languages'),
  translate: (text, source = 'hi', target = 'sat') =>
    j('/api/translate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text, target, source }),
    }),
  worksheet: (spec) =>
    fetch('/api/worksheet', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(spec),
    }).then((r) => r.text()),
  validate: (body) =>
    j('/api/validate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    }),
  validation: () => j('/api/validation'),
  seedQueue: () => j('/api/validation/seed', { method: 'POST' }),
  packUrl: '/api/pack/download',
  asrStatus: () => j('/api/asr/status'),
  // record -> transcribe (works in Firefox/Safari and wherever Web Speech API is missing)
  asr: async (blob) => {
    const fd = new FormData()
    fd.append('file', blob, 'clip.webm')
    const r = await fetch('/api/asr', { method: 'POST', body: fd })
    const body = await r.json().catch(() => ({}))
    if (!r.ok) throw new Error(body.detail || `ASR ${r.status}`)
    return body
  },
}

// --- audio helper: /api/tts returns an mp3, cached server-side and by the SW ---
const playing = new Set()

export function speak(text, lang = 'sat', { slow = false, onEnd } = {}) {
  if (!text) return null
  const key = `${lang}:${slow}:${text}`
  if (playing.has(key)) return null
  playing.add(key)
  const url = `/api/tts?text=${encodeURIComponent(text)}&lang=${lang}&slow=${slow}`
  const el = new Audio(url)
  let failed = false
  el.onended = el.onerror = () => {
    playing.delete(key)
    if (!failed) onEnd && onEnd()
  }
  el.play().catch(async () => {
    playing.delete(key)
    failed = true
    // 501 = this language has no voice model. Say so instead of playing silence.
    if (typeof window !== 'undefined') {
      try {
        const r = await fetch(url)
        const detail = (await r.json()).detail
        window.dispatchEvent(new CustomEvent('mtb-tts-unavailable', { detail }))
      } catch { /* nothing to add */ }
    }
    onEnd && onEnd()
  })
  return el
}

export function speakPost(text, lang = 'sat') {
  // POST variant (used when text may be long / contain special characters)
  fetch('/api/tts', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text, lang, slow: false }),
  })
    .then((r) => r.blob())
    .then((b) => new Audio(URL.createObjectURL(b)).play())
    .catch(() => {})
}
