// Builds the whole site into ONE self-contained file: portfolio.html.
//
// Scripts, styles, fonts and images are all inlined, so the file works when it
// is double-clicked from disk, emailed, or dropped on any static host — no
// server, no build tools and no internet connection needed.
//
//   npm run build:single

import { readdirSync, readFileSync, rmSync, writeFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { build } from 'vite'

const root = fileURLToPath(new URL('..', import.meta.url))
const outDir = `${root}dist-single`

await build({
  root,
  logLevel: 'warn',
  build: {
    outDir,
    emptyOutDir: true,
    // Turn every imported font and image into a data: URI…
    assetsInlineLimit: () => true,
    cssCodeSplit: false,
    // …and keep the lazy-loaded 3D scene in the same script.
    rolldownOptions: { output: { codeSplitting: false } },
    chunkSizeWarningLimit: 4000,
  },
})

const assets = readdirSync(`${outDir}/assets`)
const scripts = assets.filter((f) => f.endsWith('.js'))
const styles = assets.filter((f) => f.endsWith('.css'))
if (scripts.length !== 1 || styles.length !== 1 || assets.length !== 2) {
  throw new Error(`Expected exactly one script and one stylesheet, found: ${assets.join(', ')}`)
}

// Inline code must never contain a literal closing tag or an HTML comment
// opener, or the browser would end the element early.
const js = readFileSync(`${outDir}/assets/${scripts[0]}`, 'utf8').replace(/<\/script/gi, '<\\/script')
const css = readFileSync(`${outDir}/assets/${styles[0]}`, 'utf8').replace(/<\/style/gi, '<\\/style')
if (js.includes('<!--')) throw new Error('The script contains "<!--", which is unsafe to inline.')

const favicon = `data:image/svg+xml;base64,${readFileSync(`${root}public/favicon.svg`).toString('base64')}`

let html = readFileSync(`${outDir}/index.html`, 'utf8')
let inlined = 0
html = html
  .replace(/<script type="module"[^>]*\ssrc="[^"]+"[^>]*><\/script>/, () => (inlined++, `<script type="module">${js}</script>`))
  .replace(/<link rel="stylesheet"[^>]*>/, () => (inlined++, `<style>${css}</style>`))
  .replace(/\s*<link rel="modulepreload"[^>]*>/g, '')
  .replace(/href="\.\/favicon\.svg"/, () => (inlined++, `href="${favicon}"`))
if (inlined !== 3) throw new Error(`Could not inline everything (${inlined}/3 replacements made).`)
if (/(src|href)="\.\//.test(html.replace(js, '').replace(css, ''))) throw new Error('The page still points at a separate file.')

const target = `${root}portfolio.html`
writeFileSync(target, html)
rmSync(outDir, { recursive: true, force: true })
console.log(`wrote ${target} (${(Buffer.byteLength(html) / 1024 / 1024).toFixed(2)} MB, self-contained)`)
