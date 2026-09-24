// A 7.4 m Downeast-style lobster boat, built procedurally.
//
// Local frame: x = starboard, y = up, z = aft (bow at -z), origin on the
// design waterline amidships. The hull is lofted from cubic Bézier sections
// (deadrise at the keel, full round bilge, flared topsides), the wheelhouse
// has open window frames (no glass), and the helm has a drawn instrument
// panel. Materials are procedural (paint bands, wear, wood grain, non-skid).

import * as THREE from 'three/webgpu';
import {
  positionLocal, positionWorld, vec3, vec2, float, mix, smoothstep, clamp, abs, texture, uv, normalWorld,
  uniform, sin, fract, floor, max, min,
} from 'three/tsl';
import { mergeGeometries as mergeRaw } from 'three/addons/utils/BufferGeometryUtils.js';
import { standard } from '../render/materials.js';
import { fbm2, vnoise2, gnoise2, hash21 } from '../render/tslnoise.js';

export const BOAT = { L: 7.4, B: 2.5, deck: 0.12 };

// merge anything: non-indexed, position/normal/uv only (missing uvs are zero)
export function mergeGeometries(list) {
  const clean = list.map((g) => {
    let q = g.index ? g.toNonIndexed() : g.clone();
    if (!q.attributes.normal) q.computeVertexNormals();
    if (!q.attributes.uv) q.setAttribute('uv', new THREE.BufferAttribute(new Float32Array(q.attributes.position.count * 2), 2));
    for (const k of Object.keys(q.attributes)) if (!['position', 'normal', 'uv'].includes(k)) q.deleteAttribute(k);
    q.morphAttributes = {};
    return q;
  });
  return mergeRaw(clean);
}
const HB = BOAT.B / 2;

// ------------------------------------------------------------------ hull lines
function halfBeam(s) {
  if (s <= 0.45) return HB * (0.86 + 0.14 * Math.sin(Math.PI / 2 * s / 0.45));
  return HB * Math.pow(Math.max(Math.cos(Math.PI / 2 * (s - 0.45) / 0.55), 0), 0.72);
}
const sstep = (a, b, x) => { const t = Math.min(Math.max((x - a) / (b - a), 0), 1); return t * t * (3 - 2 * t); };
function keelY(s) { return -0.62 + 0.07 * s + sstep(0.7, 1.0, s) * 1.62 - 0.1 * sstep(0.2, 0.0, s); }
function sheerY(s) { return 0.74 + 0.46 * Math.pow(s, 2.2); }
function zOf(s) { return BOAT.L / 2 - s * BOAT.L; }

/** point on the starboard section at station s, parameter t (0 keel .. 1 sheer) */
function sectionPoint(s, t) {
  const hb = halfBeam(s), K = keelY(s), S = sheerY(s);
  const dead = THREE.MathUtils.degToRad(11 + 34 * s * s);
  const p0 = [0, K], p1 = [hb * 0.55, K + hb * 0.55 * Math.tan(dead)];
  const p2 = [hb * 1.05, K + (S - K) * 0.38], p3 = [hb, S];
  const u = 1 - t;
  const b0 = u * u * u, b1 = 3 * u * u * t, b2 = 3 * u * t * t, b3 = t * t * t;
  return [b0 * p0[0] + b1 * p1[0] + b2 * p2[0] + b3 * p3[0], b0 * p0[1] + b1 * p1[1] + b2 * p2[1] + b3 * p3[1]];
}

/** hull half-width at height y for station s (for the deck outline / fittings) */
export function hullWidthAt(s, y) {
  let lo = 0, hi = 1;
  for (let i = 0; i < 24; i++) { const m = (lo + hi) / 2; if (sectionPoint(s, m)[1] < y) lo = m; else hi = m; }
  return sectionPoint(s, (lo + hi) / 2)[0];
}

function hullGeometry(NS = 56, NT = 18, inset = 0, tMin = 0) {
  const pos = [], idx = [];
  const side = (sign) => {
    const base = pos.length / 3;
    for (let i = 0; i <= NS; i++) {
      const s = i / NS;
      for (let j = 0; j <= NT; j++) {
        const t = tMin + (1 - tMin) * j / NT;
        const [x, y] = sectionPoint(Math.min(s, 0.9995), t);
        pos.push(sign * Math.max(x - inset, 0), y, zOf(s));
      }
    }
    for (let i = 0; i < NS; i++) {
      for (let j = 0; j < NT; j++) {
        const a = base + i * (NT + 1) + j, b = a + 1, c = a + NT + 1, d = c + 1;
        if (sign > 0) idx.push(a, c, b, b, c, d); else idx.push(a, b, c, b, d, c);
      }
    }
  };
  side(1); side(-1);
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  g.setIndex(idx);
  g.computeVertexNormals();
  return g;
}

