// Water probe: evaluates the exact surface function on the GPU.
//
//  - a 4×4 patch of finest-LOD mesh vertices around the eye. The composite
//    interpolates them with the mesh's own triangulation, so the waterline it
//    computes on the near plane matches the rendered surface to the pixel
//    (no gap between the surface and the underwater volume);
//  - arbitrary query points (boat hull, swimmer, creatures) whose heights are
//    read back asynchronously for physics.

import * as THREE from 'three/webgpu';
import { Fn, instanceIndex, instancedArray, storage, uniform, vec2, vec4, float, uint, If, int } from 'three/tsl';

export const PROBE_SPACING = 0.125;   // finest ocean LOD vertex spacing (LEAF_SIZE / PATCH)
export const PROBE_GRID = 4;
export const MAX_QUERIES = 64;

export class WaterProbe {
  constructor(renderer, ocean, shore, time) {
    this.renderer = renderer;
    this.gridOrigin = uniform(new THREE.Vector2());
    const G = PROBE_GRID * PROBE_GRID;
    this.count = G + MAX_QUERIES;
    this.queryData = new Float32Array(MAX_QUERIES * 4);
    this.queryAttr = new THREE.StorageInstancedBufferAttribute(this.queryData, 4);
    this.queries = storage(this.queryAttr, 'vec4', MAX_QUERIES).toReadOnly();
    this.results = instancedArray(this.count, 'vec4');
    const { results } = this;
    const queries = this.queries;
    this.kernel = Fn(() => {
      const i = instanceIndex;
      If(i.lessThan(uint(G)), () => {
        const gx = float(i.mod(uint(PROBE_GRID))), gz = float(i.div(uint(PROBE_GRID)));
        const xz = this.gridOrigin.add(vec2(gx, gz).mul(PROBE_SPACING));
        const s = ocean.surface(xz, float(PROBE_SPACING), shore, time);
        results.element(i).assign(vec4(s.y, 0, 0, 1));
      }).Else(() => {
        // arbitrary point: invert the horizontal displacement (2 iterations)
        const q = queries.element(i.sub(uint(G)));
        const p = q.xy;
        const s0 = ocean.surface(p, float(0.5), shore, time);
        const p1 = p.sub(s0.disp.xz);
        const s1 = ocean.surface(p1, float(0.5), shore, time);
        const p2 = p.sub(s1.disp.xz);
        const s2 = ocean.surface(p2, float(0.5), shore, time);
        // slope from a small stencil (for buoyancy torque / orientation)
        const e = 0.4;
        const sx = ocean.surface(p2.add(vec2(e, 0)), float(0.5), shore, time).y;
        const sz = ocean.surface(p2.add(vec2(0, e)), float(0.5), shore, time).y;
        results.element(i).assign(vec4(s2.y, sx.sub(s2.y).div(e), sz.sub(s2.y).div(e), select_foam(s2)));
      });
    })().compute(this.count, [64]);
    this.pending = false;
    this.cpu = new Float32Array(this.count * 4);
    this.numQueries = 0;
    this.frame = 0;
  }

  /** Set up to MAX_QUERIES (x, z) points; results are available one or two frames later. */
  setQueries(points) {
    this.numQueries = Math.min(points.length, MAX_QUERIES);
    for (let k = 0; k < this.numQueries; k++) {
      this.queryData[k * 4] = points[k][0];
      this.queryData[k * 4 + 1] = points[k][1];
    }
    this.queryAttr.needsUpdate = true;
  }

  update(camera) {
    const S = PROBE_SPACING;
    const ox = Math.floor(camera.position.x / S) * S - S;
    const oz = Math.floor(camera.position.z / S) * S - S;
    this.gridOrigin.value.set(ox, oz);
    this.renderer.compute(this.kernel);
    if (!this.pending && !this.noReadback) {
      this.pending = true;
      const origin = [ox, oz];
      this.renderer.getArrayBufferAsync(this.results.value).then((buf) => {
        this.cpu.set(new Float32Array(buf));
        this.cpuOrigin = origin;
        this.pending = false;
        this.frame++;
      }).catch(() => { this.pending = false; });
    }
  }

  /** latest water height at the eye (from the grid, bilinear) */
  eyeHeight(camera) {
    const S = PROBE_SPACING;
    if (!this.cpuOrigin) return 0;
    const [ox, oz] = this.cpuOrigin;
    const fx = (camera.position.x - ox) / S, fz = (camera.position.z - oz) / S;
    const i = Math.max(0, Math.min(PROBE_GRID - 2, Math.floor(fx))), j = Math.max(0, Math.min(PROBE_GRID - 2, Math.floor(fz)));
    const tx = Math.min(1, Math.max(0, fx - i)), tz = Math.min(1, Math.max(0, fz - j));
    const h = (a, b) => this.cpu[(b * PROBE_GRID + a) * 4];
    return (h(i, j) * (1 - tx) + h(i + 1, j) * tx) * (1 - tz) + (h(i, j + 1) * (1 - tx) + h(i + 1, j + 1) * tx) * tz;
  }

  query(k) {
    const o = (PROBE_GRID * PROBE_GRID + k) * 4;
    return { height: this.cpu[o], slopeX: this.cpu[o + 1], slopeZ: this.cpu[o + 2], foam: this.cpu[o + 3] };
  }
}

function select_foam(s) {
  return s.fftFoam ? s.fftFoam : float(0);
}
