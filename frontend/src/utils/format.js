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
