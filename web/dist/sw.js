/* Offline-capable service worker for the MTB-MLE classroom tool.
 *
 * Changed in v3 after a real problem: the old worker was cache-first for the app shell,
 * so a browser that had visited once kept showing the old page for ever - new screens
 * ("Text -> Text", "PDF translation") simply never appeared. The app must stay usable
 * offline, but it must never lie about which version it is.
 *
 * Rules now:
 *   1. pages and API calls  -> network first, cache only as an offline fallback
 *   2. /assets/*            -> cache first (file names contain a content hash, so a
 *                              new build always has a new name)
 *   3. /api/tts             -> cache first (clips are content-addressed and slow to make)
 *   4. a new worker takes over immediately and the page reloads itself once
 */
const SHELL = 'mtb-shell-v3'
const AUDIO = 'mtb-audio-v1'
const PACK = 'mtb-pack-v1'
const KEEP = [SHELL, AUDIO, PACK]

self.addEventListener('install', (e) => {
  e.waitUntil(caches.open(SHELL).then(() => self.skipWaiting()))
})

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => !KEEP.includes(k)).map((k) => caches.delete(k))))
      .then(() => self.clients.claim()),
  )
})

self.addEventListener('message', (e) => {
  const cmd = e.data && e.data.type
  if (cmd === 'SKIP_WAITING') self.skipWaiting()
  if (cmd === 'CLEAR_CACHES') {
    e.waitUntil(caches.keys().then((keys) => Promise.all(keys.map((k) => caches.delete(k)))))
  }
})

async function networkFirst(request, cacheName) {
  try {
    const res = await fetch(request)
    if (res && res.ok && cacheName) {
      const copy = res.clone()
      caches.open(cacheName).then((c) => c.put(request, copy)).catch(() => {})
    }
    return res
  } catch (err) {
    const hit = await caches.match(request)
    if (hit) return hit
    if (request.mode === 'navigate') {
      const shell = await caches.match('/index.html')
      if (shell) return shell
    }
    return new Response(JSON.stringify({ offline: true }), {
      status: 503, headers: { 'Content-Type': 'application/json' },
    })
  }
}

async function cacheFirst(request, cacheName) {
  const hit = await caches.match(request)
  if (hit) return hit
  try {
    const res = await fetch(request)
    if (res && res.ok) {
      const copy = res.clone()
      caches.open(cacheName).then((c) => c.put(request, copy)).catch(() => {})
    }
    return res
  } catch (err) {
    return new Response('', { status: 504, statusText: 'unavailable offline' })
  }
}

self.addEventListener('fetch', (event) => {
  const { request } = event
  if (request.method !== 'GET') return
  const url = new URL(request.url)
  if (url.origin !== location.origin) return

  // audio clips: cache first, they are content-addressed and expensive to synthesise
  if (url.pathname.startsWith('/api/tts')) {
    event.respondWith(cacheFirst(request, AUDIO))
    return
  }

  // hashed build output: cache first, a new build always has a new name
  if (url.pathname.startsWith('/assets/')) {
    event.respondWith(cacheFirst(request, SHELL))
    return
  }

  // pages and every other API call: always ask the server first, fall back to cache
  event.respondWith(networkFirst(request, url.pathname.startsWith('/api/') ? null : SHELL))
})
