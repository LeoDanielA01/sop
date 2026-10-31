<template>
  <PageHeader>
    <AppBreadcrumbs :tail="[{ label: data?.type_label || route.params.doctype }]" />
  </PageHeader>

  <div class="mx-auto w-full max-w-[1000px] px-3 pb-12 pt-4 sm:px-5">
    <div class="flex flex-wrap items-center gap-3">
      <span :class="data?.icon || 'lucide-list'" class="size-5 text-ink-gray-5" aria-hidden="true" />
      <h1 class="text-xl font-semibold text-ink-gray-9">{{ data?.type_label || route.params.doctype }}</h1>
      <Badge v-for="(value, key) in filters" :key="key" theme="gray" variant="subtle" size="md">
        {{ value }}
        <button type="button" class="ml-1 text-ink-gray-5 hover:text-ink-gray-8" :aria-label="__('Remove filter')" @click="clearFilter(key)">
          <span class="lucide-x size-3" aria-hidden="true" />
        </button>
      </Badge>
      <TextInput v-model="search" class="ml-auto w-64" type="search" :placeholder="__('Search')" :aria-label="__('Search')">
        <template #prefix><span class="lucide-search size-4 text-ink-gray-5" aria-hidden="true" /></template>
      </TextInput>
    </div>

    <ErrorMessage :message="list.error?.messages?.[0]" class="mt-4" />

    <div class="mt-4 overflow-hidden rounded-4 border border-outline-gray-2">
      <div class="overflow-x-auto">
        <table class="w-full min-w-[640px] text-base">
          <thead>
            <tr class="border-b border-outline-gray-2 bg-surface-gray-1 text-left text-sm text-ink-gray-5">
              <th class="px-3 py-2 font-medium">{{ __('Name') }}</th>
              <th v-for="column in data?.columns || []" :key="column.key" class="px-3 py-2 font-medium">{{ column.label }}</th>
              <th class="px-3 py-2 font-medium" />
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="row in rows"
              :key="row.name"
              class="cursor-pointer border-b border-outline-gray-1 last:border-0 hover:bg-surface-gray-1"
              @click="router.push(recordPath(route.params.doctype, row.name))"
            >
              <td class="max-w-[320px] px-3 py-2">
                <div class="flex items-center gap-2.5">
                  <img v-if="row.image" :src="row.image" alt="" class="size-8 shrink-0 rounded-3 object-cover" />
                  <div class="min-w-0">
                    <p class="truncate font-medium text-ink-gray-9">{{ row.title }}</p>
                    <p v-if="row.title !== row.name" class="truncate font-mono text-sm text-ink-gray-5">{{ row.name }}</p>
                  </div>
                </div>
              </td>
              <td v-for="column in data?.columns || []" :key="column.key" class="max-w-[220px] truncate px-3 py-2 text-ink-gray-7">
                {{ row.values[column.key] }}
              </td>
              <td class="px-3 py-2 text-right">
                <Badge v-if="row.status" :theme="row.status_tone || 'gray'" variant="subtle" size="sm">{{ row.status }}</Badge>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <p v-if="list.loading && !rows.length" class="px-3 py-6 text-center text-base text-ink-gray-5">{{ __('Loading…') }}</p>
      <p v-else-if="!rows.length" class="px-3 py-6 text-center text-base text-ink-gray-5">{{ __('Nothing found.') }}</p>
    </div>

    <div v-if="data?.more" class="mt-4 flex justify-center">
      <Button :label="__('Load more')" :loading="list.loading" @click="loadMore" />
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Badge, Button, ErrorMessage, PageHeader, TextInput, createResource, debounce } from 'frappe-ui'
import AppBreadcrumbs from '@/components/Layouts/AppBreadcrumbs.vue'
import { recordPath } from '@/utils/records'
import { translate as __ } from '@/translation'

const route = useRoute()
const router = useRouter()

const search = ref(route.query.q || '')
const rows = ref([])
const filters = computed(() => Object.fromEntries(Object.entries(route.query).filter(([key, value]) => key !== 'q' && value)))

let offset = 0

const list = createResource({
  url: 'sop.api.records.get_list',
  onSuccess(result) {
    rows.value = offset ? [...rows.value, ...result.rows] : result.rows
  },
})

const data = computed(() => list.data || null)

function load(start = 0) {
  offset = start
  list.submit({
    doctype: route.params.doctype,
    search: search.value || null,
    filters: JSON.stringify(filters.value),
    start,
  })
}

function loadMore() {
  load(rows.value.length)
}

function clearFilter(key) {
  const query = { ...route.query }
  delete query[key]
  router.replace({ query })
}

const searchLater = debounce(() => {
  router.replace({ query: { ...route.query, q: search.value || undefined } })
}, 300)

watch(search, searchLater)

watch(
  () => [route.params.doctype, JSON.stringify(route.query)],
  ([doctype]) => {
    if (!doctype) return
    search.value = route.query.q || ''
    load(0)
  },
  { immediate: true },
)
</script>
