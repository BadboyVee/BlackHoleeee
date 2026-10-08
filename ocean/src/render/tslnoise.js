// TSL noise library: world-space (non-periodic) and periodic (tileable) noise
// used by materials and the texture baker.

import {
  Fn, float, vec2, vec3, vec4, uint, uvec2, uvec3, floor, fract, dot, mix, min, max, sqrt, abs,
  sin, cos, length, smoothstep, clamp,
} from 'three/tsl';

// ---------------------------------------------------------------- hashing
// pure-expression PCG2D (usable outside Fn stacks)
export const pcg2 = (v) => {
  const x = v.mul(uint(1664525)).add(uint(1013904223));
  let a = x.x.add(x.y.mul(uint(1664525)));
  let b = x.y.add(a.mul(uint(1664525)));
  a = a.bitXor(a.shiftRight(uint(16)));
  b = b.bitXor(b.shiftRight(uint(16)));
  const a2 = a.add(b.mul(uint(1664525)));
  const b2 = b.add(a2.mul(uint(1664525)));
  return uvec2(a2.bitXor(a2.shiftRight(uint(16))), b2.bitXor(b2.shiftRight(uint(16))));
};

/** vec2 cell (can be negative, float) -> vec2 in [0,1) */
export const hash22 = (p) => vec2(pcg2(uvec2(p.add(32768)))).div(4294967295.0);
export const hash21 = (p) => hash22(p).x;

export const hash33 = (p) => {
  const v = uvec3(p.add(32768)).mul(uint(1664525)).add(uint(1013904223));
  let x = v.x.add(v.y.mul(v.z));
  let y = v.y.add(v.z.mul(x));
  let z = v.z.add(x.mul(y));
  x = x.bitXor(x.shiftRight(uint(16))); y = y.bitXor(y.shiftRight(uint(16))); z = z.bitXor(z.shiftRight(uint(16)));
  const x2 = x.add(y.mul(z));
  const y2 = y.add(z.mul(x2));
  const z2 = z.add(x2.mul(y2));
  return vec3(x2, y2, z2).div(4294967295.0);
};

const quintic = (t) => t.mul(t).mul(t).mul(t.mul(t.mul(6).sub(15)).add(10));

// ---------------------------------------------------------------- world space
/** 2D value noise in [0,1] */
export const vnoise2 = Fn(([p]) => {
  const i = floor(p), f = fract(p);
  const u = f.mul(f).mul(f.mul(-2).add(3));
  const a = hash21(i), b = hash21(i.add(vec2(1, 0))), c = hash21(i.add(vec2(0, 1))), d = hash21(i.add(vec2(1, 1)));
  return mix(mix(a, b, u.x), mix(c, d, u.x), u.y);
}).setLayout({ name: 'vnoise2', type: 'float', inputs: [{ name: 'p', type: 'vec2' }] });

/** 2D gradient noise in [-1,1] */
export const gnoise2 = Fn(([p]) => {
  const i = floor(p), f = fract(p);
  const u = quintic(f);
  const g = (o) => {
    const h = hash22(i.add(o)).mul(6.2831853);
    return dot(vec2(cos(h.x), sin(h.x)), f.sub(o));
  };
  return mix(mix(g(vec2(0, 0)), g(vec2(1, 0)), u.x), mix(g(vec2(0, 1)), g(vec2(1, 1)), u.x), u.y).mul(1.4);
}).setLayout({ name: 'gnoise2', type: 'float', inputs: [{ name: 'p', type: 'vec2' }] });

/** 3D value noise in [0,1] */
export const vnoise3 = Fn(([p]) => {
  const i = floor(p), f = fract(p);
  const u = f.mul(f).mul(f.mul(-2).add(3));
  const h = (o) => hash33(i.add(o)).x;
  const x00 = mix(h(vec3(0, 0, 0)), h(vec3(1, 0, 0)), u.x), x10 = mix(h(vec3(0, 1, 0)), h(vec3(1, 1, 0)), u.x);
  const x01 = mix(h(vec3(0, 0, 1)), h(vec3(1, 0, 1)), u.x), x11 = mix(h(vec3(0, 1, 1)), h(vec3(1, 1, 1)), u.x);
  return mix(mix(x00, x10, u.y), mix(x01, x11, u.y), u.z);
}).setLayout({ name: 'vnoise3', type: 'float', inputs: [{ name: 'p', type: 'vec3' }] });

export function fbm2(p, octaves = 4, gain = 0.5, lac = 2.03) {
  let sum = float(0), amp = 0.5, norm = 0, q = p;
  for (let o = 0; o < octaves; o++) {
    sum = sum.add(gnoise2(q).mul(amp)); norm += amp; amp *= gain;
    q = vec2(q.x.mul(0.8).sub(q.y.mul(0.6)), q.x.mul(0.6).add(q.y.mul(0.8))).mul(lac).add(vec2(17.3, -9.1));
  }
  return sum.div(norm);
}

