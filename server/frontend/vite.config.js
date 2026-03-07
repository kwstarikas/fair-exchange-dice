import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// In Docker use VITE_PROXY_TARGET=http://server:8000
const proxyTarget = process.env.VITE_PROXY_TARGET || 'http://localhost:8000'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  // Proxy API requests to Django during development
  server: {
    allowedHosts: ['narcisa-kathartic-celestina.ngrok-free.dev'],
    hmr: {
      host: 'narcisa-kathartic-celestina.ngrok-free.dev',
      protocol: 'wss',
      clientPort: 443,
    },
    proxy: {
      '/api': {
        target: proxyTarget,
        changeOrigin: true,
      },
      '/admin': {
        target: proxyTarget,
        changeOrigin: true,
      },
    },
  },
  // Build output goes to Django's static folder
  build: {
    outDir: '../static/frontend',
    emptyOutDir: true,
  },
})
