#!/usr/bin/env node
// Bakes the island: analytic shape, river incision and rill erosion, sky
// visibility and tree cover, written to assets/terrain/island.bin.gz.
// Run it again after changing src/world/islandShape.js or erosion.js:
//
//   node tools/bake-island.mjs
//
// (plain Node >= 18, no dependencies; takes about a minute)

import fs from 'node:fs';
import zlib from 'node:zlib';
import { fileURLToPath } from 'node:url';
import { IslandShape, WORLD, WORLD_TEXEL } from '../src/world/islandShape.js';
import { encodeIsland, decodeIsland } from '../src/world/islandData.js';

const out = fileURLToPath(new URL('../assets/terrain/island.bin.gz', import.meta.url));
const t0 = performance.now();
const shape = new IslandShape(7);
const r = shape.bake({ log: (s) => console.log('  ' + s) });
const N = WORLD.res;
const raw = encodeIsland(r, N, WORLD_TEXEL * WORLD_TEXEL);
const gz = zlib.gzipSync(raw, { level: 9 });
fs.writeFileSync(out, gz);
// round trip check: the quantized heights stay within half a step
const back = decodeIsland(zlib.gunzipSync(gz).buffer.slice(0));
let err = 0;
for (let i = 0; i < N * N; i++) err = Math.max(err, Math.abs(back.height[i] - r.height[i]));
let hMax = -Infinity;
for (const v of r.height) hMax = Math.max(hMax, v);
console.log(`wrote ${out}: ${(gz.length / 1024).toFixed(0)} KiB (raw ${(raw.length / 1048576).toFixed(1)} MiB), ` +
  `max height ${hMax.toFixed(1)} m, quantization error ${(err * 1000).toFixed(1)} mm, ${((performance.now() - t0) / 1000).toFixed(1)} s`);
