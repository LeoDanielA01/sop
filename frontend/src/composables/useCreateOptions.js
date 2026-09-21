import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { activeSpace } from '@/data/navigation'
import { session } from '@/data/session'
import { useUI } from '@/stores/ui'
import { translate as __ } from '@/translation'

export function useCreateOptions() {
  const router = useRouter()
  const ui = useUI()

  return computed(() => [
    {
      label: __('Procedure'),
      icon: 'lucide-file-plus-2',
      onClick: () => router.push('/new'),
      condition: () => !!session.user.is_author,
    },
    {
      label: __('Procedure from a template'),
      icon: 'lucide-sparkles',
      onClick: () => (ui.templateDialog = true),
      condition: () => !!session.user.is_author && !!activeSpace.value,
    },
    {
      label: __('Process'),
      icon: 'lucide-workflow',
      onClick: () => ui.askForProcess({ space: activeSpace.value }),
      condition: () => !!session.user.is_author && !!activeSpace.value,
    },
    {
      label: __('Space'),
      icon: 'lucide-folder-plus',
      onClick: () => (ui.spaceDialog = true),
    },
    {
      label: __('Training session'),
      icon: 'lucide-calendar-plus',
      onClick: () => {
        router.push('/training/sessions')
        ui.sessionDialog = true
      },
    },
    {
      label: __('Training rule'),
      icon: 'lucide-scroll-text',
      onClick: () => router.push('/training/rules'),
    },
  ])
}
