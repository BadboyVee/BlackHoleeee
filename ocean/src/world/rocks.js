// Boulders on the crags, in scoured gullies and along the rocky coast.
//
// Meshes come from Blender (tools/blender/rocks.py: fractured, weathered
// icospheres with cavity and moss masks in their vertex colours); they are
// textured triplanar with the terrain's basalt layer so rock outcrops and
// boulders read as the same stone, with moss on top in damp shade.

import * as THREE from 'three/webgpu';
import { attribute, positionWorld, normalWorld, vec3, float, abs, pow, mix, smoothstep, texture, int, max } from 'three/tsl';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { DRACOLoader } from 'three/addons/loaders/DRACOLoader.js';
import { standard, staticVelocity } from '../render/materials.js';
import { vnoise2 } from '../render/tslnoise.js';
import { inRange, uploadFirst } from './vegetation.js';
import { assetURL, dracoDecoderPath } from '../core/assets.js';
import { VILLAGE } from './island.js';
import { TERRAIN_TILE } from './terrainTextures.js';

const rndGen = (seed) => () => { seed |= 0; seed = seed + 0x6D2B79F5 | 0; let t = Math.imul(seed ^ seed >>> 15, 1 | seed); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; };
const smoothstepJS = (a, b, x) => { const t = Math.min(Math.max((x - a) / (b - a), 0), 1); return t * t * (3 - 2 * t); };

const NEAR = 70, FAR = 700;

export class Boulders {
  static async create(opts) {
    const draco = new DRACOLoader();
    draco.setDecoderPath(dracoDecoderPath());
    const gltf = await new GLTFLoader().setDRACOLoader(draco).loadAsync(assetURL('assets/terrain/rocks.glb'));
    draco.dispose();
    const geoms = {};
    gltf.scene.traverse((o) => { if (o.isMesh) geoms[o.name] = o.geometry; });
    return new Boulders(geoms, opts);
  }

  constructor(geoms, { scene, island, collision, textures }) {
    this.island = island;
    this.group = new THREE.Group();
    this.group.name = 'boulders';
    scene.add(this.group);
    const variants = Object.keys(geoms).filter((k) => k.endsWith('lod0')).length;
    this.list = this._place(variants, collision);
    this.material = this._material(textures);
    this.sets = [];
    for (let v = 0; v < variants; v++) {
      const list = this.list.filter((o) => o.v === v);
      if (!list.length) continue;
      const mk = (name) => {
        const g = geoms[name].clone();
        const m = new THREE.InstancedMesh(g, this.material, list.length);
        const data = new THREE.InstancedBufferAttribute(new Float32Array(list.length * 4), 4);
        data.setUsage(THREE.DynamicDrawUsage);
        g.setAttribute('vegData', data);
        m.count = 0;
        m.frustumCulled = false;
        m.castShadow = true;
        m.receiveShadow = true;
        m.userData.data = data;
        this.group.add(m);
        return m;
      };
      this.sets.push({ list, lod0: mk(`rock_${v}_lod0`), lod1: mk(`rock_${v}_lod1`) });
    }
    this.counts = this.list.length;
  }

  _material(textures) {
    const m = staticVelocity(standard({ roughness: 0.85, metalness: 0 }));
    const col = attribute('color', 'vec4');
    const n = normalWorld;
    const w = pow(abs(n), vec3(4)).toVar();
    const wn = w.div(max(w.x.add(w.y).add(w.z), 1e-4));
    const tile = TERRAIN_TILE[1];
    const p = positionWorld.div(tile);
    const tri = (uvv) => texture(textures.albedo, uvv).depth(int(1)).rgb;
    const albedo = tri(p.zy).mul(wn.x).add(tri(p.xz).mul(wn.y)).add(tri(p.xy).mul(wn.z));
    // moss on the tops, heavier where the stone sits in the forest's shade
    const moss = smoothstep(0.35, 0.8, col.y.mul(vnoise2(positionWorld.xz.mul(0.7)).mul(0.5).add(0.75)));
    const mossCol = mix(vec3(0.06, 0.09, 0.025), vec3(0.1, 0.12, 0.04), vnoise2(positionWorld.xz.mul(2.3)).mul(0.5).add(0.5));
    m.colorNode = mix(albedo.mul(1.1), mossCol, moss.mul(0.85));
    m.roughnessNode = mix(float(0.82), float(0.95), moss);
    m.aoNode = col.x;
    const data = attribute('vegData', 'vec4');
    m.maskNode = inRange(data.z, data.w);
    m.maskShadowNode = m.maskNode;
    return m;
  }

