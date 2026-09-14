<template>
  <SidebarRail class="border-r">
    <SidebarRailItem label="Procedures" @click="router.push('/')">
      <Avatar image="/sop-mark.svg" label="SOP" size="lg" shape="square" class="size-7" />
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
        label="Find and replace"
        variant="ghost"
        icon="lucide-replace"
        @click="ui.replaceDialog = true"
      />
    </div>

    <div class="flex flex-col items-center gap-2.5">
      <SidebarRailItem
        label="New procedure"
        variant="ghost"
        icon="lucide-plus"
        @click="router.push('/new')"
      />
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

      <Dropdown :options="userMenu">
        <template #trigger>
          <SidebarRailItem :label="session.user.full_name">
            <Avatar
              :image="session.user.image"
              :label="session.user.full_name"
              size="lg"
              class="size-7"
            />
          </SidebarRailItem>
        </template>
      </Dropdown>
    </div>
  </SidebarRail>
</template>

<script setup>
import { computed, markRaw } from 'vue'
import { useRouter } from 'vue-router'
import { Avatar, Dropdown, SidebarRail, SidebarRailItem, useColorScheme } from 'frappe-ui'
import UserCard from './UserCard.vue'
import { useSection } from '@/composables/useSection'
import { SECTIONS, attention } from '@/data/navigation'
import { session } from '@/data/session'
import { trainingCounts } from '@/data/training'
import { useUI } from '@/stores/ui'

const router = useRouter()
const ui = useUI()
const { section } = useSection()
const { colorScheme, setColorScheme } = useColorScheme()

const badges = computed(() => ({
  procedures: attention.value || undefined,
  training: trainingCounts.data?.open || undefined,
}))

function railLabel(item) {
  const count = badges.value[item.key]
  if (!count) return item.label

  return `${item.label} — ${count} waiting on you`
}

const userMenu = computed(() => [
  { component: markRaw(UserCard) },
  {
    icon: 'lucide-settings',
    label: 'Settings',
    onClick: () => ui.openSettings('preferences'),
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
</script>
