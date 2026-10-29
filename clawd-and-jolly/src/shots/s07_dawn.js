// 0:50.0 - 0:56.0  Sunrise. a: the first sunlight sweeps across their faces as the blossoms
// burst. b: silhouettes against the sunrise, Jolly leans on Clawd, fluff drifts in the rays.
import * as THREE from 'three';
import { makeBowlShot } from '../bowlshot.js';
import { handheld, smoothstep, Rail } from '../anim.js';

export const SETUPS = { a: { t0: 50.4, t1: 53.0, focal: 24, quality: 0.6, mossStrands: 90000 }, b: { t0: 53.0, t1: 56.0, focal: 28 } };

export default async function (engine, opts = {}) {
  const which = opts.setup || 'a';
  let rail = null;
  return makeBowlShot(engine, opts, {
    ...SETUPS[which], withTree: true,
    look: { tintShadows: [0.95, 0.97, 1.05], tintHighlights: [1.08, 1.0, 0.9] },
    camera(t, ctx, { camera, lens, jolly, clawd, story, look, parts }) {
      const c = story.SEAT_C.clone().lerp(story.SEAT_J, 0.5);
      if (!rail) {
        rail = which === 'a'
          ? new Rail([
            { t: 50.4, pos: [c.x + 6.5, c.y + 9.0, c.z + 22.0], target: [c.x - 1.0, c.y + 9.5, c.z - 30.0] },
            { t: 53.0, pos: [c.x + 5.0, c.y + 7.5, c.z + 18.0], target: [c.x - 1.0, c.y + 8.5, c.z - 30.0] },
          ])
          : new Rail([
            { t: 53.0, pos: [c.x + 1.8, c.y + 3.6, c.z + 9.0], target: [c.x - 0.4, c.y + 4.0, c.z - 30.0] },
            { t: 56.0, pos: [c.x + 1.2, c.y + 3.0, c.z + 7.0], target: [c.x - 0.3, c.y + 3.8, c.z - 30.0] },
          ]);
      }
      rail.apply(camera, t);
      lens.fstop = which === 'a' ? 5.6 : 4.0;
      lens.focus = camera.position.distanceTo(c);
      handheld(camera, t, 0.002, 0.6);
      camera.updateMatrixWorld(true);
      const sp = camera.position.clone().addScaledVector(parts.sunDir, 500).project(camera);
      look.sunUV = [sp.x * 0.5 + 0.5, sp.y * 0.5 + 0.5];
      look.godRays = sp.z < 1 ? (opts.rays ?? 0.6) * smoothstep(50.7, 51.9, t) : 0;
      look.godThreshold = 60.0;
      if (which === 'b') look.exposure *= 0.62;
    },
  });
}
