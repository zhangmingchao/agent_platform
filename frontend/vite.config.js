import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 20001,
    proxy: {
      '/api': {
        target: 'http://localhost:20000',
        changeOrigin: true
      }
    }
  }
})