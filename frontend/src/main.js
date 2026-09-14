import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { FrappeUI, frappeRequest, setConfig } from 'frappe-ui'
import router from './router'
import './index.css'

setConfig('resourceFetcher', frappeRequest)

async function hydrate() {
  if (window.csrf_token) return

  const response = await fetch('/api/method/sop.api.session.me', {
    headers: { Accept: 'application/json' },
  })

  if (!response.ok) return

  const { message } = await response.json()
  window.sop_user = message
  window.csrf_token = message.csrf_token
}

async function start() {
  await hydrate().catch(() => {})

  const { default: App } = await import('./App.vue')

  const app = createApp(App)
  app.use(createPinia())
  app.use(router)
  app.use(FrappeUI)
  app.mount('#app')
}

start()
