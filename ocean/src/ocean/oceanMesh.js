// Ocean surface geometry: a CDLOD quadtree of instanced 32×32 patches.
//
// Vertices sit on a world-anchored grid for every LOD, so waves never swim
// under the mesh as the camera moves (the classic projected-grid jitter), and
// each patch geomorphs odd vertices onto its parent's grid as it approaches its
// LOD range, so there is no popping or cracking between levels.

import * as THREE from 'three/webgpu';

export const PATCH = 32;               // quads per patch edge
export const LEAF_SIZE = 4;            // metres covered by a finest-level patch
export const LEVELS = 14;              // 4 m .. 32 km
export const RANGE_FACTOR = 2.35;      // LOD range = factor * patch size

const MAX_PATCHES = 1400;

export function createPatchGeometry(attrName = 'oceanPatch') {
  const g = new THREE.InstancedBufferGeometry();
  const V = PATCH + 1;
  const pos = new Float32Array(V * V * 3);
  for (let z = 0; z < V; z++) {
    for (let x = 0; x < V; x++) {
      const i = (z * V + x) * 3;
      pos[i] = x; pos[i + 1] = 0; pos[i + 2] = z;
    }
  }
  const idx = [];
  for (let z = 0; z < PATCH; z++) {
    for (let x = 0; x < PATCH; x++) {
      const a = z * V + x, b = a + 1, c = a + V, d = c + 1;
      // alternate the diagonal so the tessellation is symmetric
      if ((x + z) & 1) idx.push(a, c, b, b, c, d);
      else idx.push(a, c, d, a, d, b);
    }
  }
  g.setIndex(idx);
  g.setAttribute('position', new THREE.BufferAttribute(pos, 3));
  const nrm = new Float32Array(V * V * 3);
  for (let i = 0; i < V * V; i++) nrm[i * 3 + 1] = 1;
  g.setAttribute('normal', new THREE.BufferAttribute(nrm, 3));
  const patch = new THREE.InstancedBufferAttribute(new Float32Array(MAX_PATCHES * 4), 4);
  patch.setUsage(THREE.DynamicDrawUsage);
  g.setAttribute(attrName, patch);
  g.instanceCount = 0;
  g.boundingSphere = new THREE.Sphere(new THREE.Vector3(), 1e7);
  g.boundingBox = new THREE.Box3(new THREE.Vector3(-1e7, -100, -1e7), new THREE.Vector3(1e7, 100, 1e7));
  return g;
}

const _box = new THREE.Box3();
const _frustum = new THREE.Frustum();
const _m = new THREE.Matrix4();

/**
 * Selects quadtree nodes around the camera and writes them to the instanced
 * 'oceanPatch' attribute as (originX, originZ, spacing, morphEnd).
 */
export class PatchSelector {
  constructor(geometry, { maxHeight = 12, minHeight = null, levels = LEVELS, leafSize = LEAF_SIZE, rangeFactor = RANGE_FACTOR, attrName = 'oceanPatch', bounds = null } = {}) {
    this.geometry = geometry;
    this.attr = geometry.getAttribute(attrName);
    this.maxHeight = maxHeight;
    this.minHeight = minHeight === null ? -maxHeight : minHeight;
    this.levels = levels;
    this.leafSize = leafSize;
    this.rootSize = leafSize * Math.pow(2, levels - 1);
    this.ranges = [];
    for (let l = 0; l < levels; l++) this.ranges.push(leafSize * Math.pow(2, l) * rangeFactor);
    this.bounds = bounds; // optional {x0, z0, x1, z1} world clamp
    this.heightRange = null; // optional (x, z, size) => [min, max]
    this.count = 0;
  }

  update(camera, extraFrustumMargin = 0) {
    _m.multiplyMatrices(camera.projectionMatrix, camera.matrixWorldInverse);
    _frustum.setFromProjectionMatrix(_m, camera.coordinateSystem);
    const cam = camera.getWorldPosition(new THREE.Vector3());
    this.cam = cam;
    this.count = 0;
    const R = this.rootSize;
    if (this.bounds) {
      const b = this.bounds;
      for (let z = b.z0; z < b.z1; z += R) for (let x = b.x0; x < b.x1; x += R) this._select(x, z, R, this.levels - 1, extraFrustumMargin);
    } else {
      // root grid of 3×3 nodes around the camera so the ocean always surrounds it
      const cx = Math.floor(cam.x / R) * R, cz = Math.floor(cam.z / R) * R;
      for (let j = -1; j <= 1; j++) {
        for (let i = -1; i <= 1; i++) {
          this._select(cx + i * R, cz + j * R, R, this.levels - 1, extraFrustumMargin);
        }
      }
    }
    this.geometry.instanceCount = this.count;
    this.attr.needsUpdate = true;
    this.attr.clearUpdateRanges();
    this.attr.addUpdateRange(0, this.count * 4);
  }

  _range(x, z, size) {
    if (this.heightRange) return this.heightRange(x, z, size);
    return [this.minHeight, this.maxHeight];
  }

  _distanceSq(x, z, size) {
    const c = this.cam;
    const [lo, hi] = this._range(x, z, size);
    const dx = Math.max(x - c.x, 0, c.x - (x + size));
    const dz = Math.max(z - c.z, 0, c.z - (z + size));
    const dy = Math.max(lo - c.y, 0, c.y - hi);
    return dx * dx + dy * dy + dz * dz;
  }

  _inFrustum(x, z, size, margin) {
    const [lo, hi] = this._range(x, z, size);
    _box.min.set(x - margin, lo - margin, z - margin);
    _box.max.set(x + size + margin, hi + margin, z + size + margin);
    return _frustum.intersectsBox(_box);
  }

  _add(x, z, size, morphRange) {
    if (this.count >= MAX_PATCHES) return;
    const a = this.attr.array, o = this.count * 4;
    a[o] = x; a[o + 1] = z; a[o + 2] = size / PATCH; a[o + 3] = morphRange;
    this.count++;
  }

  // CDLOD selection (Strugar 2009)
  _select(x, z, size, level, margin) {
    const d2 = this._distanceSq(x, z, size);
    const r = this.ranges[level];
    if (d2 > r * r && level < this.levels - 1) return false;
    if (!this._inFrustum(x, z, size, margin)) return true;
    if (level === 0) { this._add(x, z, size, r); return true; }
    const rc = this.ranges[level - 1];
    if (d2 > rc * rc) { this._add(x, z, size, r); return true; }
    const h = size / 2;
    for (let j = 0; j < 2; j++) {
      for (let i = 0; i < 2; i++) {
        const nx = x + i * h, nz = z + j * h;
        if (!this._select(nx, nz, h, level - 1, margin)) {
          // quadrant lies beyond the child range: draw it at child density but
          // fully morphed, which is exactly the parent's grid
          if (this._inFrustum(nx, nz, h, margin)) this._add(nx, nz, h, rc);
        }
      }
    }
    return true;
  }
}
