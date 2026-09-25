#!/usr/bin/env node
// Builds the whole game into ONE html file - the code with three.js bundled
// in, and every model, texture and sound embedded as data URLs (see
// src/core/assets.js) - so it runs when opened straight from disk, offline.
//
//   npm i --no-save esbuild three@0.186.0
//   node tools/build-single.mjs [out.html]          (default dist/saltwind-cove.html)
//
// DEPS=/path/to/node_modules picks the folder esbuild and three are
// installed in (default: ./node_modules next to this repo's ocean/ folder).

import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createRequire } from 'node:module';

const ROOT = path.resolve(fileURLToPath(new URL('..', import.meta.url)));
const DEPS = path.resolve(process.env.DEPS || path.join(ROOT, 'node_modules'));
const OUT = path.resolve(process.argv[2] || path.join(ROOT, 'dist', 'saltwind-cove.html'));
const require = createRequire(path.join(DEPS, 'resolve.js'));
const esbuild = require('esbuild');
const THREE = path.join(DEPS, 'three');
if (!fs.existsSync(path.join(THREE, 'build/three.webgpu.js'))) throw new Error(`three.js not found in ${DEPS}`);

// every bare 'three' specifier resolves to the one WebGPU build, like the import map
const threePlugin = {
  name: 'three',
  setup(b) {
    b.onResolve({ filter: /^three(\/webgpu)?$/ }, () => ({ path: path.join(THREE, 'build/three.webgpu.js') }));
    b.onResolve({ filter: /^three\/tsl$/ }, () => ({ path: path.join(THREE, 'build/three.tsl.js') }));
    b.onResolve({ filter: /^three\/addons\// }, (a) => ({ path: path.join(THREE, 'examples/jsm', a.path.slice(13)) }));
  },
};

const t0 = performance.now();
const result = await esbuild.build({
  entryPoints: [path.join(ROOT, 'src/main.js')],
  bundle: true,
  format: 'esm',
  target: 'es2022',
  minify: true,
  write: false,
  legalComments: 'eof',
  plugins: [threePlugin],
  logLevel: 'warning',
});
const js = result.outputFiles[0].text;

// ---- assets: everything under assets/ plus the Draco decoder; not the credits,
// and the sounds only as their compact Opus copies (assets/audio/opus/, made by
// tools/audio-opus.py), which keeps the file small enough to send around
const MIME = {
  '.webp': 'image/webp', '.png': 'image/png', '.jpg': 'image/jpeg', '.json': 'application/json',
  '.glb': 'model/gltf-binary', '.gz': 'application/gzip', '.mp3': 'audio/mpeg', '.wasm': 'application/wasm',
  '.js': 'text/javascript', '.bin': 'application/octet-stream', '.ogg': 'audio/ogg',
};
const assets = {};
let raw = 0;
const add = (key, file) => {
  const mime = MIME[path.extname(file)] || 'application/octet-stream';
  const buf = fs.readFileSync(file);
  raw += buf.length;
  assets[key] = `data:${mime};base64,${buf.toString('base64')}`;
};
const walk = (dir) => {
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    const f = path.join(dir, e.name);
    if (e.isDirectory()) walk(f);
    else {
      const key = path.relative(ROOT, f).split(path.sep).join('/');
      if (!key.endsWith('.md') && !/^assets\/audio\/[^/]+\.mp3$/.test(key)) add(key, f);
    }
  }
};
walk(path.join(ROOT, 'assets'));
for (const f of ['draco_wasm_wrapper.js', 'draco_decoder.wasm']) add('draco/' + f, path.join(THREE, 'examples/jsm/libs/draco/gltf', f));

// ---- page: index.html with the stylesheet inlined, the import map and the
// module entry replaced by the embedded assets and the bundle
let html = fs.readFileSync(path.join(ROOT, 'index.html'), 'utf8');
const css = fs.readFileSync(path.join(ROOT, 'src/ui/ui.css'), 'utf8');
const safe = (s) => s.replace(/<\/script/gi, '<\\/script');
const swap = (from, to) => {
  if (!from.test(html)) throw new Error(`index.html: ${from} not found`);
  html = html.replace(from, () => to);
};
swap(/<link rel="stylesheet" href="src\/ui\/ui\.css" \/>/, `<style>\n${css}\n</style>`);
swap(/<script type="importmap">[\s\S]*?<\/script>\n?/, '');
swap(/<script type="module" src="src\/main\.js"><\/script>/,
  `<script>globalThis.__SALTWIND_ASSETS__ = ${safe(JSON.stringify(assets))};</script>\n<script type="module">\n${safe(js)}\n</script>`);

fs.mkdirSync(path.dirname(OUT), { recursive: true });
fs.writeFileSync(OUT, html);
const mb = (n) => (n / 1048576).toFixed(1);
console.log(`wrote ${OUT}: ${mb(Buffer.byteLength(html))} MB (code ${mb(js.length)} MB, ${Object.keys(assets).length} assets ${mb(raw)} MB raw) in ${((performance.now() - t0) / 1000).toFixed(1)} s`);
