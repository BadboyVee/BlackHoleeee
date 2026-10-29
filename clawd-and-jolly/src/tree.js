// The tree Clawd and Jolly grow together: a voxel trunk and branches in Clawd's orange,
// crowned with plush blossoms made of Jolly's blue fur. Growth is a pure function of time.
import * as THREE from 'three';
import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js';
import { CLAWD_ORANGE } from './clawd.js';
import { createFur, makeFurUniforms } from './fur.js';
import { rng, clamp01, easeOutBack, smoothstep } from './anim.js';

export class VoxelTree {
  constructor(opts) {
    const { seed, unit = 0.25, start = 41.0, quality = 1 } = opts;
    this.unit = unit; this.start = start; this.seed = seed.clone();
    this.group = new THREE.Group();
    this.group.position.copy(seed);
    const R = rng(2024);
    const vox = new Map(); // key -> {p: grid Vector3, t: birth}
    const tips = [];
    const add = (g, t) => {
      const k = `${g.x},${g.y},${g.z}`;
      if (!vox.has(k) || vox.get(k).t > t) vox.set(k, { g: g.clone(), t });
    };
    const branch = (p, dir, len, thick, depth, t0, dt) => {
      const pos = p.clone();
      let d = dir.clone().normalize();
      let t = t0;
      for (let i = 0; i < len; i++) {
        // gentle meander, always a little upward
        const wob = depth === 0 ? 0.12 : 0.35;
        d.add(new THREE.Vector3((R() - 0.5) * wob, (R() - 0.3) * 0.15, (R() - 0.5) * wob)).normalize();
        if (d.y < 0.15) { d.y = 0.15; d.normalize(); }
        pos.add(d);
        const g = new THREE.Vector3(Math.round(pos.x), Math.round(pos.y), Math.round(pos.z));
        add(g, t);
        const th = typeof thick === 'function' ? thick(i) : thick;
        if (th >= 2) { add(g.clone().add(new THREE.Vector3(1, 0, 0)), t + dt * 0.3); add(g.clone().add(new THREE.Vector3(0, 0, 1)), t + dt * 0.3); add(g.clone().add(new THREE.Vector3(1, 0, 1)), t + dt * 0.5); }
        if (th >= 3) for (const o of [[-1, 0, 0], [0, 0, -1], [-1, 0, -1], [-1, 0, 1], [1, 0, -1]]) add(g.clone().add(new THREE.Vector3(...o)), t + dt * 0.6);
        t += dt;
      }
      if (depth >= 3) { tips.push({ g: pos.clone(), t, dir: d.clone(), depth }); return; }
      const n = depth === 0 ? 4 : depth === 1 ? 3 : 2 + (R() < 0.5 ? 1 : 0);
      const base = R() * Math.PI * 2;
      for (let k = 0; k < n; k++) {
        const a = base + (k / n) * Math.PI * 2 + (R() - 0.5) * 0.6;
        const tilt = depth === 0 ? 0.85 + R() * 0.25 : 0.6 + R() * 0.4;
        const nd = new THREE.Vector3(Math.cos(a) * Math.sin(tilt), Math.cos(tilt), Math.sin(a) * Math.sin(tilt));
        nd.lerp(d, 0.25).normalize();
        const nl = depth === 0 ? 10 + Math.floor(R() * 5) : depth === 1 ? 6 + Math.floor(R() * 3) : 3 + Math.floor(R() * 3);
        branch(pos, nd, nl, depth === 0 ? (i) => (i < 5 ? 2 : 1) : 1, depth + 1, t, dt * 1.08);
      }
      if (depth >= 1) tips.push({ g: pos.clone(), t, dir: d.clone(), depth, mid: true });
    };
    add(new THREE.Vector3(0, 0, 0), start - 0.01);
    branch(new THREE.Vector3(0, 0, 0), new THREE.Vector3(0, 1, 0), 21, (i) => (i < 8 ? 3 : 2), 0, start, 0.108);
    this.voxels = [...vox.values()].sort((a, b) => a.t - b.t);
    this.tips = tips;
    // voxels
    const geo = new RoundedBoxGeometry(1, 1, 1, 2, 0.06);
    this.glowAttr = new THREE.InstancedBufferAttribute(new Float32Array(this.voxels.length), 1);
    geo.setAttribute('aGlow', this.glowAttr);
    const mat = new THREE.MeshPhysicalMaterial({ color: CLAWD_ORANGE, roughness: 0.4, clearcoat: 0.75, clearcoatRoughness: 0.16, sheen: 0.35, sheenColor: new THREE.Color(1, 0.7, 0.55) });
    mat.onBeforeCompile = (sh) => {
      sh.vertexShader = sh.vertexShader.replace('#include <common>', '#include <common>\nattribute float aGlow;\nvarying float vGlow;').replace('#include <begin_vertex>', '#include <begin_vertex>\nvGlow = aGlow;');
      sh.fragmentShader = sh.fragmentShader.replace('#include <common>', '#include <common>\nvarying float vGlow;')
        .replace('#include <emissivemap_fragment>', '#include <emissivemap_fragment>\ntotalEmissiveRadiance += vec3(1.0, 0.30, 0.07) * vGlow;');
    };
    mat.customProgramCacheKey = () => 'treevox';
    this.mesh = new THREE.InstancedMesh(geo, mat, this.voxels.length);
    this.mesh.castShadow = this.mesh.receiveShadow = true;
    this.mesh.frustumCulled = false;
    this.group.add(this.mesh);
    // blossoms at the tips
    const tipsSorted = tips.filter((tp, i) => !tp.mid || i % 3 === 0);
    this.blossoms = tipsSorted.map((tp, i) => {
      const kind = i % 5;
      const pink = kind === 1 || kind === 3, peach = kind === 4;
      // Jolly's blue fur, with a few rosy (cheek) and pale-sky blossoms
      const tipC = pink ? new THREE.Color(1.0, 0.58, 0.64) : peach ? new THREE.Color(0.45, 0.7, 1.0) : new THREE.Color(0.08, 0.32, 1.0);
      const rootC = pink ? new THREE.Color(0.9, 0.36, 0.45) : peach ? new THREE.Color(0.15, 0.4, 0.9) : new THREE.Color(0.015, 0.1, 0.55);
      const r = (tp.mid ? 0.6 : 0.9) + R() * 0.4;
      const sph = new THREE.SphereGeometry(1, 40, 28);
      const u = makeFurUniforms();
      u.uForce.value.set(0, -0.15, 0);
      u.uFrizz.value = 0.08;
      const fur = createFur(sph, {
        count: Math.round((tp.mid ? 900 : 1400) * quality), length: 0.42, width: 0.022, segs: 3, seed: 100 + i, curl: 7, jitter: 0.2, clump: 0.5, clumpCount: 120,
        colorFn: () => [rootC.clone(), tipC.clone()], uniforms: u, shadowFraction: 0.3,
      });
      const skin = new THREE.Mesh(sph, new THREE.MeshStandardMaterial({ color: rootC.clone().multiplyScalar(0.8), roughness: 0.95, emissive: rootC.clone(), emissiveIntensity: 0 }));
      const g = new THREE.Group();
      g.add(skin, fur);
      g.position.copy(tp.g).multiplyScalar(unit).add(tp.dir.clone().multiplyScalar(unit * 0.6));
      g.userData = { t: tp.t + 0.25 + R() * 0.35, r, u, skin, phase: R() * 6.28, tipT: tp.t };
      skin.castShadow = true;
      this.group.add(g);
      return g;
    });
    // spread the blooms so the crown keeps opening right up to the climax
    {
      const order = [...this.blossoms].sort((a, b) => a.userData.tipT - b.userData.tipT);
      const n = order.length;
      order.forEach((b, k) => { b.userData.t = (opts.bloomStart ?? 45.4) + Math.pow(k / Math.max(1, n - 1), 0.85) * ((opts.bloomEnd ?? 49.9) - (opts.bloomStart ?? 45.4)) + (R() - 0.5) * 0.15; });
    }
    // crown light
    this.light = new THREE.PointLight(new THREE.Color(1.0, 0.6, 0.35), 0, 0, 2);
    this.light.position.set(0, 7, 0);
    this.group.add(this.light);
    this.dummy = new THREE.Object3D();
    this.height = Math.max(...this.voxels.map((v) => v.g.y)) * unit;
  }