function transomGeometry() {
  const pos = [], idx = [];
  const NT = 18;
  pos.push(0, keelY(0), zOf(0));
  for (const sign of [1, -1]) {
    for (let j = 0; j <= NT; j++) { const [x, y] = sectionPoint(0, j / NT); pos.push(sign * x, y, zOf(0) + 0.001); }
  }
  // close to the sheer line centre
  pos.push(0, sheerY(0), zOf(0));
  const top = pos.length / 3 - 1;
  for (let j = 0; j < NT; j++) {
    const a = 1 + j, b = 2 + j;
    idx.push(0, b, a);
    const c = 1 + NT + 1 + j, d = c + 1;
    idx.push(0, c, d);
  }
  idx.push(1 + NT, top, 1 + NT + 1 + NT);
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  g.setIndex(idx);
  g.computeVertexNormals();
  return g;
}

// inner bulwark + gunwale cap + deck, all derived from the same lines
function deckAndBulwarks() {
  const NS = 48, thick = 0.06;
  const bulw = [], bIdx = [], cap = [], cIdx = [];
  const deckY = (s) => (s < 0.72 ? BOAT.deck : THREE.MathUtils.lerp(BOAT.deck, sheerY(s) - 0.06, sstep(0.72, 0.8, s)));
  for (const sign of [1, -1]) {
    const bb = bulw.length / 3, cb = cap.length / 3;
    for (let i = 0; i <= NS; i++) {
      const s = Math.min(i / NS, 0.985);
      const z = zOf(s), S = sheerY(s), yd = deckY(s);
      const wTop = hullWidthAt(s, S - 0.001) - thick, wBot = hullWidthAt(s, Math.max(yd, keelY(s) + 0.05)) - thick;
      bulw.push(sign * Math.max(wBot, 0), yd, z, sign * Math.max(wTop, 0), S - 0.015, z);
      const wo = hullWidthAt(s, S - 0.001) + 0.02;
      cap.push(sign * Math.max(wTop - 0.02, 0), S + 0.03, z, sign * wo, S + 0.03, z, sign * wo, S - 0.03, z, sign * Math.max(wTop - 0.02, 0), S - 0.01, z);
    }
    for (let i = 0; i < NS; i++) {
      const a = bb + i * 2, b = a + 1, c = a + 2, d = a + 3;
      if (sign > 0) bIdx.push(a, b, c, b, d, c); else bIdx.push(a, c, b, b, c, d);
      for (let k = 0; k < 3; k++) {
        const e = cb + i * 4 + k, f = e + 1, g = e + 4, h = e + 5;
        if (sign > 0) cIdx.push(e, g, f, f, g, h); else cIdx.push(e, f, g, f, h, g);
      }
    }
  }
  const mk = (p, i) => { const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.Float32BufferAttribute(p, 3)); g.setIndex(i); g.computeVertexNormals(); return g; };
  // deck: strip between the port and starboard inner bulwark feet
  const dp = [], di = [];
  for (let i = 0; i <= NS; i++) {
    const s = Math.min(i / NS, 0.985);
    const w = Math.max(hullWidthAt(s, Math.max(deckY(s), keelY(s) + 0.05)) - thick, 0);
    dp.push(-w, deckY(s), zOf(s), w, deckY(s), zOf(s));
  }
  for (let i = 0; i < NS; i++) { const a = i * 2, b = a + 1, c = a + 2, d = a + 3; di.push(a, b, c, b, d, c); }
  // transom inner face above the deck
  const tw = hullWidthAt(0, sheerY(0) - 0.01) - thick;
  const tp = [-tw, BOAT.deck, zOf(0) - thick, tw, BOAT.deck, zOf(0) - thick, -tw, sheerY(0) - 0.015, zOf(0) - thick, tw, sheerY(0) - 0.015, zOf(0) - thick];
  const tcap = new THREE.BoxGeometry(tw * 2 + 0.08, 0.06, thick + 0.05).translate(0, sheerY(0), zOf(0) - thick / 2);
  return {
    bulwark: mergeGeometries([mk(bulw, bIdx), mk(tp, [0, 2, 1, 1, 2, 3])]),
    cap: mergeGeometries([mk(cap, cIdx), tcap.toNonIndexed().index ? tcap : tcap]),
    deck: mk(dp, di),
    deckY,
  };
}

