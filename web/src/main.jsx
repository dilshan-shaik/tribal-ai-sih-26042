import React from 'react'
import { createRoot } from 'react-dom/client'
import App from './App.jsx'
import './styles.css'

createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)

// ----------------------------------------------------------------------------
// Offline-first, but never stale.
//
// The classroom tool has to open with no internet (PS section 7 & 19), so the app is
// backed by a service worker. The first version of that worker was cache-first for the
// page itself, which meant a browser that had opened the app once kept showing that
// same old build no matter what the server said - new screens never appeared. The
// worker is network-first now, and this code makes the swap invisible:
//
//   * the browser is told never to trust its HTTP cache for the worker script
//   * when a new worker installs it is activated immediately
//   * the moment it takes control the page reloads once, so the teacher sees the
//     new build without knowing any of this happened
// ----------------------------------------------------------------------------
if ('serviceWorker' in navigator && location.protocol.startsWith('http')) {
  let reloading = false
  navigator.serviceWorker.addEventListener('controllerchange', () => {
    if (reloading) return
    reloading = true
    // a fresh worker is in charge: one reload shows the current build
    if (!sessionStorage.getItem('mtb-sw-reloaded')) {
      sessionStorage.setItem('mtb-sw-reloaded', '1')
      window.location.reload()
    }
  })

  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js', { updateViaCache: 'none' }).then((reg) => {
      // ask for an update check on every load, not once a day
      reg.update().catch(() => {})
      reg.addEventListener('updatefound', () => {
        const sw = reg.installing
        if (!sw) return
        sw.addEventListener('statechange', () => {
          if (sw.state === 'installed' && navigator.serviceWorker.controller) {
            sw.postMessage({ type: 'SKIP_WAITING' })
          }
        })
      })
    }).catch(() => {})
  })
}
