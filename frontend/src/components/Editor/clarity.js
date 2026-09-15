export const LONG_SENTENCE = 25

const BASE_TERMS = [
  'SOP',
  'SOPS',
  'QA',
  'QC',
  'ID',
  'OK',
  'PDF',
  'ISO',
  'GMP',
  'EU',
  'TBD',
  'FAQ',
]

function escape(text) {
  return text.replace(/[.*+?^${}()|[\]\\]/g, '\\$&').replace(/\s+/g, '\\s+')
}

function whole(source, flags = 'iu') {
  return new RegExp(`(?<![\\p{L}\\p{N}])(?:${source})(?![\\p{L}\\p{N}])`, flags)
}

function listOf(words) {
  return whole(`(${words.map(escape).join('|')})`)
}

const ENGLISH_IRREGULAR =
  'made|done|kept|put|set|held|left|sent|given|taken|shown|seen|known|told|built|cut|found|brought|bought|caught|taught|paid|laid|said|sold|shut|split|spread|worn|torn|written|chosen|driven|eaten|fallen|forgotten|hidden|spoken|stolen|thrown|frozen|broken|drawn|grown|run|read|fed|led|met'

export const RULES = {
  en: {
    readability: 'flesch',
    sections: [
      ['Purpose'],
      ['Scope'],
      ['Responsibilities', 'Roles'],
      ['Procedure', 'Steps', 'Method'],
      ['Records', 'Documentation'],
    ],
    owner: /^\s*responsible\b/i,
    warning: /^\s*(warning|caution|danger)\b/i,
    ownerText: ' — responsible: @',
    warningText:
      '<blockquote><p><strong>Warning</strong> — the hazard, and what it does if ignored</p></blockquote>',
    passive: [
      whole(`(is|are|was|were|be|been|being)\\s+(\\p{L}+ly\\s+)?(\\p{L}+ed|${ENGLISH_IRREGULAR})`),
    ],
    vague: listOf([
      'as needed',
      'as required',
      'if necessary',
      'when necessary',
      'where appropriate',
      'as appropriate',
      'appropriate',
      'properly',
      'carefully',
      'correctly',
      'adequately',
      'adequate',
      'sufficiently',
      'sufficient',
      'regularly',
      'periodically',
      'from time to time',
      'as soon as possible',
      'asap',
      'reasonable',
      'and so on',
      'etc',
    ]),
    roles: whole(
      '(operators?|supervisors?|technicians?|engineers?|inspectors?|managers?|planners?|analysts?|quality|qa|qc|maintenance|storekeepers?|drivers?|leads?|owners?|responsible|shift|trainers?|approvers?|chemists?|cleaners?|handlers?)',
    ),
    records: whole(
      '(batch record|work order|records?|logbooks?|logs?|forms?|registers?|checklists?|sheets?|reports?|certificates?|labels?)',
    ),
    measure: whole(
      '(check|measure|set|adjust|heat|cool|weigh|tighten|torque|fill|dose|dilute|hold|maintain|verify)[^.]*?(?<![\\p{L}\\p{N}])(temperature|pressure|speed|weight|torque|time|level|ph|humidity|concentration|volume|flow|thickness|gap|voltage|current|rpm)',
    ),
    hazard: whole(
      '(hot|burns?|sharp|blades?|chemicals?|acids?|caustic|pressuri[sz]ed|high pressure|voltage|electrical|live parts|lockout|rotating|moving parts|toxic|flammable|forklifts?|at height|pinch|crush)',
    ),
    numberWords: 'step|no|rev|revision|version|section|page|table|figure|item|line|shift|sop|batch',
    terms: [...BASE_TERMS, 'UK', 'US', 'AM', 'PM', 'NA'],
  },
  da: {
    readability: 'lix',
    sections: [
      ['Formål'],
      ['Omfang', 'Anvendelsesområde'],
      ['Ansvar', 'Ansvarsfordeling'],
      ['Fremgangsmåde', 'Procedure', 'Arbejdsgang'],
      ['Dokumentation', 'Registreringer', 'Optegnelser'],
    ],
    owner: /^\s*ansvarlig/i,
    warning: /^\s*(advarsel|forsigtig|fare|pas på)/i,
    ownerText: ' — ansvarlig: @',
    warningText:
      '<blockquote><p><strong>Advarsel</strong> — faren, og hvad der sker, hvis den ignoreres</p></blockquote>',
    passive: [
      whole('(skal|må|bør|kan|vil|skulle|kunne|burde|måtte)\\s+(ikke\\s+)?\\p{L}{3,}es'),
      whole('(blive|bliver|blev|blevet)\\s+\\p{L}+(et|t)'),
      /^\p{L}+(en|et|ne)\s+\p{L}{2,}es(?![\p{L}\p{N}])/iu,
    ],
    vague: listOf([
      'efter behov',
      'ved behov',
      'om nødvendigt',
      'hvis nødvendigt',
      'når det er nødvendigt',
      'passende',
      'korrekt',
      'korrekte',
      'forsvarligt',
      'forsvarlig',
      'tilstrækkeligt',
      'tilstrækkelig',
      'løbende',
      'jævnligt',
      'regelmæssigt',
      'med jævne mellemrum',
      'hurtigst muligt',
      'snarest',
      'rimeligt',
      'rimelig',
      'osv',
      'm.m',
      'mv',
      'o.l',
      'etc',
    ]),
    roles: whole(
      '(operatør|medarbejder|sagsbehandler|leder|chef|kontorchef|fuldmægtig|tekniker|ansvarlig|supervisor|vagt|specialist|konsulent|koordinator|kvalitet|sikkerhed|ejer)\\p{L}*',
    ),
    records: whole(
      '(logbog|log|skema|formular|register|tjekliste|rapport|journal|blanket|certifikat|attest|protokol|kvittering|mærkat|etiket)\\p{L}*',
    ),
    measure: whole(
      '(kontrollér|kontroller|mål|indstil|justér|juster|opvarm|afkøl|vej|stram|fyld|dosér|doser|fortynd|hold|verificér|verificer|tjek)\\p{L}*[^.]*?(?<![\\p{L}\\p{N}])(temperatur|tryk|hastighed|vægt|moment|tid|niveau|ph|fugtighed|koncentration|volumen|flow|tykkelse|spænding|strøm|omdrejninger)\\p{L}*',
    ),
    hazard: whole(
      '(varm|brand|forbrænd|skarp|kniv|klinge|kemikalie|syre|ætsende|lud|under tryk|højtryk|højspænding|elektrisk|strømførende|roterende|bevægelige dele|giftig|brandfarlig|gaffeltruck|truck|højde|klem)\\p{L}*',
    ),
    numberWords:
      'trin|nr|rev|revision|version|afsnit|side|tabel|figur|punkt|linje|vagt|sop|batch|uge|kapitel',
    terms: [...BASE_TERMS, 'IT', 'HR', 'CPR', 'CVR', 'MV'],
  },
}

