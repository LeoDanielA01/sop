<template>
  <Sidebar width="14rem" class="border-r">
    <SidebarHeader :title="title" :subtitle="subtitle" :show-logo="false" />

    <ScrollArea class="min-h-0 flex-1" viewport-class="px-2 pt-0.5 pb-10">
      <TrainingNav v-if="section === 'training'" />
      <ProceduresNav v-else />
    </ScrollArea>
  </Sidebar>
</template>

<script setup>
import { computed } from 'vue'
import { ScrollArea, Sidebar, SidebarHeader } from 'frappe-ui'
import ProceduresNav from './ProceduresNav.vue'
import TrainingNav from './TrainingNav.vue'
import { useSection } from '@/composables/useSection'
import { trainingCounts } from '@/data/training'

const { section, space } = useSection()

const title = computed(() =>
  section.value === 'training' ? 'Training' : space.value?.title || 'Procedures',
)

const subtitle = computed(() =>
  section.value === 'training'
    ? `${trainingCounts.data?.open || 0} outstanding`
    : `${space.value?.total || 0} procedures`,
)
</script>
