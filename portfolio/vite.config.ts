import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig, type Plugin } from 'vite'
import { site } from './src/content/site.ts'

/** Fills the %SITE_*% placeholders in index.html from src/content/site.ts. */
function siteMeta(): Plugin {
  const escape = (value: string) =>
    value.replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
  const values: Record<string, string> = {
    SITE_TITLE: site.title,
    SITE_DESCRIPTION: site.description,
    SITE_NAME: site.name,
    SITE_EMAIL: site.email,
    SITE_YEAR: site.year,
    SITE_OG_IMAGE: site.ogImage,
  }
  return {
    name: 'site-meta',
    transformIndexHtml: (html) => html.replace(/%(SITE_[A-Z_]+)%/g, (match, key: string) => (key in values ? escape(values[key]) : match)),
  }
}

// https://vite.dev/config/
export default defineConfig({
  // Relative asset URLs, so the built site works from any folder:
  // a Netlify root, a GitHub Pages sub-path, or a plain static server.
  base: './',
  plugins: [siteMeta(), react(), tailwindcss()],
  build: {
    target: 'es2022',
    // three.js alone is ~700 kB minified; it gets its own long-cached chunk below.
    chunkSizeWarningLimit: 900,
    rolldownOptions: {
      output: {
        codeSplitting: {
          groups: [
            { name: 'three', test: /node_modules[\\/]three[\\/]/ },
            { name: 'r3f', test: /node_modules[\\/](@react-three|its-fine|zustand|suspend-react|tunnel-rat|react-use-measure)/ },
            { name: 'motion', test: /node_modules[\\/](gsap|@gsap|lenis)[\\/]/ },
            { name: 'react', test: /node_modules[\\/](react|react-dom|scheduler)[\\/]/ },
          ],
        },
      },
    },
  },
})
