// Choreography for 0:31 - 1:00, as pure functions of film time, shared by every camera that
// films the moss bowl so cuts stay continuous.
import * as THREE from 'three';
import { Clawd } from './clawd.js';
import { Jolly } from './jolly.js';
import { BOWL } from './desk.js';
import { smoothstep, clamp01, spring, springSin, rng, easeOutBack, easeInOutCubic, bezier3 } from './anim.js';
import { clawdHops, clawdWalk } from './choreo.js';
import { JOLLY_SPOT, JOLLY_YAW, PLANT_SPOT, sleepingJolly } from './cast.js';

const V = (x, y, z) => new THREE.Vector3(x, y, z);
const win = (t, a, b, c, d) => smoothstep(a, b, t) * (1 - smoothstep(c, d, t));

export const BEATS = {
  wake: 32.9, startle: 33.15, burst: 33.25, wave: 34.7, waveBack: 35.6, boop: 37.2,
  gift: 37.6, place: 39.5, puff: 39.9, grow: 41.0, bloom: 45.4, climax: 50.4, turn: 50.8, lean: 53.6, happy: 54.3,
};

export function makeStory(parts) {
  const h = (x, z) => parts.mossHeight(x, z);
  const IN = V(26.4, 0, -3.4); IN.y = h(IN.x, IN.z) - 0.05;
  const MEET = V(BOWL.x - 3.0, 0, BOWL.z + 1.5); MEET.y = h(MEET.x, MEET.z) - 0.05;
  const JPOS = JOLLY_SPOT.clone(); JPOS.y = h(JPOS.x, JPOS.z) - 0.25;
  const JNEAR = V(BOWL.x + 1.3, 0, BOWL.z + 1.4); JNEAR.y = h(JNEAR.x, JNEAR.z) - 0.25;
  const SEED = PLANT_SPOT.clone(); SEED.y = h(SEED.x, SEED.z);
  // final seats for the sunrise, side by side facing the window
  const SEAT_C = V(BOWL.x - 2.4, 0, BOWL.z + 2.4); SEAT_C.y = h(SEAT_C.x, SEAT_C.z) - 0.05;
  const SEAT_J = V(BOWL.x + 1.25, 0, BOWL.z + 2.2); SEAT_J.y = h(SEAT_J.x, SEAT_J.z) - 0.25;
  const walkIn = new THREE.CatmullRomCurve3([IN, V(28.5, 0, -3.6), V(30.2, 0, -4.2), MEET].map((p) => { p.y = h(p.x, p.z) - 0.05; return p; }));
  const r = rng(4242);
  const burstDirs = Array.from({ length: 300 }, () => V(r() - 0.5, r() - 0.5, r() - 0.5));

  function clawdAt(clawd, t) {
    const P = clawd.pose;
    Object.assign(P, Clawd.defaultPose());
    let pos, yaw;
    if (t < 31.0) { pos = IN.clone(); yaw = 1.35; }
    else if (t < 32.6) { pos = clawdWalk(t, 31.0, 32.5, walkIn, P, { gait: 7 }); yaw = THREE.MathUtils.lerp(1.35, 0.55, smoothstep(31.0, 32.4, t)); }
    else if (t < BEATS.turn) { pos = MEET.clone(); yaw = 0.55; }
    else { pos = clawdWalk(t, BEATS.turn, BEATS.turn + 0.9, (k) => MEET.clone().lerp(SEAT_C, k), P, { gait: 8 }); yaw = THREE.MathUtils.lerp(0.55, Math.PI + 0.25, smoothstep(BEATS.turn, BEATS.turn + 0.9, t)); }
    // curiosity lean, then the startle
    P.lean += 0.16 * win(t, 32.6, 32.9, 33.15, 33.3);
    const b = smoothstep(BEATS.burst, BEATS.burst + 0.06, t) * Math.exp(-Math.max(0, t - BEATS.burst - 0.06) * 5.5);
    P.wobble = (i, v) => burstDirs[i % 300].clone().multiplyScalar(1.4 * b).add(v.base.clone().setY(v.base.y - 2).multiplyScalar(0.22 * b));
    P.squash += spring(t, BEATS.burst + 0.3, 0.12, 3.2, 6);
    // head tilt and blinks
    P.tilt += 0.18 * win(t, 34.0, 34.25, 34.55, 34.8);
    P.blink = Math.max(win(t, 34.12, 34.16, 34.2, 34.26), win(t, 36.3, 36.34, 36.38, 36.45), win(t, 40.6, 40.64, 40.68, 40.75), win(t, 44.0, 44.04, 44.08, 44.15));
    // wave hello (arm on Jolly's side)
    const wv = win(t, BEATS.wave, BEATS.wave + 0.15, BEATS.wave + 0.6, BEATS.wave + 0.75);
    P.armL += wv * (1.0 + 0.45 * Math.sin((t - BEATS.wave) * 18));
    // boop: squash and a little hop back
    P.squash += spring(t, BEATS.boop, 0.22, 3.6, 7);
    // gift: perk up
    P.squash -= 0.12 * win(t, 37.45, 37.55, 37.65, 37.8);
    P.armL += 0.9 * win(t, 37.9, 38.1, 39.3, 39.6);
    // awe while the tree grows: lean back, step back
    P.lean -= 0.22 * win(t, 41.4, 42.4, 49.6, 50.4);
    P.armL += 0.5 * win(t, 46.5, 46.8, 49.6, 50.2) * (1 + 0.3 * Math.sin(t * 12));
    P.armR += 0.5 * win(t, 46.5, 46.8, 49.6, 50.2) * (1 + 0.3 * Math.sin(t * 12 + 1));
    // joy hops at the blooms
    if (t > 46.6 && t < 49.9) pos.y += Math.abs(Math.sin((t - 46.6) * Math.PI / 0.55)) * 0.45;
    P.squash += t > 46.6 && t < 49.9 ? -0.08 * Math.sin((t - 46.6) * Math.PI * 2 / 0.55) : 0;
    const back = smoothstep(41.2, 42.2, t) * (1 - smoothstep(BEATS.turn - 0.4, BEATS.turn, t));
    pos.add(V(-0.6, 0, 0.7).multiplyScalar(back));
    pos.y = Math.max(pos.y, h(pos.x, pos.z) - 0.05);
    // the gift voxel leaves the head (top row, middle) and the hole stays
    const giftIdx = clawd.voxels.findIndex((v) => v.row === 0 && v.x === 8 && v.z === 1);
    const prevFn = P.voxelFn;
    P.voxelFn = (i, v, out) => {
      if (prevFn) prevFn(i, v, out);
      if (i === giftIdx && t >= BEATS.gift) out.visible = false;
    };
    clawd.group.position.copy(pos);
    clawd.group.rotation.set(0, yaw, 0);
    clawd.group.updateMatrixWorld(true);
    return { pos, yaw, giftIdx };
  }

  // the gift voxel in world space (null before it leaves Clawd)
  function giftAt(clawd, t) {
    if (t < BEATS.gift) return null;
    const v = clawd.voxels.find((vv) => vv.row === 0 && vv.x === 8 && vv.z === 1);
    const head = v.base.clone().multiplyScalar(clawd.s).applyMatrix4(clawd.group.matrixWorld);
    const above = head.clone().add(V(0, 1.4, 0.3));
    const seed = SEED.clone().add(V(0, 0.08, 0));
    let p, rot = 0, scale = 1, glow = 0;
    if (t < 38.0) { const k = easeInOutCubic(clamp01((t - BEATS.gift) / 0.4)); p = head.clone().lerp(above, k); rot = k * Math.PI * 2; glow = 1.5 * k; }
    else if (t < 38.6) { p = above.clone().add(V(0, Math.sin((t - 38.0) * 9) * 0.06, 0)); rot = (t - 38.0) * 3; glow = 1.5 + 0.4 * Math.sin(t * 20); }
    else if (t < BEATS.place) {
      const k = easeInOutCubic(clamp01((t - 38.6) / (BEATS.place - 38.6)));
      p = bezier3(above, above.clone().add(V(0.4, 1.2, 0)), seed.clone().add(V(0, 1.6, 0)), seed, k);
      rot = 1.8 + k * Math.PI; glow = 1.5;
    } else {
      p = seed.clone().add(V(0, springSin(t, BEATS.place, -0.06, 4, 8), 0));
      rot = 1.8 + Math.PI;
      glow = 1.5 + 2.5 * win(t, BEATS.puff + 0.6, BEATS.puff + 0.9, BEATS.grow, BEATS.grow + 0.3) + 0.5 * Math.sin(t * 12) * win(t, 40.2, 40.4, 41.0, 41.1);
    }
    return { pos: p, rot, scale, glow, size: clawd.s };
  }

  function jollyAt(jolly, t) {
    const P = jolly.pose;
    Object.assign(P, Jolly.defaultPose());
    P.time = t;
    let pos = JPOS.clone(), yaw = JOLLY_YAW;
    if (t < BEATS.wake) sleepingJolly(jolly, t, 1);
    else {
      const k = 1 - smoothstep(BEATS.wake, BEATS.wake + 0.25, t);
      sleepingJolly(jolly, t, k);
      P.blink = Math.max(k, win(t, 34.3, 34.34, 34.38, 34.45), win(t, 38.9, 38.94, 38.98, 39.05), win(t, 43.1, 43.14, 43.18, 43.25));
    }
    // startle hop
    if (t > BEATS.startle && t < BEATS.startle + 0.42) {
      const k = (t - BEATS.startle) / 0.42;
      pos.y += 4 * 1.3 * k * (1 - k);
      P.squash += -0.25 * Math.sin(Math.PI * Math.min(1, k * 1.5));
      P.force = V(0, -0.22 - 2.2 * Math.cos(Math.PI * k), 0);
      P.armL += 0.8 * Math.sin(Math.PI * k); P.armR += 0.8 * Math.sin(Math.PI * k);
    }
    P.squash += spring(t, BEATS.startle + 0.42, 0.3, 3.0, 6);
    P.force.y += springSin(t, BEATS.startle + 0.42, -1.4, 3, 6);
    yaw += -0.25 * smoothstep(BEATS.startle + 0.2, BEATS.startle + 0.5, t);
    P.tilt += 0.28 * win(t, 33.9, 34.2, 34.9, 35.2);
    // wave back with a blush
    const wv = win(t, BEATS.waveBack, BEATS.waveBack + 0.15, BEATS.waveBack + 0.65, BEATS.waveBack + 0.8);
    P.armR += wv * (1.2 + 0.4 * Math.sin((t - BEATS.waveBack) * 16));
    P.happy = Math.max(win(t, 35.9, 36.05, 36.35, 36.5), win(t, 47.0, 47.2, 49.4, 49.7), smoothstep(BEATS.happy, BEATS.happy + 0.4, t));
    P.cheekGlow = win(t, 35.8, 36.1, 37.6, 38.4) + smoothstep(46.5, 47.5, t);
    // hop closer and boop
    if (t > 36.5) {
      const k = clamp01((t - 36.5) / 0.45);
      pos.lerp(JNEAR, k);
      pos.y += 4 * 0.9 * k * (1 - k);
    }
    P.squash += spring(t, 36.95, 0.2, 3.4, 7);
    P.lean += 0.25 * win(t, 37.0, 37.15, 37.3, 37.6);
    // puff on the seed
    const puff = win(t, BEATS.puff, BEATS.puff + 0.3, BEATS.puff + 0.8, BEATS.puff + 1.0);
    P.lean += 0.22 * puff;
    P.squash += -0.08 * puff;
    P.wind = V(-1.5, 0.3, -0.8).multiplyScalar(puff * 0.6);
    // watching the tree: lean back, bounce at the blooms
    P.lean -= 0.25 * win(t, 41.6, 42.6, 49.6, 50.4);
    P.squash += t > 46.9 && t < 49.6 ? 0.1 * Math.sin((t - 46.9) * Math.PI * 2 / 0.6) : 0;
    // turn to the window and sit with Clawd, then lean on him
    if (t > BEATS.turn) {
      const k = smoothstep(BEATS.turn + 0.2, BEATS.turn + 1.1, t);
      pos.lerp(SEAT_J, k);
      yaw = THREE.MathUtils.lerp(yaw, Math.PI - 0.2, k);
    }
    const lean = smoothstep(BEATS.lean, BEATS.lean + 0.8, t);
    P.tilt += -0.32 * lean;
    pos.x -= 0.25 * lean;
    jolly.group.position.copy(pos);
    jolly.group.rotation.set(0, yaw, 0);
    jolly.group.updateMatrixWorld(true);
    jolly.update();
    return { pos, yaw };
  }

  return { clawdAt, jollyAt, giftAt, SEED, MEET, JPOS, SEAT_C, SEAT_J };
}
