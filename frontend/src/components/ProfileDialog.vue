<template>
  <Dialog v-model:open="open" size="md" bare>
    <template #default>
      <div class="overflow-hidden rounded-lg">
        <div class="relative h-24 bg-surface-gray-3">
          <div class="absolute inset-0 bg-gradient-to-br from-surface-gray-4 to-surface-gray-2" />

          <Button
            class="absolute right-2 top-2"
            variant="ghost"
            icon="lucide-x"
            label="Close"
            @click="open = false"
          />
        </div>

        <div class="px-5 pb-5">
          <div class="-mt-9 flex items-end gap-3">
            <Avatar
              :image="session.user.image"
              :label="session.user.full_name"
              size="3xl"
              class="ring-4 ring-surface-base"
            />
            <div class="min-w-0 flex-1 pb-1">
              <div class="truncate text-lg font-semibold text-ink-gray-9">
                {{ session.user.full_name }}
              </div>
              <div class="truncate text-sm text-ink-gray-5">{{ session.user.name }}</div>
            </div>
            <Badge variant="subtle" size="sm" class="mb-1.5">{{ role }}</Badge>
          </div>

          <div class="mt-5 grid grid-cols-3 gap-2">
            <div
              v-for="tile in tiles"
              :key="tile.label"
              class="rounded-lg border border-outline-gray-2 bg-surface-gray-1 px-3 py-2.5 text-center"
            >
              <div class="text-lg font-semibold text-ink-gray-8">{{ tile.value }}</div>
              <div class="mt-0.5 text-sm text-ink-gray-5">{{ tile.label }}</div>
            </div>
          </div>

          <div class="mt-5 flex items-center justify-between gap-2">
            <Button
              variant="ghost"
              icon-left="lucide-settings"
              label="Settings"
              @click="openSettings"
            />
            <Button
              variant="subtle"
              icon-left="lucide-log-out"
              label="Log out"
              @click="session.logout()"
            />
          </div>
        </div>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { computed } from 'vue'
import { Avatar, Badge, Button, Dialog } from 'frappe-ui'
import { attention } from '@/data/navigation'
import { session } from '@/data/session'
import { trainingCounts } from '@/data/training'
import { useUI } from '@/stores/ui'

const open = defineModel('open', { type: Boolean, default: false })

const ui = useUI()

const role = computed(() => {
  if (session.user.is_manager) return 'Manager'
  if (session.user.is_author) return 'Author'

  return 'Reader'
})

const tiles = computed(() => [
  { label: 'Waiting on you', value: attention.value },
  { label: 'Training open', value: trainingCounts.data?.open || 0 },
  { label: 'Overdue', value: trainingCounts.data?.overdue || 0 },
])

function openSettings() {
  open.value = false
  ui.openSettings('preferences')
}
</script>
