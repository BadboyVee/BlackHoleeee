// Seagulls wheeling over the pier, the village and the surf.
//
// Each gull follows its own drifting loop, banking into turns, mostly
// gliding with bursts of flapping when it climbs. The body is a small
// procedural mesh; wings have an inner and an outer segment that fold with
// the flap in the vertex shader (per-instance phase/amplitude attribute).

import * as THREE from 'three/webgpu';
import { attribute, positionGeometry, vec3, float, sin, cos, mix, select, abs, max, clamp } from 'three/tsl';
import { mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';
import { standard, deform } from '../render/materials.js';

function tag(g, seg, side) {
  const n = g.attributes.position.count;
  g.setAttribute('wing', new THREE.BufferAttribute(new Float32Array(n * 2).map((_, i) => (i % 2 === 0 ? seg : side)), 2));
  const q = g.index ? g.toNonIndexed() : g;
  for (const k of Object.keys(q.attributes)) if (!['position', 'normal', 'wing'].includes(k)) q.deleteAttribute(k);
  if (!q.attributes.normal) q.computeVertexNormals();
  return q;
}

function gullGeometry() {
  // body along -z (forward), wings along x, span ~1.3 m
  const body = new THREE.SphereGeometry(0.1, 12, 8).scale(0.85, 0.8, 2.4);
  const head = new THREE.SphereGeometry(0.065, 10, 8).translate(0, 0.05, -0.27);
  const beak = new THREE.ConeGeometry(0.018, 0.08, 6).rotateX(-Math.PI / 2).translate(0, 0.04, -0.36);
  const tail = new THREE.BoxGeometry(0.14, 0.012, 0.12).translate(0, 0, 0.27);
  const parts = [tag(body, 0, 0), tag(head, 0, 0), tag(tail, 0, 0)];
  const beakG = tag(beak, 3, 0);
  for (const side of [-1, 1]) {
    // inner wing: root chord 0.2, to 0.32 m out; outer: tapering tip to 0.65 m
    const inner = new THREE.BufferGeometry();
    inner.setAttribute('position', new THREE.Float32BufferAttribute([
      0, 0, -0.1, side * 0.32, 0.01, -0.08, side * 0.32, 0.01, 0.1,
      0, 0, -0.1, side * 0.32, 0.01, 0.1, 0, 0, 0.1,
    ], 3));
    inner.computeVertexNormals();
    const outer = new THREE.BufferGeometry();
    outer.setAttribute('position', new THREE.Float32BufferAttribute([
      side * 0.32, 0.01, -0.08, side * 0.66, 0.0, 0.02, side * 0.32, 0.01, 0.1,
    ], 3));
    outer.computeVertexNormals();
    parts.push(tag(inner, 1, side), tag(outer, 2, side));
  }
  return { body: mergeGeometries(parts), beak: beakG };
}

export class Birds {
  constructor({ scene, count = 14, center = new THREE.Vector3(118, 0, 20) }) {
    const g = gullGeometry();
    this.count = count;
    const flap = new THREE.InstancedBufferAttribute(new Float32Array(count * 2), 2);
    flap.setUsage(THREE.DynamicDrawUsage);
    g.body.setAttribute('flap', flap);
    g.beak.setAttribute('flap', flap);
    this.flap = flap;
    const mat = standard({ roughness: 0.7, metalness: 0, side: THREE.DoubleSide });
    const w = attribute('wing', 'vec2'), f = attribute('flap', 'vec2');
    const p = positionGeometry;
    // fold the wing: inner segment rotates about the body axis, the outer
    // segment rotates further about the inner wing's tip
    const a1 = f.y.mul(sin(f.x)).mul(0.9).mul(w.y);
    const a2 = f.y.mul(sin(f.x.sub(0.6))).mul(0.6).mul(w.y);
    const side = w.y;
    const r1x = p.x.mul(cos(a1)).sub(p.y.mul(sin(a1))), r1y = p.x.mul(sin(a1)).add(p.y.mul(cos(a1)));
    const tip = vec3(side.mul(0.32).mul(cos(a1)), side.mul(0.32).mul(sin(a1)), 0);
    const ox = p.x.sub(side.mul(0.32)), oy = p.y.sub(0.01);
    const r2x = ox.mul(cos(a1.add(a2))).sub(oy.mul(sin(a1.add(a2)))).add(tip.x);
    const r2y = ox.mul(sin(a1.add(a2))).add(oy.mul(cos(a1.add(a2)))).add(tip.y);
    const isInner = w.x.greaterThan(0.5).and(w.x.lessThan(1.5));
    const isOuter = w.x.greaterThan(1.5).and(w.x.lessThan(2.5));
    // (folded in the bird's own frame, before the instance transform)
    deform(mat, vec3(select(isOuter, r2x, select(isInner, r1x, p.x)), select(isOuter, r2y, select(isInner, r1y, p.y)), p.z));
    // plumage: white body/head, grey mantle and wings, black wing tips
    const wingTop = mix(vec3(0.55, 0.57, 0.6), vec3(0.04, 0.04, 0.05), select(isOuter, clamp(abs(p.x).sub(0.5).div(0.14), 0, 1), float(0)));
    mat.colorNode = select(w.x.greaterThan(0.5), wingTop, vec3(0.92, 0.92, 0.9));
    this.mesh = new THREE.InstancedMesh(g.body, mat, count);
    const beakMat = standard({ color: 0xe8b830, roughness: 0.5 });
    this.beaks = new THREE.InstancedMesh(g.beak, beakMat, count);
    for (const m of [this.mesh, this.beaks]) { m.castShadow = true; m.frustumCulled = false; scene.add(m); }
    this.birds = [];
    for (let i = 0; i < count; i++) {
      this.birds.push({
        c: center.clone().add(new THREE.Vector3((Math.random() - 0.5) * 140, 0, (Math.random() - 0.5) * 120)),
        r: 12 + Math.random() * 30, h: 9 + Math.random() * 22, w: (0.12 + Math.random() * 0.1) * (Math.random() < 0.5 ? -1 : 1),
        a: Math.random() * 6.28, phase: Math.random() * 6, flapT: 0, pos: new THREE.Vector3(), prev: new THREE.Vector3(),
      });
    }
    this.m4 = new THREE.Matrix4();
  }

  update(dt, time) {
    const q = new THREE.Quaternion(), s = new THREE.Vector3(1, 1, 1), e = new THREE.Euler();
    this.birds.forEach((b, i) => {
      b.a += b.w * dt;
      b.c.x += Math.sin(time * 0.02 + i) * dt * 0.8;
      b.c.z += Math.cos(time * 0.017 + i * 1.3) * dt * 0.8;
      const hh = b.h + Math.sin(time * 0.3 + b.phase) * 3;
      b.prev.copy(b.pos);
      b.pos.set(b.c.x + Math.cos(b.a) * b.r, hh, b.c.z + Math.sin(b.a) * b.r);
      const vel = b.pos.clone().sub(b.prev);
      const climbing = vel.y > 0.02 * dt * 60;
      // flap in bursts (and while climbing), glide otherwise
      b.flapT = Math.max(0, b.flapT - dt);
      if (Math.random() < dt * 0.15 || climbing) b.flapT = Math.max(b.flapT, 1.2 + Math.random() * 1.5);
      const flapping = b.flapT > 0;
      b.phase += dt * (flapping ? 11 : 0.8);
      const amp = flapping ? 0.55 : 0.06;
      this.flap.setXY(i, b.phase, amp);
      const yaw = Math.atan2(vel.x, -vel.z);
      const bank = -b.w * 3.2;
      e.set(Math.atan2(vel.y, Math.hypot(vel.x, vel.z) + 1e-6) * 0.5, -yaw, bank, 'YXZ');
      q.setFromEuler(e);
      this.m4.compose(b.pos, q, s);
      this.mesh.setMatrixAt(i, this.m4);
      this.beaks.setMatrixAt(i, this.m4);
    });
    this.flap.needsUpdate = true;
    this.mesh.instanceMatrix.needsUpdate = true;
    this.beaks.instanceMatrix.needsUpdate = true;
  }
}
