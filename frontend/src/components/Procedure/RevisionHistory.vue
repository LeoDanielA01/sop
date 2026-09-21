<template>
  <section v-if="revisions.length" :class="print ? 'sop-print-section' : 'mt-10 border-t border-outline-gray-1 pt-5'">
    <h2 :class="print ? '' : 'mb-3 text-base font-semibold text-ink-gray-9'">{{ __('Revision history') }}</h2>

    <div :class="print ? '' : '-mx-1 overflow-x-auto'">
      <table :class="print ? 'sop-print-table' : 'w-full min-w-[34rem] text-left text-sm'">
        <thead :class="print ? '' : 'text-ink-gray-5'">
          <tr>
            <th :class="cell">{{ __('Rev') }}</th>
            <th :class="cell">{{ __('In force from') }}</th>
            <th :class="cell">{{ __('What changed') }}</th>
            <th :class="cell">{{ __('Approved by') }}</th>
          </tr>
        </thead>
        <tbody :class="print ? '' : 'text-ink-gray-8'">
          <tr
            v-for="row in revisions"
            :key="row.version"
            :class="print ? '' : 'border-t border-outline-gray-1 align-top'"
          >
            <td :class="cell" class="whitespace-nowrap font-medium">
              {{ row.version }}
              <span v-if="row.version === current" :class="print ? '' : 'ml-1 text-xs font-normal text-ink-green-3'">
                {{ __('in force') }}
              </span>
            </td>
            <td :class="cell" class="whitespace-nowrap">{{ shortDate(row.effective_from) || '—' }}</td>
            <td :class="cell">
              {{ row.change_summary || __('Not recorded') }}
              <span v-if="row.is_material" :class="print ? '' : 'ml-1 text-xs text-ink-amber-6'">
                · {{ __('material') }}
              </span>
            </td>
            <td :class="cell">{{ row.approved_by?.length ? row.approved_by.join(', ') : '—' }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>
</template>

<script setup>
import { computed } from 'vue'
import { shortDate } from '@/utils/format'
import { translate as __ } from '@/translation'

const props = defineProps({
  revisions: { type: Array, default: () => [] },
  current: { type: [Number, String, null], default: null },
  print: { type: Boolean, default: false },
})

const cell = computed(() => (props.print ? '' : 'px-1 py-2'))
</script>
