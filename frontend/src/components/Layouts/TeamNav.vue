<template>
  <nav class="space-y-0.5">
    <SidebarItem
      v-for="item in ITEMS"
      :key="item.id"
      :active="currentRole === item.role"
      @click="navigate(item.role)"
    >
      <template #prefix>
        <span :class="item.icon" class="size-4" aria-hidden="true" />
      </template>
      <span class="flex-1 truncate text-sm">{{ __(item.label) }}</span>
    </SidebarItem>
  </nav>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { SidebarItem } from 'frappe-ui'
import { translate as __ } from '@/translation'

const route = useRoute()
const router = useRouter()

const ITEMS = [
  { id: 'team-all', role: 'all', label: 'All Team', icon: 'lucide-users' },
  { id: 'team-authors', role: 'authors', label: 'SOP Authors', icon: 'lucide-pencil-line' },
  { id: 'team-approvers', role: 'approvers', label: 'SOP Approvers', icon: 'lucide-stamp' },
  { id: 'team-owners', role: 'owners', label: 'Active Owners', icon: 'lucide-book-user' },
]

const currentRole = computed(() => route.query.role || 'all')

function navigate(role) {
  router.push({ path: '/team', query: role === 'all' ? {} : { role } })
}
</script>