function rubRail() {
  const pts = [];
  for (let i = 0; i <= 60; i++) {
    const s = Math.min(i / 60, 0.99);
    const y = sheerY(s) - 0.09;
    pts.push(new THREE.Vector3(hullWidthAt(s, y) + 0.015, y, zOf(s)));
  }
  const curve = new THREE.CatmullRomCurve3(pts);
  const star = new THREE.TubeGeometry(curve, 90, 0.028, 6, false);
  const port = star.clone().scale(-1, 1, 1);
  // flip winding of the mirrored copy
  const ix = port.index.array;
  for (let i = 0; i < ix.length; i += 3) { const t = ix[i + 1]; ix[i + 1] = ix[i + 2]; ix[i + 2] = t; }
  port.computeVertexNormals();
  return mergeGeometries([star, port]);
}

// ------------------------------------------------------------------ wheelhouse
function box(w, h, d, x, y, z, rx = 0, ry = 0, rz = 0) {
  const g = new THREE.BoxGeometry(w, h, d);
  if (rx || ry || rz) g.applyMatrix4(new THREE.Matrix4().makeRotationFromEuler(new THREE.Euler(rx, ry, rz)));
  return g.translate(x, y, z);
}

function wheelhouse(deckY) {
  const zF = -0.95, zB = 1.05, W = 1.02, y0 = deckY, roofY = 2.02;
  const t = 0.05;
  const walls = [], trim = [];
  const sill = y0 + 1.02, head = y0 + 1.72;
  // front wall: lower panel, header, three open windows split by mullions
  walls.push(box(2 * W, sill - y0, t, 0, (sill + y0) / 2, zF));
  walls.push(box(2 * W, roofY - head, t, 0, (roofY + head) / 2, zF));
  for (const x of [-W + 0.05, -0.33, 0.33, W - 0.05]) walls.push(box(0.1, head - sill, t, x, (head + sill) / 2, zF));
  // sides: lower panel, header, one window each, open aft section
  for (const sgn of [-1, 1]) {
    const x = sgn * W;
    walls.push(box(t, sill - y0, zB - zF, x, (sill + y0) / 2, (zF + zB) / 2));
    walls.push(box(t, roofY - head, zB - zF, x, (roofY + head) / 2, (zF + zB) / 2));
    walls.push(box(t, head - sill, 0.12, x, (head + sill) / 2, zF + 0.06));
    walls.push(box(t, head - sill, 0.1, x, (head + sill) / 2, zF + 1.02));
    walls.push(box(t, head - sill, 0.1, x, (head + sill) / 2, zB - 0.05));
    // window trim (rounded-ish frame strips, proud of the wall so nothing is coplanar)
    trim.push(box(t + 0.03, 0.035, 0.9, x, sill + 0.017, zF + 0.56));
    trim.push(box(t + 0.03, 0.035, 0.9, x, head - 0.017, zF + 0.56));
  }
  for (const [x0, x1] of [[-W + 0.1, -0.38], [-0.28, 0.28], [0.38, W - 0.1]]) {
    trim.push(box(x1 - x0, 0.035, t + 0.03, (x0 + x1) / 2, sill + 0.017, zF));
    trim.push(box(x1 - x0, 0.035, t + 0.03, (x0 + x1) / 2, head - 0.017, zF));
  }
  // roof with overhang and a slight camber (two tilted slabs meeting at the ridge)
  const roof = [
    box(W + 0.14, 0.06, zB - zF + 0.3, (W + 0.14) / 2 - 0.001, roofY + 0.05, (zF + zB) / 2 - 0.05, 0, 0, -0.04),
    box(W + 0.14, 0.06, zB - zF + 0.3, -(W + 0.14) / 2 + 0.001, roofY + 0.05, (zF + zB) / 2 - 0.05, 0, 0, 0.04),
  ];
  // roof edge trim
  trim.push(box(2 * W + 0.3, 0.05, 0.05, 0, roofY + 0.02, zF - 0.2));
  trim.push(box(2 * W + 0.3, 0.05, 0.05, 0, roofY + 0.02, zB + 0.1));
  return { walls: mergeGeometries(walls), trim: mergeGeometries(trim), roof: mergeGeometries(roof), zF, zB, W, roofY, sill };
}

