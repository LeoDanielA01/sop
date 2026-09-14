import { onBeforeUnmount, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { preferences } from '@/data/preferences'
import { useUI } from '@/stores/ui'

const TYPING = ['input', 'textarea', 'select']

export const SHORTCUTS = [
  { keys: ['mod', 'K'], label: 'Search', group: 'Anywhere' },
  { keys: ['mod', 'B'], label: 'Show or hide the sidebar', group: 'Anywhere' },
  { keys: ['mod', 'S'], label: 'Save the draft you are editing', group: 'Anywhere' },
  { keys: ['N'], label: 'New procedure', group: 'Do' },
  { keys: ['F'], label: 'Find and replace', group: 'Do' },
  { keys: ['I'], label: 'Notifications', group: 'Do' },
  { keys: ['G', 'P'], label: 'Procedures', group: 'Go to' },
  { keys: ['G', 'T'], label: 'Training', group: 'Go to' },
  { keys: ['G', 'M'], label: 'Training matrix', group: 'Go to' },
  { keys: ['G', 'S'], label: 'Sessions', group: 'Go to' },
  { keys: ['?'], label: 'This list', group: 'Help' },
  { keys: ['Esc'], label: 'Close what is open', group: 'Help' },
]

export function useShortcuts() {
  const router = useRouter()
  const ui = useUI()

  let chord = null
  let timer = null

  function typing(event) {
    const target = event.target

    return target?.isContentEditable || TYPING.includes((target?.tagName || '').toLowerCase())
  }

  function armChord() {
    chord = 'g'
    clearTimeout(timer)
    timer = setTimeout(() => (chord = null), 1200)
  }

  function followChord(key, event) {
    const routes = { p: '/', t: '/training', m: '/training/matrix', s: '/training/sessions' }

    chord = null
    clearTimeout(timer)

    if (!routes[key]) return

    event.preventDefault()
    router.push(routes[key])
  }

  function onKeydown(event) {
    const key = event.key.toLowerCase()

    if (event.metaKey || event.ctrlKey) {
      if (key === 'k') {
        event.preventDefault()
        ui.searchDialog = true
      }

      if (key === 'b') {
        event.preventDefault()
        ui.toggleSidebar()
      }

      return
    }

    if (!preferences.shortcuts || event.altKey || typing(event)) return

    if (chord === 'g') return followChord(key, event)
    if (key === 'g') return armChord()

    if (key === 'n') {
      event.preventDefault()
      router.push('/new')
    }

    if (key === 'f') {
      event.preventDefault()
      ui.replaceDialog = true
    }

    if (key === 'i') {
      event.preventDefault()
      ui.notificationsDialog = true
    }

    if (key === '?') {
      event.preventDefault()
      ui.openSettings('shortcuts')
    }
  }

  onMounted(() => document.addEventListener('keydown', onKeydown))

  onBeforeUnmount(() => {
    document.removeEventListener('keydown', onKeydown)
    clearTimeout(timer)
  })
}
