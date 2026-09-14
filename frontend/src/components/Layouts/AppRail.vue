<template>
  <SidebarRail class="border-r">
    <SidebarRailItem label="Procedures" @click="router.push('/')">
      <Avatar :image="mark" label="SOP" size="lg" shape="square" class="size-7" />
    </SidebarRailItem>

    <div class="flex w-full flex-1 flex-col items-center gap-3 pt-3">
      <SidebarRailItem
        v-for="item in SECTIONS"
        :key="item.route"
        :label="railLabel(item)"
        :icon="item.icon"
        :active="section === item.key"
        :badge="badges[item.key]"
        badge-style="count"
        @click="router.push(item.route)"
      />

      <SidebarRailItem
        :label="unreadCount ? `Notifications — ${unreadCount} new` : 'Notifications'"
        variant="ghost"
        icon="lucide-bell"
        :badge="unreadCount || undefined"
        badge-style="count"
        @click="ui.notificationsPanel = !ui.notificationsPanel"
      />

      <SidebarRailItem
        label="Find and replace"
        variant="ghost"
        icon="lucide-replace"
        @click="ui.replaceDialog = true"
      />
    </div>

    <div class="flex flex-col items-center gap-2.5">
      <Dropdown :options="createOptions" side="right" align="end" :offset="8">
        <span class="flex">
          <SidebarRailItem label="Create" variant="ghost" icon="lucide-plus" />
        </span>
      </Dropdown>
      <SidebarRailItem
        :label="ui.sidebarCollapsed ? 'Show the sidebar' : 'Hide the sidebar'"
        variant="ghost"
        :icon="ui.sidebarCollapsed ? 'lucide-panel-left-open' : 'lucide-panel-left-close'"
        @click="ui.toggleSidebar"
      />
      <SidebarRailItem
        label="Search"
        variant="ghost"
        icon="lucide-search"
        @click="ui.searchDialog = true"
      />
      <SidebarRailItem
        label="Settings"
        variant="ghost"
        icon="lucide-settings"
        @click="ui.settingsDialog = true"
      />

      <SidebarRailItem :label="session.user.full_name" @click="ui.profileDialog = true">
        <Avatar
          :image="session.user.image"
          :label="session.user.full_name"
          size="lg"
          class="size-7"
        />
      </SidebarRailItem>
    </div>
  </SidebarRail>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { Avatar, Dropdown, SidebarRail, SidebarRailItem } from 'frappe-ui'
import mark from '@/assets/sop-mark.svg'
import { useSection } from '@/composables/useSection'
import { SECTIONS, activeSpace, attention } from '@/data/navigation'
import { unreadCount } from '@/data/notifications'
import { session } from '@/data/session'
import { trainingCounts } from '@/data/training'
import { useUI } from '@/stores/ui'

const router = useRouter()
const ui = useUI()
const { section } = useSection()

const badges = computed(() => ({
  procedures: attention.value || undefined,
  training: trainingCounts.data?.open || undefined,
}))

const createOptions = computed(() => [
  {
    label: 'Procedure',
    icon: 'lucide-file-plus-2',
    onClick: () => router.push('/new'),
  },
  {
    label: 'Procedure from a template',
    icon: 'lucide-sparkles',
    onClick: () => (ui.templateDialog = true),
    condition: () => !!activeSpace.value,
  },
  {
    label: 'Process',
    icon: 'lucide-workflow',
    onClick: () => ui.askForProcess({ space: activeSpace.value }),
    condition: () => !!activeSpace.value,
  },
  {
    label: 'Space',
    icon: 'lucide-folder-plus',
    onClick: () => (ui.spaceDialog = true),
  },
  {
    label: 'Training session',
    icon: 'lucide-calendar-plus',
    onClick: () => {
      router.push('/training/sessions')
      ui.sessionDialog = true
    },
  },
  {
    label: 'Training rule',
    icon: 'lucide-scroll-text',
    onClick: () => router.push('/training/rules'),
  },
])

function railLabel(item) {
  const count = badges.value[item.key]
  if (!count) return item.label

  return `${item.label} — ${count} waiting on you`
}
</script>
