// 0:25.0 - 0:31.0  Clawd lands on the desk, scuttles to the moss bowl, hops in and finds a
// sleeping plush creature in the moss.
import * as THREE from 'three';
import { buildDesk, BOWL } from '../desk.js';
import { Clawd } from '../clawd.js';
import { Jolly } from '../jolly.js';
import { fovFromFocal } from '../env.js';
import { smoothstep, clamp01, handheld, springSin, spring, Rail } from '../anim.js';
import { clawdHops, clawdWalk } from '../choreo.js';
import { JOLLY_SPOT, JOLLY_YAW, sleepingJolly } from '../cast.js';

export const T0 = 25.0;
const V = (x, y, z) => new THREE.Vector3(x, y, z);

export default async function (engine, opts = {}) {
  const { scene, parts } = buildDesk(engine.renderer, opts);
  const clawd = new Clawd();
  scene.add(clawd.group);
  const jolly = new Jolly({ quality: opts.quality ?? 1 });
  scene.add(jolly.group);
  const jy = parts.mossHeight(JOLLY_SPOT.x, JOLLY_SPOT.z) - 0.25;
  jolly.group.position.set(JOLLY_SPOT.x, jy, JOLLY_SPOT.z);
  jolly.group.rotation.y = JOLLY_YAW;

  const LAND = V(18.6, 0, 0.6);
  const W1 = V(23.0, 0, -2.4);
  const IN = V(26.4, 0, -3.4); IN.y = parts.mossHeight(IN.x, IN.z) - 0.05;
  const walk = new THREE.CatmullRomCurve3([LAND, V(20.4, 0, -0.2), V(22.0, 0, -1.6), W1]);
  const jump = { t0: 25.06 - 0.6, t1: 25.06, from: V(13.2, 1.42, -1.4), to: LAND, h: 2.4, impact: 1.3 };
  const hopIn = { t0: 28.75, t1: 29.3, from: W1, to: IN, h: 3.2, impact: 1.0 };

  const camera = new THREE.PerspectiveCamera(fovFromFocal(35), engine.width / engine.height, 0.05, 3000);
  const lens = { fstop: 2.8, focalLength: 35, focus: 10 };
  const look = { exposure: 2.3, bloomStrength: 0.08, bloomThreshold: 0.9, vignette: 0.45, grain: 0.02, saturation: 1.12, contrast: 1.08,
    tintShadows: [0.92, 0.97, 1.08], tintHighlights: [1.05, 1.0, 0.95] };
  const rail = new Rail([
    { t: 25.0, pos: [12.5, 1.1, 8.0], target: [18.6, 0.8, 0.6] },
    { t: 27.6, pos: [15.5, 1.6, 7.5], target: [22.0, 1.2, -2.0] },
    { t: 29.3, pos: [19.0, 6.5, 3.5], target: [26.5, 5.6, -3.4] },
    { t: 31.0, pos: [21.8, 8.6, 0.6], target: [33.5, 6.4, -4.6] },
  ]);

  return {
    scene, camera, lens, look, duration: 6.0, samples: 16,
    cues: () => [
      { t: 25.06, type: 'land_wood' }, { t: 25.45, type: 'shake', dur: 0.45 },
      { t: 26.0, type: 'scuttle', dur: 2.6, surface: 'wood', gait: 7 },
      { t: 28.75, type: 'hop' }, { t: 29.3, type: 'land_moss' }, { t: 29.7, type: 'notice' },
    ],
    update(tl, ctx) {
      const t = tl + T0;
      parts.stdUpdate(t, ctx);
      const pose = clawd.pose;
      Object.assign(pose, Clawd.defaultPose());
      let pos;
      if (t < 26.0) {
        pos = clawdHops(t, [jump], pose).pos;
        // shake it off
        const sh = smoothstep(25.45, 25.55, t) * (1 - smoothstep(25.85, 26.0, t));
        pose.wobble = (i, v) => new THREE.Vector3(Math.sin(t * 70 + v.x) * 0.06 * sh, 0, 0);
      } else if (t < 28.75) {
        pos = clawdWalk(t, 26.0, 28.6, walk, pose, { gait: 7 });
        clawdHops(t, [hopIn], pose);
      } else {
        pos = clawdHops(t, [hopIn], pose).pos;
      }
      pose.blink = Math.max(smoothstep(25.7, 25.75, t) * (1 - smoothstep(25.8, 25.87, t)), smoothstep(29.95, 30.0, t) * (1 - smoothstep(30.05, 30.12, t)));
      // freeze and lean in when he notices the sleeper
      const notice = smoothstep(29.6, 30.0, t);
      pose.lean += 0.18 * notice;
      pose.squash += 0.05 * notice;
      clawd.group.position.copy(pos);
      const yawWalk = t < 26.0 ? -0.2 + 0.6 * smoothstep(25.6, 25.8, t) - 0.9 * smoothstep(25.8, 26.0, t) : 0.85;
      const yawIn = 1.35;
      clawd.group.rotation.set(0, t < 28.6 ? (t < 26.0 ? yawWalk : 0.75) : THREE.MathUtils.lerp(0.75, yawIn, smoothstep(28.6, 29.4, t)), 0);
      clawd.update();

      jolly.pose.time = t;
      sleepingJolly(jolly, t, 1);
      jolly.group.updateMatrixWorld(true);
      jolly.update();

      const tg = rail.apply(camera, t);
      // follow Clawd early on
      if (t < 29.3) camera.lookAt(tg.lerp(pos.clone().add(V(0, 0.7, 0)), 0.6));
      handheld(camera, t, 0.003, 0.8);
      const fC = camera.position.distanceTo(pos), fJ = camera.position.distanceTo(jolly.group.position);
      lens.focus = THREE.MathUtils.lerp(fC, fJ, smoothstep(29.9, 30.7, t));
      camera.fov = fovFromFocal(lens.focalLength); camera.updateProjectionMatrix();
    },
  };
}
