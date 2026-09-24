// Grass: ~70k blades around the eye, laid out on the GPU every frame.
//
// A 56 m square grid anchored to world cells (so blades never swim as you
// move) is filled by a compute pass: each cell gets jittered blades where the
// terrain shader would draw grass (same noise masks), thinning with distance.
// Blades are 3-segment tapered strips that bend with travelling gusts and
// lean away from the player's feet; tips are lighter and let light through.

import * as THREE from 'three/webgpu';
import {
  Fn, instancedArray, instanceIndex, uniform, vec2, vec3, vec4, float, uint, int, floor, fract, sin, cos, mix,
  smoothstep, clamp, max, min, length, normalize, dot, attribute, positionGeometry, cameraPosition, cameraViewMatrix,
  cameraProjectionMatrix, varying, pow, select, positionWorld, If, abs,
} from 'three/tsl';
import { standard } from '../render/materials.js';
import { fbm2, vnoise2, hash22, hash21 } from '../render/tslnoise.js';
import { env } from '../env.js';

let GRID = 112;               // cells per side
const CELL = 0.5;             // m
const PER_CELL = 6;           // blade slots per cell
let COUNT = GRID * GRID * PER_CELL;

export class Grass {
  constructor(renderer, { terrain, island, grid = 112 }) {
    GRID = grid; COUNT = GRID * GRID * PER_CELL;
    this.renderer = renderer;
    this.terrain = terrain;
    this.island = island;
    this.blades = instancedArray(COUNT, 'vec4');     // x, y, z, packed(yaw, phase)
    this.shape = instancedArray(COUNT, 'vec4');      // height, width, lean, tint
    this.origin = uniform(new THREE.Vector2());
    this.eye = uniform(new THREE.Vector3());
    this.foot = uniform(new THREE.Vector3(0, -1000, 0));
    this.density = uniform(1);
    this._build();
  }

