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

      <Button variant="ghost" icon="lucide-search" label="Search" @click="ui.searchDialog = true" />
      <Button variant="ghost" label="Account" @click="ui.profileDialog = true">
        <Avatar :image="session.user.image" :label="session.user.full_name" size="sm" />
      </Button>
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
        <span class="relative">
          <span
            :class="[item.icon, isActive(item) ? 'text-ink-gray-9' : 'text-ink-gray-5']"
            class="size-5"
            aria-hidden="true"
          />
          <span
            v-if="item.count"
            class="absolute -right-2 -top-1 grid min-w-4 place-content-center rounded-full bg-surface-red-6 px-1 text-[10px] font-medium text-white"
          >
            {{ item.count }}
          </span>
        </span>
        <span
          class="max-w-full truncate text-xs"
          :class="isActive(item) ? 'text-ink-gray-9' : 'text-ink-gray-5'"
        >
          {{ item.label }}
        </span>
      </Button>
    </nav>

    <Dialog v-model:open="showSpaces" title="Spaces" size="sm">
      <template #default>
        <div class="flex flex-col gap-1">
          <Button
            v-for="row in spaces"
            :key="row.name"
            :variant="row.name === activeSpace ? 'subtle' : 'ghost'"
            class="!justify-start"
            @click="pickSpace(row.name)"
          >
            <Avatar :label="row.title" size="sm" shape="square" />
            <span class="ml-2 flex-1 truncate text-left">{{ row.title }}</span>
            <span v-if="row.overdue" class="text-sm text-ink-red-3">{{ row.overdue }} overdue</span>
          </Button>

          <template v-if="tree.length">
            <div class="mt-2 px-2 text-sm text-ink-gray-5">Processes</div>
            <Button
              v-for="node in tree"
              :key="node.name"
              :variant="node.name === activeProcess ? 'subtle' : 'ghost'"
              class="!justify-start"
              @click="pickProcess(node)"
            >
              <span
                class="min-w-0 flex-1 truncate text-left"
                :style="{ paddingLeft: `${node.depth * 0.75}rem` }"
              >
                {{ node.title }}
              </span>
              <span v-if="node.total" class="text-sm text-ink-gray-5">{{ node.total }}</span>
            </Button>
          </template>

          <Button variant="subtle" icon-left="lucide-plus" label="New space" @click="newSpace" />

          <p v-if="!spaces.length" class="px-2 pb-2 pt-4 text-center text-sm text-ink-gray-5">
            A space is a binder — QA, Production, HR. Procedures are numbered from its code.
          </p>
        </div>
      </template>
    </Dialog>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Avatar, Button, Dialog } from 'frappe-ui'
import { useSection } from '@/composables/useSection'
import { activeSpace, setSpace, spaces, views } from '@/data/navigation'
import { activeProcess, flatten, processes, setProcess } from '@/data/processes'
import { session } from '@/data/session'
import { trainingCounts } from '@/data/training'
import { useUI } from '@/stores/ui'

const route = useRoute()
const router = useRouter()
const ui = useUI()
const showSpaces = ref(false)

const { space, activeView } = useSection()
const onList = computed(() => route.name === 'Procedures')
const tree = computed(() => flatten(processes.value))


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

function newSpace() {
  showSpaces.value = false
  ui.spaceDialog = true
}

function pickSpace(name) {
  setSpace(name)
  setProcess(null)
  showSpaces.value = false
  router.push({ path: '/', query: { space: name } })
}

function pickProcess(node) {
  setProcess(node.name)
  showSpaces.value = false
  router.push({ path: '/', query: { space: activeSpace.value, process: node.name } })
}
</script>
