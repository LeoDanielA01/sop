<template>
  <figure class="viz m-0 flex flex-col rounded-3 border border-outline-gray-2 bg-surface-base">
    <figcaption class="flex items-start gap-3 px-4 pb-2 pt-3.5">
      <div class="min-w-0 flex-1">
        <p class="text-base font-semibold text-ink-gray-9">{{ title }}</p>
        <p v-if="subtitle" class="mt-0.5 text-sm text-ink-gray-5">{{ subtitle }}</p>
      </div>

      <slot name="legend" />

      <Tooltip v-if="toggle" :text="table ? __('Show as chart') : __('Show as table')">
        <Button
          variant="ghost"
          size="sm"
          :icon="table ? 'lucide-chart-line' : 'lucide-table'"
          :label="table ? __('Show as chart') : __('Show as table')"
          @click="table = !table"
        />
      </Tooltip>
    </figcaption>

    <div class="min-w-0 flex-1 px-4 pb-4">
      <slot :table="table" />
    </div>
  </figure>
</template>

<script setup>
import { Button, Tooltip } from 'frappe-ui'
import { translate as __ } from '@/translation'

defineProps({
  title: { type: String, required: true },
  subtitle: { type: String, default: '' },
  toggle: { type: Boolean, default: true },
})

const table = defineModel('table', { type: Boolean, default: false })
</script>
