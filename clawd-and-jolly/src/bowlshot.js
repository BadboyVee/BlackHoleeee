// Shared builder for every shot filmed in the moss bowl (0:31 - 0:56)
import * as THREE from 'three';
import { buildDesk } from './desk.js';
import { Clawd } from './clawd.js';
import { Jolly } from './jolly.js';
import { VoxelTree } from './tree.js';
import { Motes } from './particles.js';
import { makeStory, BEATS } from './story.js';
import { fovFromFocal } from './env.js';
import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js';
import { CLAWD_ORANGE } from './clawd.js';
import { smoothstep } from './anim.js';

export function dawnAt(t) { return smoothstep(BEATS.climax - 0.2, BEATS.climax + 3.5, t) * 0.9; }

export async function makeBowlShot(engine, opts, { t0, t1, focal = 50, camera: camFn, look: lookOver = {}, samples = 16, withTree = true }) {
  const { scene, parts } = buildDesk(engine.renderer, opts);
  const clawd = new Clawd();
  const jolly = new Jolly({ quality: opts.quality ?? 1 });
  scene.add(clawd.group, jolly.group);
  const story = makeStory(parts);
  let tree = null, motes = null;
  if (withTree && t1 > 39) {
    tree = new VoxelTree({ seed: story.SEED, start: BEATS.grow, quality: opts.quality ?? 1 });
    scene.add(tree.group);
    motes = new Motes();
    scene.add(motes.group);
  }
  // the gift voxel as its own object once it leaves Clawd
  const giftMat = new THREE.MeshPhysicalMaterial({ color: CLAWD_ORANGE, roughness: 0.4, clearcoat: 0.75, clearcoatRoughness: 0.16, emissive: new THREE.Color(1.0, 0.3, 0.07), emissiveIntensity: 0 });
  const gift = new THREE.Mesh(new RoundedBoxGeometry(1, 1, 1, 3, 0.045), giftMat);
  gift.castShadow = true;
  scene.add(gift);
  const giftLight = new THREE.PointLight(new THREE.Color(1.0, 0.4, 0.12), 0, 0, 2);
  scene.add(giftLight);

  const camera = new THREE.PerspectiveCamera(fovFromFocal(focal), engine.width / engine.height, 0.05, 3000);
  const lens = { fstop: 2.8, focalLength: focal, focus: 15 };
  const look = { exposure: 2.3, bloomStrength: 0.09, bloomThreshold: 0.9, vignette: 0.45, grain: 0.02, saturation: 1.12, contrast: 1.08,
    tintShadows: [0.92, 0.97, 1.08], tintHighlights: [1.05, 1.0, 0.95], ...lookOver };
  const base = { ...look };
  const ctxShot = { scene, parts, clawd, jolly, story, tree, motes, camera, lens, look, gift };

  return {
    scene, camera, lens, look, duration: t1 - t0, samples, t0,
    cues: () => [
      ...Object.entries(BEATS).map(([k, v]) => ({ t: v, type: 'beat_' + k })),
      { t: 31.0, type: 'scuttle', dur: 1.5, surface: 'moss', gait: 7 },
      { t: BEATS.turn, type: 'scuttle', dur: 0.9, surface: 'moss', gait: 8 },
      ...(tree ? tree.voxels.map((v) => ({ t: v.t, type: 'tree_vox', y: v.g.y })) : []),
      ...(tree ? tree.blossoms.map((b) => ({ t: b.userData.t, type: 'blossom', r: b.userData.r })) : []),
    ],
    update(tl, ctx) {
      const t = tl + t0;
      const dawn = dawnAt(t);
      const sunElev = 0.08 + 0.17 * smoothstep(BEATS.climax, BEATS.climax + 3.2, t);
      parts.stdUpdate(t, ctx, { dawn, lamp: 16000, sunElev });
      parts.lights.moon.intensity = 4.5 * (1 - dawn);
      parts.lights.glowA.intensity = 420 * (1 - dawn); parts.lights.glowB.intensity = 320 * (1 - dawn);
      const bf = parts.lights.bowlFill;
      bf.intensity = (opts.fill ?? 2600) * (1 - dawn * 0.85);
      bf.castShadow = bf.intensity > 1;
      bf.position.copy(parts.bowlFillBase).add(new THREE.Vector3(ctx.rand(3) - 0.5, ctx.rand(4) - 0.5, 0).multiplyScalar(14));
      story.clawdAt(clawd, t);
      clawd.update();
      story.jollyAt(jolly, t);
      const g = story.giftAt(clawd, t);
      if (g && (!tree || t < 41.1)) {
        gift.visible = true;
        gift.position.copy(g.pos).add(new THREE.Vector3(0, g.size * 0.5, 0));
        gift.rotation.set(0, g.rot, 0);
        gift.scale.setScalar(g.size * 0.994);
        giftMat.emissiveIntensity = g.glow * 0.6;
        giftLight.position.copy(gift.position).add(new THREE.Vector3(0, 0.5, 0.4));
        giftLight.intensity = 3 * g.glow;
      } else { gift.visible = false; giftLight.intensity = 0; }
      if (tree) {
        tree.update(t, { climax: BEATS.climax });
        const mouth = jolly.group.localToWorld(new THREE.Vector3(0, jolly.R * 0.75, jolly.R * 1.1));
        motes.update(t, { centre: story.SEED, height: tree.height, mouth, seed: story.SEED, climax: BEATS.climax, dawn });
      }
      Object.assign(look, base);
      look.exposure = base.exposure * (1 - 0.48 * dawn / 0.9);
      camFn(t, ctx, ctxShot);
      camera.fov = fovFromFocal(lens.focalLength); camera.updateProjectionMatrix();
    },
  };
}
