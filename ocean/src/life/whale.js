// A humpback whale that cruises the outer bay, surfaces to blow, shows its
// flukes as it dives, and now and then breaches.
//
// Model: lofted body (flat-topped rostrum, throat pleats, dorsal hump + fin),
// long pectoral flippers with a knobbly leading edge, swept flukes with a
// notch and a ragged trailing edge. Animation in the vertex shader: a vertical
// body wave that grows toward the flukes (the fluke stroke), flipper strokes.
// Skin: matte countershading, tubercles on the head, barnacle patches, scars.

import * as THREE from 'three/webgpu';
import {
  attribute, positionGeometry, normalGeometry, vec2, vec3, vec4, float, sin, cos, mix, smoothstep, clamp, max, abs,
  uniform, normalize, varying, fract, floor, dot, length, select, pow, positionWorld, cameraViewMatrix, transformNormalToView,
} from 'three/tsl';
import { mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';
import { standard } from '../render/materials.js';
import { fbm2, vnoise2, voronoi2, hash21, gnoise2 } from '../render/tslnoise.js';
import { env } from '../env.js';

const L = 13;

function lerpTable(tab, t) {
  for (let i = 0; i < tab.length - 1; i++) {
    const [t0, v0] = tab[i], [t1, v1] = tab[i + 1];
    if (t <= t1) { const u = (t - t0) / (t1 - t0); const s = u * u * (3 - 2 * u); return v0 + (v1 - v0) * s; }
  }
  return tab[tab.length - 1][1];
}
const W_TAB = [[0, 0.08], [0.04, 0.55], [0.12, 1.05], [0.26, 1.5], [0.45, 1.45], [0.62, 1.0], [0.8, 0.42], [0.92, 0.2], [1, 0.12]];
const H_TAB = [[0, 0.1], [0.04, 0.5], [0.12, 0.95], [0.26, 1.3], [0.45, 1.42], [0.62, 1.12], [0.8, 0.62], [0.92, 0.34], [1, 0.16]];

function withAttrs(g, t, part) {
  const n = g.attributes.position.count;
  const tt = new Float32Array(n), pp = new Float32Array(n);
  const pos = g.attributes.position;
  for (let i = 0; i < n; i++) { tt[i] = typeof t === 'function' ? t(pos.getX(i), pos.getY(i), pos.getZ(i)) : t; pp[i] = part; }
  g.setAttribute('bodyT', new THREE.BufferAttribute(tt, 1));
  g.setAttribute('part', new THREE.BufferAttribute(pp, 1));
  if (!g.attributes.uv) g.setAttribute('uv', new THREE.BufferAttribute(new Float32Array(n * 2), 2));
  return g;
}

function bodyGeometry() {
  const NX = 64, NR = 28;
  const pos = [], idx = [], uvs = [];
  for (let i = 0; i <= NX; i++) {
    const t = i / NX;
    const w = lerpTable(W_TAB, t) / 2, h = lerpTable(H_TAB, t) / 2;
    const x = (0.5 - t) * L;
    // the belly sags a little forward (throat), the back rises into a hump near the dorsal fin
    const drop = -0.18 * Math.exp(-(((t - 0.28) / 0.18) ** 2));
    const hump = 0.12 * Math.exp(-(((t - 0.6) / 0.05) ** 2));
    for (let j = 0; j <= NR; j++) {
      const a = j / NR * Math.PI * 2;
      const sa = Math.sin(a), ca = Math.cos(a);
      // flatter top on the rostrum, flatter belly behind the throat
      const top = sa > 0 ? Math.pow(sa, t < 0.14 ? 0.7 : 0.95) : -Math.pow(-sa, 0.85);
      let y = top * h + (sa < 0 ? drop * (-sa) : hump * Math.max(sa, 0) * Math.max(0, 1 - Math.abs(ca) * 3));
      const z = ca * w * (sa < 0 ? 1.02 : 0.96);
      pos.push(x, y, z);
      uvs.push(t, j / NR);
    }
  }
  for (let i = 0; i < NX; i++) for (let j = 0; j < NR; j++) {
    const a = i * (NR + 1) + j, b = a + 1, c = a + NR + 1, d = c + 1;
    idx.push(a, c, b, b, c, d);
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  g.setAttribute('uv', new THREE.Float32BufferAttribute(uvs, 2));
  g.setIndex(idx);
  g.computeVertexNormals();
  return withAttrs(g.toNonIndexed(), (x) => 0.5 - x / L, 0);
}

function flipperGeometry(side) {
  // long, narrow wing with scalloped leading edge; root at the body side, t ~0.27
  const len = 4.2, NS = 32, NC = 8;
  const pos = [], idx = [];
  for (let i = 0; i <= NS; i++) {
    const s = i / NS;
    const chord = 0.9 * (1 - s * 0.72) * (0.75 + 0.25 * Math.sin(Math.PI * Math.min(1, s * 3)));
    const bump = Math.pow(Math.abs(Math.sin(s * Math.PI * 9)), 3) * 0.07 * (1 - s * 0.6);
    const thick = 0.14 * (1 - s * 0.75);
    const sweep = s * s * 1.2;
    for (let j = 0; j <= NC; j++) {
      const a = j / NC * Math.PI * 2;
      const u = (1 - Math.cos(a)) / 2;                // 0 leading .. 1 trailing .. back
      const lead = u < 0.15 ? bump : 0;
      pos.push(-sweep - u * chord - lead * 0.5 + 0.2, Math.sin(a) * thick * Math.sqrt(Math.max(1 - (2 * u - 1) ** 2, 0.04)), side * (0.45 + s * len));
    }
  }
  for (let i = 0; i < NS; i++) for (let j = 0; j < NC; j++) {
    const a = i * (NC + 1) + j, b = a + 1, c = a + NC + 1, d = c + 1;
    if (side > 0) idx.push(a, b, c, b, d, c); else idx.push(a, c, b, b, c, d);
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  g.setIndex(idx);
  g.computeVertexNormals();
  // tilt down and back, place at the root
  g.rotateX(side * 0.35).translate((0.5 - 0.27) * L, -0.45, side * 0.55);
  return withAttrs(g.toNonIndexed(), 0.27, side > 0 ? 2 : 1);
}

function flukeGeometry() {
  const span = 2.1, NS = 24;
  const shape = new THREE.Shape();
  shape.moveTo(0, 0);
  for (let i = 0; i <= NS; i++) {
    const s = i / NS;
    shape.lineTo(-0.2 - s * s * 1.1, s * span);     // leading edge, swept back
  }
  for (let i = NS; i >= 0; i--) {
    const s = i / NS;
    const rag = Math.abs(Math.sin(s * 37)) * 0.06 * s;
    shape.lineTo(-0.2 - s * s * 1.1 - (0.55 + 0.35 * Math.sin(Math.PI * s)) * (1 - s * 0.4) - rag + (s < 0.08 ? 0.2 : 0), s * span);
  }
  const g1 = new THREE.ExtrudeGeometry(shape, { depth: 0.08, bevelEnabled: true, bevelThickness: 0.04, bevelSize: 0.04, bevelSegments: 2, curveSegments: 4 });
  g1.translate(0, 0, -0.04).rotateX(-Math.PI / 2);
  const g2 = g1.clone().scale(1, 1, -1);
  const ix = g2.index ? g2.index.array : null;
  if (ix) for (let i = 0; i < ix.length; i += 3) { const t = ix[i + 1]; ix[i + 1] = ix[i + 2]; ix[i + 2] = t; }
  g2.computeVertexNormals();
  const g = mergeGeometries([g1.toNonIndexed(), g2.index ? g2.toNonIndexed() : g2]);
  for (const k of Object.keys(g.attributes)) if (!['position', 'normal', 'uv'].includes(k)) g.deleteAttribute(k);
  g.translate(-0.5 * L + 0.15, 0, 0);
  return withAttrs(g, (x) => 0.5 - x / L, 3);
}

function dorsalGeometry() {
  const shape = new THREE.Shape([new THREE.Vector2(0.35, 0), new THREE.Vector2(-0.1, 0.32), new THREE.Vector2(-0.35, 0.36), new THREE.Vector2(-0.45, 0)]);
  const g = new THREE.ExtrudeGeometry(shape, { depth: 0.12, bevelEnabled: true, bevelThickness: 0.05, bevelSize: 0.05, bevelSegments: 2 });
  g.translate(0, 0, -0.06).translate((0.5 - 0.64) * L, 0.52, 0);
  const q = g.toNonIndexed();
  for (const k of Object.keys(q.attributes)) if (!['position', 'normal', 'uv'].includes(k)) q.deleteAttribute(k);
  return withAttrs(q, 0.64, 0);
}

export class Whale {
  constructor({ scene, spray = null, ocean = null }) {
    this.spray = spray;
    this.ocean = ocean;
    const parts = [bodyGeometry(), flipperGeometry(1), flipperGeometry(-1), flukeGeometry(), dorsalGeometry()];
    const clean = parts.map((g) => { for (const k of Object.keys(g.attributes)) if (!['position', 'normal', 'uv', 'bodyT', 'part'].includes(k)) g.deleteAttribute(k); return g; });
    this.geometry = mergeGeometries(clean);
    this.phase = uniform(0);        // fluke stroke phase (rad)
    this.stroke = uniform(0.5);     // stroke amplitude scale
    this.flip = uniform(0);         // flipper angle
    this.arch = uniform(0);         // back arch while diving
    this.wet = uniform(1);
    this.mesh = new THREE.Mesh(this.geometry, this._material());
    this.mesh.castShadow = true;
    this.mesh.receiveShadow = true;
    this.mesh.frustumCulled = false;
    this.mesh.name = 'whale';
    scene.add(this.mesh);
    // behaviour
    this.route = [];
    for (let k = 0; k < 10; k++) {
      const a = -0.9 + k / 10 * 1.8;
      this.route.push(new THREE.Vector3(Math.sin(a) * 520, 0, -300 + Math.cos(a) * 520 + 90 * Math.sin(k * 2.1)));
    }
    this.pos = this.route[0].clone(); this.pos.y = -9;
    this.heading = 0;
    this.pitch = 0; this.roll = 0;
    this.speed = 2.2;
    this.state = 'cruise'; this.stateT = 0;
    this.nextBreath = 25; this.nextBreach = 70;
    this.wp = 1;
    this.events = [];
  }

  _material() {
    const m = standard({ roughness: 0.62, metalness: 0 });
    const tAttr = attribute('bodyT', 'float'), part = attribute('part', 'float');
    const g = positionGeometry;
    // --- deformation: vertical travelling wave from mid-body to the flukes
    const t = tAttr;
    const amp = smoothstep(0.35, 1.05, t).pow(1.6).mul(0.85).mul(this.stroke);
    const wave = sin(this.phase.sub(t.mul(3.2)));
    const dy = amp.mul(wave).add(this.arch.mul(t.sub(0.5).mul(t.sub(0.5))).mul(-3.0));
    // flipper stroke: rotate about the body's long axis at the root
    const isFlip = part.greaterThan(0.5).and(part.lessThan(2.5));
    const side = select(part.greaterThan(1.5), float(1), float(-1));
    const ang = this.flip.mul(side);
    const rootZ = side.mul(0.55), rootY = float(-0.45);
    const ry = g.y.sub(rootY), rz = g.z.sub(rootZ);
    const fy = ry.mul(cos(ang)).sub(rz.mul(sin(ang))).add(rootY);
    const fz = ry.mul(sin(ang)).add(rz.mul(cos(ang))).add(rootZ);
    const py = select(isFlip, fy, g.y).add(dy);
    const pz = select(isFlip, fz, g.z);
    m.positionNode = vec3(g.x, py, pz);
    // bend the normal with the local wave slope (d(dy)/dx)
    const slope = amp.mul(cos(this.phase.sub(t.mul(3.2)))).mul(3.2 / L);
    const n = normalGeometry;
    const nf = normalize(vec3(n.x.add(n.y.mul(slope)), n.y, n.z));
    m.normalNode = transformNormalToView(nf);

    // --- skin
    const vT = varying(t, 'vWhaleT');
    const vP = varying(vec3(g.x, py, pz), 'vWhaleP');
    const vPart = varying(part, 'vWhalePart');
    const up = normalize(vP.sub(vec3(vP.x, -0.1, 0))).y;             // around the body: +1 back, -1 belly
    const mottle = fbm2(vec2(vP.x.mul(0.8), vP.z.mul(0.8).add(vP.y)), 4).mul(0.5).add(0.5);
    const back = vec3(0.045, 0.05, 0.058).mul(mix(0.75, 1.3, mottle));
    const belly = vec3(0.72, 0.72, 0.7).mul(mix(0.8, 1.05, mottle));
    // white belly with irregular boundary, white flipper undersides/most of the flipper
    const edge = smoothstep(-0.25, 0.15, up.add(fbm2(vP.xz.mul(0.9), 3).mul(0.35)));
    let col = mix(belly, back, edge);
    const flipperWhite = select(vPart.greaterThan(0.5).and(vPart.lessThan(2.5)), smoothstep(0.6, -0.2, up).mul(0.85).add(0.1), float(0));
    col = mix(col, belly, flipperWhite);
    // throat pleats: dark grooves on the white throat
    const pleat = smoothstep(0.75, 0.95, sin(vP.z.mul(24)).mul(0.5).add(0.5)).mul(smoothstep(0.05, 0.12, vT)).mul(smoothstep(0.48, 0.38, vT)).mul(smoothstep(0.1, -0.35, up));
    col = col.mul(float(1).sub(pleat.mul(0.45)));
    // barnacle clusters (chin, flipper edges, fluke) and tubercle knobs on the rostrum
    const cells = voronoi2(vec2(vP.x.mul(6), vP.z.mul(6).add(vP.y.mul(4))));
    const barnZone = smoothstep(0.62, 0.8, fbm2(vec2(vP.x.mul(0.6), vP.z.mul(0.6).add(vP.y)), 3).mul(0.5).add(0.5)).mul(select(vPart.greaterThan(2.5), float(0.7), float(1)));
    const barn = smoothstep(0.3, 0.12, cells.x).mul(barnZone);
    col = mix(col, vec3(0.58, 0.56, 0.5), barn);
    const knobs = smoothstep(0.25, 0.08, voronoi2(vP.xz.mul(2.2)).x).mul(smoothstep(0.16, 0.02, vT)).mul(smoothstep(-0.1, 0.4, up));
    col = mix(col, back.mul(1.6), knobs.mul(0.6));
    // scars: thin pale scratches
    const sc = smoothstep(0.985, 1.0, sin(vP.x.mul(3.1).add(vP.z.mul(9.7)).add(fbm2(vP.xz.mul(0.7), 2).mul(6))).mul(0.5).add(0.5)).mul(edge);
    col = mix(col, vec3(0.35, 0.36, 0.36), sc.mul(0.6));
    m.colorNode = col;
    // matte skin, a little sheen when wet at the surface
    m.roughnessNode = mix(float(0.72), float(0.42), this.wet).add(barn.mul(0.2));
    return m;
  }

  update(dt, time, focus) {
    if (dt <= 0) { this._pose(time); return; }
    const target = this.route[this.wp];
    const flat = new THREE.Vector3(target.x - this.pos.x, 0, target.z - this.pos.z);
    if (flat.length() < 40) this.wp = (this.wp + 1) % this.route.length;
    const want = Math.atan2(flat.x, -flat.z);
    const dh = Math.atan2(Math.sin(want - this.heading), Math.cos(want - this.heading));
    this.heading += THREE.MathUtils.clamp(dh, -0.08 * dt, 0.08 * dt);
    this.stateT += dt;
    this.nextBreath -= dt; this.nextBreach -= dt;
    let targetY = -9, spd = 2.2, strokeRate = 0.55, stroke = 0.45, arch = 0, pitchWant = 0;
    const s = this.state;
    if (s === 'cruise') {
      if (this.nextBreach <= 0) { this.state = 'breachDive'; this.stateT = 0; }
      else if (this.nextBreath <= 0) { this.state = 'surface'; this.stateT = 0; }
    } else if (s === 'surface') {
      targetY = -0.9; spd = 1.8; stroke = 0.3; strokeRate = 0.4;
      if (this.pos.y > -1.4 && !this.blown) { this.blown = true; this._blow(); }
      if (this.stateT > 14) { this.state = 'dive'; this.stateT = 0; this.blown = false; }
    } else if (s === 'dive') {
      // arch the back, raise the flukes, slide under
      arch = Math.min(this.stateT / 3, 1) * 0.9; pitchWant = -0.35 * Math.min(this.stateT / 2.5, 1);
      targetY = -14; spd = 2.4; stroke = 0.35;
      if (this.stateT > 9) { this.state = 'cruise'; this.stateT = 0; this.nextBreath = 35 + Math.random() * 30; }
    } else if (s === 'breachDive') {
      targetY = -16; spd = 2.6;
      if (this.stateT > 6) { this.state = 'breach'; this.stateT = 0; this.vy = 0; }
    } else if (s === 'breach') {
      // power up and out of the water, twist, fall back on the side
      stroke = 1.1; strokeRate = 1.5;
      if (this.stateT < 3.2) { this.vy = Math.min((this.vy || 0) + dt * 5.2, 9.5); pitchWant = 1.15; }
      else this.vy -= 9.81 * dt;
      this.pos.y += this.vy * dt;
      this.roll += dt * (this.stateT > 3 ? 0.9 : 0.15);
      if (this.pos.y > 0.5 && !this.launched) { this.launched = true; this._splash(0.6); }
      if (this.launched && this.pos.y < 0.2 && this.vy < 0) { this._splash(1.6); this.state = 'recover'; this.stateT = 0; this.launched = false; }
    } else if (s === 'recover') {
      targetY = -7; stroke = 0.4; spd = 1.6;
      this.roll *= Math.exp(-dt * 0.6);
      if (this.stateT > 12) { this.state = 'cruise'; this.nextBreach = 120 + Math.random() * 90; this.nextBreath = 30; this.roll = 0; }
    }
    if (s !== 'breach') {
      this.pos.y += (targetY - this.pos.y) * (1 - Math.exp(-dt * 0.25));
      pitchWant += THREE.MathUtils.clamp((targetY - this.pos.y) * 0.04, -0.3, 0.3);
      this.vy = 0;
    }
    this.pitch += (pitchWant - this.pitch) * (1 - Math.exp(-dt * 1.2));
    this.speed += (spd - this.speed) * (1 - Math.exp(-dt * 0.4));
    const fwd = new THREE.Vector3(Math.sin(this.heading), 0, -Math.cos(this.heading));
    this.pos.addScaledVector(fwd, this.speed * dt * Math.cos(this.pitch));
    this.phase.value += dt * strokeRate * 2 * Math.PI * 0.25;
    this.stroke.value += (stroke - this.stroke.value) * (1 - Math.exp(-dt));
    this.arch.value += (arch - this.arch.value) * (1 - Math.exp(-dt * 1.5));
    this.flip.value = Math.sin(time * 0.35) * 0.18 + (s === 'breach' ? Math.sin(time * 2.1) * 0.6 : 0);
    this.wet.value = THREE.MathUtils.clamp(this.pos.y + 1.2, 0, 1);
    this._pose(time);
  }

  _pose() {
    this.mesh.position.copy(this.pos);
    // local +x is the head: yaw so +x points along the heading
    const q = new THREE.Quaternion().setFromEuler(new THREE.Euler(this.roll, -this.heading + Math.PI / 2, this.pitch, 'YZX'));
    this.mesh.quaternion.copy(q);
  }

  _blow() {
    if (!this.spray) return;
    const head = new THREE.Vector3(L * 0.33, 0.6, 0).applyQuaternion(this.mesh.quaternion).add(this.pos);
    head.y = Math.max(head.y, 0.3);
    this.spray.emit({ position: head, velocity: new THREE.Vector3(0, 7.5, 0), count: 260, spread: 1.1, size: 0.05, life: 3.2, mist: 0.75, radius: 0.35 });
    this.events.push({ type: 'blow', pos: head.clone() });
  }

  _splash(k) {
    if (!this.spray) return;
    const p = this.pos.clone(); p.y = 0.2;
    for (let i = 0; i < 6; i++) {
      const a = i / 6 * Math.PI * 2;
      const dir = new THREE.Vector3(Math.cos(a) * 3.5 * k, (6 + Math.random() * 4) * k, Math.sin(a) * 3.5 * k);
      this.spray.emit({ position: p.clone().add(new THREE.Vector3(Math.cos(a) * 2.5, 0, Math.sin(a) * 2.5)), velocity: dir, count: 220 * k, spread: 2.6 * k, size: 0.06, life: 2.5, mist: 0.45, radius: 2.5 });
    }
    this.events.push({ type: 'splash', pos: p.clone(), strength: k });
    if (this.ocean && this.ocean.addFoamBlob) this.ocean.addFoamBlob(p.x, p.z, 7 * k + 3);
  }
}
