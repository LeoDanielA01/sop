import { createResource } from 'frappe-ui'
import { computed, reactive } from 'vue'

const DEFAULTS = {
  autosave: 1,
  shortcuts: 1,
  rows_per_page: 20,
  email_on_approval: 1,
  email_on_publish: 1,
  email_on_training: 1,
  digest: 'Weekly',
}

export const preferences = reactive({ ...DEFAULTS })

export const preferencesResource = createResource({
  url: 'sop.api.preferences.get',
  auto: true,
  onSuccess(data) {
    Object.assign(preferences, data)
  },
})

const saveResource = createResource({ url: 'sop.api.preferences.save' })

export const preferencesError = computed(
  () => preferencesResource.error?.messages?.[0] || saveResource.error?.messages?.[0] || '',
)

export function setPreference(key, value) {
  if (preferences[key] === value) return

  preferences[key] = value
  saveResource.submit({ [key]: value })
}
