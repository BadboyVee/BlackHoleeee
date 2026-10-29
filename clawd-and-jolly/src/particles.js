// Fluff seeds and glowing voxel embers that swirl around the tree, then drift in the sunrise
import * as THREE from 'three';
import { rng, clamp01, smoothstep, bezier3, easeInOutCubic } from './anim.js';

function fluffTexture() {
  const c = document.createElement('canvas'); c.width = c.height = 128;
  const g = c.getContext('2d');
  g.translate(64, 64);
  const grd = g.createRadialGradient(0, 0, 0, 0, 0, 14);
  grd.addColorStop(0, 'rgba(255,250,240,1)'); grd.addColorStop(1, 'rgba(255,250,240,0)');
  g.fillStyle = grd; g.beginPath(); g.arc(0, 0, 14, 0, Math.PI * 2); g.fill();
  const R = rng(5);
  for (let i = 0; i < 46; i++) {
    const a = (i / 46) * Math.PI * 2 + R() * 0.1, l = 34 + R() * 26;
    const lg = g.createLinearGradient(0, 0, Math.cos(a) * l, Math.sin(a) * l);
    lg.addColorStop(0, 'rgba(255,248,235,0.9)'); lg.addColorStop(1, 'rgba(255,248,235,0)');
    g.strokeStyle = lg; g.lineWidth = 1.6;
    g.beginPath(); g.moveTo(0, 0); g.lineTo(Math.cos(a) * l, Math.sin(a) * l); g.stroke();
  }
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace;
  return t;
}

