import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig(({ command }) => ({
  plugins: [react()],
  // En prod, les assets sont servis sous /app par FastAPI.
  // En dev, la base reste / pour que le proxy Vite fonctionne normalement.
  base: command === 'build' ? '/app/' : '/',
  server: {
    port: 5173,
    proxy: {
      '/dev-senior': 'http://localhost:8080',
      '/biz-manager': 'http://localhost:8080',
    },
  },
}))
