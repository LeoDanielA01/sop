import { createResource } from 'frappe-ui'
import { reactive } from 'vue'

const GUEST = { name: 'Guest', full_name: 'Guest', image: null, is_manager: false, is_author: false }

export const session = reactive({
  user: window.sop_user || GUEST,
  logout: () => {
    logoutResource.submit()
  },
})

const logoutResource = createResource({
  url: 'logout',
  onSuccess: () => window.location.replace('/login'),
})
