// Jolly, the plush mascot of Meta's Muse: a cream, fuzzy, round body with small black
// bead eyes, rosy cheeks and an embroidered smile. Built from published descriptions.
import * as THREE from 'three';
import { createFur, makeFurUniforms } from './fur.js';

// Meta blue fur (lighter tips, deeper roots)
const CREAM_TIP = new THREE.Color().setRGB(0.07, 0.30, 1.0);
const CREAM_ROOT = new THREE.Color().setRGB(0.012, 0.085, 0.52);
const PINK_TIP = new THREE.Color().setRGB(1.0, 0.56, 0.58);
const PINK_ROOT = new THREE.Color().setRGB(0.92, 0.45, 0.48);

function eggGeometry(r) {
  const g = new THREE.SphereGeometry(1, 160, 120);
  const p = g.attributes.position, v = new THREE.Vector3();
  for (let i = 0; i < p.count; i++) {
    v.fromBufferAttribute(p, i);
    // a little pear: wider low, slightly narrower top, flattened base
    const y = v.y;
    const widen = 1 + 0.07 * Math.max(0, -y) - 0.04 * Math.max(0, y);
    v.x *= widen; v.z *= widen * 0.94;
    v.y = y * 1.04;
    if (v.y < -0.78) v.y = -0.78 - (Math.abs(v.y + 0.78)) * 0.25;
    v.multiplyScalar(r);
    p.setXYZ(i, v.x, v.y, v.z);
  }
  g.computeVertexNormals();
  return g;
}

