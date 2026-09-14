<template>
  <div class="flex items-center gap-2.5 px-2 py-2">
    <Avatar :image="session.user.image" :label="session.user.full_name" size="xl" />

    <div class="min-w-0 flex-1">
      <div class="truncate text-base font-medium text-ink-gray-8">
        {{ session.user.full_name }}
      </div>
      <div class="truncate text-sm text-ink-gray-5">{{ session.user.name }}</div>
    </div>

    <Badge variant="subtle" size="sm">{{ role }}</Badge>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { Avatar, Badge } from 'frappe-ui'
import { session } from '@/data/session'

const role = computed(() => {
  if (session.user.is_manager) return 'Manager'
  if (session.user.is_author) return 'Author'

  return 'Reader'
})
</script>
