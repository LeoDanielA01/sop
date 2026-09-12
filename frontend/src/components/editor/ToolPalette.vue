<script setup>
/**
 * The tools, in one of two modes.
 *
 *   Floating — summoned with a right-click (or a long press) at the pointer,
 *              showing only what suits whatever was clicked. Dismisses itself.
 *   Pinned   — docked above the document as an ordinary toolbar, and the
 *              browser's own right-click menu is handed back, so copy, paste
 *              and spellcheck work the way people expect.
 *
 * The pin is the switch between them, and it is remembered.
 */
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { Button, Tooltip } from 'frappe-ui'
import { contextAt, groupsFor } from './tools'

const props = defineProps({
  editor: { type: Object, default: null },
  api: { type: Object, required: true },
})

const pinned = defineModel('pinned', { type: Boolean, default: false })

const open = ref(false)
const palette = ref(null)
const position = ref({ left: 0, top: 0 })
const context = ref({ kind: 'empty' })

const groups = computed(() => groupsFor(context.value))

/** Keep the palette on screen, and flip it above the pointer near the bottom. */
async function showAt(x, y) {
  context.value = contextAt(props.editor)
  open.value = true
  await nextTick()

  const box = palette.value?.getBoundingClientRect()
  const width = box?.width || 280
  const height = box?.height || 200
  const margin = 8

  position.value = {
    left: Math.min(Math.max(margin, x), window.innerWidth - width - margin),
    top: y + height + margin > window.innerHeight ? Math.max(margin, y - height) : y,
  }
}

function close() {
  open.value = false
}

function onContextMenu(event) {
  if (pinned.value) return // the native menu is more useful than ours

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

function run(tool) {
  tool.run(props.editor, props.api)
  if (!pinned.value) close()
}

function onKeydown(event) {
  if (event.key === 'Escape' && open.value) close()
}

function onPointerDown(event) {
  if (open.value && palette.value && !palette.value.contains(event.target)) close()
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

<template>
  <!-- Docked. An ordinary toolbar, every group visible, nothing hidden behind a click. -->
  <div
    v-if="pinned"
    class="sticky top-0 z-10 flex flex-wrap items-center gap-1 border-b border-outline-gray-1 bg-surface-base px-1 py-1.5"
  >
    <template v-for="group in groupsFor({ kind: 'text' })" :key="group.name">
      <div class="flex items-center gap-0.5">
        <Tooltip v-for="tool in group.tools" :key="tool.label" :text="tool.hint || tool.label">
          <Button
            variant="ghost"
            :icon="tool.icon"
            :label="tool.label"
            :class="tool.active && editor && tool.active(editor) ? 'bg-surface-gray-3' : ''"
            @click="run(tool)"
          />
        </Tooltip>
      </div>
      <div class="mx-1 h-5 w-px bg-outline-gray-1" />
    </template>

    <Tooltip text="Unpin — tools follow your right-click instead">
      <Button variant="ghost" icon="lucide-pin-off" label="Unpin tools" @click="pinned = false" />
    </Tooltip>
  </div>

  <!-- Floating. Summoned where you are working, showing only what fits there. -->
  <Teleport to="body">
    <div
      v-if="open && !pinned"
      ref="palette"
      class="fixed z-50 w-64 rounded-lg border border-outline-gray-2 bg-surface-base p-1 shadow-2xl"
      :style="{ left: `${position.left}px`, top: `${position.top}px` }"
      role="menu"
    >
      <div
        class="flex items-center justify-between px-2 py-1 text-xs uppercase tracking-wide text-ink-gray-4"
      >
        <span>{{ context.kind === 'table' ? 'Table' : 'Tools' }}</span>
        <Tooltip text="Pin — keep the tools in a bar at the top">
          <Button variant="ghost" size="sm" icon="lucide-pin" label="Pin tools" @click="pinned = true" />
        </Tooltip>
      </div>

      <div v-for="group in groups" :key="group.name" class="py-0.5">
        <div class="px-2 py-1 text-xs text-ink-gray-4">{{ group.name }}</div>
        <div class="flex flex-wrap gap-0.5 px-1">
          <Tooltip v-for="tool in group.tools" :key="tool.label" :text="tool.hint || tool.label">
            <Button
              variant="ghost"
              :icon="tool.icon"
              :label="tool.label"
              :class="tool.active && editor && tool.active(editor) ? 'bg-surface-gray-3' : ''"
              @click="run(tool)"
            />
          </Tooltip>
        </div>
      </div>
    </div>
  </Teleport>
</template>
