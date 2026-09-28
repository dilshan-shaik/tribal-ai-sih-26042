import React, { useEffect, useState } from 'react'
import { useI18n } from '../i18n.js'
import { api } from '../api.js'
import { store } from '../store.js'

export default function Offline({ health, notify }) {
  const { t } = useI18n()
  const [stats, setStats] = useState(null)
  const [swState, setSwState] = useState('checking')
  const [cached, setCached] = useState(false)
  const [syncedAt, setSyncedAt] = useState(store.get('mtb-sync'))

  useEffect(() => {
    api.stats().then(setStats).catch(() => {})
    if (!('serviceWorker' in navigator)) { setSwState('unsupported'); return }
    navigator.serviceWorker.getRegistration().then((r) => setSwState(r ? 'active' : 'none'))
    caches?.keys().then((keys) => setCached(keys.some((k) => k.includes('mtb')))).catch(() => {})
  }, [])

  async function downloadPack() {
    try {
      const c = await caches.open('mtb-pack-v1')
      await c.add(api.packUrl)
      setCached(true)
    } catch {
      notify('⚠️ this preview frame does not expose the Cache API — download works in a normal tab')
      return
    }
    const now = new Date().toLocaleString()
    store.set('mtb-sync', now)
    setSyncedAt(now)
    notify('✅ language pack cached for offline use')
  }

  // the escape hatch: drop every cache, unregister the worker, reload the current build
  async function refreshApp() {
    try {
      const keys = await caches.keys()
      await Promise.all(keys.map((k) => caches.delete(k)))
      const regs = await navigator.serviceWorker.getRegistrations()
      await Promise.all(regs.map((r) => r.unregister()))
      notify(t('appRefreshed'))
    } catch {
      notify(t('appRefreshNote'))
    }
    setTimeout(() => window.location.reload(), 600)
  }

  async function syncNow() {
    try {
      await fetch('/api/health')
      await downloadPack()
    } catch {
      notify('⚠️ still offline — continues working from cache')
    }
  }

  const ttsMb = stats?.tts?.mb ?? health?.tts?.mb ?? 0

  return (
    <div className="grid g3">
      <div className="card card-pad stat">
        <div className="n">{health ? `${(4.6).toFixed(1)} MB` : '–'}</div>
        <div className="l">{t('packSize')}</div>
        <div className="small muted" style={{ marginTop: 6 }}>{health?.counts.vocab} words · {health?.counts.sentence_memory} sentences</div>
      </div>
      <div className="card card-pad stat">
        <div className="n">{stats?.tts?.clips ?? health?.tts?.clips ?? 0}</div>
        <div className="l">{t('ttsClips')}</div>
        <div className="small muted" style={{ marginTop: 6 }}>{ttsMb} MB cached audio</div>
      </div>
      <div className="card card-pad stat">
        <div className="n">{swState === 'active' ? '✓' : swState === 'unsupported' ? '—' : '…'}</div>
        <div className="l">{t('swState')}</div>
        <div className="small muted" style={{ marginTop: 6 }}>{swState === 'active' ? t('cached') : t('notCached')}</div>
      </div>

      <div className="card card-pad" style={{ gridColumn: '1 / -1' }}>
        <div className="grid g2">
          <div>
            <div className="label">{t('syncTitle')}</div>
            <p className="small muted" style={{ lineHeight: 1.6 }}>{t('offlineSub')}</p>
            <div className="chipbar" style={{ marginTop: 10 }}>
              <button className="btn" onClick={syncNow}>🔄 {t('syncNow')}</button>
              <button className="btn ghost" onClick={downloadPack}>{cached ? '✓ ' : '⬇️ '}{t('downloadPack')}</button>
              <button className="btn ghost" onClick={refreshApp} title={t('appRefreshNote')}>
                ♻️ {t('appRefresh')}
              </button>
            </div>
            <div className="small muted" style={{ marginTop: 10 }}>
              {t('lastSync')}: {syncedAt || '—'}
            </div>
          </div>
          <div>
            <div className="label">{t('sources')}</div>
            <div className="small" style={{ lineHeight: 1.9 }}>
              <div>📦 <b>aiswarya9302/english-santali-combined</b> — 72,977 sentence pairs <span className="muted xsmall">(Hugging Face)</span></div>
              <div>📦 <b>google/smol</b> — smolsent + gatitos word lexicons <span className="muted xsmall">(Hugging Face)</span></div>
              <div>🗂️ <b>Wikidata</b> — 7,549 sat.wikipedia × hi.wikipedia title pairs</div>
              <div>✍️ <b>Project lexicon</b> — 208-word foundational-literacy list</div>
            </div>
          </div>
        </div>
      </div>

      <div className="card card-pad" style={{ gridColumn: '1 / -1' }}>
        <div className="label">Usage on this device</div>
        <table className="simple">
          <tbody>
            {Object.entries(stats?.usage || health?.counts || {}).slice(0, 8).map(([k, v]) => (
              <tr key={k}><td>{k}</td><td className="bold">{String(v)}</td></tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
