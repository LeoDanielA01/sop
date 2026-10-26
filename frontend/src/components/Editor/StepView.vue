<template>
  <NodeViewWrapper data-sop="step" :data-phase="node.attrs.phase || null" :data-hue="node.attrs.hue || null">
    <div contenteditable="false" class="sop-step-head">
      <span class="sop-step-no" />
      <input
        v-if="editable"
        :value="node.attrs.phase"
        class="sop-step-phase-input"
        :placeholder="__('Phase')"
        list="sop-step-phases"
        @change="setPhase($event.target.value)"
        @keydown.enter.prevent="$event.target.blur()"
      />
      <span v-else-if="node.attrs.phase" class="sop-step-phase">{{ node.attrs.phase }}</span>
      <datalist id="sop-step-phases">
        <option v-for="phase in phases" :key="phase" :value="phase" />
      </datalist>
      <span class="flex-1" />
      <Tooltip v-if="editable" :text="__('Delete this step')">
        <Button variant="ghost" size="sm" icon="lucide-trash-2" @mousedown.prevent @click="deleteNode" />
      </Tooltip>
    </div>
    <NodeViewContent />
  </NodeViewWrapper>
</template>

<script setup>
import { computed } from 'vue'
import { Button, Tooltip } from 'frappe-ui'
import { NodeViewContent, NodeViewWrapper, nodeViewProps } from '@tiptap/vue-3'
import { hueOf } from './blocks'
import { translate as __ } from '@/translation'

const props = defineProps(nodeViewProps)

const editable = computed(() => props.editor.isEditable)

const phases = computed(() => {
  const found = []
  props.editor.state.doc.descendants((node) => {
    const phase = node.type.name === 'sopStep' ? node.attrs.phase : ''
    if (phase && !found.includes(phase)) found.push(phase)
    return true
  })
  return found
})

function setPhase(value) {
  const phase = (value || '').trim().toUpperCase()
  props.updateAttributes({ phase, hue: hueOf(props.editor, phase) })
}
</script>
