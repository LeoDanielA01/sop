import path from 'node:path'
import vue from '@vitejs/plugin-vue'
import { defineConfig } from 'vite'
import frappeui from 'frappe-ui/vite'

export default defineConfig(({ mode }) => ({
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
    exclude: mode === 'production' ? [] : ['frappe-ui'],
  },
}))
