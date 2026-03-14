import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// In Docker use VITE_PROXY_TARGET=http://server:8000
const proxyTarget = process.env.VITE_PROXY_TARGET || 'http://localhost:8000'
const publicHost = process.env.VITE_PUBLIC_HOST

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  // Proxy API requests to Django during development
  server: {
    host: '0.0.0.0',
    allowedHosts: publicHost ? [publicHost] : true,
    hmr: publicHost
      ? {
          host: publicHost,
          protocol: 'wss',
          clientPort: 443,
        }
      : undefined,
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
