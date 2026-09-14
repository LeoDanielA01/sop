<template>
  <Sidebar width="14rem" class="border-r">
    <SidebarHeader
      :title="title"
      :subtitle="subtitle"
      :show-logo="false"
      :menu-items="menuItems"
    />

    <ScrollArea class="min-h-0 flex-1" viewport-class="px-2 pt-0.5 pb-10">
      <TrainingNav v-if="section === 'training'" />
      <ProceduresNav v-else />
    </ScrollArea>
  </Sidebar>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { ScrollArea, Sidebar, SidebarHeader } from 'frappe-ui'
import ProceduresNav from './ProceduresNav.vue'
import TrainingNav from './TrainingNav.vue'
import { useSection } from '@/composables/useSection'
import { activeSpace } from '@/data/navigation'
import { trainingCounts } from '@/data/training'
import { useUI } from '@/stores/ui'

const router = useRouter()
const ui = useUI()
const { section, space } = useSection()

const title = computed(() =>
  section.value === 'training' ? 'Training' : space.value?.title || 'Procedures',
)

const subtitle = computed(() =>
  section.value === 'training'
    ? `${trainingCounts.data?.open || 0} outstanding`
    : `${space.value?.total || 0} procedures`,
)

const menuItems = computed(() => {
  if (section.value === 'training') {
    return [
      {
        label: 'Plan a session',
        icon: 'lucide-calendar-plus',
        onClick: () => {
          router.push('/training/sessions')
          ui.sessionDialog = true
        },
      },
      {
        label: 'Write a training rule',
        icon: 'lucide-scroll-text',
        onClick: () => router.push('/training/rules'),
      },
    ]
  }

  return [
    {
      label: 'Add a process here',
      icon: 'lucide-workflow',
      onClick: () => ui.askForProcess({ space: activeSpace.value }),
      condition: () => !!activeSpace.value,
    },
    {
      label: 'Start from a template',
      icon: 'lucide-sparkles',
      onClick: () => (ui.templateDialog = true),
      condition: () => !!activeSpace.value,
    },
    {
      label: 'New space',
      icon: 'lucide-plus',
      onClick: () => (ui.spaceDialog = true),
    },
    {
      label: 'Manage spaces',
      icon: 'lucide-settings',
      onClick: () => ui.openSettings('spaces'),
    },
  ]
})
</script>