// instrument panel drawn on a canvas: gauges, plotter, switches, labels
function dashTexture() {
  if (typeof document === 'undefined') return null;   // headless tests
  const c = document.createElement('canvas');
  c.width = 1024; c.height = 256;
  const g = c.getContext('2d');
  const grd = g.createLinearGradient(0, 0, 0, 256);
  grd.addColorStop(0, '#23272b'); grd.addColorStop(1, '#16191c');
  g.fillStyle = grd; g.fillRect(0, 0, 1024, 256);
  // subtle panel texture
  for (let i = 0; i < 4000; i++) { g.fillStyle = `rgba(255,255,255,${Math.random() * 0.025})`; g.fillRect(Math.random() * 1024, Math.random() * 256, 1, 1); }
  const gauge = (cx, cy, r, label, frac, red = 0.8) => {
    g.fillStyle = '#0b0c0d'; g.beginPath(); g.arc(cx, cy, r + 6, 0, Math.PI * 2); g.fill();
    g.strokeStyle = '#9aa3a8'; g.lineWidth = 3; g.beginPath(); g.arc(cx, cy, r + 4, 0, Math.PI * 2); g.stroke();
    g.fillStyle = '#101214'; g.beginPath(); g.arc(cx, cy, r, 0, Math.PI * 2); g.fill();
    const a0 = Math.PI * 0.75, a1 = Math.PI * 2.25;
    for (let k = 0; k <= 20; k++) {
      const a = a0 + (a1 - a0) * k / 20, big = k % 5 === 0;
      g.strokeStyle = k / 20 > red ? '#d8443a' : '#e8eef0';
      g.lineWidth = big ? 3 : 1.5;
      g.beginPath(); g.moveTo(cx + Math.cos(a) * r * (big ? 0.72 : 0.8), cy + Math.sin(a) * r * (big ? 0.72 : 0.8)); g.lineTo(cx + Math.cos(a) * r * 0.9, cy + Math.sin(a) * r * 0.9); g.stroke();
    }
    g.fillStyle = '#e8eef0'; g.font = `600 ${Math.round(r * 0.22)}px sans-serif`; g.textAlign = 'center';
    g.fillText(label, cx, cy + r * 0.5);
    const a = a0 + (a1 - a0) * frac;
    g.strokeStyle = '#ff8a2a'; g.lineWidth = 4;
    g.beginPath(); g.moveTo(cx, cy); g.lineTo(cx + Math.cos(a) * r * 0.78, cy + Math.sin(a) * r * 0.78); g.stroke();
    g.fillStyle = '#444'; g.beginPath(); g.arc(cx, cy, 6, 0, Math.PI * 2); g.fill();
  };
  gauge(96, 120, 70, 'RPM ×1000', 0.18);
  gauge(250, 128, 48, 'FUEL', 0.66, 2);
  gauge(360, 128, 48, 'OIL', 0.52);
  gauge(470, 128, 48, 'TEMP', 0.45);
  // chart plotter
  g.fillStyle = '#050607'; g.fillRect(560, 30, 280, 196);
  const sea = g.createLinearGradient(0, 36, 0, 220); sea.addColorStop(0, '#0f3d5e'); sea.addColorStop(1, '#0a2a44');
  g.fillStyle = sea; g.fillRect(568, 38, 264, 180);
  g.fillStyle = '#c9b77e'; g.beginPath(); g.moveTo(568, 38); g.lineTo(832, 38); g.lineTo(832, 80);
  for (let x = 832; x >= 568; x -= 12) g.lineTo(x, 88 + Math.sin(x * 0.05) * 16 + Math.sin(x * 0.13) * 6);
  g.closePath(); g.fill();
  g.strokeStyle = 'rgba(160,200,230,.35)'; g.lineWidth = 1;
  for (let k = 0; k < 5; k++) { g.beginPath(); for (let x = 568; x <= 832; x += 8) g.lineTo(x, 110 + k * 22 + Math.sin(x * 0.04 + k) * 8); g.stroke(); }
  g.fillStyle = '#ff5b3a'; g.beginPath(); g.moveTo(700, 170); g.lineTo(708, 190); g.lineTo(692, 190); g.fill();
  g.fillStyle = '#9fe0ff'; g.font = '600 15px monospace'; g.textAlign = 'left'; g.fillText('SOG 0.0 kn  HDG 205°', 576, 212);
  // switch panel
  for (let k = 0; k < 6; k++) {
    const x = 870 + (k % 3) * 46, y = 60 + Math.floor(k / 3) * 90;
    g.fillStyle = '#0c0d0e'; g.fillRect(x - 14, y - 22, 28, 44);
    g.fillStyle = k % 2 ? '#c73a2f' : '#3a3f44'; g.fillRect(x - 8, y - 16, 16, 18);
    g.fillStyle = '#cfd6da'; g.font = '600 11px sans-serif'; g.textAlign = 'center';
    g.fillText(['NAV', 'ANC', 'BILGE', 'WIPER', 'HORN', 'CABIN'][k], x, y + 36);
  }
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace;
  t.anisotropy = 8;
  return t;
}

