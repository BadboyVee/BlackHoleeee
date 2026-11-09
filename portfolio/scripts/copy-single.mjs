// Copies the one-file build next to the source as portfolio.html.
import { copyFileSync, statSync } from 'node:fs'
copyFileSync('dist-single/index.html', 'portfolio.html')
console.log(`portfolio.html: ${(statSync('portfolio.html').size / 1024 / 1024).toFixed(2)} MB, opens straight from disk`)
