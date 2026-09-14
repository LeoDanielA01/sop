<template>
  <nav class="space-y-0.5">
    <SidebarItem :active="route.name === 'Training'" @click="router.push('/training')">
      <template #prefix>
        <span class="lucide-graduation-cap size-4" aria-hidden="true" />
      </template>
      <span class="flex-1 truncate text-sm">My training</span>
      <template #suffix>
        <span
          v-if="trainingCounts.data?.open"
          class="mr-1 grid size-4 place-content-center text-xs"
          :class="trainingCounts.data?.overdue ? 'text-ink-red-3' : 'text-ink-gray-5'"
        >
          {{ trainingCounts.data.open }}
        </span>
      </template>
    </SidebarItem>

    <SidebarItem :active="route.name === 'TrainingMatrix'" @click="router.push('/training/matrix')">
      <template #prefix>
        <span class="lucide-grid-3x3 size-4" aria-hidden="true" />
      </template>
      <span class="flex-1 truncate text-sm">Training matrix</span>
    </SidebarItem>

    <SidebarItem
      :active="route.name === 'TrainingSessions'"
      @click="router.push('/training/sessions')"
    >
      <template #prefix>
        <span class="lucide-users size-4" aria-hidden="true" />
      </template>
      <span class="flex-1 truncate text-sm">Sessions</span>
    </SidebarItem>

    <SidebarItem :active="route.name === 'TrainingRules'" @click="router.push('/training/rules')">
      <template #prefix>
        <span class="lucide-scroll-text size-4" aria-hidden="true" />
      </template>
      <span class="flex-1 truncate text-sm">Rules</span>
    </SidebarItem>
  </nav>
</template>

<script setup>
import { useRoute, useRouter } from 'vue-router'
import { SidebarItem } from 'frappe-ui'
import { trainingCounts } from '@/data/training'

const route = useRoute()
const router = useRouter()
</script>
