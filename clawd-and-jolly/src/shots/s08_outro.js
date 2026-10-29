// 0:56.0 - 1:00.0  Morning. Back on the laptop: the welcome box now shows both of them as
// pixel sprites side by side. The cursor blinks, and we fade out.
import * as THREE from 'three';
import { buildDesk } from '../desk.js';
import { fovFromFocal } from '../env.js';
import { SPRITE_POS } from '../screen-ui.js';
import { Rail, smoothstep, handheld } from '../anim.js';

export default async function (engine, opts = {}) {
  const { scene, parts } = buildDesk(engine.renderer, opts);
  parts.mossFur.castShadow = false;
  const camera = new THREE.PerspectiveCamera(fovFromFocal(60), engine.width / engine.height, 0.05, 3000);
  const lens = { fstop: 5.6, focalLength: 60, focus: 20 };
  const look = { exposure: 1.5, bloomStrength: 0.08, bloomThreshold: 0.9, vignette: 0.5, grain: 0.02, saturation: 1.12, contrast: 1.08, fade: 1,
    tintShadows: [0.97, 0.97, 1.03], tintHighlights: [1.06, 1.0, 0.92] };
  const nrm = parts.screenNormal();
  const box = parts.uiToWorld(SPRITE_POS.x + 300, SPRITE_POS.y + 40);
  const right = new THREE.Vector3(1, 0, 0);
  const up = new THREE.Vector3().crossVectors(nrm, right).negate();
  const at = (dx, dy, dz) => box.clone().addScaledVector(right, dx).addScaledVector(up, dy).addScaledVector(nrm, dz).toArray();
  const rail = new Rail([
    { t: 56.0, pos: at(5.5, -2.6, 15.5), target: at(1.2, -0.6, 0) },
    { t: 60.0, pos: at(2.6, -1.2, 8.0), target: at(0.2, 0.0, 0) },
  ]);
  return {
    scene, camera, lens, look, duration: 4.0, samples: 16,
    update(tl, ctx) {
      const t = tl + 56.0;
      parts.stdUpdate(t, ctx, { dawn: 0.9, sunElev: 0.25, showJolly: 1, screenBright: 2.0, spriteMask: () => true, maskKey: 'outro' });
      rail.apply(camera, t);
      handheld(camera, t, 0.0015, 0.6);
      lens.focus = camera.position.distanceTo(box);
      look.fade = 1 - smoothstep(58.6, 59.95, t);
      camera.fov = fovFromFocal(lens.focalLength); camera.updateProjectionMatrix();
    },
  };
}
