// Spray: GPU particles for bow spray, prop wash, breaking-wave spray and
// whale breaches.
//
// The CPU turns emitter requests into a small spawn batch each frame
// (positions, velocities, sizes, lifetimes with the requested spread). A
// compute pass copies the batch into a ring of 32k particles, a second one
// integrates them: gravity, air drag (fine mist slows fast and drifts on the
// wind, big drops fly ballistic), death on hitting the water. They are drawn
// as camera-facing discs lit by the sun (droplets throw a bright forward
// scatter when backlit) and the sky.

import * as THREE from 'three/webgpu';
import {
  Fn, instancedArray, storage, instanceIndex, uniform, vec2, vec3, vec4, float, uint, If, max, min, exp,
  length, smoothstep, dot, normalize, mix, pow, attribute, cameraPosition, cameraViewMatrix, cameraProjectionMatrix,
  positionGeometry, varying, uv, clamp, select, sqrt, texture, atomicAdd, hash,
} from 'three/tsl';
import { env } from '../env.js';

const MAX = 32768;
const BATCH = 2048;

export class Spray {
  constructor(renderer, { ocean, wake = null }) {
    this.renderer = renderer;
    this.ocean = ocean;
    this.wake = wake;
    this.pos = instancedArray(MAX, 'vec4');    // xyz, life left (s)
    this.vel = instancedArray(MAX, 'vec4');    // xyz, size (m, <0 = mist)
    this.batchData = new Float32Array(BATCH * 8);
    this.batchAttr = new THREE.StorageInstancedBufferAttribute(this.batchData, 4);
    this.batch = storage(this.batchAttr, 'vec4', BATCH * 2).toReadOnly();
    this.batchCount = uniform(0, 'uint');
    // ring-buffer head shared by CPU batches and GPU emitters
    this.headBuf = instancedArray(1, 'uint').toAtomic();
    this.emitters = [];
    this.pending = 0;
    this.dt = uniform(0);
    this.wind = uniform(new THREE.Vector3(2, 0, 1));
    this.batchN = 0;
    this._build();
  }

  _build() {
    const { pos, vel, batch } = this;
    this.spawnKernel = Fn(() => {
      const i = instanceIndex;
      If(i.lessThan(this.batchCount), () => {
        const slot = atomicAdd(this.headBuf.element(0), uint(1)).mod(uint(MAX)).toVar();
        pos.element(slot).assign(batch.element(i.mul(2)));
        vel.element(slot).assign(batch.element(i.mul(2).add(1)));
      });
    })().compute(BATCH, [64]);

    const ocean = this.ocean;
    this.updateKernel = Fn(() => {
      const i = instanceIndex;
      const p = pos.element(i).toVar();
      If(p.w.greaterThan(0), () => {
        const v = vel.element(i).toVar();
        const dt = this.dt;
        const mist = v.w.lessThan(0);
        const size = v.w.abs();
        // drag: tiny drops and mist decelerate quickly and drift with the wind
        const k = select(mist, float(2.6), float(0.9).div(size.mul(40).add(1)).add(0.08));
        const rel = v.xyz.sub(this.wind);
        const nv = v.xyz.sub(rel.mul(float(1).sub(exp(k.mul(dt).negate())))).add(vec3(0, select(mist, float(-0.4), float(-9.81)), 0).mul(dt));
        const np = p.xyz.add(nv.mul(dt));
        // water surface (large cascades are enough for spray to land on)
        const L0 = ocean.lengthScales[0], L1 = ocean.lengthScales[1];
        const h = texture(ocean.fft.displacement[0], np.xz.div(L0)).level(0).y.add(texture(ocean.fft.displacement[1], np.xz.div(L1)).level(0).y);
        const wk = this.wake ? this.wake.sample(np.xz).x : float(0);
        const under = np.y.lessThan(h.add(wk).sub(0.05)).and(mist.not());
        const life = select(under, float(0), p.w.sub(dt));
        pos.element(i).assign(vec4(np, life));
        vel.element(i).assign(vec4(nv, v.w));
      });
    })().compute(MAX, [64]);

    // render: instanced camera-facing quads
    const g = new THREE.InstancedBufferGeometry();
    g.index = new THREE.BufferAttribute(new Uint16Array([0, 1, 2, 0, 2, 3]), 1);
    g.setAttribute('position', new THREE.BufferAttribute(new Float32Array([-1, -1, 0, 1, -1, 0, 1, 1, 0, -1, 1, 0]), 3));
    g.setAttribute('uv', new THREE.BufferAttribute(new Float32Array([0, 0, 1, 0, 1, 1, 0, 1]), 2));
    g.instanceCount = MAX;
    // unlit material driven by color/opacity nodes so the scene pass's MRT
    // outputs are still generated (a raw fragmentNode would skip them)
    const mat = new THREE.MeshBasicNodeMaterial();
    mat.transparent = true;
    mat.depthWrite = false;
    mat.blending = THREE.NormalBlending;
    mat.userData.noAO = true;
    mat.userData.reactive = 1;
    // vertex shaders may not bind read-write storage: read the particle
    // buffers as instanced vertex attributes instead
    const P = pos.toAttribute(), V = vel.toAttribute();
    const alive = P.w.greaterThan(0);
    const mist = V.w.lessThan(0);
    const size = V.w.abs();
    const life = P.w;
    // fade in quickly, out over the last half second; mist swells as it ages
    const fade = smoothstep(0.0, 0.5, life);
    const grow = select(mist, float(1).add(float(1.5).sub(life).max(0).mul(0.8)), float(1));
    const viewPos = cameraViewMatrix.mul(vec4(P.xyz, 1));
    // motion streak: stretch fast drops a little along their screen velocity
    const vv = cameraViewMatrix.mul(vec4(V.xyz, 0)).xy;
    const speed = length(vv);
    const dirS = select(speed.greaterThan(1e-3), vv.div(speed), vec2(0, 1));
    const stretch = min(speed.mul(0.012).div(size.max(0.005)), 3.0).mul(select(mist, float(0), float(1)));
    const c = positionGeometry.xy;
    const along = dot(c, dirS);
    const offs = c.add(dirS.mul(along.mul(stretch))).mul(size.mul(grow)).mul(select(alive, float(1), float(0)));
    mat.vertexNode = cameraProjectionMatrix.mul(vec4(viewPos.xy.add(offs), viewPos.z, 1));
    const vFade = varying(fade.mul(select(alive, float(1), float(0))), 'vSprayFade');
    const vMist = varying(select(mist, float(1), float(0)), 'vSprayMist');
    const vWorld = varying(P.xyz, 'vSprayPos');
    const q = uv().mul(2).sub(1);
    const disc = smoothstep(1.0, mix(float(0.55), float(0.0), vMist), length(q));
    const toCam = normalize(cameraPosition.sub(vWorld));
    const cosT = dot(toCam.negate(), env.sunDir);
    // water drops: strong forward scattering (glints when looking toward the sun)
    const fwd = pow(max(cosT, 0), 6).mul(2.2).add(0.35);
    const sun = env.sunColor.mul(fwd).mul(0.09);
    const sky = env.skyIrradiance.mul(0.11);
    mat.colorNode = sun.add(sky).mul(mix(float(1), float(0.8), vMist));
    mat.opacityNode = disc.mul(vFade).mul(mix(float(0.85), float(0.22), vMist));
    this.mesh = new THREE.Mesh(g, mat);
    this.mesh.frustumCulled = false;
    this.mesh.renderOrder = 30;
    this.mesh.layers.set(3); // LAYER_NO_PREPASS
    this.mesh.name = 'spray';
  }

