import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// `base: './'` keeps every asset URL relative, so the built site works from a
// domain root (Netlify, Vercel) and from a sub-folder (GitHub Pages) alike.
export default defineConfig({
  base: './',
  plugins: [react(), tailwindcss()],
  build: {
    target: 'es2022',
    chunkSizeWarningLimit: 1400,
  },
  server: { host: true, port: 5173 },
  preview: { host: true, port: 4173 },
})
