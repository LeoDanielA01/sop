<template>
  <CommandPalette v-model:open="ui.searchDialog" />
  <SpaceDialog v-model:open="ui.spaceDialog" />
  <ProcessDialog />
  <TemplateDialog />
  <FindReplaceDialog v-model:open="ui.replaceDialog" />
  <NotificationsPanel v-model:open="ui.notificationsPanel" />
  <ProfileDialog v-model:open="ui.profileDialog" />
  <Settings v-model:open="ui.settingsDialog" />
  <RemoveProcedureDialog />
  <RemoveSpaceDialog />
</template>

<script setup>
import CommandPalette from '@/components/Search/CommandPalette.vue'
import FindReplaceDialog from '@/components/Search/FindReplaceDialog.vue'
import NotificationsPanel from '@/components/Notifications/NotificationsPanel.vue'
import ProcessDialog from '@/components/Space/ProcessDialog.vue'
import ProfileDialog from '@/components/Account/ProfileDialog.vue'
import RemoveProcedureDialog from '@/components/Procedure/RemoveProcedureDialog.vue'
import RemoveSpaceDialog from '@/components/Space/RemoveSpaceDialog.vue'
import Settings from '@/components/Account/Settings.vue'
import TemplateDialog from '@/components/Space/TemplateDialog.vue'
import SpaceDialog from '@/components/Space/SpaceDialog.vue'
import { useUI } from '@/stores/ui'

const ui = useUI()
</script>