export function rulesFor(language) {
  return RULES[language] || RULES.en
}

export function words(text) {
  return (text.match(/[\p{L}\p{N}'’-]+/gu) || []).filter((word) => /[\p{L}\p{N}]/u.test(word))
}

export function syllables(word) {
  const clean = word.toLowerCase().replace(/[^a-z]/g, '')
  if (!clean) return 0
  if (clean.length <= 3) return 1

  const trimmed = clean.replace(/(?:[^laeiouy]es|ed|[^laeiouy]e)$/, '').replace(/^y/, '')
  const groups = trimmed.match(/[aeiouy]{1,2}/g)

  return Math.max(1, groups ? groups.length : 1)
}

export function sentencesOf(text) {
  const found = []
  const pattern = /[^.!?]+[.!?]*/g
  let match

  while ((match = pattern.exec(text))) {
    const raw = match[0]
    const lead = raw.length - raw.trimStart().length
    const sentence = raw.trim()

    if (words(sentence).length) found.push({ text: sentence, index: match.index + lead })
  }

  return found
}

export function easeOf(wordCount, sentenceCount, syllableCount) {
  if (!wordCount || !sentenceCount) return null

  return Math.round(
    206.835 - 1.015 * (wordCount / sentenceCount) - 84.6 * (syllableCount / wordCount),
  )
}

export function lixOf(wordCount, sentenceCount, longCount) {
  if (!wordCount || !sentenceCount) return null

  return Math.round(wordCount / sentenceCount + (longCount * 100) / wordCount)
}

export function labelOf(score, readability = 'flesch') {
  if (score === null) return { label: 'Nothing to check yet', tone: 'gray' }

  if (readability === 'lix') {
    if (score < 35) return { label: 'Easy to read', tone: 'green' }
    if (score < 45) return { label: 'Plain', tone: 'green' }
    if (score < 55) return { label: 'Fairly hard', tone: 'amber' }

    return { label: 'Hard to read', tone: 'red' }
  }

  if (score >= 70) return { label: 'Easy to read', tone: 'green' }
  if (score >= 60) return { label: 'Plain', tone: 'green' }
  if (score >= 50) return { label: 'Fairly hard', tone: 'amber' }

  return { label: 'Hard to read', tone: 'red' }
}

function isStep(block) {
  return !block.heading && (block.ordered || /^\S[^—]{1,60}\s—\s/.test(block.text))
}

function isWarning(block, rules) {
  return Boolean(block?.quote && rules.warning.test(block.text))
}

function hasPerson(block) {
  return (block.mentions || []).some((mention) => mention.doctype === 'User')
}

function hasRecord(block) {
  return (block.mentions || []).some((mention) => mention.doctype !== 'User')
}

function spot(block, index, length) {
  return { pos: block.pos, size: block.size, index, length }
}

function writingIssues(block, sentence, rules) {
  const list = words(sentence.text)
  const issues = []
  const where = spot(block, sentence.index, sentence.text.length)

  if (list.length > LONG_SENTENCE) {
    issues.push({ kind: 'long', group: 'writing', text: sentence.text, count: list.length, ...where })
  }

  if (rules.passive.some((pattern) => pattern.test(sentence.text))) {
    issues.push({ kind: 'passive', group: 'writing', text: sentence.text, ...where })
  }

  const vague = sentence.text.match(rules.vague)
  if (vague) {
    issues.push({
      kind: 'vague',
      group: 'writing',
      text: sentence.text,
      word: vague[1].toLowerCase(),
      ...where,
    })
  }

  return issues
}

function stepIssues(block, next, rules) {
  if (!isStep(block)) return []

  const nearby = `${block.text} ${next && rules.owner.test(next.text) ? next.text : ''}`
  if (rules.roles.test(nearby) || hasPerson(block)) return []

  return [{ kind: 'who', group: 'procedure', text: block.text, ...spot(block, 0, block.text.length) }]
}

function recordIssues(block, rules) {
  if (block.heading || hasRecord(block)) return []

  const match = block.text.match(rules.records)
  if (!match) return []

  const word = match[0]

  return [
    {
      kind: 'record',
      group: 'procedure',
      text: block.text,
      word,
      after: match.index + word.length,
      ...spot(block, match.index, word.length),
    },
  ]
}

function valueIssues(block, sentence, rules) {
  const issues = []

  const measure = sentence.text.match(rules.measure)
  if (measure && !/\d/.test(sentence.text)) {
    issues.push({
      kind: 'value',
      group: 'procedure',
      text: sentence.text,
      word: measure[2].toLowerCase(),
      ...spot(block, sentence.index, sentence.text.length),
    })
  }

  const bare = new RegExp(
    `(?<!(?:${rules.numberWords})\\s)(?<![\\p{L}\\p{N}.-])\\d+(?:[.,]\\d+)?(?=\\s*(?:[.,;:)]|$))`,
    'iu',
  )
  const number = sentence.text.match(bare)
  if (number) {
    issues.push({
      kind: 'unit',
      group: 'procedure',
      text: sentence.text,
      word: number[0],
      ...spot(block, sentence.index + number.index, number[0].length),
    })
  }

  return issues
}

function safetyIssues(block, previous, next, rules) {
  if (block.heading || isWarning(block, rules)) return []

  const hazard = block.text.match(rules.hazard)
  if (!hazard || isWarning(previous, rules) || isWarning(next, rules)) return []

  return [
    {
      kind: 'safety',
      group: 'procedure',
      text: block.text,
      word: hazard[0].toLowerCase(),
      ...spot(block, hazard.index, hazard[0].length),
    },
  ]
}

function termIssues(blocks, rules) {
  const text = blocks.map((block) => block.text).join('\n')
  const known = new Set(rules.terms)
  const seen = new Set()
  const issues = []
  const pattern = /(?<![\p{L}\p{N}])\p{Lu}{2,6}(?![\p{L}\p{N}])/gu

  for (const block of blocks) {
    if (block.heading) continue

    for (const match of block.text.matchAll(pattern)) {
      const term = match[0]
      if (known.has(term) || seen.has(term)) continue

      seen.add(term)

      const defined =
        new RegExp(`\\(${term}\\)`, 'u').test(text) ||
        new RegExp(`(?<![\\p{L}\\p{N}])${term}\\s*(\\(|—|-|:|=)\\s*\\p{L}`, 'u').test(text)

      if (!defined) {
        issues.push({
          kind: 'abbreviation',
          group: 'procedure',
          text: block.text,
          word: term,
          ...spot(block, match.index, term.length),
        })
      }
    }
  }

  return issues
}

function sectionIssues(blocks, wordCount, rules) {
  if (wordCount < 40) return []

  const headings = blocks
    .filter((block) => block.heading)
    .map((block) => block.text.trim().toLowerCase())

  return rules.sections
    .filter(
      (names) =>
        !names.some((name) => headings.some((heading) => heading.startsWith(name.toLowerCase()))),
    )
    .map((names) => ({ kind: 'section', group: 'procedure', text: names[0], word: names[0] }))
}

export function analyse(blocks, language = 'en') {
  const rules = rulesFor(language)
  let wordCount = 0
  let sentenceCount = 0
  let syllableCount = 0
  let longCount = 0
  const issues = []

  blocks.forEach((block, position) => {
    const previous = blocks[position - 1]
    const next = blocks[position + 1]

    issues.push(...stepIssues(block, next, rules))
    issues.push(...recordIssues(block, rules))
    issues.push(...safetyIssues(block, previous, next, rules))

    for (const sentence of sentencesOf(block.text)) {
      const list = words(sentence.text)

      wordCount += list.length
      sentenceCount += 1
      syllableCount += list.reduce((sum, word) => sum + syllables(word), 0)
      longCount += list.filter((word) => word.replace(/[^\p{L}]/gu, '').length > 6).length

      if (block.heading) continue

      issues.push(...valueIssues(block, sentence, rules))
      issues.push(...writingIssues(block, sentence, rules))
    }
  })

  issues.push(...termIssues(blocks, rules))
  issues.push(...sectionIssues(blocks, wordCount, rules))

  const score =
    rules.readability === 'lix'
      ? lixOf(wordCount, sentenceCount, longCount)
      : easeOf(wordCount, sentenceCount, syllableCount)

  const ordered = [
    ...issues.filter((issue) => issue.group === 'procedure'),
    ...issues.filter((issue) => issue.group === 'writing'),
  ]

  return {
    language: RULES[language] ? language : 'en',
    readability: rules.readability,
    words: wordCount,
    sentences: sentenceCount,
    minutes: Math.max(1, Math.round(wordCount / 200)),
    ease: score,
    ...labelOf(score, rules.readability),
    issues: ordered.slice(0, 60),
  }
}
