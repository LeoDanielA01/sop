<template>
  <div
    class="rounded-4 border border-outline-gray-2 bg-surface-base"
    @contextmenu="palette?.onContextMenu($event)"
    @touchstart="palette?.onTouchStart($event)"
    @touchend="palette?.cancelPress()"
    @touchmove="palette?.cancelPress()"
  >
    <ToolPalette ref="palette" v-model:pinned="ui.editorToolsPinned" :editor="editor" :api="api" />

    <EditorBubbleMenu v-if="editor && editable" :editor="editor" :items="bubbleItems()" />
    <MentionSuggest :editor="editor" />
    <EditorTableMenu v-if="editor && editable" :editor="editor" />

    <EditorContent
      :editor="editor"
      class="prose-sop min-h-[60vh] px-4 py-4 text-base text-ink-gray-8 focus:outline-none"
    />

    <ClarityCheck v-if="editable" :editor="editor" />

    <LiveDialog v-model:open="live.open" :mode="live.mode" :editor="editor" />

    <div
      v-if="!ui.editorToolsPinned"
      class="flex items-center gap-1.5 border-t border-outline-gray-1 px-3 py-1.5 text-sm text-ink-gray-5"
    >
      <span class="lucide-mouse-pointer-click size-3.5 shrink-0" aria-hidden="true" />
      {{ __('Right-click for tools · long press on a phone · select text for the quick bar · pin the tools to keep a toolbar') }}
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useFileUpload } from 'frappe-ui'
import {
  EditorBubbleMenu,
  EditorContent,
  EditorTableMenu,
  RichTextKit,
  useEditor,
} from 'frappe-ui/editor'
import ClarityCheck from './ClarityCheck.vue'
import LiveDialog from './LiveDialog.vue'
import MentionSuggest from './MentionSuggest.vue'
import ToolPalette from './ToolPalette.vue'
import { useUI } from '@/stores/ui'
import { bubbleItems } from './tools'

const content = defineModel({ type: String, default: '' })
const props = defineProps({
  placeholder: { type: String, default: 'Right-click for the tools, or start writing…' },
  editable: { type: Boolean, default: true },
})

const emit = defineEmits(['change'])

const palette = ref(null)
const live = reactive({ open: false, mode: 'live' })
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

function insertStep() {
  editor.value
    ?.chain()
    .focus()
    .toggleOrderedList()
    .insertContent('<strong>What is done</strong> — responsible: role · records: document')
    .run()
}

function insertCallout(kind) {
  const lead = kind === 'warning' ? 'Warning' : 'Note'
  const body = kind === 'warning' ? 'the hazard, and what it does if ignored' : 'worth knowing'

  editor.value
    ?.chain()
    .focus()
    .toggleBlockquote()
    .insertContent(`<strong>${lead}</strong> — ${body}`)
    .run()
}

function mention(trigger) {
  editor.value?.chain().focus().insertContent(trigger).run()
}

const api = {
  insertStep,
  insertCallout,
  pickRecord: () => mention('#'),
  pickPerson: () => mention('@'),
  insertLive: () => Object.assign(live, { open: true, mode: 'live' }),
  insertCheck: () => Object.assign(live, { open: true, mode: 'check' }),
}
</script>
