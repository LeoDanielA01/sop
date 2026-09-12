import { ref, watch } from 'vue'

const STORAGE_KEY = 'sop:theme'
const media = window.matchMedia('(prefers-color-scheme: dark)')

/** 'light' | 'dark' | 'system' — system follows the OS and keeps following it. */
export const theme = ref(localStorage.getItem(STORAGE_KEY) || 'system')

function resolved() {
  if (theme.value === 'system') return media.matches ? 'dark' : 'light'
  return theme.value
}

export function applyTheme() {
  const value = resolved()
  const root = document.documentElement

  // frappe-ui reads the class; the attribute keeps our own CSS in step.
  root.classList.toggle('dark', value === 'dark')
  root.setAttribute('data-theme', value)
  root.style.colorScheme = value
}

export function setTheme(value) {
  theme.value = value
  localStorage.setItem(STORAGE_KEY, value)
  applyTheme()
}

watch(theme, applyTheme)
media.addEventListener('change', () => {
  if (theme.value === 'system') applyTheme()
})

applyTheme()
