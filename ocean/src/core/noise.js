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

// ------------------------------------------------------------------ TSL twins
// Bit-exact CPU versions of tslnoise.js' hash22 / gnoise2 / fbm2, so CPU-side
// placement (trees) agrees with the masks the shaders draw (forest floor).
const U = (x) => x >>> 0;
function pcg2(x0, y0) {
  const x = U(Math.imul(x0, 1664525) + 1013904223), y = U(Math.imul(y0, 1664525) + 1013904223);
  let a = U(x + Math.imul(y, 1664525));
  let b = U(y + Math.imul(a, 1664525));
  a = U(a ^ (a >>> 16));
  b = U(b ^ (b >>> 16));
  const a2 = U(a + Math.imul(b, 1664525));
  const b2 = U(b + Math.imul(a2, 1664525));
  return [U(a2 ^ (a2 >>> 16)), U(b2 ^ (b2 >>> 16))];
}

/** hash22 twin: integer cell -> [0,1)^2 */
export function hash22(x, y) {
  const [a, b] = pcg2(Math.trunc(x + 32768), Math.trunc(y + 32768));
  return [a / 4294967295, b / 4294967295];
}

const quintic = (t) => t * t * t * (t * (t * 6 - 15) + 10);

/** gnoise2 twin: 2D gradient noise in [-1, 1] */
export function gnoise2(px, py) {
  const ix = Math.floor(px), iy = Math.floor(py), fx = px - ix, fy = py - iy;
  const g = (ox, oy) => {
    const h = hash22(ix + ox, iy + oy)[0] * 6.2831853;
    return Math.cos(h) * (fx - ox) + Math.sin(h) * (fy - oy);
  };
  const ux = quintic(fx), uy = quintic(fy);
  const a = g(0, 0) + (g(1, 0) - g(0, 0)) * ux, b = g(0, 1) + (g(1, 1) - g(0, 1)) * ux;
  return (a + (b - a) * uy) * 1.4;
}

/** fbm2 twin (rotating, lacunarity 2.03) */
export function fbm2(px, py, octaves = 4, gain = 0.5, lac = 2.03) {
  let sum = 0, amp = 0.5, norm = 0, qx = px, qy = py;
  for (let o = 0; o < octaves; o++) {
    sum += gnoise2(qx, qy) * amp; norm += amp; amp *= gain;
    const rx = qx * 0.8 - qy * 0.6, ry = qx * 0.6 + qy * 0.8;
    qx = rx * lac + 17.3; qy = ry * lac - 9.1;
  }
  return sum / norm;
}

/** forest mask shared by the terrain (leaf litter), grass and tree placement */
export function forestMask(x, z) {
  const n1 = fbm2(x * 0.018, z * 0.018, 3) * 0.5 + 0.5;
  const west = Math.min(1, Math.max(0, (-60 - x) / 140));   // the western ("left") hill is wooded
  const t = Math.min(1, Math.max(0, (n1 + west * west * (3 - 2 * west) * 0.2 - 0.45) / 0.17));
  return t * t * (3 - 2 * t);
}
