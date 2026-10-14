<template>
  <section
    v-if="records.length || ppe.length"
    class="mb-6 rounded-4 border border-outline-amber-2 bg-surface-amber-1"
    :aria-label="__('Safety')"
  >
    <header class="flex items-center gap-2 border-b border-outline-amber-2 px-4 py-2.5">
      <span class="lucide-shield-alert size-4 shrink-0 text-ink-amber-6" aria-hidden="true" />
      <h2 class="text-base font-semibold text-ink-gray-9">{{ __('Safety') }}</h2>
      <span class="text-sm text-ink-gray-6">{{ __('from the records this procedure uses') }}</span>
    </header>

    <div v-if="ppe.length" class="border-b border-outline-amber-2 px-4 py-3">
      <p class="mb-2 text-sm font-medium text-ink-gray-7">{{ __('Wear') }}</p>
      <div class="flex flex-wrap gap-1.5">
        <a
          v-for="item in ppe"
          :key="item.name"
          :href="item.url"
          target="_blank"
          class="inline-flex items-center gap-1.5 rounded-3 border border-outline-gray-2 bg-surface-base px-2 py-1 text-sm text-ink-gray-8 hover:border-outline-gray-3"
          :title="item.for.length ? __('Needed for {0}').format(item.for.join(', ')) : ''"
        >
          <span class="lucide-hard-hat size-3.5 text-ink-gray-5" aria-hidden="true" />
          {{ item.path }}
          <span v-if="item.standard" class="text-ink-gray-5">· {{ item.standard }}</span>
        </a>
      </div>
    </div>

    <div class="grid gap-px bg-outline-amber-2 sm:grid-cols-2">
      <div v-for="record in records" :key="record.doctype + record.name" class="bg-surface-base px-4 py-3">
        <div class="flex items-start gap-2">
          <span :class="record.icon || 'lucide-file-text'" class="mt-0.5 size-4 shrink-0 text-ink-gray-5" aria-hidden="true" />
          <div class="min-w-0 flex-1">
            <a :href="record.url" target="_blank" class="block truncate text-base font-medium text-ink-gray-9 hover:underline">
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
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed, watch } from 'vue'
import { Badge, createResource } from 'frappe-ui'
import { translate as __ } from '@/translation'

const props = defineProps({
  sop: { type: String, default: null },
  version: { type: [String, Number], default: null },
})

const safety = createResource({ url: 'sop.api.safety.for_sop' })

const records = computed(() => safety.data?.records || [])
const ppe = computed(() => safety.data?.ppe || [])

function isFile(value) {
  return typeof value === 'string' && /^\/(private\/)?files\//.test(value)
}

watch(
  () => [props.sop, props.version],
  ([sop]) => sop && safety.submit({ sop }),
  { immediate: true },
)
</script>
