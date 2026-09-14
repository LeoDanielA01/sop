<template>
  <Teleport to="body">
    <div
      v-if="open"
      class="fixed z-50 w-72 overflow-hidden rounded-lg border border-outline-gray-2 bg-surface-base shadow-2xl"
      :style="{ left: `${spot.left}px`, top: `${spot.top}px` }"
      role="listbox"
    >
      <div class="border-b border-outline-gray-1 px-3 py-1.5 text-sm text-ink-gray-5">
        {{ heading }}
      </div>

      <div class="max-h-64 overflow-y-auto p-1">
        <div
          v-for="(row, index) in rows"
          :key="row.value"
          class="flex cursor-pointer items-center gap-2.5 rounded-md px-2 py-1.5"
          :class="index === cursor ? 'bg-surface-gray-2' : 'hover:bg-surface-gray-2'"
          role="option"
          :aria-selected="index === cursor"
          @mousedown.prevent="pick(row)"
          @mouseenter="cursor = index"
        >
          <Avatar v-if="row.image !== undefined" :image="row.image" :label="row.label" size="sm" />
          <span
            v-else
            :class="row.icon || 'lucide-file-text'"
            class="size-4 shrink-0 text-ink-gray-5"
            aria-hidden="true"
          />

          <span class="min-w-0 flex-1">
            <span class="block truncate text-base text-ink-gray-8">{{ row.label }}</span>
            <span v-if="row.hint" class="block truncate text-sm text-ink-gray-5">{{ row.hint }}</span>
          </span>
        </div>

        <p v-if="!rows.length" class="px-2 py-3 text-center text-sm text-ink-gray-5">
          {{ resource.loading ? 'Looking…' : 'Nothing matches' }}
        </p>
      </div>

      <div class="border-t border-outline-gray-1 px-3 py-1.5 text-xs text-ink-gray-5">
        <template v-if="stage === 'doctype'">Pick a type, then search its records</template>
        <template v-else>↑ ↓ to move · ⏎ to insert · esc to dismiss</template>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { Avatar, createResource } from 'frappe-ui'

const props = defineProps({
  editor: { type: Object, default: null },
})

const TRIGGER = /(^|[\s(])([@#])([\w .@%-]*)$/

const open = ref(false)
const cursor = ref(0)
const spot = ref({ left: 0, top: 0 })
const trigger = ref('@')
const query = ref('')
const doctype = ref(null)
const from = ref(0)

const stage = computed(() => {
  if (trigger.value === '@') return 'person'

  return doctype.value ? 'record' : 'doctype'
})

const heading = computed(() => {
  if (stage.value === 'person') return 'Mention a person'
  if (stage.value === 'doctype') return 'Mention a record — pick a type'

  return `Mention a ${doctype.value}`
})

const people = createResource({ url: 'sop.api.procedures.people' })
const types = createResource({ url: 'sop.api.mentions.doctypes' })
const records = createResource({ url: 'sop.api.mentions.find' })

const resource = computed(() => {
  if (stage.value === 'person') return people
  if (stage.value === 'doctype') return types

  return records
})

const rows = computed(() => {
  if (stage.value === 'person') {
    return (people.data || []).map((row) => ({
      value: row.name,
      label: row.full_name || row.name,
      hint: row.name,
      image: row.user_image || null,
      doctype: 'User',
    }))
  }

  if (stage.value === 'doctype') {
    return (types.data || []).map((name) => ({
      value: name,
      label: name,
      icon: 'lucide-shapes',
      type: true,
    }))
  }

  return (records.data || []).map((row) => ({
    value: row.name,
    label: row.label,
    hint: row.name === row.label ? null : row.name,
    doctype: doctype.value,
  }))
})

function search() {
  cursor.value = 0

  if (stage.value === 'person') return people.submit({ search: query.value })
  if (stage.value === 'doctype') return types.submit({ search: query.value })

  return records.submit({ doctype: doctype.value, text: query.value })
}

function close() {
  open.value = false
  doctype.value = null
  query.value = ''
}

function detect() {
  const editor = props.editor
  if (!editor) return close()

  const { state } = editor
  const { empty, $from } = state.selection
  if (!empty) return close()

  const text = $from.parent.textBetween(0, $from.parentOffset, undefined, ' ')
  const match = text.match(TRIGGER)

  if (!match) return close()

  const [, , sign, typed] = match
  const [afterType, rest] = typed.includes(':') ? typed.split(':') : [null, typed]

  trigger.value = sign
  doctype.value = sign === '#' ? afterType : null
  query.value = sign === '#' ? rest : typed
  from.value = $from.pos - typed.length - 1

  const coords = editor.view.coordsAtPos($from.pos)
  spot.value = {
    left: Math.min(coords.left, window.innerWidth - 300),
    top: Math.min(coords.bottom + 6, window.innerHeight - 320),
  }

  open.value = true
  search()
}

function pick(row) {
  if (!row) return

  if (row.type) {
    doctype.value = row.value
    query.value = ''
    props.editor?.chain().focus().insertContent(':').run()
    search()
    return
  }

  props.editor
    ?.chain()
    .focus()
    .deleteRange({ from: from.value, to: props.editor.state.selection.$from.pos })
    .insertContent([
      {
        type: 'text',
        text: row.label,
        marks: [{ type: 'link', attrs: { href: `#mention:${row.doctype}:${row.value}` } }],
      },
      { type: 'text', text: ' ' },
    ])
    .run()

  close()
}

function onKeydown(event) {
  if (!open.value) return

  if (event.key === 'Escape') {
    event.preventDefault()
    return close()
  }

  if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
    event.preventDefault()
    const step = event.key === 'ArrowDown' ? 1 : -1
    const total = rows.value.length || 1
    cursor.value = (cursor.value + step + total) % total
    return
  }

  if (event.key === 'Enter' && rows.value.length) {
    event.preventDefault()
    pick(rows.value[cursor.value])
  }
}

watch(
  () => props.editor,
  (editor) => {
    if (editor) editor.on('transaction', detect)
  },
  { immediate: true },
)

onMounted(() => document.addEventListener('keydown', onKeydown, true))

onBeforeUnmount(() => {
  document.removeEventListener('keydown', onKeydown, true)
  props.editor?.off('transaction', detect)
})
</script>
