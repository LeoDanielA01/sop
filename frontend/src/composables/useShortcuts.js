import { onBeforeUnmount, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { preferences } from '@/data/preferences'
import { useUI } from '@/stores/ui'

const GO_TO = { p: '/', t: '/training', m: '/training/matrix', s: '/training/sessions' }

export const SHORTCUTS = [
  { keys: ['mod', 'K'], label: 'Search', group: 'Anywhere' },
  { keys: ['mod', 'B'], label: 'Show or hide the sidebar', group: 'Anywhere' },
  { keys: ['mod', 'S'], label: 'Save the draft you are editing', group: 'Anywhere' },
  { keys: ['mod', '/'], label: 'This list', group: 'Anywhere' },
  { keys: ['mod', 'alt', 'N'], label: 'New procedure', group: 'Do' },
  { keys: ['mod', 'shift', 'F'], label: 'Find and replace', group: 'Do' },
  { keys: ['mod', 'shift', 'U'], label: 'Notifications', group: 'Do' },
  { keys: ['mod', 'alt', 'P'], label: 'Procedures', group: 'Go to' },
  { keys: ['mod', 'alt', 'T'], label: 'Training', group: 'Go to' },
  { keys: ['mod', 'alt', 'M'], label: 'Training matrix', group: 'Go to' },
  { keys: ['mod', 'alt', 'S'], label: 'Sessions', group: 'Go to' },
  { keys: ['Esc'], label: 'Close what is open', group: 'Help' },
]

export function useShortcuts() {
  const router = useRouter()
  const ui = useUI()

  function keyOf(event) {
    if (event.code?.startsWith('Key')) return event.code.slice(3).toLowerCase()
    if (event.code === 'Slash') return '/'

    return (event.key || '').toLowerCase()
  }

  function onKeydown(event) {
    if (!event.metaKey && !event.ctrlKey) return

    const key = keyOf(event)

    if (!event.altKey && !event.shiftKey) {
      if (key === 'k') {
        event.preventDefault()
        ui.searchDialog = true
      }

      if (key === 'b') {
        event.preventDefault()
        ui.toggleSidebar()
      }

      if (key === '/') {
        event.preventDefault()
        ui.openSettings('shortcuts')
      }

      return
    }

    if (!preferences.shortcuts) return

    if (event.altKey && !event.shiftKey) {
      if (key === 'n') {
        event.preventDefault()
        router.push('/new')
        return
      }

      if (GO_TO[key]) {
        event.preventDefault()
        router.push(GO_TO[key])
      }

      return
    }

    if (event.shiftKey && !event.altKey) {
      if (key === 'f') {
        event.preventDefault()
        ui.replaceDialog = true
      }

      if (key === 'u') {
        event.preventDefault()
        ui.notificationsPanel = !ui.notificationsPanel
      }
    }
  }

  onMounted(() => document.addEventListener('keydown', onKeydown))

  onBeforeUnmount(() => document.removeEventListener('keydown', onKeydown))
}
