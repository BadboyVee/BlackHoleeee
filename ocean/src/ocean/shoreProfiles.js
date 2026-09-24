// Keyframed breaking-wave cross sections.
//
// Each keyframe maps a vertex's rest position s (distance from the crest in
// units of wave height H; s > 0 behind/seaward, s < 0 in front/shoreward) to
// a target point (xi, y) in the wave frame, also in units of H (xi forward
// toward the shore). Keyframes run from a shoaled crest, through a steep face,
// an overhanging lip that curls and falls, the impact, to a turbulent bore.
//
// Baked into a small float texture sampled with (s, beta):
//   r: forward displacement  (xi + s) * H      (identity outside the crest zone)
//   g: height y * H
//   b: whitewater (only after the lip has hit the trough)
//   a: sheet thinness (thin lip / crest -> translucent when backlit)

import * as THREE from 'three/webgpu';

export const PROFILE = { sMin: -7, sMax: 5, S: 128, B: 24, betaMax: 3.2 };

// rest s -> [xi, y, foam, thin] control points per keyframe (beta)
const KEYS = [
  { beta: 0.0, pts: [
    [5, -5, 0.00, 0, 0], [2.5, -2.5, 0.18, 0, 0], [1.2, -1.2, 0.55, 0, 0.1], [0, 0, 0.78, 0, 0.2],
    [-1.2, 1.2, 0.55, 0, 0.1], [-2.5, 2.5, 0.18, 0, 0], [-7, 7, 0.0, 0, 0]] },
  { beta: 0.55, pts: [   // steepening, asymmetric (front face steeper)
    [5, -5, -0.02, 0, 0], [2.5, -2.4, 0.22, 0, 0], [1.1, -1.05, 0.62, 0, 0.1], [0, 0.05, 0.92, 0, 0.3],
    [-0.6, 0.62, 0.62, 0, 0.3], [-1.3, 1.3, 0.2, 0, 0.05], [-2.6, 2.6, -0.05, 0, 0], [-7, 7, -0.05, 0, 0]] },
  { beta: 1.0, pts: [    // vertical face, crest starting to pitch
    [5, -5, -0.05, 0, 0], [2.5, -2.35, 0.25, 0, 0], [1.1, -0.9, 0.72, 0, 0.1], [0, 0.22, 1.02, 0, 0.5],
    [-0.35, 0.55, 0.9, 0, 0.7], [-0.8, 0.62, 0.45, 0, 0.3], [-1.5, 0.75, 0.08, 0, 0.1], [-2.6, 2.3, -0.12, 0, 0], [-7, 7, -0.12, 0, 0]] },
  { beta: 1.5, pts: [    // overhanging lip, open tube
    [5, -5, -0.08, 0, 0], [2.5, -2.3, 0.28, 0, 0], [1.1, -0.8, 0.78, 0, 0.1], [0.2, 0.15, 1.08, 0, 0.4],
    [-0.3, 0.72, 1.05, 0, 0.8], [-0.7, 1.1, 0.88, 0, 1.0], [-1.0, 1.18, 0.66, 0, 1.0], [-1.35, 1.0, 0.5, 0, 0.8],
    [-1.8, 0.62, 0.38, 0, 0.4], [-2.4, 0.35, 0.18, 0, 0.2], [-3.1, 0.55, -0.1, 0, 0], [-4.2, 2.0, -0.16, 0, 0], [-7, 7, -0.16, 0, 0]] },
  { beta: 1.9, pts: [    // lip falling as a sheet, tube closing
    [5, -5, -0.08, 0, 0], [2.5, -2.3, 0.26, 0, 0], [1.1, -0.75, 0.72, 0, 0.1], [0.2, 0.3, 0.95, 0, 0.4],
    [-0.35, 0.95, 0.9, 0, 0.8], [-0.75, 1.45, 0.6, 0, 1.0], [-1.05, 1.62, 0.28, 0.05, 1.0], [-1.35, 1.45, 0.08, 0.1, 0.9],
    [-1.8, 0.9, 0.18, 0, 0.5], [-2.4, 0.45, 0.1, 0, 0.2], [-3.2, 0.9, -0.12, 0, 0], [-4.4, 2.3, -0.16, 0, 0], [-7, 7, -0.16, 0, 0]] },
  { beta: 2.25, pts: [   // impact: lip hits the trough, splash-up, whitewater begins
    [5, -5, -0.05, 0.1, 0], [2.5, -2.3, 0.2, 0.2, 0], [1.1, -0.8, 0.55, 0.45, 0], [0.2, 0.3, 0.72, 0.8, 0.2],
    [-0.5, 1.05, 0.6, 1.0, 0.3], [-1.1, 1.6, 0.35, 1.0, 0.2], [-1.6, 1.9, 0.2, 1.0, 0.1], [-2.4, 2.4, 0.05, 0.6, 0],
    [-3.4, 3.3, -0.08, 0.1, 0], [-7, 7, -0.1, 0, 0]] },
  { beta: 2.7, pts: [    // collapsing into a bore
    [5, -5, 0.0, 0.3, 0], [2.5, -2.4, 0.18, 0.5, 0], [1.0, -0.9, 0.42, 0.8, 0], [0, 0.1, 0.52, 1.0, 0],
    [-0.8, 0.95, 0.42, 1.0, 0], [-1.5, 1.6, 0.18, 0.9, 0], [-2.3, 2.35, 0.0, 0.4, 0], [-7, 7, -0.05, 0, 0]] },
  { beta: 3.2, pts: [    // turbulent bore
    [5, -5, 0.05, 0.4, 0], [2.5, -2.5, 0.16, 0.6, 0], [1.0, -1.0, 0.3, 0.9, 0], [0, 0.0, 0.36, 1.0, 0],
    [-0.8, 0.8, 0.26, 0.9, 0], [-1.6, 1.6, 0.06, 0.5, 0], [-2.6, 2.6, 0.0, 0.1, 0], [-7, 7, 0.0, 0, 0]] },
];

