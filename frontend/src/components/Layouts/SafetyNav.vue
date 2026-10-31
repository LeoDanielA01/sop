<template>
  <nav class="space-y-0.5">
    <SidebarItem :active="route.path === '/where-used'" @click="router.push('/where-used')">
      <template #prefix>
        <span class="lucide-network size-4" aria-hidden="true" />
      </template>
      <span class="flex-1 truncate text-sm">{{ __('Where used') }}</span>
    </SidebarItem>

    <SidebarItem v-if="authoring.data?.erpnext" :active="route.path === '/issue'" @click="router.push('/issue')">
      <template #prefix>
        <span class="lucide-hand-helping size-4" aria-hidden="true" />
      </template>
      <span class="flex-1 truncate text-sm">{{ __('Issue to employee') }}</span>
    </SidebarItem>

    <template v-if="resourceTypes.length || session.user.is_manager">
      <p class="px-2 pb-1 pt-4 text-xs font-medium text-ink-gray-5">{{ __('Resources') }}</p>

      <SidebarItem v-for="item in resourceTypes" :key="item.name" :active="isActive(item.url)" @click="router.push(item.url)">
        <template #prefix>
          <span :class="item.icon" class="size-4" aria-hidden="true" />
        </template>
        <span class="flex-1 truncate text-sm">{{ item.name }}</span>
        <span class="text-xs tabular-nums text-ink-gray-5">{{ item.count }}</span>
      </SidebarItem>

      <SidebarItem v-if="session.user.is_manager" :active="isActive(typesUrl)" @click="router.push(typesUrl)">
        <template #prefix>
          <span class="lucide-shapes size-4" aria-hidden="true" />
        </template>
        <span class="flex-1 truncate text-sm">{{ resourceTypes.length ? __('Resource types') : __('Add a resource type') }}</span>
      </SidebarItem>
    </template>

    <template v-if="linked.length">
      <p class="px-2 pb-1 pt-4 text-xs font-medium text-ink-gray-5">{{ __('Other records') }}</p>

      <SidebarItem v-for="item in linked" :key="item.value" :active="isActive(item.url)" @click="router.push(item.url)">
        <template #prefix>
          <span :class="item.icon" class="size-4" aria-hidden="true" />
        </template>
        <span class="flex-1 truncate text-sm">{{ item.label }}</span>
      </SidebarItem>
    </template>

    <SidebarItem v-if="session.user.is_manager" class="mt-3" @click="ui.openSettings('linked-records')">
      <template #prefix>
        <span class="lucide-settings size-4" aria-hidden="true" />
      </template>
      <span class="flex-1 truncate text-sm">{{ __('Set up linked records') }}</span>
    </SidebarItem>
  </nav>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { SidebarItem, createResource } from 'frappe-ui'
import { session } from '@/data/session'
import { useUI } from '@/stores/ui'
import { listPath } from '@/utils/records'
import { translate as __ } from '@/translation'

const RESOURCE = 'SOP Resource'

const route = useRoute()
const router = useRouter()
const ui = useUI()
const authoring = createResource({ url: 'sop.api.settings.authoring', auto: true, cache: 'sop-authoring' })
const types = createResource({ url: 'sop.api.where_used.types', auto: true, cache: 'sop-where-used-types' })
const resources = createResource({ url: 'sop.resources.nav_types', auto: true, cache: 'sop-resource-types' })

const typesUrl = listPath('SOP Resource Type')

const resourceTypes = computed(() =>
  (resources.data || []).map((row) => ({
    ...row,
    icon: row.icon || 'lucide-box',
    url: listPath(RESOURCE, { resource_type: row.name }),
  })),
)

const linked = computed(() =>
  (types.data || [])
    .filter((row) => row.configured && row.value !== RESOURCE)
    .map((row) => ({
      value: row.value,
      label: row.label,
      icon: row.icon || 'lucide-link',
      url: listPath(row.value),
    })),
)

function isActive(url) {
  return router.resolve(url).fullPath === route.fullPath
}
</script>
