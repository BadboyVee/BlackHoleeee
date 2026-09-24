// The fishing village: cottages on the terrace, a timber pier with a T-head
// where the boat moors, a boat shed, a fish market with a swinging sign,
// net racks, upturned dinghies, crates, pots, buoys, rocks and driftwood.
//
// Static parts are merged per material (a handful of draw calls); walls,
// decks, posts and props register colliders so you can walk the village.
// Pier lanterns hang from chains and swing; their lights and the porch lamps
// come on at dusk.

import * as THREE from 'three/webgpu';
import { mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';
import { VILLAGE } from './island.js';
import {
  weatherboard, corrugated, planks, piling, stone, rope, net, rustyMetal, paintedWood, rawWood, windowGlass,
  canvasCloth, barkWood,
} from './villageMaterials.js';
import { standard } from '../render/materials.js';

const rnd = mulberry32(1337);
function mulberry32(a) {
  return () => { a |= 0; a = a + 0x6D2B79F5 | 0; let t = Math.imul(a ^ a >>> 15, 1 | a); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; };
}
const R = (a, b) => a + (b - a) * rnd();

// ------------------------------------------------------------------ geometry bins
class Bin {
  constructor(attrs = {}) { this.parts = []; this.attrs = attrs; }
  add(g, extra = {}) {
    g = g.index ? g.toNonIndexed() : g;
    const n = g.attributes.position.count;
    for (const [name, size] of Object.entries(this.attrs)) {
      const v = extra[name] ?? new Array(size).fill(0);
      const arr = new Float32Array(n * size);
      for (let i = 0; i < n; i++) for (let k = 0; k < size; k++) arr[i * size + k] = Array.isArray(v) ? v[k] : v;
      g.setAttribute(name, new THREE.BufferAttribute(arr, size));
    }
    if (!g.attributes.uv) g.setAttribute('uv', new THREE.BufferAttribute(new Float32Array(n * 2), 2));
    for (const k of Object.keys(g.attributes)) if (!['position', 'normal', 'uv', ...Object.keys(this.attrs)].includes(k)) g.deleteAttribute(k);
    this.parts.push(g);
    return g;
  }
  mesh(material, name) {
    if (!this.parts.length) return null;
    const m = new THREE.Mesh(mergeGeometries(this.parts), material);
    m.name = name;
    m.castShadow = true;
    m.receiveShadow = true;
    return m;
  }
}

const M4 = new THREE.Matrix4();
function place(g, x, y, z, yaw = 0, rx = 0, rz = 0) {
  g.applyMatrix4(M4.makeRotationFromEuler(new THREE.Euler(rx, yaw, rz, 'YXZ')));
  return g.translate(x, y, z);
}
function boxAt(w, h, d, x, y, z, yaw = 0, rx = 0, rz = 0) { return place(new THREE.BoxGeometry(w, h, d), x, y, z, yaw, rx, rz); }
function cylAt(r0, r1, h, x, y, z, seg = 10, yaw = 0, rx = 0, rz = 0) { return place(new THREE.CylinderGeometry(r0, r1, h, seg), x, y, z, yaw, rx, rz); }
// local (house frame) -> world
function toWorld(cx, cz, yaw, lx, lz) {
  const c = Math.cos(yaw), s = Math.sin(yaw);
  return [cx + lx * c + lz * s, cz - lx * s + lz * c];
}

export class Village {
  constructor({ scene, island, collision, terrain }) {
    this.scene = scene;
    this.island = island;
    this.collision = collision;
    this.group = new THREE.Group();
    this.group.name = 'village';
    scene.add(this.group);
    this.bins = {
      board: new Bin({ paint: 3, groundY: 1 }),
      roof: new Bin({ paint: 3, corrDir: 2 }),
      deck: new Bin(), deckX: new Bin(), pile: new Bin(), stone: new Bin(), trim: new Bin(), door: new Bin(),
      glass: new Bin(), wood: new Bin(), dark: new Bin(), rope: new Bin(), metal: new Bin(), net: new Bin(),
      cloth: new Bin(), bark: new Bin(), red: new Bin(), yellow: new Bin(), orange: new Bin(), blue: new Bin(),
      rock: new Bin(), hull: new Bin(), hullIn: new Bin(),
    };
    this.swingers = [];    // pendulums (lanterns, sign)
    this.lights = [];      // lights switched on at night
    this.lampMats = [];
    this._build();
    this._assemble();
  }

  h(x, z) { return this.island.heightAt(x, z); }

  _build() {
    this._pier();
    this._houses();
    this._boatShed();
    this._market();
    this._beachProps();
    this._debris();
  }

  // ------------------------------------------------------------------ pier
  _pier() {
    const b = this.bins, col = this.collision;
    const X = VILLAGE.pierX, z0 = 22, z1 = VILLAGE.pierZ1, W = 2.8, Y = 2.05;
    this.pierDeckY = Y;
    // deck (planks run across the pier -> plank lines advance along z)
    b.deck.add(boxAt(W, 0.08, z1 - z0, X, Y - 0.04, (z0 + z1) / 2));
    col.addBox({ x: X, z: (z0 + z1) / 2, y0: Y - 0.3, y1: Y, hx: W / 2, hz: (z1 - z0) / 2, tag: 'wood' });
    // T-head platform
    const tz0 = z1 - 7, tW = 9;
    b.deckX.add(boxAt(tW, 0.08, 7, X, Y - 0.04 + 0.001, (tz0 + z1) / 2 + 0.001));
    col.addBox({ x: X, z: (tz0 + z1) / 2, y0: Y - 0.3, y1: Y, hx: tW / 2, hz: 3.5, tag: 'wood' });
    // stringers + cap beams
    for (const dx of [-W / 2 + 0.15, 0, W / 2 - 0.15]) b.wood.add(boxAt(0.12, 0.22, z1 - z0, X + dx, Y - 0.19, (z0 + z1) / 2));
    for (const dz of [0.3, 3.5, 6.7]) b.wood.add(boxAt(tW, 0.22, 0.14, X, Y - 0.19, tz0 + dz));
    // pilings every 3 m, stopping where the beach is higher than the stringers
    const posts = [];
    for (let z = z0 + 1; z <= z1 - 0.4; z += 3) {
      for (const dx of [-W / 2 - 0.05, W / 2 + 0.05]) posts.push([X + dx, z, z < tz0 ? 1.0 : 0.3]);
    }
    for (let x = X - tW / 2 + 0.2; x <= X + tW / 2 - 0.1; x += 2.2) for (const z of [tz0 + 0.2, z1 - 0.2]) posts.push([x, z, 1.0]);
    for (const [x, z, above] of posts) {
      const bed = this.h(x, z);
      if (bed > Y - 0.35) continue;
      const top = Y + above;
      const bot = bed - 0.8;
      b.pile.add(cylAt(0.13, 0.15, top - bot, x, (top + bot) / 2, z, 9));
      col.addCylinder({ x, z, y0: bot, y1: top, r: 0.15 });
      // a little bevelled cap
      b.wood.add(cylAt(0.02, 0.15, 0.08, x, top + 0.04, z, 9));
    }
    // X-bracing under the deck on every other bay
    for (let z = z0 + 1; z < tz0; z += 6) {
      const bed = Math.max(this.h(X, z), this.h(X, z + 3));
      const yTop = Y - 0.3, yBot = Math.max(bed + 0.2, -0.9);
      if (yTop - yBot < 0.5) continue;
      const len = Math.hypot(3, yTop - yBot), ang = Math.atan2(yTop - yBot, 3);
      for (const dx of [-W / 2 - 0.2, W / 2 + 0.2]) {
        b.wood.add(boxAt(0.06, 0.16, len, X + dx, (yTop + yBot) / 2, z + 1.5, 0, ang));
        b.wood.add(boxAt(0.06, 0.16, len, X + dx, (yTop + yBot) / 2, z + 1.5, 0, -ang));
      }
    }
    // railings (top rail + mid rail) with a gap on the T-head's east side for boarding
    const railSeg = (x0, zA, x1, zB) => {
      const len = Math.hypot(x1 - x0, zB - zA), yaw = Math.atan2(x1 - x0, zB - zA);
      for (const [yy, t] of [[Y + 0.98, 0.1], [Y + 0.55, 0.07]]) b.wood.add(boxAt(0.07, t, len, (x0 + x1) / 2, yy, (zA + zB) / 2, yaw));
      col.addBox({ x: (x0 + x1) / 2, z: (zA + zB) / 2, y0: Y, y1: Y + 1.05, hx: 0.06, hz: len / 2, yaw: -yaw, walkable: false });
    };
    railSeg(X - W / 2 - 0.05, z0 + 1, X - W / 2 - 0.05, tz0);
    railSeg(X + W / 2 + 0.05, z0 + 1, X + W / 2 + 0.05, tz0);
    railSeg(X - tW / 2 + 0.2, z1 - 0.2, X + tW / 2 - 0.3, z1 - 0.2);
    railSeg(X - tW / 2 + 0.2, tz0 + 0.2, X - tW / 2 + 0.2, z1 - 0.2);
    railSeg(X - tW / 2 + 0.2, tz0 + 0.2, X - W / 2 - 0.05, tz0 + 0.2);
    railSeg(X + W / 2 + 0.05, tz0 + 0.2, X + tW / 2 - 0.3, tz0 + 0.2);
    // bollards and cleats on the T-head, ladder down to the water on the east side
    for (const [x, z] of [[X + tW / 2 - 0.5, tz0 + 1.4], [X + tW / 2 - 0.5, z1 - 1.6], [X - tW / 2 + 0.6, z1 - 1.6]]) {
      b.metal.add(cylAt(0.13, 0.15, 0.42, x, Y + 0.21, z, 14));
      b.metal.add(cylAt(0.18, 0.18, 0.05, x, Y + 0.44, z, 14));
      col.addCylinder({ x, z, y0: Y, y1: Y + 0.45, r: 0.16 });
    }
    const lx = X + tW / 2 + 0.05, lz = tz0 + 3.5;
    for (const dz of [-0.28, 0.28]) b.metal.add(boxAt(0.05, Y + 1.4, 0.05, lx, (Y - 1.4 + Y + 0.02) / 2, lz + dz));
    for (let y = Y - 1.3; y < Y; y += 0.3) b.metal.add(cylAt(0.018, 0.018, 0.56, lx, y, lz, 6, 0, Math.PI / 2));
    // mooring lines from the bollards to the boat, coiled rope, a bench, crates
    b.rope.add(place(new THREE.TorusGeometry(0.28, 0.035, 8, 24), X - 2.4, Y + 0.035, z1 - 3, 0, Math.PI / 2));
    b.rope.add(place(new THREE.TorusGeometry(0.22, 0.035, 8, 24), X - 2.4, Y + 0.1, z1 - 3, 0, Math.PI / 2));
    b.wood.add(boxAt(1.8, 0.06, 0.4, X - 3.2, Y + 0.45, z1 - 5.2));
    for (const dx of [-0.75, 0.75]) b.wood.add(boxAt(0.08, 0.45, 0.35, X - 3.2 + dx, Y + 0.22, z1 - 5.2));
    col.addBox({ x: X - 3.2, z: z1 - 5.2, y0: Y, y1: Y + 0.48, hx: 0.9, hz: 0.2 });
    this._crateStack(X - 3.4, Y, z1 - 2.1, 0.3, 3);
    // lantern posts: outside the rail posts, arm reaching out over the water
    for (const [k, z] of [[0, z0 + 7], [1, z0 + 22], [0, z0 + 37], [1, tz0 - 1]].entries()) {
      const side = z[0] === 0 ? -1 : 1, zz = z[1];
      const px = X + side * (W / 2 + 0.33);
      b.pile.add(cylAt(0.09, 0.1, 3.2, px, Y + 1.5, zz, 8));
      col.addCylinder({ x: px, z: zz, y0: Y - 0.2, y1: Y + 3.1, r: 0.1 });
      b.wood.add(boxAt(0.8, 0.08, 0.08, px + side * 0.36, Y + 2.95, zz));
      b.wood.add(boxAt(0.05, 0.4, 0.05, px + side * 0.12, Y + 2.75, zz, 0, 0, side * 0.8));
      this._lantern(new THREE.Vector3(px + side * 0.7, Y + 2.91, zz), k);
    }
    // steps up from the beach at the landward end
    for (let k = 0; k < 4; k++) b.deck.add(boxAt(W, 0.06, 0.34, X, this.h(X, z0 - 0.4) + 0.05 + k * 0.001, z0 - 0.2 - k * 0.3));
  }

  _lantern(hook, k) {
    // chain + lantern swing as a pendulum from the hook point
    const pivot = new THREE.Group();
    pivot.position.copy(hook);
    const chainMat = rustyMetal([0.12, 0.12, 0.12]);
    const links = [];
    for (let i = 0; i < 6; i++) {
      const g = new THREE.TorusGeometry(0.022, 0.006, 5, 10);
      if (i % 2) g.rotateY(Math.PI / 2);
      links.push(g.translate(0, -0.03 - i * 0.034, 0));
    }
    pivot.add(new THREE.Mesh(mergeGeometries(links), chainMat));
    const body = new THREE.Group();
    body.position.y = -0.24;
    const frame = rustyMetal([0.1, 0.11, 0.1]);
    body.add(new THREE.Mesh(new THREE.CylinderGeometry(0.05, 0.12, 0.08, 8).translate(0, 0.02, 0), frame));
    body.add(new THREE.Mesh(new THREE.CylinderGeometry(0.1, 0.1, 0.02, 8).translate(0, -0.22, 0), frame));
    for (let i = 0; i < 4; i++) {
      const a = i * Math.PI / 2 + Math.PI / 4;
      body.add(new THREE.Mesh(new THREE.BoxGeometry(0.012, 0.22, 0.012).translate(Math.cos(a) * 0.085, -0.1, Math.sin(a) * 0.085), frame));
    }
    const glowMat = new THREE.MeshBasicNodeMaterial({ color: 0x302418 });
    glowMat.userData.noAO = true;
    const bulb = new THREE.Mesh(new THREE.CylinderGeometry(0.075, 0.075, 0.18, 12).translate(0, -0.1, 0), glowMat);
    body.add(bulb);
    const light = new THREE.PointLight(0xffb866, 0, 16, 1.7);
    light.position.y = -0.1;
    body.add(light);
    pivot.add(body);
    pivot.traverse((o) => { if (o.isMesh) o.castShadow = true; });
    bulb.castShadow = false;
    this.group.add(pivot);
    this.swingers.push({ obj: pivot, phase: k * 1.7, amp: 0.12, freq: 1.45 - k * 0.07 });
    this.lights.push({ light, max: 9 });
    this.lampMats.push(glowMat);
  }

  // ------------------------------------------------------------------ houses
  _houses() {
    const palette = [[0.82, 0.8, 0.74], [0.35, 0.5, 0.62], [0.62, 0.22, 0.18], [0.75, 0.58, 0.32], [0.5, 0.58, 0.48], [0.86, 0.84, 0.78], [0.28, 0.36, 0.44], [0.7, 0.66, 0.58]];
    const roofs = [[-1, 0, 0], [0.42, 0.14, 0.1], [0.2, 0.3, 0.26], [-1, 0, 0], [0.22, 0.26, 0.34], [-1, 0, 0]];
    const spots = [
      [70, -22, 0.1], [84, -30, -0.05], [98, -24, 0.15], [140, -20, -0.1], [154, -30, 0.05], [96, -46, 0.2],
      [74, -44, -0.1], [112, -40, 0.05], [132, -44, -0.15], [150, -52, 0.1], [84, -60, 0.0], [118, -60, 0.1],
    ];
    spots.forEach(([x, z, yaw], i) => {
      const w = R(5.2, 7.2), d = R(4.4, 5.6), wallH = R(2.5, 2.9);
      this._house({ x, z, yaw, w, d, wallH, paint: palette[i % palette.length], roof: roofs[i % roofs.length], porch: i % 3 === 0, chimney: i % 2 === 0, lamp: i === 0 || i === 3 });
    });
  }

  _house({ x, z, yaw, w, d, wallH, paint, roof, porch, chimney, lamp }) {
    const b = this.bins, col = this.collision;
    // footprint heights -> floor above the highest corner, stone plinth below
    let hMin = Infinity, hMax = -Infinity;
    for (const [lx, lz] of [[-w / 2, -d / 2], [w / 2, -d / 2], [-w / 2, d / 2], [w / 2, d / 2], [0, 0]]) {
      const [wx, wz] = toWorld(x, z, yaw, lx, lz);
      const hh = this.h(wx, wz); hMin = Math.min(hMin, hh); hMax = Math.max(hMax, hh);
    }
    const F = hMax + 0.35;
    const L = (lx, ly, lz) => { const [wx, wz] = toWorld(x, z, yaw, lx, lz); return [wx, ly, wz]; };
    const add = (bin, g, lx, ly, lz, extra, rx = 0, rz = 0, ry = 0) => { const [wx, wy, wz] = L(lx, ly, lz); bin.add(place(g, wx, wy, wz, yaw + ry, rx, rz), extra); };
    b.stone.add(place(new THREE.BoxGeometry(w + 0.25, F - hMin + 0.4, d + 0.25), ...L(0, (F + hMin - 0.4) / 2, 0), yaw));
    const paintA = { paint: paint, groundY: F };
    const T = 0.14;
    const sill = 0.9, head = 2.05;
    // wall builder along local x (front/back) or z (sides) with window/door gaps
    const wall = (len, alongX, off, openings) => {
      // openings: [{c, w, y0, y1, type}]
      let cursor = -len / 2;
      const seg = (a, bnd, y0, y1) => {
        if (bnd - a < 0.01 || y1 - y0 < 0.01) return;
        const cx = (a + bnd) / 2, cy = F + (y0 + y1) / 2;
        const g = new THREE.BoxGeometry(alongX ? bnd - a : T, y1 - y0, alongX ? T : bnd - a);
        add(b.board, g, alongX ? cx : off, cy, alongX ? off : cx, paintA);
      };
      for (const o of openings) {
        seg(cursor, o.c - o.w / 2, 0, wallH);
        seg(o.c - o.w / 2, o.c + o.w / 2, 0, o.y0);
        seg(o.c - o.w / 2, o.c + o.w / 2, o.y1, wallH);
        // frame trim + glass / door
        const fx = (lx, lz, gw, gh, gd) => add(b.trim, new THREE.BoxGeometry(gw, gh, gd), lx, 0, lz);
        const cc = o.c;
        const tw = 0.07;
        const oy0 = F + o.y0, oy1 = F + o.y1;
        const mk = (along, ly, sx, sy) => {
          const g = new THREE.BoxGeometry(alongX ? sx : T + 0.05, sy, alongX ? T + 0.05 : sx);
          add(b.trim, g, alongX ? along : off, ly, alongX ? off : along);
        };
        mk(cc, oy1 + tw / 2, o.w + tw * 2, tw);
        mk(cc, oy0 - tw / 2, o.w + tw * 2 + (o.type === 'door' ? 0 : 0.12), tw);
        mk(cc - o.w / 2 - tw / 2, (oy0 + oy1) / 2, tw, o.y1 - o.y0);
        mk(cc + o.w / 2 + tw / 2, (oy0 + oy1) / 2, tw, o.y1 - o.y0);
        if (o.type === 'door') {
          const g = new THREE.BoxGeometry(alongX ? o.w : 0.05, o.y1 - o.y0, alongX ? 0.05 : o.w);
          add(b.door, g, alongX ? cc : off, (oy0 + oy1) / 2, alongX ? off : cc);
        } else {
          const g = new THREE.BoxGeometry(alongX ? o.w : 0.03, o.y1 - o.y0, alongX ? 0.03 : o.w);
          add(b.glass, g, alongX ? cc : off, (oy0 + oy1) / 2, alongX ? off : cc);
          // mullion cross
          mk(cc, (oy0 + oy1) / 2, o.w, 0.04);
          mk(cc, (oy0 + oy1) / 2, 0.04, o.y1 - o.y0);
        }
        cursor = o.c + o.w / 2;
      }
      seg(cursor, len / 2, 0, wallH);
    };
    const win = (c, ww = 0.9) => ({ c, w: ww, y0: sill, y1: head, type: 'win' });
    wall(w, true, d / 2, [win(-w * 0.3), { c: 0.2, w: 0.95, y0: 0, y1: 2.05, type: 'door' }, win(w * 0.32)]);
    wall(w, true, -d / 2, [win(-w * 0.22, 0.8), win(w * 0.25, 0.8)]);
    wall(d, false, -w / 2, [win(0, 0.8)]);
    wall(d, false, w / 2, [win(-d * 0.15, 0.8)]);
    col.addBox({ x, z, y0: hMin - 0.4, y1: F + wallH + 2, hx: w / 2 + 0.1, hz: d / 2 + 0.1, yaw: -yaw, walkable: false });
    // gable ends
    const rise = Math.tan(THREE.MathUtils.degToRad(R(28, 36))) * (d / 2);
    for (const sx of [-1, 1]) {
      const shape = new THREE.Shape([new THREE.Vector2(-d / 2, 0), new THREE.Vector2(d / 2, 0), new THREE.Vector2(0, rise)]);
      const g = new THREE.ExtrudeGeometry(shape, { depth: T, bevelEnabled: false });
      g.translate(0, 0, -T / 2).rotateY(Math.PI / 2);
      add(b.board, g, sx * w / 2, F + wallH, 0, paintA);
    }
    // roof: two corrugated slabs with overhang + ridge cap
    const over = 0.35, slabW = Math.hypot(d / 2, rise) + over, ang = Math.atan2(rise, d / 2);
    const roofPaint = { paint: roof, corrDir: [Math.sin(yaw) * 0 + Math.cos(yaw), -Math.sin(yaw)] };
    for (const sz of [-1, 1]) {
      const g = new THREE.BoxGeometry(w + over * 2, 0.05, slabW);
      const cz = sz * (slabW / 2 - over / 2) * Math.cos(ang), cy = F + wallH + rise / 2 - over / 2 * Math.sin(ang) + 0.06;
      // corrugations run down the slope: they vary along local x
      add(b.roof, g, 0, cy + 0.02, sz * (d / 4 + 0.001), { paint: roof, corrDir: [Math.cos(yaw), -Math.sin(yaw)] }, sz * ang);
      void cz;
    }
    add(b.trim, new THREE.BoxGeometry(w + over * 2 + 0.05, 0.08, 0.26), 0, F + wallH + rise + 0.08, 0);
    // fascia boards
    for (const sz of [-1, 1]) add(b.trim, new THREE.BoxGeometry(w + over * 2, 0.16, 0.04), 0, F + wallH - 0.1, sz * (d / 2 + over * 0.95));
    if (chimney) {
      add(b.stone, new THREE.BoxGeometry(0.6, rise + 1.3, 0.6), w * 0.3, F + wallH + rise / 2 + 0.4, -d * 0.12);
      add(b.dark, new THREE.BoxGeometry(0.66, 0.1, 0.66), w * 0.3, F + wallH + rise + 1.05, -d * 0.12);
    }
    if (porch) {
      const pd = 1.8, py = F - 0.08;
      add(b.deck, new THREE.BoxGeometry(w * 0.7, 0.1, pd), 0.2, py, d / 2 + pd / 2);
      const [px, , pz] = L(0.2, 0, d / 2 + pd / 2);
      col.addBox({ x: px, z: pz, y0: hMin - 0.5, y1: F - 0.03, hx: w * 0.35, hz: pd / 2, yaw: -yaw, tag: 'wood' });
      for (const sx of [-1, 1]) {
        add(b.trim, new THREE.BoxGeometry(0.12, 2.3, 0.12), 0.2 + sx * w * 0.33, F + 1.1, d / 2 + pd - 0.1);
        const [cx, , cz] = L(0.2 + sx * w * 0.33, 0, d / 2 + pd - 0.1);
        col.addCylinder({ x: cx, z: cz, y0: F - 0.1, y1: F + 2.3, r: 0.1 });
      }
      add(b.roof, new THREE.BoxGeometry(w * 0.76, 0.04, pd + 0.3), 0.2, F + 2.33, d / 2 + pd / 2, { paint: roof, corrDir: [Math.sin(yaw), Math.cos(yaw)] }, -0.12);
      // steps
      for (let k = 1; k <= 3; k++) {
        const sy = F - 0.08 - k * ((F - this.h(...L(0.2, 0, d / 2 + pd + 0.3).filter((_, i) => i !== 1))) / 4);
        add(b.deck, new THREE.BoxGeometry(1.2, 0.08, 0.3), 0.2, sy, d / 2 + pd + k * 0.28);
      }
    }
    if (lamp) {
      const [lx, ly, lz] = L(-0.55, F + 2.25, d / 2 + 0.2);
      const glowMat = new THREE.MeshBasicNodeMaterial({ color: 0x302418 });
      const bulb = new THREE.Mesh(new THREE.SphereGeometry(0.07, 10, 8), glowMat);
      bulb.position.set(lx, ly, lz);
      this.group.add(bulb);
      b.metal.add(place(new THREE.CylinderGeometry(0.1, 0.05, 0.08, 10), lx, ly + 0.08, lz));
      const light = new THREE.PointLight(0xffb060, 0, 11, 1.7);
      light.position.set(lx, ly - 0.05, lz);
      this.group.add(light);
      this.lights.push({ light, max: 5 });
      this.lampMats.push(glowMat);
    }
    // buoys and a coil of rope hung on the wall, a barrel by the door
    if (rnd() < 0.7) {
      for (let k = 0; k < 3; k++) {
        const g = new THREE.SphereGeometry(0.16, 10, 8);
        add([b.red, b.yellow, b.orange][k % 3], g, -w * 0.45 + k * 0.36, F + 1.55 + (k % 2) * 0.18, d / 2 + 0.24);
      }
    }
    const [bx, , bz] = L(w * 0.42, 0, d / 2 + 0.55);
    this._barrel(bx, this.h(bx, bz), bz);
  }

  // ------------------------------------------------------------------ other buildings
  _boatShed() {
    const b = this.bins, col = this.collision;
    const x = 132, z = 6, yaw = 0.05, w = 7, d = 9, H = 3.6;
    let hMax = -Infinity;
    for (const [lx, lz] of [[-w / 2, -d / 2], [w / 2, -d / 2], [-w / 2, d / 2], [w / 2, d / 2]]) { const [wx, wz] = toWorld(x, z, yaw, lx, lz); hMax = Math.max(hMax, this.h(wx, wz)); }
    const F = hMax + 0.1;
    const L = (lx, lz) => toWorld(x, z, yaw, lx, lz);
    const paintA = { paint: [0.44, 0.2, 0.15], groundY: F };
    const add = (bin, g, lx, ly, lz, extra, rx = 0) => { const [wx, wz] = L(lx, lz); bin.add(place(g, wx, ly, wz, yaw, rx), extra); };
    // back + sides, open front (seaward) with a sliding door pushed aside
    add(b.board, new THREE.BoxGeometry(w, H, 0.14), 0, F + H / 2, -d / 2, paintA);
    for (const sx of [-1, 1]) add(b.board, new THREE.BoxGeometry(0.14, H, d), sx * w / 2, F + H / 2, 0, paintA);
    add(b.board, new THREE.BoxGeometry(1.3, H, 0.14), -w / 2 + 0.65, F + H / 2, d / 2, paintA);
    add(b.board, new THREE.BoxGeometry(2.6, H - 0.2, 0.08), w / 2 + 0.3, F + H / 2 - 0.1, d / 2 + 0.12, paintA);
    add(b.board, new THREE.BoxGeometry(w, 0.9, 0.14), 0, F + H - 0.45, d / 2, paintA);
    for (const sx of [-1, 1]) {
      const [cx, cz] = L(sx * w / 2, 0);
      col.addBox({ x: cx, z: cz, y0: F - 1, y1: F + H, hx: 0.1, hz: d / 2, yaw: -yaw, walkable: false });
    }
    { const [cx, cz] = L(0, -d / 2); col.addBox({ x: cx, z: cz, y0: F - 1, y1: F + H, hx: w / 2, hz: 0.1, yaw: -yaw, walkable: false }); }
    // floor + slipway rails down to the water
    add(b.deck, new THREE.BoxGeometry(w - 0.2, 0.1, d), 0, F - 0.05, 0);
    { const [cx, cz] = L(0, 0); col.addBox({ x: cx, z: cz, y0: F - 1, y1: F, hx: w / 2, hz: d / 2, yaw: -yaw, tag: 'wood' }); }
    for (const sx of [-0.8, 0.8]) {
      const len = 14, drop = F + 0.8, ang = Math.atan2(drop, len);
      add(b.wood, new THREE.BoxGeometry(0.2, 0.18, Math.hypot(len, drop)), sx, F - drop / 2 - 0.1, d / 2 + len / 2, null, ang);
    }
    // gable roof
    const rise = 1.4, over = 0.3, slab = Math.hypot(w / 2, rise) + over, ang = Math.atan2(rise, w / 2);
    for (const sx of [-1, 1]) {
      const g = new THREE.BoxGeometry(slab, 0.05, d + over * 2);
      const [cx, cz] = L(sx * (w / 4), 0);
      b.roof.add(place(g, cx, F + H + rise / 2 + 0.03, cz, yaw, 0, -sx * ang), { paint: [-1, 0, 0], corrDir: [Math.sin(yaw), Math.cos(yaw)] });
    }
    for (const sz of [-1, 1]) {
      const shape = new THREE.Shape([new THREE.Vector2(-w / 2, 0), new THREE.Vector2(w / 2, 0), new THREE.Vector2(0, rise)]);
      const g = new THREE.ExtrudeGeometry(shape, { depth: 0.12, bevelEnabled: false }).translate(0, 0, -0.06);
      const [cx, cz] = L(0, sz * d / 2);
      b.board.add(place(g, cx, F + H, cz, yaw), paintA);
    }
    // inside: a dinghy on a trestle, oars, a workbench
    this._dinghy(x - 1.2, F + 0.75, z - 0.5, yaw + Math.PI / 2, true);
    add(b.wood, new THREE.BoxGeometry(2.4, 0.08, 0.7), 2.4, F + 0.9, -d / 2 + 0.6);
    for (const sx of [-1, 1]) add(b.wood, new THREE.BoxGeometry(0.08, 0.9, 0.6), 2.4 + sx * 1.1, F + 0.45, -d / 2 + 0.6);
  }

  _market() {
    const b = this.bins, col = this.collision;
    const x = 106, z = 4, yaw = 0.35;
    const F = this.h(x, z) + 0.05;
    const L = (lx, lz) => toWorld(x, z, yaw, lx, lz);
    const add = (bin, g, lx, ly, lz, extra, rx = 0) => { const [wx, wz] = L(lx, lz); bin.add(place(g, wx, ly, wz, yaw, rx), extra); };
    const w = 3.4, d = 2.2;
    for (const [sx, sz] of [[-1, -1], [1, -1], [-1, 1], [1, 1]]) {
      add(b.wood, new THREE.BoxGeometry(0.12, 2.6, 0.12), sx * w / 2, F + 1.3, sz * d / 2);
      const [cx, cz] = L(sx * w / 2, sz * d / 2);
      col.addCylinder({ x: cx, z: cz, y0: F, y1: F + 2.6, r: 0.1 });
    }
    add(b.board, new THREE.BoxGeometry(w, 2.5, 0.1), 0, F + 1.25, -d / 2, { paint: [0.3, 0.46, 0.55], groundY: F });
    // counter with fish crates on ice
    add(b.wood, new THREE.BoxGeometry(w - 0.2, 0.9, 0.7), 0, F + 0.45, d / 2 - 0.4);
    { const [cx, cz] = L(0, d / 2 - 0.4); col.addBox({ x: cx, z: cz, y0: F, y1: F + 0.95, hx: (w - 0.2) / 2, hz: 0.35, yaw: -yaw, walkable: false }); }
    for (let k = 0; k < 3; k++) {
      add(b.wood, new THREE.BoxGeometry(0.8, 0.14, 0.5), -1.05 + k * 1.05, F + 0.97, d / 2 - 0.4);
      add(b.cloth, new THREE.BoxGeometry(0.74, 0.04, 0.44), -1.05 + k * 1.05, F + 1.02, d / 2 - 0.4);
    }
    // striped awning
    const g = new THREE.BoxGeometry(w + 0.6, 0.03, d + 0.9);
    add(b.cloth, g, 0, F + 2.62, 0.35, null, -0.16);
    // the swinging fish sign on a bracket at the front corner
    const [sx, sz] = L(w / 2 + 0.2, d / 2 + 0.35);
    b.wood.add(place(new THREE.BoxGeometry(1.2, 0.07, 0.07), ...toWorld(x, z, yaw, w / 2 + 0.55, d / 2 + 0.35).flatMap((v, i) => (i === 0 ? [v, F + 2.55] : [v])), yaw));
    this._fishSign(new THREE.Vector3(...toWorld(x, z, yaw, w / 2 + 0.95, d / 2 + 0.35).flatMap((v, i) => (i === 0 ? [v, F + 2.51] : [v]))), yaw);
    void sx; void sz;
  }

  _fishSign(hook, yaw) {
    const pivot = new THREE.Group();
    pivot.position.copy(hook);
    pivot.rotation.y = yaw;
    const shape = new THREE.Shape();
    shape.moveTo(-0.55, 0);
    shape.bezierCurveTo(-0.35, 0.28, 0.25, 0.3, 0.42, 0.04);
    shape.lineTo(0.62, 0.2); shape.lineTo(0.58, -0.02); shape.lineTo(0.63, -0.22); shape.lineTo(0.42, -0.06);
    shape.bezierCurveTo(0.25, -0.3, -0.35, -0.28, -0.55, 0);
    const g = new THREE.ExtrudeGeometry(shape, { depth: 0.04, bevelEnabled: true, bevelThickness: 0.012, bevelSize: 0.012, bevelSegments: 2 });
    g.translate(0, -0.52, -0.02);
    const signMat = paintedWood(0x3d7ea6, 0.55);
    const fish = new THREE.Mesh(g, signMat);
    const eye = new THREE.Mesh(new THREE.SphereGeometry(0.035, 8, 6).translate(-0.36, -0.46, 0), standard({ color: 0xf2efe6, roughness: 0.5 }));
    const eye2 = eye.clone(); eye2.position.z = 0.001;
    const rings = new THREE.Mesh(mergeGeometries([
      new THREE.TorusGeometry(0.03, 0.006, 5, 10).translate(-0.3, -0.03, 0),
      new THREE.TorusGeometry(0.03, 0.006, 5, 10).translate(0.3, -0.03, 0),
      new THREE.CylinderGeometry(0.004, 0.004, 0.24, 4).translate(-0.3, -0.18, 0),
      new THREE.CylinderGeometry(0.004, 0.004, 0.24, 4).translate(0.3, -0.18, 0),
    ]), rustyMetal());
    pivot.add(fish, eye, rings);
    pivot.traverse((o) => { if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; } });
    this.group.add(pivot);
    this.swingers.push({ obj: pivot, phase: 0.4, amp: 0.2, freq: 1.1, axis: 'x' });
  }

  // ------------------------------------------------------------------ props
  _crateStack(x, y, z, yaw, n) {
    for (let k = 0; k < n; k++) {
      const cx = x + (k % 2) * 0.62, cz = z + Math.floor(k / 2) * 0.02, cy = y + (k >= 2 ? 0.46 : 0);
      this._crate(cx, cy, cz, yaw + R(-0.1, 0.1));
    }
  }

  _crate(x, y, z, yaw) {
    const b = this.bins;
    const W = 0.6, D = 0.42, H = 0.44;
    for (let k = 0; k < 3; k++) b.wood.add(boxAt(W, 0.11, D, x, y + 0.06 + k * 0.155, z, yaw));
    for (const [sx, sz] of [[-1, -1], [1, -1], [-1, 1], [1, 1]]) b.wood.add(boxAt(0.05, H, 0.05, x + sx * (W / 2 - 0.02) * Math.cos(yaw) + sz * (D / 2 - 0.02) * Math.sin(yaw), y + H / 2, z - sx * (W / 2 - 0.02) * Math.sin(yaw) + sz * (D / 2 - 0.02) * Math.cos(yaw), yaw));
    this.collision.addBox({ x, z, y0: y, y1: y + H, hx: W / 2, hz: D / 2, yaw: -yaw, tag: 'wood' });
  }

  _barrel(x, y, z) {
    const b = this.bins;
    const g = new THREE.CylinderGeometry(0.3, 0.3, 0.9, 16, 4);
    const p = g.attributes.position;
    for (let i = 0; i < p.count; i++) { const yy = p.getY(i); const k = 1 + 0.12 * Math.cos(yy / 0.45 * Math.PI / 2); p.setX(i, p.getX(i) * k); p.setZ(i, p.getZ(i) * k); }
    g.computeVertexNormals();
    b.wood.add(place(g, x, y + 0.45, z, R(0, 6)));
    for (const hy of [0.14, 0.76]) b.metal.add(place(new THREE.TorusGeometry(0.33, 0.012, 5, 20), x, y + hy, z, 0, Math.PI / 2));
    this.collision.addCylinder({ x, z, y0: y, y1: y + 0.9, r: 0.33, walkable: true });
  }

  _dinghy(x, y, z, yaw, upright = false) {
    // small clinker-ish hull, lofted like the big boat
    const L = 3.6, B = 1.35, NS = 20, NT = 8;
    const pos = [];
    const sect = (s, t) => {
      const hb = s < 0.55 ? B / 2 * (0.78 + 0.22 * Math.sin(Math.PI / 2 * s / 0.55)) : B / 2 * Math.pow(Math.max(Math.cos(Math.PI / 2 * (s - 0.55) / 0.45), 0), 0.7);
      const K = -0.32 + 0.3 * Math.pow(Math.max(s - 0.6, 0) / 0.4, 2), S = 0.18 + 0.12 * s * s;
      const u = 1 - t;
      const p0 = [0, K], p1 = [hb * 0.6, K + 0.08], p2 = [hb * 1.05, K + (S - K) * 0.4], p3 = [hb, S];
      return [u * u * u * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t * t * t * p3[0], u * u * u * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t * t * t * p3[1]];
    };
    const idx = [];
    for (const sg of [1, -1]) {
      const base = pos.length / 3;
      for (let i = 0; i <= NS; i++) for (let j = 0; j <= NT; j++) { const [px, py] = sect(Math.min(i / NS, 0.999), j / NT); pos.push(sg * px, py, L / 2 - i / NS * L); }
      for (let i = 0; i < NS; i++) for (let j = 0; j < NT; j++) {
        const a = base + i * (NT + 1) + j, bb = a + 1, c = a + NT + 1, d = c + 1;
        if (sg > 0) idx.push(a, c, bb, bb, c, d); else idx.push(a, bb, c, bb, d, c);
      }
    }
    const g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
    g.setIndex(idx);
    g.computeVertexNormals();
    const inner = g.clone();
    // inside face: flip normals so the upturned hull is closed for shadows and seen from inside
    const ia = inner.index.array;
    for (let i = 0; i < ia.length; i += 3) { const t = ia[i + 1]; ia[i + 1] = ia[i + 2]; ia[i + 2] = t; }
    inner.computeVertexNormals();
    const mtx = new THREE.Matrix4().compose(new THREE.Vector3(x, y, z), new THREE.Quaternion().setFromEuler(new THREE.Euler(upright ? 0 : Math.PI, yaw, 0, 'YXZ')), new THREE.Vector3(1, 1, 1));
    this.bins.hull.add(g.applyMatrix4(mtx));
    this.bins.hullIn.add(inner.applyMatrix4(mtx));
    // thwarts + gunwale
    if (upright) {
      for (const dz of [-0.4, 0.5]) this.bins.wood.add(place(new THREE.BoxGeometry(B * 0.85, 0.04, 0.2), x, y + 0.08, z, yaw, 0, 0).applyMatrix4(new THREE.Matrix4()).translate(0, 0, 0) && place(new THREE.BoxGeometry(B * 0.85, 0.04, 0.2), ...[x + Math.sin(yaw) * dz, y + 0.06, z + Math.cos(yaw) * dz], yaw));
    }
    this.collision.addBox({ x, z, y0: y - 0.35, y1: y + (upright ? 0.2 : 0.35), hx: B / 2, hz: L / 2, yaw: -yaw, walkable: !upright });
  }

  _beachProps() {
    const b = this.bins;
    // upturned dinghies on the upper beach (resting on their gunwales)
    for (const [x, z, yaw] of [[88, -1.5, 0.4], [92.5, 0.8, 0.25], [79, -4.5, -0.2]]) this._dinghy(x, this.h(x, z) + 0.34, z, yaw, false);
    // net drying racks with nets draped over
    for (const [x, z, yaw] of [[100, -8, 0.3], [141, 15, -0.5]]) {
      const y = this.h(x, z);
      const len = 5.5;
      for (const s of [-1, 1]) {
        const [px, pz] = toWorld(x, z, yaw, s * len / 2, 0);
        b.wood.add(cylAt(0.07, 0.08, 2.3, px, y + 1.1, pz, 7));
        this.collision.addCylinder({ x: px, z: pz, y0: y, y1: y + 2.3, r: 0.1 });
      }
      b.wood.add(place(new THREE.CylinderGeometry(0.05, 0.05, len + 0.4, 7), x, y + 2.15, z, yaw, 0, Math.PI / 2));
      // net: a sagging sheet hanging from the pole
      const ng = new THREE.PlaneGeometry(len - 0.3, 1.9, 24, 10);
      const p = ng.attributes.position;
      for (let i = 0; i < p.count; i++) {
        const px = p.getX(i), py = p.getY(i);
        const t = (py + 0.95) / 1.9;
        p.setZ(i, Math.sin((px / (len - 0.3) + 0.5) * Math.PI) * 0.18 * (1 - t) + Math.sin(px * 3.1) * 0.03);
        p.setY(i, py - (1 - Math.cos((px / (len - 0.3)) * Math.PI)) * 0.08 * (1 - t));
      }
      ng.computeVertexNormals();
      b.net.add(place(ng, x, y + 1.18, z, yaw));
      // floats along the top
      for (let k = 0; k < 9; k++) {
        const [fx, fz] = toWorld(x, z, yaw, -len / 2 + 0.5 + k * (len - 1) / 8, 0.05);
        b.orange.add(place(new THREE.SphereGeometry(0.08, 8, 6), fx, y + 2.05, fz));
      }
    }
    // lobster pots stacked near the pier root, crates, barrels
    for (let k = 0; k < 6; k++) {
      const x = 112 + (k % 3) * 0.95, z = 16 + Math.floor(k / 3) * 0.7, y = this.h(x, z);
      const pot = new THREE.BoxGeometry(0.9, 0.5, 0.6);
      b.net.add(place(pot, x, y + 0.25 + (k === 5 ? 0.5 : 0), z, 0.05 * k));
      b.wood.add(place(new THREE.BoxGeometry(0.92, 0.04, 0.62), x, y + 0.02, z, 0.05 * k));
      this.collision.addBox({ x, z, y0: y, y1: y + 0.5, hx: 0.45, hz: 0.3 });
    }
    this._crateStack(123, this.h(123, 18), 18, 0.2, 4);
    this._crateStack(102, this.h(102, 2), 2, -0.3, 2);
    for (const [x, z] of [[125.5, 16.5], [126.2, 17.2], [104, 7.5]]) this._barrel(x, this.h(x, z), z);
    // an old anchor and chain by the shed
    const ay = this.h(128, 12);
    b.metal.add(cylAt(0.05, 0.05, 1.3, 128, ay + 0.1, 12, 8, 0.4, Math.PI / 2));
    b.metal.add(place(new THREE.TorusGeometry(0.45, 0.05, 6, 14, Math.PI), 128, ay + 0.12, 12, 0.4, Math.PI / 2));
    // rocks at the pier root and along the berm
    for (let k = 0; k < 22; k++) {
      const x = k < 8 ? R(110, 127) : R(60, 170), z = k < 8 ? R(24, 34) : R(-12, 4);
      const s = R(0.35, k < 8 ? 1.4 : 0.8);
      const y = this.h(x, z);
      if (y < -0.5) continue;
      const g = new THREE.IcosahedronGeometry(s, 2);
      const p = g.attributes.position;
      const sx = R(0.8, 1.4), sy = R(0.5, 0.8), sz = R(0.8, 1.3);
      for (let i = 0; i < p.count; i++) {
        const vx = p.getX(i), vy = p.getY(i), vz = p.getZ(i);
        const n = 1 + 0.18 * Math.sin(vx * 4.1 + k) * Math.cos(vz * 3.7 - k) + 0.08 * Math.sin(vy * 9 + vx * 7);
        p.setXYZ(i, vx * sx * n, vy * sy * n, vz * sz * n);
      }
      g.computeVertexNormals();
      b.rock.add(place(g, x, y + s * sy * 0.35, z, R(0, 6)));
      this.collision.addCylinder({ x, z, y0: y - 1, y1: y + s * sy * 0.8, r: s * Math.max(sx, sz) * 0.8, walkable: true });
    }
  }

  // driftwood, branches and pebbles along the wrack line, ~2 m below the berm crest
  _debris() {
    const b = this.bins;
    const isl = this.island;
    let placed = 0;
    for (let k = 0; k < 400 && placed < 26; k++) {
      const x = R(-120, 200), z = R(-40, 70);
      const sdf = isl.sdfAt(x, z);
      if (sdf > -3.5 || sdf < -9) continue;            // high-water wrack line
      const y = isl.heightAt(x, z);
      if (y < 0.15 || y > 2.2) continue;
      if (Math.abs(x - VILLAGE.pierX) < 6 && z > 15) continue;
      placed++;
      const big = rnd() < 0.4;
      const len = big ? R(2.2, 4.5) : R(0.6, 1.8), r = big ? R(0.12, 0.26) : R(0.03, 0.08);
      const g = new THREE.CylinderGeometry(r * 0.8, r, len, 9, 6);
      const p = g.attributes.position;
      const bend = R(-0.25, 0.25);
      for (let i = 0; i < p.count; i++) {
        const yy = p.getY(i) / len;
        p.setX(i, p.getX(i) + bend * (1 - 4 * yy * yy) * len * 0.3 + Math.sin(yy * 17 + k) * r * 0.2);
      }
      g.computeVertexNormals();
      b.bark.add(place(g, x, y + r * 0.7, z, R(0, 6), 0, Math.PI / 2 + R(-0.1, 0.1)));
      if (big) this.collision.addBox({ x, z, y0: y, y1: y + r * 1.6, hx: r, hz: len / 2, yaw: 0, walkable: true });
      // a scatter of pebbles and a clump of weed around it
      for (let q = 0; q < 10; q++) {
        const px = x + R(-1.6, 1.6), pz = z + R(-1.6, 1.6), ps = R(0.03, 0.09);
        const pg = new THREE.IcosahedronGeometry(ps, 1).scale(1.2, 0.6, 1);
        b.rock.add(place(pg, px, isl.heightAt(px, pz) + ps * 0.3, pz, R(0, 6)));
      }
    }
  }

  // ------------------------------------------------------------------ assembly
  _assemble() {
    const b = this.bins, add = (m) => m && this.group.add(m);
    add(b.board.mesh(weatherboard(), 'village.walls'));
    add(b.roof.mesh(corrugated(), 'village.roofs'));
    add(b.deck.mesh(planks({ axis: 'z' }), 'village.deck'));
    add(b.deckX.mesh(planks({ axis: 'x' }), 'village.deckT'));
    add(b.pile.mesh(piling(), 'village.pilings'));
    add(b.stone.mesh(stone(), 'village.stone'));
    add(b.trim.mesh(paintedWood(0xe8e4da, 0.55), 'village.trim'));
    add(b.door.mesh(paintedWood(0x2f4d63, 0.5), 'village.doors'));
    add(b.glass.mesh(windowGlass(), 'village.glass'));
    add(b.wood.mesh(rawWood(), 'village.wood'));
    add(b.dark.mesh(standard({ color: 0x1b1b1b, roughness: 0.8 }), 'village.dark'));
    add(b.rope.mesh(rope(), 'village.rope'));
    add(b.metal.mesh(rustyMetal(), 'village.metal'));
    const nets = b.net.mesh(net(), 'village.nets');
    // the shadow pass ignores the mesh cut-out: a solid net shadow looks wrong
    if (nets) nets.castShadow = false;
    add(nets);
    add(b.cloth.mesh(canvasCloth(0xd9d2bf), 'village.cloth'));
    add(b.bark.mesh(barkWood(), 'village.driftwood'));
    add(b.red.mesh(standard({ color: 0xc8321f, roughness: 0.45 }), 'village.buoyR'));
    add(b.yellow.mesh(standard({ color: 0xe0b12a, roughness: 0.45 }), 'village.buoyY'));
    add(b.orange.mesh(standard({ color: 0xe86a1c, roughness: 0.5 }), 'village.buoyO'));
    add(b.rock.mesh(stone(3.2), 'village.rocks'));
    const hullMat = paintedWood(0x2e5c7a, 0.5);
    hullMat.shadowSide = THREE.DoubleSide;
    add(b.hull.mesh(hullMat, 'village.dinghies'));
    add(b.hullIn.mesh(paintedWood(0x8a7b63, 0.7), 'village.dinghiesIn'));
  }

  update(dt, time, env) {
    // wind-driven pendulums: lanterns on chains, the fish sign
    const gust = 0.6 + 0.4 * Math.sin(time * 0.37) * Math.sin(time * 0.11 + 1.3);
    for (const s of this.swingers) {
      const a = s.amp * gust * Math.sin(time * s.freq * 2 * Math.PI / 2 + s.phase) + s.amp * 0.3 * Math.sin(time * 2.7 + s.phase * 2);
      if (s.axis === 'x') s.obj.rotation.x = a; else { s.obj.rotation.x = a; s.obj.rotation.z = s.amp * 0.5 * gust * Math.sin(time * s.freq * 1.3 + s.phase); }
    }
    const n = env.nightFactor.value;
    const on = THREE.MathUtils.smoothstep(n, 0.2, 0.55);
    for (const l of this.lights) { l.light.intensity = l.max * on * (0.95 + 0.05 * Math.sin(time * 13 + l.max)); l.light.visible = on > 0.001; }
    const glow = 0.2 + 5.5 * on;
    for (const m of this.lampMats) m.color.setRGB(1.0 * glow, 0.72 * glow, 0.4 * glow);
  }
}