// Catmull-Rom through control points sorted by s (descending in the table)
function sampleKey(key, s) {
  const p = key.pts;
  // pts are sorted from s = +5 (seaward) down to s = -7
  if (s >= p[0][0]) return p[0].slice(1).map((v, i) => (i === 0 ? -s : v));
  if (s <= p[p.length - 1][0]) return p[p.length - 1].slice(1).map((v, i) => (i === 0 ? -s : v));
  let i = 0;
  while (i < p.length - 2 && s < p[i + 1][0]) i++;
  const p0 = p[Math.max(i - 1, 0)], p1 = p[i], p2 = p[i + 1], p3 = p[Math.min(i + 2, p.length - 1)];
  const t = (p1[0] - s) / (p1[0] - p2[0]);
  const out = [];
  for (let k = 1; k <= 4; k++) {
    const a = p0[k], b = p1[k], c = p2[k], d = p3[k];
    const t2 = t * t, t3 = t2 * t;
    out.push(0.5 * ((2 * b) + (-a + c) * t + (2 * a - 5 * b + 4 * c - d) * t2 + (-a + 3 * b - 3 * c + d) * t3));
  }
  return out;
}

export function buildProfileTexture() {
  const { S, B, sMin, sMax, betaMax } = PROFILE;
  const data = new Float32Array(S * B * 4);
  for (let j = 0; j < B; j++) {
    const beta = (j / (B - 1)) * betaMax;
    let k = 0;
    while (k < KEYS.length - 2 && beta > KEYS[k + 1].beta) k++;
    const k0 = KEYS[k], k1 = KEYS[k + 1];
    let t = Math.min(1, Math.max(0, (beta - k0.beta) / (k1.beta - k0.beta)));
    t = t * t * (3 - 2 * t);
    for (let i = 0; i < S; i++) {
      const s = sMin + (i / (S - 1)) * (sMax - sMin);
      const a = sampleKey(k0, s), b = sampleKey(k1, s);
      const xi = a[0] + (b[0] - a[0]) * t;
      const y = a[1] + (b[1] - a[1]) * t;
      const foam = a[2] + (b[2] - a[2]) * t;
      const thin = a[3] + (b[3] - a[3]) * t;
      const o = (j * S + i) * 4;
      data[o] = xi + s;            // displacement forward (units of H)
      data[o + 1] = y;
      data[o + 2] = Math.max(0, foam);
      data[o + 3] = Math.max(0, thin);
    }
  }
  const tex = new THREE.DataTexture(toHalf(data), S, B, THREE.RGBAFormat, THREE.HalfFloatType);
  tex.magFilter = THREE.LinearFilter;
  tex.minFilter = THREE.LinearFilter;
  tex.wrapS = tex.wrapT = THREE.ClampToEdgeWrapping;
  tex.generateMipmaps = false;
  tex.needsUpdate = true;
  tex.name = 'shore.profiles';
  return tex;
}

function toHalf(f32) {
  const out = new Uint16Array(f32.length);
  for (let i = 0; i < f32.length; i++) out[i] = THREE.DataUtils.toHalfFloat(f32[i]);
  return out;
}