function helm(deckY, cab) {
  const parts = { body: [], top: [], metal: [], black: [], wood: [], seat: [] };
  const zF = cab.zF + 0.03;
  // console along the front wall
  parts.body.push(box(1.9, 0.92, 0.42, 0, deckY + 0.46, zF + 0.23));
  // sloped instrument panel (UV mapped with the dash texture)
  const panel = new THREE.PlaneGeometry(1.86, 0.36);
  panel.applyMatrix4(new THREE.Matrix4().makeRotationX(-Math.PI / 2 + 0.62));
  panel.translate(0, deckY + 0.99, zF + 0.3);
  parts.top.push(panel);
  parts.body.push(box(1.9, 0.05, 0.12, 0, deckY + 1.14, zF + 0.12));
  // wheel: rim, spokes, hub, shaft
  const wheel = new THREE.Group();
  const rim = new THREE.TorusGeometry(0.2, 0.017, 10, 48);
  const spokes = [];
  for (let k = 0; k < 6; k++) {
    const a = k * Math.PI / 3;
    spokes.push(new THREE.CylinderGeometry(0.009, 0.009, 0.2, 6).rotateZ(Math.PI / 2).translate(0.1, 0, 0).rotateZ(a));
    spokes.push(new THREE.CylinderGeometry(0.012, 0.008, 0.08, 6).rotateZ(Math.PI / 2).translate(0.25, 0, 0).rotateZ(a));
  }
  const hub = new THREE.CylinderGeometry(0.04, 0.045, 0.06, 16).rotateX(Math.PI / 2);
  wheel.userData.geoms = { rim, spokes: mergeGeometries(spokes), hub };
  wheel.position.set(0.45, deckY + 1.08, zF + 0.52);
  wheel.rotation.x = -0.5;
  parts.metal.push(new THREE.CylinderGeometry(0.018, 0.018, 0.3, 8).rotateX(Math.PI / 2 - 0.5).translate(0.45, deckY + 1.02, zF + 0.4));
  // throttle quadrant
  parts.black.push(box(0.12, 0.1, 0.2, 0.9, deckY + 1.0, zF + 0.46));
  const lever = new THREE.CylinderGeometry(0.01, 0.01, 0.2, 6).translate(0, 0.1, 0);
  const knob = new THREE.SphereGeometry(0.03, 12, 8).translate(0, 0.2, 0);
  // compass binnacle
  parts.black.push(new THREE.CylinderGeometry(0.07, 0.08, 0.06, 20).translate(0, deckY + 1.18, zF + 0.28));
  const dome = new THREE.SphereGeometry(0.068, 20, 10, 0, Math.PI * 2, 0, Math.PI / 2).translate(0, deckY + 1.21, zF + 0.28);
  // helm seat: pedestal, cushion, backrest
  parts.metal.push(new THREE.CylinderGeometry(0.04, 0.06, 0.62, 12).translate(0.45, deckY + 0.31, zF + 1.2));
  parts.seat.push(box(0.46, 0.09, 0.42, 0.45, deckY + 0.66, zF + 1.2));
  parts.seat.push(box(0.46, 0.4, 0.07, 0.45, deckY + 0.92, zF + 1.42, -0.12));
  // wooden grab rail on the console
  parts.wood.push(box(1.6, 0.035, 0.035, 0, deckY + 1.2, zF + 0.46));
  return { parts, wheel, lever, knob, dome, leverPos: new THREE.Vector3(0.9, deckY + 1.03, zF + 0.46) };
}

