<template>
  <nav class="space-y-0.5">
    <SidebarItem :active="isAll" @click="showEverything">
      <template #prefix>
        <span class="lucide-library size-4" aria-hidden="true" />
      </template>
      <span class="flex-1 truncate text-sm">All procedures</span>
    </SidebarItem>
  </nav>

  <div class="mt-4 flex h-7 items-center justify-between">
    <SidebarLabel>Spaces</SidebarLabel>

    <div class="flex items-center">
      <Tooltip :text="anyExpanded ? 'Collapse every process' : 'Expand every process'">
        <Button
          variant="ghost"
          size="sm"
          :icon="anyExpanded ? 'lucide-chevrons-down-up' : 'lucide-chevrons-up-down'"
          :label="anyExpanded ? 'Collapse all' : 'Expand all'"
          @click="toggleAll"
        />
      </Tooltip>
      <Tooltip text="New space">
        <Button
          variant="ghost"
          size="sm"
          icon="lucide-plus"
          label="New space"
          @click="ui.spaceDialog = true"
        />
      </Tooltip>
    </div>
  </div>

  <nav class="mt-0.5 space-y-0.5">
    <template v-for="space in spaces" :key="space.name">
      <SidebarItem
        class="group"
        :active="activeSpace === space.name && !activeProcess"
        @click="pick(space)"
      >
        <template #prefix>
          <span
            :class="activeSpace === space.name ? 'lucide-folder-open' : 'lucide-folder'"
            class="size-4"
            aria-hidden="true"
          />
        </template>
        <span class="flex-1 truncate text-sm">{{ space.title }}</span>
        <template #suffix>
          <Tooltip text="Add a process to this space">
            <Button
              variant="ghost"
              size="sm"
              class="!size-5 !p-0 opacity-0 group-hover:opacity-100 group-focus-within:opacity-100"
              icon="lucide-plus"
              label="Add a process"
              @click.stop="add(space, null)"
            />
          </Tooltip>
          <span
            v-if="space.overdue"
            class="min-w-4 text-right text-xs tabular-nums text-ink-red-3 group-hover:hidden"
          >
            {{ space.overdue }}
          </span>
        </template>
      </SidebarItem>

      <div
        v-if="activeSpace === space.name"
        class="ml-3 space-y-0.5 border-l border-outline-gray-2 pl-1"
      >
        <ProcessNode
          v-for="node in processes"
          :key="node.name"
          :node="node"
          @add="add(space, $event)"
        />

        <div
          v-if="!processTree.loading && !processes.length"
          class="flex flex-col items-start gap-1 py-1.5 pl-2 pr-2"
        >
          <p class="text-sm text-ink-gray-5">No processes yet.</p>
          <Button
            variant="ghost"
            size="sm"
            icon-left="lucide-sparkles"
            label="Start from a template"
            @click="ui.templateDialog = true"
          />
        </div>
      </div>
    </template>

    <div v-if="spacesResource.loading" class="flex flex-col gap-1.5 px-2 py-2">
      <div v-for="row in 3" :key="row" class="h-4 animate-pulse rounded-3 bg-surface-gray-2" />
    </div>

    <p v-else-if="spacesResource.error" class="px-2 py-2 text-sm text-ink-gray-5">
      Spaces are not reachable right now.
    </p>

    <div
      v-else-if="!spaces.length"
      class="mt-1 flex flex-col items-center gap-2 rounded-4 border border-dashed border-outline-gray-2 px-3 py-5 text-center"
    >
      <span class="lucide-library size-5 text-ink-gray-4" aria-hidden="true" />
      <div>
        <p class="text-base text-ink-gray-7">No spaces yet</p>
        <p class="mt-0.5 text-sm text-ink-gray-5">
          A space is a binder — QA, Manufacturing, HR — and its code numbers every procedure inside
          it.
        </p>
      </div>
      <Button
        variant="subtle"
        icon-left="lucide-plus"
        label="New space"
        @click="ui.spaceDialog = true"
      />
    </div>
  </nav>

  <div class="mt-4 flex h-7 items-center">
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

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Button, SidebarItem, SidebarLabel, Tooltip } from 'frappe-ui'
import ProcessNode from './ProcessNode.vue'
import { useSection } from '@/composables/useSection'
import { activeSpace, setSpace, spaces, spacesResource, views } from '@/data/navigation'
import {
  activeProcess,
  anyExpanded,
  processTree,
  processes,
  setProcess,
  toggleAll,
} from '@/data/processes'
import { useUI } from '@/stores/ui'

const route = useRoute()
const router = useRouter()
const ui = useUI()
const { activeView } = useSection()

const isAll = computed(
  () =>
    route.name === 'Procedures' &&
    activeView.value === 'all' &&
    !activeProcess.value &&
    !activeSpace.value,
)

function showEverything() {
  setProcess(null)
  setSpace(null)
  router.push({ path: '/' })
}

function openView(value) {
  setProcess(null)
  router.push({ path: '/', query: { space: activeSpace.value, view: value } })
}

function pick(space) {
  setProcess(null)
  setSpace(space.name)
  router.push({ path: '/', query: { space: space.name } })
}

function add(space, node) {
  ui.askForProcess({ space: space.name, parent: node })
}
</script>
