<template>
  <Dialog v-model:open="open" size="md" bare>
    <template #default>
      <div class="overflow-hidden rounded-4">
        <div class="relative h-20 bg-surface-gray-2">
          <Button
            class="absolute right-2 top-2"
            variant="ghost"
            icon="lucide-x"
            label="Close"
            @click="open = false"
          />
        </div>

        <div class="flex flex-col items-center px-5 pb-5 text-center">
          <Avatar
            :image="session.user.image"
            :label="session.user.full_name"
            size="3xl"
            class="-mt-10 ring-4 ring-surface-base"
          />

          <p class="mt-3 text-lg font-semibold text-ink-gray-9">{{ session.user.full_name }}</p>
          <p class="mt-0.5 text-sm text-ink-gray-5">{{ session.user.name }}</p>
          <Badge class="mt-2" variant="subtle" size="sm">{{ role }}</Badge>

          <div class="mt-5 grid w-full grid-cols-3 gap-2">
            <div
              v-for="tile in tiles"
              :key="tile.label"
              class="rounded-4 border border-outline-gray-2 bg-surface-gray-1 px-2 py-3"
            >
              <div class="text-lg font-semibold" :class="tile.tone || 'text-ink-gray-8'">
                {{ tile.value }}
              </div>
              <div class="mt-0.5 text-xs text-ink-gray-5">{{ tile.label }}</div>
            </div>
          </div>

          <div class="mt-4 w-full border-t border-outline-gray-1 pt-2">
            <Button
              v-for="action in actions"
              :key="action.label"
              class="!h-9 w-full !justify-start"
              variant="ghost"
              :icon-left="action.icon"
              :label="action.label"
              @click="action.onClick"
            />
          </div>
        </div>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { computed, watch } from 'vue'
import { Avatar, Badge, Button, Dialog, createResource, useColorScheme } from 'frappe-ui'
import { session } from '@/data/session'
import { useUI } from '@/stores/ui'

const open = defineModel('open', { type: Boolean, default: false })

const ui = useUI()
const { colorScheme, setColorScheme } = useColorScheme()

const stats = createResource({ url: 'sop.api.session.stats' })

const role = computed(() => {
  if (session.user.is_manager) return 'Manager'
  if (session.user.is_author) return 'Author'

  return 'Reader'
})

const tiles = computed(() => {
  const data = stats.data || {}

  return [
    { label: 'Waiting on you', value: data.waiting ?? 0 },
    { label: 'You own', value: data.owned ?? 0 },
    { label: 'Your drafts', value: data.drafts ?? 0 },
    { label: 'Signed off', value: data.signed ?? 0 },
    { label: 'Training open', value: data.training_open ?? 0 },
    {
      label: 'Overdue',
      value: data.training_overdue ?? 0,
      tone: data.training_overdue ? 'text-ink-red-3' : null,
    },
  ]
})

const actions = computed(() => [
  {
    icon: 'lucide-settings',
    label: 'Settings',
    onClick: () => {
      open.value = false
      ui.openSettings('preferences')
    },
  },
  {
    icon: colorScheme.value === 'dark' ? 'lucide-sun' : 'lucide-moon',
    label: colorScheme.value === 'dark' ? 'Switch to light' : 'Switch to dark',
    onClick: () => setColorScheme(colorScheme.value === 'dark' ? 'light' : 'dark'),
  },
  {
    icon: 'lucide-layout-grid',
    label: 'Open the desk',
    onClick: () => window.open('/app/sop', '_blank'),
  },
  { icon: 'lucide-log-out', label: 'Log out', onClick: () => session.logout() },
])

watch(open, (value) => {
  if (value) stats.reload()
})
</script>
