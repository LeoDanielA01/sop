<template>
  <PageHeader>
    <AppBreadcrumbs />
    <Button
      v-if="spaces.length"
      variant="solid"
      label="New procedure"
      icon-left="lucide-plus"
      @click="router.push('/new')"
    />
  </PageHeader>

  <div class="mx-auto flex min-h-full w-full max-w-[940px] flex-col px-3 pb-4 pt-5 sm:px-5">
    <div class="mb-4 flex items-center justify-between">
      <TabButtons
        v-model="scope"
        :options="[
          { label: 'Mine', value: 'Mine' },
          { label: 'All', value: 'All' },
        ]"
      />
      <span class="text-sm text-ink-gray-5">
        {{ total }} {{ total === 1 ? 'procedure' : 'procedures' }}
      </span>
    </div>

    <List class="-mx-3 sm:list-gap-4">
      <ListRow
        v-for="procedure in rows"
        :key="procedure.name"
        class="h-15"
        @click="open(procedure)"
      >
        <ListCell class="hidden sm:flex">
          <Avatar
            :image="procedure.owner_image"
            :label="procedure.process_owner_name || procedure.process_owner"
            size="2xl"
          />
        </ListCell>

        <ListCell>
          <div class="min-w-0 flex-1">
            <div class="truncate leading-none text-ink-gray-8">
              <span :class="procedure.unacknowledged ? 'text-base-semibold' : 'text-base'">
                {{ procedure.title }}
              </span>
            </div>
            <div class="mt-1.5 flex min-w-0 items-center text-base text-ink-gray-5">
              <span class="shrink-0 font-mono text-sm">{{ procedure.sop_no }}</span>
              <span class="shrink-0">&nbsp;·&nbsp;Rev {{ procedure.version }}&nbsp;·&nbsp;</span>
              <span class="truncate">{{ procedure.summary }}</span>
            </div>
          </div>
        </ListCell>

        <ListCell class="justify-end">
          <div>
            <div class="flex items-center justify-end gap-2">
              <Tooltip
                v-if="procedure.review_due"
                :text="`Review due ${shortDate(procedure.review_due)}`"
              >
                <Badge
                  v-if="reviewTone(procedure.review_due)"
                  :theme="reviewTone(procedure.review_due)"
                  variant="subtle"
                  size="sm"
                >
                  {{ reviewTone(procedure.review_due) === 'red' ? 'Overdue' : 'Review soon' }}
                </Badge>
              </Tooltip>
              <Badge :theme="STATUS_THEME[procedure.status]" variant="subtle" size="sm">
                {{ procedure.status }}
              </Badge>
            </div>
            <div
              class="mt-1.5 hidden whitespace-nowrap text-right text-sm text-ink-gray-5 sm:block"
            >
              {{ procedure.effective_from ? shortDate(procedure.effective_from) : 'Not effective' }}
            </div>
          </div>
        </ListCell>
      </ListRow>
    </List>

    <Pagination
      v-if="paged"
      class="mt-auto"
      v-model:page="page"
      v-model:page-length="pageLength"
      :total="total"
    />

    <ListSkeleton v-if="procedures.loading && !rows.length" />

    <div
      v-if="!procedures.loading && !rows.length"
      class="mt-16 flex flex-col items-center gap-3 px-6 text-center text-base text-ink-gray-5"
    >
      <template v-if="spaces.length">
        <span v-if="activeProcess">Nothing filed under this process yet.</span>
        <span v-else>Nothing here yet.</span>
        <Button
          variant="solid"
          icon-left="lucide-plus"
          label="Write the first procedure"
          @click="router.push('/new')"
        />
      </template>
      <template v-else>
        <span>
          Start with a space. It is the binder a procedure lives in — QA, Production, HR — and its
          code becomes the procedure number.
        </span>
        <Button
          variant="solid"
          icon-left="lucide-plus"
          label="Create a space"
          @click="ui.spaceDialog = true"
        />
      </template>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  Avatar,
  Badge,
  Button,
  PageHeader,
  TabButtons,
  Tooltip,
  createResource,
} from 'frappe-ui'
import { List, ListCell, ListRow } from 'frappe-ui/list'
import AppBreadcrumbs from '@/components/Layouts/AppBreadcrumbs.vue'
import ListSkeleton from '@/components/ListSkeleton.vue'
import Pagination from '@/components/Pagination.vue'
import { procedures, page, pageLength, reloadProcedures, view } from '@/data/procedures'
import { activeSpace, setSpace, spaces } from '@/data/navigation'
import { preferences } from '@/data/preferences'
import { activeProcess, setProcess } from '@/data/processes'
import { useUI } from '@/stores/ui'
import { STATUS_THEME, reviewTone, shortDate } from '@/utils/format'

defineProps({ compact: { type: Boolean, default: false } })

const route = useRoute()
const router = useRouter()
const ui = useUI()

const scope = ref('All')
const space = computed(() => spaces.value.find((s) => s.name === activeSpace.value))

watch(
  () => route.query.view,
  (value) => (view.value = value || 'all'),
  { immediate: true },
)

watch(
  () => route.query.space,
  (value, previous) => {
    if (value) {
      if (value !== activeSpace.value) setSpace(value)
      return
    }

    if (previous !== undefined) setSpace(null)
  },
  { immediate: true },
)

watch(
  () => route.query.process,
  (value) => {
    if ((value || null) !== activeProcess.value) setProcess(value || null)
  },
  { immediate: true },
)

const rows = computed(() => {
  const all = procedures.data?.rows || []
  return scope.value === 'Mine' ? all.filter((p) => p.is_mine) : all
})

const total = computed(() => procedures.data?.total || 0)

const paged = computed(() => total.value > Math.min(pageLength.value, preferences.rows_per_page))

onMounted(() => reloadProcedures())

function open(procedure) {
  router.push(`/${procedure.name}`)
}
</script>
