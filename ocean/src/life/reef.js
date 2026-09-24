// The coral reef off the south-west of the bay: branching and table corals,
// brain corals, sea fans and whips that sway in the surge, sponges, seagrass
// meadows and rocks, spread over the reef mounds in the terrain.
//
// Each type is one instanced mesh with per-instance colour/phase; swaying
// parts move with the wave surge (a horizontal oscillation that fades with
// depth) in the vertex shader. Colours are true colours; the water column
// makes them blue-green at depth and the flashlight brings them back.

import * as THREE from 'three/webgpu';
import {
  attribute, positionGeometry, positionLocal, positionWorld, vec2, vec3, float, sin, cos, mix, smoothstep, clamp,
  max, normalWorld, abs, exp, fract,
} from 'three/tsl';
import { mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';
import { standard } from '../render/materials.js';
import { fbm2, vnoise2, voronoi2, gnoise2 } from '../render/tslnoise.js';
import { env } from '../env.js';

const rnd = ((a) => () => { a |= 0; a = a + 0x6D2B79F5 | 0; let t = Math.imul(a ^ a >>> 15, 1 | a); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; })(4242);

function clean(g) {
  const q = g.index ? g.toNonIndexed() : g;
  for (const k of Object.keys(q.attributes)) if (!['position', 'normal', 'uv'].includes(k)) q.deleteAttribute(k);
  if (!q.attributes.uv) q.setAttribute('uv', new THREE.BufferAttribute(new Float32Array(q.attributes.position.count * 2), 2));
  q.computeVertexNormals();
  return q;
}

function branching() {
  // staghorn: recursive forking tubes
  const parts = [];
  const grow = (p, dir, len, r, depth) => {
    const end = p.clone().addScaledVector(dir, len);
    const g = new THREE.CylinderGeometry(r * 0.7, r, len, 6, 1);
    g.translate(0, len / 2, 0);
    g.applyQuaternion(new THREE.Quaternion().setFromUnitVectors(new THREE.Vector3(0, 1, 0), dir));
    g.translate(p.x, p.y, p.z);
    parts.push(clean(g));
    if (depth === 0) { parts.push(clean(new THREE.SphereGeometry(r * 0.75, 6, 4).translate(end.x, end.y, end.z))); return; }
    const n = 2 + (rnd() < 0.4 ? 1 : 0);
    for (let k = 0; k < n; k++) {
      const d2 = dir.clone().add(new THREE.Vector3((rnd() - 0.5) * 1.2, rnd() * 0.3, (rnd() - 0.5) * 1.2)).normalize();
      grow(end, d2, len * (0.7 + rnd() * 0.2), r * 0.75, depth - 1);
    }
  };
  for (let k = 0; k < 5; k++) grow(new THREE.Vector3((rnd() - 0.5) * 0.3, 0, (rnd() - 0.5) * 0.3), new THREE.Vector3((rnd() - 0.5) * 0.8, 1, (rnd() - 0.5) * 0.8).normalize(), 0.18, 0.035, 3);
  return mergeGeometries(parts);
}

function brain() {
  const g = new THREE.SphereGeometry(0.5, 32, 16, 0, Math.PI * 2, 0, Math.PI / 2);
  g.scale(1, 0.62, 1);
  return clean(g);
}

function table() {
  const top = new THREE.CylinderGeometry(0.8, 0.7, 0.07, 18, 1).translate(0, 0.42, 0);
  const p = top.attributes.position;
  for (let i = 0; i < p.count; i++) { const x = p.getX(i), z = p.getZ(i); const r = Math.hypot(x, z); p.setY(i, p.getY(i) + Math.sin(Math.atan2(z, x) * 5) * 0.03 * r); }
  const stalk = new THREE.CylinderGeometry(0.08, 0.14, 0.42, 8).translate(0, 0.21, 0);
  return mergeGeometries([clean(top), clean(stalk)]);
}

function fan() {
  // a flat, lacy fan (alpha-cut in the shader) on a short stalk
  const g = new THREE.CircleGeometry(0.55, 24, 0, Math.PI).translate(0, 0.08, 0);
  const s = new THREE.CylinderGeometry(0.015, 0.02, 0.12, 5).translate(0, 0.06, 0);
  return mergeGeometries([clean(g), clean(s)]);
}

function whip() {
  const parts = [];
  for (let k = 0; k < 7; k++) {
    const a = rnd() * 6.28, h = 0.4 + rnd() * 0.6;
    const g = new THREE.CylinderGeometry(0.006, 0.012, h, 4, 6).translate(0, h / 2, 0).rotateZ((rnd() - 0.5) * 0.4).rotateY(a).translate(Math.cos(a) * 0.05, 0, Math.sin(a) * 0.05);
    parts.push(clean(g));
  }
  return mergeGeometries(parts);
}

function sponge() {
  const parts = [];
  for (let k = 0; k < 4; k++) {
    const h = 0.25 + rnd() * 0.35, r = 0.06 + rnd() * 0.05;
    const g = new THREE.CylinderGeometry(r, r * 1.2, h, 10, 1, true).translate((rnd() - 0.5) * 0.25, h / 2, (rnd() - 0.5) * 0.25);
    parts.push(clean(g));
  }
  return mergeGeometries(parts);
}

function grassTuft() {
  const parts = [];
  for (let k = 0; k < 14; k++) {
    const h = 0.25 + rnd() * 0.45, a = rnd() * 6.28;
    const g = new THREE.PlaneGeometry(0.018, h, 1, 4).translate(0, h / 2, 0).rotateY(a).translate((rnd() - 0.5) * 0.3, 0, (rnd() - 0.5) * 0.3);
    parts.push(clean(g));
  }
  return mergeGeometries(parts);
}

function rock() {
  const g = new THREE.IcosahedronGeometry(0.5, 2);
  const p = g.attributes.position;
  const sx = 0.8 + rnd() * 0.8, sy = 0.4 + rnd() * 0.4, sz = 0.8 + rnd() * 0.6;
  for (let i = 0; i < p.count; i++) {
    const x = p.getX(i), y = p.getY(i), z = p.getZ(i);
    const n = 1 + 0.2 * Math.sin(x * 5.1) * Math.cos(z * 4.3) + 0.1 * Math.sin(y * 9 + x * 3);
    p.setXYZ(i, x * sx * n, y * sy * n, z * sz * n);
  }
  return clean(g);
}

// true colours of the reef (bright under the torch, blue-green at depth)
const PALETTE = {
  branching: [[0.62, 0.5, 0.3], [0.55, 0.35, 0.45], [0.7, 0.62, 0.4]],
  brain: [[0.6, 0.52, 0.28], [0.45, 0.55, 0.32], [0.58, 0.38, 0.3]],
  table: [[0.55, 0.52, 0.4], [0.42, 0.5, 0.45]],
  fan: [[0.55, 0.15, 0.4], [0.75, 0.45, 0.12], [0.6, 0.2, 0.2]],
  whip: [[0.8, 0.5, 0.15], [0.7, 0.22, 0.3]],
  sponge: [[0.8, 0.45, 0.1], [0.5, 0.2, 0.45], [0.8, 0.7, 0.2]],
  grass: [[0.25, 0.38, 0.15], [0.3, 0.42, 0.18]],
  rock: [[0.36, 0.35, 0.32], [0.3, 0.31, 0.3]],
};

export class Reef {
  constructor({ scene, island, reef, collision }) {
    this.group = new THREE.Group();
    this.group.name = 'reef';
    scene.add(this.group);
    const types = {
      branching: { geo: branching(), n: 140, depth: [1.8, 9], sway: 0, scale: [0.7, 1.4], rough: 0.7 },
      brain: { geo: brain(), n: 60, depth: [1.8, 10], sway: 0, scale: [0.5, 1.6], rough: 0.8, brain: true },
      table: { geo: table(), n: 45, depth: [2.5, 11], sway: 0, scale: [0.6, 1.4], rough: 0.75 },
      fan: { geo: fan(), n: 90, depth: [2.2, 12], sway: 0.18, scale: [0.6, 1.3], rough: 0.8, lace: true },
      whip: { geo: whip(), n: 80, depth: [2, 12], sway: 0.25, scale: [0.7, 1.5], rough: 0.7 },
      sponge: { geo: sponge(), n: 70, depth: [2.5, 12], sway: 0, scale: [0.7, 1.5], rough: 0.85 },
      grass: { geo: grassTuft(), n: 700, depth: [1.0, 6], sway: 0.35, scale: [0.8, 1.5], rough: 0.7, grass: true },
      rock: { geo: rock(), n: 90, depth: [1.2, 14], sway: 0, scale: [0.6, 2.4], rough: 0.9 },
    };
    for (const [name, t] of Object.entries(types)) {
      const list = [];
      for (let k = 0; k < t.n * 30 && list.length < t.n; k++) {
        // grass meadows sit on the sandy flats around the reef, the rest on the mounds
        const a = rnd() * Math.PI * 2;
        const r = Math.sqrt(rnd()) * reef.r * (t.grass ? 1.7 : 1.15);
        const x = reef.x + Math.cos(a) * r, z = reef.z + Math.sin(a) * r;
        const h = island.heightAt(x, z);
        if (-h < t.depth[0] || -h > t.depth[1]) continue;
        // spread out: cluster by a noise mask so there are open sandy gaps
        const m = Math.sin(x * 0.11) * Math.cos(z * 0.13) + Math.sin(x * 0.037 + z * 0.041) * 0.7;
        if (!t.grass && m < -0.35 && rnd() < 0.8) continue;
        if (t.grass && m > 0.3) continue;
        list.push({ x, z, y: h - 0.05, yaw: rnd() * 6.28, s: t.scale[0] + rnd() * (t.scale[1] - t.scale[0]), c: rnd() });
      }
      if (!list.length) continue;
      const data = new THREE.InstancedBufferAttribute(new Float32Array(list.length * 4), 4);
      const pal = PALETTE[name];
      list.forEach((o, i) => { const col = pal[Math.floor(o.c * pal.length)]; data.setXYZW(i, col[0] * (0.85 + rnd() * 0.3), col[1] * (0.85 + rnd() * 0.3), col[2] * (0.85 + rnd() * 0.3), rnd() * 6.28); });
      t.geo.setAttribute('coral', data);
      const mat = standard({ roughness: t.rough, metalness: 0, side: (t.lace || t.grass) ? THREE.DoubleSide : THREE.FrontSide });
      const cd = attribute('coral', 'vec4');
      const p = positionGeometry;
      if (t.sway) {
        // surge: horizontal back-and-forth growing with height above the base
        const surge = sin(env.time.mul(0.9).add(cd.w)).mul(t.sway).mul(p.y.max(0).mul(p.y.max(0)).mul(2.5));
        mat.positionNode = vec3(p.x.add(surge.mul(0.7)), p.y, p.z.add(surge.mul(0.5)));
      }
      let col = cd.rgb;
      if (t.brain) {
        // meandering grooves
        const v = voronoi2(positionLocal.xz.mul(9).add(positionLocal.y.mul(4)));
        const groove = smoothstep(0.04, 0.12, v.y.sub(v.x));
        col = col.mul(mix(float(0.55), float(1.05), groove));
      }
      if (t.lace) {
        const q = positionLocal.xy.mul(34);
        const cells = voronoi2(q);
        mat.opacityNode = smoothstep(0.1, 0.06, cells.y.sub(cells.x)).add(smoothstep(0.05, 0.03, positionLocal.y.sub(0.08)));
        mat.alphaTest = 0.5;
        mat.userData.noAO = true;
      }
      // polyps / grain
      col = col.mul(vnoise2(positionLocal.xz.mul(40).add(positionLocal.y.mul(30))).mul(0.25).add(0.85));
      mat.colorNode = col;
      const mesh = new THREE.InstancedMesh(t.geo, mat, list.length);
      const m4 = new THREE.Matrix4(), q = new THREE.Quaternion(), s = new THREE.Vector3(), pos = new THREE.Vector3();
      list.forEach((o, i) => {
        q.setFromAxisAngle(new THREE.Vector3(0, 1, 0), o.yaw);
        s.setScalar(o.s);
        pos.set(o.x, o.y, o.z);
        mesh.setMatrixAt(i, m4.compose(pos, q, s));
        if (name === 'rock' && o.s > 1.4 && collision) collision.addCylinder({ x: o.x, z: o.z, y0: o.y - 1, y1: o.y + o.s * 0.35, r: o.s * 0.5 });
      });
      mesh.castShadow = name !== 'grass';
      mesh.receiveShadow = true;
      mesh.name = `reef.${name}`;
      this.group.add(mesh);
    }
  }
}
