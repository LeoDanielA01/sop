<script setup>
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  Avatar,
  Button,
  DesktopShell,
  Dropdown,
  ScrollArea,
  Sidebar,
  SidebarHeader,
  SidebarItem,
  SidebarLabel,
  SidebarRail,
  SidebarRailItem,
} from 'frappe-ui'
import MobileShell from '@/components/MobileShell.vue'
import Settings from '@/components/Settings.vue'
import { useBreakpoint } from '@/composables/useBreakpoint'
import { session } from '@/data/session'
import { spaces, views, activeSpace, setSpace } from '@/data/navigation'
import { trainingCounts } from '@/data/training'

const route = useRoute()
const router = useRouter()
const showSettings = ref(false)
const { isDesktop } = useBreakpoint()

const space = computed(() => spaces.value.find((s) => s.name === activeSpace.value))
const activeView = computed(() => route.query.view || 'all')

const userMenu = [
  { label: 'My acknowledgements', icon: 'lucide-check-check' },
  {
    label: 'Settings',
    icon: 'lucide-settings',
    onClick: () => (showSettings.value = true),
  },
  { label: 'Log out', icon: 'lucide-log-out', onClick: () => session.logout() },
]

const spaceActions = [
  { label: 'New procedure', icon: 'lucide-plus', onClick: () => router.push('/new') },
  { label: 'Manage access', icon: 'lucide-users', onClick: () => (showSettings.value = true) },
  { label: 'Export binder', icon: 'lucide-download' },
]

function openView(value) {
  router.push({ path: '/', query: { space: activeSpace.value, view: value } })
}
</script>

<template>
  <div class="h-screen w-full bg-surface-base text-ink-gray-9">
    <MobileShell
      v-if="!isDesktop"
      @open-settings="showSettings = true"
      @open-search="$emit('open-search')"
    >
      <router-view :space-actions="spaceActions" :compact="true" />
    </MobileShell>

    <DesktopShell v-else>
      <template #rail>
        <SidebarRail class="border-r">
          <SidebarRailItem label="All procedures" @click="router.push('/')">
            <Avatar image="/sop-mark.svg" label="SOP" size="lg" shape="square" class="size-7" />
          </SidebarRailItem>

          <!-- One cell per binder. The badge counts procedures overdue for
               review, because that is the number people get chased about. -->
          <div class="flex w-full flex-1 flex-col items-center gap-3 pt-3">
            <SidebarRailItem
              v-for="s in spaces"
              :key="s.name"
              :label="s.title"
              :active="activeSpace === s.name"
              :badge="s.overdue"
              badge-style="count"
              @click="setSpace(s.name)"
            >
              <Avatar :label="s.title" size="lg" shape="square" class="size-7" />
            </SidebarRailItem>
          </div>

          <div class="flex flex-col items-center gap-2.5">
            <SidebarRailItem
              label="Search procedures"
              variant="ghost"
              icon="lucide-search"
              @click="$emit('open-search')"
            />
            <SidebarRailItem
              label="Settings"
              variant="ghost"
              icon="lucide-settings"
              @click="showSettings = true"
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

      <template #sidebar>
        <Sidebar width="14rem" class="border-r">
          <!-- The rail already shows which binder is active, so no logo here. -->
          <SidebarHeader
            :title="space?.title || 'Procedures'"
            :subtitle="`${space?.total || 0} procedures`"
            :show-logo="false"
            :menu-items="[
              {
                label: 'New procedure',
                icon: 'lucide-file-plus',
                onClick: () => router.push('/new'),
              },
              {
                label: 'Space settings',
                icon: 'lucide-settings-2',
                onClick: () => (showSettings = true),
              },
            ]"
          />

          <ScrollArea class="min-h-0 flex-1" viewport-class="px-2 pt-0.5 pb-10">
            <nav class="space-y-0.5">
              <SidebarItem :active="activeView === 'all'" @click="openView('all')">
                <template #prefix>
                  <span class="lucide-library size-4" aria-hidden="true" />
                </template>
                <span class="flex-1 truncate text-sm">All procedures</span>
              </SidebarItem>
              <SidebarItem @click="$emit('open-search')">
                <template #prefix>
                  <span class="lucide-search size-4" aria-hidden="true" />
                </template>
                <span class="flex-1 truncate text-sm">Search</span>
              </SidebarItem>
              <SidebarItem
                :active="route.name === 'Training'"
                @click="router.push('/training')"
              >
                <template #prefix>
                  <span class="lucide-graduation-cap size-4" aria-hidden="true" />
                </template>
                <span class="flex-1 truncate text-sm">My training</span>
                <template #suffix>
                  <span
                    v-if="trainingCounts.data?.open"
                    class="mr-1 size-4 grid place-content-center text-xs"
                    :class="trainingCounts.data?.overdue ? 'text-ink-red-3' : 'text-ink-gray-5'"
                  >
                    {{ trainingCounts.data.open }}
                  </span>
                </template>
              </SidebarItem>
            </nav>

            <div class="mt-4 flex h-7 items-center justify-between">
              <SidebarLabel>Needs attention</SidebarLabel>
              <Button variant="ghost" size="sm" icon="lucide-refresh-cw" label="Refresh counts" />
            </div>

            <nav class="mt-0.5 space-y-0.5">
              <SidebarItem
                v-for="view in views"
                :key="view.value"
                :active="activeView === view.value"
                @click="openView(view.value)"
              >
                <template #prefix>
                  <span :class="view.icon" class="size-4" aria-hidden="true" />
                </template>
                <span class="flex-1 truncate text-sm">{{ view.label }}</span>
                <template #suffix>
                  <span
                    v-if="view.count"
                    class="mr-1 size-4 grid place-content-center text-xs"
                    :class="view.tone === 'overdue' ? 'text-ink-red-3' : 'text-ink-gray-5'"
                  >
                    {{ view.count }}
                  </span>
                </template>
              </SidebarItem>
            </nav>
          </ScrollArea>
        </Sidebar>
      </template>

      <router-view :space-actions="spaceActions" />
    </DesktopShell>

    <Settings v-model:open="showSettings" />
  </div>
</template>
