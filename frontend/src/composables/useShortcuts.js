import { onBeforeUnmount, onMounted } from 'vue'
import { searchDialog } from '@/data/ui'

export function useShortcuts() {
  function onKeydown(event) {
    if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k') {
      event.preventDefault()
      searchDialog.value = true
    }
  }

  onMounted(() => document.addEventListener('keydown', onKeydown))
  onBeforeUnmount(() => document.removeEventListener('keydown', onKeydown))
}
