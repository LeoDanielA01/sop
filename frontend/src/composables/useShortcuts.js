import { onBeforeUnmount, onMounted } from 'vue'
import { useUI } from '@/stores/ui'

export function useShortcuts() {
  const ui = useUI()

  function onKeydown(event) {
    if (!event.metaKey && !event.ctrlKey) return

    const key = event.key.toLowerCase()

    if (key === 'k') {
      event.preventDefault()
      ui.searchDialog = true
    }

    if (key === 'b') {
      event.preventDefault()
      ui.toggleSidebar()
    }
  }

  onMounted(() => document.addEventListener('keydown', onKeydown))
  onBeforeUnmount(() => document.removeEventListener('keydown', onKeydown))
}
