// Material helpers shared by every lit object.
//
// The depth/normal/velocity prepass renders the same materials as the main
// pass. NodeMaterial always builds its lighting, so without help the prepass
// would shade every fragment twice. The prepass sets `context.prepass`; lit
// materials made here skip lighting (and shadows) when they see it.

import * as THREE from 'three/webgpu';
import { vec3, positionLocal, positionPrevious } from 'three/tsl';

export function prepassAware(material) {
  const setupLighting = material.setupLighting;
  material.setupLighting = function (builder) {
    if (builder.context.prepass === true) return vec3(0);
    return setupLighting.call(this, builder);
  };
  return material;
}

/**
 * For vertex-animated materials: report camera-only motion to the velocity
 * buffer (the displaced position is treated as static for this frame). The
 * alternative, the undisplaced geometry position, reads as huge bogus motion.
 */
export function staticVelocity(material) {
  const setupPosition = material.setupPosition;
  material.setupPosition = function (builder) {
    const r = setupPosition.call(this, builder);
    if (builder.needsPreviousData()) positionPrevious.assign(positionLocal);
    return r;
  };
  return material;
}

export function standard(params = {}) {
  const m = new THREE.MeshStandardNodeMaterial(params);
  return prepassAware(m);
}

export function physical(params = {}) {
  const m = new THREE.MeshPhysicalNodeMaterial(params);
  return prepassAware(m);
}