// ------------------------------------------------------------------ materials
function hullPaint() {
  const m = standard({ roughness: 0.38, metalness: 0 });
  const p = positionLocal;
  const streak = fbm2(vec2(p.z.mul(9.0), p.y.mul(0.8)), 3).mul(0.5).add(0.5);
  const grime = fbm2(p.zy.mul(1.7), 4).mul(0.5).add(0.5);
  const topsides = mix(vec3(0.86, 0.87, 0.84), vec3(0.62, 0.6, 0.55), smoothstep(0.62, 0.9, streak).mul(0.35).add(grime.mul(0.12)));
  const boot = vec3(0.04, 0.085, 0.2);
  const anti = mix(vec3(0.34, 0.07, 0.055), vec3(0.2, 0.2, 0.12), smoothstep(-0.32, -0.04, p.y).mul(0.75).mul(grime.add(0.3)));
  const col = mix(anti, mix(boot, topsides, smoothstep(0.155, 0.165, p.y)), smoothstep(-0.005, 0.005, p.y));
  m.colorNode = col;
  m.roughnessNode = mix(float(0.75), mix(float(0.3), float(0.5), grime), smoothstep(-0.005, 0.005, p.y));
  m.name = 'boat.hull';
  return m;
}

function paint(color, rough = 0.42, wear = 0.15) {
  const m = standard({ roughness: rough, metalness: 0 });
  const p = positionLocal;
  const n = fbm2(p.xz.mul(3.1).add(p.y.mul(2.3)), 4).mul(0.5).add(0.5);
  const c = new THREE.Color(color);
  m.colorNode = mix(vec3(c.r, c.g, c.b), vec3(c.r * 0.7, c.g * 0.68, c.b * 0.62), smoothstep(0.55, 0.95, n).mul(wear * 3));
  m.roughnessNode = float(rough).add(n.mul(0.12));
  return m;
}

function wood(tint = [0.42, 0.26, 0.14]) {
  const m = standard({ roughness: 0.55, metalness: 0 });
  const p = positionLocal;
  const along = p.z.add(p.x.mul(0.15));
  const rings = sin(p.x.mul(90).add(p.y.mul(140)).add(fbm2(vec2(along.mul(2.2), p.x.mul(6)), 3).mul(6))).mul(0.5).add(0.5);
  const fibre = fbm2(vec2(along.mul(1.5), p.x.mul(60).add(p.y.mul(60))), 3).mul(0.5).add(0.5);
  const base = vec3(...tint);
  m.colorNode = base.mul(mix(0.72, 1.12, rings.mul(0.4).add(fibre.mul(0.6))));
  m.roughnessNode = mix(float(0.42), float(0.68), fibre);
  return m;
}

function nonSkid() {
  const m = standard({ roughness: 0.82, metalness: 0 });
  const p = positionLocal;
  const grit = vnoise2(p.xz.mul(160)).mul(0.5).add(0.5);
  const dirt = fbm2(p.xz.mul(1.2), 4).mul(0.5).add(0.5);
  m.colorNode = mix(vec3(0.78, 0.79, 0.76), vec3(0.5, 0.48, 0.42), smoothstep(0.5, 0.95, dirt).mul(0.6)).mul(mix(0.92, 1.04, grit));
  return m;
}

