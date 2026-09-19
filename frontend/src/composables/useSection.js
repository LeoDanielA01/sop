import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { activeSpace, spaces } from '@/data/navigation'

export function useSection() {
  const route = useRoute()

  const section = computed(() => {
    if (route.path.startsWith('/training')) return 'training'
    if (route.path.startsWith('/insights')) return 'insights'
    return 'procedures'
  })
  const space = computed(() => spaces.value.find((row) => row.name === activeSpace.value))
  const activeView = computed(() => route.query.view || 'all')

  return { section, space, activeView }
}
