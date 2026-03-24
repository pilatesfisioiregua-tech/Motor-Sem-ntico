import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    proxy: {
      '/pilates': {
        target: 'https://motor-semantico-omni.fly.dev',
        changeOrigin: true,
        secure: true,
        headers: {
          'Origin': 'https://motor-semantico-omni.fly.dev',
        },
      },
    },
  },
})
