import path from 'node:path'
import fs from 'node:fs'
import vue from '@vitejs/plugin-vue'
import frappeui from 'frappe-ui/vite'
import { defineConfig } from 'vite'

const frappeUiSubpathPlugin = {
  name: 'frappe-ui-subpath-resolver',
  setup(build) {
    build.onResolve({ filter: /^#(components|molecules|composables|utils)\// }, (args) => {
      const match = args.path.match(/^#(components|molecules|composables|utils)\/(.*)$/)
      if (match) {
        const [, dir, rest] = match
        const base = path.resolve(__dirname, `node_modules/frappe-ui/src/${dir}/${rest}`)
        for (const ext of ['', '.ts', '.js', '.vue', '/index.ts', '/index.js']) {
          const fullPath = base + ext
          if (fs.existsSync(fullPath) && fs.statSync(fullPath).isFile()) {
            if (fullPath.endsWith('.vue')) {
              return { path: fullPath, external: true }
            }
            return { path: fullPath }
          }
        }
      }
    })
  },
}

export default defineConfig({
  plugins: [
    frappeui({
      frappeProxy: true,
      lucideIcons: true,
      jinjaBootData: true,
      // The built index.html is written straight into the app's www folder,
      // so Frappe serves the SPA at /sop with boot data already injected.
      buildConfig: {
        outDir: '../sop/public/frontend',
        indexHtmlPath: '../sop/www/sop.html',
      },
    }),
    vue(),
  ],
  resolve: {
    alias: [
      { find: '@', replacement: path.resolve(__dirname, 'src') },
      { find: /^#components\/(.*)$/, replacement: path.resolve(__dirname, 'node_modules/frappe-ui/src/components/$1') },
      { find: /^#molecules\/(.*)$/, replacement: path.resolve(__dirname, 'node_modules/frappe-ui/src/molecules/$1') },
      { find: /^#composables\/(.*)$/, replacement: path.resolve(__dirname, 'node_modules/frappe-ui/src/composables/$1') },
      { find: /^#utils\/(.*)$/, replacement: path.resolve(__dirname, 'node_modules/frappe-ui/src/utils/$1') },
    ],
  },
  build: {
    outDir: '../sop/public/frontend',
    emptyOutDir: true,
    chunkSizeWarningLimit: 1000,
  },
  optimizeDeps: {
    esbuildOptions: {
      plugins: [frappeUiSubpathPlugin],
      resolveExtensions: ['.ts', '.js', '.mjs', '.json', '.vue'],
    },
  },
})
