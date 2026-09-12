import { createResource } from 'frappe-ui'
import { reactive } from 'vue'

export const session = reactive({
  user: window.frappe?.boot?.user || { full_name: 'Guest', image: null },
  logout: () => {
    logoutResource.submit()
  },
})

const logoutResource = createResource({
  url: 'logout',
  onSuccess: () => window.location.replace('/login'),
})
