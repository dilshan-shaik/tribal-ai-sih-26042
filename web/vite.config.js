import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// The API is served by the same FastAPI process in production (relative URLs),
// and proxied during `vite dev` so browser-facing code never talks to localhost.
export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5173,
    proxy: {
      '/api': { target: 'http://127.0.0.1:8000', changeOrigin: true },
      '/audio': { target: 'http://127.0.0.1:8000', changeOrigin: true },
    },
  },
  build: { outDir: 'dist', sourcemap: false, chunkSizeWarningLimit: 900 },
})