// ------------------------------------------------------------------ assembly
export function buildBoatModel() {
  const group = new THREE.Group();
  group.name = 'boat';
  const hull = new THREE.Mesh(mergeGeometries([hullGeometry(), transomGeometry()]), hullPaint());
  const dk = deckAndBulwarks();
  const white = paint(0xe9e7df, 0.4, 0.12);
  const bulwark = new THREE.Mesh(dk.bulwark, white);
  const cap = new THREE.Mesh(dk.cap, wood());
  const deck = new THREE.Mesh(dk.deck, nonSkid());
  const rail = new THREE.Mesh(rubRail(), paint(0x1a1c1e, 0.5, 0.05));
  const cab = wheelhouse(BOAT.deck);
  const cabWalls = new THREE.Mesh(cab.walls, white);
  const cabTrim = new THREE.Mesh(cab.trim, paint(0x243b52, 0.45, 0.05));
  const roof = new THREE.Mesh(cab.roof, nonSkid());
  group.add(hull, bulwark, cap, deck, rail, cabWalls, cabTrim, roof);

  // helm
  const h = helm(BOAT.deck, cab);
  const dashTex = dashTexture();
  const dashMat = standard({ roughness: 0.55, metalness: 0.0, map: dashTex, emissiveMap: dashTex, emissive: 0x3a3a3a });
  const blackMat = standard({ color: 0x141618, roughness: 0.45 });
  const metalMat = standard({ color: 0xc8ccd0, roughness: 0.22, metalness: 1 });
  const seatMat = standard({ color: 0x1d2c44, roughness: 0.6 });
  group.add(new THREE.Mesh(mergeGeometries(h.parts.body), paint(0x2d3237, 0.5, 0.05)));
  group.add(new THREE.Mesh(mergeGeometries(h.parts.top), dashMat));
  group.add(new THREE.Mesh(mergeGeometries(h.parts.metal), metalMat));
  group.add(new THREE.Mesh(mergeGeometries(h.parts.black), blackMat));
  group.add(new THREE.Mesh(mergeGeometries(h.parts.wood), wood([0.36, 0.2, 0.1])));
  group.add(new THREE.Mesh(mergeGeometries(h.parts.seat), seatMat));
  const g = h.wheel.userData.geoms;
  h.wheel.add(new THREE.Mesh(g.rim, wood([0.3, 0.17, 0.08])), new THREE.Mesh(g.spokes, metalMat), new THREE.Mesh(g.hub, metalMat));
  group.add(h.wheel);
  const leverPivot = new THREE.Group();
  leverPivot.position.copy(h.leverPos);
  leverPivot.add(new THREE.Mesh(h.lever, metalMat), new THREE.Mesh(h.knob, blackMat));
  group.add(leverPivot);
  const glass = standard({ color: 0x223040, roughness: 0.05, metalness: 0.2 });
  group.add(new THREE.Mesh(h.dome, glass));

  // fittings: cleats, mast with lights, antenna, life ring, rope coil, crates, fenders
  const fit = [];
  for (const [s, sgn] of [[0.08, 1], [0.08, -1], [0.62, 1], [0.62, -1]]) {
    const y = sheerY(s) + 0.05, x = sgn * (hullWidthAt(s, sheerY(s) - 0.01) - 0.04), z = zOf(s);
    fit.push(box(0.035, 0.035, 0.2, x, y + 0.02, z), box(0.035, 0.04, 0.035, x, y, z - 0.05), box(0.035, 0.04, 0.035, x, y, z + 0.05));
  }
  fit.push(new THREE.CylinderGeometry(0.03, 0.035, 1.4, 10).translate(0, cab.roofY + 0.75, (cab.zF + cab.zB) / 2 + 0.25));
  fit.push(new THREE.CylinderGeometry(0.015, 0.015, 0.9, 6).rotateZ(Math.PI / 2).translate(0, cab.roofY + 1.2, (cab.zF + cab.zB) / 2 + 0.25));
  fit.push(new THREE.CylinderGeometry(0.008, 0.012, 1.6, 6).translate(0.5, cab.roofY + 0.85, cab.zB - 0.1));
  group.add(new THREE.Mesh(mergeGeometries(fit), metalMat));
  const ring = new THREE.Mesh(new THREE.TorusGeometry(0.28, 0.06, 12, 36), paint(0xe24d1c, 0.5, 0.2));
  ring.position.set(-0.55, BOAT.deck + 1.25, cab.zB + 0.03);
  group.add(ring);
  const rope = [];
  for (let k = 0; k < 5; k++) rope.push(new THREE.TorusGeometry(0.2 - k * 0.012, 0.018, 8, 28).rotateX(Math.PI / 2).translate(0.7, BOAT.deck + 0.02 + k * 0.03, 2.9));
  group.add(new THREE.Mesh(mergeGeometries(rope), standard({ color: 0xb9a57a, roughness: 0.9 })));
  const crateMat = wood([0.5, 0.36, 0.2]);
  const crates = [];
  for (const [x, z, r] of [[-0.55, 2.2, 0.1], [-0.5, 2.95, -0.05], [-0.52, 2.55, 0.02]]) {
    const y = BOAT.deck + (z === 2.55 ? 0.62 : 0.2);
    for (const yy of [0, 1]) crates.push(box(0.72, 0.12, 0.5, x, y - 0.14 + yy * 0.28, z, 0, r, 0));
    crates.push(box(0.68, 0.4, 0.46, x, y, z, 0, r, 0));
  }
  group.add(new THREE.Mesh(mergeGeometries(crates), crateMat));
  const fenders = [];
  for (const z of [-0.6, 1.4]) {
    const f = new THREE.CapsuleGeometry(0.1, 0.34, 6, 12);
    fenders.push(f.clone().translate(hullWidthAt(0.45, 0.4) + 0.11, 0.35, z));
    fenders.push(f.clone().translate(-hullWidthAt(0.45, 0.4) - 0.11, 0.35, z));
  }
  const fenderMesh = new THREE.Mesh(mergeGeometries(fenders), standard({ color: 0xf0efe8, roughness: 0.55 }));
  group.add(fenderMesh);

  // lights: masthead + nav (emissive), cab lamp (a real light at night)
  const lampMat = new THREE.MeshBasicNodeMaterial({ color: 0xfff3dc });
  lampMat.userData.noAO = true;
  const redMat = new THREE.MeshBasicNodeMaterial({ color: 0xff2b1a });
  const greenMat = new THREE.MeshBasicNodeMaterial({ color: 0x19ff5a });
  const masthead = new THREE.Mesh(new THREE.SphereGeometry(0.05, 12, 8), lampMat);
  masthead.position.set(0, cab.roofY + 1.5, (cab.zF + cab.zB) / 2 + 0.25);
  const port = new THREE.Mesh(new THREE.BoxGeometry(0.04, 0.07, 0.12), redMat);
  port.position.set(-cab.W - 0.04, cab.roofY - 0.25, cab.zF + 0.2);
  const star = new THREE.Mesh(new THREE.BoxGeometry(0.04, 0.07, 0.12), greenMat);
  star.position.set(cab.W + 0.04, cab.roofY - 0.25, cab.zF + 0.2);
  const cabLampMesh = new THREE.Mesh(new THREE.CylinderGeometry(0.09, 0.11, 0.05, 16), lampMat);
  cabLampMesh.position.set(0, cab.roofY - 0.04, (cab.zF + cab.zB) / 2);
  group.add(masthead, port, star, cabLampMesh);
  const cabLight = new THREE.PointLight(0xffc98a, 0, 7, 1.8);
  cabLight.position.set(0, cab.roofY - 0.25, (cab.zF + cab.zB) / 2);
  group.add(cabLight);
  const deckLight = new THREE.SpotLight(0xfff0d8, 0, 14, 0.9, 0.7, 1.6);
  deckLight.position.set(0, cab.roofY + 0.05, cab.zB + 0.1);
  deckLight.target.position.set(0, 0, 3.2);
  group.add(deckLight, deckLight.target);

  group.traverse((o) => { if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; } });
  masthead.castShadow = port.castShadow = star.castShadow = cabLampMesh.castShadow = false;

  return {
    group, wheel: h.wheel, lever: leverPivot, cabLight, deckLight, lampMats: [lampMat, redMat, greenMat],
    fenders: fenderMesh, cab, deckY: dk.deckY,
    helmEye: new THREE.Vector3(0.45, BOAT.deck + 1.62, cab.zF + 1.15),
  };
}

