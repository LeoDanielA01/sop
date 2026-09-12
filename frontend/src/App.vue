<template>
  <div class="h-screen w-full bg-surface-base text-ink-gray-9">
    <MobileShell
      v-if="!isDesktop"
      @open-settings="showSettings = true"
      @open-search="showSearch = true"
    >
      <router-view :space-actions="spaceActions" :compact="true" />
    </MobileShell>

    <DesktopShell v-else>
      <template #rail>
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
              :badge="item.key === 'training' ? trainingCounts.data?.open : undefined"
              badge-style="count"
              @click="router.push(item.route)"
            />
          </div>

          <div class="flex flex-col items-center gap-2.5">
            <SidebarRailItem
              label="Search"
              variant="ghost"
              icon="lucide-search"
              @click="showSearch = true"
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
          <SidebarHeader
            :title="sidebarTitle"
            :subtitle="sidebarSubtitle"
            :show-logo="false"
            :menu-items="headerMenu"
          />

          <ScrollArea class="min-h-0 flex-1" viewport-class="px-2 pt-0.5 pb-10">
            <template v-if="section === 'training'">
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
                <SidebarItem
                  :active="route.name === 'TrainingMatrix'"
                  @click="router.push('/training/matrix')"
                >
                  <template #prefix>
                    <span class="lucide-grid-3x3 size-4" aria-hidden="true" />
                  </template>
                  <span class="flex-1 truncate text-sm">Training matrix</span>
                </SidebarItem>
              </nav>
            </template>

            <template v-else>
              <nav class="space-y-0.5">
                <SidebarItem :active="isAll" @click="openView('all')">
                  <template #prefix>
                    <span class="lucide-library size-4" aria-hidden="true" />
                  </template>
                  <span class="flex-1 truncate text-sm">All procedures</span>
                </SidebarItem>
                <SidebarItem @click="showSearch = true">
                  <template #prefix>
                    <span class="lucide-search size-4" aria-hidden="true" />
                  </template>
                  <span class="flex-1 truncate text-sm">Search</span>
                </SidebarItem>
              </nav>

              <div class="mt-4 flex h-7 items-center justify-between">
                <SidebarLabel>Spaces</SidebarLabel>
                <Button
                  variant="ghost"
                  size="sm"
                  icon="lucide-plus"
                  label="New space"
                  @click="showSettings = true"
                />
              </div>

              <nav class="mt-0.5 space-y-0.5">
                <SidebarItem
                  v-for="s in spaces"
                  :key="s.name"
                  :active="activeSpace === s.name"
                  @click="setSpace(s.name)"
                >
                  <template #prefix>
                    <span class="lucide-folder size-4" aria-hidden="true" />
                  </template>
                  <span class="flex-1 truncate text-sm">{{ s.title }}</span>
                  <template #suffix>
                    <span
                      v-if="s.overdue"
                      class="mr-1 grid size-4 place-content-center text-xs text-ink-red-3"
                    >
                      {{ s.overdue }}
                    </span>
                  </template>
                </SidebarItem>

                <p v-if="!spaces.length" class="px-2 py-2 text-sm text-ink-gray-5">
                  No spaces yet. A space is a binder — QA, Production, HR.
                </p>
              </nav>

              <div class="mt-4 flex h-7 items-center justify-between">
                <SidebarLabel>Needs attention</SidebarLabel>
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
                      class="mr-1 grid size-4 place-content-center text-xs"
                      :class="view.tone === 'overdue' ? 'text-ink-red-3' : 'text-ink-gray-5'"
                    >
                      {{ view.count }}
                    </span>
                  </template>
                </SidebarItem>
              </nav>
            </template>
          </ScrollArea>
        </Sidebar>
      </template>

      <router-view :space-actions="spaceActions" />
    </DesktopShell>

    <SearchDialog v-model:open="showSearch" />
    <Settings v-model:open="showSettings" />
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
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
import SearchDialog from '@/components/SearchDialog.vue'
import Settings from '@/components/Settings.vue'
import { useBreakpoint } from '@/composables/useBreakpoint'
import { session } from '@/data/session'
import { SECTIONS, activeSpace, setSpace, spaces, views } from '@/data/navigation'
import { trainingCounts } from '@/data/training'

const route = useRoute()
const router = useRouter()
const { isDesktop } = useBreakpoint()

const showSettings = ref(false)
const showSearch = ref(false)

const section = computed(() => (route.path.startsWith('/training') ? 'training' : 'procedures'))
const space = computed(() => spaces.value.find((s) => s.name === activeSpace.value))
const activeView = computed(() => route.query.view || 'all')
const isAll = computed(() => route.name === 'Procedures' && activeView.value === 'all')

const sidebarTitle = computed(() =>
  section.value === 'training' ? 'Training' : space.value?.title || 'Procedures',
)

const sidebarSubtitle = computed(() =>
  section.value === 'training'
    ? `${trainingCounts.data?.open || 0} outstanding`
    : `${space.value?.total || 0} procedures`,
)

const headerMenu = computed(() =>
  section.value === 'training'
    ? [
        {
          label: 'Training matrix',
          icon: 'lucide-grid-3x3',
          onClick: () => router.push('/training/matrix'),
        },
      ]
    : [
        { label: 'New procedure', icon: 'lucide-file-plus', onClick: () => router.push('/new') },
        {
          label: 'Space settings',
          icon: 'lucide-settings-2',
          onClick: () => (showSettings.value = true),
        },
      ],
)

const userMenu = [
  { label: 'My training', icon: 'lucide-graduation-cap', onClick: () => router.push('/training') },
  { label: 'Settings', icon: 'lucide-settings', onClick: () => (showSettings.value = true) },
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

function onKeydown(event) {
  if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k') {
    event.preventDefault()
    showSearch.value = true
  }
}

onMounted(() => document.addEventListener('keydown', onKeydown))
onBeforeUnmount(() => document.removeEventListener('keydown', onKeydown))
</script>
