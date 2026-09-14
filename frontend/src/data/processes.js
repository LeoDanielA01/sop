import { createResource } from 'frappe-ui'
import { computed, ref, watch } from 'vue'
import { activeSpace } from '@/data/navigation'

export const activeProcess = ref(null)
export const expanded = ref(new Set())

export const processTree = createResource({
  url: 'sop.api.processes.tree',
  auto: true,
  makeParams: () => ({ space: activeSpace.value }),
})

export const processes = computed(() => processTree.data || [])

export const createProcess = createResource({
  url: 'sop.api.processes.create_process',
  onSuccess(process) {
    processTree.reload()
    if (process.parent) expanded.value = new Set([...expanded.value, process.parent])
  },
})

export const trailResource = createResource({ url: 'sop.api.processes.trail' })

export const trail = computed(() => (activeProcess.value ? trailResource.data || [] : []))

export const templates = createResource({ url: 'sop.api.processes.templates', auto: true })

export const applyTemplate = createResource({
  url: 'sop.api.processes.apply_to_space',
  onSuccess: () => processTree.reload(),
})

watch(activeSpace, () => {
  activeProcess.value = null
  expanded.value = new Set()
  processTree.reload()
})

export function setProcess(name) {
  activeProcess.value = name || null

  if (name) trailResource.submit({ process: name })
}

export function toggle(name) {
  const next = new Set(expanded.value)
  next.has(name) ? next.delete(name) : next.add(name)
  expanded.value = next
}

export function flatten(nodes, depth = 0, out = []) {
  for (const node of nodes) {
    out.push({ ...node, depth })
    flatten(node.children || [], depth + 1, out)
  }

  return out
}
