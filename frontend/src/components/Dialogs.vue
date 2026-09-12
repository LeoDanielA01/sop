<template>
  <CommandPalette v-model:open="searchDialog" />
  <SpaceDialog v-model:open="spaceDialog" />
  <ProcessDialog />
  <TemplateDialog />
  <Settings v-model:open="settingsDialog" />
</template>

<script setup>
import CommandPalette from '@/components/CommandPalette.vue'
import ProcessDialog from '@/components/ProcessDialog.vue'
import Settings from '@/components/Settings.vue'
import TemplateDialog from '@/components/TemplateDialog.vue'
import SpaceDialog from '@/components/SpaceDialog.vue'
import { searchDialog, settingsDialog, spaceDialog } from '@/data/ui'
</script>
