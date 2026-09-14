export const STATUS_THEME = {
  Draft: 'gray',
  'In Review': 'amber',
  Approved: 'blue',
  Effective: 'green',
  'Under Revision': 'amber',
  Retired: 'red',
}

export function shortDate(value) {
  if (!value) return ''
  const d = new Date(value)
  return d.toLocaleDateString(undefined, { day: '2-digit', month: 'short', year: 'numeric' })
}

export function dayLabel(value) {
  if (!value) return 'Earlier'

  const day = new Date(value)
  const start = new Date(day.getFullYear(), day.getMonth(), day.getDate())
  const now = new Date()
  const days = Math.round(
    (new Date(now.getFullYear(), now.getMonth(), now.getDate()) - start) / 86400000,
  )

  if (days <= 0) return 'Today'
  if (days === 1) return 'Yesterday'
  if (days < 7) return 'This week'

  return day.toLocaleDateString(undefined, { day: '2-digit', month: 'short', year: 'numeric' })
}

export function reviewTone(due) {
  if (!due) return null
  const days = Math.ceil((new Date(due) - new Date()) / 86400000)
  if (days < 0) return 'red'
  if (days <= 30) return 'amber'
  return null
}

export function today() {
  return new Date().toISOString().slice(0, 10)
}
