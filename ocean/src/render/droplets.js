// Water drops on the camera lens after surfacing.
//
// Drops are simulated on the CPU in screen space: they bead up where the
// water left them, the heavy ones break away and roll down (wobbling,
// merging, shedding tiny beads), the small ones stick and evaporate. They are
// splatted as little hemispherical lenses into a half-res offset buffer
// (rg = refraction offset, b = coverage) and the post pass refracts the frame
// through them. There is no full-screen warp: only the drops distort.

import * as THREE from 'three/webgpu';
import {
  Fn, attribute, uv, vec2, vec3, vec4, float, length, sqrt, max, smoothstep, dot, clamp, uniform, screenUV, mix, If,
} from 'three/tsl';

const MAX = 96;

export class LensDroplets {
  constructor(renderer) {
    this.renderer = renderer;
    this.drops = [];
    this.params = new Float32Array(MAX * 4);   // x, y (0..1, y up), radius (fraction of height), stretch
    this.extra = new Float32Array(MAX * 4);    // alpha, vx, vy, seed
    this.active = false;
    this.aspect = uniform(16 / 9);
    this.strength = uniform(1);
    this._build();
  }

  _build() {
    const g = new THREE.InstancedBufferGeometry();
    g.index = new THREE.BufferAttribute(new Uint16Array([0, 1, 2, 0, 2, 3]), 1);
    g.setAttribute('position', new THREE.BufferAttribute(new Float32Array([-1, -1, 0, 1, -1, 0, 1, 1, 0, -1, 1, 0]), 3));
    g.setAttribute('uv', new THREE.BufferAttribute(new Float32Array([0, 0, 1, 0, 1, 1, 0, 1]), 2));
    this.pAttr = new THREE.InstancedBufferAttribute(this.params, 4);
    this.eAttr = new THREE.InstancedBufferAttribute(this.extra, 4);
    this.pAttr.setUsage(THREE.DynamicDrawUsage);
    this.eAttr.setUsage(THREE.DynamicDrawUsage);
    g.setAttribute('dropP', this.pAttr);
    g.setAttribute('dropE', this.eAttr);
    g.instanceCount = 0;
    this.geometry = g;

    const mat = new THREE.NodeMaterial();
    mat.transparent = true;
    mat.depthTest = false;
    mat.depthWrite = false;
    mat.blending = THREE.NormalBlending;
    const P = attribute('dropP', 'vec4'), E = attribute('dropE', 'vec4');
    const corner = attribute('position', 'vec3').xy;
    // drops are round in pixels, stretched a little along their motion
    const r = P.z, stretch = P.w;
    const ndc = vec2(P.x.mul(2).sub(1), P.y.mul(2).sub(1));
    const off = vec2(corner.x.mul(r).div(this.aspect), corner.y.mul(r).mul(stretch)).mul(2);
    mat.vertexNode = vec4(ndc.add(off), 0, 1);
    mat.fragmentNode = Fn(() => {
      const p = uv().mul(2).sub(1);
      const d2 = dot(p, p);
      const inside = smoothstep(1.0, 0.8, sqrt(d2));
      const h = sqrt(max(float(1).sub(d2), 0));
      // a drop is a tiny fisheye: it shows a flipped, shrunken image of the
      // scene around it, bent hardest at the rim
      const bend = p.mul(float(1).sub(h).mul(2.0).add(2.2)).negate().mul(r).mul(this.strength);
      const hl = smoothstep(0.28, 0.0, length(p.sub(vec2(-0.32, 0.38)))).mul(0.6);
      const shade = mix(float(1.02), float(0.78), smoothstep(0.55, 1.0, sqrt(d2))).add(hl);
      const a = inside.mul(E.x);
      // NormalBlending: rgb = src * a + dst * (1 - a); alpha accumulates coverage
      return vec4(bend.x, bend.y, shade, a);
    })();
    this.mesh = new THREE.Mesh(g, mat);
    this.mesh.frustumCulled = false;
    this.scene = new THREE.Scene();
    this.scene.add(this.mesh);
    this.cam = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);
    this.target = new THREE.RenderTarget(4, 4, { type: THREE.HalfFloatType, depthBuffer: false });
    this.target.texture.name = 'lensDroplets';
  }

  resize(w, h) {
    const W = Math.max(4, Math.floor(w / 2)), H = Math.max(4, Math.floor(h / 2));
    if (this.target.width !== W || this.target.height !== H) this.target.setSize(W, H);
    this.aspect.value = w / h;
  }

  clear() { this.drops.length = 0; }

  /** water left on the lens as the camera leaves the water (amount 0..1) */
  splash(amount = 1) {
    const n = Math.round(24 + 60 * amount);
    for (let i = 0; i < n && this.drops.length < MAX; i++) {
      const big = Math.random() < 0.18;
      const r = big ? 0.012 + Math.random() * 0.02 : 0.003 + Math.pow(Math.random(), 2) * 0.01;
      this.drops.push({
        x: Math.random(), y: Math.random() * 1.1, r, vx: 0, vy: 0,
        life: 2.5 + Math.random() * 5 + r * 120, age: 0, alpha: 0, seed: Math.random() * 100, stuck: 0,
      });
    }
  }

  update(dt, underwater) {
    if (underwater) { this.drops.length = 0; }
    const ds = this.drops;
    for (let i = ds.length - 1; i >= 0; i--) {
      const d = ds[i];
      d.age += dt;
      d.alpha = Math.min(1, d.alpha + dt * 12) * Math.min(1, (d.life - d.age) / 0.8);
      // heavy drops overcome surface tension and roll; small ones stick
      const excess = d.r - 0.0105;
      if (excess > 0) {
        const vTarget = -(0.05 + excess * 28);
        d.vy += (vTarget - d.vy) * (1 - Math.exp(-dt * 3));
        d.vx += (Math.sin(d.age * 3.1 + d.seed) * 0.02 - d.vx) * (1 - Math.exp(-dt * 2));
        // stick-slip: occasionally pause on a dry patch
        if (Math.random() < dt * 0.7) d.stuck = 0.05 + Math.random() * 0.25;
        if (d.stuck > 0) { d.stuck -= dt; d.vy *= 0.2; }
        // shed a tiny bead behind now and then
        if (Math.random() < dt * 4 && ds.length < MAX) {
          ds.push({ x: d.x + (Math.random() - 0.5) * d.r * 0.3, y: d.y + d.r * 0.8, r: 0.002 + Math.random() * 0.003, vx: 0, vy: 0, life: 1.5 + Math.random() * 2.5, age: 0, alpha: 0, seed: Math.random() * 100, stuck: 0 });
          d.r *= 0.985;
        }
      } else {
        d.vy *= Math.exp(-dt * 8);
        d.vx *= Math.exp(-dt * 8);
      }
      d.x += d.vx * dt;
      d.y += d.vy * dt;
      d.r *= Math.exp(-dt * 0.04);
      if (d.age >= d.life || d.y < -0.1 || d.r < 0.0015) ds.splice(i, 1);
    }
    // merge overlapping drops (the bigger one swallows the smaller)
    for (let i = 0; i < ds.length; i++) {
      for (let j = i + 1; j < ds.length; j++) {
        const a = ds[i], b = ds[j];
        const dx = (a.x - b.x) * 1.7, dy = a.y - b.y;
        const rr = (a.r + b.r) * 0.7;
        if (dx * dx + dy * dy < rr * rr) {
          const big = a.r >= b.r ? a : b, small = big === a ? b : a;
          big.r = Math.cbrt(big.r ** 3 + small.r ** 3);
          big.life = Math.max(big.life, small.life);
          small.age = small.life;
        }
      }
    }
    for (let i = ds.length - 1; i >= 0; i--) if (ds[i].age >= ds[i].life) ds.splice(i, 1);
    const n = Math.min(ds.length, MAX);
    for (let i = 0; i < n; i++) {
      const d = ds[i];
      const sp = Math.min(Math.abs(d.vy) * 6, 0.6);
      this.params.set([d.x, d.y, d.r, 1 + sp], i * 4);
      this.extra.set([Math.max(0, d.alpha), d.vx, d.vy, d.seed], i * 4);
    }
    this.geometry.instanceCount = n;
    this.pAttr.needsUpdate = true;
    this.eAttr.needsUpdate = true;
    this.pAttr.clearUpdateRanges?.();
    this.eAttr.clearUpdateRanges?.();
    this.wasActive = this.active;
    this.active = n > 0;
  }

  render() {
    if (!this.active && !this.wasActive) return;
    const r = this.renderer;
    const prev = r.getRenderTarget();
    const prevClear = r.getClearColor(new THREE.Color());
    const prevAlpha = r.getClearAlpha();
    r.setRenderTarget(this.target);
    r.setClearColor(0x000000, 0);
    r.clear();
    if (this.active) r.render(this.scene, this.cam);
    r.setRenderTarget(prev);
    r.setClearColor(prevClear, prevAlpha);
  }

  /** post node: refract the frame through the drops */
  node() {
    return (color, ctx) => Fn(() => {
      const col = vec3(color.rgb).toVar();
      const drop = (ctx.dropletTexture ? ctx.dropletTexture.sample(screenUV) : vec4(0)).toVar();
      If(drop.a.greaterThan(0.003), () => {
        const cov = clamp(drop.a, 0, 1);
        const inv = float(1).div(max(drop.a, 1e-3));
        const offs = drop.rg.mul(inv);
        const shade = drop.b.mul(inv);
        const uv2 = screenUV.add(vec2(offs.x, offs.y.negate()));
        // the drops sit on the lens, far out of focus: a small blur
        const e = length(offs).mul(0.12).add(0.0008);
        const through = ctx.postTexture.sample(uv2).rgb.mul(0.4)
          .add(ctx.postTexture.sample(uv2.add(vec2(e, 0))).rgb.mul(0.15))
          .add(ctx.postTexture.sample(uv2.sub(vec2(e, 0))).rgb.mul(0.15))
          .add(ctx.postTexture.sample(uv2.add(vec2(0, e))).rgb.mul(0.15))
          .add(ctx.postTexture.sample(uv2.sub(vec2(0, e))).rgb.mul(0.15));
        col.assign(mix(col, through.mul(shade), cov.mul(0.95)));
      });
      return vec4(col, 1);
    })();
  }
}
