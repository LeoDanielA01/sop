<template>
  <Teleport v-if="target" :to="target">
    <a
      :href="reference.url"
      target="_blank"
      class="inline-flex items-center gap-1.5 rounded border border-outline-gray-2 bg-surface-gray-1 px-1.5 py-px align-baseline text-ink-gray-8 no-underline hover:bg-surface-gray-2"
    >
      <span class="text-xs uppercase tracking-wide text-ink-gray-5">
        {{ reference.short_type || reference.reference_doctype }}
      </span>
      <span>{{ reference.label || reference.reference_name }}</span>

            <Tooltip
        v-for="badge in reference.badges || []"
        :key="badge.label"
        :text="badge.hint || ''"
      >
        <Badge :theme="tone[badge.tone] || 'gray'" variant="subtle" size="sm">
          {{ badge.label }}
        </Badge>
      </Tooltip>
    </a>
  </Teleport>
</template>

<script setup>
import { computed } from 'vue'
import { Badge, Tooltip } from 'frappe-ui'

const props = defineProps({
  reference: { type: Object, required: true },
  root: { type: [Object, null], default: null },
})

const target = computed(() => {
  if (!props.root) return null
  return props.root.querySelector(
    `[data-mention][data-doctype="${props.reference.reference_doctype}"][data-name="${props.reference.reference_name}"]`,
  )
})

const tone = {
  warning: 'amber',
  critical: 'red',
  good: 'green',
  neutral: 'gray',
}
</script>
