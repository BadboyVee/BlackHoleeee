// Island heightfield (CPU), shoreline distance field and shore frame.
//
// World: x = east, z = south, y = up, metres, mean sea level y = 0.
// A south-facing cove: berm and dunes behind a sandy beach, a sandbar and
// trough offshore (so swell breaks in sets), rocky headlands east and west,
// a coral reef to the south-west and deep water beyond.

import * as THREE from 'three/webgpu';
import { makeSimplex, fbm, ridged, smoothstep, lerp, clamp } from '../core/noise.js';

export const WORLD = {
  originX: -800, originZ: -900, size: 1600, res: 1024,
  deep: -70,
};
// the pier runs out past the surf to ~4 m of water, where the boat can lie
export const VILLAGE = { x0: 55, x1: 205, pierX: 118, pierZ0: -2, pierZ1: 140 };
export const REEF = { x: -150, z: 165, r: 95 };

const TEX = WORLD.size / WORLD.res;

export const ISLAND = { cx: 0, cz: -300, R: 430, bayDepth: 120, bayCenter: 0.12, baySigma: 0.58 };

function wrapAngle(a) { while (a > Math.PI) a -= 2 * Math.PI; while (a < -Math.PI) a += 2 * Math.PI; return a; }

export class Island {
  constructor(seed = 7) {
    this.noise = makeSimplex(seed);
    this.noise2 = makeSimplex(seed * 31 + 5);
    const N = WORLD.res;
    this.height = new Float32Array(N * N);
    this._generate();
    this._computeShoreField();
  }

  /** coastline radius (from the island centre) for a bearing theta (0 = south, +pi/2 = east) */
  coastRadius(theta) {
    const n = this.noise2;
    const org = fbm(n, Math.cos(theta) * 1.3 + 3.1, Math.sin(theta) * 1.3 - 7.7, 4) * 70
      + fbm(n, Math.cos(theta) * 4.0 + 1.1, Math.sin(theta) * 4.0 + 2.2, 3) * 18;
    const bay = ISLAND.bayDepth * Math.exp(-((wrapAngle(theta - ISLAND.bayCenter) / ISLAND.baySigma) ** 2));
    return ISLAND.R + org + 30 * Math.cos(2 * theta) - bay;
  }

  /** 0..1 how sandy the coast is at bearing theta */
  beachiness(theta) {
    return Math.exp(-((wrapAngle(theta - ISLAND.bayCenter) / 0.5) ** 4));
  }

  // raw analytic height before sampling
  _heightAt(x, z) {
    const n = this.noise, n2 = this.noise2;
    const dx = x - ISLAND.cx, dz = z - ISLAND.cz;
    const r = Math.hypot(dx, dz);
    const theta = Math.atan2(dx, dz);
    const warp = fbm(n2, x * 0.004, z * 0.004, 3) * 14;
    const coast = this.coastRadius(theta) + warp;
    const s = r - coast; // + seaward
    // sand/rock blend: sharp along the coast, very smooth offshore so the seabed
    // has no radial steps
    const sandyOff = Math.exp(-((wrapAngle(theta - ISLAND.bayCenter) / 0.95) ** 2));
    const sandy = lerp(this.beachiness(theta), sandyOff, smoothstep(0, 160, s));

    // --- sandy beach / seabed profile
    let hb;
    if (s >= 0) {
      hb = -2.1 * (1 - Math.exp(-s / 14)) - 0.011 * s;
      hb += 1.6 * Math.exp(-(((s - 62) / 15) ** 2)) * (0.72 + 0.28 * fbm(n, x * 0.008, 3.1, 2));   // sandbar
      hb -= 0.45 * Math.exp(-(((s - 88) / 13) ** 2));                                           // trough
      hb += fbm(n, x * 0.02, z * 0.02, 3) * 0.25 * smoothstep(20, 80, s);
    } else {
      const d = -s;
      hb = d * 0.082;                                                     // beach face ~1:12
      hb = lerp(hb, 1.85 + (d - 22) * 0.012, smoothstep(16, 30, d));      // berm
      const dunes = (0.5 + 0.5 * fbm(n, x * 0.018, z * 0.018, 4)) * 2.4;
      hb += dunes * smoothstep(26, 60, d) * (1 - smoothstep(90, 160, d) * 0.5);
    }
    // --- rocky coast: cliffs and boulder slopes, seabed drops fast
    let hr;
    const rg = ridged(n2, x * 0.012, z * 0.012, 5);
    if (s >= 0) {
      hr = -Math.min(s * 0.35, 9) - 0.02 * s + rg * 3.5 - 1.0;
    } else {
      const d = -s;
      hr = Math.min(d * 0.95, 13 + rg * 9) + rg * 4 + fbm(n, x * 0.03, z * 0.03, 3) * 2.0;
    }
    let h = lerp(hr, hb, sandy);

    // --- interior: rolling hills rising to a forested ridge
    if (s < 0) {
      const d = -s;
      const rise = smoothstep(40, 330, d);
      h += rise * (22 + 26 * (0.5 + 0.5 * fbm(n2, x * 0.003, z * 0.003, 3)));
      h += Math.max(0, fbm(n, x * 0.006, z * 0.006, 5)) * 34 * smoothstep(80, 380, d);
      h += ridged(n, x * 0.004, z * 0.004, 4) * 28 * smoothstep(150, 420, d);
    }
    // --- shelf and drop-off offshore
    if (s > 0) h -= 30 * smoothstep(230, 620, s) + 14 * smoothstep(600, 900, s);

    // --- village terrace (east side of the bay), gently graded
    const vx = smoothstep(VILLAGE.x0 - 30, VILLAGE.x0 + 10, x) * (1 - smoothstep(VILLAGE.x1 - 10, VILLAGE.x1 + 35, x));
    if (vx > 0 && s < -14) {
      const d = -s;
      const graded = 1.95 + (d - 22) * 0.045 + fbm(n, x * 0.05, z * 0.05, 2) * 0.12;
      const m = vx * smoothstep(14, 26, d) * (1 - smoothstep(95, 130, d));
      h = lerp(h, graded, m);
    }

    // --- no stray depressions below sea level inland (they would flood)
    if (s < -4) h = Math.max(h, 0.3 + Math.min(-s - 4, 20) * 0.02);

    // --- coral reef mounds
    const rd = Math.hypot(x - REEF.x, z - REEF.z) / REEF.r;
    if (rd < 1.6) {
      const m = 1 - smoothstep(0.55, 1.6, rd);
      const mounds = Math.pow(ridged(n2, x * 0.035, z * 0.035, 4), 1.4) * 5.5 + fbm(n, x * 0.08, z * 0.08, 3) * 0.8;
      h = Math.max(h, lerp(h, Math.min(-1.4, h + mounds + 1.5), m));
    }
    return h;
  }

