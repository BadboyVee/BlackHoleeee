// Hydraulic erosion of the island heightfield (droplet model, after Beyer 2015).
//
// Thousands of rain droplets run downhill; each picks up sediment where it
// speeds up and drops it where it slows, so water carves dendritic gullies,
// sharpens the ridges between them and fills valley floors with soft fans.
// Besides the new heights it records where water gathers (flow) and where
// material was removed or laid down - the terrain shader and the vegetation
// read those to put rock in scoured channels and the lushest green in the
// damp valleys.
//
// Deterministic (seeded) and restricted by a mask, so the beach, the village
// terrace and the coast keep their hand-shaped profiles.

export function erode(height, N, {
  mask,                       // Float32Array N*N, 0..1: how much a cell may change
  droplets = 300000,
  seed = 1,
  scale = 100,                // metres per normalized height unit
  inertia = 0.05,
  capacity = 4,
  minCapacity = 0.01,
  erodeSpeed = 0.3,
  depositSpeed = 0.3,
  evaporate = 0.015,
  gravity = 4,
  maxSteps = 48,
  radius = 3,
} = {}) {
  const H = new Float32Array(N * N);
  for (let i = 0; i < N * N; i++) H[i] = height[i] / scale;
  const flow = new Float32Array(N * N);
  const change = new Float32Array(N * N);   // + deposited, - eroded (normalized)

  // erosion brush: weights fall off linearly with distance
  const bOff = [], bW = [];
  let wsum = 0;
  for (let y = -radius; y <= radius; y++) for (let x = -radius; x <= radius; x++) {
    const d = Math.hypot(x, y);
    if (d < radius) { bOff.push([x, y]); const w = 1 - d / radius; bW.push(w); wsum += w; }
  }
  for (let k = 0; k < bW.length; k++) bW[k] /= wsum;

  // spawn cells: wherever erosion is allowed
  const spawn = [];
  for (let i = 0; i < N * N; i++) if (mask[i] > 0.05) spawn.push(i);
  if (!spawn.length) return { height, flow, change };

  let s = seed >>> 0;
  const rnd = () => { s = (s + 0x6D2B79F5) >>> 0; let t = s; t = Math.imul(t ^ (t >>> 15), t | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return ((t ^ (t >>> 14)) >>> 0) / 4294967296; };

  // bilinear height + gradient at a cell-space position
  const hg = { h: 0, gx: 0, gy: 0 };
  const sampleHG = (px, py) => {
    const ix = px | 0, iy = py | 0;
    const u = px - ix, v = py - iy;
    const k = iy * N + ix;
    const a = H[k], b = H[k + 1], c = H[k + N], d = H[k + N + 1];
    hg.gx = (b - a) * (1 - v) + (d - c) * v;
    hg.gy = (c - a) * (1 - u) + (d - b) * u;
    hg.h = a * (1 - u) * (1 - v) + b * u * (1 - v) + c * (1 - u) * v + d * u * v;
  };

  for (let n = 0; n < droplets; n++) {
    const c0 = spawn[(rnd() * spawn.length) | 0];
    let px = (c0 % N) + rnd(), py = ((c0 / N) | 0) + rnd();
    let dx = 0, dy = 0, speed = 1, water = 1, sediment = 0;
    for (let step = 0; step < maxSteps; step++) {
      const ix = px | 0, iy = py | 0;
      if (ix < radius || iy < radius || ix >= N - radius - 1 || iy >= N - radius - 1) break;
      const k = iy * N + ix;
      const u = px - ix, v = py - iy;
      sampleHG(px, py);
      const h0 = hg.h;
      dx = dx * inertia - hg.gx * (1 - inertia);
      dy = dy * inertia - hg.gy * (1 - inertia);
      const len = Math.hypot(dx, dy);
      if (len < 1e-9) break;
      dx /= len; dy /= len;
      px += dx; py += dy;
      const nx = px | 0, ny = py | 0;
      if (nx < radius || ny < radius || nx >= N - radius - 1 || ny >= N - radius - 1) break;
      flow[k] += water;
      // leaving the erodible area (beach, coast, village): stop here and
      // keep the sediment rather than piling it up at the boundary
      const m = mask[k];
      if (m <= 0.05) break;
      sampleHG(px, py);
      const dh = hg.h - h0;
      const cap = Math.max(-dh * speed * water * capacity, minCapacity);
      if (sediment > cap || dh > 0) {
        // uphill: fill the pit we just crossed; otherwise drop the excess
        const amt = dh > 0 ? Math.min(dh, sediment) : (sediment - cap) * depositSpeed;
        sediment -= amt;
        const a = amt * m;
        H[k] += a * (1 - u) * (1 - v); change[k] += a * (1 - u) * (1 - v);
        H[k + 1] += a * u * (1 - v); change[k + 1] += a * u * (1 - v);
        H[k + N] += a * (1 - u) * v; change[k + N] += a * (1 - u) * v;
        H[k + N + 1] += a * u * v; change[k + N + 1] += a * u * v;
      } else {
        const amt = Math.min((cap - sediment) * erodeSpeed, -dh);
        for (let b = 0; b < bOff.length; b++) {
          const kk = (iy + bOff[b][1]) * N + ix + bOff[b][0];
          const w = amt * bW[b] * mask[kk];
          const e = H[kk] < w ? H[kk] : w;
          H[kk] -= e; change[kk] -= e;
          sediment += e;
        }
      }
      speed = Math.sqrt(Math.max(speed * speed + dh * gravity, 0));
      water *= 1 - evaporate;
    }
  }
  const out = new Float32Array(N * N);
  for (let i = 0; i < N * N; i++) { out[i] = H[i] * scale; change[i] *= scale; }
  return { height: out, flow, change };
}

/** Separable box blur (clamped edges), in place friendly. */
export function blur(src, N, r) {
  const tmp = new Float32Array(N * N), out = new Float32Array(N * N);
  const w = 1 / (2 * r + 1);
  for (let j = 0; j < N; j++) {
    const row = j * N;
    let acc = 0;
    for (let i = -r; i <= r; i++) acc += src[row + Math.min(Math.max(i, 0), N - 1)];
    for (let i = 0; i < N; i++) {
      tmp[row + i] = acc * w;
      acc += src[row + Math.min(i + r + 1, N - 1)] - src[row + Math.max(i - r, 0)];
    }
  }
  for (let i = 0; i < N; i++) {
    let acc = 0;
    for (let j = -r; j <= r; j++) acc += tmp[Math.min(Math.max(j, 0), N - 1) * N + i];
    for (let j = 0; j < N; j++) {
      out[j * N + i] = acc * w;
      acc += tmp[Math.min(j + r + 1, N - 1) * N + i] - tmp[Math.max(j - r, 0) * N + i];
    }
  }
  return out;
}

/**
 * Two-scale erosion: a pass on a half-resolution grid carves the large
 * valleys (droplets travel twice as far per step), then a full-resolution
 * pass cuts the gullies and rills into them.
 */
export function erodeMultiscale(height, N, { mask, coarse = {}, fine = {}, seed = 1 } = {}) {
  const M = N >> 1;
  const down = (src) => {
    const o = new Float32Array(M * M);
    for (let j = 0; j < M; j++) for (let i = 0; i < M; i++) {
      const k = j * 2 * N + i * 2;
      o[j * M + i] = (src[k] + src[k + 1] + src[k + N] + src[k + N + 1]) * 0.25;
    }
    return o;
  };
  // bilinear upsample (cell centres of the coarse grid sit between fine cells)
  const up = (src) => {
    const o = new Float32Array(N * N);
    for (let j = 0; j < N; j++) {
      const fy = Math.min(Math.max((j - 0.5) / 2, 0), M - 1.001);
      const y0 = fy | 0, ty = fy - y0;
      for (let i = 0; i < N; i++) {
        const fx = Math.min(Math.max((i - 0.5) / 2, 0), M - 1.001);
        const x0 = fx | 0, tx = fx - x0;
        const k = y0 * M + x0;
        o[j * N + i] = (src[k] * (1 - tx) + src[k + 1] * tx) * (1 - ty) + (src[k + M] * (1 - tx) + src[k + M + 1] * tx) * ty;
      }
    }
    return o;
  };
  const hc = down(height), mc = down(mask);
  const rc = erode(hc, M, { mask: mc, seed, ...coarse });
  const dc = new Float32Array(M * M);
  for (let i = 0; i < M * M; i++) dc[i] = rc.height[i] - hc[i];
  const delta = up(dc), flowC = up(rc.flow);
  const h1 = new Float32Array(N * N);
  for (let i = 0; i < N * N; i++) h1[i] = height[i] + delta[i];
  const rf = erode(h1, N, { mask, seed: seed + 1, ...fine });
  const flow = new Float32Array(N * N), change = new Float32Array(N * N);
  for (let i = 0; i < N * N; i++) {
    flow[i] = rf.flow[i] + flowC[i] * 0.5;
    change[i] = rf.change[i] + delta[i];
  }
  return { height: rf.height, flow, change };
}

/**
 * Stream-power incision (Braun & Willett 2013): each cell drains to one
 * neighbour; channels cut down in proportion to sqrt(upstream area) times
 * slope, solved implicitly from the outlets upward. Large drainage areas
 * make valleys that branch and merge like real ones, with sharp ridges left
 * between them; hillslope diffusion then rounds the crests, and a talus
 * pass keeps valley walls standable.
 *
 * Drainage is routed with priority-flood (Barnes 2014), so closed basins
 * spill over their lowest rim instead of trapping water.
 */
export function streamPowerErode(height, N, {
  mask, cell = 1, iterations = 40, K = 0.0006, m = 0.5, diffusion = 0.02, talus = 0.8, eps = 1e-3,
} = {}) {
  const NN = N * N;
  const h = new Float64Array(NN);
  for (let i = 0; i < NN; i++) h[i] = height[i];
  const rec = new Int32Array(NN), stack = new Int32Array(NN), area = new Float64Array(NN);
  const recDist = new Float32Array(NN);
  const fill = new Float64Array(NN);
  const state = new Uint8Array(NN);   // 0 unvisited, 1 queued/visited
  const erodible = new Uint8Array(NN);
  for (let i = 0; i < NN; i++) erodible[i] = mask[i] > 0.02 ? 1 : 0;
  const DX = [1, -1, 0, 0, 1, 1, -1, -1], DY = [0, 0, 1, -1, 1, -1, 1, -1];
  const DL = [1, 1, 1, 1, Math.SQRT2, Math.SQRT2, Math.SQRT2, Math.SQRT2];
  // binary min-heap on fill height
  const heapK = new Float64Array(NN), heapV = new Int32Array(NN);
  let hn = 0;
  const push = (k, v) => {
    let i = hn++;
    while (i > 0) { const p = (i - 1) >> 1; if (heapK[p] <= k) break; heapK[i] = heapK[p]; heapV[i] = heapV[p]; i = p; }
    heapK[i] = k; heapV[i] = v;
  };
  const pop = () => {
    const v = heapV[0], k = heapK[--hn], x = heapV[hn];
    let i = 0;
    for (;;) {
      let c = 2 * i + 1; if (c >= hn) break;
      if (c + 1 < hn && heapK[c + 1] < heapK[c]) c++;
      if (heapK[c] >= k) break;
      heapK[i] = heapK[c]; heapV[i] = heapV[c]; i = c;
    }
    heapK[i] = k; heapV[i] = x;
    return v;
  };
  const flow = new Float32Array(NN);
  for (let it = 0; it < iterations; it++) {
    // --- routing: flood from the fixed cells (sea, beach, village) inward
    state.fill(0); hn = 0;
    let ns = 0;
    for (let j = 1; j < N - 1; j++) for (let i = 1; i < N - 1; i++) {
      const k = j * N + i;
      if (erodible[k]) continue;
      // fixed cells bordering the erodible area are the outlets
      let border = false;
      for (let d = 0; d < 8 && !border; d++) if (erodible[k + DY[d] * N + DX[d]]) border = true;
      if (border) { state[k] = 1; fill[k] = h[k]; push(h[k], k); rec[k] = k; }
    }
    while (hn > 0) {
      const c = pop();
      if (erodible[c]) stack[ns++] = c;
      const ci = c % N, cj = (c / N) | 0;
      for (let d = 0; d < 8; d++) {
        const ii = ci + DX[d], jj = cj + DY[d];
        if (ii < 1 || jj < 1 || ii >= N - 1 || jj >= N - 1) continue;
        const k = jj * N + ii;
        if (state[k] || !erodible[k]) continue;
        state[k] = 1;
        fill[k] = Math.max(h[k], fill[c] + eps);
        rec[k] = c; recDist[k] = DL[d] * cell;
        push(fill[k], k);
      }
    }
    // --- drainage area (m^2), accumulated from the tips down
    for (let s = 0; s < ns; s++) area[stack[s]] = cell * cell;
    for (let s = ns - 1; s >= 0; s--) { const k = stack[s]; const r = rec[k]; if (erodible[r]) area[r] += area[k]; }
    // --- implicit incision, outlets first
    for (let s = 0; s < ns; s++) {
      const k = stack[s], r = rec[k];
      if (h[k] <= h[r]) continue;
      const F = K * mask[k] * Math.pow(area[k], m) / recDist[k];
      h[k] = (h[k] + F * h[r]) / (1 + F);
    }
    // --- hillslope diffusion (explicit), rounds crests and softens rills
    if (diffusion > 0) {
      for (let s = 0; s < ns; s++) {
        const k = stack[s];
        const lap = h[k - 1] + h[k + 1] + h[k - N] + h[k + N] - 4 * h[k];
        fill[k] = h[k] + diffusion * mask[k] * lap;
      }
      for (let s = 0; s < ns; s++) h[stack[s]] = fill[stack[s]];
    }
    if (it === iterations - 1) for (let s = 0; s < ns; s++) flow[stack[s]] = area[stack[s]];
  }
  // --- talus: no wall steeper than `talus` (rise over run) except where fixed
  for (let pass = 0; pass < 30; pass++) {
    let moved = 0;
    for (let j = 1; j < N - 1; j++) for (let i = 1; i < N - 1; i++) {
      const k = j * N + i;
      if (!erodible[k]) continue;
      for (let d = 0; d < 4; d++) {
        const n = k + DY[d] * N + DX[d];
        const diff = h[k] - h[n] - talus * cell;
        if (diff > 0) { const a = diff * 0.25 * mask[k] * (erodible[n] ? 1 : 0); h[k] -= a; h[n] += a; moved += a; }
      }
    }
    if (moved < 1e-3) break;
  }
  const out = new Float32Array(NN), change = new Float32Array(NN);
  for (let i = 0; i < NN; i++) { out[i] = h[i]; change[i] = h[i] - height[i]; }
  return { height: out, flow, change };
}
