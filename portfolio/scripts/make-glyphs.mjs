// Builds src/three/glyphs.json: a tiny three.js "typeface" font that holds only
// the code symbols floating around the scene, traced from JetBrains Mono.
//
// Shipping a dozen glyph outlines (a few KB) beats shipping a font parser.
// Re-run with `npm run glyphs` after changing CHARS.

import { readFileSync, writeFileSync } from 'node:fs'
import { createRequire } from 'node:module'
import { fileURLToPath } from 'node:url'
import opentype from 'opentype.js'

const CHARS = '</>{}()[];=#*+_'

const require = createRequire(import.meta.url)
const fontPath = require.resolve('@fontsource/jetbrains-mono/files/jetbrains-mono-latin-800-normal.woff')
const data = readFileSync(fontPath)
const font = opentype.parse(data.buffer.slice(data.byteOffset, data.byteOffset + data.byteLength))

const scale = 100000 / ((font.unitsPerEm || 2048) * 72)
const round = Math.round
const glyphs = {}

for (const char of CHARS) {
  const glyph = font.charToGlyph(char)
  const token = {
    ha: round(glyph.advanceWidth * scale),
    x_min: round(glyph.xMin * scale),
    x_max: round(glyph.xMax * scale),
    o: '',
  }
  for (const command of glyph.path.commands) {
    const type = command.type.toLowerCase() === 'c' ? 'b' : command.type.toLowerCase()
    token.o += type + ' '
    if (command.x !== undefined && command.y !== undefined) token.o += round(command.x * scale) + ' ' + round(command.y * scale) + ' '
    if (command.x1 !== undefined && command.y1 !== undefined) token.o += round(command.x1 * scale) + ' ' + round(command.y1 * scale) + ' '
    if (command.x2 !== undefined && command.y2 !== undefined) token.o += round(command.x2 * scale) + ' ' + round(command.y2 * scale) + ' '
  }
  glyphs[char] = token
}

const out = {
  glyphs,
  familyName: 'JetBrains Mono (symbols subset)',
  ascender: round(font.ascender * scale),
  descender: round(font.descender * scale),
  underlinePosition: round(font.tables.post.underlinePosition * scale),
  underlineThickness: round(font.tables.post.underlineThickness * scale),
  boundingBox: {
    xMin: round(font.tables.head.xMin * scale),
    xMax: round(font.tables.head.xMax * scale),
    yMin: round(font.tables.head.yMin * scale),
    yMax: round(font.tables.head.yMax * scale),
  },
  resolution: 1000,
  original_font_information: { license: 'SIL Open Font License 1.1 — JetBrains Mono' },
}

const target = fileURLToPath(new URL('../src/three/glyphs.json', import.meta.url))
writeFileSync(target, JSON.stringify(out))
console.log(`wrote ${target} (${Object.keys(glyphs).length} glyphs, ${JSON.stringify(out).length} bytes)`)