  _build() {
    const T = this.terrain;
    this.kernel = Fn(() => {
      const i = instanceIndex;
      const cellIdx = i.div(uint(PER_CELL));
      const slot = float(i.mod(uint(PER_CELL)));
      const cx = float(cellIdx.mod(uint(GRID))), cz = float(cellIdx.div(uint(GRID)));
      const worldCell = floor(this.origin.div(CELL)).add(vec2(cx, cz));
      const h2 = hash22(worldCell.mul(7.13).add(slot.mul(31.7)));
      const xz = worldCell.add(h2).mul(CELL).toVar();
      const d = T.sampleLevel(xz).toVar();
      const h = d.x, sdf = d.y;
      // same masks as the terrain's grass layer: inland, not beach, not forest floor, gentle slope
      const e = 1.6;
      const hx = T.sampleLevel(xz.add(vec2(e, 0))).x.sub(T.sampleLevel(xz.sub(vec2(e, 0))).x);
      const hz = T.sampleLevel(xz.add(vec2(0, e))).x.sub(T.sampleLevel(xz.sub(vec2(0, e))).x);
      const slope = float(1).sub(normalize(vec3(hx.negate(), e * 2, hz.negate())).y);
      const beach = smoothstep(-75, -45, sdf).mul(smoothstep(5.0, 3.2, h)).max(smoothstep(0.4, -0.4, h));
      const n1 = fbm2(xz.mul(0.018), 3).mul(0.5).add(0.5);
      const forest = smoothstep(0.45, 0.62, n1);
      const steep = smoothstep(0.2, 0.34, slope);
      let mask = float(1).sub(beach).mul(float(1).sub(steep)).mul(mix(float(1), float(0.25), forest));
      // tufts: patchy density so the carpet isn't uniform
      const tuft = smoothstep(0.25, 0.7, vnoise2(xz.mul(0.35)).mul(0.5).add(0.5).add(vnoise2(xz.mul(1.7)).mul(0.25)));
      mask = mask.mul(mix(float(0.35), float(1), tuft));
      // thin out with distance (keep the nearest slots)
      const dist = length(xz.sub(this.eye.xz));
      const keepFrac = smoothstep(28, 10, dist).mul(0.8).add(0.2).mul(this.density);
      const keep = mask.mul(select(slot.div(PER_CELL).lessThan(keepFrac), float(1), float(0))).mul(smoothstep(27.5, 24, dist));
      const r = hash22(worldCell.mul(3.1).add(slot.mul(11.3)));
      const height = mix(0.28, 0.75, r.x).mul(mix(0.7, 1.15, tuft)).mul(keep).mul(smoothstep(0.1, 0.35, mask));
      const width = mix(0.018, 0.03, r.y).mul(mix(float(1), float(1.8), smoothstep(12, 26, dist)));
      this.blades.element(i).assign(vec4(xz.x, h, xz.y, r.x.mul(6.283).add(floor(r.y.mul(50)).mul(6.283))));
      this.shape.element(i).assign(vec4(height, width, r.y.sub(0.5).mul(0.6), hash21(worldCell.add(slot))));
    })().compute(COUNT, [64]);

    // blade: 3 segments, tapered, 7 vertices
    const g = new THREE.InstancedBufferGeometry();
    const pos = [], idx = [];
    const segs = [0, 0.4, 0.75, 1];
    for (let k = 0; k < 3; k++) { const t = segs[k]; const w = 1 - t * 0.85; pos.push(-w, t, 0, w, t, 0); }
    pos.push(0, 1, 0);
    for (let k = 0; k < 2; k++) { const a = k * 2; idx.push(a, a + 1, a + 2, a + 1, a + 3, a + 2); }
    idx.push(4, 5, 6);
    g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
    g.setIndex(idx);
    g.instanceCount = COUNT;
    const mat = standard({ roughness: 0.82, metalness: 0, side: THREE.DoubleSide });
    const B = this.blades.toAttribute(), S = this.shape.toAttribute();
    const local = positionGeometry;
    const t = local.y;
    const yaw = fract(B.w.div(6.283)).mul(6.283);
    const phase = floor(B.w.div(6.283));
    const H = S.x, W = S.y;
    const side = vec3(cos(yaw), 0, sin(yaw));
    const face = vec3(sin(yaw).negate(), 0, cos(yaw));
    // wind: gust waves travelling downwind + per-blade flutter
    const w2 = env.windDir;
    const along = dot(B.xz, w2);
    const gust = sin(along.mul(0.35).sub(env.time.mul(2.2))).mul(0.5).add(0.5).mul(vnoise2(B.xz.mul(0.05).sub(w2.mul(env.time.mul(0.6)))).mul(0.5).add(0.6));
    const flutter = sin(env.time.mul(4.3).add(phase.mul(1.7))).mul(0.12);
    const bendAmt = gust.mul(0.55).add(flutter).mul(env.windSpeed.div(8)).add(S.z.mul(0.5));
    // push away from the player's feet
    const toFoot = B.xyz.sub(this.foot);
    const dF = length(toFoot.xz);
    const push = smoothstep(0.9, 0.15, dF).mul(smoothstep(1.2, 0.0, abs(toFoot.y)));
    const pushDir = select(dF.greaterThan(1e-3), normalize(vec3(toFoot.x, 0, toFoot.z)), vec3(0));
    const bendDir = normalize(vec3(w2.x, 0, w2.y).mul(bendAmt).add(pushDir.mul(push.mul(1.4))).add(face.mul(S.z.mul(0.3))).add(vec3(1e-4, 0, 0)));
    const bend = min(length(vec3(w2.x, 0, w2.y).mul(bendAmt).add(pushDir.mul(push.mul(1.4)))), 1.3);
    const curve = t.mul(t);
    const p = B.xyz.add(side.mul(local.x.mul(W)))
      .add(vec3(0, t.mul(H).mul(float(1).sub(curve.mul(bend).mul(0.35))), 0))
      .add(bendDir.mul(curve.mul(bend).mul(H).mul(0.7)));
    mat.positionNode = p;
    // rounded blade normal: tilt across the width, facing up the bend
    const n = normalize(face.add(side.mul(local.x.mul(0.6))).add(vec3(0, 0.4, 0)));
    mat.normalNode = cameraViewMatrix.mul(vec4(n, 0)).xyz;
    const tint = S.w;
    const base = mix(vec3(0.16, 0.22, 0.08), vec3(0.2, 0.25, 0.1), tint);
    const tip = mix(vec3(0.46, 0.56, 0.22), vec3(0.62, 0.6, 0.3), tint.mul(tint));
    const vt = varying(t, 'vGrassT');
    mat.colorNode = mix(base, tip, vt.pow(0.8));
    const V = normalize(positionWorld.sub(cameraPosition));
    const back = pow(max(dot(V, env.sunDir), 0), 4);
    mat.emissiveNode = tip.mul(tip).mul(env.sunColor).mul(back.mul(vt).mul(0.05));
    mat.userData.noContactShadow = true;
    mat.aoNode = mix(float(0.45), float(1), vt);
    this.mesh = new THREE.Mesh(g, mat);
    this.mesh.frustumCulled = false;
    this.mesh.castShadow = false;
    this.mesh.receiveShadow = true;
    this.mesh.name = 'grass';
  }

  update(camera, player) {
    const c = camera.position;
    this.origin.value.set(c.x - GRID * CELL / 2, c.z - GRID * CELL / 2);
    this.eye.value.copy(c);
    if (player && player.mode === 'walk') this.foot.value.copy(player.feet); else this.foot.value.set(0, -1000, 0);
    // nothing to draw far above the ground
    this.mesh.visible = c.y < Math.max(this.island.heightAt(c.x, c.z), 0) + 60;
    if (this.mesh.visible) this.renderer.compute(this.kernel);
  }
}
