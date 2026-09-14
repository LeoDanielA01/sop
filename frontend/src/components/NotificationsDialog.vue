<template>
  <Dialog v-model:open="open" size="lg" bare>
    <template #default>
      <div class="text-base">
        <div class="flex items-center justify-between border-b border-outline-gray-1 px-4 py-2.5">
          <div class="flex items-center gap-2">
            <span class="text-base font-medium text-ink-gray-8">Notifications</span>
            <Badge v-if="unreadCount" variant="subtle" theme="orange" size="sm">
              {{ unreadCount }} new
            </Badge>
          </div>

          <Button
            v-if="unreadCount"
            variant="ghost"
            size="sm"
            label="Mark all read"
            :loading="read.loading"
            @click="read.submit({})"
          />
        </div>

        <div class="max-h-96 overflow-y-auto p-1.5">
          <div
            v-for="row in rows"
            :key="row.name"
            class="flex cursor-pointer items-start gap-3 rounded-3 px-2.5 py-2 hover:bg-surface-gray-2"
            @click="visit(row)"
          >
            <span
              class="mt-1.5 size-1.5 shrink-0 rounded-full"
              :class="row.read ? 'bg-transparent' : 'bg-surface-amber-3'"
              aria-hidden="true"
            />

            <div class="min-w-0 flex-1">
              <p class="text-base" :class="row.read ? 'text-ink-gray-6' : 'text-ink-gray-8'">
                {{ row.subject }}
              </p>
              <p class="mt-0.5 text-sm text-ink-gray-5">{{ row.when }}</p>
            </div>
          </div>

          <p v-if="!feed.loading && !rows.length" class="px-3 py-10 text-center text-sm text-ink-gray-5">
            Nothing yet. Approvals, decisions and training land here.
          </p>
        </div>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { Badge, Button, Dialog } from 'frappe-ui'
import { feed, unreadCount, read, refreshNotifications } from '@/data/notifications'

const open = defineModel('open', { type: Boolean, default: false })

const router = useRouter()

const rows = computed(() => feed.data || [])

function visit(row) {
  if (!row.read) read.submit({ name: row.name })

  open.value = false
  router.push(row.route)
}

watch(open, (value) => {
  if (value) refreshNotifications()
})
</script>
