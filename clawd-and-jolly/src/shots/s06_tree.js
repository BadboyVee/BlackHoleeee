// 0:37.4 - 0:50.0  The gift and the tree. a: Clawd takes a voxel out of his own head and plants
// it, Jolly blows fluff onto it. b: the voxel tree grows and blooms in plush blossoms.
import * as THREE from 'three';
import { makeBowlShot } from '../bowlshot.js';
import { handheld, smoothstep, Rail } from '../anim.js';
import { BEATS } from '../story.js';

export const SETUPS = {
  a: { t0: 37.4, t1: 41.2, focal: 50 },
  b: { t0: 41.2, t1: 50.4, focal: 32, quality: 0.6, mossStrands: 90000 },
};

export default async function (engine, opts = {}) {
  const which = opts.setup || 'a';
  const S = SETUPS[which];
  let rail = null;
  return makeBowlShot(engine, opts, {
    ...S, withTree: true,
    camera(t, ctx, { camera, lens, jolly, clawd, story, tree, look }) {
      const J = jolly.group.position, C = clawd.group.position, SEED = story.SEED;
      if (which === 'a') {
        const mid = C.clone().lerp(J, 0.5).lerp(SEED, 0.35);
        const k = smoothstep(37.4, 41.2, t);
        camera.position.set(mid.x + 0.4, mid.y + 3.2 + 0.6 * k, mid.z + 17.0 - 2.5 * k);
        // follow the gift up and down
        const g = story.giftAt(clawd, t);
        const tg = mid.clone().add(new THREE.Vector3(0, 1.0, 0));
        if (g) tg.lerp(g.pos, 0.12 * smoothstep(37.6, 38.3, t));
        camera.lookAt(tg);
        lens.fstop = 4.5;
        lens.focus = camera.position.distanceTo(mid);
      } else {
        if (!rail) {
          const s = SEED;
          rail = new Rail([
            { t: 41.2, pos: [s.x - 4.0, s.y + 2.0, s.z + 13.0], target: [s.x, s.y + 1.5, s.z] },
            { t: 44.5, pos: [s.x - 10.0, s.y + 6.0, s.z + 15.0], target: [s.x, s.y + 4.5, s.z] },
            { t: 47.5, pos: [s.x - 6.0, s.y + 10.5, s.z + 20.0], target: [s.x, s.y + 7.5, s.z] },
            { t: 50.4, pos: [s.x + 3.0, s.y + 12.0, s.z + 23.5], target: [s.x, s.y + 8.0, s.z] },
          ]);
        }
        rail.apply(camera, t);
        lens.fstop = 4.0;
        lens.focus = camera.position.distanceTo(SEED.clone().add(new THREE.Vector3(0, Math.min(tree.height * 0.5, (t - 41.2) * 1.2), 0)));
        look.exposure = 2.3 - 0.3 * smoothstep(47, 50, t);
      }
      handheld(camera, t, which === 'a' ? 0.0012 : 0.0025, 0.8);
    },
  });
}
