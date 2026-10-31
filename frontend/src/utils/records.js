const BASE = '/sop'

export function recordPath(doctype, name) {
  return `/records/${encodeURIComponent(doctype)}/${encodeURIComponent(name)}`
}

export function listPath(doctype, query = {}) {
  const search = Object.entries(query)
    .filter(([, value]) => value !== undefined && value !== null && value !== '')
    .map(([key, value]) => `${encodeURIComponent(key)}=${encodeURIComponent(value)}`)
    .join('&')
  return `/records/${encodeURIComponent(doctype)}${search ? `?${search}` : ''}`
}

export function isAppUrl(url) {
  return typeof url === 'string' && (url === BASE || url.startsWith(`${BASE}/`))
}

export function appPath(url) {
  return isAppUrl(url) ? url.slice(BASE.length) || '/' : url
}

export function followLink(router, event, url) {
  if (!isAppUrl(url) || event.metaKey || event.ctrlKey || event.shiftKey || event.button) return
  event.preventDefault()
  router.push(appPath(url))
}
