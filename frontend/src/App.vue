<template>
  <div class="h-screen w-full bg-surface-base text-ink-gray-9">
    <component :is="Layout">
      <router-view :compact="!isDesktop" />
    </component>

    <Dialogs />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import Dialogs from '@/components/Dialogs.vue'
import DesktopLayout from '@/components/Layouts/DesktopLayout.vue'
import MobileLayout from '@/components/Layouts/MobileLayout.vue'
import { useBreakpoint } from '@/composables/useBreakpoint'
import { useShortcuts } from '@/composables/useShortcuts'

const { isDesktop } = useBreakpoint()

const Layout = computed(() => (isDesktop.value ? DesktopLayout : MobileLayout))

useShortcuts()
</script>