  _generate() {
    const N = WORLD.res;
    const H = this.height;
    let mn = Infinity, mx = -Infinity;
    for (let j = 0; j < N; j++) {
      const z = WORLD.originZ + (j + 0.5) * TEX;
      for (let i = 0; i < N; i++) {
        const x = WORLD.originX + (i + 0.5) * TEX;
        let h = this._heightAt(x, z);
        // fade to the deep floor at the edges of the map
        const ex = Math.min(i, N - 1 - i) / N, ez = Math.min(j, N - 1 - j) / N;
        const edge = smoothstep(0.0, 0.08, Math.min(ex, ez));
        h = lerp(Math.min(h, WORLD.deep), h, edge);
        H[j * N + i] = h;
        if (h < mn) mn = h; if (h > mx) mx = h;
      }
    }
    this.min = mn; this.max = mx;
  }

  /** bilinear height lookup (world metres) */
  heightAt(x, z) {
    const N = WORLD.res;
    const fx = (x - WORLD.originX) / TEX - 0.5, fz = (z - WORLD.originZ) / TEX - 0.5;
    if (fx < 0 || fz < 0 || fx > N - 1 || fz > N - 1) return WORLD.deep;
    const i = Math.floor(fx), j = Math.floor(fz);
    const tx = fx - i, tz = fz - j;
    const i1 = Math.min(i + 1, N - 1), j1 = Math.min(j + 1, N - 1);
    const H = this.height;
    const a = H[j * N + i], b = H[j * N + i1], c = H[j1 * N + i], d = H[j1 * N + i1];
    return (a * (1 - tx) + b * tx) * (1 - tz) + (c * (1 - tx) + d * tx) * tz;
  }

  normalAt(x, z, out = new THREE.Vector3()) {
    const e = TEX;
    const hx = this.heightAt(x + e, z) - this.heightAt(x - e, z);
    const hz = this.heightAt(x, z + e) - this.heightAt(x, z - e);
    return out.set(-hx, 2 * e, -hz).normalize();
  }