  // bloomShift lets the edit squeeze blooms toward the climax
  update(t, { climax = 50.0, glowBoost = 0 } = {}) {
    const u = this.unit, d = this.dummy;
    const pulse = Math.exp(-Math.max(0, t - climax) * 2.5) * smoothstep(climax - 0.1, climax, t);
    let shown = 0;
    for (let i = 0; i < this.voxels.length; i++) {
      const v = this.voxels[i];
      const age = t - v.t;
      const k = clamp01(age / 0.22);
      const s = age < 0 ? 0 : easeOutBack(k, 2.2);
      d.position.copy(v.g).multiplyScalar(u);
      d.position.y += u * 0.5;
      d.rotation.set(0, 0, 0);
      d.scale.setScalar(Math.max(0, s) * u * 0.985);
      d.updateMatrix();
      this.mesh.setMatrixAt(i, d.matrix);
      this.glowAttr.array[i] = age < 0 ? 0 : 1.6 * Math.exp(-age * 2.0) + 0.25 + 1.2 * pulse + glowBoost;
      if (age >= 0) shown++;
    }
    this.mesh.instanceMatrix.needsUpdate = true;
    this.glowAttr.needsUpdate = true;
    let open = 0;
    for (const b of this.blossoms) {
      const { t: bt, r, u: fu, skin, phase } = b.userData;
      const age = t - bt;
      const k = clamp01(age / 0.6);
      const s = age < 0 ? 0 : easeOutBack(k, 2.6) * (1 + 0.12 * pulse);
      b.visible = s > 0.001;
      b.scale.setScalar(Math.max(0.001, s * r));
      fu.uGrow.value = 0.3 + 0.7 * k;
      fu.uTime.value = t + phase;
      fu.uWind.value.set(Math.sin(t * 0.7 + phase) * 0.15, 0, Math.cos(t * 0.5 + phase) * 0.1);
      fu.uGlow.value = 0.22 * k + 0.7 * pulse + glowBoost * 0.3;
      skin.material.emissiveIntensity = 0.2 * k + pulse;
      open += k;
    }
    this.openFrac = open / this.blossoms.length;
    this.grownFrac = shown / this.voxels.length;
    this.light.intensity = 25 * this.openFrac + 80 * pulse;
    this.light.position.set(0, this.height + 3.5, 1.5);
  }
}
