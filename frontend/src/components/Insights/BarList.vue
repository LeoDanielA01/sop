<template>
  <table v-if="table" class="w-full text-sm">
    <thead>
      <tr class="border-b border-outline-gray-2 text-left text-ink-gray-6">
        <th class="py-1.5 pr-3 font-medium">{{ labelHeading }}</th>
        <th class="py-1.5 text-right font-medium">{{ valueHeading }}</th>
      </tr>
    </thead>
    <tbody>
      <tr v-for="row in rows" :key="row.label" class="border-b border-outline-gray-1 last:border-0">
        <td class="py-1 pr-3 text-ink-gray-7">{{ row.label }}</td>
        <td class="py-1 text-right tabular-nums text-ink-gray-8">{{ row.value }}</td>
      </tr>
    </tbody>
  </table>

  <ul v-else class="flex flex-col gap-1" role="list">
    <li v-for="row in rows" :key="row.label">
      <Tooltip :text="`${row.label}: ${row.value}`">
        <div
          tabindex="0"
          class="group grid w-full grid-cols-[8.5rem_1fr] items-center gap-3 rounded-2 px-1 py-1 hover:bg-surface-gray-1 focus-visible:bg-surface-gray-1 focus-visible:outline-none"
          :aria-label="`${row.label}: ${row.value}`"
        >
          <span class="truncate text-sm text-ink-gray-7">{{ row.label }}</span>
          <span class="flex min-w-0 items-center gap-2">
            <span
              v-if="row.value"
              class="h-3 shrink-0 rounded-r-[4px] transition-opacity group-hover:opacity-80"
              :style="{ width: `${(row.value / highest) * 85}%`, minWidth: '4px', background: 'var(--viz-1)' }"
            />
            <span class="text-sm font-medium tabular-nums text-ink-gray-8">{{ row.value }}</span>
          </span>
        </div>
      </Tooltip>
    </li>
  </ul>
</template>

<script setup>
import { computed } from 'vue'
import { Tooltip } from 'frappe-ui'

const props = defineProps({
  rows: { type: Array, default: () => [] },
  table: { type: Boolean, default: false },
  labelHeading: { type: String, default: '' },
  valueHeading: { type: String, default: '' },
})

const highest = computed(() => Math.max(1, ...props.rows.map((row) => row.value)))
</script>
