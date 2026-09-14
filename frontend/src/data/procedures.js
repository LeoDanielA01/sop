import { createResource } from 'frappe-ui'
import { computed, ref, watch } from 'vue'
import { activeSpace } from '@/data/navigation'
import { activeProcess } from '@/data/processes'
import { preferences, setPreference } from '@/data/preferences'
import { createRetryingResource } from '@/data/resource'

export const page = ref(1)
export const pageLength = computed({
  get: () => preferences.rows_per_page,
  set: (value) => setPreference('rows_per_page', Number(value)),
})
export const view = ref('all')
export const search = ref('')

export const procedures = createRetryingResource({
  url: 'sop.api.procedures.list_procedures',
  auto: true,
  makeParams: () => ({
    space: activeSpace.value,
    process: activeProcess.value || undefined,
    view: view.value,
    search: search.value || undefined,
    start: (page.value - 1) * pageLength.value,
    page_length: pageLength.value,
  }),
})

watch([page, pageLength], () => procedures.reload())

watch([activeSpace, activeProcess, view, search], () => {
  page.value = 1
  procedures.reload()
})

export const procedure = createResource({
  url: 'sop.api.procedures.get_procedure',
})

export const acknowledge = createResource({
  url: 'sop.api.procedures.acknowledge',
  onSuccess: () => procedure.reload(),
})

export const resolveMentions = createResource({
  url: 'sop.api.mentions.resolve',
})
