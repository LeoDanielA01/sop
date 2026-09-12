import { ref } from 'vue'

export const searchDialog = ref(false)
export const settingsDialog = ref(false)
export const spaceDialog = ref(false)
export const templateDialog = ref(false)
export const processDialog = ref({ open: false, space: null, parent: null, parentTitle: null })

export function askForProcess({ space, parent = null }) {
  processDialog.value = {
    open: true,
    space,
    parent: parent?.name || null,
    parentTitle: parent?.title || null,
  }
}
