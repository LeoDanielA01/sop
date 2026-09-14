import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useUI = defineStore('ui', () => {
  const searchDialog = ref(false)
  const settingsDialog = ref(false)
  const spaceDialog = ref(false)
  const templateDialog = ref(false)
  const processDialog = ref({ open: false, space: null, parent: null, parentTitle: null })

  const sidebarCollapsed = ref(false)
  const editorToolsPinned = ref(true)

  function askForProcess({ space, parent = null }) {
    processDialog.value = {
      open: true,
      space,
      parent: parent?.name || null,
      parentTitle: parent?.title || null,
    }
  }

  function toggleSidebar() {
    sidebarCollapsed.value = !sidebarCollapsed.value
  }

  return {
    searchDialog,
    settingsDialog,
    spaceDialog,
    templateDialog,
    processDialog,
    sidebarCollapsed,
    editorToolsPinned,
    askForProcess,
    toggleSidebar,
  }
})
