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
import { standard, staticVelocity } from '../render/materials.js';
import { vnoise2, hash22, hash21 } from '../render/tslnoise.js';
import { env } from '../env.js';

let GRID = 112;               // cells per side
const CELL = 0.45;            // m
const PER_CELL = 7;           // clump slots per cell (each clump: 5 blades)
let COUNT = GRID * GRID * PER_CELL;

export class Grass {
  constructor(renderer, { terrain, island, grid = 112 }) {
    this.enabled = true;     // off in the Low quality tier (the blades and their compute are skipped)
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
      // baked maps: tree cover (the forest floor is litter, not turf) and
      // drainage (lush, taller grass in damp hollows, short on dry ridges)
      const aux = T.sampleAux(xz, 0);
      const forest = aux.a;
      const moist = smoothstep(3.5, 10.0, aux.r.mul(255 / 12));
      const steep = smoothstep(0.2, 0.34, slope);
      let mask = float(1).sub(beach).mul(float(1).sub(steep)).mul(mix(float(1), float(0.2), forest));
      // tufts: patchy density so the carpet isn't uniform
      const tuft = smoothstep(0.25, 0.7, vnoise2(xz.mul(0.35)).mul(0.5).add(0.5).add(vnoise2(xz.mul(1.7)).mul(0.25)));
      mask = mask.mul(mix(float(0.35), float(1), tuft));
      // thin out with distance (keep the nearest slots)
      const dist = length(xz.sub(this.eye.xz));
      const keepFrac = smoothstep(25, 8, dist).mul(0.75).add(0.25).mul(this.density);
      const keep = mask.mul(select(slot.div(PER_CELL).lessThan(keepFrac), float(1), float(0))).mul(smoothstep(24.8, 21.5, dist));
      const r = hash22(worldCell.mul(3.1).add(slot.mul(11.3)));
      // short turf with the odd taller seed stalk; lusher where it is damp
      const stalk = select(r.x.greaterThan(0.96), float(1.7), float(1));
      const height = mix(0.08, 0.34, r.x.mul(r.x)).mul(stalk).mul(mix(0.7, 1.15, tuft)).mul(mix(0.8, 1.25, moist)).mul(keep).mul(smoothstep(0.3, 0.6, mask));
      const width = mix(0.008, 0.016, r.y).mul(mix(float(1), float(2.2), smoothstep(10, 24, dist)));
      // dry, straw-coloured blades on dry ground (packed into the tint's integer part)
      const dry = select(hash21(worldCell.mul(1.7).add(slot.mul(5.1))).lessThan(moist.oneMinus().mul(0.14).add(0.03)), float(1), float(0));
      this.blades.element(i).assign(vec4(xz.x, h, xz.y, r.x.mul(6.283).add(floor(r.y.mul(50)).mul(6.283))));
      this.shape.element(i).assign(vec4(height, width, r.y.sub(0.5).mul(0.9), hash21(worldCell.add(slot)).mul(0.999).add(dry)));
    })().compute(COUNT, [64]);

    // a clump of 5 blades, each 3 tapered segments (7 vertices); the blade's
    // index within the clump rides in position.z
    const CLUMP = 5;
    const g = new THREE.InstancedBufferGeometry();
    const pos = [], idx = [];
    const segs = [0, 0.4, 0.75, 1];
    for (let b = 0; b < CLUMP; b++) {
      const o = b * 7;
      for (let k = 0; k < 3; k++) { const t = segs[k]; const w = 1 - t * 0.85; pos.push(-w, t, b, w, t, b); }
      pos.push(0, 1, b);
      for (let k = 0; k < 2; k++) { const a = o + k * 2; idx.push(a, a + 1, a + 2, a + 1, a + 3, a + 2); }
      idx.push(o + 4, o + 5, o + 6);
    }
    g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
    g.setIndex(idx);
    g.instanceCount = COUNT;
    const mat = standard({ roughness: 0.82, metalness: 0, side: THREE.DoubleSide });
    const B = this.blades.toAttribute(), S = this.shape.toAttribute();
    const local = positionGeometry;
    const t = local.y;
    const phase = floor(B.w.div(6.283));
    // this blade within the clump: its own heading, spot, height and outward lean
    const kb = local.z;
    const hk = hash21(vec2(phase.mul(0.37).add(kb.mul(3.1)), kb.mul(7.7).add(fract(B.w))));
    const hk2 = hash21(vec2(kb.mul(5.3).add(1.7), phase.mul(0.11).add(kb)));
    const yaw = fract(B.w.div(6.283)).mul(6.283).add(kb.mul(2.39996)).add(hk.sub(0.5));
    const ang = kb.mul(2.39996).add(hk2.mul(6.283));
    const out = vec3(cos(ang), 0, sin(ang));
    const root = B.xyz.add(out.mul(hk2.sqrt().mul(0.06)));
    const H = S.x.mul(hk.mul(0.55).add(0.65)), W = S.y;
    const side = vec3(cos(yaw), 0, sin(yaw));
    const face = vec3(sin(yaw).negate(), 0, cos(yaw));
    // wind: gust waves travelling downwind + per-blade flutter
    const w2 = env.windDir;
    const along = dot(B.xz, w2);
    const gust = sin(along.mul(0.35).sub(env.time.mul(2.2))).mul(0.5).add(0.5).mul(vnoise2(B.xz.mul(0.05).sub(w2.mul(env.time.mul(0.6)))).mul(0.5).add(0.6));
    const flutter = sin(env.time.mul(4.3).add(phase.mul(1.7)).add(kb.mul(1.3))).mul(0.12);
    const bendAmt = gust.mul(0.55).add(flutter).mul(env.windSpeed.div(8)).add(S.z.mul(0.5));
    // push away from the player's feet
    const toFoot = B.xyz.sub(this.foot);
    const dF = length(toFoot.xz);
    const push = smoothstep(0.9, 0.15, dF).mul(smoothstep(1.2, 0.0, abs(toFoot.y)));
    const pushDir = select(dF.greaterThan(1e-3), normalize(vec3(toFoot.x, 0, toFoot.z)), vec3(0));
    // blades fan out of the clump
    const splay = out.mul(hk.mul(0.35).add(0.2));
    const bendVec = vec3(w2.x, 0, w2.y).mul(bendAmt).add(pushDir.mul(push.mul(1.4))).add(splay);
    const bendDir = normalize(bendVec.add(face.mul(S.z.mul(0.3))).add(vec3(1e-4, 0, 0)));
    const bend = min(length(bendVec), 1.3);
    const curve = t.mul(t);
    const p = root.add(side.mul(local.x.mul(W)))
      .add(vec3(0, t.mul(H).mul(float(1).sub(curve.mul(bend).mul(0.35))), 0))
      .add(bendDir.mul(curve.mul(bend).mul(H).mul(0.7)));
    mat.positionNode = p;
    staticVelocity(mat);   // blades are anchored; their bending is slow
    // rounded blade normal: tilt across the width, facing up the bend
    const n = normalize(face.add(side.mul(local.x.mul(0.6))).add(vec3(0, 0.4, 0)));
    mat.normalNode = cameraViewMatrix.mul(vec4(n, 0)).xyz;
    const tint = fract(S.w), dry = floor(S.w);
    // real grass albedo (linear) tops out around 0.2 in green: brighter blades
    // would ring the player with a pale disc against the terrain's grass
    const base = mix(mix(vec3(0.04, 0.075, 0.018), vec3(0.055, 0.09, 0.024), tint), vec3(0.14, 0.12, 0.06), dry);
    const tip = mix(mix(vec3(0.12, 0.19, 0.045), vec3(0.17, 0.22, 0.06), tint.mul(tint)), vec3(0.3, 0.27, 0.13), dry);
    const vt = varying(t, 'vGrassT');
    mat.colorNode = mix(base, tip, vt.pow(0.8));
    const V = normalize(positionWorld.sub(cameraPosition));
    const back = pow(max(dot(V, env.sunDir), 0), 4);
    mat.emissiveNode = tip.mul(env.sunColor).mul(back.mul(vt).mul(0.06));
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
    this.mesh.visible = this.enabled && c.y < Math.max(this.island.heightAt(c.x, c.z), 0) + 60;
    if (this.mesh.visible) this.renderer.compute(this.kernel);
  }
}
