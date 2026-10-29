// Character look-development stage
import * as THREE from 'three';
import { Clawd } from '../clawd.js';
import { Jolly } from '../jolly.js';
import { makeEnvironment, fovFromFocal, softSpot } from '../env.js';

function cyclorama() {
  const prof = [];
  for (let z = 60; z > 0; z -= 5) prof.push([z, 0]);
  for (let i = 0; i <= 16; i++) { const a = (i / 16) * Math.PI / 2; prof.push([-Math.sin(a) * 18, 18 - Math.cos(a) * 18]); }
  prof.push([-18, 80]);
  const pos = [], idx = [];
  const X = 80;
  prof.forEach(([z, y], i) => { pos.push(-X, y, z, X, y, z); if (i < prof.length - 1) { const k = i * 2; idx.push(k, k + 2, k + 1, k + 1, k + 2, k + 3); } });
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3)); g.setIndex(idx); g.computeVertexNormals();
  return g;
}

export default async function (engine, opts) {
  const r = engine.renderer;
  const scene = new THREE.Scene();
  scene.environment = makeEnvironment(r, {
    top: [0.06, 0.06, 0.07], bottom: [0.03, 0.028, 0.025],
    panels: [
      { pos: [-20, 25, 20], size: [25, 25], color: [1, 0.95, 0.9], intensity: 3 },
      { pos: [30, 10, -20], size: [10, 30], color: [0.9, 0.95, 1], intensity: 2 },
    ],
  });
  scene.environmentIntensity = 0.6;
  const cyc = new THREE.Mesh(cyclorama(), new THREE.MeshStandardMaterial({ color: new THREE.Color().setRGB(0.42, 0.40, 0.38), roughness: 0.92, side: THREE.DoubleSide }));
  cyc.position.z = -6; cyc.receiveShadow = true;
  scene.add(cyc);

  const clawd = new Clawd();
  clawd.group.position.set(-3.2, 0, 0);
  clawd.group.rotation.y = 0.35;
  scene.add(clawd.group);
  const jolly = new Jolly({ quality: opts.quality ?? 1 });
  jolly.group.position.set(2.6, 0, 0.3);
  jolly.group.rotation.y = -0.35;
  scene.add(jolly.group);
  if (opts.nofur) jolly.group.traverse((o) => { if (o.userData.furUniforms) o.visible = false; });
  if (opts.nojolly) jolly.group.visible = false;

  const key = new THREE.SpotLight(0xffe8d0, 12000, 0, 0.5, 0.6, 2);
  const keyBase = new THREE.Vector3(-18, 26, 22);
  key.position.copy(keyBase); key.target.position.set(0, 1.5, 0);
  key.castShadow = true; key.shadow.mapSize.set(2048, 2048); key.shadow.bias = -0.0002; key.shadow.normalBias = 0.01;
  key.shadow.camera.near = 10; key.shadow.camera.far = 80;
  scene.add(key, key.target);
  const rim = new THREE.SpotLight(0xd8e6ff, 5000, 0, 0.45, 0.7, 2);
  const rimBase = new THREE.Vector3(16, 14, -18);
  rim.position.copy(rimBase); rim.target.position.set(0, 2, 0);
  rim.castShadow = true; rim.shadow.mapSize.set(1024, 1024); rim.shadow.bias = -0.0002;
  scene.add(rim, rim.target);
  if (opts.noshadow) { key.castShadow = false; rim.castShadow = false; }
  scene.add(new THREE.HemisphereLight(0xe8ecff, 0x2a2420, 0.6));

  const camera = new THREE.PerspectiveCamera(fovFromFocal(opts.focal ?? 70), engine.width / engine.height, 0.5, 400);
  const view = opts.view ?? 0;
  const views = [[0, 4.5, 30, 0, 1.6, 0], [-3.2, 2.0, 9, -3.2, 0.8, 0], [2.6, 2.6, 11, 2.6, 1.6, 0]];
  const [cx, cy, cz, tx, ty, tz] = views[view];
  return {
    scene, camera, duration: opts.duration ?? 2, samples: 16,
    lens: { fstop: 4, focalLength: opts.focal ?? 70, focus: Math.hypot(cx - tx, cy - ty, cz - tz) },
    look: { exposure: 1.6, bloomStrength: 0.03, vignette: 0.3 },
    update(t, ctx) {
      camera.position.set(cx, cy, cz); camera.lookAt(tx, ty, tz);
      softSpot(key, keyBase, 4, ctx.lightJitter);
      softSpot(rim, rimBase, 3, [ctx.rand(0) * 2 - 1, ctx.rand(1) * 2 - 1]);
      clawd.pose.blink = 0; clawd.update();
      jolly.pose.time = t; jolly.group.updateMatrixWorld(true); jolly.update();
    },
  };
}
