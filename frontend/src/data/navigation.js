import { createResource } from 'frappe-ui'
import { computed, ref, watch } from 'vue'
import { createRetryingResource } from '@/data/resource'

export const SECTIONS = [
  { key: 'procedures', label: 'Procedures', icon: 'lucide-book-text', route: '/' },
  { key: 'training', label: 'Training', icon: 'lucide-graduation-cap', route: '/training' },
]

export const activeSpace = ref(null)

let chosen = false

export const spacesResource = createRetryingResource({
  url: 'sop.api.procedures.spaces',
  auto: true,
  onSuccess(data) {
    if (!chosen && !activeSpace.value && data.length) activeSpace.value = data[0].name
  },
})

export const spaces = computed(() => spacesResource.data || [])

export const viewsResource = createRetryingResource({
  url: 'sop.api.procedures.counts',
  auto: true,
  makeParams: () => ({ space: activeSpace.value }),
})

export const attention = computed(() => viewsResource.data?.attention || 0)

export const views = computed(() => {
  const counts = viewsResource.data || {}
  return [
    { label: 'Awaiting my approval', value: 'approval', icon: 'lucide-stamp', count: counts.approval },
    { label: 'My drafts', value: 'drafts', icon: 'lucide-pencil-line', count: counts.drafts },
    {
      label: 'Unacknowledged',
      value: 'unacknowledged',
      icon: 'lucide-check-check',
      count: counts.unacknowledged,
    },
    {
      label: 'Due for review',
      value: 'review',
      icon: 'lucide-calendar-clock',
      count: counts.review,
      tone: 'overdue',
    },
  ]
})

export const createSpace = createResource({
  url: 'sop.api.procedures.create_space',
  onSuccess(space) {
    spacesResource.reload()
    setSpace(space.name)
  },
})

export function setSpace(name) {
  chosen = true
  activeSpace.value = name || null
}

watch(activeSpace, () => viewsResource.reload())

if (typeof window !== 'undefined') {
  window.addEventListener('focus', () => {
    viewsResource.reload()
    spacesResource.reload()
  })
}

export function refreshCounts() {
  viewsResource.reload()
  spacesResource.reload()
}
