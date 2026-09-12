import path from 'node:path'
import fs from 'node:fs'
import { pathToFileURL } from 'node:url'
import vue from '@vitejs/plugin-vue'
import { defineConfig } from 'vite'

export default defineConfig(async ({ mode }) => {
  const isDev = mode === 'development'
  const localFrappeUI = isDev ? findLocalFrappeUI() : null
  const frappeui = await importFrappeUIPlugin(localFrappeUI)

  const config = {
    define: {
      __VUE_PROD_HYDRATION_MISMATCH_DETAILS__: 'false',
    },
    plugins: [
      frappeui({
        frappeProxy: true,
        lucideIcons: true,
        jinjaBootData: true,
        buildConfig: {
          indexHtmlPath: '../sop/www/sop.html',
          emptyOutDir: true,
        },
      }),
      vue(),
    ],
    server: {
      allowedHosts: true,
    },
    resolve: {
      alias: {
        '@': path.resolve(__dirname, 'src'),
        'tailwind.config.js': path.resolve(__dirname, 'tailwind.config.js'),
      },
      dedupe: [
        'vue',
        'prosemirror-model',
        'prosemirror-state',
        'prosemirror-view',
        'prosemirror-transform',
      ],
    },
    build: {
      outDir: '../sop/public/frontend',
      emptyOutDir: true,
      chunkSizeWarningLimit: 1500,
    },
    optimizeDeps: {
      exclude: localFrappeUI ? ['frappe-ui'] : [],
      esbuildOptions: {
        resolveExtensions: ['.ts', '.js', '.mjs', '.json', '.vue'],
      },
    },
  }

  if (localFrappeUI) {
    config.resolve.alias['frappe-ui'] = localFrappeUI
  }

  return config
})

function findLocalFrappeUI() {
  for (const candidate of ['frappe-ui', '../frappe-ui', '../../frappe-ui']) {
    const dir = path.resolve(__dirname, candidate)
    if (fs.existsSync(path.join(dir, 'package.json'))) return dir
  }

  return null
}

async function importFrappeUIPlugin(localFrappeUI) {
  if (localFrappeUI) {
    try {
      const module = await import(pathToFileURL(path.join(localFrappeUI, 'vite/index.js')).href)
      return module.default
    } catch (error) {
      console.warn('Local frappe-ui found but its vite plugin did not load:', error.message)
    }
  }

  const module = await import('frappe-ui/vite')
  return module.default
}