  _place(variants, col) {
    const isl = this.island;
    const rnd = rndGen(77);
    const out = [];
    const S = 3.5;
    for (let z = -800; z < 170; z += S) {
      for (let x = -570; x < 570; x += S) {
        const px = x + rnd() * S, pz = z + rnd() * S;
        const h = isl.heightAt(px, pz);
        if (h < 0.4) continue;
        const sdf = isl.sdfAt(px, pz);
        const n = isl.normalAt(px, pz);
        const slope = 1 - n.y;
        const eroded = isl.auxAt(px, pz, 1) * 255 / 6 - 128 / 6;
        const forest = isl.forestAt(px, pz);
        // near the village and on the beach the ground stays clear
        const vx = px > VILLAGE.x0 - 40 && px < VILLAGE.x1 + 40 && sdf > -170;
        if ((px - 72) ** 2 + (pz + 3) ** 2 < 81) continue;      // the player's arrival spot
        if (vx || (sdf > -45 && h < 4.5)) continue;
        let p = 0.002 + forest * 0.006;
        p += smoothstepJS(0.2, 0.34, slope) * 0.22;                     // crags
        p += smoothstepJS(96, 108, h) * smoothstepJS(0.08, 0.18, slope) * 0.12;
        p += smoothstepJS(-4, -8, eroded) * smoothstepJS(0.1, 0.2, slope) * 0.1;
        p += (sdf > -60 ? 0.05 : 0) * smoothstepJS(4, 9, h);              // rocky coast above the waves
        if (rnd() > p) continue;
        const s = 0.35 + rnd() ** 2.2 * 2.4;
        const sunk = s * 0.25;
        out.push({ x: px, z: pz, y: h - sunk, s, yaw: rnd() * Math.PI * 2, v: Math.floor(rnd() * variants), nx: n.x, nz: n.z });
        if (s > 0.8) col.addCylinder({ x: px, z: pz, y0: h - 1, y1: h + s * 0.6, r: s * 0.75 });
      }
    }
    return out;
  }

  prime(on) {
    this.primed = on;
    if (!on) { this.lastX = undefined; return; }
    for (const e of this.sets) {
      for (const m of [e.lod0, e.lod1]) { m.visible = true; m.count = Math.max(m.count, 1); m.userData.data.setXYZW(0, 0, 0, 0, 1); m.userData.data.needsUpdate = true; }
    }
  }

  update(camera) {
    if (this.primed) return;
    const cx = camera.position.x, cz = camera.position.z;
    if (this.lastX !== undefined && Math.hypot(cx - this.lastX, cz - this.lastZ) < 2) return;
    this.lastX = cx; this.lastZ = cz;
    if (!this.matrices) {
      // the stones never move: compose their matrices once
      const m4 = new THREE.Matrix4(), q = new THREE.Quaternion(), qt = new THREE.Quaternion(), sc = new THREE.Vector3(), p = new THREE.Vector3();
      const up = new THREE.Vector3(0, 1, 0), nrm = new THREE.Vector3();
      for (const o of this.list) {
        // sit the stone on the slope: yaw, then half-way toward the ground normal
        nrm.set(o.nx * 0.5, 1, o.nz * 0.5).normalize();
        qt.setFromUnitVectors(up, nrm);
        q.setFromAxisAngle(up, o.yaw).premultiply(qt);
        sc.setScalar(o.s); p.set(o.x, o.y, o.z);
        o.m = new Float32Array(m4.compose(p, q, sc).elements);
      }
      this.matrices = true;
    }
    for (const e of this.sets) {
      let n0 = 0, n1 = 0;
      for (const o of e.list) {
        const d = Math.hypot(o.x - cx, o.z - cz);
        if (d > FAR) continue;
        const f0 = 1 - smoothstepJS(NEAR * 0.85, NEAR * 1.15, d);
        const f1 = (1 - f0) * (1 - smoothstepJS(FAR * 0.85, FAR, d));
        if (f0 > 0.001) { e.lod0.instanceMatrix.array.set(o.m, n0 * 16); e.lod0.userData.data.setXYZW(n0, 0, 0, 0, f0); n0++; }
        if (f1 > 0.001) { e.lod1.instanceMatrix.array.set(o.m, n1 * 16); e.lod1.userData.data.setXYZW(n1, 0, 0, f0, f0 + f1); n1++; }
      }
      for (const [m, n] of [[e.lod0, n0], [e.lod1, n1]]) { m.count = n; m.visible = n > 0; uploadFirst(m.instanceMatrix, n); uploadFirst(m.userData.data, n); }
    }
  }
}
