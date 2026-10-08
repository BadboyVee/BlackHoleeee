// Tileable noise textures for the cloud renderer, generated once on the GPU.
//   shape  (N³ rgba8)   r: Perlin-Worley, gba: Worley fBm at 2/4/8× base freq
//   detail (32³ rgba8)  rgb: Worley fBm at 4/8/16
//   weather (512² rgba8) r: cumulus coverage, g: height variation, b: cirrus fields
//   cirrus (1024² r8)   fibrous, domain-warped streak texture

import * as THREE from 'three/webgpu';
import {
  Fn, uint, uvec3, uvec2, vec2, vec3, vec4, float, floor, fract, dot, min, max, mix, clamp,
  length, sqrt, abs, sin, cos, pow, textureStore, instanceIndex, smoothstep, normalize, exp,
  texture,
} from 'three/tsl';

// PCG3D integer hash -> [0,1)^3
export const hash33u = (vu) => {
  let v = vu.mul(uint(1664525)).add(uint(1013904223)).toVar();
  v.x.addAssign(v.y.mul(v.z)); v.y.addAssign(v.z.mul(v.x)); v.z.addAssign(v.x.mul(v.y));
  v.bitXorAssign(v.shiftRight(uvec3(16)));
  v.x.addAssign(v.y.mul(v.z)); v.y.addAssign(v.z.mul(v.x)); v.z.addAssign(v.x.mul(v.y));
  return vec3(v).div(4294967295.0);
};

const wrapCell = (c, period) => c.sub(floor(c.div(period)).mul(period));

// periodic Worley (F1), returns 1 - distance so that cells read as billows
export const worley3 = Fn(([p, period]) => {
  const pp = p.mul(period);
  const cell = floor(pp);
  const f = fract(pp);
  const md = float(1.0).toVar();
  for (let z = -1; z <= 1; z++) for (let y = -1; y <= 1; y++) for (let x = -1; x <= 1; x++) {
    const o = vec3(x, y, z);
    const c = wrapCell(cell.add(o), period);
    const fp = hash33u(uvec3(c));
    md.assign(min(md, length(o.add(fp).sub(f))));
  }
  return float(1).sub(md);
}).setLayout({ name: 'worley3', type: 'float', inputs: [{ name: 'p', type: 'vec3' }, { name: 'period', type: 'float' }] });

const fade = (t) => t.mul(t).mul(t).mul(t.mul(t.mul(6).sub(15)).add(10));

// periodic gradient noise in [-1,1]; period per axis (cells across [0,1))
export const perlin3v = Fn(([p, period]) => {
  const pp = p.mul(period);
  const i = floor(pp);
  const f = fract(pp);
  const u = fade(f);
  const g = (o) => {
    const c = wrapCell(i.add(o), period);
    const h = hash33u(uvec3(c)).mul(2).sub(1);
    return dot(normalize(h.add(1e-5)), f.sub(o));
  };
  const n000 = g(vec3(0, 0, 0)), n100 = g(vec3(1, 0, 0)), n010 = g(vec3(0, 1, 0)), n110 = g(vec3(1, 1, 0));
  const n001 = g(vec3(0, 0, 1)), n101 = g(vec3(1, 0, 1)), n011 = g(vec3(0, 1, 1)), n111 = g(vec3(1, 1, 1));
  const x00 = mix(n000, n100, u.x), x10 = mix(n010, n110, u.x), x01 = mix(n001, n101, u.x), x11 = mix(n011, n111, u.x);
  return mix(mix(x00, x10, u.y), mix(x01, x11, u.y), u.z).mul(1.6);
}).setLayout({ name: 'perlin3v', type: 'float', inputs: [{ name: 'p', type: 'vec3' }, { name: 'period', type: 'vec3' }] });
export const perlin3 = (p, period) => perlin3v(p, vec3(period));

const remap = (v, a, b, c, d) => c.add(v.sub(a).div(b.sub(a)).mul(d.sub(c)));

// 3D noise lives in padded 2D slice atlases (sampled with two bilinear taps):
// portable to every WebGPU implementation and just as fast in practice.
export function makeAtlasInfo(size) {
  const cols = Math.ceil(Math.sqrt(size * 2) / 2) * 2 > 0 ? 16 : 16;
  const tiles = size <= 32 ? 8 : 16;
  const rows = Math.ceil(size / tiles);
  const pad = size + 2;
  return { size, tiles, rows, pad, width: tiles * pad, height: rows * pad };
}

