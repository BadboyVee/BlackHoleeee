// Fish schools: GPU boids with procedural, animated fish.
//
// Each species keeps its own storage buffers and school anchor. Per frame a
// compute pass steers every fish: cohesion/alignment toward a few sampled
// school mates, separation, a wandering school target, the seabed and the
// surface as soft walls, and a scatter away from the swimmer or the boat.
// The fish are lofted bodies (fusiform or deep-bodied) with caudal, dorsal,
// anal and pectoral fins, rendered instanced; a travelling body wave drives
// the tail beat at a rate that follows each fish's speed.

import * as THREE from 'three/webgpu';
import {
  Fn, instancedArray, instanceIndex, uniform, vec2, vec3, vec4, float, uint, int, normalize, length, cross,
  dot, mix, clamp, smoothstep, sin, cos, max, min, abs, select, If, attribute, positionGeometry, normalGeometry,
  positionLocal, hash, varying, uv, fract, exp, pow, cameraViewMatrix,
} from 'three/tsl';
import { mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';
import { standard, previousPosition } from '../render/materials.js';
import { hash21, vnoise2 } from '../render/tslnoise.js';
import { env } from '../env.js';

// lofted fish body: x from 0 (snout) to 1 (tail peduncle), scaled to length L
function fishGeometry({ L, depth, width, tail = 0.28, dorsal = 0.5, deep = false }) {
  const NX = 22, NR = 12;
  const pos = [], uvs = [], idx = [];
  const prof = (t) => {
    // body outline: blunt head, max depth ~1/3 back, narrow peduncle
    const h = Math.pow(Math.sin(Math.PI * Math.min(1, Math.pow(t, 0.75) * 1.05)), deep ? 0.8 : 1.1) * (1 - 0.72 * Math.pow(t, 3));
    return Math.max(h, 0.04);
  };
  for (let i = 0; i <= NX; i++) {
    const t = i / NX;
    const s = prof(t);
    const hh = depth * s * L, ww = width * s * L * (1 - 0.3 * t);
    for (let j = 0; j <= NR; j++) {
      const a = j / NR * Math.PI * 2;
      const y = Math.sin(a) * hh * (Math.sin(a) < 0 ? 0.85 : 1);
      pos.push((0.5 - t) * L, y, Math.cos(a) * ww);
      uvs.push(t, j / NR);
    }
  }
  for (let i = 0; i < NX; i++) for (let j = 0; j < NR; j++) {
    const a = i * (NR + 1) + j, b = a + 1, c = a + NR + 1, d = c + 1;
    idx.push(a, b, c, b, d, c);
  }
  const body = new THREE.BufferGeometry();
  body.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  body.setAttribute('uv', new THREE.Float32BufferAttribute(uvs, 2));
  body.setIndex(idx);
  body.computeVertexNormals();
  const fin = (pts, uvT) => {
    const shape = new THREE.Shape(pts.map(([x, y]) => new THREE.Vector2(x, y)));
    const g = new THREE.ShapeGeometry(shape);
    const uva = new Float32Array(g.attributes.position.count * 2);
    for (let i = 0; i < g.attributes.position.count; i++) { uva[i * 2] = uvT; uva[i * 2 + 1] = 0.5; }
    g.setAttribute('uv', new THREE.BufferAttribute(uva, 2));
    return g;
  };
  const xT = -0.5 * L, hT = depth * prof(1) * L;
  // forked caudal fin
  const cf = fin([[xT + 0.02 * L, hT * 0.6], [xT - tail * L, tail * L * 0.95], [xT - tail * L * 0.72, 0], [xT - tail * L, -tail * L * 0.9], [xT + 0.02 * L, -hT * 0.6]], 1.02);
  // dorsal + anal fins (in the median plane)
  const xd = (0.5 - dorsal) * L, dh = depth * prof(dorsal) * L;
  const df = fin([[xd + 0.12 * L, dh * 0.9], [xd + 0.02 * L, dh + depth * L * (deep ? 0.55 : 0.32)], [xd - 0.22 * L, dh * 0.75], [xd - 0.2 * L, dh * 0.6]], dorsal);
  const af = fin([[xd - 0.05 * L, -dh * 0.8], [xd - 0.12 * L, -dh - depth * L * (deep ? 0.4 : 0.18)], [xd - 0.26 * L, -dh * 0.55]], dorsal + 0.1);
  // pectoral fins, angled out from the flanks
  const pf = [];
  for (const s of [-1, 1]) {
    const g = fin([[0, 0], [-0.13 * L, 0.03 * L], [-0.11 * L, -0.03 * L]], 0.3);
    g.rotateX(s * 1.2).rotateY(s * 0.4).translate(0.22 * L, -depth * L * 0.25, s * width * L * 0.7);
    pf.push(g);
  }
  const parts = [body, cf, df, af, ...pf].map((g) => {
    const q = g.index ? g.toNonIndexed() : g;
    q.computeVertexNormals();
    return q;
  });
  return mergeGeometries(parts);
}

const SPECIES = [
  // silvery schooling fish (sardine / jack): big tight schools in open water
  { name: 'jacks', count: 520, L: 0.28, depth: 0.2, width: 0.09, tail: 0.3, deep: false, speed: 1.3, schools: 3, radius: 5, spread: 110, colors: [[0.12, 0.2, 0.26], [0.72, 0.76, 0.78]], metal: 0.65, stripes: 0.0, rough: 0.28, yRange: [-7, -1.5] },
  // yellow-and-blue reef fish, small loose groups over the coral
  { name: 'reef', count: 180, L: 0.2, depth: 0.42, width: 0.08, tail: 0.24, deep: true, speed: 0.55, schools: 9, radius: 3, spread: 70, colors: [[0.06, 0.12, 0.35], [0.95, 0.72, 0.1]], metal: 0.05, stripes: 1.0, rough: 0.45, yRange: [-6, -1.2] },
  // pilot fish that ride the whale's pressure wave, just ahead of its head
  { name: 'pilot', follow: true, count: 64, L: 0.3, depth: 0.24, width: 0.09, tail: 0.3, deep: false, speed: 3.0, schools: 1, radius: 2.5, spread: 1, colors: [[0.1, 0.16, 0.24], [0.62, 0.68, 0.74]], metal: 0.5, stripes: 0.9, rough: 0.32, yRange: [-15, -1.4] },
  // a few bigger fish (grouper / snapper) near the bottom
  { name: 'snapper', count: 24, L: 0.75, depth: 0.28, width: 0.12, tail: 0.24, deep: false, speed: 0.7, schools: 4, radius: 5, spread: 80, colors: [[0.32, 0.12, 0.1], [0.8, 0.52, 0.42]], metal: 0.15, stripes: 0.3, rough: 0.4, yRange: [-10, -2.5] },
];

export class Fish {
  constructor(renderer, { scene, terrain, reef, extraAnchors = [], escortStart = null }) {
    this.renderer = renderer;
    this.terrain = terrain;
    this.groups = [];
    this.flee = uniform(new THREE.Vector3(0, -1000, 0));
    // the whale's body (a capsule, head to flukes) that every fish keeps clear of
    this.avoidA = uniform(new THREE.Vector3(0, -1000, 0));
    this.avoidB = uniform(new THREE.Vector3(0, -1000, 1));
    this.avoidR = uniform(1.5);
    this.dt = uniform(0);
    this.time = uniform(0);
    this._fwd = new THREE.Vector3();
    const escort = escortStart ? { x: escortStart.x, z: escortStart.z } : reef;
    for (const sp of SPECIES) this.groups.push(this._species(sp, sp.follow ? escort : reef, scene, extraAnchors));
  }

  _species(sp, reef, scene, extraAnchors) {
    const N = sp.count;
    const pos = instancedArray(N, 'vec4');   // xyz, phase
    const vel = instancedArray(N, 'vec4');   // xyz, school index
    const anchors = [];
    for (let s = 0; s < sp.schools; s++) {
      const a = (s / sp.schools) * Math.PI * 2;
      const r = sp.spread * (0.3 + 0.7 * ((s * 0.618) % 1));
      anchors.push(new THREE.Vector3(reef.x + Math.cos(a) * r * 0.8, 0, reef.z + Math.sin(a) * r));
    }
    for (const e of extraAnchors) if (sp.name === 'jacks') anchors.push(e.clone());
    // school targets are a uniform array updated on the CPU (wandering)
    const targetU = [];
    for (let k = 0; k < 16; k++) targetU.push(uniform(new THREE.Vector4(0, 0, 0, 0)));
    // initial state (CPU)
    const p0 = pos.value.array, v0 = vel.value.array;
    for (let i = 0; i < N; i++) {
      const s = i % anchors.length;
      const a = anchors[s];
      p0[i * 4] = a.x + (Math.random() - 0.5) * sp.radius * 2;
      p0[i * 4 + 1] = (sp.yRange[0] + sp.yRange[1]) / 2 + (Math.random() - 0.5) * 2;
      p0[i * 4 + 2] = a.z + (Math.random() - 0.5) * sp.radius * 2;
      p0[i * 4 + 3] = Math.random() * 100;
      v0[i * 4] = (Math.random() - 0.5) * sp.speed; v0[i * 4 + 1] = 0; v0[i * 4 + 2] = (Math.random() - 0.5) * sp.speed;
      v0[i * 4 + 3] = s;
    }
    pos.value.needsUpdate = true; vel.value.needsUpdate = true;
    const T = this.terrain;
    const kernel = Fn(() => {
      const i = instanceIndex;
      const p = pos.element(i).toVar();
      const v = vel.element(i).toVar();
      const school = int(v.w);
      // school target (select from the uniform list)
      let tgt = targetU[0];
      for (let k = 1; k < anchors.length; k++) tgt = select(school.equal(k), targetU[k], tgt);
      const tv = vec4(tgt).toVar();
      const toT = tv.xyz.sub(p.xyz);
      const steer = normalize(toT.add(vec3(1e-4, 0, 0))).mul(smoothstep(0.0, sp.radius * 1.5, length(toT))).mul(1.2).toVar();
      // a few pseudo-random school mates: alignment, cohesion, separation
      const align = vec3(0).toVar(), coh = vec3(0).toVar(), sep = vec3(0).toVar();
      for (let k = 0; k < 6; k++) {
        const j = uint(hash21(vec2(float(i), float(k).add(fract(this.time.mul(0.37)).mul(13)))).mul(N)).min(uint(N - 1));
        const q = pos.element(j), w = vel.element(j);
        const same = select(int(w.w).equal(school), float(1), float(0));
        const d = q.xyz.sub(p.xyz);
        const dl = length(d);
        const near = smoothstep(sp.L * 12, sp.L * 2, dl).mul(same);
        align.addAssign(w.xyz.mul(near));
        coh.addAssign(d.mul(near));
        sep.subAssign(d.div(dl.mul(dl).add(0.01)).mul(smoothstep(sp.L * 3.5, sp.L * 0.8, dl)).mul(same));
      }
      steer.addAssign(align.mul(0.12).add(coh.mul(0.08)).add(sep.mul(sp.L * 0.9)));
      // seabed and surface walls
      const bed = T.sampleLevel(p.xz).x;
      steer.y.addAssign(smoothstep(1.4, 0.3, p.y.sub(bed)).mul(2.5));
      steer.y.addAssign(smoothstep(sp.yRange[1] - 1.5, sp.yRange[1] + 0.5, p.y).mul(-2.0));
      steer.y.addAssign(smoothstep(sp.yRange[0] + 1, sp.yRange[0] - 1, p.y).mul(1.0));
      // scatter from the swimmer / hull
      const df = p.xyz.sub(this.flee);
      const fl = length(df);
      const scare = smoothstep(4.5, 1.2, fl);
      steer.addAssign(normalize(df.add(vec3(0, 1e-3, 0))).mul(scare.mul(6)));
      // keep clear of the whale
      const ab = this.avoidB.sub(this.avoidA);
      const tq = clamp(dot(p.xyz.sub(this.avoidA), ab).div(dot(ab, ab).max(1e-4)), 0, 1);
      const dw = p.xyz.sub(this.avoidA.add(ab.mul(tq)));
      const dwl = length(dw);
      steer.addAssign(dw.div(dwl.max(1e-3)).mul(smoothstep(this.avoidR.add(1.5), this.avoidR, dwl).mul(6)));
      // integrate with a speed that rises when scared, never stopping
      const dt = this.dt;
      const nv = v.xyz.add(steer.mul(dt).mul(sp.speed * 1.6)).toVar();
      const spd = length(nv);
      const want = clamp(spd, sp.speed * 0.5, float(sp.speed).mul(scare.mul(2.5).add(1)));
      nv.assign(nv.div(spd.max(1e-4)).mul(want));
      nv.y.mulAssign(0.7);
      const np = p.xyz.add(nv.mul(dt));
      pos.element(i).assign(vec4(np, p.w.add(dt.mul(want.div(sp.L).mul(1.8)))));
      vel.element(i).assign(vec4(nv, v.w));
    })().compute(N, [64]);

    // mesh + material
    const geom = fishGeometry(sp);
    const inst = new THREE.InstancedBufferGeometry().copy(geom);
    inst.instanceCount = N;
    const mat = standard({ roughness: sp.rough, metalness: sp.metal, side: THREE.DoubleSide });
    const P = pos.toAttribute(), V = vel.toAttribute();
    const g = positionGeometry;
    const t = clamp(float(0.5).sub(g.x.div(sp.L)), 0, 1.3);           // 0 snout .. 1 tail
    // travelling body wave, amplitude growing toward the tail
    const phase = P.w;
    const amp = t.mul(t).mul(sp.L * 0.16).add(t.mul(sp.L * 0.02));
    const wave = sin(phase.mul(6.2831).sub(t.mul(4.0)));
    const local = vec3(g.x, g.y, g.z.add(wave.mul(amp)));
    // orient: forward = velocity
    const f = normalize(V.xyz.add(vec3(1e-4, 0, 0)));
    const right = normalize(cross(vec3(0, 1, 0), f).add(vec3(0, 0, 1e-4)));
    const up = cross(f, right);
    const world = P.xyz.add(f.mul(local.x)).add(up.mul(local.y)).add(right.mul(local.z).negate());
    mat.positionNode = world;
    // where it was last frame, for the velocity buffer (TAA, motion blur)
    previousPosition(mat, world.sub(V.xyz.mul(this.dt)));
    const n = normalGeometry;
    const nW = normalize(f.mul(n.x).add(up.mul(n.y)).add(right.mul(n.z).negate()));
    mat.normalNode = cameraViewMatrix.mul(vec4(nW, 0)).xyz;
    // countershading: dark back, silvery belly; stripes on reef fish; eye spot
    const vuv = varying(vec2(t, g.y.div(sp.L * sp.depth + 1e-4)), 'vFishUV');
    const back = vec3(...sp.colors[0]), belly = vec3(...sp.colors[1]);
    const shade = smoothstep(-0.25, 0.45, vuv.y);
    let col = mix(belly, back, shade);
    if (sp.stripes > 0) {
      const stripe = smoothstep(0.35, 0.6, sin(vuv.x.mul(18)).mul(0.5).add(0.5));
      col = mix(col, back.mul(0.4), stripe.mul(sp.stripes).mul(smoothstep(0.1, 0.35, vuv.x)).mul(smoothstep(0.95, 0.7, vuv.x)));
    }
    const eye = smoothstep(0.06, 0.035, length(vec2(vuv.x.sub(0.12).mul(1.4), vuv.y.sub(0.25).abs().sub(0.0))));
    col = mix(col, vec3(0.02), eye);
    mat.colorNode = col;
    const mesh = new THREE.Mesh(inst, mat);
    mesh.frustumCulled = false;
    mesh.castShadow = false;
    mesh.receiveShadow = true;
    mesh.name = `fish.${sp.name}`;
    scene.add(mesh);
    return { sp, kernel, targetU, anchors, mesh, wander: anchors.map(() => ({ a: Math.random() * 6, r: Math.random() })) };
  }

  /** follow: the whale ({ pos, heading, pitch, length }) or null */
  update(dt, time, flee, follow = null) {
    this.dt.value = Math.min(dt, 0.05);
    this.time.value = time;
    this.flee.value.copy(flee);
    if (follow) {
      const f = this._fwd.set(Math.sin(follow.heading) * Math.cos(follow.pitch), Math.sin(follow.pitch), -Math.cos(follow.heading) * Math.cos(follow.pitch));
      this.avoidA.value.copy(follow.pos).addScaledVector(f, follow.length * 0.4);
      this.avoidB.value.copy(follow.pos).addScaledVector(f, -follow.length * 0.42);
    }
    if (dt <= 0) return;
    for (const g of this.groups) {
      const { sp } = g;
      if (sp.follow) {
        if (!follow) continue;
        // a loose knot just ahead of and below the whale's head, drifting side to side
        const f = this._fwd;
        const t = g.targetU[0].value;
        t.set(this.avoidA.value.x + f.x * 2.5 - f.z * Math.sin(time * 0.31) * 2.5, 0, this.avoidA.value.z + f.z * 2.5 + f.x * Math.sin(time * 0.31) * 2.5, 0);
        t.y = THREE.MathUtils.clamp(this.avoidA.value.y - 1.6, sp.yRange[0] + 1, sp.yRange[1] - 1);
        this.renderer.compute(g.kernel);
        continue;
      }
      g.anchors.forEach((a, k) => {
        const w = g.wander[k];
        w.a += dt * 0.07 * (0.5 + w.r);
        const R = sp.radius * 4 + 6;
        const y = sp.yRange[0] + (sp.yRange[1] - sp.yRange[0]) * (0.5 + 0.4 * Math.sin(time * 0.05 + k));
        g.targetU[k].value.set(a.x + Math.cos(w.a) * R, y, a.z + Math.sin(w.a * 1.3) * R, 0);
      });
      this.renderer.compute(g.kernel);
    }
  }
}
