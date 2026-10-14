<template>
  <PageHeader>
    <AppBreadcrumbs />
  </PageHeader>

  <div class="mx-auto w-full max-w-[1000px] px-3 pb-12 pt-4 sm:px-5">
    <h1 class="text-xl font-semibold text-ink-gray-9">{{ __('Where used') }}</h1>
    <p class="mt-1 text-base text-ink-gray-6">
      {{ __('Pick a record to see every procedure that mentions it, for example before a chemical is replaced.') }}
    </p>

    <div class="mt-5 flex flex-wrap items-center gap-2">
      <FormControl
        v-model="doctype"
        type="select"
        class="w-56"
        :options="typeOptions"
        :placeholder="__('Record type')"
        :aria-label="__('Record type')"
      />
      <Combobox
        class="w-80"
        :options="recordOptions"
        :modelValue="record"
        :loading="lookup.loading"
        :disabled="!doctype"
        :placeholder="__('Search records')"
        @update:modelValue="pick"
        @update:query="search"
      />
    </div>

    <ErrorMessage :message="usage.error?.messages?.[0]" class="mt-4" />

    <div v-if="record" class="mt-6">
      <p class="mb-2 text-sm text-ink-gray-5">
        {{
          usage.loading
            ? __('Looking…')
            : rows.length === 1
              ? __('Used in 1 procedure')
              : __('Used in {0} procedures').format(rows.length)
        }}
      </p>

      <div v-if="rows.length" class="divide-y divide-outline-gray-1 rounded-4 border border-outline-gray-2">
        <button
          v-for="row in rows"
          :key="row.name"
          type="button"
          class="flex w-full items-start gap-3 px-4 py-3 text-left hover:bg-surface-gray-1"
          @click="router.push(`/${row.name}`)"
        >
          <div class="min-w-0 flex-1">
            <p class="truncate text-base font-medium text-ink-gray-9">{{ row.title }}</p>
            <p class="mt-0.5 font-mono text-sm text-ink-gray-5">{{ row.sop_no }} · Rev {{ row.version || '—' }}</p>
            <p v-if="row.snippet" class="mt-1 line-clamp-2 text-sm text-ink-gray-6">{{ row.snippet }}</p>
          </div>
          <Badge :theme="STATUS_THEME[row.status]" variant="subtle" size="sm">{{ row.status }}</Badge>
        </button>
      </div>

      <p v-else-if="!usage.loading" class="rounded-4 border border-outline-gray-2 px-4 py-8 text-center text-base text-ink-gray-5">
        {{ __('No procedure mentions this record.') }}
      </p>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Badge, Combobox, ErrorMessage, FormControl, PageHeader, createResource } from 'frappe-ui'
import AppBreadcrumbs from '@/components/Layouts/AppBreadcrumbs.vue'
import { STATUS_THEME } from '@/utils/format'
import { translate as __ } from '@/translation'

const route = useRoute()
const router = useRouter()

const doctype = ref(route.query.doctype || '')
const record = ref(route.query.name || null)

const types = createResource({ url: 'sop.api.where_used.types', auto: true })
const lookup = createResource({ url: 'sop.api.mentions.find' })
const usage = createResource({ url: 'sop.api.where_used.find' })

const typeOptions = computed(() =>
  (types.data || []).map((row) => ({ label: row.count ? `${row.label} (${row.count})` : row.label, value: row.value })),
)

const recordOptions = computed(() => {
  const found = (lookup.data || []).map((row) => ({ label: row.label, value: row.name, description: row.hint }))
  if (record.value && !found.some((row) => row.value === record.value)) {
    found.unshift({ label: record.value, value: record.value })
  }
  return found
})

const rows = computed(() => usage.data || [])

function search(text) {
  if (doctype.value) lookup.submit({ doctype: doctype.value, text, limit: 10 })
}

function pick(value) {
  record.value = value
}

watch(doctype, (value, old) => {
  if (old !== undefined && value !== old) record.value = null
  search('')
})

watch(
  [doctype, record],
  ([type, name]) => {
    router.replace({ query: type ? { doctype: type, ...(name ? { name } : {}) } : {} })
    if (type && name) usage.submit({ doctype: type, name })
  },
  { immediate: true },
)
</script>
