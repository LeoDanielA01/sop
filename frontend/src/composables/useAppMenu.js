import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { toast } from 'frappe-ui'
import { activeSpace, setSpace, views } from '@/data/navigation'
import { setProcess } from '@/data/processes'
import { acknowledge, procedure } from '@/data/procedures'
import { session } from '@/data/session'
import { useUI } from '@/stores/ui'
import { translate as __ } from '@/translation'

const NATIVE = 'input, textarea, select'

export function useAppMenu() {
  const route = useRoute()
  const router = useRouter()
  const ui = useUI()

  const picked = ref({ text: '', route: '', href: '', target: '', process: '', space: '' })

  const current = computed(() => (route.name === 'Procedure' ? procedure.data || null : null))

  function short(text) {
    return text.length > 24 ? `${text.slice(0, 24)}…` : text
  }

  function urlOf(path) {
    return new URL(router.resolve(path).href, window.location.origin).href
  }

  function procedureOf(path) {
    if (!path) return null

    const resolved = router.resolve(path)

    return resolved.name === 'Procedure' ? String(resolved.params.name) : null
  }

  async function copy(text) {
    try {
      await navigator.clipboard.writeText(text)
      toast.success(__('Copied'))
    } catch {
      toast.error(__('Your browser did not allow copying'))
    }
  }

  function search(text) {
    ui.searchQuery = text
    ui.searchDialog = true
  }

  function showSpace(space, process = null) {
    setSpace(space)
    setProcess(process)
    router.push({ path: '/', query: process ? { space, process } : { space } })
  }

  function startIn(space, process = null) {
    setSpace(space)
    setProcess(process)
    router.push('/new')
  }

  function procedureGroup(name, doc) {
    return {
      group: doc ? __('This procedure') : name,
      options: [
        {
          label: __('Open'),
          icon: 'lucide-arrow-up-right',
          onClick: () => router.push(`/${name}`),
          condition: () => !doc,
        },
        {
          label: __('Open in new tab'),
          icon: 'lucide-external-link',
          onClick: () => window.open(urlOf(`/${name}`), '_blank'),
        },
        {
          label: __('Edit'),
          icon: 'lucide-pencil',
          onClick: () => router.push(`/${name}/edit`),
          condition: () => !!doc?.can_edit,
        },
        {
          label: __('Mark as read and understood'),
          icon: 'lucide-check-check',
          onClick: () => acknowledge.submit({ sop: name, version: doc.version }),
          condition: () => doc?.status === 'Effective' && !doc?.acknowledged,
        },
        {
          label: __('Revision history'),
          icon: 'lucide-history',
          onClick: () => router.push(`/${name}/history`),
        },
        {
          label: __('Print a controlled copy'),
          icon: 'lucide-printer',
          onClick: () => window.print(),
          condition: () => !!doc,
        },
        {
          label: ui.fullScreen ? __('Leave full screen') : __('Read full screen'),
          icon: ui.fullScreen ? 'lucide-shrink' : 'lucide-expand',
          onClick: () => ui.toggleFullScreen(),
          condition: () => !!doc,
        },
        {
          label: __('Copy procedure number'),
          icon: 'lucide-hash',
          onClick: () => copy(doc?.sop_no || name),
        },
        {
          label: __('Copy link'),
          icon: 'lucide-link',
          onClick: () => copy(urlOf(`/${name}`)),
        },
        {
          label: __('Delete draft'),
          icon: 'lucide-trash-2',
          theme: 'red',
          onClick: () => (ui.removeProcedure = { name, sop_no: doc.sop_no, mode: 'draft' }),
          condition: () => !!doc?.actions?.delete,
        },
        {
          label: __('Delete permanently'),
          icon: 'lucide-trash-2',
          theme: 'red',
          onClick: () => (ui.removeProcedure = { name, sop_no: doc.sop_no, mode: 'purge' }),
          condition: () => !!doc?.actions?.purge,
        },
      ],
    }
  }

  const options = computed(() => {
    const { text, route: path, href, target, process, space } = picked.value
    const groups = []

    if (text) {
      groups.push({
        group: __('Selection'),
        options: [
          { label: __('Copy'), icon: 'lucide-copy', onClick: () => copy(text) },
          {
            label: __('Search for “{0}”').format(short(text)),
            icon: 'lucide-search',
            onClick: () => search(text),
          },
        ],
      })
    }

    const linked = procedureOf(path)
    const plain = !path && !href && !process && !space
    const name = linked || (plain ? current.value?.name : null)

    if (name) {
      const doc = !linked || linked === current.value?.name ? current.value : null
      groups.push(procedureGroup(name, doc))
    } else if (path || href) {
      groups.push({
        group: __('Link'),
        options: [
          {
            label: __('Open'),
            icon: 'lucide-arrow-up-right',
            onClick: () => (path ? router.push(path) : window.open(href, target || '_self')),
          },
          {
            label: __('Open in new tab'),
            icon: 'lucide-external-link',
            onClick: () => window.open(path ? urlOf(path) : href, '_blank'),
          },
          {
            label: __('Copy link'),
            icon: 'lucide-link',
            onClick: () => copy(path ? urlOf(path) : href),
          },
        ],
      })
    }

    if (process) {
      groups.push({
        group: __('This process'),
        options: [
          {
            label: __('Show its procedures'),
            icon: 'lucide-list',
            onClick: () => showSpace(space, process),
          },
          {
            label: __('New procedure here'),
            icon: 'lucide-file-plus-2',
            onClick: () => startIn(space, process),
          },
        ],
      })
    } else if (space) {
      groups.push({
        group: __('This space'),
        options: [
          { label: __('Show its procedures'), icon: 'lucide-list', onClick: () => showSpace(space) },
          {
            label: __('New procedure here'),
            icon: 'lucide-file-plus-2',
            onClick: () => startIn(space),
          },
          {
            label: __('Delete space'),
            icon: 'lucide-trash-2',
            theme: 'red',
            onClick: () => (ui.removeSpace = { name: space }),
            condition: () => !!session.user.is_manager,
          },
        ],
      })
    }

    groups.push({
      group: __('Procedures'),
      options: [
        { label: __('New procedure'), icon: 'lucide-file-plus-2', onClick: () => router.push('/new') },
        {
          label: __('Search procedures'),
          icon: 'lucide-search',
          onClick: () => (ui.searchDialog = true),
        },
        {
          label: __('Find and replace'),
          icon: 'lucide-replace',
          onClick: () => (ui.replaceDialog = true),
        },
      ],
    })

    groups.push({
      group: __('My work'),
      options: [
        ...views.value.map((view) => ({
          label: view.count ? `${view.label} · ${view.count}` : view.label,
          icon: view.icon,
          onClick: () =>
            router.push({ path: '/', query: { space: activeSpace.value, view: view.value } }),
        })),
        {
          label: __('My training'),
          icon: 'lucide-graduation-cap',
          onClick: () => router.push('/training'),
        },
      ],
    })

    return groups
  })

  function onContextMenu(event) {
    const target = event.target instanceof Element ? event.target : event.target?.parentElement

    if (target?.closest('.ProseMirror')) return

    if (event.shiftKey || !target || target.closest(NATIVE)) {
      event.stopPropagation()
      return
    }

    const marked = target.closest('[data-context-link]')
    const anchor = marked ? null : target.closest('a[href]')
    const processRow = target.closest('[data-context-process]')
    const spaceRow = target.closest('[data-context-space]')

    picked.value = {
      text: (window.getSelection()?.toString() || '').trim(),
      route: marked?.dataset.contextLink || '',
      href: anchor?.href || '',
      target: anchor?.target || '',
      process: processRow?.dataset.contextProcess || '',
      space: processRow?.dataset.contextSpace || spaceRow?.dataset.contextSpace || '',
    }
  }

  return { options, onContextMenu }
}
