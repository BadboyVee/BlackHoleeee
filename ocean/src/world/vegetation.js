// Vegetation: coconut palms on the berm, broadleaf trees and pines inland,
// shrubs, and a carpet of grass blades around the eye.
//
// Trees are procedural (curved, ringed palm trunks with drooping fronds;
// branching broadleaf and whorled pines with dense leaf-cluster cards drawn
// on canvas). Every species has a few variants, each drawn as two instanced
// LODs; instances cross-fade between them with a 4x4 Bayer dither so there is
// no pop. Wind bends trunks by height and makes leaves flutter; leaves are
// matte and let backlight through.

import * as THREE from 'three/webgpu';
import {
  Fn, attribute, positionLocal, positionWorld, vec2, vec3, vec4, float, sin, cos, mix, smoothstep, clamp, max,
  dot, normalize, screenCoordinate, floor, fract, uniform, Discard, If, texture, uv, cameraPosition, pow, instanceIndex,
  instancedArray, uint, int, select, length, abs, mod,
} from 'three/tsl';
import { mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';
import { standard } from '../render/materials.js';
import { fbm2, vnoise2, hash21 } from '../render/tslnoise.js';
import { env } from '../env.js';
import { VILLAGE } from './island.js';

const rndGen = (seed) => () => { seed |= 0; seed = seed + 0x6D2B79F5 | 0; let t = Math.imul(seed ^ seed >>> 15, 1 | seed); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; };

// ------------------------------------------------------------------ textures
function canvasTex(w, h, draw) {
  const c = document.createElement('canvas');
  c.width = w; c.height = h;
  const g = c.getContext('2d');
  draw(g, w, h);
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace;
  t.generateMipmaps = true;
  t.minFilter = THREE.LinearMipmapLinearFilter;
  t.anisotropy = 4;
  return t;
}

function leafClusterTexture(seed, palette) {
  const rnd = rndGen(seed);
  return canvasTex(512, 512, (g, W, H) => {
    g.clearRect(0, 0, W, H);
    // twigs
    g.strokeStyle = 'rgba(70,52,34,1)'; g.lineWidth = 5;
    for (let k = 0; k < 6; k++) { g.beginPath(); g.moveTo(W / 2, H * 0.95); g.quadraticCurveTo(W / 2 + (rnd() - 0.5) * 200, H * 0.6, W * (0.15 + rnd() * 0.7), H * (0.1 + rnd() * 0.5)); g.stroke(); }
    // leaves: layered ellipses with a midrib, darker underneath
    for (let k = 0; k < 150; k++) {
      const a = rnd() * Math.PI * 2;
      const r = Math.sqrt(rnd()) * W * 0.42;
      const x = W / 2 + Math.cos(a) * r, y = H / 2 + Math.sin(a) * r * 0.9;
      const len = 26 + rnd() * 30, wid = len * (0.38 + rnd() * 0.18);
      const col = palette[Math.floor(rnd() * palette.length)];
      const shade = 0.7 + rnd() * 0.45;
      g.save(); g.translate(x, y); g.rotate(a + (rnd() - 0.5) * 1.4);
      g.fillStyle = `rgb(${col[0] * shade | 0},${col[1] * shade | 0},${col[2] * shade | 0})`;
      g.beginPath(); g.ellipse(0, 0, len / 2, wid / 2, 0, 0, Math.PI * 2); g.fill();
      g.strokeStyle = `rgba(${col[0] * 1.3 | 0},${col[1] * 1.3 | 0},${col[2] * 1.2 | 0},0.6)`; g.lineWidth = 1.2;
      g.beginPath(); g.moveTo(-len / 2, 0); g.lineTo(len / 2, 0); g.stroke();
      g.restore();
    }
  });
}

function frondTexture() {
  // palm frond card: rachis along x, leaflets angled forward on both sides
  return canvasTex(1024, 256, (g, W, H) => {
    g.clearRect(0, 0, W, H);
    const rnd = rndGen(91);
    for (let i = 0; i < 90; i++) {
      const x = 20 + i / 90 * (W - 40);
      const len = (H * 0.48) * Math.sin(Math.PI * Math.min(1, (i + 6) / 96)) * (0.85 + rnd() * 0.2);
      for (const s of [-1, 1]) {
        const shade = 0.75 + rnd() * 0.35;
        g.strokeStyle = `rgb(${(58 + rnd() * 20) * shade | 0},${(92 + rnd() * 30) * shade | 0},${(34 + rnd() * 14) * shade | 0})`;
        g.lineWidth = 4 + rnd() * 2;
        g.beginPath(); g.moveTo(x, H / 2);
        const ex = x + len * 0.55, ey = H / 2 + s * len;
        g.quadraticCurveTo(x + len * 0.15, H / 2 + s * len * 0.6, ex + (rnd() - 0.5) * 10, ey);
        g.stroke();
      }
    }
    g.strokeStyle = 'rgb(120,110,60)'; g.lineWidth = 6;
    g.beginPath(); g.moveTo(0, H / 2); g.lineTo(W, H / 2); g.stroke();
  });
}

function needleTexture() {
  return canvasTex(256, 256, (g, W, H) => {
    g.clearRect(0, 0, W, H);
    const rnd = rndGen(5);
    g.strokeStyle = 'rgb(70,55,40)'; g.lineWidth = 4;
    g.beginPath(); g.moveTo(W * 0.1, H / 2); g.lineTo(W * 0.95, H / 2); g.stroke();
    for (let i = 0; i < 260; i++) {
      const t = rnd();
      const x = W * (0.1 + t * 0.85), y = H / 2;
      const a = (rnd() - 0.5) * 2.4 + (rnd() < 0.5 ? Math.PI * 0.35 : -Math.PI * 0.35);
      const len = 30 + rnd() * 40 * (1 - t * 0.5);
      const sh = 0.7 + rnd() * 0.4;
      g.strokeStyle = `rgb(${34 * sh | 0},${70 * sh | 0},${40 * sh | 0})`; g.lineWidth = 1.6;
      g.beginPath(); g.moveTo(x, y); g.lineTo(x + Math.cos(a) * len, y + Math.sin(a) * len); g.stroke();
    }
  });
}

// ------------------------------------------------------------------ geometry
function tube(points, radii, radial = 8, ringBumps = 0) {
  const curve = new THREE.CatmullRomCurve3(points);
  const segs = Math.max(4, points.length * 4);
  const frames = curve.computeFrenetFrames(segs, false);
  const pos = [], idx = [], uvs = [];
  for (let i = 0; i <= segs; i++) {
    const t = i / segs;
    const p = curve.getPointAt(t);
    const r0 = radii(t);
    const r = ringBumps ? r0 * (1 + 0.06 * Math.pow(Math.abs(Math.sin(t * ringBumps * Math.PI)), 6)) : r0;
    const N = frames.normals[i], B = frames.binormals[i];
    for (let j = 0; j <= radial; j++) {
      const a = j / radial * Math.PI * 2;
      pos.push(p.x + (N.x * Math.cos(a) + B.x * Math.sin(a)) * r, p.y + (N.y * Math.cos(a) + B.y * Math.sin(a)) * r, p.z + (N.z * Math.cos(a) + B.z * Math.sin(a)) * r);
      uvs.push(j / radial, t);
    }
  }
  for (let i = 0; i < segs; i++) for (let j = 0; j < radial; j++) {
    const a = i * (radial + 1) + j, b = a + 1, c = a + radial + 1, d = c + 1;
    idx.push(a, c, b, b, c, d);
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  g.setAttribute('uv', new THREE.Float32BufferAttribute(uvs, 2));
  g.setIndex(idx);
  g.computeVertexNormals();
  return g;
}

// a bent quad strip (leaf card / frond) from a list of centre points and widths
function ribbon(points, width, up) {
  const pos = [], uvs = [], idx = [];
  const n = points.length;
  for (let i = 0; i < n; i++) {
    const p = points[i];
    const t = points[Math.min(i + 1, n - 1)].clone().sub(points[Math.max(i - 1, 0)]).normalize();
    const side = new THREE.Vector3().crossVectors(t, up).normalize().multiplyScalar(width(i / (n - 1)) / 2);
    pos.push(p.x - side.x, p.y - side.y, p.z - side.z, p.x + side.x, p.y + side.y, p.z + side.z);
    uvs.push(i / (n - 1), 0, i / (n - 1), 1);
  }
  for (let i = 0; i < n - 1; i++) { const a = i * 2; idx.push(a, a + 2, a + 1, a + 1, a + 2, a + 3); }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  g.setAttribute('uv', new THREE.Float32BufferAttribute(uvs, 2));
  g.setIndex(idx);
  g.computeVertexNormals();
  return g;
}

function card(center, size, rnd, face = null) {
  const g = new THREE.PlaneGeometry(size, size);
  const q = new THREE.Quaternion();
  if (face) q.setFromUnitVectors(new THREE.Vector3(0, 0, 1), face);
  else q.setFromEuler(new THREE.Euler(rnd() * Math.PI, rnd() * Math.PI * 2, rnd() * Math.PI));
  g.applyQuaternion(q).translate(center.x, center.y, center.z);
  // normals point away from the canopy centre (fake sphere normals: soft, even lighting)
  return g;
}

function sphereNormals(g, center, blend = 0.75) {
  const p = g.attributes.position, n = g.attributes.normal;
  const v = new THREE.Vector3(), nn = new THREE.Vector3();
  for (let i = 0; i < p.count; i++) {
    v.set(p.getX(i), p.getY(i), p.getZ(i)).sub(center).normalize();
    nn.set(n.getX(i), n.getY(i), n.getZ(i));
    nn.lerp(v, blend).normalize();
    n.setXYZ(i, nn.x, nn.y, nn.z);
  }
  return g;
}

function palmVariant(seed) {
  const rnd = rndGen(seed);
  const H = 6.5 + rnd() * 4.5;
  const lean = 0.08 + rnd() * 0.22, dir = rnd() * Math.PI * 2;
  const pts = [];
  for (let i = 0; i <= 8; i++) {
    const t = i / 8;
    const off = Math.sin(t * Math.PI * 0.55) * lean * H * t + t * t * 0.3;
    pts.push(new THREE.Vector3(Math.cos(dir) * off, t * H, Math.sin(dir) * off));
  }
  const trunk = tube(pts, (t) => 0.2 * (1 - t * 0.35) + 0.1 * Math.pow(1 - t, 8), 9, H / 0.13);
  const top = pts[pts.length - 1];
  const fronds = [];
  const nF = 14 + Math.floor(rnd() * 5);
  for (let k = 0; k < nF; k++) {
    const a = k / nF * Math.PI * 2 + rnd() * 0.3;
    const up0 = 0.35 + rnd() * 0.9 - (k % 3 === 0 ? 0.6 : 0);
    const len = 3.2 + rnd() * 1.4;
    const cp = [];
    for (let i = 0; i <= 10; i++) {
      const t = i / 10;
      const r = t * len;
      const y = up0 * r - 0.55 * r * r / len * (1.2 + rnd() * 0.1);
      cp.push(new THREE.Vector3(top.x + Math.cos(a) * r, top.y + y, top.z + Math.sin(a) * r));
    }
    const tang = new THREE.Vector3(Math.cos(a), 0, Math.sin(a));
    const upv = new THREE.Vector3().crossVectors(tang, new THREE.Vector3(0, 1, 0)).cross(tang).normalize().negate();
    fronds.push(ribbon(cp, (t) => 1.4 * Math.sin(Math.PI * Math.min(1, t * 1.05 + 0.05)) + 0.1, upv.lerp(new THREE.Vector3(0, 1, 0), 0.5).normalize()));
  }
  const nuts = [];
  for (let k = 0; k < 5; k++) nuts.push(new THREE.SphereGeometry(0.12, 8, 6).translate(top.x + Math.cos(k * 1.3) * 0.25, top.y - 0.25 - (k % 2) * 0.1, top.z + Math.sin(k * 1.3) * 0.25));
  return { trunk: mergeGeometries([trunk, ...nuts.map((g) => stripTo(g))].map(stripTo)), leaves: mergeGeometries(fronds.map(stripTo)), height: H, leavesLow: mergeGeometries(fronds.filter((_, i) => i % 2 === 0).map(stripTo)) };
}

function stripTo(g) {
  let q = g.index ? g.toNonIndexed() : g;
  if (!q.attributes.uv) q.setAttribute('uv', new THREE.BufferAttribute(new Float32Array(q.attributes.position.count * 2), 2));
  if (!q.attributes.normal) q.computeVertexNormals();
  for (const k of Object.keys(q.attributes)) if (!['position', 'normal', 'uv'].includes(k)) q.deleteAttribute(k);
  return q;
}

function broadleafVariant(seed) {
  const rnd = rndGen(seed);
  const H = 7 + rnd() * 5;
  const trunkH = H * (0.35 + rnd() * 0.12);
  const branches = [];
  const tips = [];
  const trunkPts = [new THREE.Vector3(0, 0, 0), new THREE.Vector3((rnd() - 0.5) * 0.4, trunkH * 0.5, (rnd() - 0.5) * 0.4), new THREE.Vector3((rnd() - 0.5) * 0.6, trunkH, (rnd() - 0.5) * 0.6)];
  branches.push(tube(trunkPts, (t) => 0.28 * (1 - t * 0.45) + 0.12 * Math.pow(1 - t, 6), 8));
  const crownC = new THREE.Vector3(trunkPts[2].x, trunkH + (H - trunkH) * 0.5, trunkPts[2].z);
  const crownR = new THREE.Vector3((H - trunkH) * (0.55 + rnd() * 0.2), (H - trunkH) * 0.5, (H - trunkH) * (0.55 + rnd() * 0.2));
  const nb = 5 + Math.floor(rnd() * 3);
  for (let k = 0; k < nb; k++) {
    const a = k / nb * Math.PI * 2 + rnd() * 0.6;
    const el = 0.35 + rnd() * 0.5;
    const L = crownR.x * (0.7 + rnd() * 0.4);
    const p0 = trunkPts[2].clone().add(new THREE.Vector3(0, -rnd() * trunkH * 0.25, 0));
    const p1 = p0.clone().add(new THREE.Vector3(Math.cos(a) * L * 0.5, L * el * 0.6, Math.sin(a) * L * 0.5));
    const p2 = p0.clone().add(new THREE.Vector3(Math.cos(a) * L, L * el, Math.sin(a) * L));
    branches.push(tube([p0, p1, p2], (t) => 0.12 * (1 - t * 0.7), 6));
    tips.push(p1, p2);
    // twigs
    for (let q = 0; q < 3; q++) {
      const s = p1.clone().lerp(p2, rnd());
      const b2 = s.clone().add(new THREE.Vector3((rnd() - 0.5) * 2, rnd() * 1.4, (rnd() - 0.5) * 2));
      branches.push(tube([s, s.clone().lerp(b2, 0.5), b2], (t) => 0.05 * (1 - t * 0.7), 4));
      tips.push(b2);
    }
  }
  // leaf cluster cards fill an ellipsoidal crown, denser at branch tips
  const cards = [], cardsLow = [];
  const nCards = 110;
  for (let k = 0; k < nCards; k++) {
    let c;
    if (k < tips.length * 3) { const t = tips[k % tips.length]; c = t.clone().add(new THREE.Vector3((rnd() - 0.5) * 1.6, (rnd() - 0.4) * 1.2, (rnd() - 0.5) * 1.6)); }
    else {
      const u = rnd() * 2 - 1, th = rnd() * Math.PI * 2, r = Math.cbrt(rnd()) * 0.95;
      const s = Math.sqrt(1 - u * u);
      c = crownC.clone().add(new THREE.Vector3(Math.cos(th) * s * r * crownR.x, u * r * crownR.y, Math.sin(th) * s * r * crownR.z));
    }
    const size = 1.5 + rnd() * 0.9;
    const g = sphereNormals(card(c, size, rnd), crownC);
    cards.push(g);
    if (k % 4 === 0) cardsLow.push(sphereNormals(card(c, size * 1.9, rnd), crownC));
  }
  return { trunk: mergeGeometries(branches.map(stripTo)), leaves: mergeGeometries(cards.map(stripTo)), leavesLow: mergeGeometries(cardsLow.map(stripTo)), height: H };
}

function pineVariant(seed) {
  const rnd = rndGen(seed);
  const H = 10 + rnd() * 7;
  const trunk = tube([new THREE.Vector3(0, 0, 0), new THREE.Vector3((rnd() - 0.5) * 0.3, H * 0.5, (rnd() - 0.5) * 0.3), new THREE.Vector3((rnd() - 0.5) * 0.2, H, (rnd() - 0.5) * 0.2)], (t) => 0.26 * (1 - t * 0.85) + 0.1 * Math.pow(1 - t, 8), 8);
  const parts = [trunk], cards = [], cardsLow = [];
  const crownStart = H * (0.3 + rnd() * 0.15);
  const whorls = 9 + Math.floor(rnd() * 4);
  for (let w = 0; w < whorls; w++) {
    const t = w / whorls;
    const y = crownStart + t * (H - crownStart);
    const L = (1 - t) * 2.8 + 0.5;
    const nb = 5 + Math.floor(rnd() * 3);
    for (let k = 0; k < nb; k++) {
      const a = k / nb * Math.PI * 2 + w * 0.9 + rnd() * 0.4;
      const p0 = new THREE.Vector3(0, y, 0);
      const p2 = new THREE.Vector3(Math.cos(a) * L, y - L * 0.25 + rnd() * 0.3, Math.sin(a) * L);
      parts.push(tube([p0, p0.clone().lerp(p2, 0.5).add(new THREE.Vector3(0, 0.15, 0)), p2], (tt) => 0.05 * (1 - tt * 0.8), 4));
      // needle cards along the branch, facing up-ish
      for (let q = 0; q < 3; q++) {
        const c = p0.clone().lerp(p2, 0.35 + q * 0.3);
        const g = new THREE.PlaneGeometry(1.5, 1.0);
        g.rotateX(-Math.PI / 2 + (rnd() - 0.5) * 0.6).rotateY(-a + (rnd() - 0.5) * 0.5).translate(c.x, c.y + 0.05, c.z);
        cards.push(sphereNormals(g, new THREE.Vector3(0, y + 0.8, 0), 0.5));
        if (q === 1 && k % 2 === 0) { const g2 = g.clone().scale(1.6, 1, 1.6); cardsLow.push(g2); }
      }
    }
  }
  return { trunk: mergeGeometries(parts.map(stripTo)), leaves: mergeGeometries(cards.map(stripTo)), leavesLow: mergeGeometries(cardsLow.map(stripTo)), height: H };
}

function shrubVariant(seed) {
  const rnd = rndGen(seed);
  const cards = [];
  const c0 = new THREE.Vector3(0, 0.6, 0);
  for (let k = 0; k < 22; k++) {
    const c = c0.clone().add(new THREE.Vector3((rnd() - 0.5) * 1.8, rnd() * 0.9, (rnd() - 0.5) * 1.8));
    cards.push(sphereNormals(card(c, 0.9 + rnd() * 0.5, rnd), c0.clone().setY(0.2)));
  }
  const g = mergeGeometries(cards.map(stripTo));
  return { trunk: null, leaves: g, leavesLow: g, height: 1.4 };
}

// ------------------------------------------------------------------ materials
const bayer4 = (p) => {
  // 4x4 ordered-dither threshold in [0, 1)
  const x = mod(floor(p.x), 4), y = mod(floor(p.y), 4);
  const m = [0, 8, 2, 10, 12, 4, 14, 6, 3, 11, 1, 9, 15, 7, 13, 5];
  let v = float(m[15]);
  for (let i = 14; i >= 0; i--) v = select(x.add(y.mul(4)).equal(float(i)), float(m[i]), v);
  return v.add(0.5).div(16);
};

function windOffset(heightFrac, H, phase, flutter = 0) {
  const t = env.time;
  const w = env.windDir;
  const gust = sin(t.mul(0.31).add(phase.mul(0.2))).mul(0.35).add(sin(t.mul(0.83).add(phase)).mul(0.25)).add(0.9);
  const bend = heightFrac.mul(heightFrac).mul(H.mul(0.012)).mul(gust).mul(env.windSpeed.div(7));
  const sway = sin(t.mul(1.3).add(phase)).mul(0.35).add(0.65);
  const off = vec3(w.x, 0, w.y).mul(bend.mul(sway));
  if (flutter) {
    const f = sin(t.mul(7.1).add(positionLocal.x.mul(3.1)).add(positionLocal.z.mul(2.3)).add(phase)).mul(flutter).mul(env.windSpeed.div(7));
    return off.add(vec3(f, f.mul(0.6), f.mul(0.8)).mul(heightFrac.add(0.2)));
  }
  return off;
}

function makeMaterials(kind, leafTex) {
  // per-instance: data = (phase, height, fade, lodSign); wind works in local space
  const data = attribute('vegData', 'vec4');
  const phase = data.x, H = data.y, fade = data.z;
  const hf = clamp(positionLocal.y.div(H.max(0.5)), 0, 1.2);
  const dither = (m) => {
    m.maskNode = Fn(() => {
      const keep = fade.greaterThan(bayer4(screenCoordinate.xy));
      return keep;
    })();
  };
  const bark = standard({ roughness: 0.92, metalness: 0 });
  const p = positionLocal;
  const ridges = fbm2(vec2(p.x.add(p.z).mul(kind === 'palm' ? 1.5 : 3.0), p.y.mul(kind === 'palm' ? 7.5 : 1.2)), 4).mul(0.5).add(0.5);
  const barkCol = kind === 'palm' ? vec3(0.44, 0.39, 0.32) : kind === 'pine' ? vec3(0.36, 0.25, 0.18) : vec3(0.33, 0.29, 0.25);
  bark.colorNode = barkCol.mul(mix(0.62, 1.12, ridges));
  bark.positionNode = positionLocal.add(windOffset(hf, H, phase));
  bark.opacityNode = float(1);
  bark.alphaTest = 0.0;
  dither(bark);

  const leaf = standard({ roughness: 0.78, metalness: 0, side: THREE.DoubleSide, map: leafTex, alphaTest: 0.45, transparent: false });
  leaf.positionNode = positionLocal.add(windOffset(hf, H, phase, kind === 'palm' ? 0.05 : 0.035));
  // backlight through thin leaves (view toward the sun)
  const V = normalize(positionWorld.sub(cameraPosition));
  const back = pow(max(dot(V, env.sunDir), 0), 3);
  const tex = texture(leafTex);
  leaf.emissiveNode = tex.rgb.mul(tex.rgb).mul(env.sunColor).mul(back.mul(0.09).add(0.004));
  leaf.colorNode = tex.rgb.mul(mix(float(0.85), float(1.1), vnoise2(positionWorld.xz.mul(0.07)).mul(0.5).add(0.5)));
  dither(leaf);
  leaf.userData.noContactShadow = true;
  return { bark, leaf };
}

// ------------------------------------------------------------------ system
export class Vegetation {
  constructor({ scene, island, collision, terrain }) {
    this.scene = scene;
    this.island = island;
    this.collision = collision;
    this.group = new THREE.Group();
    this.group.name = 'vegetation';
    scene.add(this.group);
    const textures = {
      palm: frondTexture(),
      broad: leafClusterTexture(3, [[60, 96, 38], [74, 110, 44], [48, 80, 34], [90, 118, 52]]),
      pine: needleTexture(),
      shrub: leafClusterTexture(8, [[66, 90, 40], [80, 102, 46], [100, 110, 50], [58, 76, 36]]),
    };
    this.species = {
      palm: { variants: [11, 12, 13, 14].map(palmVariant), tex: textures.palm, near: 110, far: 900 },
      broad: { variants: [21, 22, 23, 24].map(broadleafVariant), tex: textures.broad, near: 120, far: 1100 },
      pine: { variants: [31, 32, 33].map(pineVariant), tex: textures.pine, near: 120, far: 1100 },
      shrub: { variants: [41, 42, 43].map(shrubVariant), tex: textures.shrub, near: 70, far: 260 },
    };
    this._place();
    this._buildMeshes();
    this.frame = 0;
  }

  _place() {
    const isl = this.island, col = this.collision;
    const rnd = rndGen(2024);
    const inst = { palm: [], broad: [], pine: [], shrub: [] };
    const blocked = (x, z, r) => {
      if (Math.abs(x - VILLAGE.pierX) < 5 && z > 10) return true;
      const g = col.groundAt(x, z, 100, 0, r);
      return g.surface !== null || col.ceilingAt(x, z, isl.heightAt(x, z) - 1) < Infinity;
    };
    const slopeAt = (x, z) => { const n = isl.normalAt(x, z); return 1 - n.y; };
    const noise = (x, z, f) => (Math.sin(x * f * 1.7 + Math.cos(z * f * 1.3) * 2.1) * Math.cos(z * f * 1.9 - Math.sin(x * f * 0.7) * 1.7) + 1) * 0.5;
    for (let k = 0; k < 26000; k++) {
      const x = -520 + rnd() * 1040, z = -760 + rnd() * 900;
      const h = isl.heightAt(x, z);
      if (h < 0.6) continue;
      const sdf = isl.sdfAt(x, z);
      const slope = slopeAt(x, z);
      if (slope > 0.42) continue;
      const cluster = noise(x, z, 0.012) * 0.7 + noise(x + 71, z - 13, 0.045) * 0.3;
      let kind = null;
      if (sdf < -9 && sdf > -60 && h < 5.5 && rnd() < 0.05 * smoothstepJS(0.35, 0.7, cluster) + 0.012) kind = 'palm';
      else if (sdf < -45 && h > 3) {
        const forest = smoothstepJS(0.42, 0.66, cluster) + (x < -120 ? 0.35 : 0);    // the western ("left") hill is wooded
        const r = rnd();
        if (r < 0.1 * forest) kind = h > 28 || noise(x, z, 0.03) > 0.6 ? 'pine' : 'broad';
        else if (r < 0.1 * forest + 0.05 * (0.4 + forest)) kind = 'shrub';
      } else if (sdf < -22 && sdf > -60 && rnd() < 0.02) kind = 'shrub';
      if (!kind) continue;
      const rad = kind === 'shrub' ? 0.9 : 2.2;
      if (blocked(x, z, rad)) continue;
      // spacing: reject if too close to one of the same kind recently placed nearby
      const list = inst[kind];
      let ok = true;
      for (let q = Math.max(0, list.length - 60); q < list.length; q++) { const o = list[q]; if ((o.x - x) ** 2 + (o.z - z) ** 2 < (rad * 2.2) ** 2) { ok = false; break; } }
      if (!ok) continue;
      const v = Math.floor(rnd() * this.species[kind].variants.length);
      const s = kind === 'shrub' ? 0.7 + rnd() * 0.8 : 0.8 + rnd() * 0.45;
      list.push({ x, z, y: h - 0.08, yaw: rnd() * Math.PI * 2, s, v, phase: rnd() * 100 });
      if (kind !== 'shrub') col.addCylinder({ x, z, y0: h - 1, y1: h + 6, r: kind === 'palm' ? 0.22 : 0.3 });
    }
    this.instances = inst;
  }

  _buildMeshes() {
    this.meshes = [];
    for (const [kind, sp] of Object.entries(this.species)) {
      const mats = makeMaterials(kind, sp.tex);
      sp.variants.forEach((v, vi) => {
        const list = this.instances[kind].filter((o) => o.v === vi);
        if (!list.length) return;
        const mk = (geom, mat, lod) => {
          if (!geom) return null;
          const m = new THREE.InstancedMesh(geom, mat, list.length);
          m.count = 0;
          m.frustumCulled = false;
          // only the near LOD casts shadows: alpha-tested leaves in every
          // cascade are expensive, and far tree shadows barely resolve
          m.castShadow = lod === 0;
          m.receiveShadow = true;
          const data = new THREE.InstancedBufferAttribute(new Float32Array(list.length * 4), 4);
          data.setUsage(THREE.DynamicDrawUsage);
          geom.setAttribute('vegData', data);
          m.userData = { lod, data };
          this.group.add(m);
          return m;
        };
        const g0 = v.leaves.clone(), g1 = v.leavesLow.clone();
        const t0 = v.trunk ? v.trunk.clone() : null, t1 = v.trunk ? v.trunk.clone() : null;
        this.meshes.push({
          kind, list, height: v.height, near: sp.near, far: sp.far,
          lod0: [mk(t0, mats.bark, 0), mk(g0, mats.leaf, 0)].filter(Boolean),
          lod1: [mk(t1, mats.bark, 1), mk(g1, mats.leaf, 1)].filter(Boolean),
        });
      });
    }
  }

  /** draw one instance of every LOD mesh (so their pipelines compile while loading) */
  prime(on) {
    this.primed = on;
    for (const e of this.meshes) {
      for (const m of [...e.lod0, ...e.lod1]) {
        if (on) { m.count = Math.max(m.count, 1); m.userData.data.setXYZW(0, 0, e.height, 1, 0); m.userData.data.needsUpdate = true; }
      }
    }
    if (!on) this.frame = 0;
  }

  /** assign instances to LODs with dithered cross-fades (every few frames) */
  update(camera) {
    if (this.primed) return;
    if (this.frame++ % 3 !== 0) return;
    const cx = camera.position.x, cz = camera.position.z;
    const m4 = new THREE.Matrix4(), q = new THREE.Quaternion(), s = new THREE.Vector3(), p = new THREE.Vector3();
    const up = new THREE.Vector3(0, 1, 0);
    for (const e of this.meshes) {
      let n0 = 0, n1 = 0;
      const band = e.near * 0.25;
      for (const o of e.list) {
        const d = Math.hypot(o.x - cx, o.z - cz);
        if (d > e.far) continue;
        const f0 = 1 - smoothstepJS(e.near - band, e.near + band, d);
        const fFar = 1 - smoothstepJS(e.far * 0.85, e.far, d);
        q.setFromAxisAngle(up, o.yaw); s.setScalar(o.s); p.set(o.x, o.y, o.z);
        m4.compose(p, q, s);
        if (f0 > 0.001) {
          for (const m of e.lod0) { m.setMatrixAt(n0, m4); m.userData.data.setXYZW(n0, o.phase, e.height, f0, 0); }
          n0++;
        }
        const f1 = Math.min(1 - f0 + 0.001, fFar);
        if (f1 > 0.002 && f0 < 0.999) {
          for (const m of e.lod1) { m.setMatrixAt(n1, m4); m.userData.data.setXYZW(n1, o.phase, e.height, f1, 1); }
          n1++;
        }
      }
      for (const m of e.lod0) { m.count = n0; m.instanceMatrix.needsUpdate = true; m.userData.data.needsUpdate = true; }
      for (const m of e.lod1) { m.count = n1; m.instanceMatrix.needsUpdate = true; m.userData.data.needsUpdate = true; }
    }
  }
}

function smoothstepJS(a, b, x) { const t = Math.min(Math.max((x - a) / (b - a), 0), 1); return t * t * (3 - 2 * t); }
