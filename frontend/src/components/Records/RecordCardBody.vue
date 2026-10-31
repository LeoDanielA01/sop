<template>
  <div class="flex items-start gap-2.5">
    <Avatar :image="info.image" :label="info.title" size="xl" shape="square" />
    <div class="min-w-0 flex-1">
      <p class="truncate text-base font-medium text-ink-gray-9">{{ info.title }}</p>
      <p class="truncate text-sm text-ink-gray-5">{{ info.doctype }} · {{ info.name }}</p>
    </div>
    <Badge v-if="info.status" :theme="info.status_tone" variant="subtle" size="sm">
      {{ info.status }}
    </Badge>
  </div>

  <dl v-if="info.facts?.length" class="mt-3 divide-y divide-outline-gray-1 border-t border-outline-gray-1">
    <div v-for="fact in info.facts" :key="fact.label" class="flex items-center justify-between gap-3 py-1.5">
      <dt class="shrink-0 text-sm text-ink-gray-5">{{ fact.label }}</dt>
      <dd class="min-w-0 truncate text-right text-sm text-ink-gray-8">
        <Badge v-if="fact.tone && fact.tone !== 'gray'" :theme="fact.tone" variant="subtle" size="sm">
          {{ fact.value }}
        </Badge>
        <template v-else>{{ fact.value }}</template>
      </dd>
    </div>
  </dl>

  <div v-if="stock" class="mt-3 border-t border-outline-gray-1 pt-2">
    <p class="mb-1 text-sm font-medium text-ink-gray-7">{{ stock.title }}</p>
    <table v-if="stock.rows.length" class="w-full text-sm">
      <thead>
        <tr class="text-xs text-ink-gray-5">
          <th class="py-0.5 text-left font-normal">{{ __('Warehouse') }}</th>
          <th class="py-0.5 text-right font-normal">{{ __('On hand') }}</th>
          <th class="py-0.5 text-right font-normal">{{ __('Projected') }}</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="row in stock.rows.slice(0, SHOWN)" :key="row.warehouse">
          <td class="max-w-[9rem] truncate py-0.5 text-ink-gray-8" :title="row.warehouse">{{ row.warehouse }}</td>
          <td class="py-0.5 text-right tabular-nums" :class="row.on_hand <= 0 ? 'text-ink-red-4' : 'text-ink-gray-8'">{{ number(row.on_hand) }}</td>
          <td class="py-0.5 text-right tabular-nums" :class="row.projected < 0 ? 'text-ink-red-4' : 'text-ink-gray-6'">{{ number(row.projected) }}</td>
        </tr>
        <tr v-if="stock.rows.length > 1" class="border-t border-outline-gray-1 font-medium">
          <td class="py-0.5 text-ink-gray-7">
            {{ stock.rows.length > SHOWN ? __('Total ({0} warehouses)').format(stock.rows.length) : __('Total') }}
          </td>
          <td class="py-0.5 text-right tabular-nums text-ink-gray-9">{{ number(stock.totals.on_hand) }} {{ stock.uom }}</td>
          <td class="py-0.5 text-right tabular-nums text-ink-gray-7">{{ number(stock.totals.projected) }}</td>
        </tr>
      </tbody>
    </table>
    <p v-else class="text-sm text-ink-gray-5">{{ __('No stock in any warehouse.') }}</p>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { Avatar, Badge } from 'frappe-ui'
import { translate as __ } from '@/translation'

const props = defineProps({
  info: { type: Object, required: true },
})

const SHOWN = 5

const stock = computed(() => (props.info.sections || []).find((section) => section.key === 'stock_by_warehouse') || null)

function number(value) {
  return new Intl.NumberFormat(undefined, { maximumFractionDigits: 3 }).format(Number(value) || 0)
}
</script>
