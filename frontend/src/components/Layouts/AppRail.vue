<template>
  <SidebarRail class="border-r">
    <SidebarRailItem label="Procedures" @click="router.push('/')">
      <Avatar image="/sop-mark.svg" label="SOP" size="lg" shape="square" class="size-7" />
    </SidebarRailItem>

    <div class="flex w-full flex-1 flex-col items-center gap-3 pt-3">
      <SidebarRailItem
        v-for="item in SECTIONS"
        :key="item.route"
        :label="item.label"
        :icon="item.icon"
        :active="section === item.key"
        :badge="badges[item.key]"
        badge-style="count"
        @click="router.push(item.route)"
      />
    </div>

    <div class="flex flex-col items-center gap-2.5">
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
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { Avatar, Dropdown, SidebarRail, SidebarRailItem } from 'frappe-ui'
import { useSection } from '@/composables/useSection'
import { SECTIONS, attention } from '@/data/navigation'
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

const userMenu = [{ label: 'Log out', icon: 'lucide-log-out', onClick: () => session.logout() }]
</script>
