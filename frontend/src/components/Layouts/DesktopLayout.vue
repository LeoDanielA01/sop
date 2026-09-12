<template>
  <DesktopShell>
    <template #rail>
      <AppRail />
    </template>

    <template #sidebar>
      <AppSidebar />
    </template>

    <slot />
  </DesktopShell>
</template>

<script setup>
import { DesktopShell } from 'frappe-ui'
import AppRail from './AppRail.vue'
import AppSidebar from './AppSidebar.vue'
</script>
