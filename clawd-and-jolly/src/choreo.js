// Character choreography helpers shared by shots
import * as THREE from 'three';
import { clamp01, smoothstep, spring, springSin } from './anim.js';

// hops: [{t0, t1, from: Vector3, to: Vector3, h, spin?}] sorted by time. Returns world position and
// writes squash/stretch, arms and legs into the Clawd pose.
export function clawdHops(t, hops, pose, rest) {
  let pos = rest ? rest.clone() : hops[0].from.clone();
  let yaw = 0;
  let squash = 0, armUp = 0, legTuck = 0;
  for (const h of hops) {
    const dur = h.t1 - h.t0;
    if (t >= h.t0 - 0.16 && t < h.t0) { // anticipation
      pos = h.from.clone();
      squash += 0.22 * smoothstep(h.t0 - 0.16, h.t0 - 0.02, t);
      armUp += 0.3 * smoothstep(h.t0 - 0.16, h.t0, t);
    } else if (t >= h.t0 && t < h.t1) {
      const k = (t - h.t0) / dur;
      pos = new THREE.Vector3().lerpVectors(h.from, h.to, k);
      pos.y += 4 * h.h * k * (1 - k);
      squash += -0.2 * Math.sin(Math.PI * Math.min(1, k * 1.6)) * (k < 0.6 ? 1 : 0.4);
      armUp += 0.6 + 0.3 * Math.sin(k * Math.PI);
      legTuck += Math.sin(k * Math.PI);
      if (h.spin) yaw += h.spin * smoothstep(0.05, 0.95, k);
    } else if (t >= h.t1) {
      pos = h.to.clone();
      squash += spring(t, h.t1, 0.28 * (h.impact ?? 1), 3.4, 7.5);
      armUp += springSin(t, h.t1, 0.5, 2.6, 5) + 0.6 * Math.exp(-(t - h.t1) * 9);
      if (h.spin) yaw += h.spin;
    }
  }
  pose.squash += squash;
  pose.armL += armUp; pose.armR += armUp;
  pose.legLift = pose.legLift.map((v, i) => v + legTuck * (0.5 + 0.3 * (i % 2)));
  return { pos, yaw };
}

// scuttle: crab walk along a path with a gait; returns position and sets legs
export function clawdWalk(t, t0, t1, path, pose, { gait = 9, bob = 0.05 } = {}) {
  const k = clamp01((t - t0) / (t1 - t0));
  const kk = k * k * (3 - 2 * k);
  const p = path.getPointAt ? path.getPointAt(kk) : path(kk);
  const moving = t > t0 && t < t1 ? Math.min(1, Math.min(t - t0, t1 - t) * 6) : 0;
  pose.legLift = pose.legLift.map((v, i) => v + moving * Math.max(0, Math.sin(t * gait * Math.PI + (i % 4) * Math.PI / 2 + (i >= 4 ? Math.PI : 0))) * 0.9);
  p.y += moving * Math.abs(Math.sin(t * gait * Math.PI)) * bob;
  pose.squash += moving * Math.sin(t * gait * Math.PI * 2) * 0.02;
  return p;
}

// keyboard: press keys under a footprint and leave a glowing ripple behind
export function keyImpacts(t, parts, impacts, { footW = 2.3, footD = 0.75 } = {}) {
  const K = parts.keys;
  K.press.fill(0); K.glow.fill(0);
  for (const im of impacts) {
    if (t < im.t) continue;
    const dt = t - im.t;
    K.defs.forEach((d, i) => {
      const dx = Math.abs(d.x - im.x), dz = Math.abs(d.z - im.z);
      const under = dx < footW + d.w / 2 - 0.4 && dz < footD + d.d / 2 - 0.3;
      if (under && (im.until === undefined || t < im.until)) K.press[i] = Math.max(K.press[i], 1);
      const dist = Math.hypot(d.x - im.x, (d.z - im.z) * 1.2);
      const front = dt * (im.speed ?? 14);
      const ring = Math.exp(-Math.pow((dist - front) / 2.2, 2)) * Math.exp(-dt * 1.4) * (im.ripple ?? 0.6);
      const own = under ? Math.exp(-dt * (im.decay ?? 0.9)) : 0;
      K.glow[i] = Math.max(K.glow[i], own * (im.strength ?? 1), ring);
    });
  }
  parts.updateKeys();
}
