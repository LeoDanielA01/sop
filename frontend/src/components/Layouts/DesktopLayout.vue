<template>
  <ContextMenu :options="options">
    <div class="h-full" @contextmenu.capture="onContextMenu">
      <DesktopShell :scroll="!route.meta.fixed">
        <template #rail>
          <AppRail v-if="!ui.fullScreen" />
        </template>

        <template #sidebar>
          <AppSidebar v-if="!ui.sidebarCollapsed && !ui.fullScreen" />
        </template>

        <slot />
      </DesktopShell>
    </div>
  </ContextMenu>
</template>

<script setup>
import { useRoute } from 'vue-router'
import { ContextMenu, DesktopShell } from 'frappe-ui'
import AppRail from './AppRail.vue'
import AppSidebar from './AppSidebar.vue'
import { useAppMenu } from '@/composables/useAppMenu'
import { useUI } from '@/stores/ui'

const route = useRoute()
const ui = useUI()
const { options, onContextMenu } = useAppMenu()
</script>
