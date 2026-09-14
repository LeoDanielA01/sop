<template>
  <Dialog v-model:open="open" size="lg" bare>
    <template #default>
      <div class="text-base">
        <div class="flex items-center justify-between border-b border-outline-gray-1 px-4 py-2.5">
          <span class="text-base font-medium text-ink-gray-8">Notifications</span>

          <Button
            v-if="counts.total"
            variant="ghost"
            size="sm"
            icon-left="lucide-check-check"
            label="Mark all read"
            :loading="read.loading"
            @click="read.submit({ kind: tab || undefined })"
          />
        </div>

        <div class="flex items-center gap-2 border-b border-outline-gray-1 px-4 py-2">
          <TabButtons
            v-model="tab"
            :options="[
              { label: 'All', value: '' },
              { label: 'Procedures', value: 'procedure' },
              { label: 'Training', value: 'training' },
            ]"
            @update:modelValue="load"
          />

          <Badge v-if="badgeFor" variant="subtle" theme="red" size="sm">{{ badgeFor }} unread</Badge>
        </div>

        <div class="max-h-[26rem] overflow-y-auto py-1">
          <div
            v-for="row in rows"
            :key="row.name"
            class="flex cursor-pointer items-start gap-3 px-4 py-2.5 hover:bg-surface-gray-1"
            @click="visit(row)"
          >
            <span
              class="mt-2 size-2 shrink-0 rounded-full"
              :class="row.read ? 'bg-transparent' : 'bg-surface-red-6'"
              aria-hidden="true"
            />

            <span
              class="grid size-8 shrink-0 place-content-center rounded-4 border border-outline-gray-2 bg-surface-gray-1"
            >
              <span
                :class="row.kind === 'training' ? 'lucide-graduation-cap' : 'lucide-file-text'"
                class="size-4 text-ink-gray-6"
                aria-hidden="true"
              />
            </span>

            <div class="min-w-0 flex-1">
              <p class="text-base" :class="row.read ? 'text-ink-gray-6' : 'text-ink-gray-8'">
                {{ row.subject }}
              </p>

              <p class="mt-0.5 flex min-w-0 flex-wrap items-center gap-x-2 text-sm text-ink-gray-5">
                <span v-if="row.title" class="truncate">{{ row.title }}</span>
                <Badge v-if="row.status" :theme="STATUS_THEME[row.status]" variant="subtle" size="sm">
                  {{ row.status }}
                </Badge>
                <span v-if="row.due_on">· due {{ shortDate(row.due_on) }}</span>
                <span>· {{ row.when }}</span>
              </p>
            </div>

            <Avatar
              v-if="row.actor"
              :image="row.actor_image"
              :label="row.actor"
              size="sm"
              class="mt-0.5 shrink-0"
            />
          </div>

          <p
            v-if="!feed.loading && !rows.length"
            class="px-4 py-12 text-center text-sm text-ink-gray-5"
          >
            {{ emptyLine }}
          </p>
        </div>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { Avatar, Badge, Button, Dialog, TabButtons } from 'frappe-ui'
import { feed, counts, read, refreshNotifications } from '@/data/notifications'
import { STATUS_THEME, shortDate } from '@/utils/format'

const open = defineModel('open', { type: Boolean, default: false })

const router = useRouter()
const tab = ref('')

const rows = computed(() => feed.data || [])

const badgeFor = computed(() => (tab.value ? counts.value[tab.value] : counts.value.total))

const emptyLine = computed(() => {
  if (tab.value === 'training') return 'No training news yet.'
  if (tab.value === 'procedure') return 'Nothing about procedures yet.'

  return 'Nothing yet. Approvals, decisions and training land here.'
})

function load() {
  feed.submit({ kind: tab.value || undefined })
}

function visit(row) {
  if (!row.read) read.submit({ name: row.name })

  open.value = false
  router.push(row.route)
}

watch(open, (value) => {
  if (!value) return

  tab.value = ''
  refreshNotifications()
})
</script>
