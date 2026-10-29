// 0:00 - 0:17.4  One take: a blinking cursor at subpixel macro, a glide up the session to the
// welcome box, then the Clawd sprite's pixels pop out of the display as voxels and assemble
// into Clawd hovering in front of the screen. Ends as he drops toward the keys.
import * as THREE from 'three';
import { buildDesk } from '../desk.js';
import { Clawd } from '../clawd.js';
import { fovFromFocal } from '../env.js';
import { spritePixelUI, CURSOR_UI, SPRITE_POS, UI_W, UI_H } from '../screen-ui.js';
import { Rail, rng, clamp01, smoothstep, easeInOutCubic, easeOutCubic, bezier3, spring, springSin, handheld } from '../anim.js';

export const CUES = { stab1: 7.87, stab2: 12.61, drop: 17.05, land: 17.4 };

export default async function (engine, opts = {}) {
  const { scene, parts } = buildDesk(engine.renderer, opts);
  parts.mossFur.castShadow = false;
  const clawd = new Clawd();
  scene.add(clawd.group);
  parts.enableScreenReflection(engine.width >> 1, engine.height >> 1, 1.0);
  clawd.group.traverse((o) => o.layers.enable(1));
  const HOVER = new THREE.Vector3(-6.5, 7.6, -4.2);
  clawd.group.position.copy(HOVER);
  const s = clawd.s;

  // glow light carried by Clawd while his voxels are hot
  const glowLight = new THREE.PointLight(new THREE.Color(1.0, 0.45, 0.2), 0, 0, 2);
  scene.add(glowLight);
  glowLight.layers.enable(1);

  // dust motes in the screen light
  const R = rng(17);
  const nDust = 150;
  const dust = new THREE.InstancedMesh(new THREE.SphereGeometry(1, 8, 6), new THREE.MeshBasicMaterial({ color: 0xffffff }), nDust);
  const dustSeed = [];
  for (let i = 0; i < nDust; i++) {
    dustSeed.push({ p: new THREE.Vector3((R() - 0.5) * 30, 2 + R() * 16, -12 + R() * 22), r: 0.004 + R() * 0.01, ph: R() * 6.28, sp: 0.1 + R() * 0.3, b: 0.3 + R() });
    dust.setColorAt(i, new THREE.Color(1, 0.95, 0.9).multiplyScalar(0.45 * dustSeed[i].b));
  }
  scene.add(dust);
  dust.layers.enable(1);
  // dust on the glass itself
  const nGlass = 35;
  const glassDust = new THREE.InstancedMesh(new THREE.SphereGeometry(1, 6, 4), new THREE.MeshBasicMaterial({ color: new THREE.Color(0.6, 0.6, 0.62) }), nGlass);
  const m4 = new THREE.Matrix4();
  for (let i = 0; i < nGlass; i++) {
    const p = parts.uiToWorld(R() * UI_W, R() * UI_H).addScaledVector(parts.screenNormal(), 0.01);
    m4.makeScale(1, 1, 1).setPosition(p); m4.scale(new THREE.Vector3().setScalar(0.003 + R() * 0.006));
    glassDust.setMatrixAt(i, m4);
  }
  scene.add(glassDust);

  // ---- voxel choreography ----
  const N = clawd.count;
  const plan = [];
  const pr = rng(99);
  // launch order: shuffle sprite columns (screen pixels), front layer leads its column
  const pix = new Map();
  clawd.voxels.forEach((v, i) => { const k = v.row + ',' + v.x; if (!pix.has(k)) pix.set(k, []); pix.get(k).push(i); });
  const keys = [...pix.keys()].sort(() => pr() - 0.5);
  const launchStart = CUES.stab1, launchEnd = 10.9;
  keys.forEach((k, j) => {
    const u = j / (keys.length - 1);
    const L = launchStart + (launchEnd - launchStart) * Math.pow(u, 0.75);
    const [row, x] = k.split(',').map(Number);
    for (const i of pix.get(k)) {
      const v = clawd.voxels[i];
      const launch = L + v.z * 0.075;
      const arrive = Math.min(CUES.stab2 - 0.12, launch + 1.5 + pr() * 0.8);
      plan[i] = {
        row, x, launch, arrive,
        swirl: new THREE.Vector3((pr() - 0.5) * 7, 1 + pr() * 4, 2 + pr() * 4),
        axis: new THREE.Vector3(pr() - 0.5, pr() - 0.5, pr() - 0.5).normalize(),
        spin: (1 + Math.floor(pr() * 2)) * Math.PI * 2 * (pr() < 0.5 ? -1 : 1),
      };
    }
  });
  const eyePlan = [0, 1].map((k) => ({ launch: CUES.stab2 - 0.75 - k * 0.1, arrive: CUES.stab2, x: k ? 12 : 5, row: 1 }));
  const launchedPixels = new Set();

  // world position of a sprite pixel on the screen, and of a voxel in assembled Clawd
  const screenPos = (row, x) => { const u = spritePixelUI(row, x); return parts.uiToWorld(u.x, u.y); };
  const nrm = parts.screenNormal();
  const tmp = new THREE.Vector3();
  const inv = new THREE.Matrix4();

  // ---- camera ----
  const camera = new THREE.PerspectiveCamera(fovFromFocal(70), engine.width / engine.height, 0.02, 3000);
  const cur = parts.uiToWorld(CURSOR_UI.x, CURSOR_UI.y);
  const sprC = parts.uiToWorld(SPRITE_POS.x + 9 * SPRITE_POS.px, SPRITE_POS.y + 2.5 * SPRITE_POS.px);
  const right = new THREE.Vector3(1, 0, 0);
  const up = new THREE.Vector3().crossVectors(nrm, right).negate();
  const off = (base, dx, dy, dz) => base.clone().addScaledVector(right, dx).addScaledVector(up, dy).addScaledVector(nrm, dz).toArray();
  const tgt = (base, dx = 0, dy = 0) => base.clone().addScaledVector(right, dx).addScaledVector(up, dy).toArray();
  const rail = new Rail([
    { t: 0.0, pos: off(cur, -1.6, -0.7, 2.6), target: tgt(cur, -0.25, 0), fstop: 16, ease: 'linear' },
    { t: 4.6, pos: off(cur, -0.4, -0.35, 2.4), target: tgt(cur, 0.3, 0.06), fstop: 16, ease: 'in' },
    { t: 7.5, pos: off(sprC, -2.6, -2.4, 7.0), target: tgt(sprC, 0.3, 0), fstop: 11 },
    { t: 9.4, pos: off(sprC, 3.0, 2.2, 9.0), target: tgt(sprC, 0.9, 0.6), fstop: 8 },
    { t: 11.6, pos: [-15.5, 8.5, 12.5], target: [-7.0, 9.0, -6.5], fstop: 5.6 },
    { t: 14.2, pos: [-12.5, 9.6, 9.8], target: HOVER.clone().add(new THREE.Vector3(0, 0.5, 0)).toArray(), fstop: 4 },
    { t: 16.6, pos: [-10.8, 8.2, 8.4], target: HOVER.clone().add(new THREE.Vector3(0, 0.2, 0)).toArray(), fstop: 4 },
    { t: 17.4, pos: [-10.6, 6.8, 8.6], target: [-6.5, 3.4, -4.2], fstop: 4, ease: 'linear' },
  ]);
  let focusTarget = new THREE.Vector3();
  const lens = { fstop: 16, focalLength: 70, focus: 2.5 };

  const look = { fade: 1, exposure: 2.4, bloomStrength: 0.07, bloomThreshold: 0.9, vignette: 0.45, grain: 0.02, saturation: opts.sat ?? 1.12, contrast: opts.con ?? 1.08,
    tintShadows: [0.92, 0.97, 1.08], tintHighlights: [1.05, 1.0, 0.95] };

  return {
    scene, camera, lens, look, duration: CUES.land, samples: 16,
    cues: () => [
      ...plan.map((p, i) => ({ t: p.launch, type: 'vox_launch', z: clawd.voxels[i].z, x: p.x })),
      ...plan.map((p, i) => ({ t: p.arrive, type: 'vox_arrive', z: clawd.voxels[i].z, x: p.x })),
      ...eyePlan.map((e) => ({ t: e.arrive, type: 'eye_arrive' })),
      { t: CUES.stab1, type: 'stab1' }, { t: CUES.stab2, type: 'stab2' },
      { t: 13.58, type: 'blink' }, { t: 15.18, type: 'blink' }, { t: CUES.drop, type: 'drop' },
      ...Array.from({ length: 8 }, (_, k) => ({ t: k * 1.06, type: 'cursor_on' })),
    ],
    update(t, ctx) {
      // lights
      look.fade = smoothstep(0.0, 1.6, t);
      parts.setDawn(0, t);
      parts.jitterScreenLight(ctx.lightJitter);
      parts.jitterDirectional(parts.lights.moon, parts.moonBase, parts.lights.moon.target.position, [ctx.rand(0) * 2 - 1, ctx.rand(1) * 2 - 1], 0.01);
      parts.lights.lamp.castShadow = false; parts.lights.sun.castShadow = false;
      parts.lights.lamp.position.copy(parts.lampBase).add(new THREE.Vector3(ctx.rand(2) - 0.5, ctx.rand(3) - 0.5, 0).multiplyScalar(25));
      parts.lights.lamp.intensity = 30000;

      // screen: cursor blink, sprite pulse before launch, pixels removed as they leave
      const blink = 0.5 + 0.5 * Math.cos((t % 1.06) / 1.06 * Math.PI * 2);
      const cursor = smoothstep(0.35, 0.65, blink);
      launchedPixels.clear();
      for (let i = 0; i < N; i++) if (t >= plan[i].launch && clawd.voxels[i].z === 0) launchedPixels.add(plan[i].row + ',' + plan[i].x);
      for (let i = 0; i < N; i++) if (t >= plan[i].launch) launchedPixels.add(plan[i].row + ',' + plan[i].x);
      const maskKey = [...launchedPixels].sort().join('|');
      parts.drawScreen({ cursor, maskKey, spriteMask: (r, c) => !launchedPixels.has(r + ',' + c), typed: 0 });
      const pulse = smoothstep(6.6, 8.0, t) * (1 - smoothstep(10.5, 12.5, t));
      parts.screenMat.userData.uniforms.uBright.value = 2.2 + pulse * 1.0;

      // Clawd
      const P = clawd.pose;
      Object.assign(P, Clawd.defaultPose());
      const tAfter = t - CUES.stab2;
      // hover, glances, blinks, the drop
      let gy = HOVER.y + Math.sin(Math.max(0, tAfter) * 2.4) * 0.12 * smoothstep(0, 0.6, tAfter);
      let dropK = 0;
      if (t > CUES.drop) { dropK = clamp01((t - CUES.drop) / (CUES.land - CUES.drop)); gy = gy - (gy - (parts.keys.top)) * dropK * dropK; }
      clawd.group.position.set(HOVER.x, gy, HOVER.z);
      clawd.group.rotation.set(0, 0.35 * smoothstep(13.8, 14.3, t) * (1 - smoothstep(14.9, 15.4, t)) - 0.25 * smoothstep(15.4, 15.9, t) * (1 - smoothstep(16.2, 16.6, t)), 0);
      P.squash = spring(t, CUES.stab2, 0.14, 3.2, 5) + 0.12 * smoothstep(16.65, 16.95, t) * (1 - smoothstep(16.95, 17.1, t)) - 0.18 * smoothstep(17.05, 17.25, t);
      P.blink = Math.max(smoothstep(13.55, 13.62, t) * (1 - smoothstep(13.68, 13.78, t)), smoothstep(15.15, 15.22, t) * (1 - smoothstep(15.28, 15.38, t)));
      if (t < CUES.stab2 + 0.02) P.blink = 0;
      P.armL = 0.5 * smoothstep(17.0, 17.3, t) + springSin(t, CUES.stab2, 0.5, 2.5, 4);
      P.armR = 0.5 * smoothstep(17.0, 17.3, t) + springSin(t, CUES.stab2 + 0.05, 0.5, 2.5, 4);
      P.legLift = P.legLift.map((_, k) => 0.35 * smoothstep(16.9, 17.2, t) * (k % 2 ? 1 : 0.6) + 0.2 * Math.max(0, Math.sin(t * 9 + k)) * smoothstep(14.2, 14.5, t) * (1 - smoothstep(15.6, 16.0, t)));
      const hot = 1 - smoothstep(CUES.stab2 + 0.2, CUES.stab2 + 2.6, t);
      clawd.group.updateMatrixWorld(true);
      inv.copy(clawd.group.matrixWorld).invert();
      P.voxelFn = (i, v, out) => {
        if (i < 0) {
          const e = eyePlan[-1 - i];
          if (t < e.launch) { out.visible = false; return; }
          const k = clamp01((t - e.launch) / (e.arrive - e.launch));
          const from = screenPos(e.row, e.x).applyMatrix4(inv).multiplyScalar(1 / s);
          const to = out.pos.clone();
          const kk = easeInOutCubic(k);
          bezier3(from, from.clone().addScaledVector(nrm.clone().transformDirection(inv), 2.5 / s), to.clone().add(new THREE.Vector3(0, 0, 4)), to, kk, out.pos);
          out.scale = 0.75 + 0.25 * kk;
          return;
        }
        const p = plan[i];
        if (t < p.launch) { out.visible = false; out.scale = 0; return; }
        const final = out.pos.clone();
        const k = clamp01((t - p.launch) / (p.arrive - p.launch));
        const from = screenPos(p.row, p.x).applyMatrix4(inv).multiplyScalar(1 / s);
        const nLocal = nrm.clone().transformDirection(inv);
        const kk = easeInOutCubic(k);
        bezier3(from, from.clone().addScaledVector(nLocal, 3.0 / s), final.clone().add(p.swirl.clone().multiplyScalar(1 / s * 0.6)), final, kk, out.pos);
        // pop out of the glass with a little overshoot
        const pop = easeOutCubic(clamp01((t - p.launch) / 0.18));
        out.scale = (0.6 + 0.4 * kk) * pop;
        const spin = (1 - kk) * p.spin;
        out.quat.multiply(new THREE.Quaternion().setFromAxisAngle(p.axis, spin));
        // settle wobble after arrival
        if (t > p.arrive) out.pos.addScaledVector(nLocal, springSin(t, p.arrive, 0.25, 5, 9));
        out.glow = (k < 1 ? 2.4 * (1 - kk) + 0.55 : 0.55) * hot;
      };
      clawd.update();
      glowLight.position.copy(clawd.group.position).add(new THREE.Vector3(0, -1.2, 1.6));
      glowLight.intensity = 5 * hot * smoothstep(CUES.stab1, CUES.stab1 + 1.5, t);

      // dust
      for (let i = 0; i < nDust; i++) {
        const d = dustSeed[i];
        tmp.copy(d.p).add(new THREE.Vector3(Math.sin(t * d.sp + d.ph) * 0.6, Math.sin(t * d.sp * 0.7 + d.ph * 2) * 0.4 + t * 0.05, Math.cos(t * d.sp * 0.8 + d.ph) * 0.5));
        m4.makeScale(d.r, d.r, d.r).setPosition(tmp);
        dust.setMatrixAt(i, m4);
      }
      dust.instanceMatrix.needsUpdate = true;

      // camera
      let tg = rail.apply(camera, t);
      if (t > 11.0) {
        const cpos = new THREE.Vector3(HOVER.x, gy + 0.55, HOVER.z);
        const w = smoothstep(11.0, 13.0, t);
        tg = tg.clone().lerp(cpos, w);
        camera.lookAt(tg);
      }
      handheld(camera, t, 0.0015 * smoothstep(8, 11, t), 0.7);
      lens.fstop = rail.scalar('fstop', t, 8);
      // focus: on the screen point early on, then on Clawd
      const focusPt = new THREE.Vector3(HOVER.x, gy + 0.6, HOVER.z);
      focusTarget.copy(t < 9.6 ? tg : tg.clone().lerp(focusPt, smoothstep(9.6, 11.6, t)));
      lens.focus = camera.position.distanceTo(focusTarget);
      camera.fov = fovFromFocal(lens.focalLength); camera.updateProjectionMatrix();
    },
  };
}
