import { createApp } from 'vue'
import { FrappeUI, setConfig, frappeRequest } from 'frappe-ui'
import App from './App.vue'
import router from './router'
import { applyTheme } from '@/composables/useTheme'
import './index.css'

setConfig('resourceFetcher', frappeRequest)

applyTheme()

const app = createApp(App)
app.use(router)
app.use(FrappeUI)
app.mount('#app')
