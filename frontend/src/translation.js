import { createResource } from 'frappe-ui'

export default function translationPlugin(app) {
  app.config.globalProperties.__ = translate
  window.__ = translate

  if (!window.translatedMessages) fetchTranslations()
}

export function translate(message) {
  const messages = window.translatedMessages || {}
  const translated = messages[message] || message

  if (!/{\d+}/.test(message)) return translated

  return {
    format: (...args) =>
      translated.replace(/{(\d+)}/g, (match, position) =>
        typeof args[position] !== 'undefined' ? args[position] : match,
      ),
  }
}

export function fetchTranslations(language) {
  return createResource({
    url: 'sop.api.i18n.translations',
    params: language ? { language } : {},
    cache: ['translations', language || 'user'],
    auto: true,
    transform(data) {
      window.translatedMessages = data
      return data
    },
  })
}
