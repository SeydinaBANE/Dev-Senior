import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig(({ command }) => ({
  plugins: [react()],
  // VITE_BASE_PATH override: '/' sur Vercel, '/app/' sur self-hosted (FastAPI).
  // En dev la base est toujours '/' pour que le proxy Vite fonctionne.
  base: command === 'build' ? (process.env.VITE_BASE_PATH ?? '/app/') : '/',
  server: {
    port: 5173,
    proxy: {
      '/dev-senior': 'http://localhost:8080',
      '/biz-manager': 'http://localhost:8080',
    },
  },
}))
