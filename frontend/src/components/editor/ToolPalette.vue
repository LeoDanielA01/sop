<template>
  <div
    v-if="pinned"
    class="sticky top-0 z-10 flex items-center gap-1 border-b border-outline-gray-1 bg-surface-base px-1.5 py-1"
  >
    <EditorFixedMenu
      v-if="editor"
      class="min-w-0 flex-1 overflow-x-auto"
      :editor="editor"
      :items="fixedItems(api)"
    />
    <Tooltip text="Unpin — the tools follow your right-click instead">
      <Button variant="ghost" icon="lucide-pin-off" label="Unpin tools" @click="pinned = false" />
    </Tooltip>
  </div>

  <Teleport to="body">
    <div
      v-if="open && !pinned && editor"
      ref="panel"
      class="fixed z-50 w-72 rounded-lg border border-outline-gray-2 bg-surface-base p-1 shadow-2xl"
      :style="{ left: `${position.left}px`, top: `${position.top}px` }"
      role="menu"
    >
      <div class="flex items-center justify-between pl-2.5">
        <span class="text-sm text-ink-gray-5">{{ groups[0]?.name || 'Tools' }}</span>
        <Tooltip text="Pin — keep the tools in a bar at the top">
          <Button variant="ghost" icon="lucide-pin" label="Pin tools" @click="pinned = true" />
        </Tooltip>
      </div>

      <div v-for="(group, index) in groups" :key="group.name" class="pb-0.5">
        <div v-if="index" class="px-2.5 pb-0.5 pt-1.5 text-sm text-ink-gray-5">
          {{ group.name }}
        </div>
        <EditorFixedMenu
          class="flex-wrap"
          :editor="editor"
          :items="group.items"
          @click="afterRun"
        />
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { Button, Tooltip } from 'frappe-ui'
import { EditorFixedMenu } from 'frappe-ui/editor'
import { contextAt, fixedItems, paletteGroups } from './tools'

const props = defineProps({
  editor: { type: Object, default: null },
  api: { type: Object, required: true },
})

const pinned = defineModel('pinned', { type: Boolean, default: false })

const open = ref(false)
const panel = ref(null)
const position = ref({ left: 0, top: 0 })
const context = ref({ kind: 'empty' })

const groups = computed(() => paletteGroups(context.value, props.api))

async function showAt(x, y) {
  context.value = contextAt(props.editor)
  open.value = true
  await nextTick()

  const box = panel.value?.getBoundingClientRect()
  const width = box?.width || 288
  const height = box?.height || 220
  const margin = 8

  position.value = {
    left: Math.min(Math.max(margin, x), window.innerWidth - width - margin),
    top: y + height + margin > window.innerHeight ? Math.max(margin, y - height) : y,
  }
}

function close() {
  open.value = false
}

function afterRun() {
  if (!pinned.value) close()
}

function onContextMenu(event) {
  if (pinned.value) return

  event.preventDefault()
  showAt(event.clientX, event.clientY)
}

let pressTimer = null

function onTouchStart(event) {
  if (pinned.value) return

  const touch = event.touches[0]
  pressTimer = setTimeout(() => showAt(touch.clientX, touch.clientY), 450)
}

function cancelPress() {
  clearTimeout(pressTimer)
}

function onKeydown(event) {
  if (event.key === 'Escape' && open.value) close()
}

function onPointerDown(event) {
  if (open.value && panel.value && !panel.value.contains(event.target)) close()
}

onMounted(() => {
  document.addEventListener('keydown', onKeydown)
  document.addEventListener('pointerdown', onPointerDown, true)
})

onBeforeUnmount(() => {
  document.removeEventListener('keydown', onKeydown)
  document.removeEventListener('pointerdown', onPointerDown, true)
  cancelPress()
})

watch(pinned, (value) => {
  if (value) close()
  localStorage.setItem('sop:editor-tools-pinned', value ? '1' : '0')
})

defineExpose({ onContextMenu, onTouchStart, cancelPress })
</script>
