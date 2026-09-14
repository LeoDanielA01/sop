<template>
  <SidebarItem class="group" :active="activeProcess === node.name" @click="open">
    <template v-if="node.children.length" #prefix>
      <Button
        variant="ghost"
        size="sm"
        class="!size-4 !p-0"
        :icon="isOpen ? 'lucide-chevron-down' : 'lucide-chevron-right'"
        :label="isOpen ? 'Collapse' : 'Expand'"
        @click.stop="toggle(node.name)"
      />
    </template>

    <span class="flex-1 truncate text-sm">{{ node.title }}</span>

    <template #suffix>
      <Tooltip text="Add a process inside this one">
        <Button
          variant="ghost"
          size="sm"
          class="!size-5 !p-0 opacity-0 group-hover:opacity-100 group-focus-within:opacity-100"
          icon="lucide-plus"
          label="Add a step"
          @click.stop="emit('add', node)"
        />
      </Tooltip>
      <span
        v-if="node.total"
        class="min-w-4 text-right text-xs tabular-nums text-ink-gray-5 group-hover:hidden"
      >
        {{ node.total }}
      </span>
    </template>
  </SidebarItem>

  <div
    v-if="isOpen && node.children.length"
    class="ml-3 space-y-0.5 border-l pl-1"
    :class="holdsActive ? 'border-outline-gray-4' : 'border-outline-gray-2'"
  >
    <ProcessNode
      v-for="child in node.children"
      :key="child.name"
      :node="child"
      @add="emit('add', $event)"
    />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { Button, SidebarItem, Tooltip } from 'frappe-ui'
import { activeProcess, expanded, setProcess, toggle } from '@/data/processes'
import { activeSpace } from '@/data/navigation'

const props = defineProps({
  node: { type: Object, required: true },
})

const emit = defineEmits(['add'])

const router = useRouter()

const isOpen = computed(() => expanded.value.has(props.node.name))

const holdsActive = computed(() => contains(props.node, activeProcess.value))

function contains(node, name) {
  if (!name) return false

  return (node.children || []).some((child) => child.name === name || contains(child, name))
}

function open() {
  setProcess(props.node.name)
  router.push({ path: '/', query: { space: activeSpace.value, process: props.node.name } })
}
</script>
