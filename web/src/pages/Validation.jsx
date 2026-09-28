import React, { useEffect, useState } from 'react'
import { useI18n } from '../i18n.js'
import { api } from '../api.js'

// Human-in-the-loop (PS section 17): a teacher or native speaker confirms or
// corrects a translation once, and the whole platform starts using it.
export default function Validation({ notify }) {
  const { t } = useI18n()
  const [pending, setPending] = useState([])
  const [drafts, setDrafts] = useState({})
  const [teacher, setTeacher] = useState('')
  const [done, setDone] = useState(0)

  const load = () => api.validation().then((d) => setPending(d.items)).catch(() => {})

  useEffect(() => { load() }, [])

  async function seed() {
    const r = await api.seedQueue()
    notify(`${r.queued} ${t('queued')}`)
    load()
  }

  async function save(item) {
    const sat = drafts[`${item.scope}:${item.hindi}`] ?? item.proposed
    await api.validate({ scope: item.scope, hindi: item.hindi, sat, note: 'reviewed in app', teacher })
    setDone((d) => d + 1)
    notify(t('saved'))
  }

  return (
    <>
      <div className="card card-pad" style={{ marginBottom: 16 }}>
        <div className="grid g2" style={{ alignItems: 'end' }}>
          <div>
            <span className="label">{t('teacherName')} (validator)</span>
            <input className="field" value={teacher} onChange={(e) => setTeacher(e.target.value)} placeholder="—" />
          </div>
          <div className="chipbar">
            <button className="btn" onClick={seed}>📋 {t('seedQueue')}</button>
            <span className="pill">{pending.length} {t('queued')}</span>
            <span className="pill on">✓ {done} {t('saved').split('—')[0]}</span>
          </div>
        </div>
      </div>

      {pending.length === 0 && (
        <div className="card card-pad empty">
          <div style={{ fontSize: 40 }}>🎉</div>
          <div className="bold" style={{ marginTop: 8 }}>{t('noPending')}</div>
        </div>
      )}

      {pending.map((p) => {
        const key = `${p.scope}:${p.hindi}`
        return (
          <div className="card card-pad" style={{ marginBottom: 12 }} key={key}>
            <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', alignItems: 'center' }}>
              <span className={`badge ${p.scope === 'phrase' ? 'attested' : 'medium'}`}>{p.scope}</span>
              <div className="grow">
                <div className="hi bold" style={{ fontSize: 17 }}>{p.hindi}</div>
                <div className="small muted">{t('proposed')}: <span className="ol">{p.proposed || '—'}</span></div>
              </div>
              <div style={{ minWidth: 280, flex: '1 1 280px' }}>
                <span className="label">{t('correction')}</span>
                <input
                  className="field ol"
                  style={{ fontSize: 20 }}
                  defaultValue={p.proposed}
                  onChange={(e) => setDrafts((d) => ({ ...d, [key]: e.target.value }))}
                />
              </div>
              <button className="btn" onClick={() => save(p)}>💾 {t('save')}</button>
            </div>
          </div>
        )
      })}
    </>
  )
}
