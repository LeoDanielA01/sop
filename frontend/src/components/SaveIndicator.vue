<template>
  <div class="flex items-center gap-1.5">
    <template v-if="error">
      <Tooltip :text="error">
        <span class="flex items-center gap-1.5 text-sm text-ink-red-3">
          <span class="lucide-triangle-alert size-3.5" aria-hidden="true" />
          Not saved
        </span>
      </Tooltip>
      <Button variant="ghost" size="sm" label="Try again" @click="emit('retry')" />
    </template>

    <span v-else-if="loading" class="flex items-center gap-1.5 text-sm text-ink-gray-5">
      <span class="lucide-loader-circle size-3.5 animate-spin" aria-hidden="true" />
      Saving
    </span>

    <Tooltip v-else-if="dirty" :text="hint">
      <span class="flex items-center gap-1.5 text-sm text-ink-gray-5">
        <span class="size-1.5 rounded-full bg-surface-amber-3" aria-hidden="true" />
        Unsaved changes
      </span>
    </Tooltip>

    <Tooltip v-else-if="savedAt" :text="stamp">
      <span class="flex items-center gap-1.5 text-sm text-ink-gray-5">
        <span class="lucide-check size-3.5 text-ink-green-3" aria-hidden="true" />
        Saved {{ ago }}
      </span>
    </Tooltip>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { Button, Tooltip } from 'frappe-ui'

const props = defineProps({
  loading: { type: Boolean, default: false },
  dirty: { type: Boolean, default: false },
  savedAt: { type: Date, default: null },
  error: { type: String, default: '' },
  autosave: { type: Boolean, default: true },
})

const emit = defineEmits(['retry'])

const hint = computed(() =>
  props.autosave
    ? 'It saves on its own, or press Ctrl+S'
    : 'Saving as you type is off — press Ctrl+S or Save draft',
)

const now = ref(Date.now())
let timer = null

const ago = computed(() => {
  if (!props.savedAt) return ''

  const seconds = Math.max(0, Math.round((now.value - props.savedAt.getTime()) / 1000))
  if (seconds < 45) return 'just now'

  const minutes = Math.round(seconds / 60)
  if (minutes < 60) return `${minutes} min ago`

  const hours = Math.round(minutes / 60)
  return hours === 1 ? 'an hour ago' : `${hours} hours ago`
})

const stamp = computed(() =>
  props.savedAt
    ? `Last saved at ${props.savedAt.toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' })}`
    : '',
)

onMounted(() => {
  timer = setInterval(() => (now.value = Date.now()), 20000)
})

onBeforeUnmount(() => clearInterval(timer))
</script>
