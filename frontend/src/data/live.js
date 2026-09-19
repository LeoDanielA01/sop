import { translate as __ } from '@/translation'

export const CHECK_WORDS = {
  at_least: { label: 'is at least', target: 'number' },
  at_most: { label: 'is at most', target: 'number' },
  above_zero: { label: 'is more than zero' },
  not_passed: { label: 'has not passed' },
  days_left: { label: 'is at least … days away', target: 'days' },
  is: { label: 'is', target: 'text' },
  is_not: { label: 'is not', target: 'text' },
  no_warning: { label: 'has no warning' },
}

function part(value) {
  return encodeURIComponent(String(value ?? ''))
}

export function liveHref(doctype, name, key) {
  return `#live:${[doctype, name, key].map(part).join(':')}`
}

export function checkHref(doctype, name, key, check, target = '') {
  return `#check:${[doctype, name, key, check, target].map(part).join(':')}`
}

export function isLiveHref(href) {
  return /^#(live|check):/.test(href || '')
}

export function checkPhrase(check, target) {
  const words = CHECK_WORDS[check]
  if (!words) return check
  if (check === 'days_left') return __('is at least {0} days away').format(target || 0)
  if (words.target) return `${__(words.label)} ${target ?? ''}`.trim()
  return __(words.label)
}
