// 0:31.0 - 0:37.4  The meeting, in three set-ups (a: Jolly wakes and jumps, b: Clawd bursts
// apart and pulls himself together, waves, c: two-shot, Jolly waves back, hops over, boop)
import * as THREE from 'three';
import { makeBowlShot } from '../bowlshot.js';
import { handheld, smoothstep } from '../anim.js';

export const SETUPS = {
  a: { t0: 31.0, t1: 33.6, focal: 85 },
  b: { t0: 33.6, t1: 35.4, focal: 70 },
  c: { t0: 35.4, t1: 37.4, focal: 50 },
};

export default async function (engine, opts = {}) {
  const which = opts.setup || 'a';
  const S = SETUPS[which];
  return makeBowlShot(engine, opts, {
    ...S, withTree: false,
    camera(t, ctx, { camera, lens, jolly, clawd, story }) {
      const J = jolly.group.position, C = clawd.group.position;
      if (which === 'a') {
        const k = smoothstep(31.0, 33.6, t);
        camera.position.set(J.x - 12.5 + 1.8 * k, J.y + 2.6 - 0.4 * k, J.z + 8.6 - 1.2 * k);
        camera.lookAt(J.x, J.y + 1.55 + (J.y - story.JPOS.y) * 0.7, J.z);
        lens.fstop = 2.8;
        lens.focus = camera.position.distanceTo(J) * 0.97;
      } else if (which === 'b') {
        const k = smoothstep(33.6, 35.4, t);
        camera.position.set(C.x + 3.0 - 0.6 * k, C.y + 2.0, C.z + 10.5 - 0.8 * k);
        camera.lookAt(C.x + 0.4, C.y + 0.75, C.z);
        lens.fstop = 2.8;
        lens.focus = camera.position.distanceTo(C);
      } else {
        const mid = C.clone().lerp(J, 0.5);
        const k = smoothstep(35.4, 37.4, t);
        camera.position.set(mid.x - 1.0 + 0.8 * k, mid.y + 3.2, mid.z + 15.5 - 1.5 * k);
        camera.lookAt(mid.x, mid.y + 1.0, mid.z);
        lens.fstop = 4;
        lens.focus = camera.position.distanceTo(mid);
      }
      handheld(camera, t, 0.0025, 0.8);
    },
  });
}
