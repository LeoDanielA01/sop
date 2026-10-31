<template>
  <section
    v-if="records.length || related.length"
    class="mb-6 rounded-4 border border-outline-amber-2 bg-surface-amber-1"
    :aria-label="__('Before you start')"
  >
    <header class="flex items-center gap-2 border-b border-outline-amber-2 px-4 py-2.5">
      <span class="lucide-clipboard-list size-4 shrink-0 text-ink-amber-6" aria-hidden="true" />
      <h2 class="text-base font-semibold text-ink-gray-9">{{ __('Before you start') }}</h2>
      <span class="text-sm text-ink-gray-6">{{ __('from the records this procedure uses') }}</span>
    </header>

    <div v-if="related.length" class="border-b border-outline-amber-2 px-4 py-3">
      <p class="mb-2 text-sm font-medium text-ink-gray-7">{{ __('Also needed') }}</p>
      <div class="flex flex-wrap gap-1.5">
        <RecordHover v-for="item in related" :key="item.doctype + item.name" :doctype="item.doctype" :name="item.name">
          <a
            :href="item.url"
            :target="isAppUrl(item.url) ? undefined : '_blank'"
            class="inline-flex items-center gap-1.5 rounded-3 border border-outline-gray-2 bg-surface-base px-2 py-1 text-sm text-ink-gray-8 hover:border-outline-gray-3"
            @click="followLink(router, $event, item.url)"
            :title="item.for.length ? __('Needed for {0}').format(item.for.join(', ')) : ''"
          >
            <span :class="item.icon || 'lucide-box'" class="size-3.5 text-ink-gray-5" aria-hidden="true" />
            {{ item.path }}
            <span class="text-ink-gray-5">· {{ item.type_label }}</span>
          </a>
        </RecordHover>
      </div>
    </div>

    <div class="grid gap-px bg-outline-amber-2 sm:grid-cols-2">
      <div v-for="record in records" :key="record.doctype + record.name" class="bg-surface-base px-4 py-3">
        <div class="flex items-start gap-2">
          <span :class="record.icon || 'lucide-file-text'" class="mt-0.5 size-4 shrink-0 text-ink-gray-5" aria-hidden="true" />
          <div class="min-w-0 flex-1">
            <a
              :href="record.url"
              :target="isAppUrl(record.url) ? undefined : '_blank'"
              class="block truncate text-base font-medium text-ink-gray-9 hover:underline"
              @click="followLink(router, $event, record.url)"
            >
              {{ record.title }}
            </a>
            <p class="truncate text-sm text-ink-gray-5">{{ record.type_label }}</p>
          </div>
          <Badge v-if="record.status" :theme="record.status_tone" variant="subtle" size="sm">{{ record.status }}</Badge>
        </div>

        <dl v-if="record.facts.length" class="mt-2 space-y-1.5">
          <div v-for="fact in record.facts" :key="fact.label">
            <dt class="text-sm text-ink-gray-5">{{ fact.label }}</dt>
            <dd class="text-sm text-ink-gray-8">
              <a v-if="isFile(fact.value)" :href="fact.value" target="_blank" class="inline-flex items-center gap-1 text-ink-blue-3 hover:underline">
                <span class="lucide-file-down size-3.5" aria-hidden="true" />{{ __('Open') }}
              </a>
              <Badge v-else-if="fact.tone && fact.tone !== 'gray'" :theme="fact.tone" variant="subtle" size="sm">
                {{ fact.value }}
              </Badge>
              <span v-else class="whitespace-pre-line">{{ fact.value }}</span>
            </dd>
          </div>
        </dl>

        <div v-if="stockOf(record)" class="mt-2">
          <p class="text-sm text-ink-gray-5">{{ stockOf(record).title }}</p>
          <ul v-if="stockOf(record).rows.length" class="mt-0.5 space-y-0.5 text-sm">
            <li v-for="row in stockOf(record).rows" :key="row.warehouse" class="flex justify-between gap-3">
              <span class="truncate text-ink-gray-8">{{ row.warehouse }}</span>
              <span class="tabular-nums" :class="row.on_hand <= 0 ? 'text-ink-red-4' : 'text-ink-gray-8'">{{ number(row.on_hand) }}</span>
            </li>
            <li v-if="stockOf(record).rows.length > 1" class="flex justify-between gap-3 border-t border-outline-gray-1 pt-0.5 font-medium">
              <span class="text-ink-gray-7">{{ __('Total') }}</span>
              <span class="tabular-nums text-ink-gray-9">{{ number(stockOf(record).totals.on_hand) }} {{ stockOf(record).uom }}</span>
            </li>
          </ul>
          <p v-else class="text-sm text-ink-red-4">{{ __('No stock in any warehouse.') }}</p>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { Badge, createResource } from 'frappe-ui'
import { followLink, isAppUrl } from '@/utils/records'
import RecordHover from '@/components/Records/RecordHover.vue'
import { translate as __ } from '@/translation'

const router = useRouter()

const props = defineProps({
  sop: { type: String, default: null },
  version: { type: [String, Number], default: null },
})

const safety = createResource({ url: 'sop.api.safety.for_sop' })

const records = computed(() => safety.data?.records || [])
const related = computed(() => safety.data?.related || [])

function stockOf(record) {
  return (record.sections || []).find((section) => section.key === 'stock_by_warehouse') || null
}

function number(value) {
  return new Intl.NumberFormat(undefined, { maximumFractionDigits: 3 }).format(Number(value) || 0)
}

function isFile(value) {
  return typeof value === 'string' && /^\/(private\/)?files\//.test(value)
}

watch(
  () => [props.sop, props.version],
  ([sop]) => sop && safety.submit({ sop }),
  { immediate: true },
)
</script>
