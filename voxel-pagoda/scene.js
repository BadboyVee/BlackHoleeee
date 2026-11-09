/*
 * Voxel Pagoda — procedural scene generator.
 *
 * Builds the whole diorama (terrain, five-story pagoda, cherry trees, bamboo grove,
 * maples, pond, bridge, lanterns, birds) as one dense grid of cubic voxels. Nothing is
 * loaded from disk: every voxel is placed by the code below, deterministically.
 *
 * The same file feeds both renderers:
 *   - index.html runs it in a Web Worker and path-traces the grid on the GPU;
 *   - tools/export.js runs it in Node and hands the grid to the offline path tracer.
 *
 * Everything lives inside one self-contained function so it can be stringified into a
 * worker (which also keeps the page working when opened straight from file://).
 */
function voxelPagodaScene() {
  'use strict';

  // ----------------------------------------------------------------- layout
  const NX = 512, NY = 256, NZ = 480;      // grid size in voxels (x east, y up, z south)
  const NXZ = NX * NZ;
  const G = 28;                            // y of the top ground voxel at garden level
  const PX = 280, PZ = 254;                // pagoda centre (a voxel boundary: the plan is even-sized)

  // The hero camera looks at the pagoda from 35 degrees off its front face. Garden
  // features are laid out in that camera's ground frame: u = to the right, w = away.
  const AZIM = 35 * Math.PI / 180;
  const CAMX = Math.sin(AZIM), CAMZ = Math.cos(AZIM);   // pagoda -> camera
  const RX = CAMZ, RZ = -CAMX;                          // camera right
  const FX = -CAMX, FZ = -CAMZ;                         // camera forward
  const toUW = (x, z) => { const dx = x + 0.5 - PX, dz = z + 0.5 - PZ; return [dx * RX + dz * RZ, dx * FX + dz * FZ]; };
  const fromUW = (u, w) => [Math.round(PX + u * RX + w * FX), Math.round(PZ + u * RZ + w * FZ)];

  // ------------------------------------------------------------------- math
  const clamp = (v, a, b) => (v < a ? a : v > b ? b : v);
  const lerp = (a, b, t) => a + (b - a) * t;
  const smooth = (a, b, x) => { const t = clamp((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t); };

  function rng(seed) {
    let a = seed | 0;
    return function () {
      a = (a + 0x6d2b79f5) | 0;
      let t = Math.imul(a ^ (a >>> 15), 1 | a);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }
  function hash3(x, y, z) {
    let h = Math.imul(x | 0, 0x27d4eb2d) ^ Math.imul(y | 0, 0x165667b1) ^ Math.imul(z | 0, 0x9e3779b1);
    h = Math.imul(h ^ (h >>> 15), 0x85ebca6b);
    h = Math.imul(h ^ (h >>> 13), 0xc2b2ae35);
    return ((h ^ (h >>> 16)) >>> 0) / 4294967296;
  }
  function vnoise3(x, y, z) {
    const xi = Math.floor(x), yi = Math.floor(y), zi = Math.floor(z);
    let fx = x - xi, fy = y - yi, fz = z - zi;
    fx = fx * fx * (3 - 2 * fx); fy = fy * fy * (3 - 2 * fy); fz = fz * fz * (3 - 2 * fz);
    const a = hash3(xi, yi, zi), b = hash3(xi + 1, yi, zi), c = hash3(xi, yi + 1, zi), d = hash3(xi + 1, yi + 1, zi);
    const e = hash3(xi, yi, zi + 1), f = hash3(xi + 1, yi, zi + 1), g = hash3(xi, yi + 1, zi + 1), h = hash3(xi + 1, yi + 1, zi + 1);
    const ab = a + (b - a) * fx, cd = c + (d - c) * fx, ef = e + (f - e) * fx, gh = g + (h - g) * fx;
    const lo = ab + (cd - ab) * fy, hi = ef + (gh - ef) * fy;
    return lo + (hi - lo) * fz;
  }
  function fbm2(x, z, oct) {
    let s = 0, a = 0.5, n = 0;
    for (let i = 0; i < oct; i++) { s += a * vnoise3(x, i * 7.31, z); n += a; x *= 2.03; z *= 2.03; a *= 0.5; }
    return s / n;
  }

  // ---------------------------------------------------------------- palette
  // Material ids start at 1 (0 is air). kind: 0 matte, 1 water, 2 metal, 3 glowing, 4 leaf.
  const PAL = [];
  const DIFF = 0, WATER = 1, METAL = 2, EMIT = 3, LEAF = 4;
  const mat = (hex, kind, vary) => { PAL.push({ hex, kind: kind || 0, vary: vary === undefined ? 0.05 : vary }); return PAL.length; };
  const mats = (list, kind, vary) => list.map((h) => mat(h, kind, vary));

  // architecture
  const VERM = mats(['#e23f1e', '#cf3419', '#f0522a'], DIFF, 0.035);
  const VERM_D = mat('#b12a17', DIFF, 0.04);
  const PLASTER = mats(['#f5eddb', '#ebe1cc'], DIFF, 0.025);
  const WOOD_D = mat('#5e3020', DIFF, 0.06);
  const WOOD = mats(['#9a5a36', '#87492b'], DIFF, 0.05);
  const INTERIOR = mat('#2a1a15', DIFF, 0.02);
  const LATTICE = mat('#2f7d5d', DIFF, 0.05);
  const T_RIDGE = mat('#56c9b5', DIFF, 0.045), T_TILE = mat('#2fa594', DIFF, 0.06), T_TROUGH = mat('#1f867a', DIFF, 0.06);
  const T_DARK = mat('#166a60', DIFF, 0.05), T_EDGE = mat('#3db4a2', DIFF, 0.04);
  const GOLD = mat('#f2c043', METAL, 0.04), BRONZE = mat('#9c7638', METAL, 0.06);
  const STONE = mats(['#beb9ad', '#aca79b', '#cec9be', '#9c978c'], DIFF, 0.035);
  // ground
  const GRASS = mats(['#5d9f39', '#69ad3e', '#76ba45', '#84c64f', '#92cf5a'], DIFF, 0.06);
  const MOSS = mats(['#4c8a35', '#5a9a3c', '#6aa845'], DIFF, 0.06);
  const DIRT = mats(['#8b6440', '#7b5636', '#9a7149'], DIFF, 0.06);
  const ROCK = mats(['#8d9093', '#7c7f83', '#9fa2a4', '#6e7175'], DIFF, 0.05);
  const CLIFF = mats(['#a99c86', '#978a71', '#b7aa94', '#857860'], DIFF, 0.05);
  const GRAVEL = mats(['#e4dcc7', '#dad1b9', '#cdc3a9'], DIFF, 0.03);
  const PAVE = mats(['#c6c1b5', '#b4afa3', '#d4cfc4'], DIFF, 0.03);
  const PAVE_J = mat('#8f8a7f', DIFF, 0.04);
  const SAND = mats(['#c3b695', '#b3a684'], DIFF, 0.05);
  const LITTER = mats(['#b7a468', '#a6935a', '#8e9a4b', '#9c8a52'], DIFF, 0.06);
  const WATER_S = mat('#62c8cc', WATER, 0.02), WATER_M = mat('#3da8ba', WATER, 0.02), WATER_D = mat('#2c88a8', WATER, 0.02);
  const FALL = mats(['#e2f4f8', '#c9eaf2', '#f6fcfd'], DIFF, 0.03);
  const PETAL = mats(['#f9cfdc', '#f5bacd', '#fde2ea'], DIFF, 0.03);
  // trees
  const BARK_C = mats(['#4f372c', '#5e4336', '#3f2b22'], DIFF, 0.07);
  const BARK_M = mats(['#43302a', '#35251f'], DIFF, 0.07);
  const BARK_P = mats(['#74493b', '#603c30', '#855846'], DIFF, 0.07);
  const BLOSSOM = {
    pink: mats(['#f186aa', '#f69bba', '#fab1ca', '#fec6d9', '#ffdae6'], LEAF, 0.045),
    white: mats(['#f3c0d0', '#f9d6e1', '#fde7ed', '#fff2f5', '#ffffff'], LEAF, 0.035),
    deep: mats(['#dc5888', '#e8709c', '#f288ae', '#f8a0bf', '#febbd2'], LEAF, 0.045),
  };
  const CULM = mats(['#74bb3f', '#62a836', '#86c94a'], DIFF, 0.05);
  const CULM_NODE = mat('#c5df76', DIFF, 0.04);
  const BLEAF = mats(['#4f9a33', '#62ad3a', '#78c043', '#8fd04d', '#a8dc5c', '#c4e772'], LEAF, 0.06);
  const MAPLE = {
    orange: mats(['#cf420e', '#e85d0c', '#f97a12', '#ff9626', '#ffb347'], LEAF, 0.05),
    gold: mats(['#dd9205', '#f0a904', '#fcbf10', '#ffd231', '#ffe368'], LEAF, 0.05),
    red: mats(['#a82410', '#c93316', '#e2461a', '#f15f1e', '#fa7b29'], LEAF, 0.05),
  };
  const PINE = mats(['#1e5631', '#28683b', '#337a45', '#429052', '#55a45f'], LEAF, 0.06);
  const SHRUB = mats(['#3d8436', '#4a963c', '#59a844', '#6bb84e'], LEAF, 0.06);
  const AZALEA = mats(['#ff5c9d', '#ff8fbd', '#ffffff', '#e0408f', '#ffd24d'], LEAF, 0.04);
  const BLADE = mats(['#5fa63c', '#7fc24b', '#93d05a'], LEAF, 0.06);
  const FLOWER = mats(['#ffffff', '#ffd83d', '#8f6fe0', '#f0442e', '#ff8fbd'], DIFF, 0.03);
  // props and creatures
  const LSTONE = mats(['#a9a69c', '#96938a', '#bab7ad'], DIFF, 0.04);
  const GLOW = mat('#ffdf9a', EMIT, 0.02);
  const KOI = mats(['#ff7b1c', '#fbf7ef', '#e03a1c'], DIFF, 0.03);
  const LILY = mats(['#4fae4a', '#62bd55'], DIFF, 0.04);
  const LOTUS = mat('#ffb7d2', DIFF, 0.03);
  const BIRD = mat('#2c313a', DIFF, 0.02);
  const FENCE = mats(['#cdb46b', '#b89d57'], DIFF, 0.05);

  // ------------------------------------------------------------------ build
  function build(report) {
    report = report || function () {};
    const V = new Uint8Array(NXZ * NY);
    const inb = (x, y, z) => x >= 0 && x < NX && z >= 0 && z < NZ && y >= 0 && y < NY;
    const set = (x, y, z, m) => { if (inb(x, y, z)) V[x + NX * z + NXZ * y] = m; };
    const setE = (x, y, z, m) => { if (inb(x, y, z)) { const i = x + NX * z + NXZ * y; if (V[i] === 0) V[i] = m; } };
    const get = (x, y, z) => (inb(x, y, z) ? V[x + NX * z + NXZ * y] : 0);
    const pick = (list, x, y, z) => list[(hash3(x, y, z) * list.length) | 0];

    // =============================================================== terrain
    const Hm = new Int16Array(NXZ);          // y of the top ground voxel
    const Sm = new Uint8Array(NXZ);          // surface type
    const Wt = new Int16Array(NXZ).fill(-1); // y of the top water voxel, -1 where dry
    const Occ = new Uint8Array(NXZ);         // 1 where nothing should be planted
    const S_GRASS = 0, S_COURT = 1, S_PATH = 2, S_POND = 3, S_STREAM = 4, S_MOSS = 5, S_LITTER = 6, S_SHORE = 7;

    const POND = { x: PX + 94, z: PZ + 6, rx: 27, rz: 43 };
    const pondF = (x, z) => {
      const ex = (x + 0.5 - POND.x) / POND.rx, ez = (z + 0.5 - POND.z) / POND.rz;
      return ex * ex + ez * ez + (vnoise3(x / 13, 3.3, z / 13) - 0.5) * 0.55;
    };
    // Two blocky stepped mounds rise in the foreground corners of the picture.
    const ML = { u: -118, w: -104, ru: 54, rw: 42, peak: 32 };
    const MR = { u: 126, w: -114, ru: 50, rw: 40, peak: 40 };
    const mound = (M, u, w, n) => {
      const e = Math.hypot((u - M.u) / M.ru, (w - M.w) / M.rw);
      return Math.round(clamp((1 - e + (n - 0.5) * 0.4) * 1.5, 0, 1) * M.peak / 8) * 8;
    };
    // Where the bamboo grove begins, measured to the camera's right.
    const bambooEdge = (x, z, w) => (w < -62 ? 186 : 128 - 30 * smooth(40, 140, w)) + (vnoise3(x / 23, 1.7, z / 23) - 0.5) * 22;

    function raise(x, z) {
      const [u, w] = toUW(x, z);
      const r = Math.hypot(x + 0.5 - PX, z + 0.5 - PZ);
      const n1 = fbm2(x / 95, z / 95, 3), n2 = fbm2(x / 41 + 31.7, z / 41 + 7.3, 3), n3 = fbm2(x / 15 + 3.1, z / 15 + 9.9, 2);
      const wj = w + (n1 - 0.5) * 50, uj = u + (n2 - 0.5) * 44;
      const hM = Math.max(mound(ML, u, w, n2), mound(MR, u, w, n2));
      const hN = Math.round(smooth(-152, -235, wj) * 26 / 8) * 8;      // hill behind the camera's feet
      const hL = Math.round(smooth(-112, -205, uj) * 16 / 4) * 4;      // cherry grove
      const hR = Math.round(smooth(130, 210, uj) * 12 / 4) * 4;        // bamboo grove
      const hB = Math.round(smooth(112, 225, wj) * 12 / 6) * 6;        // rise behind the pagoda
      let h = Math.max(hM, hN, hL, hR, hB);
      if (h === 0) h = Math.max(0, Math.round((n3 - 0.45) * 5 * smooth(62, 96, r)));
      return h;
    }

    for (let z = 0; z < NZ; z++) {
      for (let x = 0; x < NX; x++) {
        const i = x + NX * z;
        const [u] = toUW(x, z);
        const r = Math.hypot(x + 0.5 - PX, z + 0.5 - PZ);
        let h = raise(x, z), s = S_GRASS;
        const nm = vnoise3(x / 19, 5.5, z / 19);
        if (nm > 0.6) s = S_MOSS;
        if (u > bambooEdge(x, z, toUW(x, z)[1]) - 4) s = S_LITTER;
        if (r < 60) { h = 0; s = S_COURT; Occ[i] = 1; }
        const pf = pondF(x, z);
        if (pf < 1) {
          h = -(3 + Math.round(4.5 * (1 - pf)));
          s = S_POND; Wt[i] = G - 2; Occ[i] = 1;
        } else if (pf < 1.25) { h = 0; s = S_SHORE; Occ[i] = 1; }
        Hm[i] = G + h; Sm[i] = s;
      }
    }

    // ---- a stream tumbles down the right-hand mound into the pond
    {
      const course = [[118, -124], [100, -113], [84, -103], [66, -96], [50, -93]].map((p) => fromUW(p[0], p[1]));
      for (let k = 0; k + 1 < course.length; k++) {
        const a = course[k], b = course[k + 1], n = Math.ceil(Math.hypot(b[0] - a[0], b[1] - a[1]) * 2);
        for (let j = 0; j <= n; j++) {
          const cx = Math.round(lerp(a[0], b[0], j / n)), cz = Math.round(lerp(a[1], b[1], j / n));
          const hc = G + raise(cx, cz);
          for (let dz = -5; dz <= 5; dz++) for (let dx = -5; dx <= 5; dx++) {
            const x = cx + dx, z = cz + dz, d2 = dx * dx + dz * dz;
            if (x < 0 || z < 0 || x >= NX || z >= NZ) continue;
            const i = x + NX * z;
            if (Sm[i] === S_POND) continue;
            if (d2 <= 6.5) {
              if (Sm[i] !== S_STREAM || hc - 1 < Wt[i]) { Sm[i] = S_STREAM; Wt[i] = hc - 1; Hm[i] = hc - 2; }
              Occ[i] = 1;
            } else if (d2 <= 20 && Sm[i] !== S_STREAM) {
              if (Hm[i] < hc) Hm[i] = hc;
              Sm[i] = S_SHORE; Occ[i] = 1;
            }
          }
        }
      }
    }

    // ---- paths (stone paving; they smooth the terraces into flights of steps)
    function paintPath(pts, halfW) {
      const sm = [];
      for (let k = 0; k + 1 < pts.length; k++) {
        const a = pts[k], b = pts[k + 1], n = Math.ceil(Math.hypot(b[0] - a[0], b[1] - a[1]) * 2);
        for (let j = 0; j < n; j++) sm.push([lerp(a[0], b[0], j / n), lerp(a[1], b[1], j / n)]);
      }
      const hs = sm.map((p) => Hm[clamp(Math.round(p[0]), 0, NX - 1) + NX * clamp(Math.round(p[1]), 0, NZ - 1)]);
      const win = 16, hw = Math.ceil(halfW);
      for (let k = 0; k < sm.length; k++) {
        let acc = 0, cnt = 0;
        for (let j = Math.max(0, k - win); j <= Math.min(sm.length - 1, k + win); j++) { acc += hs[j]; cnt++; }
        const h = Math.round(acc / cnt), cx = Math.round(sm[k][0]), cz = Math.round(sm[k][1]);
        for (let dz = -hw; dz <= hw; dz++) for (let dx = -hw; dx <= hw; dx++) {
          if (dx * dx + dz * dz > halfW * halfW) continue;
          const x = cx + dx, z = cz + dz;
          if (x < 0 || z < 0 || x >= NX || z >= NZ) continue;
          const i = x + NX * z;
          if (Sm[i] === S_POND || Sm[i] === S_STREAM) continue;
          Hm[i] = h; Sm[i] = S_PATH; Occ[i] = 1;
        }
      }
    }
    const P = (dx, dz) => [PX + dx, PZ + dz];
    paintPath([P(0, 44), P(0, 66), fromUW(-32, -96), fromUW(-22, -140), fromUW(-8, -200), fromUW(0, -262)], 4.2);
    paintPath([P(44, 0), P(64, 0)], 4.2);
    paintPath([P(124, 0), P(150, -6), P(186, -22), P(214, -30)], 3.6);
    paintPath([P(-44, 0), P(-78, 0), fromUW(-118, 6), fromUW(-176, -14), fromUW(-250, -4)], 3.6);
    paintPath([P(0, -44), P(0, -84), P(-12, -122), P(-34, -170), P(-40, -240)], 3.6);

    // ---- fill the columns
    report('terrain', 0.08);
    for (let z = 0; z < NZ; z++) {
      for (let x = 0; x < NX; x++) {
        const i = x + NX * z, h = Hm[i], s = Sm[i];
        const r = Math.hypot(x + 0.5 - PX, z + 0.5 - PZ);
        for (let y = 0; y <= h; y++) {
          const dep = h - y;
          let m;
          if (dep === 0) {
            const hv = hash3(x, 11, z);
            if (s === S_GRASS) m = GRASS[clamp(((vnoise3(x / 8, 2.2, z / 8) * 0.75 + hv * 0.4) * 5) | 0, 0, 4)];
            else if (s === S_MOSS) m = MOSS[(vnoise3(x / 5, 8.1, z / 5) * 0.7 + hv * 0.3) * 3 | 0];
            else if (s === S_COURT) m = (Math.round(r) % 4 === 0) ? GRAVEL[2] : GRAVEL[hv < 0.55 ? 0 : 1];
            else if (s === S_PATH) m = (x % 4 === 0 || z % 4 === 0) ? PAVE_J : PAVE[(hash3(x >> 2, 3, z >> 2) * 3) | 0];
            else if (s === S_POND) m = SAND[hv < 0.6 ? 0 : 1];
            else if (s === S_STREAM) m = ROCK[(hv * 4) | 0];
            else if (s === S_LITTER) m = hv < 0.2 ? MOSS[0] : LITTER[(vnoise3(x / 6, 4.4, z / 6) * 0.6 + hv * 0.4) * 4 | 0];
            else m = hv < 0.45 ? SAND[0] : hv < 0.75 ? ROCK[2] : GRAVEL[2];
          } else if (dep <= 3 && s !== S_POND && s !== S_STREAM && s !== S_COURT && s !== S_PATH) {
            m = DIRT[(hash3(x >> 1, y, z >> 1) * 3) | 0];
          } else {
            const band = vnoise3(x / 40, y / 5, z / 40) + (y < 7 ? -0.3 : 0);
            m = band < 0.3 ? ROCK[3] : band < 0.5 ? ROCK[1] : band < 0.7 ? ROCK[0] : CLIFF[3];
          }
          V[i + NXZ * y] = m;
        }
        if (Wt[i] >= 0) {
          const d = Wt[i] - h;
          const wm = s === S_STREAM ? WATER_S : d <= 2 ? WATER_S : d <= 4 ? WATER_M : WATER_D;
          for (let y = h + 1; y <= Wt[i]; y++) V[i + NXZ * y] = wm;
        }
      }
    }

    // ---- cliffs: exposed terrace walls become chunky stone blocks
    for (let z = 1; z < NZ - 1; z++) {
      for (let x = 1; x < NX - 1; x++) {
        const i = x + NX * z, h = Hm[i];
        const lo = Math.min(Hm[i - 1], Hm[i + 1], Hm[i - NX], Hm[i + NX]);
        if (h - lo < 3) continue;
        for (let y = lo + 1; y < h; y++) {
          const c = hash3(x >> 2, (y / 3) | 0, z >> 2), v = hash3(x, y, z);
          V[i + NXZ * y] = v < 0.06 ? MOSS[0] : CLIFF[clamp((c * 3.2 + v * 0.8) | 0, 0, 3)];
        }
        if (Sm[i] === S_GRASS && hash3(x >> 1, 77, z >> 1) < 0.35) V[i + NXZ * h] = CLIFF[(hash3(x, 5, z) * 3) | 0];
      }
    }

    // ---- waterfalls where the stream drops a terrace
    for (let z = 1; z < NZ - 1; z++) {
      for (let x = 1; x < NX - 1; x++) {
        const i = x + NX * z, a = Wt[i];
        if (a < 0) continue;
        const nb = [i - 1, i + 1, i - NX, i + NX];
        for (const n of nb) {
          const b = Wt[n];
          if (b < 0 || b > a - 2) continue;
          for (let y = b + 1; y <= a; y++) V[n + NXZ * y] = FALL[(hash3(n, y, 9) * 3) | 0];
          // churned foam at the foot of the fall
          const nx = n % NX, nz = (n / NX) | 0;
          for (let dz = -3; dz <= 3; dz++) for (let dx = -3; dx <= 3; dx++) {
            const j = (nx + dx) + NX * (nz + dz);
            if (nx + dx < 0 || nx + dx >= NX || nz + dz < 0 || nz + dz >= NZ) continue;
            if (Wt[j] === b && hash3(nx + dx, 41, nz + dz) < 0.5 - 0.05 * (dx * dx + dz * dz)) V[j + NXZ * b] = FALL[2];
          }
        }
      }
    }
    report('terrain', 0.14);

    const groundY = (x, z) => Hm[clamp(x, 0, NX - 1) + NX * clamp(z, 0, NZ - 1)];
    const free = (x, z, rad) => {
      for (let dz = -rad; dz <= rad; dz += Math.max(1, rad)) for (let dx = -rad; dx <= rad; dx += Math.max(1, rad)) {
        const xx = x + dx, zz = z + dz;
        if (xx < 0 || zz < 0 || xx >= NX || zz >= NZ) return false;
        if (Occ[xx + NX * zz]) return false;
      }
      return true;
    };
    const occupy = (x, z, rad) => {
      for (let dz = -rad; dz <= rad; dz++) for (let dx = -rad; dx <= rad; dx++) {
        const xx = x + dx, zz = z + dz;
        if (xx >= 0 && zz >= 0 && xx < NX && zz < NZ && dx * dx + dz * dz <= rad * rad) Occ[xx + NX * zz] = 1;
      }
    };

    // ============================================================ primitives
    function ball(cx, cy, cz, r, list) {
      const X = Math.round(cx), Y = Math.round(cy), Z = Math.round(cz);
      if (r <= 0.8) { set(X, Y, Z, pick(list, X, Y >> 1, Z)); return; }
      const ri = Math.ceil(r), r2 = r * r;
      for (let dy = -ri; dy <= ri; dy++) for (let dz = -ri; dz <= ri; dz++) for (let dx = -ri; dx <= ri; dx++) {
        if (dx * dx + dy * dy + dz * dz <= r2) set(X + dx, Y + dy, Z + dz, pick(list, X + dx, (Y + dy) >> 1, Z + dz));
      }
    }
    function limb(a, b, r0, r1, list) {
      const n = Math.max(1, Math.ceil(Math.hypot(b[0] - a[0], b[1] - a[1], b[2] - a[2]) * 1.5));
      for (let i = 0; i <= n; i++) { const t = i / n; ball(lerp(a[0], b[0], t), lerp(a[1], b[1], t), lerp(a[2], b[2], t), lerp(r0, r1, t), list); }
    }
    function bez(a, c, b, r0, r1, list) {
      const n = Math.max(2, Math.ceil((Math.hypot(c[0] - a[0], c[1] - a[1], c[2] - a[2]) + Math.hypot(b[0] - c[0], b[1] - c[1], b[2] - c[2])) * 1.5));
      for (let i = 0; i <= n; i++) {
        const t = i / n, k0 = (1 - t) * (1 - t), k1 = 2 * t * (1 - t), k2 = t * t;
        ball(k0 * a[0] + k1 * c[0] + k2 * b[0], k0 * a[1] + k1 * c[1] + k2 * b[1], k0 * a[2] + k1 * c[2] + k2 * b[2], lerp(r0, r1, t), list);
      }
    }
    // A sculpted foliage lobe: an ellipsoid with a noise-eroded, slightly open surface.
    // Shades run dark -> light; tops and outer voxels drift lighter.
    function blob(cx, cy, cz, rx, ry, rz, shades, o) {
      o = o || {};
      const erode = o.erode === undefined ? 0.28 : o.erode, thin = o.thin === undefined ? 0.26 : o.thin;
      const ns = o.ns || 0.19, light = o.light === undefined ? 0.34 : o.light, accents = o.accents, ap = o.accentP || 0;
      const lim = 1 + erode, lim2 = lim * lim, inner = 1 - erode, L = shades.length;
      const x0 = Math.floor(cx - rx * lim), x1 = Math.ceil(cx + rx * lim);
      const y0 = Math.max(Math.floor(cy - ry * lim), o.minY === undefined ? 0 : o.minY), y1 = Math.ceil(cy + ry * lim);
      const z0 = Math.floor(cz - rz * lim), z1 = Math.ceil(cz + rz * lim);
      for (let y = y0; y <= y1; y++) {
        if (y < 0 || y >= NY) continue;
        const ey = (y + 0.5 - cy) / ry;
        for (let z = z0; z <= z1; z++) {
          if (z < 0 || z >= NZ) continue;
          const ez = (z + 0.5 - cz) / rz, eyz = ey * ey + ez * ez;
          if (eyz > lim2) continue;
          for (let x = x0; x <= x1; x++) {
            if (x < 0 || x >= NX) continue;
            const ex = (x + 0.5 - cx) / rx, d2 = ex * ex + eyz;
            if (d2 > lim2) continue;
            let d = Math.sqrt(d2);
            const hv = hash3(x, y, z);
            if (d > inner) {
              d += (vnoise3(x * ns, y * ns, z * ns) - 0.5) * 2 * erode;
              if (d > 1) continue;
              if (d > 0.8 && hv < thin) continue;
            }
            const i = x + NX * z + NXZ * y;
            if (V[i] !== 0) continue;
            if (accents && d > 0.72 && hv > 1 - ap) { V[i] = accents[(hash3(x, z, y) * accents.length) | 0]; continue; }
            const g = 0.42 + ey * light + (hash3(x >> 2, y >> 2, z >> 2) - 0.5) * 0.5 + (hv - 0.5) * 0.42 + (d - 0.7) * 0.25;
            V[i] = shades[clamp((g * L) | 0, 0, L - 1)];
          }
        }
      }
    }

    // ================================================================ pagoda
    function pagoda() {
      // The plan is four-fold symmetric, so build one quadrant and mirror it.
      // d = ring distance from the centre, mm = position along the wall from its middle.
      const q4 = (ax, y, az, m) => {
        set(PX + ax, y, PZ + az, m); set(PX - 1 - ax, y, PZ + az, m);
        set(PX + ax, y, PZ - 1 - az, m); set(PX - 1 - ax, y, PZ - 1 - az, m);
      };
      const stoneAt = (ax, y, az) => STONE[clamp((hash3(ax >> 2, y >> 1, az >> 2) * 3.4 + hash3(ax, y, az) * 0.6) | 0, 0, 3)];
      const y0 = G + 1;

      // ---- two-tier granite platform with a flight of steps on each side
      const PL1 = 36, PL2 = 31;
      for (let az = 0; az < 48; az++) for (let ax = 0; ax < 48; ax++) {
        const d = Math.max(ax, az), mm = Math.min(ax, az);
        if (d < PL1) for (let yy = 0; yy < 3; yy++) q4(ax, y0 + yy, az, yy === 2 && d >= PL2 ? STONE[2] : stoneAt(ax, yy, az));
        if (d < PL2) for (let yy = 3; yy < 8; yy++) q4(ax, y0 + yy, az, yy === 7 ? (d === PL2 - 1 ? STONE[2] : ((ax % 5 === 4 || az % 5 === 4) ? STONE[3] : STONE[0])) : stoneAt(ax, yy, az));
        if (d >= PL2 && d < PL2 + 14 && mm < 8) {
          const j = (d - PL2) >> 1, top = 6 - j;                 // step j, counting down from the top
          if (mm < 7) { for (let yy = 0; yy <= top; yy++) q4(ax, y0 + yy, az, yy === top ? STONE[2] : stoneAt(ax, yy, az)); }
          else { for (let yy = 0; yy <= top + 2; yy++) q4(ax, y0 + yy, az, yy === top + 2 ? STONE[2] : STONE[1]); }   // cheek walls
        }
      }
      const yP = y0 + 8;

      const b = [19, 17, 15, 13, 11];       // body half-widths
      const R = [44, 40, 36, 32, 28];       // eave half-widths
      const ftf = [24, 23, 22, 21];         // storey heights
      const E = [yP + 22];                  // y of the lowest eave layer of each roof
      for (let i = 0; i < 4; i++) E.push(E[i] + ftf[i]);
      const RISE = 9, TOP_RISE = 18;

      // Roof surface: concave in section, and swept up toward the corners.
      function roofTop(i, d, mm) {
        const inner = i < 4 ? b[i + 1] : 3;
        const t = clamp((R[i] - 1 - d) / (R[i] - 1 - inner), 0, 1);
        const rise = i < 4 ? RISE : TOP_RISE, p = i < 4 ? 1.5 : 1.3;
        const lift = 5.3 * Math.pow(mm / Math.max(d, 1), 7) * (1 - t) * (1 - t);
        return E[i] + 2 + Math.round(rise * Math.pow(t, p) + lift);
      }

      function wallMat(i, row, nrows, mm, bi) {
        const p1 = i === 0 ? 5 : Math.round(bi / 3) - 1;
        if (mm >= bi - 2 || mm === p1 || mm === p1 + 1) return VERM[0];          // pillars
        if (row < 2) return VERM_D;                                               // ground beam
        if (row >= nrows - 2) return VERM[1];                                     // tie beam
        if (i === 0) {
          if (mm < p1) {                                                          // door bay
            if (row === nrows - 5) return VERM[1];
            if (row > nrows - 5) return PLASTER[0];
            if (mm === 0 && row >= 6 && row <= 8) return GOLD;
            return (mm % 2 === 1 && row % 4 === 3) ? GOLD : WOOD_D;
          }
          if (row === 7) return VERM[1];
          if (row > 7 && row < nrows - 3 && mm >= p1 + 3 && mm <= bi - 5) return (mm % 2) ? LATTICE : INTERIOR;
          return PLASTER[(row * 3 + mm) % 7 === 0 ? 1 : 0];
        }
        if (mm < p1 && row >= 3 && row <= nrows - 4) return (mm % 2) ? LATTICE : INTERIOR;
        return PLASTER[0];
      }

      for (let i = 0; i < 5; i++) {
        const bi = b[i], Ri = R[i], Ei = E[i];
        const inner = i < 4 ? b[i + 1] : 3;
        const yw0 = i === 0 ? yP : E[i - 1] + RISE + 3;      // first wall row
        const yw1 = Ei - 4;                                  // last wall row
        const nrows = yw1 - yw0 + 1;

        // ---- body: solid core, a skin of walls, pillars standing proud of it
        for (let az = 0; az <= bi; az++) for (let ax = 0; ax <= bi; ax++) {
          const d = Math.max(ax, az), mm = Math.min(ax, az);
          const p1 = i === 0 ? 5 : Math.round(bi / 3) - 1;
          if (d < bi - 1) { for (let y = yw0 - 6; y <= Ei + RISE + 2; y++) if (i > 0 || y >= yP) q4(ax, y, az, INTERIOR); }
          else if (d === bi - 1) {
            for (let y = yw0; y <= yw1; y++) q4(ax, y, az, wallMat(i, y - yw0, nrows, mm, bi));
            for (let y = yw1 + 1; y <= Ei + RISE + 2; y++) q4(ax, y, az, VERM_D);
            if (i > 0) for (let y = yw0 - 6; y < yw0; y++) q4(ax, y, az, VERM_D);
          } else if (mm >= bi - 2 || mm === p1 || mm === p1 + 1) {
            for (let y = yw0; y <= yw1; y++) q4(ax, y, az, y - yw0 < 1 ? VERM_D : VERM[0]);
          }
        }

        // ---- bracket complex: corbels stepping out under the eaves
        for (let y = Ei - 3; y <= Ei + RISE; y++) {
          const L = y - (Ei - 3), reach = bi + L;
          for (let az = 0; az <= reach; az++) for (let ax = 0; ax <= reach; ax++) {
            const d = Math.max(ax, az), mm = Math.min(ax, az);
            if (d < bi || y >= roofTop(i, d, mm) - 2) continue;
            let m = VERM_D;
            if (d >= reach - 1) {
              const arm = mm % 4 < 2 || d - mm <= 2;
              if (arm) m = d === reach ? VERM[2] : VERM[0];
              else if (L % 2 === 0) m = PLASTER[0];
              else continue;
            }
            q4(ax, y, az, m);
          }
        }

        // ---- roof
        for (let az = 0; az < Ri; az++) for (let ax = 0; ax < Ri; ax++) {
          const d = Math.max(ax, az), mm = Math.min(ax, az);
          if (d < inner) continue;
          const yt = roofTop(i, d, mm), hip = d - mm <= 1, eave = d === Ri - 1;
          q4(ax, yt - 2, az, eave ? ((mm & 1) ? PLASTER[0] : VERM[0]) : ((mm & 1) ? VERM_D : VERM[1]));   // rafters
          q4(ax, yt - 1, az, eave ? T_DARK : T_TROUGH);
          if (hip) {
            q4(ax, yt, az, T_DARK); q4(ax, yt + 1, az, T_DARK);
            if (d < Ri - 1) q4(ax, yt + 2, az, d >= Ri - 3 ? GOLD : T_DARK);
            else q4(ax, yt + 2, az, GOLD);
          } else if (mm % 3 === 1) {                        // round tile ridges running down the slope
            q4(ax, yt, az, T_TILE);
            q4(ax, yt + 1, az, eave ? ((((mm - 1) / 3) & 1) ? GOLD : T_EDGE) : T_RIDGE);
          } else {
            q4(ax, yt, az, eave ? T_EDGE : (hash3(ax, yt, az) < 0.5 ? T_TILE : T_TROUGH));
          }
          // keep the slab watertight where the surface steps up steeply
          const ytIn = d > inner ? roofTop(i, d - 1, Math.min(mm, d - 1)) : yt;
          for (let y = yt + 1; y < ytIn - 2; y++) q4(ax, y, az, T_TROUGH);
        }
        // wind bells under each corner
        { const c = Ri - 1, yt = roofTop(i, c, c); q4(c, yt - 3, c, BRONZE); q4(c, yt - 4, c, GOLD); q4(c, yt - 5, c, GOLD); }

        // ---- balcony with a vermilion railing around every upper storey
        if (i > 0) {
          const fy = E[i - 1] + RISE + 2, rr = bi + 3;
          for (let az = 0; az <= rr; az++) for (let ax = 0; ax <= rr; ax++) {
            const d = Math.max(ax, az), mm = Math.min(ax, az);
            if (d < bi) continue;
            for (let y = roofTop(i - 1, d, mm) + 1; y <= fy; y++) q4(ax, y, az, y === fy ? WOOD[(ax + az) & 1] : VERM_D);
            if (d === rr) {
              const post = mm % 4 === 0 || mm === rr || mm === rr - 1;
              if (post) { for (let k = 1; k <= 4; k++) q4(ax, fy + k, az, VERM[0]); if (mm === rr) q4(ax, fy + 5, az, GOLD); }
              q4(ax, fy + 4, az, VERM[2]); q4(ax, fy + 2, az, VERM[1]);
            }
          }
        }
      }

      // ---- top roof cap and the bronze-and-gold finial (sorin)
      const capY = E[4] + 2 + TOP_RISE;
      for (let az = 0; az < 3; az++) for (let ax = 0; ax < 3; ax++) for (let y = capY - 8; y <= capY; y++) q4(ax, y, az, T_DARK);
      let fy = capY + 1;
      const plate = (hw, y, m, cut) => { for (let az = 0; az < hw; az++) for (let ax = 0; ax < hw; ax++) { if (cut && ax === hw - 1 && az === hw - 1) continue; q4(ax, y, az, m); } };
      plate(4, fy, BRONZE); plate(4, fy + 1, BRONZE); plate(4, fy + 2, GOLD);            // dew basin base
      plate(3, fy + 3, GOLD, true); plate(2, fy + 4, GOLD);                              // inverted bowl
      plate(3, fy + 5, GOLD, true);                                                      // lotus
      for (let y = fy + 6; y < fy + 34; y++) plate(1, y, BRONZE);                        // mast
      for (let k = 0; k < 9; k++) plate(k < 3 ? 4 : k < 7 ? 3 : 2, fy + 7 + k * 2, GOLD, true);   // nine rings
      for (let k = 0; k < 7; k++) {                                                       // water-flame fins
        const reach = k < 2 ? 3 : k < 5 ? 2 : 1, y = fy + 26 + k;
        for (let a = 1; a <= reach; a++) if ((a + k) % 3 !== 0 || a === reach) { q4(a, y, 0, GOLD); q4(0, y, a, GOLD); }
      }
      plate(1, fy + 34, GOLD); plate(1, fy + 35, GOLD);                                   // jewel
      return fy + 35;
    }
    const pagodaTop = pagoda();
    report('pagoda', 0.2);

    // ================================================================= props
    function lantern(x, z) {
      let y = groundY(x, z) + 1;
      const box = (hw, yy, m) => { for (let dz = -hw; dz < hw; dz++) for (let dx = -hw; dx < hw; dx++) set(x + dx, yy, z + dz, typeof m === 'function' ? m(dx, dz) : m); };
      box(2, y++, LSTONE[1]);
      for (let k = 0; k < 4; k++) box(1, y++, LSTONE[0]);
      box(2, y++, LSTONE[2]);
      for (let k = 0; k < 3; k++) box(2, y++, (dx, dz) => ((dx === -2 || dx === 1) && (dz === -2 || dz === 1)) ? LSTONE[0] : (k === 1 ? GLOW : LSTONE[1]));
      box(3, y++, LSTONE[1]); box(2, y++, LSTONE[0]); box(1, y++, LSTONE[2]); box(1, y++, LSTONE[1]);
      occupy(x, z, 4);
    }

    function bridge() {
      const xa = PX + 62, xb = PX + 126, z0 = PZ - 4, z1 = PZ + 3, base = G + 1;
      for (let x = xa; x <= xb; x++) {
        const t = (x - xa) / (xb - xa), arch = Math.round(7.5 * (1 - (2 * t - 1) * (2 * t - 1)));
        const yd = base + arch;
        for (let z = z0; z <= z1; z++) {
          set(x, yd, z, (x & 1) ? WOOD[0] : WOOD[1]);
          set(x, yd - 1, z, VERM_D);
          const side = z === z0 || z === z1;
          if (side) {
            set(x, yd - 2, z, VERM_D);
            const post = (x - xa) % 8 === 0;
            if (post) { for (let k = 1; k <= 4; k++) set(x, yd + k, z, VERM[0]); set(x, yd + 5, z, GOLD); }
            set(x, yd + 3, z, VERM[2]); set(x, yd + 1, z, VERM[1]);
          }
        }
        // two pairs of piers standing in the pond
        if (x === xa + 20 || x === xa + 21 || x === xb - 20 || x === xb - 21) {
          for (const z of [z0 + 1, z1 - 1]) for (let y = groundY(x, z) + 1; y < yd - 1; y++) set(x, y, z, VERM_D);
        }
        for (let z = z0; z <= z1; z++) Occ[x + NX * z] = 1;
      }
    }
    bridge();

    // lanterns: beside each flight of steps, along the approach, and by the bridge
    for (const [dx, dz] of [[12, 50], [-12, 50], [50, 12], [50, -12], [-50, 12], [-50, -12], [12, -50], [-12, -50]]) lantern(PX + dx, PZ + dz);
    for (const [dx, dz] of [[58, 9], [58, -9], [130, 9], [130, -9]]) lantern(PX + dx, PZ + dz);
    for (const [u, w] of [[-44, -92], [-11, -128], [-33, -168], [-96, 14], [-140, -2]]) { const [x, z] = fromUW(u, w); lantern(x, z); }

    function rock(x, z, r, seed) {
      const y = groundY(x, z);
      blob(x, y + r * 0.25, z, r, r * 0.72, r * (0.8 + hash3(seed, 1, 2) * 0.4), ROCK, { erode: 0.22, thin: 0, light: 0.5, ns: 0.3 });
      for (let dz = -r - 1; dz <= r + 1; dz++) for (let dx = -r - 1; dx <= r + 1; dx++) {
        for (let yy = y + Math.ceil(r); yy > y; yy--) {
          const m = get(x + dx, yy, z + dz);
          if (m === 0) continue;
          if (hash3(x + dx, yy, z + dz) < 0.45 && ROCK.indexOf(m) >= 0) set(x + dx, yy, z + dz, MOSS[(hash3(dx, yy, dz) * 3) | 0]);
          break;
        }
      }
      occupy(x, z, Math.ceil(r));
    }

    function shrub(x, z, r, seed, flowers) {
      const y = groundY(x, z);
      blob(x + 0.5, y + 1 + r * 0.25, z + 0.5, r, r * 0.78, r, SHRUB, { erode: 0.2, thin: 0.12, light: 0.5, ns: 0.33, minY: y + 1, accents: flowers, accentP: flowers ? 0.22 : 0 });
    }

    // ================================================================= trees
    function cherry(x, z, s, shades, seed) {
      const R = rng(seed), y0 = groundY(x, z);
      const th = (24 + R() * 8) * s, la = R() * 6.283, ld = (3 + R() * 5) * s;
      const tx = x + Math.cos(la) * ld, tz = z + Math.sin(la) * ld, ty = y0 + th;
      bez([x, y0 - 2, z], [x - Math.cos(la) * ld * 0.5, y0 + th * 0.5, z - Math.sin(la) * ld * 0.5], [tx, ty, tz], 3.1 * s, 2.1 * s, BARK_C);
      for (let k = 0; k < 4; k++) { const a = k * 1.571 + la; limb([x, y0 + 4 * s, z], [x + Math.cos(a) * 5 * s, y0 - 1, z + Math.sin(a) * 5 * s], 1.7 * s, 1.1 * s, BARK_C); }
      const tips = [];
      const nb = 5 + ((R() * 3) | 0), a0 = R() * 6.283;
      for (let i = 0; i < nb; i++) {
        const a = a0 + (i / nb) * 6.283 + (R() - 0.5) * 0.6;
        const len = (24 + R() * 14) * s, el = 0.45 + R() * 0.5;
        const ex = tx + Math.cos(a) * Math.cos(el) * len, ey = ty + Math.sin(el) * len, ez = tz + Math.sin(a) * Math.cos(el) * len;
        bez([tx, ty, tz], [lerp(tx, ex, 0.45), lerp(ty, ey, 0.45) + len * 0.16, lerp(tz, ez, 0.45)], [ex, ey, ez], 2.0 * s, 0.9 * s, BARK_C);
        tips.push([ex, ey, ez, 1]);
        tips.push([lerp(tx, ex, 0.58), lerp(ty, ey, 0.58) + 4 * s, lerp(tz, ez, 0.58), 0.86]);
        for (let j = 0; j < 2; j++) {
          const a2 = a + (j ? 1 : -1) * (0.55 + R() * 0.5), l2 = (11 + R() * 9) * s, e2 = 0.15 + R() * 0.6;
          const bx = lerp(tx, ex, 0.5), by = lerp(ty, ey, 0.5) + len * 0.07, bz = lerp(tz, ez, 0.5);
          const q = [bx + Math.cos(a2) * Math.cos(e2) * l2, by + Math.sin(e2) * l2, bz + Math.sin(a2) * Math.cos(e2) * l2];
          limb([bx, by, bz], q, 1.25 * s, 0.7 * s, BARK_C);
          tips.push([q[0], q[1], q[2], 0.9]);
        }
      }
      const top = [tx + (R() - 0.5) * 8 * s, ty + (20 + R() * 8) * s, tz + (R() - 0.5) * 8 * s];
      limb([tx, ty, tz], top, 1.8 * s, 0.8 * s, BARK_C);
      tips.push([top[0], top[1], top[2], 1.1]);
      for (const t of tips) {
        const r = (10 + R() * 5) * s * t[3];
        blob(t[0] + (R() - 0.5) * 4 * s, t[1] + r * 0.15, t[2] + (R() - 0.5) * 4 * s, r, r * 0.74, r, shades, { erode: 0.3, thin: 0.3 });
      }
      occupy(x, z, Math.ceil(5 * s));
      return 40 * s;
    }

    function weepingCherry(x, z, s, shades, seed) {
      const R = rng(seed), y0 = groundY(x, z), th = 30 * s;
      bez([x, y0 - 2, z], [x + 3 * s, y0 + th * 0.5, z - 2 * s], [x, y0 + th, z], 2.6 * s, 1.6 * s, BARK_C);
      const nb = 8, rc = 24 * s;
      for (let i = 0; i < nb; i++) {
        const a = (i / nb) * 6.283 + R() * 0.5, len = rc * (0.75 + R() * 0.35);
        const e = [x + Math.cos(a) * len, y0 + th - 2 * s + R() * 5 * s, z + Math.sin(a) * len];
        bez([x, y0 + th, z], [x + Math.cos(a) * len * 0.5, y0 + th + 12 * s, z + Math.sin(a) * len * 0.5], e, 1.5 * s, 0.7 * s, BARK_C);
        blob(e[0], e[1] + 2 * s, e[2], 8 * s, 4.5 * s, 8 * s, shades, { erode: 0.3, thin: 0.3 });
        blob(lerp(x, e[0], 0.5), y0 + th + 7 * s, lerp(z, e[2], 0.5), 9 * s, 5 * s, 9 * s, shades, { erode: 0.3, thin: 0.3 });
      }
      blob(x, y0 + th + 9 * s, z, 11 * s, 6 * s, 11 * s, shades, { erode: 0.3, thin: 0.3 });
      // cascading strands
      const n = Math.round(150 * s * s);
      for (let k = 0; k < n; k++) {
        const a = R() * 6.283, rr = rc * 1.15 * Math.sqrt(0.25 + 0.75 * R());
        const sx = Math.round(x + Math.cos(a) * rr), sz = Math.round(z + Math.sin(a) * rr);
        let y = y0 + Math.round(th + 16 * s);
        while (y > y0 && get(sx, y, sz) === 0) y--;
        if (y <= y0 + 6) continue;
        const len = Math.round((10 + R() * 20) * s), L = shades.length;
        for (let j = 1; j <= len && y - j > y0 + 2; j++) {
          if (R() < 0.12) continue;
          setE(sx, y - j, sz, shades[clamp(((j / len) * L + R() * 1.5) | 0, 0, L - 1)]);
        }
      }
      occupy(x, z, Math.ceil(5 * s));
      return rc;
    }

    function maple(x, z, s, shades, seed) {
      const R = rng(seed), y0 = groundY(x, z);
      const n = 2 + ((R() * 2) | 0), a0 = R() * 6.283;
      const pad = (px, py, pz, rx, ry) => blob(px, py, pz, rx, ry, rx * (0.85 + R() * 0.3), shades, { erode: 0.27, thin: 0.28, light: 0.5, ns: 0.22 });
      for (let i = 0; i < n; i++) {
        const a = a0 + (i / n) * 6.283 + (R() - 0.5) * 0.7, hh = (17 + R() * 9) * s, off = (5 + R() * 6) * s;
        const e = [x + Math.cos(a) * off, y0 + hh, z + Math.sin(a) * off];
        bez([x, y0 - 1, z], [x + Math.cos(a) * off * 0.15, y0 + hh * 0.6, z + Math.sin(a) * off * 0.15], e, 1.7 * s, 0.9 * s, BARK_M);
        pad(e[0], e[1] + 2 * s, e[2], (9 + R() * 5) * s, (3.8 + R() * 1.4) * s);
        for (let j = 0; j < 2; j++) {
          const a2 = a + (R() - 0.5) * 2.2, o2 = (8 + R() * 7) * s, hy = y0 + hh * (0.5 + R() * 0.3);
          const q = [x + Math.cos(a2) * o2, hy, z + Math.sin(a2) * o2];
          limb([x + Math.cos(a) * off * 0.4, y0 + hh * 0.55, z + Math.sin(a) * off * 0.4], q, 1.0 * s, 0.6 * s, BARK_M);
          pad(q[0], q[1] + 1.5 * s, q[2], (7 + R() * 4) * s, (3 + R() * 1.2) * s);
        }
      }
      pad(x + (R() - 0.5) * 4 * s, y0 + 29 * s, z + (R() - 0.5) * 4 * s, (10 + R() * 3) * s, 5 * s);
      limb([x, y0 + 12 * s, z], [x, y0 + 27 * s, z], 1.2 * s, 0.7 * s, BARK_M);
      occupy(x, z, Math.ceil(3 * s));
      return 20 * s;
    }

    function ginkgo(x, z, s, shades, seed) {
      const R = rng(seed), y0 = groundY(x, z), hh = 46 * s;
      limb([x, y0 - 1, z], [x + (R() - 0.5) * 3, y0 + hh, z + (R() - 0.5) * 3], 2.0 * s, 0.8 * s, BARK_M);
      const prof = [8, 11.5, 13, 12.5, 10.5, 7.5];
      for (let k = 0; k < prof.length; k++) {
        const r = prof[k] * s * (0.9 + R() * 0.2), cy = y0 + (15 + k * 7) * s;
        for (let j = 0; j < 2; j++) {
          const a = R() * 6.283, o = r * 0.35;
          blob(x + Math.cos(a) * o, cy + (R() - 0.5) * 3, z + Math.sin(a) * o, r * 0.85, r * 0.6, r * 0.85, shades, { erode: 0.28, thin: 0.3, light: 0.45 });
        }
      }
      occupy(x, z, Math.ceil(3 * s));
      return 14 * s;
    }

    function pine(x, z, s, seed) {
      const R = rng(seed), y0 = groundY(x, z);
      const a = R() * 6.283, c = Math.cos(a), sn = Math.sin(a);
      const p = [[x, y0 - 1, z], [x + c * 5 * s, y0 + 10 * s, z + sn * 5 * s], [x - c * 2 * s, y0 + 21 * s, z - sn * 2 * s], [x + c * 3 * s, y0 + 31 * s, z + sn * 3 * s]];
      limb(p[0], p[1], 2.0 * s, 1.7 * s, BARK_P); limb(p[1], p[2], 1.7 * s, 1.3 * s, BARK_P); limb(p[2], p[3], 1.3 * s, 0.8 * s, BARK_P);
      const pad = (q, rx) => blob(q[0], q[1] + 1.2 * s, q[2], rx, 2.5 * s, rx * (0.8 + R() * 0.3), PINE, { erode: 0.22, thin: 0.22, light: 0.75, ns: 0.3 });
      const at = (t) => { const k = Math.min(2, (t * 3) | 0), f = t * 3 - k; return [lerp(p[k][0], p[k + 1][0], f), lerp(p[k][1], p[k + 1][1], f), lerp(p[k][2], p[k + 1][2], f)]; };
      const np = 6;
      for (let i = 0; i < np; i++) {
        const t = 0.3 + 0.62 * (i / (np - 1)), o = at(t);
        const b2 = a + 1.3 + i * 2.4 + (R() - 0.5) * 0.6, len = (13 - 7 * t + R() * 3) * s;
        const q = [o[0] + Math.cos(b2) * len, o[1] + (R() - 0.3) * 3 * s, o[2] + Math.sin(b2) * len];
        limb(o, q, 1.0 * s, 0.6 * s, BARK_P);
        pad(q, (9 - 4 * t + R() * 2) * s);
      }
      pad([p[3][0], p[3][1] + s, p[3][2]], 6.5 * s);
      occupy(x, z, Math.ceil(3 * s));
    }

    function bamboo(x, z, hgt, seed, thick) {
      const R = rng(seed), y0 = groundY(x, z);
      const a = R() * 6.283, bend = 4 + R() * 12, cm = CULM[(R() * 3) | 0];
      const seg = 6 + ((R() * 3) | 0);
      const leafAt = (lx, ly, lz, n) => {
        for (let k = 0; k < n; k++) {
          const dx = Math.round((R() - 0.5) * 5), dz = Math.round((R() - 0.5) * 5), dy = Math.round((R() - 0.65) * 3);
          setE(lx + dx, ly + dy, lz + dz, BLEAF[clamp((1.2 + R() * 4.2 + dy * 0.5) | 0, 0, 5)]);
        }
      };
      for (let y = 0; y <= hgt; y++) {
        const t = y / hgt, off = bend * Math.pow(t, 2.6);
        const cx = Math.round(x + Math.cos(a) * off), cz = Math.round(z + Math.sin(a) * off), cy = y0 + y;
        const node = y % seg === seg - 1;
        const m = node ? CULM_NODE : cm;
        set(cx, cy, cz, m);
        if (thick && t < 0.7) { set(cx + 1, cy, cz, m); set(cx, cy, cz + 1, m); set(cx + 1, cy, cz + 1, m); }
        if (node && t > 0.4) {
          const nbr = t > 0.75 ? 3 : 2;
          for (let k = 0; k < nbr; k++) {
            const b = R() * 6.283, len = Math.round((3 + R() * 6) * (1.15 - 0.5 * t));
            const up = 0.15 + R() * 0.4, droop = 0.03 + R() * 0.05;
            for (let j = 1; j <= len; j++) {
              const lx = Math.round(cx + Math.cos(b) * j), lz = Math.round(cz + Math.sin(b) * j), ly = Math.round(cy + j * up - j * j * droop);
              setE(lx, ly, lz, BLEAF[1 + ((R() * 2) | 0)]);
              if (j >= 2) leafAt(lx, ly, lz, 3);
            }
            leafAt(Math.round(cx + Math.cos(b) * len), Math.round(cy + len * up - len * len * droop), Math.round(cz + Math.sin(b) * len), 9);
          }
        }
        if (t > 0.9) leafAt(cx, cy, cz, 5);
      }
    }

    // ============================================================== planting
    report('trees', 0.22);
    const cherries = [];
    const plantCherry = (u, w, s, kind, seed, weeping) => {
      const [x, z] = fromUW(u, w);
      if (x < 8 || z < 8 || x > NX - 9 || z > NZ - 9) return;
      const r = weeping ? weepingCherry(x, z, s, BLOSSOM[kind], seed) : cherry(x, z, s, BLOSSOM[kind], seed);
      cherries.push([x, z, r]);
    };
    // hero trees framing the left of the picture
    plantCherry(-186, -58, 1.85, 'pink', 101);
    plantCherry(-216, 34, 1.75, 'white', 102);
    plantCherry(-150, 74, 1.5, 'deep', 103);
    plantCherry(-236, -130, 1.5, 'pink', 104);
    plantCherry(-110, 138, 1.2, 'white', 105);
    // behind the pagoda
    plantCherry(-44, 142, 1.02, 'pink', 108);
    plantCherry(24, 158, 1.0, 'white', 109);
    plantCherry(86, 150, 0.95, 'deep', 110);
    // a weeping cherry leaning over the pond
    plantCherry(56, 34, 1.0, 'pink', 111, true);
    plantCherry(-84, -34, 0.9, 'white', 112, true);

    // foreground: maples and ginkgos cascading down the terraces
    const fgTrees = [
      [-120, -100, 1.45, 'orange', 0], [-92, -86, 1.1, 'gold', 0], [-148, -84, 1.2, 'red', 0], [-100, -130, 1.1, 'gold', 1],
      [-76, -114, 0.9, 'orange', 0], [-144, -128, 1.2, 'gold', 0],
      [138, -98, 1.45, 'orange', 0], [104, -88, 1.05, 'gold', 0], [156, -88, 1.15, 'red', 0], [152, -130, 1.15, 'gold', 1],
      [96, -134, 0.95, 'orange', 0],
    ];
    fgTrees.forEach((t, k) => {
      const [x, z] = fromUW(t[0], t[1]);
      if (x < 8 || z < 8 || x > NX - 9 || z > NZ - 9) return;
      if (t[4]) ginkgo(x, z, t[2], MAPLE[t[3]], 300 + k); else maple(x, z, t[2], MAPLE[t[3]], 300 + k);
    });

    // sculpted pines around the court
    for (const [u, w, s, seed] of [[-58, -28, 1.0, 1], [52, 62, 1.1, 2], [-62, 66, 1.05, 3], [30, -64, 0.8, 4], [4, 96, 1.0, 5]]) {
      const [x, z] = fromUW(u, w); pine(x, z, s, 400 + seed);
    }

    report('trees', 0.5);
    // fill the rest of the garden zone by zone on a jittered grid
    {
      const R = rng(777), cell = 30;
      for (let gz = 10; gz < NZ - 10; gz += cell) for (let gx = 10; gx < NX - 10; gx += cell) {
        const x = Math.round(gx + R() * (cell - 6)), z = Math.round(gz + R() * (cell - 6));
        const pick3 = R(), sz = R(), seed = 1000 + gx * 7 + gz * 131;
        if (x < 12 || z < 12 || x > NX - 13 || z > NZ - 13 || !free(x, z, 4)) continue;
        const [u, w] = toUW(x, z), r = Math.hypot(x - PX, z - PZ);
        if (r < 84) continue;
        if (cherries.some((c) => Math.hypot(c[0] - x, c[1] - z) < 30)) continue;
        if (u > bambooEdge(x, z, w) - 12) continue;                         // bamboo country
        if (mound(ML, u, w, 0.5) > 0 || mound(MR, u, w, 0.5) > 0) continue;
        if (w < -150) {                                                    // foreground hills
          const kind = pick3 < 0.45 ? 'orange' : pick3 < 0.8 ? 'gold' : 'red';
          if (sz < 0.35) ginkgo(x, z, 0.9 + sz, MAPLE[kind], seed); else maple(x, z, 0.9 + sz * 0.6, MAPLE[kind], seed);
        } else if (u < -112 || w > 118) {                                    // cherry grove and back hill
          if (pick3 < 0.2) pine(x, z, 0.95 + sz * 0.4, seed);
          else { const kind = pick3 < 0.55 ? 'pink' : pick3 < 0.85 ? 'white' : 'deep'; const rr = cherry(x, z, 0.8 + sz * 0.4, BLOSSOM[kind], seed); cherries.push([x, z, rr]); }
        }
      }
    }
    report('bamboo', 0.62);
    {
      const R = rng(4242), cell = 6;
      for (let gz = 4; gz < NZ - 4; gz += cell) for (let gx = 4; gx < NX - 4; gx += cell) {
        const x = Math.round(gx + R() * (cell - 1)), z = Math.round(gz + R() * (cell - 1));
        const keep = R(), hr = R(), seed = (R() * 1e9) | 0;
        if (x < 5 || z < 5 || x > NX - 6 || z > NZ - 6 || Occ[x + NX * z]) continue;
        const [u, w] = toUW(x, z);
        const edge = u - bambooEdge(x, z, w);
        if (edge < 0 || keep > 0.78) continue;
        const hgt = Math.round((116 + hr * 36) * (0.72 + 0.28 * smooth(0, 26, edge)));
        bamboo(x, z, hgt, seed, hr > 0.7);
      }
    }

    // ---- understorey: clipped shrubs, azaleas, rocks
    report('garden', 0.74);
    {
      const R = rng(9001), cell = 13;
      for (let gz = 6; gz < NZ - 6; gz += cell) for (let gx = 6; gx < NX - 6; gx += cell) {
        const x = Math.round(gx + R() * (cell - 2)), z = Math.round(gz + R() * (cell - 2));
        const kind = R(), sz = R(), seed = (R() * 1e9) | 0;
        if (x < 8 || z < 8 || x > NX - 9 || z > NZ - 9 || !free(x, z, 3)) continue;
        const [u] = toUW(x, z);
        if (kind < 0.16) rock(x, z, 2.5 + sz * 4, seed);
        else if (kind < 0.62 && u < 112) shrub(x, z, 2.6 + sz * 3.6, seed, kind < 0.42 ? AZALEA : null);
      }
      // a clipped hedge of azaleas ringing the gravel court
      for (let k = 0; k < 44; k++) {
        const a = (k / 44) * 6.283 + 0.07, rr = 63 + 2 * Math.sin(k * 1.7);
        const x = Math.round(PX + Math.cos(a) * rr), z = Math.round(PZ + Math.sin(a) * rr);
        if (Sm[x + NX * z] === S_PATH || Sm[x + NX * z] === S_POND || Sm[x + NX * z] === S_SHORE) continue;
        if (Math.abs(x - PX) < 11 || Math.abs(z - PZ) < 11) continue;
        if (k % 5 === 2) rock(x, z, 3.2, k); else shrub(x, z, 3.4 + (k % 3) * 0.7, k, k % 2 ? AZALEA : null);
      }
      // boulders along the pond shore and the stream
      for (let k = 0; k < 26; k++) {
        const a = (k / 26) * 6.283, x = Math.round(POND.x + Math.cos(a) * (POND.rx + 2)), z = Math.round(POND.z + Math.sin(a) * (POND.rz + 2));
        if (Math.abs(z - PZ) < 9) continue;
        if (R() < 0.6) rock(x, z, 2.2 + R() * 2.8, 50 + k);
      }
    }

    // ---- pond life
    {
      const R = rng(31337);
      for (let k = 0; k < 16; k++) {                                        // lily pads, a few in flower
        const a = R() * 6.283, rr = Math.sqrt(R()) * 0.82;
        const x = Math.round(POND.x + Math.cos(a) * POND.rx * rr), z = Math.round(POND.z + Math.sin(a) * POND.rz * rr);
        if (Math.abs(z - PZ) < 8 || Wt[x + NX * z] < 0) continue;
        const y = G - 1;
        for (let dz = -1; dz <= 1; dz++) for (let dx = -1; dx <= 1; dx++) if ((dx || dz || true) && Wt[(x + dx) + NX * (z + dz)] >= 0 && Math.abs(dx) + Math.abs(dz) < 2 + (k % 2)) set(x + dx, y, z + dz, LILY[(k + dx) & 1]);
        if (k % 3 === 0) set(x, y + 1, z, LOTUS);
      }
      for (let k = 0; k < 22; k++) {                                        // koi just under the surface
        const a = R() * 6.283, rr = Math.sqrt(R()) * 0.78;
        const x = Math.round(POND.x + Math.cos(a) * POND.rx * rr), z = Math.round(POND.z + Math.sin(a) * POND.rz * rr);
        const dir = R() < 0.5, c = KOI[(R() * 3) | 0], c2 = KOI[(R() * 3) | 0];
        for (let j = 0; j < 3; j++) {
          const xx = dir ? x + j : x, zz = dir ? z : z + j, i = xx + NX * zz;
          if (Wt[i] >= 0 && V[i + NXZ * (G - 1)] === 0 && V[i + NXZ * Wt[i]] !== FALL[2]) V[i + NXZ * Wt[i]] = j === 1 ? c2 : c;
        }
      }
    }

    // ---- ground cover: grass blades, wild flowers, ferns, fallen petals
    report('garden', 0.82);
    for (let z = 2; z < NZ - 2; z++) {
      for (let x = 2; x < NX - 2; x++) {
        const i = x + NX * z, s = Sm[i], h = Hm[i];
        if (V[i + NXZ * (h + 1)] !== 0) continue;
        const hv = hash3(x, 91, z);
        if (s === S_GRASS || s === S_MOSS) {
          const dens = 0.05 + 0.1 * vnoise3(x / 11, 6.6, z / 11);
          if (hv < dens) { const n = 1 + ((hash3(x, 92, z) * 2.3) | 0); for (let k = 1; k <= n; k++) setE(x, h + k, z, BLADE[(hash3(x, k, z) * 3) | 0]); }
          else if (hv > 0.988) { setE(x, h + 1, z, BLADE[0]); setE(x, h + 2, z, FLOWER[(hash3(z, 93, x) * 5) | 0]); }
        } else if (s === S_LITTER) {
          if (hv < 0.035) { setE(x, h + 1, z, BLADE[0]); setE(x, h + 2, z, BLADE[1]); setE(x + 1, h + 2, z, BLADE[2]); setE(x - 1, h + 2, z, BLADE[1]); setE(x, h + 2, z + 1, BLADE[2]); setE(x, h + 2, z - 1, BLADE[1]); }
        } else if (s === S_SHORE) {
          if (hv < 0.05) { for (let k = 1; k <= 3; k++) setE(x, h + k, z, BLADE[1]); if (hv < 0.02) setE(x, h + 4, z, FLOWER[2]); }
        }
      }
    }
    {
      const R = rng(555);
      for (const [cx, cz, cr] of cherries) {
        const n = Math.round(cr * cr * 1.7);
        for (let k = 0; k < n; k++) {
          const a = R() * 6.283, rr = cr * 1.15 * Math.sqrt(R());
          const x = Math.round(cx + Math.cos(a) * rr), z = Math.round(cz + Math.sin(a) * rr);
          if (x < 0 || z < 0 || x >= NX || z >= NZ) continue;
          const i = x + NX * z, h = Wt[i] >= 0 ? Wt[i] : Hm[i];
          if (V[i + NXZ * (h + 1)] !== 0) continue;
          if (Wt[i] >= 0 && R() > 0.25) continue;
          V[i + NXZ * h] = PETAL[(R() * 3) | 0];
        }
      }
    }

    // ---- a few birds, far off over the trees
    {
      const flock = [[-150, 200, 186], [-100, 240, 196], [-176, 160, 174], [96, 180, 192], [128, 150, 180], [64, 230, 200], [-62, 280, 202]];
      flock.forEach(([u, w, y], k) => {
        const [x, z] = fromUW(u, w);
        const along = k % 2 === 0;        // wings spread across the view
        for (let j = -2; j <= 2; j++) {
          const yy = y + (Math.abs(j) === 2 ? (k % 3 === 0 ? 0 : 1) : Math.abs(j) === 1 ? 1 : 0);
          if (along) set(x + j, yy, z, BIRD); else set(x + j, yy, z - Math.sign(j) * (Math.abs(j) > 1 ? 1 : 0), BIRD);
        }
      });
    }
    report('done', 0.86);

    return { nx: NX, ny: NY, nz: NZ, vox: V, pagodaTop };
  }

  // -------------------------------------------------------------- encoding
  // Air voxels store how far the nearest solid is (chessboard distance - 1, capped at 31)
  // so a ray can leap across empty space; solid voxels store 31 + material id.
  function encode(V, report) {
    report = report || function () {};
    const CAP = 32;
    const px = NX + 2, pz = NZ + 2, py = NY + 2, sy = px * pz;
    const D = new Uint8Array(px * pz * py).fill(CAP);
    for (let y = 0; y < NY; y++) for (let z = 0; z < NZ; z++) {
      let i = z * NX + y * NXZ, j = 1 + (z + 1) * px + (y + 1) * sy;
      for (let x = 0; x < NX; x++, i++, j++) if (V[i] !== 0) D[j] = 0;
    }
    report('lighting grid', 0.88);
    const min = Math.min;
    for (let y = 1; y <= NY; y++) for (let z = 1; z <= NZ; z++) {
      let j = 1 + z * px + y * sy;
      for (let x = 1; x <= NX; x++, j++) {
        const c = D[j];
        if (c <= 1) continue;
        const a = j - sy, b = j - px;
        let m = min(D[a - px - 1], D[a - px], D[a - px + 1], D[a - 1], D[a], D[a + 1], D[a + px - 1], D[a + px], D[a + px + 1], D[b - 1], D[b], D[b + 1], D[j - 1]) + 1;
        if (m < c) D[j] = m;
      }
    }
    report('lighting grid', 0.94);
    for (let y = NY; y >= 1; y--) for (let z = NZ; z >= 1; z--) {
      let j = NX + z * px + y * sy;
      for (let x = NX; x >= 1; x--, j--) {
        const c = D[j];
        if (c <= 1) continue;
        const a = j + sy, b = j + px;
        let m = min(D[a - px - 1], D[a - px], D[a - px + 1], D[a - 1], D[a], D[a + 1], D[a + px - 1], D[a + px], D[a + px + 1], D[b - 1], D[b], D[b + 1], D[j + 1]) + 1;
        if (m < c) D[j] = m;
      }
    }
    const out = new Uint8Array(NXZ * NY);
    for (let y = 0; y < NY; y++) for (let z = 0; z < NZ; z++) {
      let i = z * NX + y * NXZ, j = 1 + (z + 1) * px + (y + 1) * sy;
      for (let x = 0; x < NX; x++, i++, j++) out[i] = V[i] !== 0 ? 31 + V[i] : D[j] - 1;
    }
    report('lighting grid', 1);
    return out;
  }

  // ------------------------------------------------------- camera and light
  const camDist = 494, camHeight = 210;
  const view = {
    eye: [PX + CAMX * camDist, G + camHeight, PZ + CAMZ * camDist],
    target: [PX, G + 80, PZ],
    fov: 26,
  };
  // The sun sits to the camera's left, lighting the pagoda's front and leaving its side in open shade.
  const sunAz = 52 * Math.PI / 180, sunEl = 47 * Math.PI / 180;
  const sh = [Math.cos(sunAz) * CAMX - Math.sin(sunAz) * RX, Math.cos(sunAz) * CAMZ - Math.sin(sunAz) * RZ];
  const sun = [sh[0] * Math.cos(sunEl), Math.sin(sunEl), sh[1] * Math.cos(sunEl)];

  return { NX, NY, NZ, G, PX, PZ, palette: PAL, view, sun, build, encode };
}

if (typeof module !== 'undefined' && module.exports) module.exports = voxelPagodaScene;