export function fbm3(p, octaves = 4, gain = 0.5) {
  let sum = float(0), amp = 0.5, norm = 0, q = p;
  for (let o = 0; o < octaves; o++) {
    sum = sum.add(vnoise3(q).mul(amp)); norm += amp; amp *= gain;
    q = q.mul(2.07).add(vec3(5.1, 1.3, 7.7));
  }
  return sum.div(norm);
}

/** 2D Voronoi: returns vec4(F1, F2, cellHashA, cellHashB) */
export const voronoi2 = Fn(([p]) => {
  const i = floor(p), f = fract(p);
  const f1 = float(8).toVar(), f2 = float(8).toVar();
  const id = vec2(0).toVar();
  for (let y = -1; y <= 1; y++) for (let x = -1; x <= 1; x++) {
    const o = vec2(x, y);
    const h = hash22(i.add(o));
    const d = length(o.add(h).sub(f));
    const closer = d.lessThan(f1);
    f2.assign(closer.select(f1, min(f2, d)));
    id.assign(closer.select(hash22(i.add(o).add(71.3)), id));
    f1.assign(min(f1, d));
  }
  return vec4(f1, f2, id);
}).setLayout({ name: 'voronoi2', type: 'vec4', inputs: [{ name: 'p', type: 'vec2' }] });

// ---------------------------------------------------------------- periodic
const wrap2 = (c, period) => c.sub(floor(c.div(period)).mul(period));

/** periodic gradient noise in [-1,1]; p in [0,1)^2 * period */
export const gnoiseP = Fn(([p, period]) => {
  const i = floor(p), f = fract(p);
  const u = quintic(f);
  const g = (o) => {
    const h = hash22(wrap2(i.add(o), period)).mul(6.2831853);
    return dot(vec2(cos(h.x), sin(h.x)), f.sub(o));
  };
  return mix(mix(g(vec2(0, 0)), g(vec2(1, 0)), u.x), mix(g(vec2(0, 1)), g(vec2(1, 1)), u.x), u.y).mul(1.4);
}).setLayout({ name: 'gnoiseP', type: 'float', inputs: [{ name: 'p', type: 'vec2' }, { name: 'period', type: 'vec2' }] });

/** periodic value noise in [0,1] */
export const vnoiseP = Fn(([p, period]) => {
  const i = floor(p), f = fract(p);
  const u = f.mul(f).mul(f.mul(-2).add(3));
  const h = (o) => hash21(wrap2(i.add(o), period));
  return mix(mix(h(vec2(0, 0)), h(vec2(1, 0)), u.x), mix(h(vec2(0, 1)), h(vec2(1, 1)), u.x), u.y);
}).setLayout({ name: 'vnoiseP', type: 'float', inputs: [{ name: 'p', type: 'vec2' }, { name: 'period', type: 'vec2' }] });

/** periodic fBm over uv in [0,1)^2 with base integer frequency */
export function fbmP(uv, freq, octaves = 5, gain = 0.5, fn = gnoiseP) {
  let sum = float(0), amp = 0.5, norm = 0;
  let f = freq;
  for (let o = 0; o < octaves; o++) {
    const period = vec2(f[0], f[1]);
    sum = sum.add(fn(uv.mul(period).add(vec2(o * 13.7, o * 7.3).mul(0)), period).mul(amp));
    norm += amp; amp *= gain; f = [f[0] * 2, f[1] * 2];
  }
  return sum.div(norm);
}

/** periodic Voronoi: vec4(F1, F2, idA, idB); uv in [0,1)^2, freq cells per tile */
export const voronoiP = Fn(([p, period]) => {
  const i = floor(p), f = fract(p);
  const f1 = float(8).toVar(), f2 = float(8).toVar();
  const id = vec2(0).toVar();
  for (let y = -1; y <= 1; y++) for (let x = -1; x <= 1; x++) {
    const o = vec2(x, y);
    const c = wrap2(i.add(o), period);
    const h = hash22(c);
    const d = length(o.add(h).sub(f));
    const closer = d.lessThan(f1);
    f2.assign(closer.select(f1, min(f2, d)));
    id.assign(closer.select(hash22(c.add(71.3)), id));
    f1.assign(min(f1, d));
  }
  return vec4(f1, f2, id);
}).setLayout({ name: 'voronoiP', type: 'vec4', inputs: [{ name: 'p', type: 'vec2' }, { name: 'period', type: 'vec2' }] });
