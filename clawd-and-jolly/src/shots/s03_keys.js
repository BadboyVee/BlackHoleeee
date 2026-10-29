// 0:17.4 - 0:25.0  Clawd lands on the keyboard and hops across it; every landing presses the
// keys and leaves an orange backlight ripple. He peers over the edge and jumps.
import * as THREE from 'three';
import { buildDesk } from '../desk.js';
import { Clawd } from '../clawd.js';
import { fovFromFocal } from '../env.js';
import { Rail, smoothstep, clamp01, handheld, springSin } from '../anim.js';
import { clawdHops, keyImpacts } from '../choreo.js';

export const T0 = 17.4;
const V = (x, y, z) => new THREE.Vector3(x, y, z);

export default async function (engine, opts = {}) {
  const { scene, parts } = buildDesk(engine.renderer, opts);
  parts.mossFur.castShadow = false;
  const clawd = new Clawd();
  scene.add(clawd.group);
  const ky = parts.keys.top;
  // hop plan (film time)
  const P = [V(-6.5, ky, -4.2), V(-3.6, ky, -4.1), V(-0.8, ky, -3.8), V(2.0, ky, -3.2), V(5.2, ky, -2.6), V(8.0, ky, -2.2), V(10.8, ky, -1.9), V(13.2, 1.42, -1.4)];
  const times = [[18.25, 18.70], [19.00, 19.45], [19.76, 20.21], [20.52, 21.12], [21.65, 22.10], [22.42, 22.87], [23.18, 23.62]];
  const hops = times.map(([a, b], i) => ({ t0: a, t1: b, from: P[i], to: P[i + 1], h: i === 3 ? 2.6 : 1.3 + (i % 2) * 0.3, spin: i === 3 ? Math.PI * 2 : 0 }));
  const JUMP = { t0: 24.45, t1: 25.06, from: P[7], to: V(18.6, 0, 0.6), h: 2.4 };
  hops.push(JUMP);
  const impacts = [{ t: 17.4, x: P[0].x, z: P[0].z, strength: 1.4, ripple: 1.0, until: hops[0].t0, speed: 16 }];
  hops.slice(0, 6).forEach((h, i) => impacts.push({ t: h.t1, x: h.to.x, z: h.to.z, strength: 1.0, ripple: 0.55, until: hops[i + 1].t0 }));
  hops[0].impact = 1;

  // orange spill from the last two key impacts
  const spill = [0, 1].map(() => { const l = new THREE.PointLight(new THREE.Color(1.0, 0.35, 0.08), 0, 0, 2); scene.add(l); return l; });
  const camera = new THREE.PerspectiveCamera(fovFromFocal(50), engine.width / engine.height, 0.05, 3000);
  const lens = { fstop: 2.8, focalLength: 50, focus: 10 };
  const look = { exposure: 2.3, bloomStrength: 0.08, bloomThreshold: 0.9, vignette: 0.45, grain: 0.02, saturation: 1.12, contrast: 1.08,
    tintShadows: [0.92, 0.97, 1.08], tintHighlights: [1.05, 1.0, 0.95] };

  return {
    scene, camera, lens, look, duration: 25.0 - T0, samples: 16,
    cues: () => [
      { t: 17.4, type: 'land_keys', big: true, x: P[0].x },
      ...hops.slice(0, 7).map((h) => ({ t: h.t0, type: 'hop', x: h.from.x })),
      ...hops.slice(0, 6).map((h) => ({ t: h.t1, type: 'land_keys', x: h.to.x })),
      { t: hops[6].t1, type: 'land_alu', x: hops[6].to.x },
      { t: 23.8, type: 'peek' }, { t: JUMP.t0, type: 'jump', x: JUMP.from.x }, { t: 20.52, type: 'spin' },
    ],
    update(tl, ctx) {
      const t = tl + T0;
      parts.setDawn(0, t);
      parts.jitterScreenLight(ctx.lightJitter);
      parts.jitterDirectional(parts.lights.moon, parts.moonBase, parts.lights.moon.target.position, [ctx.rand(0) * 2 - 1, ctx.rand(1) * 2 - 1], 0.01);
      parts.lights.sun.castShadow = false;
      parts.lights.lamp.castShadow = false;
      parts.lights.lamp.position.copy(parts.lampBase).add(new THREE.Vector3(ctx.rand(2) - 0.5, ctx.rand(3) - 0.5, 0).multiplyScalar(25));
      parts.lights.lamp.intensity = 30000;
      const blink = 0.5 + 0.5 * Math.cos((t % 1.06) / 1.06 * Math.PI * 2);
      parts.drawScreen({ cursor: smoothstep(0.35, 0.65, blink), maskKey: 'all', spriteMask: () => false });
      parts.screenMat.userData.uniforms.uBright.value = 2.2;

      // Clawd
      const pose = clawd.pose;
      Object.assign(pose, Clawd.defaultPose());
      // landing from the drop at 17.4
      pose.squash += 0.0;
      const first = { t0: 17.05, t1: 17.4, from: V(-6.5, 7.6, -4.2), to: P[0], h: 0, impact: 1.5 };
      const { pos, yaw } = clawdHops(t, [first, ...hops], pose);
      // peer over the edge
      const peek = smoothstep(23.75, 24.0, t) * (1 - smoothstep(24.25, 24.4, t));
      pose.lean = 0.35 * peek;
      pose.legLift = pose.legLift.map((v, i) => v + peek * 0.25 * Math.max(0, Math.sin(t * 30 + i * 1.7)));
      pose.blink = Math.max(smoothstep(19.9, 19.95, t) * (1 - smoothstep(20.0, 20.07, t)), smoothstep(23.66, 23.7, t) * (1 - smoothstep(23.75, 23.82, t)));
      clawd.group.position.copy(pos);
      clawd.group.rotation.set(0, -0.25 + yaw - 0.5 * smoothstep(23.6, 23.9, t) + 0.5 * smoothstep(24.3, 24.45, t), 0);
      clawd.update();
      keyImpacts(t, parts, impacts);
      const past = impacts.filter((im) => im.t <= t).slice(-2);
      spill.forEach((l, i) => {
        const im = past[past.length - 1 - i];
        if (!im) { l.intensity = 0; return; }
        l.position.set(im.x, parts.keys.top + 0.15, im.z + 0.3);
        l.intensity = 9 * Math.exp(-(t - im.t) * 1.2) * (i ? 0.6 : 1);
      });

      // camera: low tracking dolly, then swing to the edge
      const cx = pos.x;
      const trackPos = V(Math.max(-11.5, cx - 6.0), 2.5 + Math.max(0, pos.y - ky) * 0.35, 4.2);
      const trackTgt = V(cx + 1.2, ky + 0.8 + Math.max(0, pos.y - ky) * 0.6, pos.z);
      const edgePos = V(23.5, 4.6, 11.5), edgeTgt = V(14.4, 1.6, -1.2);
      const w = smoothstep(22.9, 23.9, t);
      // after the jump, follow him down
      const fall = smoothstep(24.45, 25.0, t);
      camera.position.copy(trackPos).lerp(edgePos, w);
      const tg = trackTgt.clone().lerp(edgeTgt, w).lerp(pos.clone().add(V(0, 0.6, 0)), fall * 0.8);
      camera.lookAt(tg);
      handheld(camera, t, 0.003, 0.8);
      lens.focus = camera.position.distanceTo(pos.clone().add(V(0, 0.6, 0)));
      camera.fov = fovFromFocal(lens.focalLength); camera.updateProjectionMatrix();
    },
  };
}