function makeAtlas(info, name) {
  const t = new THREE.StorageTexture(info.width, info.height);
  t.format = THREE.RGBAFormat;
  // half float: the density remaps stretch the noise ~16x, which turns 8-bit
  // steps into visible contour bands through the clouds
  t.type = THREE.HalfFloatType;
  t.wrapS = t.wrapT = THREE.ClampToEdgeWrapping;
  t.magFilter = THREE.LinearFilter;
  t.minFilter = THREE.LinearFilter;
  t.generateMipmaps = false;
  t.name = name;
  return t;
}

/** TSL: trilinear sample of a periodic 3D atlas at p (periodic in [0,1)^3). */
export function sampleAtlas(tex, info, p) {
  const N = info.size;
  const q = fract(p).mul(N);
  const zf = q.z.sub(0.5);
  const z0 = floor(zf);
  const fz = zf.sub(z0);
  const s0 = z0.add(N).mod(N), s1 = z0.add(N + 1).mod(N);
  const inner = q.xy.add(1); // skip the 1-texel border
  const uvFor = (s) => {
    const tx = s.mod(info.tiles), ty = floor(s.div(info.tiles));
    return vec2(tx, ty).mul(info.pad).add(inner).div(vec2(info.width, info.height));
  };
  const a = texture(tex, uvFor(s0)).level(0);
  const b = texture(tex, uvFor(s1)).level(0);
  return mix(a, b, fz);
}

function make2D(size, name, format = THREE.RGBAFormat) {
  const t = new THREE.StorageTexture(size, size);
  t.format = format;
  t.type = THREE.UnsignedByteType;
  t.wrapS = t.wrapT = THREE.RepeatWrapping;
  t.magFilter = THREE.LinearFilter;
  t.minFilter = THREE.LinearMipmapLinearFilter;
  t.generateMipmaps = true;
  t.name = name;
  return t;
}

