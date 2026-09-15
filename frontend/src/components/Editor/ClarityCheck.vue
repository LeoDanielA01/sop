<template>
  <div v-if="editor" class="border-t border-outline-gray-1">
    <div class="px-1.5 py-1">
      <Button
        variant="ghost"
        class="w-full !justify-start"
        :aria-expanded="open"
        @click="open = !open"
      >
        <template #prefix>
          <span class="lucide-gauge size-3.5 shrink-0 text-ink-gray-6" aria-hidden="true" />
        </template>

        <span class="flex min-w-0 items-center gap-2 truncate text-sm text-ink-gray-6">
          <Badge :theme="report.tone" variant="subtle" size="sm">{{ __(report.label) }}</Badge>
          <span v-if="report.words">{{ __('{0} min read').format(report.minutes) }}</span>
          <span v-if="groups.procedure.length">
            · {{ __('{0} in the procedure').format(groups.procedure.length) }}
          </span>
          <span v-if="groups.writing.length">
            · {{ __('{0} in the writing').format(groups.writing.length) }}
          </span>
        </span>

        <template #suffix>
          <span
            class="ml-auto size-3.5 shrink-0 text-ink-gray-5"
            :class="open ? 'lucide-chevron-up' : 'lucide-chevron-down'"
            aria-hidden="true"
          />
        </template>
      </Button>
    </div>

    <template v-if="open">
      <ScrollArea v-if="all.length" viewport-class="max-h-72 px-2 pb-2">
        <template v-for="group in GROUPS" :key="group.key">
          <p
            v-if="groups[group.key].length"
            class="px-2 pb-1 pt-2 text-sm font-medium text-ink-gray-5"
          >
            {{ __(group.label) }}
          </p>

          <div
            v-for="(issue, index) in groups[group.key]"
            :key="`${group.key}-${index}`"
            class="flex items-start gap-2 rounded-3 px-2 py-1.5 hover:bg-surface-gray-1"
          >
            <Badge
              :theme="issue.tone || KINDS[issue.kind].theme"
              variant="subtle"
              size="sm"
              class="mt-0.5 shrink-0"
            >
              {{ __(KINDS[issue.kind].label) }}
            </Badge>

            <span class="min-w-0 flex-1 text-sm">
              <span class="line-clamp-2 text-ink-gray-7">{{ issue.text }}</span>
              <span class="block text-ink-gray-5">{{ hintOf(issue) }}</span>
            </span>

            <div class="flex shrink-0 items-center gap-0.5">
              <Button
                v-if="FIXES[issue.kind]"
                variant="subtle"
                size="sm"
                :icon-left="FIXES[issue.kind].icon"
                :label="__(FIXES[issue.kind].label)"
                @click="fix(issue)"
              />
              <Button
                v-if="issue.pos !== undefined"
                variant="ghost"
                size="sm"
                icon="lucide-text-cursor-input"
                :label="__('Select it in the text')"
                :tooltip="__('Select it in the text')"
                @click="reveal(issue)"
              />
            </div>
          </div>
        </template>
      </ScrollArea>

      <p v-else class="px-3 pb-2 text-sm text-ink-gray-5">
        {{ __('Nothing to tighten. Every step has an owner, values have units, links are live.') }}
      </p>
    </template>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import { Badge, Button, ScrollArea, createResource, debounce } from 'frappe-ui'
import { translate as __ } from '@/translation'
import { session } from '@/data/session'
import { analyse, rulesFor } from './clarity'

const props = defineProps({
  editor: { type: Object, default: null },
})

const GROUPS = [
  { key: 'procedure', label: 'Procedure' },
  { key: 'writing', label: 'Writing' },
]

const KINDS = {
  who: { label: 'Owner', theme: 'amber' },
  record: { label: 'Record', theme: 'blue' },
  value: { label: 'Value', theme: 'amber' },
  unit: { label: 'Unit', theme: 'amber' },
  safety: { label: 'Safety', theme: 'red' },
  section: { label: 'Section', theme: 'gray' },
  abbreviation: { label: 'Term', theme: 'gray' },
  mention: { label: 'Link', theme: 'red' },
  long: { label: 'Long', theme: 'amber' },
  passive: { label: 'Passive', theme: 'blue' },
  vague: { label: 'Vague', theme: 'red' },
}

const FIXES = {
  who: { label: 'Mention a person', icon: 'lucide-at-sign' },
  record: { label: 'Link a record', icon: 'lucide-hash' },
  safety: { label: 'Add a warning', icon: 'lucide-triangle-alert' },
  section: { label: 'Add section', icon: 'lucide-heading-2' },
  mention: { label: 'Open record', icon: 'lucide-arrow-up-right' },
}

const language = computed(() => session.user?.writing_language || 'en')
const rules = computed(() => rulesFor(language.value))

const open = ref(false)
const report = ref(analyse([], language.value))
const linkIssues = ref([])
let checkedLinks = ''

const all = computed(() => [...linkIssues.value, ...report.value.issues])

const groups = computed(() => ({
  procedure: all.value.filter((issue) => issue.group === 'procedure'),
  writing: all.value.filter((issue) => issue.group === 'writing'),
}))

