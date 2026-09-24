// Island heightfield generator (pure JS, no three.js): the analytic shape
// plus baked hydraulic erosion. tools/bake-island.mjs runs this offline and
// writes assets/terrain/island.bin.gz, which the game loads (see island.js).
//
// World: x = east, z = south, y = up, metres, mean sea level y = 0.
// A south-facing cove: berm and dunes behind a sandy beach, a sandbar and
// trough offshore (so swell breaks in sets), rocky headlands east and west,
// a coral reef to the south-west and deep water beyond. Inland, an old
// volcanic massif - a high western summit and a lower eastern one joined by
// a saddle - whose flanks the rain has cut into ridges and valleys.

import { makeSimplex, fbm, ridged, smoothstep, lerp } from '../core/noise.js';
import { erode, streamPowerErode, blur as blurField } from './erosion.js';

export const WORLD = {
  originX: -800, originZ: -900, size: 1600, res: 1024,
  deep: -70,
};
// the pier runs out past the surf to ~4 m of water, where the boat can lie
export const VILLAGE = { x0: 55, x1: 205, pierX: 118, pierZ0: -2, pierZ1: 140 };
export const REEF = { x: -150, z: 165, r: 95 };
export const ISLAND = { cx: 0, cz: -300, R: 430, bayDepth: 120, bayCenter: 0.12, baySigma: 0.58 };
// the massif's main ridge: a spine from the high western summit over a saddle
// to the lower eastern one (x, z, crest height m, flank half-width m)
export const SPINE = [
  { x: -300, z: -250, h: 58, w: 250 },
  { x: -170, z: -345, h: 108, w: 300 },
  { x: -40, z: -420, h: 72, w: 290 },
  { x: 130, z: -450, h: 86, w: 280 },
  { x: 290, z: -540, h: 48, w: 240 },
];

const TEX = WORLD.size / WORLD.res;

function wrapAngle(a) { while (a > Math.PI) a -= 2 * Math.PI; while (a < -Math.PI) a += 2 * Math.PI; return a; }
// smooth maximum (polynomial), k in metres; the rounding fades out where
// either input is near zero, so flat ground is not lifted by k/4
const smax = (a, b, k) => {
  const h = Math.max(k - Math.abs(a - b), 0) / k;
  return Math.max(a, b) + h * h * k * 0.25 * Math.min(1, Math.max(Math.min(a, b), 0) / k);
};

