// localStorage throws in sandboxed iframes (opaque origin) - never let that
// crash the app, the classroom tool must open anywhere.
export const store = {
  get(key, fallback = null) {
    try { return window.localStorage.getItem(key) ?? fallback } catch { return fallback }
  },
  set(key, value) {
    try { window.localStorage.setItem(key, value) } catch { /* ignore */ }
  },
}

// Capability probe for voice input, so the UI can explain *why* it is missing
// instead of silently doing nothing.
export function voiceCapabilities() {
  const inFrame = (() => { try { return window.self !== window.top } catch { return true } })()
  const secure = window.isSecureContext !== false
  const SR = typeof window !== 'undefined'
    ? (window.SpeechRecognition || window.webkitSpeechRecognition) : null
  const mediaRecorder = typeof window !== 'undefined' && 'MediaRecorder' in window
  const getUserMedia = !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia)
  return {
    inFrame,
    secure,
    speechRecognition: !!SR,
    SR,
    mediaRecorder,
    getUserMedia,
    anyVoice: !!SR || (mediaRecorder && getUserMedia),
  }
}
