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
    <Tooltip :text="__('Unpin — the tools follow your right-click instead')">
      <Button variant="ghost" icon="lucide-pin-off" :label="__('Unpin tools')" @click="pinned = false" />
    </Tooltip>
  </div>

  <Teleport to="body">
    <div
      v-if="open && !pinned && editor"
      ref="panel"
      class="fixed z-50 flex w-80 flex-col overflow-hidden rounded-4 border border-outline-gray-2 bg-surface-base shadow-2xl"
      :style="{ left: `${position.left}px`, top: `${position.top}px` }"
      role="menu"
    >
      <div class="flex items-center gap-1 border-b border-outline-gray-1 px-2 py-1.5">
        <span class="lucide-search size-4 shrink-0 text-ink-gray-5" aria-hidden="true" />
        <input
          ref="search"
          v-model="query"
          type="text"
          :placeholder="__('Find a tool')"
          class="min-w-0 flex-1 border-0 bg-transparent p-0 text-base text-ink-gray-8 placeholder:text-ink-gray-4 focus:outline-none focus:ring-0"
          @keydown.down.prevent="move(1)"
          @keydown.up.prevent="move(-1)"
          @keydown.enter.prevent="run(flat[cursor])"
          @keydown.esc.prevent="close"
        />
        <Tooltip :text="__('Pin — keep the tools in a bar at the top')">
          <Button variant="ghost" icon="lucide-pin" :label="__('Pin tools')" @click="pinned = true" />
        </Tooltip>
      </div>

      <div ref="list" class="max-h-80 overflow-y-auto py-1">
        <div v-for="group in groups" :key="group.name">
          <p class="px-3 pb-0.5 pt-1.5 text-sm text-ink-gray-5">{{ group.name }}</p>

          <button
            v-for="item in group.items"
            :key="item.key"
            type="button"
            :data-index="indexOf(item)"
            class="flex w-full items-center gap-2.5 px-2 py-1.5 text-left"
            :class="
              indexOf(item) === cursor ? 'bg-surface-gray-2' : 'hover:bg-surface-gray-1'
            "
            @mousemove="cursor = indexOf(item)"
            @click="run(item)"
          >
            <span
              class="grid size-6 shrink-0 place-content-center rounded-3 border border-outline-gray-2"
              :class="isOn(item) ? 'bg-surface-gray-4' : 'bg-surface-gray-1'"
            >
              <span :class="item.icon" class="size-3.5 text-ink-gray-7" aria-hidden="true" />
            </span>

            <span class="min-w-0 flex-1">
              <span class="block truncate text-base text-ink-gray-8">{{ item.label }}</span>
              <span v-if="item.hint && !isShortcut(item)" class="block truncate text-sm text-ink-gray-5">
                {{ item.hint }}
              </span>
            </span>

            <kbd
              v-if="isShortcut(item)"
              class="shrink-0 rounded-3 bg-surface-gray-2 px-1.5 py-0.5 font-mono text-xs text-ink-gray-6"
            >
              {{ item.hint }}
            </kbd>
            <span
              v-else-if="isOn(item)"
              class="lucide-check size-4 shrink-0 text-ink-gray-7"
              aria-hidden="true"
            />
          </button>
        </div>

        <p v-if="!flat.length" class="px-3 py-6 text-center text-sm text-ink-gray-5">
          Nothing matches “{{ query }}”.
        </p>
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
const search = ref(null)
const list = ref(null)
const query = ref('')
const cursor = ref(0)
const position = ref({ left: 0, top: 0 })
const context = ref({ kind: 'empty' })

const all = computed(() => paletteGroups(context.value, props.api, props.editor))

const groups = computed(() => {
  const text = query.value.trim().toLowerCase()
  if (!text) return all.value

  return all.value
    .map((group) => ({
      name: group.name,
      items: group.items.filter((item) => item.label.toLowerCase().includes(text)),
    }))
    .filter((group) => group.items.length)
})

const flat = computed(() => groups.value.flatMap((group) => group.items))

function indexOf(item) {
  return flat.value.indexOf(item)
}

function isOn(item) {
  return !!(item.active && props.editor && item.active(props.editor))
}

function isShortcut(item) {
  return !!item.hint && item.hint.length <= 10
}

function move(step) {
  if (!flat.value.length) return

  cursor.value = (cursor.value + step + flat.value.length) % flat.value.length

  nextTick(() => {
    list.value
      ?.querySelector(`[data-index="${cursor.value}"]`)
      ?.scrollIntoView({ block: 'nearest' })
  })
}

function run(item) {
  if (!item) return

  item.run(props.editor, props.api)
  close()
}

async function showAt(x, y) {
  context.value = contextAt(props.editor)
  query.value = ''
  cursor.value = 0
  open.value = true
  await nextTick()

  const box = panel.value?.getBoundingClientRect()
  const width = box?.width || 320
  const height = box?.height || 320
  const margin = 8

  position.value = {
    left: Math.min(Math.max(margin, x), window.innerWidth - width - margin),
    top: y + height + margin > window.innerHeight ? Math.max(margin, y - height) : y,
  }

  search.value?.focus()
}

function close() {
  open.value = false
  query.value = ''
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

watch(query, () => (cursor.value = 0))

watch(pinned, (value) => {
  if (value) close()
})

onMounted(() => {
  document.addEventListener('keydown', onKeydown)
  document.addEventListener('pointerdown', onPointerDown, true)
})

onBeforeUnmount(() => {
  document.removeEventListener('keydown', onKeydown)
  document.removeEventListener('pointerdown', onPointerDown, true)
  cancelPress()
})

defineExpose({ onContextMenu, onTouchStart, cancelPress })
</script>
