// Animation helpers: easing, curves, camera rails. Everything is a pure function of time.
import * as THREE from 'three';

export const clamp01 = (x) => Math.max(0, Math.min(1, x));
export const lerp = (a, b, t) => a + (b - a) * t;
export const smoothstep = (a, b, x) => { const t = clamp01((x - a) / (b - a)); return t * t * (3 - 2 * t); };
export const smootherstep = (a, b, x) => { const t = clamp01((x - a) / (b - a)); return t * t * t * (t * (t * 6 - 15) + 10); };
export const easeInOutCubic = (t) => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2);
export const easeOutCubic = (t) => 1 - Math.pow(1 - t, 3);
export const easeInCubic = (t) => t * t * t;
export const easeOutBack = (t, s = 1.7) => 1 + (s + 1) * Math.pow(t - 1, 3) + s * Math.pow(t - 1, 2);
export const easeInOutSine = (t) => -(Math.cos(Math.PI * t) - 1) / 2;

export function rng(seed) { let s = seed >>> 0 || 1; return () => ((s = (s * 16807) % 2147483647) / 2147483647); }

export function bezier3(p0, p1, p2, p3, t, out = new THREE.Vector3()) {
  const u = 1 - t;
  return out.set(0, 0, 0)
    .addScaledVector(p0, u * u * u).addScaledVector(p1, 3 * u * u * t)
    .addScaledVector(p2, 3 * u * t * t).addScaledVector(p3, t * t * t);
}

// damped spring settling to 0: value after an impulse at t0
export function spring(t, t0, amp, freq = 4, damp = 7) {
  if (t < t0) return 0;
  const x = t - t0;
  return amp * Math.exp(-damp * x) * Math.cos(2 * Math.PI * freq * x);
}
export function springSin(t, t0, amp, freq = 4, damp = 7) {
  if (t < t0) return 0;
  const x = t - t0;
  return amp * Math.exp(-damp * x) * Math.sin(2 * Math.PI * freq * x);
}

// Keyframed rail: keys = [{t, pos:[x,y,z], target:[x,y,z], fstop, focal}] ; Catmull-Rom through
// positions and targets, eased in time between the first and last key.
export class Rail {
  constructor(keys, { ease = true } = {}) {
    this.keys = keys;
    this.pos = new THREE.CatmullRomCurve3(keys.map((k) => new THREE.Vector3(...k.pos)), false, 'centripetal');
    this.tgt = new THREE.CatmullRomCurve3(keys.map((k) => new THREE.Vector3(...k.target)), false, 'centripetal');
    this.ease = ease;
  }
  // map time to curve parameter: piecewise linear between keys, with smooth in/out at ends
  param(t) {
    const K = this.keys, n = K.length;
    if (t <= K[0].t) return 0;
    if (t >= K[n - 1].t) return 1;
    let i = 0; while (i < n - 2 && t > K[i + 1].t) i++;
    let f = (t - K[i].t) / (K[i + 1].t - K[i].t);
    if (K[i].ease === 'in') f = f * f; else if (K[i].ease === 'out') f = 1 - (1 - f) * (1 - f); else if (K[i].ease !== 'linear') f = easeInOutSine(f);
    return (i + f) / (n - 1);
  }
  scalar(name, t, def) {
    const K = this.keys; const n = K.length;
    const vals = K.map((k) => k[name] ?? def);
    if (t <= K[0].t) return vals[0];
    if (t >= K[n - 1].t) return vals[n - 1];
    let i = 0; while (i < n - 2 && t > K[i + 1].t) i++;
    const f = easeInOutSine((t - K[i].t) / (K[i + 1].t - K[i].t));
    return lerp(vals[i], vals[i + 1], f);
  }
  apply(camera, t) {
    const u = this.param(t);
    camera.position.copy(this.pos.getPoint(u));
    const target = this.tgt.getPoint(u);
    camera.up.set(0, 1, 0);
    camera.lookAt(target);
    const roll = this.scalar('roll', t, 0);
    if (roll) camera.rotateZ(roll);
    return target;
  }
}

// handheld-style drift: smooth pseudo-random rotation offsets
export function handheld(camera, t, amount = 0.002, speed = 1) {
  const a = Math.sin(t * 1.3 * speed) * 0.6 + Math.sin(t * 2.9 * speed + 1.3) * 0.3 + Math.sin(t * 5.1 * speed + 4.1) * 0.1;
  const b = Math.sin(t * 1.1 * speed + 2.1) * 0.6 + Math.sin(t * 2.3 * speed + 0.4) * 0.3 + Math.sin(t * 4.7 * speed + 2.7) * 0.1;
  camera.rotateX(a * amount); camera.rotateY(b * amount);
}
