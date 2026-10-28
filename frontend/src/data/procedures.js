import { createResource, debounce } from 'frappe-ui'
import { computed, reactive, ref, watch } from 'vue'
import { activeSpace } from '@/data/navigation'
import { activeProcess } from '@/data/processes'
import { preferences } from '@/data/preferences'
import { createRetryingResource } from '@/data/resource'

export const page = ref(1)
export const pageLength = ref(preferences.rows_per_page)

watch(
  () => preferences.rows_per_page,
  (value) => (pageLength.value = value),
)
export const view = ref('all')
export const search = ref('')
export const sort = ref('')
export const filters = reactive({})

export const facets = createResource({ url: 'sop.api.search.facets', cache: 'sop-search-facets' })

function chosenFilters() {
  const out = {}
  for (const [field, values] of Object.entries(filters)) if (values?.length) out[field] = values
  return Object.keys(out).length ? JSON.stringify(out) : undefined
}

export const procedures = createRetryingResource({
  url: 'sop.api.procedures.list_procedures',
  auto: true,
  makeParams: () => ({
    space: activeSpace.value,
    process: activeProcess.value || undefined,
    view: view.value,
    search: search.value || undefined,
    filters: chosenFilters(),
    sort: sort.value || undefined,
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
    chosenFilters(),
    sort.value,
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

watch([activeSpace, activeProcess, view, search, sort, () => chosenFilters()], () => {
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
