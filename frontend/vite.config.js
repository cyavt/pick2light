import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://core-api:8002',
        changeOrigin: true,
      },
      '/auth': {
        target: 'http://auth-service:8001',
        changeOrigin: true,
      },
      '/ws': {
        target: 'ws://ws-service:8003',
        ws: true,
      },
    },
  },
})
