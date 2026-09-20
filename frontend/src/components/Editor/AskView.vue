<template>
  <NodeViewWrapper class="my-3 overflow-hidden rounded-3 border border-outline-gray-3 bg-surface-base">
    <div
      contenteditable="false"
      class="flex items-center gap-2 border-b border-outline-gray-2 bg-surface-gray-1 px-2.5 py-1.5"
    >
      <span class="lucide-message-circle-question size-3.5 shrink-0 text-ink-gray-5" aria-hidden="true" />
      <span class="min-w-0 flex-1 truncate text-sm text-ink-gray-7">
        {{ __('A question readers answer') }}
      </span>
      <Tooltip v-if="editable" :text="__('Delete this question')">
        <Button
          variant="ghost"
          size="sm"
          icon="lucide-trash-2"
          :label="__('Delete')"
          @mousedown.prevent
          @click="deleteNode"
        />
      </Tooltip>
    </div>

    <NodeViewContent class="px-3 pt-2.5 text-base font-medium text-ink-gray-9" />

    <div
      v-if="editable"
      contenteditable="false"
      class="flex flex-wrap items-center gap-1.5 px-3 pb-2.5 pt-2"
    >
      <span
        v-for="answer in answers"
        :key="answer"
        class="inline-flex items-center gap-1 rounded-full border border-outline-gray-2 bg-surface-gray-1 py-0.5 pl-2.5 pr-1 text-sm text-ink-gray-7"
      >
        {{ answer }}
        <button
          type="button"
          class="grid size-4 place-content-center rounded-full text-ink-gray-5 hover:bg-surface-gray-3"
          :aria-label="__('Remove {0}').format(answer)"
          @mousedown.prevent
          @click="remove(answer)"
        >
          <span class="lucide-x size-3" aria-hidden="true" />
        </button>
      </span>

      <input
        v-model="draft"
        type="text"
        class="w-32 border-0 bg-transparent px-1 py-0.5 text-sm text-ink-gray-9 placeholder:text-ink-gray-4 focus:ring-0"
        :placeholder="__('Add an answer…')"
        @keydown.enter.prevent="add"
        @blur="add"
      />
    </div>

    <p v-if="!answers.length" contenteditable="false" class="px-3 pb-2.5 text-sm text-ink-amber-6">
      {{ __('Add the answers, then wrap what follows each one in a branch.') }}
    </p>
  </NodeViewWrapper>
</template>

<script setup>
import { computed, ref } from 'vue'
import { Button, Tooltip } from 'frappe-ui'
import { NodeViewContent, NodeViewWrapper, nodeViewProps } from '@tiptap/vue-3'
import { SEPARATOR, answersOf } from '@/data/flow'
import { translate as __ } from '@/translation'

const props = defineProps(nodeViewProps)

const draft = ref('')
const editable = computed(() => props.editor.isEditable)

const answers = computed(() => answersOf(props.node.attrs.options))

function save(list) {
  props.updateAttributes({ options: list.join(SEPARATOR) })
}

function add() {
  const value = draft.value.trim()
  draft.value = ''

  if (!value || value.includes(SEPARATOR) || answers.value.includes(value)) return

  save([...answers.value, value])
}

function remove(answer) {
  save(answers.value.filter((row) => row !== answer))
}
</script>
