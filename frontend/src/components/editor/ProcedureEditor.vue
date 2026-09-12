<script setup>
/**
 * The procedure editor.
 *
 * A thin wrapper over frappe-ui's TextEditor with the built-in menus turned
 * off: tools arrive on right-click through ToolPalette, or docked when pinned.
 * Everything SOP-specific — steps, hazard callouts, live mentions, shared
 * blocks — is inserted as plain HTML with data attributes, so the stored
 * document stays portable and the reader can render it without this component.
 */
import { onMounted, ref, watch } from 'vue'
import { Dialog, TextEditor, createResource } from 'frappe-ui'
import ToolPalette from './ToolPalette.vue'

const content = defineModel({ type: String, default: '' })
const props = defineProps({
  placeholder: { type: String, default: 'Write the procedure…' },
  editable: { type: Boolean, default: true },
})

const emit = defineEmits(['change'])

const textEditor = ref(null)
const palette = ref(null)
const editor = ref(null)
const pinned = ref(localStorage.getItem('sop:editor-tools-pinned') === '1')

const picker = ref({ open: false, kind: null, query: '', results: [] })

const search = createResource({
  url: 'frappe.client.get_list',
  onSuccess(rows) {
    picker.value.results = rows
  },
})

onMounted(() => {
  editor.value = textEditor.value?.editor || null
})

watch(content, () => emit('change', content.value))

/* ── what the palette can ask for ──────────────────────────────────────── */

function insertStep() {
  editor.value
    ?.chain()
    .focus()
    .insertContent(
      '<div data-sop="step"><p><strong>Step</strong> — what is done</p>' +
        '<p data-sop="step-meta">Responsible: role · Records: document</p></div><p></p>',
    )
    .run()
}

function insertCallout(kind) {
  editor.value
    ?.chain()
    .focus()
    .insertContent(`<div data-sop="callout" data-tone="${kind}"><p>Hazard or caution</p></div><p></p>`)
    .run()
}

function promptLink() {
  const url = window.prompt('Link to')
  if (url) editor.value?.chain().focus().setLink({ href: url }).run()
}

function pastePlain() {
  navigator.clipboard?.readText().then((text) => {
    editor.value?.chain().focus().insertContent(text).run()
  })
}

function openPicker(kind, doctype, fields) {
  picker.value = { open: true, kind, query: '', results: [], doctype, fields }
  runSearch()
}

function runSearch() {
  const { doctype, fields, query } = picker.value
  search.submit({
    doctype,
    fields,
    filters: query ? [[fields[1] || 'name', 'like', `%${query}%`]] : undefined,
    limit_page_length: 10,
  })
}

const pickRecord = () => openPicker('record', 'Item', ['name', 'item_name'])
const pickPerson = () => openPicker('person', 'User', ['name', 'full_name'])
const pickBlock = () => openPicker('block', 'SOP Block', ['name', 'title'])

/** Mentions are stored as spans carrying the reference, never as loose text. */
function choose(row) {
  const { kind, doctype } = picker.value
  const label = row.item_name || row.full_name || row.title || row.name

  const html =
    kind === 'block'
      ? `<div data-block="${row.name}" data-pin="latest"></div><p></p>`
      : `<span data-mention="${kind}" data-doctype="${doctype}" data-name="${row.name}">${label}</span>&nbsp;`

  editor.value?.chain().focus().insertContent(html).run()
  picker.value.open = false
}

const api = { insertStep, insertCallout, promptLink, pastePlain, pickRecord, pickPerson, pickBlock }
</script>

<template>
  <div
    class="rounded-lg border border-outline-gray-2 bg-surface-base"
    @contextmenu="palette?.onContextMenu($event)"
    @touchstart="palette?.onTouchStart($event)"
    @touchend="palette?.cancelPress()"
    @touchmove="palette?.cancelPress()"
  >
    <ToolPalette ref="palette" v-model:pinned="pinned" :editor="editor" :api="api" />

    <TextEditor
      ref="textEditor"
      v-model:content="content"
      :editable="editable"
      :placeholder="placeholder"
      :fixed-menu="false"
      :bubble-menu="false"
      editor-class="prose-sop min-h-[60vh] px-4 py-4 text-base text-ink-gray-8 focus:outline-none"
    />

    <div
      v-if="!pinned"
      class="flex items-center gap-1.5 border-t border-outline-gray-1 px-3 py-1.5 text-xs text-ink-gray-4"
    >
      <span class="lucide-mouse-pointer-click size-3.5" aria-hidden="true" />
      Right-click for tools · long press on a phone · pin them to keep a toolbar
    </div>
  </div>

  <Dialog
    v-model="picker.open"
    :options="{
      title:
        picker.kind === 'person'
          ? 'Mention a person'
          : picker.kind === 'block'
            ? 'Insert a shared block'
            : 'Mention a record',
      size: 'md',
    }"
  >
    <template #body-content>
      <FormControl
        type="text"
        placeholder="Search"
        v-model="picker.query"
        @update:modelValue="runSearch"
      />
      <div class="mt-3 flex flex-col gap-1">
        <Button
          v-for="row in picker.results"
          :key="row.name"
          variant="ghost"
          class="!justify-start"
          @click="choose(row)"
        >
          <span class="truncate text-left">
            {{ row.item_name || row.full_name || row.title || row.name }}
          </span>
          <span class="ml-2 truncate font-mono text-xs text-ink-gray-4">{{ row.name }}</span>
        </Button>
        <p v-if="!search.loading && !picker.results.length" class="px-2 py-6 text-center text-sm text-ink-gray-5">
          Nothing matches that.
        </p>
      </div>
    </template>
  </Dialog>
</template>
