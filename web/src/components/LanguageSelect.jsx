// Target-language <select>. One control, used by every translation screen, so a
// teacher picks the language once and the whole screen follows.
//
// It also states the truth about each language: what script it uses, how much data
// backs it, whether a voice exists, and - for Hindi input - that Mundari and Ho are
// word-level only. A selector that hides that would be the dishonest kind of UI.
import React, { useEffect, useState } from 'react'
import { api } from '../api.js'
import { useI18n } from '../i18n.js'

let CACHE = null

export function useLanguages() {
  const [langs, setLangs] = useState(CACHE || [])
  useEffect(() => {
    if (CACHE) return
    api.languages().then((d) => { CACHE = d.items || []; setLangs(CACHE) }).catch(() => {})
  }, [])
  return langs
}

export const TTS_NOTE = (lang) => {
  if (!lang) return null
  if (!lang.tts?.available) return lang.tts?.why || 'no voice model yet'
  return lang.tts.approx
    ? `${lang.tts.engine} — approximate: ${lang.tts.why}`
    : lang.tts.engine
}

export default function LanguageSelect({ value, onChange, compact = false }) {
  const { t } = useI18n()
  const langs = useLanguages()
  const cur = langs.find((l) => l.code === value)

  return (
    <div className={compact ? 'langsel compact' : 'langsel'}>
      <label className="label" htmlFor="lang-select">🌐 {t('targetLanguage')}</label>
      <select
        id="lang-select"
        className="select"
        value={value}
        onChange={(e) => onChange(e.target.value)}
      >
        {langs.length === 0 && <option value="sat">Santhali</option>}
        {langs.map((l) => (
          <option key={l.code} value={l.code}>
            {l.language} · {l.script}
          </option>
        ))}
      </select>

      {cur && (
        <div className="langmeta small muted">
          <div>
            {cur.counts?.sentence_memory != null
              ? `${cur.counts.sentence_memory.toLocaleString()} ${t('langSentences')}`
              : ''}
            {cur.counts?.dictionary_en ? ` · ${cur.counts.dictionary_en} ${t('langWords')}` : ''}
            {cur.counts?.vocab ? ` · ${cur.counts.vocab} ${t('langWords')}` : ''}
          </div>
          <div>
            {cur.tts?.available
              ? (cur.tts.approx ? `🔊 ${t('ttsApprox')}` : `🔊 ${cur.tts.engine}`)
              : `🔇 ${t('ttsNone')}`}
          </div>
          <div>
            {t('langHindiIn')}: <b>{cur.hindi_supported}</b> · {t('langEnglishIn')}: <b>{cur.english_supported}</b>
          </div>
          {cur.sources?.length ? (
            <div className="xsmall">
              {t('langSources')}: {cur.sources.map((s) => `${s.name} (${s.license})`).join(' · ')}
            </div>
          ) : null}
        </div>
      )}
    </div>
  )
}