export class Motes {
  constructor({ count = 260, embers = 140 } = {}) {
    this.group = new THREE.Group();
    const R = rng(77);
    this.fluff = [];
    for (let i = 0; i < count; i++) { const dir = new THREE.Vector3(R() - 0.5, R() * 1.1 - 0.35, R() - 0.5).normalize(); this.fluff.push({ ph: R() * 6.28, r0: 1.5 + R() * 6, born: 43.4 + R() * 5.0, sp: 0.7 + R() * 0.9, rise: 2.0 + R() * 3.5, size: 0.22 + R() * 0.3, wob: R() * 6.28, bx: R() - 0.5, bz: R() - 0.5, by: R(), dir, bs: 4 + R() * 7 }); }
    const pos = new Float32Array(count * 3), size = new Float32Array(count), alpha = new Float32Array(count);
    const g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.BufferAttribute(pos, 3));
    g.setAttribute('aSize', new THREE.BufferAttribute(size, 1));
    g.setAttribute('aAlpha', new THREE.BufferAttribute(alpha, 1));
    this.points = new THREE.Points(g, new THREE.ShaderMaterial({
      uniforms: { tex: { value: fluffTexture() }, uScale: { value: 600 }, uTint: { value: new THREE.Color(0.55, 0.75, 1.0) } },
      vertexShader: `attribute float aSize; attribute float aAlpha; varying float vA; uniform float uScale;
        void main(){ vec4 mv = modelViewMatrix * vec4(position, 1.0); gl_Position = projectionMatrix * mv; gl_PointSize = aSize * uScale / -mv.z; vA = aAlpha; }`,
      fragmentShader: `uniform sampler2D tex; uniform vec3 uTint; varying float vA;
        void main(){ vec4 c = texture2D(tex, gl_PointCoord); gl_FragColor = vec4(c.rgb * uTint * vA * c.a, 0.0); }`,
      transparent: true, depthWrite: false, blending: THREE.AdditiveBlending,
    }));
    this.points.frustumCulled = false;
    this.group.add(this.points);
    // embers
    this.emb = [];
    for (let i = 0; i < embers; i++) this.emb.push({ ph: R() * 6.28, r0: 1 + R() * 5, born: 41.5 + R() * 7.5, sp: 1.0 + R() * 1.2, rise: 1.2 + R() * 2.2, life: 2.5 + R() * 3.5, size: 0.06 + R() * 0.07, ax: new THREE.Vector3(R() - 0.5, R() - 0.5, R() - 0.5).normalize(), bx: R() - 0.5, bz: R() - 0.5 });
    const eg = new THREE.BoxGeometry(1, 1, 1);
    this.embMesh = new THREE.InstancedMesh(eg, new THREE.MeshBasicMaterial({ color: 0xffffff }), embers);
    for (let i = 0; i < embers; i++) this.embMesh.setColorAt(i, new THREE.Color(1.0, 0.32, 0.06).multiplyScalar(6));
    this.embMesh.frustumCulled = false;
    this.group.add(this.embMesh);
    this.puff = Array.from({ length: 36 }, () => ({ d: R(), o: new THREE.Vector3(R() - 0.5, R() - 0.5, R() - 0.5), size: 0.15 + R() * 0.15 }));
    this.d = new THREE.Object3D();
  }

  // centre: tree base (world), height: tree height, mouth/seed for the puff
  update(t, { centre, height = 12, mouth, seed, climax = 50.0, dawn = 0, puffT = 39.9 }) {
    const pos = this.points.geometry.attributes.position.array;
    const size = this.points.geometry.attributes.aSize.array;
    const alpha = this.points.geometry.attributes.aAlpha.array;
    const n = this.fluff.length;
    const burst = smoothstep(climax, climax + 0.6, t);
    for (let i = 0; i < n; i++) {
      const f = this.fluff[i];
      const age = t - f.born;
      let p = new THREE.Vector3(), a = 0;
      if (age > 0) {
        const ang = f.ph + age * f.sp * 1.4;
        const rr = f.r0 * (0.6 + 0.4 * Math.sin(age * 0.8 + f.wob));
        const y = height * 1.1 * (1 - Math.exp(-age * f.rise * 0.9 / (height * 1.1))) + Math.sin(age * 2 + f.wob) * 0.3;
        p.set(Math.cos(ang) * rr, y, Math.sin(ang) * rr).add(centre);
        // after the burst: drift down slowly through the light
        if (t > climax) {
          const td = t - climax;
          const out = f.bs * (1 - Math.exp(-td * 2.2));
          p.addScaledVector(f.dir, out);
          p.y -= td * td * 0.05 * (0.5 + f.by);
          p.x += Math.sin(td * 0.9 + f.wob) * 0.6;
          p.z += Math.cos(td * 0.7 + f.wob) * 0.6;
        }
        a = clamp01(age / 0.6) * (0.55 + 0.45 * Math.sin(age * 3 + f.ph)) * (0.9 + dawn * 0.5);
      }
      pos[i * 3] = p.x; pos[i * 3 + 1] = p.y; pos[i * 3 + 2] = p.z;
      size[i] = f.size; alpha[i] = a;
    }
    // the puff: the first fluff seeds blown from Jolly to the seed voxel (re-use the first slots)
    if (mouth && seed && t > puffT && t < puffT + 1.6) {
      for (let k = 0; k < this.puff.length; k++) {
        const pf = this.puff[k];
        const kk = clamp01((t - puffT - pf.d * 0.4) / 0.9);
        const e = easeInOutCubic(kk);
        const p = bezier3(mouth, mouth.clone().lerp(seed, 0.3).add(new THREE.Vector3(0, 1.0, 0)).add(pf.o.clone().multiplyScalar(1.5)), seed.clone().add(new THREE.Vector3(0, 0.8, 0)).add(pf.o.clone().multiplyScalar(0.6)), seed, e);
        const i = n - 1 - k;
        pos[i * 3] = p.x; pos[i * 3 + 1] = p.y; pos[i * 3 + 2] = p.z;
        size[i] = pf.size * (1 - 0.6 * e); alpha[i] = kk > 0 ? (1 - smoothstep(0.8, 1, kk)) * 0.9 : 0;
      }
    }
    this.points.geometry.attributes.position.needsUpdate = true;
    this.points.geometry.attributes.aSize.needsUpdate = true;
    this.points.geometry.attributes.aAlpha.needsUpdate = true;
    // embers
    const d = this.d;
    for (let i = 0; i < this.emb.length; i++) {
      const e = this.emb[i];
      const age = t - e.born;
      if (age < 0) { d.scale.setScalar(0); d.updateMatrix(); this.embMesh.setMatrixAt(i, d.matrix); continue; }
      const ang = -e.ph - age * e.sp * 1.7;
      const rr = e.r0 * (0.7 + 0.3 * Math.cos(age + e.ph)) + burst * (t - climax) * 4.0;
      d.position.set(Math.cos(ang) * rr, age * e.rise, Math.sin(ang) * rr).add(centre);
      if (t > climax) { const td = t - climax; d.position.y -= td * td * 0.12; d.position.x += e.bx * td * 1.5; d.position.z += e.bz * td * 1.5; }
      d.quaternion.setFromAxisAngle(e.ax, age * 4);
      const fade = clamp01(age / 0.3) * (1 - smoothstep(e.life * 0.7, e.life, age)) * (1 - smoothstep(climax + 2.5, climax + 5.5, t));
      d.scale.setScalar(e.size * fade);
      d.updateMatrix();
      this.embMesh.setMatrixAt(i, d.matrix);
    }
    this.embMesh.instanceMatrix.needsUpdate = true;
  }
}
