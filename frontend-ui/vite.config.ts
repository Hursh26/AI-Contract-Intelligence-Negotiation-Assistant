import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// Dev server runs on :3000 (the port the backend's CORS list already allows).
// /api is proxied to the FastAPI backend so the browser never needs CORS.
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 3000,
    proxy: {
      '/api': process.env.VITE_BACKEND_URL ?? 'http://localhost:8000',
    },
  },
})
