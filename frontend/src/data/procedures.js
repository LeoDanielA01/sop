import { createResource, debounce } from 'frappe-ui'
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

function snapshot() {
  return JSON.stringify([
    activeSpace.value,
    activeProcess.value,
    view.value,
    search.value,
    page.value,
    pageLength.value,
  ])
}

const refresh = debounce(async () => {
  const mine = snapshot()
  await procedures.reload()

  if (mine !== snapshot()) refresh()
}, 60)

export function reloadProcedures() {
  refresh()
}

watch([page, pageLength], refresh)

watch([activeSpace, activeProcess, view, search], () => {
  page.value = 1
  refresh()
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
