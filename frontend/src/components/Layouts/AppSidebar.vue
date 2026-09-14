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
import { activeSpace, spaces } from '@/data/navigation'
import { trainingCounts } from '@/data/training'
import { useUI } from '@/stores/ui'
import { translate as __ } from '@/translation'

const router = useRouter()
const ui = useUI()
const { section, space } = useSection()

const title = computed(() =>
  section.value === 'training' ? 'Training' : space.value?.title || 'Procedures',
)

const subtitle = computed(() => {
  if (section.value === 'training') return `${trainingCounts.data?.open || 0} outstanding`
  if (space.value) return `${space.value.total || 0} procedures`

  const total = spaces.value.reduce((sum, row) => sum + (row.total || 0), 0)

  return `${total} across ${spaces.value.length} space${spaces.value.length === 1 ? '' : 's'}`
})

const menuItems = computed(() => {
  if (section.value === 'training') {
    return [
      {
        label: __('Plan a session'),
        icon: 'lucide-calendar-plus',
        onClick: () => {
          router.push('/training/sessions')
          ui.sessionDialog = true
        },
      },
      {
        label: __('Write a training rule'),
        icon: 'lucide-scroll-text',
        onClick: () => router.push('/training/rules'),
      },
    ]
  }

  return [
    {
      label: __('Add a process here'),
      icon: 'lucide-workflow',
      onClick: () => ui.askForProcess({ space: activeSpace.value }),
      condition: () => !!activeSpace.value,
    },
    {
      label: __('Start from a template'),
      icon: 'lucide-sparkles',
      onClick: () => (ui.templateDialog = true),
      condition: () => !!activeSpace.value,
    },
    {
      label: __('New space'),
      icon: 'lucide-plus',
      onClick: () => (ui.spaceDialog = true),
    },
    {
      label: __('Manage spaces'),
      icon: 'lucide-settings',
      onClick: () => ui.openSettings('spaces'),
    },
  ]
})
</script>
