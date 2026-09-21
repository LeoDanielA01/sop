import { defineStore } from 'pinia'
import { ref, watch } from 'vue'

const KEY = 'sop:sounds'

function stored() {
  try {
    return localStorage.getItem(KEY) !== 'off'
  } catch {
    return true
  }
}

export const useSound = defineStore('sound', () => {
  const on = ref(stored())

  watch(on, (value) => {
    try {
      localStorage.setItem(KEY, value ? 'on' : 'off')
    } catch {
      return
    }
  })

  function toggle() {
    on.value = !on.value
  }

  return { on, toggle }
})
