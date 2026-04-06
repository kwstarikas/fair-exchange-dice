import fs from 'node:fs'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// In Docker use VITE_PROXY_TARGET=https://server:8000
const proxyTarget = process.env.VITE_PROXY_TARGET || 'http://localhost:8000'
const certFile = process.env.VITE_SSL_CERT_FILE
const keyFile = process.env.VITE_SSL_KEY_FILE
const httpsConfig =
  certFile && keyFile
    ? {
        cert: fs.readFileSync(certFile),
        key: fs.readFileSync(keyFile),
      }
    : undefined

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  // Proxy API requests to Django during development
  server: {
    host: '0.0.0.0',
    https: httpsConfig,
    proxy: {
      '/api': {
        target: proxyTarget,
        changeOrigin: true,
        secure: false,
      },
      '/admin': {
        target: proxyTarget,
        changeOrigin: true,
        secure: false,
      },
    },
  },
  // Build output goes to Django's static folder
  build: {
    outDir: '../static/frontend',
    emptyOutDir: true,
  },
})
