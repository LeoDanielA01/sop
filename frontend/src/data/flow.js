import { checkPhrase } from '@/data/live'
import { translate as __ } from '@/translation'

export const SEPARATOR = '|'

const listeners = new Set()

export function onFlowEdit(handler) {
  listeners.add(handler)

  return () => listeners.delete(handler)
}

export function askFlowEdit(request) {
  for (const handler of listeners) handler(request)
}

function part(value) {
  return encodeURIComponent(String(value ?? ''))
}

export function checkCondition(doctype, name, key, check, target = '') {
  return `check:${[doctype, name, key, check, target].map(part).join(':')}`
}

export function askCondition(ask, check, answer) {
  return `ask:${[ask, check, answer].map(part).join(':')}`
}

export function parseCondition(spec) {
  let parts

  try {
    parts = String(spec || '')
      .split(':')
      .map(decodeURIComponent)
  } catch {
    return null
  }

  const [kind, ...rest] = parts

  if (kind === 'ask' && rest.length >= 3) {
    return { kind, ask: rest[0], check: rest[1], target: rest[2] }
  }

  if (kind === 'check' && rest.length >= 4) {
    return {
      kind,
      doctype: rest[0],
      name: rest[1],
      key: rest[2],
      check: rest[3],
      target: rest[4] ?? '',
    }
  }

  return null
}

export function answersOf(value) {
  return String(value || '')
    .split(SEPARATOR)
    .map((option) => option.trim())
    .filter(Boolean)
}

export function nextAskId(taken) {
  let index = 1
  while (taken.includes(`q${index}`)) index += 1

  return `q${index}`
}

export function checkLabel(record, option, check, target) {
  return `${record}: ${option} ${checkPhrase(check, target)}`
}

export function askLabel(question, check, answer) {
  const said = check === 'is_not' ? __('is not') : __('is')

  return `${question || __('The answer')} — ${said} “${answer}”`
}

export function answerPasses(spec, answers) {
  const given = answers?.[spec.ask]
  if (given === undefined || given === null || given === '') return null

  return spec.check === 'is_not' ? given !== spec.target : given === spec.target
}