export async function createCloudNoise(renderer, { shapeSize = 128 } = {}) {
  const shapeInfo = makeAtlasInfo(shapeSize);
  const detailInfo = makeAtlasInfo(32);
  const shape = makeAtlas(shapeInfo, 'clouds.shape');
  const detail = makeAtlas(detailInfo, 'clouds.detail');
  // atlas texel -> (x, y, z) inside the periodic volume (borders wrap)
  const atlasCoord = (info) => {
    const ax = instanceIndex.mod(uint(info.width)), ay = instanceIndex.div(uint(info.width));
    const tx = ax.div(uint(info.pad)), ty = ay.div(uint(info.pad));
    const lx = float(ax.mod(uint(info.pad))).sub(1), ly = float(ay.mod(uint(info.pad))).sub(1);
    const z = float(ty.mul(uint(info.tiles)).add(tx));
    const p = vec3(lx, ly, z).add(0.5).div(info.size);
    return { ax, ay, p: vec3(fract(p.x.add(1)), fract(p.y.add(1)), p.z) };
  };
  const weather = make2D(512, 'clouds.weather');
  const cirrus = make2D(1024, 'clouds.cirrus');

  const shapeKernel = Fn(() => {
    const { ax, ay, p } = atlasCoord(shapeInfo);
    // Perlin fBm, 3 octaves at base period 4
    const pn = perlin3(p, float(4)).add(perlin3(p, float(8)).mul(0.5)).add(perlin3(p, float(16)).mul(0.25)).div(1.75).mul(0.5).add(0.5);
    const w1 = worley3(p, float(4)), w2 = worley3(p, float(8)), w3 = worley3(p, float(16)), w4 = worley3(p, float(32));
    const wfbm = w1.mul(0.625).add(w2.mul(0.25)).add(w3.mul(0.125));
    // Perlin-Worley: Perlin dilated by the billowy (1 - F1) Worley fBm
    const pw = clamp(remap(pn, float(0), float(1), wfbm, float(1)), 0, 1);
    const g = w1.mul(0.625).add(w2.mul(0.25)).add(w3.mul(0.125));
    const b = w2.mul(0.625).add(w3.mul(0.25)).add(w4.mul(0.125));
    const a = w3.mul(0.75).add(w4.mul(0.25));
    textureStore(shape, uvec2(ax, ay), clamp(vec4(pw, g, b, a), 0, 1));
  })().compute(shapeInfo.width * shapeInfo.height, [64]);

  const detailKernel = Fn(() => {
    const { ax, ay, p } = atlasCoord(detailInfo);
    const w1 = worley3(p, float(2)), w2 = worley3(p, float(4)), w3 = worley3(p, float(8)), w4 = worley3(p, float(16));
    const r = w1.mul(0.625).add(w2.mul(0.25)).add(w3.mul(0.125));
    const g = w2.mul(0.625).add(w3.mul(0.25)).add(w4.mul(0.125));
    const b = w3.mul(0.75).add(w4.mul(0.25));
    textureStore(detail, uvec2(ax, ay), clamp(vec4(r, g, b, 1), 0, 1));
  })().compute(detailInfo.width * detailInfo.height, [64]);

  // 2D periodic fBm helpers on top of the 3D noise (z fixed)
  const fbm2 = (uv, period, octaves, z = 0.37) => {
    let sum = float(0), amp = 0.5, norm = 0;
    for (let o = 0; o < octaves; o++) {
      sum = sum.add(perlin3(vec3(uv, z + o * 0.13), float(period * 2 ** o)).mul(amp));
      norm += amp; amp *= 0.5;
    }
    return sum.div(norm);
  };

  const weatherKernel = Fn(() => {
    const S = uint(512);
    const x = instanceIndex.mod(S), y = instanceIndex.div(S);
    const uv = vec2(float(x), float(y)).add(0.5).div(512);
    // warped low-frequency coverage -> broad cloud fields with gaps
    const warp = vec2(fbm2(uv, 2, 3, 0.11), fbm2(uv, 2, 3, 0.71)).mul(0.12);
    const cov = fbm2(uv.add(warp), 3, 5, 0.23).mul(0.5).add(0.5);
    const clusters = worley3(vec3(uv.add(warp.mul(0.5)), 0.5), float(10));
    const coverage = clamp(cov.mul(0.75).add(clusters.mul(0.35)).sub(0.12), 0, 1);
    const height = fbm2(uv, 4, 3, 0.53).mul(0.5).add(0.5);
    const cirrusField = fbm2(uv.add(warp.mul(2)), 2, 4, 0.91).mul(0.5).add(0.5);
    textureStore(weather, uvec2(x, y), vec4(coverage, height, cirrusField, 1));
  })().compute(512 * 512, [64]);

  // cirrus: fibres = strongly anisotropic noise, advected along a curling warp
  // field so the strands bend into hooks, broken into irregular wisps
  const cirrusKernel = Fn(() => {
    const S = uint(1024);
    const x = instanceIndex.mod(S), y = instanceIndex.div(S);
    const uv = vec2(float(x), float(y)).add(0.5).div(1024);
    const warp1 = vec2(fbm2(uv, 2, 3, 0.31), fbm2(uv, 2, 3, 0.83));
    const w = uv.add(warp1.mul(0.18));
    const warp2 = vec2(fbm2(w, 4, 3, 0.19), fbm2(w, 4, 3, 0.47));
    const q = w.add(warp2.mul(0.06));
    // stretch: many cycles across the fibre, few along it
    const fibres = fbm2(vec2(q.x, q.y), 3, 2, 0.61).mul(0.35)
      .add(perlin3v(vec3(q.x, q.y, 0.2), vec3(24, 6, 24)).mul(0.35))
      .add(perlin3v(vec3(q.x, q.y, 0.8), vec3(56, 11, 56)).mul(0.2))
      .add(perlin3(vec3(q.x, q.y, 0.4), float(96)).mul(0.1));
    const strands = pow(clamp(fibres.mul(0.9).add(0.5), 0, 1), float(2.2));
    const patches = clamp(fbm2(uv.add(warp1.mul(0.3)), 3, 4, 0.05).mul(1.4).add(0.35), 0, 1);
    const wisps = clamp(fbm2(q, 12, 3, 0.77).mul(1.2).add(0.6), 0, 1);
    const v = clamp(strands.mul(patches).mul(wisps).mul(1.6), 0, 1);
    textureStore(cirrus, uvec2(x, y), vec4(v, v, v, 1));
  })().compute(1024 * 1024, [64]);

  renderer.compute(shapeKernel);
  renderer.compute(detailKernel);
  renderer.compute(weatherKernel);
  renderer.compute(cirrusKernel);
  return { shape, detail, weather, cirrus, shapeInfo, detailInfo };
}
