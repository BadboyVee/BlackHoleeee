// Helpers for image-based lighting and lens set-up
import * as THREE from 'three';

// Build a small emissive "light stage" scene and prefilter it into a PMREM environment map.
export function makeEnvironment(renderer, { panels = [], top = [0.02, 0.02, 0.025], bottom = [0.01, 0.01, 0.01], horizon = null } = {}) {
  const scene = new THREE.Scene();
  const skyGeo = new THREE.SphereGeometry(50, 64, 32);
  const cols = [];
  const p = skyGeo.attributes.position;
  for (let i = 0; i < p.count; i++) {
    const y = p.getY(i) / 50;
    const c = new THREE.Color().fromArray(y > 0 ? top : bottom);
    if (horizon) c.lerp(new THREE.Color().fromArray(horizon), Math.pow(1 - Math.abs(y), 6));
    cols.push(c.r, c.g, c.b);
  }
  skyGeo.setAttribute('color', new THREE.Float32BufferAttribute(cols, 3));
  scene.add(new THREE.Mesh(skyGeo, new THREE.MeshBasicMaterial({ vertexColors: true, side: THREE.BackSide })));
  for (const pn of panels) {
    const m = new THREE.Mesh(
      pn.round ? new THREE.CircleGeometry(pn.size[0] / 2, 32) : new THREE.PlaneGeometry(pn.size[0], pn.size[1]),
      new THREE.MeshBasicMaterial({ color: new THREE.Color().fromArray(pn.color).multiplyScalar(pn.intensity ?? 1), side: THREE.DoubleSide }));
    m.position.fromArray(pn.pos);
    m.lookAt(0, 0, 0);
    scene.add(m);
  }
  const pm = new THREE.PMREMGenerator(renderer);
  const rt = pm.fromScene(scene, 0.0, 0.1, 100);
  pm.dispose();
  return rt.texture;
}

// vertical FOV for a lens on a full-frame sensor cropped to 16:9
export function fovFromFocal(mm) { return THREE.MathUtils.radToDeg(2 * Math.atan(10.125 / mm)); }

export function softSpot(light, base, radius, jitter) {
  // move a light on a disc perpendicular to its direction for area-light soft shadows
  const dir = new THREE.Vector3().subVectors(light.target.position, base).normalize();
  const t1 = new THREE.Vector3().crossVectors(dir, Math.abs(dir.y) < 0.9 ? new THREE.Vector3(0, 1, 0) : new THREE.Vector3(1, 0, 0)).normalize();
  const t2 = new THREE.Vector3().crossVectors(dir, t1);
  const [a, b] = jitter;
  light.position.copy(base).addScaledVector(t1, a * radius).addScaledVector(t2, b * radius);
}
