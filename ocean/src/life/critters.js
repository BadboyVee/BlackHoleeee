// Ghost crabs on the wet sand, and motes of dust and salt in the air.
//
// Crabs idle near the swash line, sidle away when you come close, then dig
// in (sink and fade) and reappear somewhere else along the beach a while
// later. Motes are tiny sprites drifting with the wind in a box around the
// eye; they only show when they catch light against the sun.

import * as THREE from 'three/webgpu';
import {
  attribute, positionGeometry, vec3, vec4, float, sin, cos, mix, abs, select, uniform, instanceIndex, fract, floor,
  cameraPosition, cameraViewMatrix, cameraProjectionMatrix, normalize, dot, max, pow, smoothstep, uv, length, hash,
  positionWorld, Fn, instancedArray, varying,
} from 'three/tsl';
import { mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';
import { standard, deform } from '../render/materials.js';
import { env } from '../env.js';

function crabGeometry() {
  const parts = [];
  const tagG = (g, leg) => {
    const q = g.index ? g.toNonIndexed() : g;
    const n = q.attributes.position.count;
    q.setAttribute('leg', new THREE.BufferAttribute(new Float32Array(n).fill(leg), 1));
    for (const k of Object.keys(q.attributes)) if (!['position', 'normal', 'leg'].includes(k)) q.deleteAttribute(k);
    return q;
  };
  parts.push(tagG(new THREE.SphereGeometry(0.05, 10, 6).scale(1.25, 0.45, 1.0).translate(0, 0.035, 0), 0));
  for (const s of [-1, 1]) {
    // eye stalks
    parts.push(tagG(new THREE.CylinderGeometry(0.004, 0.004, 0.025, 4).translate(s * 0.02, 0.065, -0.035), 0));
    parts.push(tagG(new THREE.SphereGeometry(0.008, 6, 4).translate(s * 0.02, 0.079, -0.035), 9));
    // claws
    parts.push(tagG(new THREE.SphereGeometry(0.018, 6, 4).scale(1.3, 0.8, 1.6).translate(s * 0.05, 0.03, -0.055), 0));
    // 4 walking legs per side
    for (let k = 0; k < 4; k++) {
      const z = -0.03 + k * 0.022;
      const g = new THREE.CylinderGeometry(0.004, 0.003, 0.07, 4).rotateZ(s * 1.0).translate(s * 0.075, 0.02, z);
      parts.push(tagG(g, 1 + k + (s > 0 ? 4 : 0)));
    }
  }
  return mergeGeometries(parts);
}

export class Crabs {
  constructor({ scene, island, count = 24 }) {
    this.island = island;
    this.count = count;
    const g = crabGeometry();
    const data = new THREE.InstancedBufferAttribute(new Float32Array(count * 4), 4);   // walk phase, fade, -, -
    data.setUsage(THREE.DynamicDrawUsage);
    g.setAttribute('crab', data);
    this.data = data;
    const mat = standard({ roughness: 0.6 });
    const leg = attribute('leg', 'float'), cd = attribute('crab', 'vec4');
    const p = positionGeometry;
    const isLeg = leg.greaterThan(0.5).and(leg.lessThan(8.5));
    const lift = sin(cd.x.add(leg.mul(1.7))).mul(0.012).max(0).mul(select(isLeg, float(1), float(0)));
    // leg lift in the crab's own frame; shrinking and sinking into the sand
    // happen in the instance matrix, so the shadow goes with it
    deform(mat, vec3(p.x, p.y.add(lift), p.z));
    mat.colorNode = select(leg.greaterThan(8.5), vec3(0.02), mix(vec3(0.78, 0.7, 0.56), vec3(0.62, 0.55, 0.43), select(isLeg, float(1), float(0))));
    mat.opacityNode = cd.y;
    mat.alphaTest = 0.02;
    this.mesh = new THREE.InstancedMesh(g, mat, count);
    this.mesh.castShadow = true;
    this.mesh.frustumCulled = false;
    scene.add(this.mesh);
    this.crabs = [];
    for (let i = 0; i < count; i++) this.crabs.push(this._spawn({}));
    this.m4 = new THREE.Matrix4();
  }

  _spawn(c) {
    // somewhere on the damp upper beach (1-8 m above the swash line)
    for (let k = 0; k < 60; k++) {
      const x = -180 + Math.random() * 380, z = -30 + Math.random() * 90;
      const sdf = this.island.sdfAt(x, z), h = this.island.heightAt(x, z);
      if (sdf > -2 || sdf < -12 || h < 0.1 || h > 1.6) continue;
      Object.assign(c, { x, z, yaw: Math.random() * 6.28, state: 'idle', fade: 0, phase: Math.random() * 6, t: Math.random() * 5, vx: 0, vz: 0, hidden: 0 });
      return c;
    }
    return Object.assign(c, { x: 0, z: 0, state: 'hidden', fade: 0, hidden: 5, phase: 0, t: 0, vx: 0, vz: 0, yaw: 0 });
  }

  update(dt, player) {
    const q = new THREE.Quaternion(), s = new THREE.Vector3(1, 1, 1), up = new THREE.Vector3(0, 1, 0), p = new THREE.Vector3();
    const px = player.eye.x, pz = player.eye.z;
    this.crabs.forEach((c, i) => {
      c.t += dt;
      const d = Math.hypot(c.x - px, c.z - pz);
      if (c.state === 'hidden') { c.hidden -= dt; c.fade = 0; if (c.hidden <= 0) this._spawn(c); }
      else if (c.state === 'idle') {
        c.fade = Math.min(1, c.fade + dt * 1.5);
        if (Math.random() < dt * 0.3) { c.yaw += (Math.random() - 0.5) * 1.5; }
        if (d < 5.5 && player.mode !== 'fly') {
          // scuttle sideways, away from the intruder
          c.state = 'flee'; c.t = 0;
          const ax = (c.x - px) / d, az = (c.z - pz) / d;
          const sp = 2.2 + Math.random() * 1.3;
          c.vx = ax * sp; c.vz = az * sp;
          c.yaw = Math.atan2(az, -ax) + (Math.random() < 0.5 ? 0 : Math.PI);
        }
      } else if (c.state === 'flee') {
        c.x += c.vx * dt; c.z += c.vz * dt;
        c.phase += dt * 30;
        if (c.t > 1.2 + Math.random() * 0.8) { c.state = 'dig'; c.t = 0; }
      } else if (c.state === 'dig') {
        c.fade = Math.max(0, c.fade - dt * 1.4);
        c.phase += dt * 12;
        if (c.fade <= 0) { c.state = 'hidden'; c.hidden = 8 + Math.random() * 20; }
      }
      const y = this.island.heightAt(c.x, c.z);
      p.set(c.x, y - (1 - c.fade) * 0.08, c.z);
      q.setFromAxisAngle(up, c.yaw);
      s.setScalar(c.state === 'hidden' ? 0 : c.fade * 0.3 + 0.7);
      this.m4.compose(p, q, s);
      this.mesh.setMatrixAt(i, this.m4);
      this.data.setXY(i, c.phase, c.fade);
    });
    this.mesh.instanceMatrix.needsUpdate = true;
    this.data.needsUpdate = true;
  }
}

export class Motes {
  constructor({ scene, count = 1800, box = 22 }) {
    this.box = uniform(box);
    this.eye = uniform(new THREE.Vector3());
    const g = new THREE.InstancedBufferGeometry();
    g.index = new THREE.BufferAttribute(new Uint16Array([0, 1, 2, 0, 2, 3]), 1);
    g.setAttribute('position', new THREE.BufferAttribute(new Float32Array([-1, -1, 0, 1, -1, 0, 1, 1, 0, -1, 1, 0]), 3));
    g.setAttribute('uv', new THREE.BufferAttribute(new Float32Array([0, 0, 1, 0, 1, 1, 0, 1]), 2));
    const seeds = new Float32Array(count * 4);
    for (let i = 0; i < count * 4; i++) seeds[i] = Math.random();
    g.setAttribute('seed', new THREE.InstancedBufferAttribute(seeds, 4));
    g.instanceCount = count;
    const mat = new THREE.MeshBasicNodeMaterial();
    mat.transparent = true;
    mat.depthWrite = false;
    mat.blending = THREE.AdditiveBlending;
    const sd = attribute('seed', 'vec4');
    const B = this.box;
    // drift with the wind, wrapped into a box that follows the eye
    const drift = vec3(env.windDir.x, 0.05, env.windDir.y).mul(env.time.mul(0.35)).add(vec3(sin(env.time.mul(0.3).add(sd.w.mul(40))), sin(env.time.mul(0.23).add(sd.w.mul(20))).mul(0.4), cos(env.time.mul(0.27).add(sd.w.mul(30)))).mul(0.4));
    const local = fract(sd.xyz.add(drift.div(B)).sub(this.eye.div(B))).sub(0.5).mul(B);
    const world = this.eye.add(local);
    const view = cameraViewMatrix.mul(vec4(world, 1));
    const size = sd.w.mul(0.012).add(0.004);
    mat.vertexNode = cameraProjectionMatrix.mul(vec4(view.xy.add(positionGeometry.xy.mul(size)), view.z, 1));
    const vW = varying(world, 'vMote');
    const V = normalize(vW.sub(cameraPosition));
    const forward = pow(max(dot(V, env.sunDir), 0), 8);
    const dist = length(vW.sub(cameraPosition));
    const disc = smoothstep(1.0, 0.0, length(uv().mul(2).sub(1)));
    const fadeD = smoothstep(0.3, 1.2, dist).mul(smoothstep(11, 6, dist));
    mat.colorNode = env.sunColor.mul(forward.mul(0.02).add(0.0004)).mul(disc).mul(fadeD).mul(float(1).sub(env.cameraUnderwater));
    this.mesh = new THREE.Mesh(g, mat);
    this.mesh.frustumCulled = false;
    this.mesh.renderOrder = 40;
    this.mesh.layers.set(3);
    scene.add(this.mesh);
  }

  update(camera) { this.eye.value.copy(camera.position); }
}
