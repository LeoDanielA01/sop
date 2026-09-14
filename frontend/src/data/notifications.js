import { createResource } from 'frappe-ui'
import { computed } from 'vue'
import { createRetryingResource } from '@/data/resource'

export const feed = createResource({ url: 'sop.api.notifications.feed', auto: true })

export const unreadResource = createRetryingResource({
  url: 'sop.api.notifications.unread',
  auto: true,
})

export const counts = computed(
  () => unreadResource.data || { total: 0, procedure: 0, training: 0 },
)

export const unreadCount = computed(() => counts.value.total)

export const read = createResource({
  url: 'sop.api.notifications.mark_read',
  onSuccess() {
    feed.reload()
    unreadResource.reload()
  },
})

export function refreshNotifications() {
  feed.reload()
  unreadResource.reload()
}

if (typeof window !== 'undefined') {
  window.addEventListener('focus', refreshNotifications)
}
