import path from 'node:path'
import vue from '@vitejs/plugin-vue'
import frappeui from 'frappe-ui/vite'
import { defineConfig } from 'vite'

export default defineConfig({
  plugins: [
    frappeui({
      frappeProxy: true,
      lucideIcons: true,
      jinjaBootData: true,
      // The built index.html is written straight into the app's www folder,
      // so Frappe serves the SPA at /sop with boot data already injected.
      buildConfig: {
        indexHtmlPath: '../sop/www/sop.html',
      },
    }),
    vue(),
  ],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src'),
    },
  },
  build: {
    outDir: '../sop/public/frontend',
    emptyOutDir: true,
    chunkSizeWarningLimit: 1000,
  },
  optimizeDeps: {
    include: ['feather-icons', 'showdown', 'tailwind.config.js'],
  },
})
