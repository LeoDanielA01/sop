<template>
  <PageHeader>
    <AppBreadcrumbs
      :tail="[{ label: sopNo, route: `/${route.params.name}` }, { label: 'Revision history' }]"
    />
    <Button
      variant="ghost"
      icon-left="lucide-arrow-left"
      :label="__('Back to the procedure')"
      @click="router.push(`/${route.params.name}`)"
    />
  </PageHeader>

  <div class="mx-auto mt-5 w-full max-w-[940px] px-3 pb-10 sm:px-5">
    <List class="-mx-3 sm:list-gap-4">
      <ListRow v-for="row in rows" :key="row.name" class="h-15">
        <ListCell>
          <Badge variant="subtle" size="sm">Rev {{ row.version }}</Badge>
        </ListCell>

        <ListCell>
          <div class="min-w-0 flex-1">
            <div class="truncate leading-none text-ink-gray-8">
              <span class="text-base">{{ row.change_summary || 'No summary given' }}</span>
            </div>
            <div class="mt-1.5 truncate text-base text-ink-gray-5">
              {{ row.cause || 'Direct edit' }}
              <template v-if="row.is_material"> {{ __('· material change') }}</template>
            </div>
          </div>
        </ListCell>

        <ListCell class="justify-end">
          <div class="text-right">
            <div class="text-sm text-ink-gray-5">{{ shortDate(row.effective_from) }}</div>
            <div class="mt-1.5 text-sm text-ink-gray-5">{{ row.approved_by }}</div>
          </div>
        </ListCell>
      </ListRow>
    </List>

    <ListSkeleton v-if="revisions.loading && !rows.length" :avatar="false" />

    <p
      v-if="!revisions.loading && !rows.length"
      class="mt-16 text-center text-base text-ink-gray-5"
    >
      {{ __('No revisions yet. The first one is cut when this procedure becomes effective.') }}
    </p>
  </div>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Badge, Button, PageHeader, createResource } from 'frappe-ui'
import { List, ListCell, ListRow } from 'frappe-ui/list'
import AppBreadcrumbs from '@/components/Layouts/AppBreadcrumbs.vue'
import ListSkeleton from '@/components/Common/ListSkeleton.vue'
import { procedure } from '@/data/procedures'
import { shortDate } from '@/utils/format'

const route = useRoute()
const router = useRouter()

const revisions = createResource({
  url: 'frappe.client.get_list',
  makeParams: () => ({
    doctype: 'SOP Revision',
    filters: { sop: route.params.name },
    fields: [
      'name',
      'version',
      'effective_from',
      'change_summary',
      'cause',
      'approved_by',
      'approved_on',
      'is_material',
    ],
    order_by: 'version desc',
    limit_page_length: 100,
  }),
})

const sopNo = computed(() =>
  procedure.data?.name === route.params.name ? procedure.data.sop_no : route.params.name,
)

const rows = computed(() => revisions.data || [])
onMounted(() => revisions.fetch())
</script>
