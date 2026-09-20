<template>
  <NodeViewWrapper
    class="my-3 overflow-hidden rounded-3 border border-dashed border-outline-gray-3 bg-surface-gray-1"
  >
    <div
      contenteditable="false"
      class="flex items-center gap-2 border-b border-outline-gray-2 px-2.5 py-1.5"
    >
      <span
        :class="spec?.kind === 'ask' ? 'lucide-message-circle-question' : 'lucide-git-branch'"
        class="size-3.5 shrink-0 text-ink-gray-5"
        aria-hidden="true"
      />

      <span class="min-w-0 flex-1 truncate text-sm" :class="label ? 'text-ink-gray-7' : 'text-ink-amber-6'">
        {{ label ? __('Only when {0}').format(label) : __('No condition set — this always shows') }}
      </span>

      <Tooltip v-if="editable" :text="__('Change the condition')">
        <Button variant="ghost" size="sm" icon="lucide-pencil" :label="__('Change')" @mousedown.prevent @click="edit" />
      </Tooltip>
      <Tooltip v-if="editable" :text="__('Always show this')">
        <Button variant="ghost" size="sm" icon="lucide-ungroup" :label="__('Always show')" @mousedown.prevent @click="unwrap" />
      </Tooltip>
      <Tooltip v-if="editable" :text="__('Delete this branch')">
        <Button variant="ghost" size="sm" icon="lucide-trash-2" :label="__('Delete')" @mousedown.prevent @click="deleteNode" />
      </Tooltip>
    </div>

    <NodeViewContent class="prose-sop px-3 py-2" />
  </NodeViewWrapper>
</template>

<script setup>
import { computed } from 'vue'
import { Button, Tooltip } from 'frappe-ui'
import { NodeViewContent, NodeViewWrapper, nodeViewProps } from '@tiptap/vue-3'
import { askFlowEdit, parseCondition } from '@/data/flow'
import { translate as __ } from '@/translation'

const props = defineProps(nodeViewProps)

const editable = computed(() => props.editor.isEditable)
const label = computed(() => props.node.attrs.label)
const spec = computed(() => parseCondition(props.node.attrs.when))

function edit() {
  askFlowEdit({
    editor: props.editor,
    when: props.node.attrs.when,
    apply: (attrs) => props.updateAttributes(attrs),
  })
}

function unwrap() {
  const from = props.getPos()
  if (typeof from !== 'number') return

  const node = props.node

  props.editor
    .chain()
    .focus()
    .command(({ tr }) => {
      tr.replaceWith(from, from + node.nodeSize, node.content)
      return true
    })
    .run()
}
</script>
