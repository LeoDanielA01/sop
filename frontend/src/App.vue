<template>
  <div class="h-screen w-full bg-surface-base text-ink-gray-9">
    <component :is="Layout">
      <router-view :compact="!isDesktop" />
    </component>

    <AppDialogs />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import AppDialogs from '@/components/Layouts/AppDialogs.vue'
import DesktopLayout from '@/components/Layouts/DesktopLayout.vue'
import MobileLayout from '@/components/Layouts/MobileLayout.vue'
import { useBreakpoint } from '@/composables/useBreakpoint'
import { useShortcuts } from '@/composables/useShortcuts'
import { listenForCalls } from '@/data/call'
import { listenForMessages } from '@/data/chat'
import { session } from '@/data/session'

const { isDesktop } = useBreakpoint()

const Layout = computed(() => (isDesktop.value ? DesktopLayout : MobileLayout))

useShortcuts()

if (session.user.name !== 'Guest') {
  listenForMessages()
  listenForCalls()
}
</script>
