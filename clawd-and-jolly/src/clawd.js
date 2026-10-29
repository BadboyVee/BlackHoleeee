// Clawd: the Claude Code mascot, rebuilt from its terminal block art
//
//    ▐▛███▜▌        each character cell is 2x2 quadrant pixels, which gives
//   ▝▜█████▛▘       an 18 x 5 pixel sprite. Extruded four voxels deep, with
//     ▘▘ ▝▝         two arms, eight crab legs and two recessed eyes.
import * as THREE from 'three';
import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js';

export const CLAWD_ORANGE = new THREE.Color().setRGB(215 / 255, 119 / 255, 87 / 255, THREE.SRGBColorSpace);

// sprite rows from the top: '#' body, 'e' eye socket, 'a' arm, 'l' leg
export const SPRITE = [
  '...############...',
  '...##e######e##...',
  '.aa############aa.',
  '...############...',
  '....l.l....l.l....',
];
export const SPRITE_W = 18, SPRITE_H = 5;

function smooth(x) { return x * x * (3 - 2 * x); }
function clamp01(x) { return Math.max(0, Math.min(1, x)); }

export class Clawd {
  constructor({ voxel = 0.25, depth = 4, material } = {}) {
    this.s = voxel; this.depth = depth;
    this.group = new THREE.Group();
    this.group.name = 'Clawd';
    this.voxels = [];
    const D = depth;
    for (let row = 0; row < SPRITE_H; row++) {
      for (let x = 0; x < SPRITE_W; x++) {
        const c = SPRITE[row][x];
        if (c === '.') continue;
        for (let z = 0; z < D; z++) {
          if (c === 'e' && z === 0) continue;             // eye socket: hole in the front layer
          if (c === 'a' && (z === 0 || z === D - 1)) continue; // arms two voxels deep
          if (c === 'l' && !(z === 0 || z === D - 1)) continue; // legs at front and back
          const part = c === 'a' ? (x < 9 ? 'armL' : 'armR') : c === 'l' ? 'leg' : 'body';
          const legIndex = c === 'l' ? [4, 6, 11, 13].indexOf(x) + (z === 0 ? 0 : 4) : -1;
          const interior = part === 'body' && x > 3 && x < 14 && row > 0 && row < 3 && z > 0 && z < D - 1;
          this.voxels.push({
            x, row, z, part, legIndex, interior,
            // local rest position in voxel units: x centred, y up from the floor, z centred (front = +z)
            base: new THREE.Vector3(x - (SPRITE_W - 1) / 2, (SPRITE_H - 1 - row) + 0.5, (D - 1) / 2 - z),
          });
        }
      }
    }
    this.count = this.voxels.length;
    const geo = new RoundedBoxGeometry(1, 1, 1, 3, 0.03);
    this.material = material || new THREE.MeshPhysicalMaterial({
      color: CLAWD_ORANGE, roughness: 0.4, metalness: 0.0,
      clearcoat: 0.75, clearcoatRoughness: 0.16,
      sheen: 0.35, sheenRoughness: 0.4, sheenColor: new THREE.Color(1.0, 0.7, 0.55),
    });
    this.glowAttr = new THREE.InstancedBufferAttribute(new Float32Array(this.count), 1);
    geo.setAttribute('aGlow', this.glowAttr);
    this.material.onBeforeCompile = (sh) => {
      sh.uniforms.uGlowColor = { value: new THREE.Color(1.0, 0.30, 0.07) };
      this.glowUniforms = sh.uniforms;
      sh.vertexShader = sh.vertexShader.replace('#include <common>', '#include <common>\nattribute float aGlow;\nvarying float vGlow;')
        .replace('#include <begin_vertex>', '#include <begin_vertex>\nvGlow = aGlow;');
      sh.fragmentShader = sh.fragmentShader.replace('#include <common>', '#include <common>\nvarying float vGlow;\nuniform vec3 uGlowColor;')
        .replace('#include <emissivemap_fragment>', '#include <emissivemap_fragment>\ntotalEmissiveRadiance += uGlowColor * vGlow;');
    };
    this.mesh = new THREE.InstancedMesh(geo, this.material, this.count);
    this.mesh.castShadow = true; this.mesh.receiveShadow = true;
    this.mesh.frustumCulled = false;
    const col = new THREE.Color();
    let seed = 7;
    const rnd = () => ((seed = (seed * 16807) % 2147483647) / 2147483647);
    for (let i = 0; i < this.count; i++) {
      const k = 1 + (rnd() - 0.5) * 0.05;
      col.setRGB(k, k * (1 + (rnd() - 0.5) * 0.03), k);
      this.mesh.setColorAt(i, col);
    }
    this.group.add(this.mesh);

    // eyes: glossy black blocks set back in the sockets, plus orange lids for blinking
    this.eyeMat = new THREE.MeshPhysicalMaterial({ color: 0x050403, roughness: 0.12, clearcoat: 1, clearcoatRoughness: 0.05 });
    this.eyes = [5, 12].map((x) => {
      const m = new THREE.Mesh(new RoundedBoxGeometry(1, 1, 1, 3, 0.1), this.eyeMat);
      m.userData.base = new THREE.Vector3(x - (SPRITE_W - 1) / 2, SPRITE_H - 1 - 1 + 0.5, (D - 1) / 2);
      m.castShadow = true; m.receiveShadow = true;
      this.group.add(m);
      return m;
    });
    this.lids = [5, 12].map((x, i) => {
      const m = new THREE.Mesh(geo.clone(), this.material);
      m.geometry.deleteAttribute('aGlow');
      m.geometry.setAttribute('aGlow', new THREE.BufferAttribute(new Float32Array(m.geometry.attributes.position.count), 1));
      m.userData.base = this.eyes[i].userData.base.clone();
      m.castShadow = true;
      this.group.add(m);
      return m;
    });
    this.dummy = new THREE.Object3D();
    this.pose = Clawd.defaultPose();
  }