const health = createResource({
  url: 'sop.api.mentions.health',
  onSuccess(rows) {
    const mentions = mentionsOf(props.editor)

    linkIssues.value = (rows || []).map((row) => {
      const found = mentions.find((item) => item.doctype === row.doctype && item.name === row.name)

      return {
        kind: 'mention',
        group: 'procedure',
        text: found?.text || `${row.doctype} ${row.name}`,
        message: row.message,
        tone: row.tone,
        doctype: row.doctype,
        name: row.name,
        pos: found ? found.from - 1 : undefined,
        index: 0,
        length: found ? found.to - found.from : 0,
      }
    })
  },
})

function blocksOf(editor) {
  const blocks = []
  const { doc } = editor.state

  doc.descendants((node, pos) => {
    if (!node.isTextblock) return true

    const $pos = doc.resolve(pos + 1)
    let ordered = false
    let quote = false

    for (let depth = $pos.depth; depth > 0; depth -= 1) {
      const name = $pos.node(depth).type.name
      if (name === 'orderedList') ordered = true
      if (name === 'blockquote') quote = true
    }

    const mentions = []
    node.forEach((child) => {
      const link = child.marks.find((mark) => mark.attrs?.href?.startsWith('#mention:'))
      if (!link) return

      const [, doctype, ...rest] = link.attrs.href.split(':')
      mentions.push({ doctype, name: rest.join(':') })
    })

    blocks.push({
      text: node.textContent,
      pos,
      size: node.nodeSize,
      heading: node.type.name === 'heading',
      ordered,
      quote,
      mentions,
    })

    return false
  })

  return blocks
}

function mentionsOf(editor) {
  const found = []
  if (!editor) return found

  editor.state.doc.descendants((node, pos) => {
    if (!node.isText) return true

    const link = node.marks.find((mark) => mark.attrs?.href?.startsWith('#mention:'))
    if (!link) return true

    const [, doctype, ...rest] = link.attrs.href.split(':')
    found.push({ doctype, name: rest.join(':'), text: node.text, from: pos, to: pos + node.nodeSize })

    return true
  })

  return found
}

const checkLinks = debounce(() => {
  const mentions = mentionsOf(props.editor)
  const key = mentions.map((item) => `${item.doctype}:${item.name}`).sort().join('|')

  if (key === checkedLinks) return
  checkedLinks = key

  if (!mentions.length) {
    linkIssues.value = []
    return
  }

  health.submit({
    references: mentions.map((item) => ({ doctype: item.doctype, name: item.name })),
  })
}, 1200)

const run = debounce(() => {
  if (!props.editor) return

  report.value = analyse(blocksOf(props.editor), language.value)
  checkLinks()
}, 300)

function hintOf(issue) {
  switch (issue.kind) {
    case 'who':
      return __('No one owns this step. Name the person or role.')
    case 'record':
      return __('“{0}”: link the actual record so readers can open it.').format(issue.word)
    case 'value':
      return __('Give the target {0} and its tolerance, e.g. 72 ± 2 °C.').format(issue.word)
    case 'unit':
      return __('Add the unit to {0}.').format(issue.word)
    case 'safety':
      return __('Mentions “{0}” but there is no warning near it.').format(issue.word)
    case 'section':
      return __('The {0} section is missing.').format(issue.word)
    case 'abbreviation':
      return __('Spell out {0} the first time it appears.').format(issue.word)
    case 'mention':
      return issue.message
    case 'long':
      return __('{0} words. Split it into two steps.').format(issue.count)
    case 'passive':
      return __('Say who does it: “The operator checks…”')
    default:
      return __('“{0}”: say exactly how, when or how much.').format(issue.word)
  }
}

function reveal(issue) {
  const size = props.editor.state.doc.content.size
  const from = Math.min(issue.pos + 1 + issue.index, size)
  const to = Math.min(from + issue.length, size)

  props.editor.chain().focus().setTextSelection({ from, to }).scrollIntoView().run()
}

function endOf(issue) {
  return issue.pos + issue.size - 1
}

function fix(issue) {
  const chain = props.editor.chain().focus()

  if (issue.kind === 'who') {
    chain.setTextSelection(endOf(issue)).insertContent(rules.value.ownerText).run()
    return
  }

  if (issue.kind === 'record') {
    chain.setTextSelection(issue.pos + 1 + issue.after).insertContent(' #').run()
    return
  }

  if (issue.kind === 'safety') {
    chain
      .insertContentAt(issue.pos + issue.size, rules.value.warningText)
      .scrollIntoView()
      .run()
    return
  }

  if (issue.kind === 'section') {
    const end = props.editor.state.doc.content.size
    chain.insertContentAt(end, `<h2>${issue.word}</h2><p></p>`).scrollIntoView().run()
    return
  }

  if (issue.kind === 'mention') {
    const slug = issue.doctype.toLowerCase().replace(/\s+/g, '-')
    window.open(`/app/${slug}/${encodeURIComponent(issue.name)}`, '_blank')
  }
}

watch(
  () => props.editor,
  (editor, previous) => {
    previous?.off('update', run)

    if (!editor) return

    editor.on('update', run)
    report.value = analyse(blocksOf(editor), language.value)
    checkLinks()
  },
  { immediate: true },
)

onBeforeUnmount(() => props.editor?.off('update', run))
</script>