export class IslandShape {
  constructor(seed = 7) {
    this.noise = makeSimplex(seed);
    this.noise2 = makeSimplex(seed * 31 + 5);
    this.noise3 = makeSimplex(seed * 57 + 11);
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

  /** nearest point on the spine: arc length, perpendicular distance, crest height, half-width */
  spineFrame(x, z) {
    let best = { d2: Infinity, u: 0, h: 0, w: 1, t: 0 };
    let acc = 0;
    for (let k = 0; k < SPINE.length - 1; k++) {
      const A = SPINE[k], B = SPINE[k + 1];
      const ex = B.x - A.x, ez = B.z - A.z;
      const L2 = ex * ex + ez * ez, L = Math.sqrt(L2);
      const t = Math.min(Math.max(((x - A.x) * ex + (z - A.z) * ez) / L2, 0), 1);
      const px = A.x + ex * t - x, pz = A.z + ez * t - z;
      const d2 = px * px + pz * pz;
      if (d2 < best.d2) {
        // smooth crest height between the control points
        const tt = t * t * (3 - 2 * t);
        best = { d2, u: acc + t * L, h: lerp(A.h, B.h, tt), w: lerp(A.w, B.w, t), ax: ex / L, az: ez / L, k, t };
      }
      acc += L;
    }
    best.d = Math.sqrt(best.d2);
    return best;
  }

  /**
   * The massif: a ridge spine with a rounded crest, steep flanks and a long
   * concave foot. Spurs run straight downhill from the crest (noise stretched
   * along the fall line), so the rain has ridges and hollows to work on.
   */
  massif(x, z) {
    const n2 = this.noise2, n3 = this.noise3;
    // domain warp keeps the spine from reading as straight segments
    const wx = x + fbm(n2, x * 0.002 + 3.7, z * 0.002 - 1.9, 3) * 60;
    const wz = z + fbm(n2, x * 0.002 - 6.1, z * 0.002 + 4.4, 3) * 60;
    const f = this.spineFrame(wx, wz);
    const t = Math.min(f.d / f.w, 1);
    const prof = (1 - t) * (1 - t) * (1 + 2 * t) * 0.62 + Math.pow(1 - t, 2.6) * 0.38;
    let h = f.h * prof;
    // fall-line coordinates: across the slope (u, along the spine) and down it (d)
    const across = f.u + (f.k === 0 && f.t === 0 || f.k === SPINE.length - 2 && f.t === 1 ? Math.atan2(wz - SPINE[f.k].z, wx - SPINE[f.k].x) * 60 : 0);
    const spur = ridged(n3, across * 0.021, f.d * 0.0045 + 3.3, 3);
    const spur2 = ridged(n3, across * 0.05 + 7.7, f.d * 0.011 - 2.1, 2);
    const mid = smoothstep(0.08, 0.35, t) * (1 - smoothstep(0.75, 1.0, t));
    h += ((spur - 0.33) * 22 + (spur2 - 0.3) * 7) * mid * (f.h / 100);
    // a rounded, slightly lumpy crest instead of a knife edge
    h += fbm(n3, x * 0.011 + 9.1, z * 0.011 - 3.3, 3) * 4 * smoothstep(0.4, 0.0, t);
    return Math.max(h, 0);
  }

  // raw analytic height before erosion
  heightAt(x, z) {
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
    // --- rocky coast: cliffs and boulder slopes, seabed drops fast; the
    // broken ground stays near the cliffs, inland the cliff top smooths out
    let hr;
    const rg = ridged(n2, x * 0.012, z * 0.012, 5);
    if (s >= 0) {
      hr = -Math.min(s * 0.35, 9) - 0.02 * s + rg * 3.5 - 1.0;
    } else {
      const d = -s;
      const rough = 1 - smoothstep(25, 110, d);
      const top = 13 + lerp(ridged(n2, x * 0.012, z * 0.012, 2), rg, rough) * 9;
      hr = Math.min(d * 0.95, top) + (rg * 4 + fbm(n, x * 0.03, z * 0.03, 3) * 2.0) * rough;
    }
    let h = lerp(hr, hb, sandy);

    // --- interior: foothills behind the coast, then the massif
    if (s < 0) {
      const d = -s;
      const foot = smoothstep(40, 300, d) * (10 + 8 * (0.5 + 0.5 * fbm(n2, x * 0.004, z * 0.004, 3)));
      const m = this.massif(x, z) * smoothstep(30, 190, d);
      h += smax(foot, m, 10);
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

  /** how much erosion may change a spot: the hills, not the coast or the village */
  erodibility(x, z, h) {
    const dx = x - ISLAND.cx, dz = z - ISLAND.cz;
    const s = Math.hypot(dx, dz) - this.coastRadius(Math.atan2(dx, dz)) - fbm(this.noise2, x * 0.004, z * 0.004, 3) * 14;
    const vx = smoothstep(VILLAGE.x0 - 50, VILLAGE.x0 - 10, x) * (1 - smoothstep(VILLAGE.x1 + 10, VILLAGE.x1 + 55, x));
    const village = vx * (1 - smoothstep(120, 170, -s));
    return smoothstep(45, 110, -s) * smoothstep(3, 8, h) * (1 - village);
  }

  /** raw analytic grid and the erosion mask */
  rawGrid() {
    const N = WORLD.res;
    const H = new Float32Array(N * N);
    const mask = new Float32Array(N * N);
    for (let j = 0; j < N; j++) {
      const z = WORLD.originZ + (j + 0.5) * TEX;
      for (let i = 0; i < N; i++) {
        const x = WORLD.originX + (i + 0.5) * TEX;
        let h = this.heightAt(x, z);
        // fade to the deep floor at the edges of the map
        const ex = Math.min(i, N - 1 - i) / N, ez = Math.min(j, N - 1 - j) / N;
        const edge = smoothstep(0.0, 0.08, Math.min(ex, ez));
        h = lerp(Math.min(h, WORLD.deep), h, edge);
        H[j * N + i] = h;
        mask[j * N + i] = this.erodibility(x, z, h);
      }
    }
    return { height: H, mask };
  }

  /**
   * The full offline bake (tools/bake-island.mjs): analytic shape, river
   * incision, rill erosion, then the maps the game reads.
   *   height  Float32 metres
   *   flow    drainage area, m^2
   *   change  metres removed (-) or laid down (+) by erosion
   *   sky     0..1 sky visibility (terrain-scale ambient occlusion)
   *   forest  0..1 tree cover
   */
  bake({ log = () => {} } = {}) {
    const N = WORLD.res;
    let t = performance.now();
    const lap = (what) => { const n = performance.now(); log(`${what}: ${(n - t).toFixed(0)} ms`); t = n; };
    const raw = this.rawGrid();
    lap('analytic shape');
    const spl = streamPowerErode(raw.height, N, { mask: raw.mask, cell: TEX, iterations: 400, K: 0.002, diffusion: 0.004, talus: 0.9 });
    lap('river incision');
    const rill = erode(spl.height, N, { mask: raw.mask, droplets: 140000, radius: 2, maxSteps: 36, capacity: 3, erodeSpeed: 0.18, depositSpeed: 0.25, seed: 12 });
    lap('rill erosion');
    const height = rill.height;
    const flow = new Float32Array(N * N), change = new Float32Array(N * N);
    const cellA = TEX * TEX;
    for (let i = 0; i < N * N; i++) {
      // droplet visits count as a little catchment of their own, so rills show
      flow[i] = Math.max(spl.flow[i], rill.flow[i] * cellA * 2);
      change[i] = spl.change[i] + rill.change[i];
    }
    const sky = skyVisibility(height, N, TEX);
    lap('sky visibility');
    const sdf = signedCoastDistance(height, N);
    const forest = this.forestCover(height, flow, sdf);
    lap('forest cover');
    return { height, flow: blurField(flow, N, 1), change, sky, forest, sdf };
  }

  /**
   * Where the trees grow. Damp hollows and valley floors are wooded, ridge
   * crests and the windswept summits stay open grassland, the steepest
   * faces are rock with scrub, and the village keeps its clearing. The
   * western massif is the wilder, more wooded side.
   */
  forestCover(height, flow, sdf) {
    const N = WORLD.res;
    const n3 = this.noise3, n = this.noise;
    // curvature at two scales: + hollow / valley, - ridge / spur
    const b1 = blurField(blurField(height, N, 3), N, 3);
    const b2 = blurField(blurField(height, N, 9), N, 9);
    const out = new Float32Array(N * N);
    for (let j = 1; j < N - 1; j++) {
      const z = WORLD.originZ + (j + 0.5) * TEX;
      for (let i = 1; i < N - 1; i++) {
        const k = j * N + i;
        const h = height[k];
        const d = -sdf[k];
        if (h <= 0.5 || d < 40) continue;
        const x = WORLD.originX + (i + 0.5) * TEX;
        const gx = (height[k + 1] - height[k - 1]) / (2 * TEX), gz = (height[k + N] - height[k - N]) / (2 * TEX);
        const slope = Math.hypot(gx, gz);
        const curvS = (b1[k] - height[k]) * 0.6 + (b2[k] - b1[k]) * 0.4;     // metres above the surroundings -> hollow
        const moist = smoothstep(4, 11, Math.log2(1 + flow[k] / (TEX * TEX)));
        const patch = fbm(n3, x * 0.0085 + 1.7, z * 0.0085 - 8.2, 4);
        const fine = fbm(n, x * 0.04 - 3.1, z * 0.04 + 6.6, 2);
        let f = 0.52
          + moist * 0.45
          + smoothstep(-0.6, 2.2, curvS) * 0.35 - smoothstep(0.2, -1.8, curvS) * 0.45
          + smoothstep(-60, -260, x) * 0.28                                      // the wooded western massif
          - smoothstep(88, 112, h) * 0.5                                          // open summits
          - smoothstep(0.85, 1.25, slope) * 0.35                                  // crags
          + patch * 0.42 + fine * 0.08;
        // coastal strip: palms and scrub belong to the placement code
        f *= smoothstep(55, 110, d);
        // the village clearing and its fields
        const vx = smoothstep(VILLAGE.x0 - 45, VILLAGE.x0 - 5, x) * (1 - smoothstep(VILLAGE.x1 + 5, VILLAGE.x1 + 45, x));
        f -= vx * (1 - smoothstep(140, 200, d)) * 1.2;
        out[k] = smoothstep(0.42, 0.62, f);
      }
    }
    return out;
  }
}

/**
 * Sky visibility (sky-view factor): the cosine-weighted share of the sky a
 * horizontal patch of ground sees past the surrounding terrain, from a
 * horizon search in 16 directions out to ~150 m.
 */
export function skyVisibility(height, N, cell) {
  const out = new Float32Array(N * N);
  const DIRS = 16, steps = [1, 2, 3, 4, 6, 8, 11, 15, 20, 27, 36, 48, 64, 85];
  const dx = [], dy = [];
  for (let d = 0; d < DIRS; d++) { const a = (d + 0.5) / DIRS * Math.PI * 2; dx.push(Math.cos(a)); dy.push(Math.sin(a)); }
  const at = (x, y) => {
    x = Math.min(Math.max(x, 0), N - 1.001); y = Math.min(Math.max(y, 0), N - 1.001);
    const ix = x | 0, iy = y | 0, u = x - ix, v = y - iy, k = iy * N + ix;
    return (height[k] * (1 - u) + height[k + 1] * u) * (1 - v) + (height[k + N] * (1 - u) + height[k + N + 1] * u) * v;
  };
  for (let j = 0; j < N; j++) for (let i = 0; i < N; i++) {
    const k = j * N + i;
    const h0 = Math.max(height[k], 0);
    if (height[k] < -2) { out[k] = 1; continue; }
    let vis = 0;
    for (let d = 0; d < DIRS; d++) {
      let t2 = 0;   // max tan^2 of the horizon elevation
      for (const s of steps) {
        const rise = Math.max(at(i + dx[d] * s, j + dy[d] * s), 0) - h0;
        if (rise > 0) { const tn = rise / (s * cell); t2 = Math.max(t2, tn * tn); }
      }
      vis += 1 / (1 + t2);   // cos^2 of the horizon angle
    }
    out[k] = vis / DIRS;
  }
  return out;
}

/** signed distance (metres) to the y = 0 contour, + seaward */
export function signedCoastDistance(height, N) {
  const land = new Uint8Array(N * N);
  for (let i = 0; i < N * N; i++) land[i] = height[i] > 0 ? 1 : 0;
  const dOut = edt(land, N, 1), dIn = edt(land, N, 0);
  const sdf = new Float32Array(N * N);
  for (let i = 0; i < N * N; i++) sdf[i] = (land[i] ? -(dIn[i] - 0.5) : (dOut[i] - 0.5)) * TEX;
  return sdf;
}

// Felzenszwalb & Huttenlocher exact Euclidean distance transform (in texels)
export function edt(mask, N, target) {
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

export { TEX as WORLD_TEXEL, blurField };
