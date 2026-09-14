<template>
  <Breadcrumbs :items="items" />
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { Breadcrumbs } from 'frappe-ui'
import { useSection } from '@/composables/useSection'
import { activeSpace } from '@/data/navigation'
import { trail } from '@/data/processes'
import { procedure } from '@/data/procedures'

const props = defineProps({
  tail: { type: Array, default: () => [] },
})

const route = useRoute()
const { section, space } = useSection()

const PROCEDURE_ROUTES = ['Procedure', 'EditProcedure', 'History']

const doc = computed(() => {
  const data = procedure.data
  return PROCEDURE_ROUTES.includes(route.name) && data?.name === route.params.name ? data : null
})

const items = computed(() => {
  if (section.value === 'training') {
    return [{ label: 'Training', route: '/training' }, ...props.tail]
  }

  const crumbs = [{ label: 'Procedures', route: '/' }]
  const spaceName = doc.value?.space || activeSpace.value
  const spaceTitle = doc.value ? doc.value.space_title || doc.value.space : space.value?.title

  if (spaceTitle) {
    crumbs.push({ label: spaceTitle, route: `/?space=${spaceName}` })
  }

  for (const step of doc.value ? doc.value.process_trail || [] : trail.value) {
    crumbs.push({ label: step.title, route: `/?space=${spaceName}&process=${step.name}` })
  }

  return [...crumbs, ...props.tail]
})
</script>
