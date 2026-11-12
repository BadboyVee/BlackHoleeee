#!/usr/bin/env node
// Builds the page into ONE html file - the code with three.js bundled in and
// the Blender-made textures embedded - so it runs when opened straight from
// disk, offline.
//
//   npm i --no-save esbuild three@0.186.0
//   node tools/build-single.mjs [out.html]          (default dist/sakura.html)
//
// DEPS=/path/to/node_modules picks the folder esbuild and three are
// installed in (default: ./node_modules in the sakura/ folder).

import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createRequire } from 'node:module';

const ROOT = path.resolve(fileURLToPath(new URL('..', import.meta.url)));
const DEPS = path.resolve(process.env.DEPS || path.join(ROOT, 'node_modules'));
const OUT = path.resolve(process.argv[2] || path.join(ROOT, 'dist', 'sakura.html'));
const require = createRequire(path.join(DEPS, 'resolve.js'));
const esbuild = require('esbuild');
const THREE = path.join(DEPS, 'three');
if (!fs.existsSync(path.join(THREE, 'build/three.module.js'))) throw new Error(`three.js not found in ${DEPS}`);

// the page's own module script
const html = fs.readFileSync(path.join(ROOT, 'index.html'), 'utf8');
const open = '<script type="module">';
const a = html.lastIndexOf(open), b = html.indexOf('</script>', a);
if (a < 0 || b < 0) throw new Error('module script not found in index.html');

// 'three' and its addons resolve to the installed package, like the import map does on the web
const threePlugin = {
  name: 'three',
  setup(build) {
    build.onResolve({ filter: /^three$/ }, () => ({ path: path.join(THREE, 'build/three.module.js') }));
    build.onResolve({ filter: /^three\/addons\// }, (x) => ({ path: path.join(THREE, 'examples/jsm', x.path.slice(13)) }));
  },
};
const t0 = performance.now();
const result = await esbuild.build({
  stdin: { contents: html.slice(a + open.length, b), resolveDir: ROOT, loader: 'js' },
  bundle: true, format: 'esm', target: 'es2022', minify: true, legalComments: 'none', write: false, plugins: [threePlugin],
});
const inline = (s) => s.replace(/<\/script/gi, '<\\/script');           // nothing inside may close the tag early

let out = html.slice(0, a) + open + inline(result.outputFiles[0].text) + html.slice(b);
const importMap = /<script type="importmap">[\s\S]*?<\/script>\n?/;
const textures = '<script src="assets/textures.js"></script>';
if (!importMap.test(out) || !out.includes(textures)) throw new Error('index.html no longer has the import map or the textures tag');
out = out.replace(importMap, '');
out = out.replace(textures, () => '<script>' + inline(fs.readFileSync(path.join(ROOT, 'assets/textures.js'), 'utf8')) + '</script>');

fs.mkdirSync(path.dirname(OUT), { recursive: true });
fs.writeFileSync(OUT, out);
console.log(`${path.relative(process.cwd(), OUT)}  ${(out.length / 1048576).toFixed(1)} MB  in ${((performance.now() - t0) / 1000).toFixed(1)}s`);
