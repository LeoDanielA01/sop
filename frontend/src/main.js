import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { FrappeUI, frappeRequest, setConfig } from 'frappe-ui'
import router from './router'
import translationPlugin from './translation'
import './index.css'

setConfig('resourceFetcher', frappeRequest)

async function hydrate() {
  if (window.csrf_token && window.site_name) return

  const response = await fetch('/api/method/sop.api.session.realtime', {
    headers: { Accept: 'application/json' },
  })

  if (!response.ok) return

  const { message } = await response.json()
  Object.assign(window, message)
  window.csrf_token = message.sop_user.csrf_token
}

async function start() {
  await hydrate().catch(() => {})

  const { default: App } = await import('./App.vue')

  const app = createApp(App)
  app.use(createPinia())
  app.use(router)
  app.use(FrappeUI)
  app.use(translationPlugin)
  app.mount('#app')
}

start()
