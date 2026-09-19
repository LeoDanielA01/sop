<template>
  <div class="flex flex-col rounded-3 border border-outline-gray-2 bg-surface-base px-4 py-3.5">
    <p class="flex items-center gap-1.5 text-sm text-ink-gray-6">
      <span :class="icon" class="size-4 shrink-0 text-ink-gray-5" aria-hidden="true" />
      {{ label }}
    </p>

    <p class="mt-1.5 flex items-baseline gap-1.5">
      <span class="text-3xl font-semibold text-ink-gray-9">{{ value ?? '—' }}</span>
      <span v-if="unit && value !== null && value !== undefined" class="text-base text-ink-gray-5">{{ unit }}</span>
    </p>

    <div
      v-if="meter !== null && meter !== undefined"
      class="mt-2.5 h-1.5 w-full overflow-hidden rounded-full"
      :style="{ background: `color-mix(in srgb, ${fill} 18%, transparent)` }"
      role="meter"
      :aria-label="label"
      :aria-valuenow="meter"
      aria-valuemin="0"
      aria-valuemax="100"
    >
      <div class="h-full rounded-full" :style="{ width: `${Math.max(0, Math.min(100, meter))}%`, background: fill }" />
    </div>

    <p class="mt-2 flex items-center gap-1.5 text-sm">
      <span v-if="state" :class="stateIcon" class="size-3.5 shrink-0" aria-hidden="true" />
      <span class="text-ink-gray-6">{{ detail }}</span>
    </p>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  label: { type: String, required: true },
  value: { type: [String, Number, null], default: null },
  unit: { type: String, default: '' },
  detail: { type: String, default: '' },
  icon: { type: String, default: 'lucide-activity' },
  meter: { type: [Number, null], default: null },
  state: { type: String, default: '' },
})

const STATUS = {
  good: { color: 'var(--ink-green-3)', icon: 'lucide-circle-check text-ink-green-3' },
  warning: { color: 'var(--ink-amber-3, #fab219)', icon: 'lucide-triangle-alert text-ink-amber-6' },
  critical: { color: 'var(--ink-red-3)', icon: 'lucide-circle-alert text-ink-red-3' },
}

const fill = computed(() => STATUS[props.state]?.color || 'var(--viz-1)')

const stateIcon = computed(() => STATUS[props.state]?.icon || '')
</script>
