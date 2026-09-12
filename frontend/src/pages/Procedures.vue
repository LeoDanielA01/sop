<script setup>
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  Avatar,
  Badge,
  Button,
  Dropdown,
  PageHeader,
  PageHeaderTitle,
  TabButtons,
  Tooltip,
} from 'frappe-ui'
import { List, ListCell, ListRow } from 'frappe-ui/list'
import Pagination from '@/components/Pagination.vue'
import { procedures, page, pageLength, view } from '@/data/procedures'
import { activeSpace, spaces } from '@/data/navigation'
import { STATUS_THEME, reviewTone, shortDate } from '@/utils/format'

defineProps({
  spaceActions: { type: Array, default: () => [] },
  compact: { type: Boolean, default: false },
})

const route = useRoute()
const router = useRouter()

const scope = ref('All')
const space = computed(() => spaces.value.find((s) => s.name === activeSpace.value))

watch(
  () => route.query.view,
  (value) => (view.value = value || 'all'),
  { immediate: true },
)

const rows = computed(() => {
  const all = procedures.data?.rows || []
  return scope.value === 'Mine' ? all.filter((p) => p.is_mine) : all
})

const total = computed(() => procedures.data?.total || 0)

function open(procedure) {
  router.push(`/${procedure.name}`)
}
</script>

<template>
  <PageHeader>
    <div class="flex items-center gap-1">
      <PageHeaderTitle>{{ space?.title || 'All procedures' }}</PageHeaderTitle>
      <Dropdown :options="spaceActions">
        <Button variant="ghost" icon="lucide-ellipsis" label="Space actions" />
      </Dropdown>
    </div>
    <Button label="New procedure" icon-left="lucide-plus" @click="router.push('/new')" />
  </PageHeader>

  <div class="mx-auto mt-5 w-full max-w-[940px] px-3 pb-10 sm:px-5">
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

    <!-- -mx-3 lets the row hover surface bleed past the text edge while the
         content stays aligned with the container. -->
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
            <!-- The sized text sits in an inner span so `truncate` cannot
                 shear the descenders off the line above. -->
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

    <Pagination v-if="total > pageLength" v-model:page="page" v-model:page-length="pageLength" :total="total" />

    <div
      v-if="!procedures.loading && !rows.length"
      class="mt-16 flex flex-col items-center gap-3 text-center text-base text-ink-gray-5"
    >
      <span>No procedures in this space yet.</span>
      <Button
        variant="solid"
        icon-left="lucide-plus"
        label="Write the first one"
        @click="router.push('/new')"
      />
    </div>
  </div>
</template>
