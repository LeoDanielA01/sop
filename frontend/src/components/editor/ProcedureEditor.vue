<template>
  <div
    class="rounded-lg border border-outline-gray-2 bg-surface-base"
    @contextmenu="palette?.onContextMenu($event)"
    @touchstart="palette?.onTouchStart($event)"
    @touchend="palette?.cancelPress()"
    @touchmove="palette?.cancelPress()"
  >
    <ToolPalette ref="palette" v-model:pinned="ui.editorToolsPinned" :editor="editor" :api="api" />

    <EditorBubbleMenu v-if="editor && editable" :editor="editor" :items="BUBBLE_ITEMS" />
    <EditorTableMenu v-if="editor && editable" :editor="editor" />

    <EditorContent
      :editor="editor"
      class="prose-sop min-h-[60vh] px-4 py-4 text-base text-ink-gray-8 focus:outline-none"
    />

    <div
      v-if="!ui.editorToolsPinned"
      class="flex items-center gap-1.5 border-t border-outline-gray-1 px-3 py-1.5 text-sm text-ink-gray-5"
    >
      <span class="lucide-mouse-pointer-click size-3.5 shrink-0" aria-hidden="true" />
      Right-click for tools · long press on a phone · select text for the quick bar · pin the tools
      to keep a toolbar
    </div>
  </div>

  <Dialog v-model:open="picker.open" :title="PICKER_TITLE[picker.kind]" size="md">
    <template #default>
      <div class="flex flex-col gap-3">
        <Select
          v-if="picker.kind === 'record' && targets.data?.length > 1"
          :options="targets.data.map((row) => ({ label: row.doctype, value: row.doctype }))"
          :modelValue="picker.doctype"
          @update:modelValue="switchDoctype"
        />

        <FormControl
          type="text"
          placeholder="Search"
          v-model="picker.query"
          @update:modelValue="runSearch"
        />

        <div class="flex max-h-72 flex-col gap-1 overflow-y-auto">
          <Button
            v-for="row in picker.results"
            :key="row.name"
            variant="ghost"
            class="!justify-start"
            @click="choose(row)"
          >
            <span class="min-w-0 flex-1 truncate text-left">{{ row.label }}</span>
            <span class="ml-2 shrink-0 truncate font-mono text-sm text-ink-gray-4">
              {{ row.name }}
            </span>
          </Button>

          <p
            v-if="picker.kind === 'record' && !targets.data?.length"
            class="px-2 py-6 text-center text-sm text-ink-gray-5"
          >
            No doctype is set up for mentions yet. Settings → Mention chips decides what a mentioned
            record shows.
          </p>
          <p
            v-else-if="!loading && !picker.results.length"
            class="px-2 py-6 text-center text-sm text-ink-gray-5"
          >
            Nothing matches that.
          </p>
        </div>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { computed, ref } from 'vue'
import {
  Button,
  Dialog,
  FormControl,
  Select,
  createResource,
  useFileUpload,
} from 'frappe-ui'
import {
  EditorBubbleMenu,
  EditorContent,
  EditorTableMenu,
  RichTextKit,
  useEditor,
} from 'frappe-ui/editor'
import ToolPalette from './ToolPalette.vue'
import { useUI } from '@/stores/ui'
import { BUBBLE_ITEMS } from './tools'

const content = defineModel({ type: String, default: '' })
const props = defineProps({
  placeholder: { type: String, default: 'Right-click for the tools, or start writing…' },
  editable: { type: Boolean, default: true },
})

const emit = defineEmits(['change'])

const PICKER_TITLE = {
  record: 'Mention a record',
  person: 'Mention a person',
}

const palette = ref(null)
const ui = useUI()
const fileUpload = useFileUpload()

const editor = useEditor({
  content,
  format: 'html',
  editable: () => props.editable,
  placeholder: props.placeholder,
  extensions: [RichTextKit],
  uploadFunction: (file) => fileUpload.upload(file, { private: false, folder: 'Home/SOP' }),
  onUpdate({ editor }) {
    content.value = editor.getHTML()
    emit('change', content.value)
  },
})

const picker = ref({ open: false, kind: null, doctype: null, query: '', results: [] })

const targets = createResource({ url: 'sop.api.mentions.targets' })

const records = createResource({
  url: 'sop.api.mentions.find',
  onSuccess(rows) {
    picker.value.results = rows
  },
})

const people = createResource({
  url: 'sop.api.procedures.people',
  onSuccess(rows) {
    picker.value.results = rows.map((row) => ({ name: row.name, label: row.full_name }))
  },
})

const loading = computed(() => records.loading || people.loading)

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
    .insertContent(
      `<div data-sop="callout" data-tone="${kind}"><p>${
        kind === 'warning' ? 'Hazard or caution' : 'Worth knowing'
      }</p></div><p></p>`,
    )
    .run()
}

function runSearch() {
  const { kind, doctype, query } = picker.value

  if (kind === 'person') return people.submit({ search: query })
  if (doctype) records.submit({ doctype, text: query })
}

function switchDoctype(doctype) {
  picker.value.doctype = doctype
  picker.value.results = []
  runSearch()
}

async function pickRecord() {
  picker.value = { open: true, kind: 'record', doctype: null, query: '', results: [] }

  if (!targets.data) await targets.fetch()
  picker.value.doctype = targets.data?.[0]?.doctype || null
  if (picker.value.doctype) runSearch()
}

function pickPerson() {
  picker.value = { open: true, kind: 'person', doctype: 'User', query: '', results: [] }
  runSearch()
}

function choose(row) {
  const { kind, doctype } = picker.value
  const html = `<span data-mention="${kind}" data-doctype="${doctype}" data-name="${row.name}">${row.label}</span>&nbsp;`

  editor.value?.chain().focus().insertContent(html).run()
  picker.value.open = false
}

const api = { insertStep, insertCallout, pickRecord, pickPerson }
</script>
