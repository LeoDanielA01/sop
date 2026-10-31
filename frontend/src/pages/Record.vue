<template>
  <PageHeader>
    <AppBreadcrumbs :tail="crumbs" />
  </PageHeader>

  <div class="mx-auto w-full max-w-[1000px] px-3 pb-12 pt-4 sm:px-5">
    <div v-if="record.loading && !info" class="flex flex-col gap-3">
      <Skeleton class="h-7 w-1/2" />
      <Skeleton class="h-4 w-1/3" />
      <Skeleton class="h-40 w-full" />
    </div>

    <ErrorMessage v-else-if="record.error" :message="record.error.messages?.[0] || __('Could not load this record.')" />

    <p v-else-if="info?.missing" class="py-10 text-center text-base text-ink-gray-5">{{ __('This record no longer exists.') }}</p>
    <p v-else-if="info?.blocked" class="py-10 text-center text-base text-ink-gray-5">{{ __('You are not allowed to see this record.') }}</p>

    <template v-else-if="info">
      <header class="flex items-start gap-4">
        <img
          v-if="info.image"
          :src="info.image"
          :alt="info.title"
          class="size-16 shrink-0 rounded-4 border border-outline-gray-2 object-cover"
        />
        <span
          v-else
          class="flex size-16 shrink-0 items-center justify-center rounded-4 border border-outline-gray-2 bg-surface-gray-1"
        >
          <span :class="info.icon || 'lucide-file-text'" class="size-6 text-ink-gray-5" aria-hidden="true" />
        </span>
        <div class="min-w-0 flex-1">
          <div class="flex flex-wrap items-center gap-2">
            <h1 class="truncate text-xl font-semibold text-ink-gray-9">{{ info.title }}</h1>
            <Badge v-if="info.status" :theme="info.status_tone || 'gray'" variant="subtle" size="md">{{ info.status }}</Badge>
          </div>
          <p class="mt-1 text-base text-ink-gray-6">
            <router-link :to="listPath(info.doctype)" class="hover:underline">{{ info.type_label }}</router-link>
            <span v-if="info.name !== info.title" class="font-mono text-sm text-ink-gray-5"> · {{ info.name }}</span>
          </p>
        </div>
      </header>

      <div v-if="info.facts?.length" class="mt-5 grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
        <div v-for="fact in info.facts" :key="fact.label" class="rounded-4 border border-outline-gray-2 px-3 py-2.5">
          <p class="text-sm text-ink-gray-5">{{ fact.label }}</p>
          <p class="mt-0.5 text-base">
            <Badge v-if="fact.tone && fact.tone !== 'gray'" :theme="fact.tone" variant="subtle" size="md">{{ fact.value }}</Badge>
            <span v-else class="whitespace-pre-line text-ink-gray-9">{{ fact.value }}</span>
          </p>
        </div>
      </div>

      <section v-for="section in info.sections || []" :key="section.key" class="mt-6">
        <h2 class="mb-2 text-base font-semibold text-ink-gray-9">{{ section.title }}</h2>
        <div v-if="section.key === 'stock_by_warehouse'" class="overflow-hidden rounded-4 border border-outline-gray-2">
          <div class="overflow-x-auto">
            <table v-if="section.rows.length" class="w-full min-w-[640px] text-base">
              <thead>
                <tr class="border-b border-outline-gray-2 bg-surface-gray-1 text-left text-sm text-ink-gray-5">
                  <th class="px-3 py-2 font-medium">{{ __('Warehouse') }}</th>
                  <th class="px-3 py-2 text-right font-medium">{{ __('On hand') }}</th>
                  <th class="px-3 py-2 text-right font-medium">{{ __('Reserved') }}</th>
                  <th class="px-3 py-2 text-right font-medium">{{ __('Incoming') }}</th>
                  <th class="px-3 py-2 text-right font-medium">{{ __('Projected') }}</th>
                  <th class="px-3 py-2 text-right font-medium">{{ __('Value') }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="row in section.rows" :key="row.warehouse" class="border-b border-outline-gray-1 last:border-0">
                  <td class="px-3 py-2">
                    <RecordHover doctype="Warehouse" :name="row.warehouse">
                      <a :href="row.warehouse_url" class="text-ink-gray-8 hover:underline" @click="followLink(router, $event, row.warehouse_url)">
                        {{ row.warehouse }}
                      </a>
                    </RecordHover>
                  </td>
                  <td class="px-3 py-2 text-right tabular-nums" :class="row.on_hand <= 0 ? 'text-ink-red-4' : 'text-ink-gray-9'">
                    {{ number(row.on_hand) }} <span class="text-sm text-ink-gray-5">{{ section.uom }}</span>
                  </td>
                  <td class="px-3 py-2 text-right tabular-nums text-ink-gray-7">{{ number(row.reserved) }}</td>
                  <td class="px-3 py-2 text-right tabular-nums text-ink-gray-7">{{ number(row.incoming) }}</td>
                  <td class="px-3 py-2 text-right tabular-nums" :class="row.projected < 0 ? 'text-ink-red-4' : 'text-ink-gray-7'">
                    {{ number(row.projected) }}
                  </td>
                  <td class="px-3 py-2 text-right tabular-nums text-ink-gray-7">{{ money(row.value, section.currency) }}</td>
                </tr>
              </tbody>
              <tfoot v-if="section.rows.length > 1">
                <tr class="border-t border-outline-gray-2 bg-surface-gray-1 font-medium">
                  <td class="px-3 py-2 text-ink-gray-8">{{ __('Total') }}</td>
                  <td class="px-3 py-2 text-right tabular-nums text-ink-gray-9">{{ number(section.totals.on_hand) }}</td>
                  <td class="px-3 py-2 text-right tabular-nums text-ink-gray-8">{{ number(section.totals.reserved) }}</td>
                  <td class="px-3 py-2 text-right tabular-nums text-ink-gray-8">{{ number(section.totals.incoming) }}</td>
                  <td class="px-3 py-2 text-right tabular-nums text-ink-gray-8">{{ number(section.totals.projected) }}</td>
                  <td class="px-3 py-2 text-right tabular-nums text-ink-gray-8">{{ money(section.totals.value, section.currency) }}</td>
                </tr>
              </tfoot>
            </table>
            <p v-else class="px-3 py-4 text-base text-ink-gray-5">{{ __('No stock in any warehouse.') }}</p>
          </div>
        </div>
      </section>

      <section v-for="(group, index) in info.groups || []" :key="index" class="mt-6">
        <h2 v-if="group.label" class="mb-2 text-base font-semibold text-ink-gray-9">{{ group.label }}</h2>
        <dl v-if="group.fields.length" class="grid gap-x-6 gap-y-3 rounded-4 border border-outline-gray-2 px-4 py-3 sm:grid-cols-2">
          <div v-for="field in group.fields" :key="field.key" :class="field.long ? 'sm:col-span-2' : ''">
            <dt class="text-sm text-ink-gray-5">{{ field.label }}</dt>
            <dd class="mt-0.5 break-words text-base text-ink-gray-9">
              <RecordHover v-if="field.link" :doctype="field.link_doctype" :name="field.link_name">
                <a :href="field.link" class="hover:underline" @click="followLink(router, $event, field.link)">{{ field.value }}</a>
              </RecordHover>
              <a v-else-if="field.file" :href="field.file" target="_blank" class="inline-flex items-center gap-1 text-ink-blue-3 hover:underline">
                <span class="lucide-file-down size-4" aria-hidden="true" />{{ field.value }}
              </a>
              <span v-else :class="field.long ? 'whitespace-pre-line' : ''">{{ field.value }}</span>
            </dd>
          </div>
        </dl>

        <div v-for="table in group.tables" :key="table.key" class="mt-3 overflow-hidden rounded-4 border border-outline-gray-2">
          <div class="flex items-center justify-between border-b border-outline-gray-2 bg-surface-gray-1 px-3 py-2">
            <span class="text-sm font-medium text-ink-gray-8">{{ table.label }}</span>
            <span class="text-sm text-ink-gray-5">{{ table.count === 1 ? __('1 row') : __('{0} rows').format(table.count) }}</span>
          </div>
          <div class="overflow-x-auto">
            <table class="w-full text-base">
              <thead>
                <tr class="border-b border-outline-gray-1 text-left text-sm text-ink-gray-5">
                  <th v-for="column in table.columns" :key="column.key" class="px-3 py-1.5 font-medium">{{ column.label }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(row, rowIndex) in table.rows" :key="rowIndex" class="border-b border-outline-gray-1 last:border-0">
                  <td v-for="column in table.columns" :key="column.key" class="px-3 py-1.5 text-ink-gray-8">
                    <RecordHover v-if="row[column.key].link" :doctype="row[column.key].link_doctype" :name="row[column.key].link_name">
                      <a :href="row[column.key].link" class="hover:underline" @click="followLink(router, $event, row[column.key].link)">
                        {{ row[column.key].value }}
                      </a>
                    </RecordHover>
                    <span v-else>{{ row[column.key].value }}</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </section>
    </template>
  </div>
</template>

<script setup>
import { computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Badge, ErrorMessage, PageHeader, Skeleton, createResource } from 'frappe-ui'
import AppBreadcrumbs from '@/components/Layouts/AppBreadcrumbs.vue'
import { followLink, listPath } from '@/utils/records'
import RecordHover from '@/components/Records/RecordHover.vue'
import { translate as __ } from '@/translation'

const route = useRoute()
const router = useRouter()

const record = createResource({
  url: 'sop.api.records.get_record',
  makeParams: () => ({ doctype: route.params.doctype, name: route.params.name }),
})

const info = computed(() => record.data || null)

const crumbs = computed(() => [
  { label: info.value?.type_label || route.params.doctype, route: listPath(route.params.doctype) },
  { label: info.value?.title || route.params.name },
])

function number(value) {
  return new Intl.NumberFormat(undefined, { maximumFractionDigits: 3 }).format(Number(value) || 0)
}

function money(value, currency) {
  try {
    return new Intl.NumberFormat(undefined, { style: 'currency', currency: currency || 'USD', maximumFractionDigits: 0 }).format(Number(value) || 0)
  } catch {
    return number(value)
  }
}

watch(
  () => [route.params.doctype, route.params.name],
  ([doctype, name]) => doctype && name && record.reload(),
  { immediate: true },
)
</script>
