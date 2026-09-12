import { createResource } from 'frappe-ui'
import { ref, watch } from 'vue'
import { activeSpace } from '@/data/navigation'

export const page = ref(1)
export const pageLength = ref(10)
export const view = ref('all')
export const search = ref('')

export const procedures = createResource({
  url: 'sop.api.procedures.list_procedures',
  auto: true,
  makeParams: () => ({
    space: activeSpace.value,
    view: view.value,
    search: search.value || undefined,
    start: (page.value - 1) * pageLength.value,
    page_length: pageLength.value,
  }),
})

watch([page, pageLength], () => procedures.reload())

watch([activeSpace, view, search], () => {
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
