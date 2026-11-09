#!/usr/bin/env node
/*
 * Runs the scene generator and writes the voxel grid for the offline path tracer.
 *
 *   node tools/export.js [out.bin]
 *
 * File layout (little endian):
 *   "VXP1"  int32 nx, ny, nz, npal
 *   float32 eye[3], target[3], fov, sun[3]
 *   npal x { uint8 r, g, b, kind; float32 vary }
 *   nx*ny*nz bytes, index = x + nx * (z + nz * y)   (see encode() in scene.js)
 */
const fs = require('fs');
const path = require('path');
const scene = require(path.join(__dirname, '..', 'scene.js'))();

const out = process.argv[2] || 'scene.bin';
const t0 = Date.now();
const built = scene.build((stage, f) => process.stderr.write(`\r${(f * 100).toFixed(0).padStart(3)}% ${stage}        `));
const enc = scene.encode(built.vox, (stage, f) => process.stderr.write(`\r${(f * 100).toFixed(0).padStart(3)}% ${stage}        `));
process.stderr.write('\n');

let solid = 0;
for (let i = 0; i < built.vox.length; i++) if (built.vox[i]) solid++;

const pal = scene.palette;
const head = Buffer.alloc(4 + 16 + 40 + pal.length * 8);
let o = 0;
head.write('VXP1', o); o += 4;
for (const v of [scene.NX, scene.NY, scene.NZ, pal.length]) { head.writeInt32LE(v, o); o += 4; }
for (const v of [...scene.view.eye, ...scene.view.target, scene.view.fov, ...scene.sun]) { head.writeFloatLE(v, o); o += 4; }
for (const p of pal) {
  const n = parseInt(p.hex.slice(1), 16);
  head[o++] = (n >> 16) & 255; head[o++] = (n >> 8) & 255; head[o++] = n & 255; head[o++] = p.kind;
  head.writeFloatLE(p.vary, o); o += 4;
}
const fd = fs.openSync(out, 'w');
fs.writeSync(fd, head);
fs.writeSync(fd, enc);
fs.closeSync(fd);
console.log(`${out}: ${scene.NX}x${scene.NY}x${scene.NZ}, ${solid.toLocaleString()} solid voxels, ${pal.length} materials, pagoda top y=${built.pagodaTop}, ${((Date.now() - t0) / 1000).toFixed(1)}s`);
