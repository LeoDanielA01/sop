<template>
  <div class="flex h-screen flex-col bg-surface-base">
    <header class="flex items-center gap-1 border-b border-outline-gray-1 px-2 py-2">
      <Button
        v-if="!onList"
        variant="ghost"
        icon="lucide-arrow-left"
        label="Back"
        @click="router.back()"
      />
      <Button
        v-else
        variant="ghost"
        icon-right="lucide-chevrons-up-down"
        :label="space?.title || 'Procedures'"
        @click="showSpaces = true"
      />

      <div class="flex-1" />

      <Button variant="ghost" icon="lucide-search" label="Search" @click="emit('open-search')" />
      <Dropdown :options="userMenu">
        <Button variant="ghost" label="Account">
          <Avatar :image="session.user.image" :label="session.user.full_name" size="sm" />
        </Button>
      </Dropdown>
    </header>

    <main class="min-h-0 flex-1 overflow-y-auto">
      <slot />
    </main>

    <nav
      class="flex items-stretch justify-around border-t border-outline-gray-1 bg-surface-base pb-[env(safe-area-inset-bottom)]"
    >
      <Button
        v-for="item in bottom"
        :key="item.label"
        variant="ghost"
        class="!h-14 flex-1 !flex-col !gap-1 !rounded-none"
        :label="item.label"
        @click="go(item)"
      >
        <span
          :class="[item.icon, isActive(item) ? 'text-ink-gray-9' : 'text-ink-gray-5']"
          class="size-5"
          aria-hidden="true"
        />
        <span class="text-xs" :class="isActive(item) ? 'text-ink-gray-9' : 'text-ink-gray-5'">
          {{ item.label }}<template v-if="item.count"> · {{ item.count }}</template>
        </span>
      </Button>
    </nav>

    <Dialog v-model="showSpaces" :options="{ title: 'Spaces', size: 'sm' }">
      <template #body-content>
        <div class="flex flex-col gap-1">
          <Button
            v-for="s in spaces"
            :key="s.name"
            :variant="s.name === activeSpace ? 'subtle' : 'ghost'"
            class="!justify-start"
            @click="pickSpace(s.name)"
          >
            <Avatar :label="s.title" size="sm" shape="square" />
            <span class="ml-2 flex-1 truncate text-left">{{ s.title }}</span>
            <span v-if="s.overdue" class="text-sm text-ink-red-3">{{ s.overdue }} overdue</span>
          </Button>

          <p v-if="!spaces.length" class="px-2 py-6 text-center text-sm text-ink-gray-5">
            No spaces yet.
          </p>
        </div>
      </template>
    </Dialog>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Avatar, Button, Dialog, Dropdown } from 'frappe-ui'
import { activeSpace, setSpace, spaces, views } from '@/data/navigation'
import { session } from '@/data/session'
import { trainingCounts } from '@/data/training'

const emit = defineEmits(['open-settings', 'open-search'])

const route = useRoute()
const router = useRouter()
const showSpaces = ref(false)

const space = computed(() => spaces.value.find((s) => s.name === activeSpace.value))
const activeView = computed(() => route.query.view || 'all')
const onList = computed(() => route.name === 'Procedures')

const userMenu = [
  { label: 'My training', icon: 'lucide-graduation-cap', onClick: () => router.push('/training') },
  { label: 'Settings', icon: 'lucide-settings', onClick: () => emit('open-settings') },
  { label: 'Log out', icon: 'lucide-log-out', onClick: () => session.logout() },
]

const bottom = computed(() => [
  { label: 'Procedures', icon: 'lucide-library', value: 'all' },
  { label: 'Approvals', icon: 'lucide-stamp', value: 'approval', count: views.value[0]?.count },
  {
    label: 'Training',
    icon: 'lucide-graduation-cap',
    route: '/training',
    count: trainingCounts.data?.open,
  },
  { label: 'Due', icon: 'lucide-calendar-clock', value: 'review', count: views.value[3]?.count },
])

function go(item) {
  if (item.route) return router.push(item.route)
  openView(item.value)
}

function openView(value) {
  router.push({ path: '/', query: { space: activeSpace.value, view: value } })
}

function isActive(item) {
  return item.route ? route.path === item.route : !item.route && activeView.value === item.value
}

function pickSpace(name) {
  setSpace(name)
  showSpaces.value = false
  if (!onList.value) router.push('/')
}
</script>
