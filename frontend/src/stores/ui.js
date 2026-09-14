import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useUI = defineStore('ui', () => {
  const searchDialog = ref(false)
  const settingsDialog = ref(false)
  const spaceDialog = ref(false)
  const templateDialog = ref(false)
  const sessionDialog = ref(false)
  const replaceDialog = ref(false)
  const profileDialog = ref(false)
  const notificationsPanel = ref(false)
  const settingsTab = ref('preferences')
  const processDialog = ref({ open: false, space: null, parent: null, parentTitle: null })

  const sidebarCollapsed = ref(false)
  const fullScreen = ref(false)
  const editorToolsPinned = ref(true)

  function askForProcess({ space, parent = null }) {
    processDialog.value = {
      open: true,
      space,
      parent: parent?.name || null,
      parentTitle: parent?.title || null,
    }
  }

  function toggleFullScreen() {
    fullScreen.value = !fullScreen.value
  }

  function toggleSidebar() {
    sidebarCollapsed.value = !sidebarCollapsed.value
  }

  function openSettings(tab = 'preferences') {
    settingsTab.value = tab
    settingsDialog.value = true
  }

  return {
    searchDialog,
    settingsDialog,
    settingsTab,
    sessionDialog,
    replaceDialog,
    profileDialog,
    notificationsPanel,
    openSettings,
    spaceDialog,
    templateDialog,
    processDialog,
    sidebarCollapsed,
    fullScreen,
    toggleFullScreen,
    editorToolsPinned,
    askForProcess,
    toggleSidebar,
  }
})