// hull sample points for buoyancy: 3 lines (keel, port/starboard bilge) x 6 stations
export function hullSamplePoints() {
  const pts = [];
  for (const s of [0.04, 0.2, 0.38, 0.56, 0.72, 0.86]) {
    const z = zOf(s);
    const K = keelY(s);
    const [bx, by] = sectionPoint(s, 0.55);
    pts.push({ p: new THREE.Vector3(0, K, z), w: 0.6 });
    pts.push({ p: new THREE.Vector3(bx, by, z), w: 1 });
    pts.push({ p: new THREE.Vector3(-bx, by, z), w: 1 });
  }
  return pts;
}

export { sheerY, keelY, zOf, halfBeam };

// TSL twins of halfBeam / sheerY (s node in [0,1]) for shader-side hull tests
export function halfBeamNode(tsl, s) {
  const { float, cos, sin, pow, select, max } = tsl;
  const aft = float(HB).mul(float(0.86).add(sin(s.div(0.45).mul(Math.PI / 2)).mul(0.14)));
  const fore = float(HB).mul(pow(max(cos(s.sub(0.45).div(0.55).mul(Math.PI / 2)), 0.0001), 0.72));
  return select(s.lessThan(0.45), aft, fore).add(0.04);
}
export function sheerNode(tsl, s) {
  const { pow } = tsl;
  return pow(s, 2.2).mul(0.46).add(0.74);
}