  // --- signed distance to the y = 0 contour, and a smooth seaward direction
  _computeShoreField() {
    const N = WORLD.res;
    const land = new Uint8Array(N * N);
    for (let i = 0; i < N * N; i++) land[i] = this.height[i] > 0 ? 1 : 0;
    const dOut = edt(land, N, 1);   // distance to nearest land (for sea cells)
    const dIn = edt(land, N, 0);    // distance to nearest sea (for land cells)
    const sdf = new Float32Array(N * N);
    for (let i = 0; i < N * N; i++) sdf[i] = (land[i] ? -(dIn[i] - 0.5) : (dOut[i] - 0.5)) * TEX;
    this.sdf = sdf;
    // blurred SDF gradient -> seaward direction (wave rays run opposite)
    const blurred = boxBlur(boxBlur(sdf, N, 6), N, 6);
    const dir = new Float32Array(N * N * 2);
    for (let j = 0; j < N; j++) {
      for (let i = 0; i < N; i++) {
        const l = blurred[j * N + Math.max(i - 1, 0)], r = blurred[j * N + Math.min(i + 1, N - 1)];
        const u = blurred[Math.max(j - 1, 0) * N + i], d = blurred[Math.min(j + 1, N - 1) * N + i];
        let gx = r - l, gz = d - u;
        const len = Math.hypot(gx, gz) || 1;
        dir[(j * N + i) * 2] = gx / len; dir[(j * N + i) * 2 + 1] = gz / len;
      }
    }
    this.shoreDir = dir;
  }

  /** Packs height, shore SDF and seaward direction into a float texture. */
  createDataTexture() {
    const N = WORLD.res;
    const data = new Float32Array(N * N * 4);
    for (let i = 0; i < N * N; i++) {
      data[i * 4] = this.height[i];
      data[i * 4 + 1] = this.sdf[i];
      data[i * 4 + 2] = this.shoreDir[i * 2];
      data[i * 4 + 3] = this.shoreDir[i * 2 + 1];
    }
    const t = new THREE.DataTexture(data, N, N, THREE.RGBAFormat, THREE.FloatType);
    t.magFilter = THREE.LinearFilter;
    t.minFilter = THREE.LinearFilter;
    t.wrapS = t.wrapT = THREE.ClampToEdgeWrapping;
    t.generateMipmaps = false;
    t.needsUpdate = true;
    t.name = 'island.data';
    return t;
  }

  sdfAt(x, z) {
    const N = WORLD.res;
    const i = clamp(Math.floor((x - WORLD.originX) / TEX), 0, N - 1), j = clamp(Math.floor((z - WORLD.originZ) / TEX), 0, N - 1);
    return this.sdf[j * N + i];
  }
}

// Felzenszwalb & Huttenlocher exact Euclidean distance transform (in texels)
function edt(mask, N, target) {
  const INF = 1e20;
  const f = new Float64Array(N * N);
  for (let i = 0; i < N * N; i++) f[i] = mask[i] === target ? 0 : INF;
  const d = new Float64Array(N), v = new Int32Array(N), zz = new Float64Array(N + 1), col = new Float64Array(N);
  const pass1d = (get, set) => {
    for (let q = 0; q < N; q++) col[q] = get(q);
    let k = 0; v[0] = 0; zz[0] = -INF; zz[1] = INF;
    for (let q = 1; q < N; q++) {
      let s;
      do {
        const r = v[k];
        s = ((col[q] + q * q) - (col[r] + r * r)) / (2 * q - 2 * r);
        if (s <= zz[k]) k--; else break;
      } while (k >= 0);
      k++; v[k] = q; zz[k] = s; zz[k + 1] = INF;
    }
    k = 0;
    for (let q = 0; q < N; q++) {
      while (zz[k + 1] < q) k++;
      const r = v[k];
      d[q] = (q - r) * (q - r) + col[r];
    }
    for (let q = 0; q < N; q++) set(q, d[q]);
  };
  for (let x = 0; x < N; x++) pass1d((q) => f[q * N + x], (q, val) => { f[q * N + x] = val; });
  for (let y = 0; y < N; y++) pass1d((q) => f[y * N + q], (q, val) => { f[y * N + q] = val; });
  const out = new Float32Array(N * N);
  for (let i = 0; i < N * N; i++) out[i] = Math.sqrt(f[i]);
  return out;
}

function boxBlur(src, N, r) {
  const tmp = new Float32Array(N * N), out = new Float32Array(N * N);
  for (let j = 0; j < N; j++) {
    let acc = 0;
    for (let i = -r; i <= r; i++) acc += src[j * N + clamp(i, 0, N - 1)];
    for (let i = 0; i < N; i++) {
      tmp[j * N + i] = acc / (2 * r + 1);
      acc += src[j * N + clamp(i + r + 1, 0, N - 1)] - src[j * N + clamp(i - r, 0, N - 1)];
    }
  }
  for (let i = 0; i < N; i++) {
    let acc = 0;
    for (let j = -r; j <= r; j++) acc += tmp[clamp(j, 0, N - 1) * N + i];
    for (let j = 0; j < N; j++) {
      out[j * N + i] = acc / (2 * r + 1);
      acc += tmp[clamp(j + r + 1, 0, N - 1) * N + i] - tmp[clamp(j - r, 0, N - 1) * N + i];
    }
  }
  return out;
}
