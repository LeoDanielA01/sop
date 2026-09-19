<template>
  <nav class="space-y-0.5">
    <SidebarItem v-for="item in ITEMS" :key="item.id" @click="jump(item.id)">
      <template #prefix>
        <span :class="item.icon" class="size-4" aria-hidden="true" />
      </template>
      <span class="flex-1 truncate text-sm">{{ __(item.label) }}</span>
    </SidebarItem>
  </nav>
</template>

<script setup>
import { SidebarItem } from 'frappe-ui'
import { translate as __ } from '@/translation'

const ITEMS = [
  { id: 'insights-overview', label: 'Overview', icon: 'lucide-gauge' },
  { id: 'insights-activity', label: 'Activity', icon: 'lucide-chart-line' },
  { id: 'insights-attention', label: 'Needs attention', icon: 'lucide-circle-alert' },
  { id: 'insights-spaces', label: 'By space', icon: 'lucide-layout-grid' },
]

function jump(id) {
  document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}
</script>
