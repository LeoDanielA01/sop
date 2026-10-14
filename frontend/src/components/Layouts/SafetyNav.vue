<template>
  <nav class="space-y-0.5">
    <SidebarItem :active="route.path === '/where-used'" @click="router.push('/where-used')">
      <template #prefix>
        <span class="lucide-network size-4" aria-hidden="true" />
      </template>
      <span class="flex-1 truncate text-sm">{{ __('Where used') }}</span>
    </SidebarItem>

    <SidebarItem v-if="authoring.data?.erpnext" :active="route.path === '/issue-ppe'" @click="router.push('/issue-ppe')">
      <template #prefix>
        <span class="lucide-hand-helping size-4" aria-hidden="true" />
      </template>
      <span class="flex-1 truncate text-sm">{{ __('Issue PPE') }}</span>
    </SidebarItem>

    <SidebarItem v-for="item in DESK" :key="item.label" @click="open(item.url)">
      <template #prefix>
        <span :class="item.icon" class="size-4" aria-hidden="true" />
      </template>
      <span class="flex-1 truncate text-sm">{{ __(item.label) }}</span>
      <span class="lucide-external-link size-3.5 text-ink-gray-4" aria-hidden="true" />
    </SidebarItem>

    <SidebarItem v-if="session.user.is_manager" @click="ui.openSettings('linked-records')">
      <template #prefix>
        <span class="lucide-settings size-4" aria-hidden="true" />
      </template>
      <span class="flex-1 truncate text-sm">{{ __('Set up linked records') }}</span>
    </SidebarItem>
  </nav>
</template>

<script setup>
import { useRoute, useRouter } from 'vue-router'
import { SidebarItem, createResource } from 'frappe-ui'
import { session } from '@/data/session'
import { useUI } from '@/stores/ui'
import { translate as __ } from '@/translation'

const route = useRoute()
const router = useRouter()
const ui = useUI()
const authoring = createResource({ url: 'sop.api.settings.authoring', auto: true, cache: 'sop-authoring' })

const DESK = [
  { label: 'Chemicals', icon: 'lucide-flask-conical', url: '/app/sop-chemical' },
  { label: 'PPE', icon: 'lucide-hard-hat', url: '/app/sop-ppe/view/tree' },
]

function open(url) {
  window.open(url, '_blank')
}
</script>