export class Jolly {
  constructor({ radius = 1.3, strands = 100000, quality = 1 } = {}) {
    this.R = radius;
    const R = radius;
    this.group = new THREE.Group(); this.group.name = 'Jolly';
    this.body = new THREE.Group(); this.group.add(this.body);   // squash/stretch pivot at the floor
    this.inner = new THREE.Group(); this.body.add(this.inner);
    this.inner.position.y = R * 0.8;

    // face layout (unit sphere directions)
    const eyeY = 0.1, eyeX = 0.33;
    this.faceDirs = {
      eyeL: new THREE.Vector3(-eyeX, eyeY, 1).normalize(),
      eyeR: new THREE.Vector3(eyeX, eyeY, 1).normalize(),
      cheekL: new THREE.Vector3(-0.55, -0.12, 0.83).normalize(),
      cheekR: new THREE.Vector3(0.55, -0.12, 0.83).normalize(),
      mouth: new THREE.Vector3(0, -0.1, 1).normalize(),
    };
    const fd = this.faceDirs;
    const near = (n, d, rad) => Math.max(0, 1 - n.angleTo(d) / rad);

    const bodyGeo = eggGeometry(R);
    this.uniforms = makeFurUniforms();
    const colorFn = (p, n) => {
      const ck = Math.max(near(n, fd.cheekL, 0.32), near(n, fd.cheekR, 0.32));
      const k = Math.pow(ck, 0.8);
      const tip = CREAM_TIP.clone().lerp(PINK_TIP, k);
      const root = CREAM_ROOT.clone().lerp(PINK_ROOT, k);
      // slightly warmer and darker underneath
      const under = THREE.MathUtils.clamp(-n.y, 0, 1);
      tip.multiplyScalar(1 - under * 0.12); root.multiplyScalar(1 - under * 0.15);
      return [root, tip];
    };
    const lengthFn = (p, n) => {
      let l = 1;
      l *= 0.1 + 0.9 * Math.pow(1 - Math.max(near(n, fd.eyeL, 0.22), near(n, fd.eyeR, 0.22)), 2);
      l *= 0.15 + 0.85 * Math.pow(1 - near(n, fd.mouth, 0.2), 2);
      l *= 0.8 + 0.2 * (1 - Math.max(near(n, fd.cheekL, 0.3), near(n, fd.cheekR, 0.3)));
      if (n.y < -0.85) l *= 0.5;
      // the signature tuft on top of the head
      const top = near(n, new THREE.Vector3(0.05, 1, 0.12).normalize(), 0.16);
      l *= 1 + 1.2 * top * top;
      return l;
    };
    const combFn = (p, n) => {
      // fur flows down and slightly out from the face centre
      const v = new THREE.Vector3(0, -0.45, 0);
      const top = near(n, new THREE.Vector3(0.05, 1, 0.12).normalize(), 0.2);
      v.y += top * 0.9;
      v.add(new THREE.Vector3(n.x, 0, n.z).multiplyScalar(0.15));
      return v;
    };
    const N = Math.round(strands * quality);
    this.fur = createFur(bodyGeo, {
      count: N, length: 0.15 * R, width: 0.011 * R, segs: 4, seed: 3,
      colorFn, lengthFn, combFn, uniforms: this.uniforms, curl: 7, jitter: 0.14, clump: 0.55, clumpCount: 2600,
    });
    this.inner.add(this.fur);
    // a sparse halo of finer, longer fibres that catches rim light like minky fabric
    this.fuzz = createFur(bodyGeo, {
      count: Math.round(12000 * quality), length: 0.22 * R, width: 0.005 * R, segs: 4, seed: 5,
      colorFn: (p, n) => { const [r, t] = colorFn(p, n); return [r.clone().lerp(t, 0.5), t.clone().lerp(new THREE.Color(0.35, 0.6, 1.0), 0.35)]; },
      lengthFn: (p, n) => lengthFn(p, n) * (n.z > 0.7 && Math.abs(n.y) < 0.55 ? 0.2 : 1), combFn, uniforms: this.uniforms, curl: 5, jitter: 0.25,
    });
    this.inner.add(this.fuzz);

    // skin under the fur, same colours so gaps read as dense fur
    const skinCol = [], P = bodyGeo.attributes.position, Nn = bodyGeo.attributes.normal;
    const n = new THREE.Vector3(), p = new THREE.Vector3();
    for (let i = 0; i < P.count; i++) {
      n.fromBufferAttribute(Nn, i); p.fromBufferAttribute(P, i);
      const [root] = colorFn(p, n);
      skinCol.push(root.r * 0.85, root.g * 0.85, root.b * 0.85);
    }
    bodyGeo.setAttribute('color', new THREE.Float32BufferAttribute(skinCol, 3));
    this.skin = new THREE.Mesh(bodyGeo, new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 0.95 }));
    this.skin.castShadow = true; this.skin.receiveShadow = true;
    this.inner.add(this.skin);

    // bead eyes
    const eyeMat = new THREE.MeshPhysicalMaterial({ color: 0x030303, roughness: 0.06, clearcoat: 1, clearcoatRoughness: 0.02, specularIntensity: 1 });
    this.eyeMat = eyeMat;
    this.eyes = ['eyeL', 'eyeR'].map((k) => {
      const e = new THREE.Mesh(new THREE.SphereGeometry(0.12 * R, 48, 32), eyeMat);
      const d = fd[k].clone();
      e.position.copy(this.surfacePoint(d, bodyGeo)).addScaledVector(d, 0.07 * R);
      e.scale.set(1, 1.1, 0.75);
      e.lookAt(e.position.clone().add(d));
      e.castShadow = true;
      e.userData.rest = e.position.clone();
      this.inner.add(e);
      return e;
    });
    // closed eyes: little embroidered arcs that replace the beads while blinking or asleep
    const arcMat = new THREE.MeshStandardMaterial({ color: 0x050714, roughness: 0.8 });
    this.lids = this.eyes.map((e) => {
      const pts = [];
      for (let k = 0; k <= 10; k++) { const a = -1.2 + (k / 10) * 2.4; pts.push(new THREE.Vector3(Math.sin(a) * 0.11 * R, -Math.cos(a) * 0.05 * R + 0.02 * R, 0)); }
      const arc = new THREE.Mesh(new THREE.TubeGeometry(new THREE.CatmullRomCurve3(pts), 12, 0.016 * R, 6, false), arcMat);
      arc.position.copy(e.position);
      arc.quaternion.copy(e.quaternion);
      arc.visible = false;
      this.inner.add(arc);
      return arc;
    });
    // embroidered smile: dark thread along a small upturned arc, stitched in short dashes
    const smile = new THREE.Group();
    const md = fd.mouth.clone();
    const mc = this.surfacePoint(md, bodyGeo);
    const threadMat = new THREE.MeshStandardMaterial({ color: 0x0a0c1c, roughness: 0.8 });
    const stitches = 7;
    for (let i = 0; i < stitches; i++) {
      const a0 = -1.0 + (i / stitches) * 2.0, a1 = a0 + 2.0 / stitches * 0.8;
      const pts = [];
      for (let k = 0; k <= 6; k++) {
        const a = a0 + (a1 - a0) * (k / 6);
        pts.push(new THREE.Vector3(Math.sin(a) * 0.15 * R, -Math.cos(a) * 0.09 * R + 0.07 * R, 0));
      }
      const tube = new THREE.Mesh(new THREE.TubeGeometry(new THREE.CatmullRomCurve3(pts), 8, 0.017 * R, 6, false), threadMat);
      smile.add(tube);
    }
    smile.position.copy(mc).addScaledVector(md, 0.05 * R);
    smile.lookAt(smile.position.clone().add(md));
    this.smile = smile;
    this.inner.add(smile);

    // little arms and feet with their own fur
    const limbFur = (geo, seed, count, len) => createFur(geo, {
      count: Math.round(count * quality), length: len * R, width: 0.011 * R, segs: 3, seed, clump: 0.5, clumpCount: 300,
      colorFn: () => [CREAM_ROOT.clone(), CREAM_TIP.clone()],
      combFn: (p, n) => new THREE.Vector3(0, -0.3, 0), uniforms: this.uniforms, curl: 8,
    });
    this.arms = [-1, 1].map((sgn, i) => {
      const pivot = new THREE.Group();
      pivot.position.set(sgn * R * 0.86, -0.05 * R, 0.1 * R);
      const g = new THREE.SphereGeometry(0.26 * R, 48, 32);
      g.scale(0.85, 1.25, 0.85);
      g.translate(sgn * 0.12 * R, -0.22 * R, 0);
      const skin = new THREE.Mesh(g, new THREE.MeshStandardMaterial({ color: CREAM_ROOT.clone().multiplyScalar(0.85), roughness: 0.95 }));
      skin.castShadow = true; skin.receiveShadow = true;
      pivot.add(skin);
      pivot.add(limbFur(g, 11 + i, 6000, 0.15));
      pivot.rotation.z = sgn * 0.35;
      this.inner.add(pivot);
      return pivot;
    });
    this.feet = [-1, 1].map((sgn, i) => {
      const g = new THREE.SphereGeometry(0.3 * R, 40, 24);
      g.scale(1, 0.62, 1.2);
      const m = new THREE.Group();
      m.position.set(sgn * 0.42 * R, 0.13 * R, 0.4 * R);
      const skin = new THREE.Mesh(g, new THREE.MeshStandardMaterial({ color: CREAM_ROOT.clone().multiplyScalar(0.85), roughness: 0.95 }));
      skin.castShadow = true; skin.receiveShadow = true;
      m.add(skin);
      m.add(limbFur(g, 21 + i, 4000, 0.12));
      this.body.add(m);
      return m;
    });
    this.pose = Jolly.defaultPose();
  }

  surfacePoint(dir, geo) {
    // ray-march from centre outward against the egg shape (approximate by sampling closest vertex direction)
    const P = geo.attributes.position, v = new THREE.Vector3();
    let best = -2, bp = new THREE.Vector3();
    for (let i = 0; i < P.count; i += 3) {
      v.fromBufferAttribute(P, i);
      const d = v.clone().normalize().dot(dir);
      if (d > best) { best = d; bp.copy(v); }
    }
    return bp;
  }

  static defaultPose() {
    return {
      squash: 0, lean: 0, tilt: 0, turn: 0,
      armL: 0, armR: 0,        // raise (radians)
      blink: 0, happy: 0,
      force: new THREE.Vector3(0, -0.22, 0), wind: new THREE.Vector3(),
      time: 0, grow: 1, frizz: 0.06,
      cheekGlow: 0,
    };
  }

  update() {
    const P = this.pose, R = this.R;
    const sq = P.squash;
    this.body.scale.set(1 + sq * 0.45, 1 - sq, 1 + sq * 0.45);
    this.inner.rotation.set(P.lean, P.turn, P.tilt);
    this.arms[0].rotation.z = -0.35 - P.armL;
    this.arms[1].rotation.z = 0.35 + P.armR;
    const u = this.uniforms;
    u.uTime.value = P.time;
    // gravity and inertia expressed in the fur's object space
    const inv = new THREE.Quaternion().copy(this.inner.getWorldQuaternion(new THREE.Quaternion())).invert();
    u.uForce.value.copy(P.force).applyQuaternion(inv);
    u.uWind.value.copy(P.wind).applyQuaternion(inv);
    u.uGrow.value = P.grow;
    u.uFrizz.value = P.frizz;
    u.uCheek.value = P.cheekGlow;
    for (let k = 0; k < 2; k++) {
      const b = Math.max(P.blink, P.happy * 0.85);
      const e = this.eyes[k];
      e.scale.set(1, Math.max(0.05, 1.1 * (1 - b)), 0.75);
      e.visible = b < 0.92;
      this.lids[k].visible = b > 0.6;
      this.lids[k].scale.set(1, P.happy > P.blink ? -1 : 1, 1);
    }
  }
}