  static defaultPose() {
    return {
      squash: 0,          // >0 flattens, <0 stretches
      lean: 0,            // forward lean (radians)
      tilt: 0,            // sideways tilt
      armL: 0, armR: 0,   // raise angles (radians)
      armSwingL: 0, armSwingR: 0,
      legLift: new Array(8).fill(0),
      blink: 0, squint: 0,
      glow: 0,
      eyeGlow: 0,
      voxelFn: null,       // (i, v, out:{pos,quat,scale,glow}) per-voxel override in voxel units
      wobble: null,        // (i, v) => vec3 offset in voxel units
      hideInterior: false,
    };
  }

  // Bounding info in world units
  get width() { return SPRITE_W * this.s; }
  get height() { return SPRITE_H * this.s; }

  update() {
    const P = this.pose, s = this.s, D = this.depth;
    const sq = P.squash;
    const sx = 1 + sq * 0.5, sy = 1 - sq, sz = 1 + sq * 0.5;
    const d = this.dummy;
    const tmp = new THREE.Vector3();
    const q = new THREE.Quaternion();
    const out = { pos: new THREE.Vector3(), quat: new THREE.Quaternion(), scale: 1, glow: 0, visible: true };
    const leanQ = new THREE.Quaternion().setFromEuler(new THREE.Euler(P.lean, 0, P.tilt));
    const voxScale = new THREE.Vector3(1 + sq * 0.15, 1 - sq * 0.3, 1 + sq * 0.15).multiplyScalar(1.0 * s);
    for (let i = 0; i < this.count; i++) {
      const v = this.voxels[i];
      tmp.copy(v.base);
      q.identity();
      if (v.part === 'armL' || v.part === 'armR') {
        const left = v.part === 'armL';
        const pivot = new THREE.Vector3(left ? -5.5 : 5.5, 2.5, 0);
        const ang = (left ? 1 : -1) * (left ? P.armL : P.armR);
        const swing = left ? P.armSwingL : P.armSwingR;
        tmp.sub(pivot);
        const rq = new THREE.Quaternion().setFromEuler(new THREE.Euler(0, swing, -ang));
        tmp.applyQuaternion(rq).add(pivot);
        q.copy(rq);
      } else if (v.part === 'leg') {
        tmp.y += P.legLift[v.legIndex] * 0.55;
      }
      // squash and stretch about the floor
      tmp.set(tmp.x * sx, tmp.y * sy, tmp.z * sz);
      // lean about the floor centre
      tmp.applyQuaternion(leanQ); q.premultiply(leanQ);
      if (P.wobble) tmp.add(P.wobble(i, v));
      out.pos.copy(tmp); out.quat.copy(q); out.scale = 1; out.glow = P.glow; out.visible = !(P.hideInterior && v.interior);
      if (P.voxelFn) P.voxelFn(i, v, out);
      d.position.copy(out.pos).multiplyScalar(s);
      d.quaternion.copy(out.quat);
      d.scale.copy(voxScale).multiplyScalar(out.visible ? out.scale : 0);
      d.updateMatrix();
      this.mesh.setMatrixAt(i, d.matrix);
      this.glowAttr.array[i] = out.glow;
    }
    this.mesh.instanceMatrix.needsUpdate = true;
    this.glowAttr.needsUpdate = true;
    // eyes and lids
    for (let k = 0; k < 2; k++) {
      const e = this.eyes[k], lid = this.lids[k];
      const b = e.userData.base;
      tmp.set(b.x * sx, b.y * sy, b.z * sz);
      tmp.applyQuaternion(leanQ);
      const eyeOut = { pos: tmp.clone(), quat: leanQ.clone(), scale: 1, glow: 0, visible: true };
      if (P.voxelFn) P.voxelFn(-1 - k, { part: 'eye', base: b, x: k ? 12 : 5, row: 1, z: 0 }, eyeOut);
      const back = 0.42; // recess depth
      const ez = new THREE.Vector3(0, 0, -back).applyQuaternion(eyeOut.quat);
      e.position.copy(eyeOut.pos).add(ez).multiplyScalar(s);
      e.quaternion.copy(eyeOut.quat);
      const open = 1 - clamp01(Math.max(P.blink, P.squint * 0.55));
      e.scale.set(0.93 * s * eyeOut.scale, 0.93 * s * eyeOut.scale, 0.9 * s * eyeOut.scale);
      e.visible = eyeOut.visible && eyeOut.scale > 0.001;
      // lid drops from the top of the socket
      const lidH = 1 - open;
      lid.visible = lidH > 0.01 && e.visible;
      const lidOff = new THREE.Vector3(0, (1 - lidH) * 0.5, -0.06).applyQuaternion(eyeOut.quat);
      lid.position.copy(eyeOut.pos).add(lidOff).multiplyScalar(s);
      lid.quaternion.copy(eyeOut.quat);
      lid.scale.set(0.965 * s * eyeOut.scale, Math.max(0.001, lidH) * 0.965 * s * eyeOut.scale, 0.965 * s * eyeOut.scale);
      lid.geometry.attributes.aGlow.array.fill(P.glow);
      lid.geometry.attributes.aGlow.needsUpdate = true;
      this.eyeMat.emissive?.setRGB(P.eyeGlow, P.eyeGlow * 0.5, P.eyeGlow * 0.3);
    }
  }
}

// --- motion helpers -------------------------------------------------------------
// damped spring response to an impulse at t0: returns 0 before t0
export function springImpulse(t, t0, amp = 1, freq = 3, damp = 6) {
  if (t < t0) return 0;
  const x = t - t0;
  return amp * Math.exp(-damp * x) * Math.sin(2 * Math.PI * freq * x);
}
// ballistic hop between two points with apex height h, from t0 to t1; returns {pos, k}
export function hop(t, t0, t1, a, b, h) {
  const k = clamp01((t - t0) / (t1 - t0));
  const pos = new THREE.Vector3().lerpVectors(a, b, k);
  pos.y += 4 * h * k * (1 - k);
  return { pos, k };
}
export { smooth, clamp01 };
