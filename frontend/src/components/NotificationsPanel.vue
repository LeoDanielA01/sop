<template>
  <Teleport to="body">
    <Transition
      enter-active-class="transition-opacity duration-150"
      leave-active-class="transition-opacity duration-150"
      enter-from-class="opacity-0"
      leave-to-class="opacity-0"
    >
      <div v-if="open" class="fixed inset-0 z-[19] bg-black/10" @click="open = false" />
    </Transition>

    <Transition
      enter-active-class="transition-transform duration-200 ease-out"
      leave-active-class="transition-transform duration-150 ease-in"
      enter-from-class="translate-x-full"
      leave-to-class="translate-x-full"
    >
      <aside
        v-if="open"
        class="fixed inset-y-0 right-0 z-20 flex w-full flex-col border-l border-outline-gray-2 bg-surface-base shadow-2xl sm:w-[26rem]"
      >
        <div class="flex items-center gap-2 px-4 pb-2 pt-3.5">
          <span class="text-lg font-semibold text-ink-gray-9">Notifications</span>
          <Badge v-if="counts.total" theme="red" variant="subtle" size="sm">
            {{ counts.total }}
          </Badge>

          <div class="flex-1" />

          <Tooltip text="Mark everything as read">
            <Button
              variant="ghost"
              label="Mark everything as read"
              :disabled="!counts.total"
              :loading="read.loading"
              @click="markAll"
            >
              <template #icon>
                <span class="lucide-check-check size-4 text-ink-gray-7" aria-hidden="true" />
              </template>
            </Button>
          </Tooltip>

          <Tooltip text="Close">
            <Button variant="ghost" icon="lucide-x" label="Close" @click="open = false" />
          </Tooltip>
        </div>

        <TabButtons v-model="tab" :options="TABS" class="notify-tabs px-3 pb-1" @update:modelValue="load" />

        <div class="min-h-0 flex-1 overflow-y-auto">
          <ListSkeleton v-if="feed.loading && !rows.length" class="px-4 pt-3" :rows="5" />

          <template v-else-if="rows.length">
            <section v-for="group in groups" :key="group.label">
              <p
                class="sticky top-0 z-10 bg-surface-base px-4 py-1.5 text-sm font-medium text-ink-gray-5"
              >
                {{ group.label }}
              </p>

              <div
                v-for="row in group.rows"
                :key="row.name"
                class="flex cursor-pointer items-start gap-2.5 px-4 py-2.5 hover:bg-surface-gray-2"
                :class="row.read ? '' : 'bg-surface-gray-1'"
                @click="visit(row)"
              >
                <span
                  class="mt-3 size-1.5 shrink-0 rounded-full"
                  :class="row.read ? 'bg-transparent' : 'bg-surface-red-5'"
                  aria-hidden="true"
                />

                <span class="relative mt-0.5 shrink-0">
                  <Avatar :image="row.actor_image" :label="row.actor || 'SOP'" size="lg" />
                  <span
                    class="absolute -bottom-1 -right-1 grid size-4 place-content-center rounded-full bg-surface-base"
                  >
                    <span
                      :class="row.kind === 'training' ? 'lucide-graduation-cap' : 'lucide-file-text'"
                      class="size-3 text-ink-gray-6"
                      aria-hidden="true"
                    />
                  </span>
                </span>

                <div class="min-w-0 flex-1">
                  <p
                    class="text-base"
                    :class="row.read ? 'text-ink-gray-7' : 'font-medium text-ink-gray-9'"
                  >
                    {{ row.subject }}
                  </p>

                  <p class="mt-1 flex min-w-0 flex-wrap items-center gap-x-1.5 text-sm text-ink-gray-5">
                    <Badge
                      v-if="row.status"
                      :theme="STATUS_THEME[row.status]"
                      variant="subtle"
                      size="sm"
                    >
                      {{ row.status }}
                    </Badge>
                    <span v-if="row.title" class="truncate">{{ row.title }}</span>
                    <span v-if="row.due_on">· due {{ shortDate(row.due_on) }}</span>
                    <span>· {{ row.when }}</span>
                  </p>
                </div>
              </div>
            </section>
          </template>

          <div v-else class="flex flex-col items-center px-8 pb-10 pt-20 text-center">
            <span
              class="grid size-10 place-content-center rounded-full bg-surface-gray-2"
              aria-hidden="true"
            >
              <span class="lucide-bell size-5 text-ink-gray-5" />
            </span>
            <p class="mt-3 text-base font-medium text-ink-gray-7">{{ empty.title }}</p>
            <p class="mt-1 text-sm text-ink-gray-5">{{ empty.line }}</p>
          </div>
        </div>
      </aside>
    </Transition>
  </Teleport>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { Avatar, Badge, Button, TabButtons, Tooltip } from 'frappe-ui'
import ListSkeleton from '@/components/ListSkeleton.vue'
import { feed, counts, read, unreadResource } from '@/data/notifications'
import { STATUS_THEME, dayLabel, shortDate } from '@/utils/format'

const TABS = [
  { label: 'All', value: 'all' },
  { label: 'Unread', value: 'unread' },
  { label: 'Procedures', value: 'procedure' },
  { label: 'Training', value: 'training' },
]

const EMPTY = {
  all: { title: 'Nothing yet', line: 'Approvals, decisions and training land here.' },
  unread: { title: 'You are all caught up', line: 'Nothing left unread.' },
  procedure: { title: 'No procedure news', line: 'Approvals and publishing show up here.' },
  training: { title: 'No training news', line: 'Assignments and sessions show up here.' },
}

const open = defineModel('open', { type: Boolean, default: false })

const router = useRouter()
const tab = ref('all')

const rows = computed(() => feed.data || [])

const empty = computed(() => EMPTY[tab.value] || EMPTY.all)

const groups = computed(() => {
  const out = []

  for (const row of rows.value) {
    const label = dayLabel(row.creation)
    const last = out[out.length - 1]

    if (last && last.label === label) last.rows.push(row)
    else out.push({ label, rows: [row] })
  }

  return out
})

const kind = computed(() =>
  tab.value === 'procedure' || tab.value === 'training' ? tab.value : undefined,
)

function load() {
  feed.submit({ kind: kind.value, unread_only: tab.value === 'unread' ? 1 : 0 })
}

function markAll() {
  read.submit({ kind: kind.value })
}

function visit(row) {
  if (!row.read) read.submit({ name: row.name })

  open.value = false
  router.push(row.route)
}

watch(open, (value) => {
  if (!value) return

  tab.value = 'all'
  load()
  unreadResource.reload()
})
</script>

<style scoped>
:deep(.notify-tabs > div) {
  display: flex;
  width: 100%;
}
:deep(.notify-tabs [data-slot='tab-button']) {
  flex: 1 1 0%;
}
:deep(.notify-tabs [data-slot='tab-button'] > *) {
  display: flex;
  width: 100%;
  justify-content: center;
}
</style>
