<template>
  <CommandPalette v-model:open="ui.searchDialog" />
  <SpaceDialog v-model:open="ui.spaceDialog" />
  <ProcessDialog />
  <TemplateDialog />
  <FindReplaceDialog v-model:open="ui.replaceDialog" />
  <Settings v-model:open="ui.settingsDialog" />
</template>

<script setup>
import CommandPalette from '@/components/CommandPalette.vue'
import FindReplaceDialog from '@/components/FindReplaceDialog.vue'
import ProcessDialog from '@/components/ProcessDialog.vue'
import Settings from '@/components/Settings.vue'
import TemplateDialog from '@/components/TemplateDialog.vue'
import SpaceDialog from '@/components/SpaceDialog.vue'
import { useUI } from '@/stores/ui'

const ui = useUI()
</script>
