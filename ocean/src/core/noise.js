// CPU noise used for world generation and placement (deterministic).

export function mulberry32(seed) {
  let a = seed >>> 0;
  return () => {
    a |= 0; a = (a + 0x6D2B79F5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

// 2D simplex noise (Gustavson), returns [-1, 1]
const F2 = 0.5 * (Math.sqrt(3) - 1);
const G2 = (3 - Math.sqrt(3)) / 6;
const grad = new Float32Array([1, 1, -1, 1, 1, -1, -1, -1, 1, 0, -1, 0, 0, 1, 0, -1]);

export function makeSimplex(seed = 1) {
  const rand = mulberry32(seed);
  const p = new Uint8Array(256);
  for (let i = 0; i < 256; i++) p[i] = i;
  for (let i = 255; i > 0; i--) { const j = Math.floor(rand() * (i + 1)); const t = p[i]; p[i] = p[j]; p[j] = t; }
  const perm = new Uint8Array(512), permMod8 = new Uint8Array(512);
  for (let i = 0; i < 512; i++) { perm[i] = p[i & 255]; permMod8[i] = perm[i] & 7; }
  return function noise2(xin, yin) {
    let n0 = 0, n1 = 0, n2 = 0;
    const s = (xin + yin) * F2;
    const i = Math.floor(xin + s), j = Math.floor(yin + s);
    const t = (i + j) * G2;
    const x0 = xin - (i - t), y0 = yin - (j - t);
    const i1 = x0 > y0 ? 1 : 0, j1 = x0 > y0 ? 0 : 1;
    const x1 = x0 - i1 + G2, y1 = y0 - j1 + G2;
    const x2 = x0 - 1 + 2 * G2, y2 = y0 - 1 + 2 * G2;
    const ii = i & 255, jj = j & 255;
    let t0 = 0.5 - x0 * x0 - y0 * y0;
    if (t0 > 0) { const g = permMod8[ii + perm[jj]] * 2; t0 *= t0; n0 = t0 * t0 * (grad[g] * x0 + grad[g + 1] * y0); }
    let t1 = 0.5 - x1 * x1 - y1 * y1;
    if (t1 > 0) { const g = permMod8[ii + i1 + perm[jj + j1]] * 2; t1 *= t1; n1 = t1 * t1 * (grad[g] * x1 + grad[g + 1] * y1); }
    let t2 = 0.5 - x2 * x2 - y2 * y2;
    if (t2 > 0) { const g = permMod8[ii + 1 + perm[jj + 1]] * 2; t2 *= t2; n2 = t2 * t2 * (grad[g] * x2 + grad[g + 1] * y2); }
    return 70 * (n0 + n1 + n2);
  };
}

export function fbm(noise, x, y, octaves = 5, lacunarity = 2.03, gain = 0.5) {
  let sum = 0, amp = 1, norm = 0, fx = x, fy = y;
  for (let o = 0; o < octaves; o++) {
    sum += noise(fx, fy) * amp; norm += amp; amp *= gain;
    // rotate each octave a little to kill grid alignment
    const nx = fx * 0.8 - fy * 0.6, ny = fx * 0.6 + fy * 0.8;
    fx = nx * lacunarity + 17.3; fy = ny * lacunarity - 9.1;
  }
  return sum / norm;
}

export function ridged(noise, x, y, octaves = 5) {
  let sum = 0, amp = 0.5, fx = x, fy = y, prev = 1;
  for (let o = 0; o < octaves; o++) {
    let n = 1 - Math.abs(noise(fx, fy));
    n *= n; sum += n * amp * prev; prev = n;
    amp *= 0.5;
    const nx = fx * 0.8 - fy * 0.6, ny = fx * 0.6 + fy * 0.8;
    fx = nx * 2.1 + 5.2; fy = ny * 2.1 + 1.7;
  }
  return sum;
}

export const smoothstep = (a, b, x) => { const t = Math.min(1, Math.max(0, (x - a) / (b - a))); return t * t * (3 - 2 * t); };
export const lerp = (a, b, t) => a + (b - a) * t;
export const clamp = (x, a, b) => Math.min(b, Math.max(a, x));
