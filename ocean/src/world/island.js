// Island heightfield (CPU), shoreline distance field and shore frame.
//
// The heights are baked offline (tools/bake-island.mjs, from the analytic
// shape and erosion in islandShape.js) into assets/terrain/island.bin.gz,
// together with per-texel maps the terrain shader and the vegetation read:
// drainage, erosion, sky visibility and tree cover.
//
// World: x = east, z = south, y = up, metres, mean sea level y = 0.

import * as THREE from 'three/webgpu';
import { clamp } from '../core/noise.js';
import { WORLD, VILLAGE, REEF, ISLAND, SPINE, edt, blurField } from './islandShape.js';
import { fetchIsland } from './islandData.js';
import { assetURL } from '../core/assets.js';

export { WORLD, VILLAGE, REEF, ISLAND, SPINE };

const TEX = WORLD.size / WORLD.res;

export class Island {
  /** loads the baked island (see tools/bake-island.mjs) */
  static async load(url = assetURL('assets/terrain/island.bin.gz')) {
    return new Island(await fetchIsland(url));
  }

  constructor({ N, height, aux }) {
    if (N !== WORLD.res) throw new Error(`island data is ${N}^2, expected ${WORLD.res}^2`);
    this.height = height;
    this.aux = aux;            // RGBA8 per texel: drainage, erosion, sky, forest
    let mn = Infinity, mx = -Infinity;
    for (const h of height) { if (h < mn) mn = h; if (h > mx) mx = h; }
    this.min = mn; this.max = mx;
    this._computeShoreField();
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
    const blurred = blurField(blurField(sdf, N, 6), N, 6);
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

  /** nearest-texel aux value (0..1): 0 drainage, 1 erosion, 2 sky visibility, 3 tree cover */
  auxAt(x, z, channel) {
    const N = WORLD.res;
    const i = clamp(Math.floor((x - WORLD.originX) / TEX), 0, N - 1), j = clamp(Math.floor((z - WORLD.originZ) / TEX), 0, N - 1);
    return this.aux[(j * N + i) * 4 + channel] / 255;
  }

  /** bilinear tree cover 0..1 */
  forestAt(x, z) {
    const N = WORLD.res;
    const fx = clamp((x - WORLD.originX) / TEX - 0.5, 0, N - 1.001), fz = clamp((z - WORLD.originZ) / TEX - 0.5, 0, N - 1.001);
    const i = Math.floor(fx), j = Math.floor(fz), tx = fx - i, tz = fz - j;
    const A = this.aux, k = (j * N + i) * 4 + 3, r = N * 4;
    return ((A[k] * (1 - tx) + A[k + 4] * tx) * (1 - tz) + (A[k + r] * (1 - tx) + A[k + r + 4] * tx) * tz) / 255;
  }

  /** catchment area in m^2 (decoded from the log-coded drainage map) */
  drainageAt(x, z) {
    return (Math.pow(2, this.auxAt(x, z, 0) * 255 / 12) - 1) * TEX * TEX;
  }
}
