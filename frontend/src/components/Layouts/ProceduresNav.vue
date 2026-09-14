<template>
  <nav class="space-y-0.5">
    <SidebarItem :active="isAll" @click="openView('all')">
      <template #prefix>
        <span class="lucide-library size-4" aria-hidden="true" />
      </template>
      <span class="flex-1 truncate text-sm">All procedures</span>
    </SidebarItem>
  </nav>

  <div class="mt-4 flex h-7 items-center justify-between">
    <SidebarLabel>Spaces</SidebarLabel>
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

  <nav class="mt-0.5 space-y-0.5">
    <template v-for="space in spaces" :key="space.name">
      <SidebarItem :active="activeSpace === space.name && !activeProcess" @click="pick(space)">
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
              class="!size-5 !p-0"
              icon="lucide-plus"
              label="Add a process"
              @click.stop="add(space, null)"
            />
          </Tooltip>
          <span
            v-if="space.overdue"
            class="mr-1 grid size-4 place-content-center text-xs text-ink-red-3"
          >
            {{ space.overdue }}
          </span>
        </template>
      </SidebarItem>

      <div
        v-if="activeSpace === space.name"
        class="ml-[0.9rem] space-y-0.5 border-l border-outline-gray-2 pl-1.5"
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
      <div v-for="row in 3" :key="row" class="h-4 animate-pulse rounded bg-surface-gray-2" />
    </div>

    <div
      v-else-if="spacesResource.error"
      class="flex flex-col items-start gap-1 px-2 py-2 text-sm text-ink-gray-5"
    >
      <p>The spaces did not load.</p>
      <Button
        variant="ghost"
        size="sm"
        icon-left="lucide-rotate-cw"
        label="Try again"
        @click="spacesResource.reload()"
      />
    </div>

    <p v-else-if="!spaces.length" class="px-2 py-2 text-sm text-ink-gray-5">
      No spaces yet. A space is a binder — QA, Manufacturing, HR.
    </p>
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
import { activeProcess, processTree, processes, setProcess } from '@/data/processes'
import { useUI } from '@/stores/ui'

const route = useRoute()
const router = useRouter()
const ui = useUI()
const { activeView } = useSection()

const isAll = computed(
  () => route.name === 'Procedures' && activeView.value === 'all' && !activeProcess.value,
)

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
