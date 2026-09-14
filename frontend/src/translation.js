import { ref } from 'vue'
import { createResource } from 'frappe-ui'

const messages = ref(window.translatedMessages || null)

export default function translationPlugin(app) {
  app.config.globalProperties.__ = translate
  window.__ = translate

  if (!messages.value) fetchTranslations()
}

export function translate(message) {
  const translated = messages.value?.[message] || message

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
    auto: true,
    transform(data) {
      messages.value = data
      window.translatedMessages = data

      return data
    },
  })
}
