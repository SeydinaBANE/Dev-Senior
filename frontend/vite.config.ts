import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/dev-senior': 'http://localhost:8080',
      '/biz-manager': 'http://localhost:8080',
    },
  },
})
