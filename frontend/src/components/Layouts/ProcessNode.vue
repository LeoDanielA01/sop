<template>
  <SidebarItem :active="activeProcess === node.name" @click="open">
    <template #prefix>
      <span class="flex items-center" :style="{ paddingLeft: `${node.depth * 0.75}rem` }">
        <Button
          v-if="node.children.length"
          variant="ghost"
          size="sm"
          class="!size-4 !p-0"
          :icon="isOpen ? 'lucide-chevron-down' : 'lucide-chevron-right'"
          :label="isOpen ? 'Collapse' : 'Expand'"
          @click.stop="toggle(node.name)"
        />
        <span v-else class="size-4 shrink-0" />
      </span>
    </template>

    <span class="flex-1 truncate text-sm">{{ node.title }}</span>

    <template #suffix>
      <Tooltip text="Add a process inside this one">
        <Button
          variant="ghost"
          size="sm"
          class="!size-5 !p-0"
          icon="lucide-plus"
          label="Add a step"
          @click.stop="emit('add', node)"
        />
      </Tooltip>
      <span v-if="node.total" class="mr-1 grid size-4 place-content-center text-xs text-ink-gray-5">
        {{ node.total }}
      </span>
    </template>
  </SidebarItem>

  <template v-if="isOpen">
    <ProcessNode
      v-for="child in node.children"
      :key="child.name"
      :node="{ ...child, depth: node.depth + 1 }"
      @add="emit('add', $event)"
    />
  </template>
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

function open() {
  setProcess(props.node.name)
  router.push({ path: '/', query: { space: activeSpace.value, process: props.node.name } })
}
</script>
