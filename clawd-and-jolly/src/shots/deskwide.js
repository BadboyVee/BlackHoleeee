// Look-dev: wide view of the whole set
import * as THREE from 'three';
import { buildDesk } from '../desk.js';
import { fovFromFocal } from '../env.js';

export default async function (engine, opts) {
  const { scene, parts } = buildDesk(engine.renderer, opts);
  const camera = new THREE.PerspectiveCamera(fovFromFocal(opts.focal ?? 35), engine.width / engine.height, 0.5, 3000);
  const views = {
    wide: [[-10, 32, 62], [12, 6, -10]],
    bowl: [[22, 16, 22], [33, 6, -6]],
    keys: [[8, 6, 14], [0, 1.5, -4]],
  };
  const [cp, ct] = views[opts.view || 'wide'];
  return {
    scene, camera, duration: 1, samples: 8,
    lens: { fstop: 4, focalLength: opts.focal ?? 35, focus: new THREE.Vector3(...cp).distanceTo(new THREE.Vector3(...ct)) },
    look: { exposure: opts.exposure ?? 2.0, bloomStrength: 0.06 },
    update(t, ctx) {
      parts.setDawn(opts.dawn ?? 0, t);
      parts.jitterScreenLight(ctx.lightJitter);
      parts.jitterDirectional(parts.lights.moon, parts.moonBase, parts.lights.moon.target.position, [ctx.rand(0) * 2 - 1, ctx.rand(1) * 2 - 1], 0.01);
      parts.jitterDirectional(parts.lights.sun, parts.sunBase, parts.lights.sun.target.position, [ctx.rand(0) * 2 - 1, ctx.rand(1) * 2 - 1], 0.008);
      parts.lights.lamp.position.copy(parts.lampBase).add(new THREE.Vector3(ctx.rand(2) - 0.5, ctx.rand(3) - 0.5, 0).multiplyScalar(12));
      camera.position.set(...cp); camera.lookAt(...ct);
    },
  };
}
