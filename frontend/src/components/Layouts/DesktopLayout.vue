<template>
  <DesktopShell :scroll="ui.pageScroll">
    <template #rail>
      <AppRail v-if="!ui.fullScreen" />
    </template>

    <template #sidebar>
      <AppSidebar v-if="!ui.sidebarCollapsed && !ui.fullScreen" />
    </template>

    <slot />
  </DesktopShell>
</template>

<script setup>
import { DesktopShell } from 'frappe-ui'
import AppRail from './AppRail.vue'
import AppSidebar from './AppSidebar.vue'
import { useUI } from '@/stores/ui'

const ui = useUI()
</script>