  /**
   * Queue particles. count may be fractional (accumulated across frames).
   * { position, velocity, spread (m/s), size (m), life (s), mist (0..1 fraction) }
   */
  emit({ position, velocity, count, spread = 0.5, size = 0.03, life = 1.2, mist = 0.25, radius = 0.15 }) {
    // fractional counts round stochastically, so low rates still emit
    let n = Math.floor(count) + (Math.random() < count - Math.floor(count) ? 1 : 0);
    const b = this.batchData;
    while (n-- > 0 && this.batchN < BATCH) {
      const o = this.batchN * 8;
      const isMist = Math.random() < mist;
      const rx = (Math.random() * 2 - 1), ry = (Math.random() * 2 - 1), rz = (Math.random() * 2 - 1);
      b[o] = position.x + rx * radius; b[o + 1] = position.y + ry * radius * 0.5; b[o + 2] = position.z + rz * radius;
      b[o + 3] = life * (0.5 + Math.random() * 0.8) * (isMist ? 1.6 : 1);
      const sp = spread * (isMist ? 0.6 : 1);
      b[o + 4] = velocity.x + gauss() * sp; b[o + 5] = velocity.y + gauss() * sp * 0.7; b[o + 6] = velocity.z + gauss() * sp;
      const s = size * (0.5 + Math.random() * Math.random() * 1.6);
      b[o + 7] = isMist ? -s * 6 : s;
      this.batchN++;
    }
  }

  update(dt) {
    this.dt.value = Math.min(dt, 0.05);
    if (this.batchN > 0) {
      this.batchAttr.needsUpdate = true;
      this.batchCount.value = this.batchN;
      this.renderer.compute(this.spawnKernel);
      this.batchN = 0;
    }
    if (dt > 0) {
      for (const e of this.emitters) e.update?.(dt);
      for (const e of this.emitters) this.renderer.compute(e.kernel);
      this.renderer.compute(this.updateKernel);
    }
  }

  /**
   * GPU emitter: build(write) returns a compute node; write(p, v, life, size)
   * appends one particle (TSL) at a slot claimed from the shared ring.
   */
  addGpuEmitter(count, build, update = null) {
    const write = (p, v, life, size) => {
      const slot = atomicAdd(this.headBuf.element(0), uint(1)).mod(uint(MAX)).toVar();
      this.pos.element(slot).assign(vec4(p, life));
      this.vel.element(slot).assign(vec4(v, size));
    };
    const kernel = build(write).compute(count, [64]);
    this.emitters.push({ kernel, update });
    return kernel;
  }
}

function gauss() {
  return (Math.random() + Math.random() + Math.random() - 1.5) * 1.15;
}
