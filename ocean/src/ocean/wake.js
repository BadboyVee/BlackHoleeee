// Interactive wake waves: iWave (Tessendorf 2004) on the GPU.
//
// A 512² height field (0.5 m cells, 256 m square) follows the boat, shifted in
// whole cells so the waves stay put in the world. Each step convolves the
// height with the iWave kernel (the discrete sqrt(-∇²) operator), which gives
// deep-water dispersion - and with it a proper Kelvin wake: the 19.5° V of
// divergent waves plus transverse waves behind the stern - from nothing more
// than the hull pushing the surface around.
//
//   h' = h (2 - αΔt)/(1 + αΔt) - h_prev/(1 + αΔt) - g Δt² (G * h)/((1 + αΔt) Δx)
//
// The seabed feeds in: land cells are walls, the surf zone soaks the waves up
// (they break into foam), and they slow as the water shallows. A second
// channel carries aeration foam (propeller wash, breaking crests) that decays.
//
// Output texture (rgba16f, world-aligned): height, ∂h/∂x, ∂h/∂z, foam.

import * as THREE from 'three/webgpu';
import {
  Fn, uniform, vec2, vec3, vec4, float, int, uint, instancedArray, workgroupArray, workgroupBarrier,
  invocationLocalIndex, workgroupId, textureStore, texture, clamp, max, min, abs, exp, smoothstep, select,
  sqrt, length, mix, If, uvec2, tanh, cos, sin,
} from 'three/tsl';

export const WAKE_N = 512;
export const WAKE_CELL = 0.5;
const P = 6;                      // kernel half-width
const TILE = 16;
const AP = TILE + 2 * P;          // 28: tile + apron
const G = 9.81;

// iWave vertical-derivative kernel G(r) = sum q^2 exp(-q^2) J0(q r) / G0
function besselJ0(x) {
  // Numerical Recipes rational approximations
  const ax = Math.abs(x);
  if (ax < 8) {
    const y = x * x;
    const a1 = 57568490574.0 + y * (-13362590354.0 + y * (651619640.7 + y * (-11214424.18 + y * (77392.33017 + y * (-184.9052456)))));
    const a2 = 57568490411.0 + y * (1029532985.0 + y * (9494680.718 + y * (59272.64853 + y * (267.8532712 + y))));
    return a1 / a2;
  }
  const z = 8 / ax, y = z * z, xx = ax - 0.785398164;
  const a1 = 1 + y * (-0.1098628627e-2 + y * (0.2734510407e-4 + y * (-0.2073370639e-5 + y * 0.2093887211e-6)));
  const a2 = -0.1562499995e-1 + y * (0.1430488765e-3 + y * (-0.6911147651e-5 + y * (0.7621095161e-6 - y * 0.934935152e-7)));
  return Math.sqrt(0.636619772 / ax) * (Math.cos(xx) * a1 - z * Math.sin(xx) * a2);
}

function buildKernel() {
  const dq = 0.001, nq = 10000;
  let G0 = 0;
  for (let n = 1; n <= nq; n++) { const q = n * dq; G0 += q * q * Math.exp(-q * q); }
  const K = [];
  for (let j = -P; j <= P; j++) {
    for (let i = -P; i <= P; i++) {
      const r = Math.hypot(i, j);
      let g = 0;
      for (let n = 1; n <= nq; n++) { const q = n * dq; g += q * q * Math.exp(-q * q) * besselJ0(q * r); }
      K.push(g / G0);
    }
  }
  return K;
}

export class Wake {
  constructor(renderer, { terrain, size = WAKE_N }) {
    this.renderer = renderer;
    this.terrain = terrain;
    const N = this.N = size;
    this.stateA = instancedArray(N * N, 'vec4');   // h, h_prev, foam, -
    this.stateB = instancedArray(N * N, 'vec4');
    this.texture = new THREE.StorageTexture(N, N);
    this.texture.type = THREE.HalfFloatType;
    this.texture.format = THREE.RGBAFormat;
    this.texture.magFilter = THREE.LinearFilter;
    this.texture.minFilter = THREE.LinearFilter;
    this.texture.generateMipmaps = false;
    this.texture.wrapS = this.texture.wrapT = THREE.ClampToEdgeWrapping;
    this.texture.name = 'wake';

    // domain placement: origin = world position of cell (0, 0)'s corner
    this.origin = uniform(new THREE.Vector2(-N * WAKE_CELL / 2, -N * WAKE_CELL / 2));
    this.shift = uniform(new THREE.Vector2(0, 0));      // cells to shift the old state by this step
    this.dt = uniform(1 / 60);
    this.damping = uniform(0.06);
    this.strength = uniform(1);
    this.foamDecay = uniform(0.16);
    // up to two hulls: pos.xz, heading, draft (now and previous step)
    this.hulls = [0, 1].map(() => ({
      now: uniform(new THREE.Vector4(0, 0, 0, 0)), prev: uniform(new THREE.Vector4(0, 0, 0, 0)),
      size: uniform(new THREE.Vector4(7.4, 2.5, 0, 0)),          // length, beam, throttle, speed
    }));
    this.cpuOrigin = new THREE.Vector2(this.origin.value.x, this.origin.value.y);
    this.center = new THREE.Vector2(0, 0);
    this.active = false;
    this.flip = false;
    this._build();
  }

  _build() {
    const N = this.N;
    const K = buildKernel();
    const tilesPerRow = N / TILE;
    const make = (src, dst) => {
      const tile = workgroupArray('float', AP * AP);
      return Fn(() => {
        const wid = workgroupId.x;
        const lid = invocationLocalIndex;
        const tx = wid.mod(uint(tilesPerRow)), ty = wid.div(uint(tilesPerRow));
        const lx = lid.mod(uint(TILE)), ly = lid.div(uint(TILE));
        const sx = int(this.shift.x), sy = int(this.shift.y);
        // cooperative load of the tile + apron (old state, shifted)
        for (let k = 0; k < Math.ceil(AP * AP / (TILE * TILE)); k++) {
          const idx = lid.add(uint(k * TILE * TILE));
          If(idx.lessThan(uint(AP * AP)), () => {
            const ax = int(idx.mod(uint(AP))), ay = int(idx.div(uint(AP)));
            const gx = int(tx.mul(uint(TILE))).add(ax).sub(P).add(sx);
            const gy = int(ty.mul(uint(TILE))).add(ay).sub(P).add(sy);
            const inside = gx.greaterThanEqual(0).and(gx.lessThan(N)).and(gy.greaterThanEqual(0)).and(gy.lessThan(N));
            const v = select(inside, src.element(uint(gy.mul(N).add(gx))).x, float(0));
            tile.element(idx).assign(v);
          });
        }
        workgroupBarrier();
        const cx = int(tx.mul(uint(TILE)).add(lx)), cy = int(ty.mul(uint(TILE)).add(ly));
        // convolution with the constant kernel (unrolled, symmetric weights)
        // (one statement per tap: a single 169-term expression is too deep for WGSL parsers)
        const vdV = float(0).toVar();
        const base = int(ly).mul(AP).add(int(lx)).toVar();
        for (let j = -P; j <= P; j++) {
          for (let i = -P; i <= P; i++) {
            const w = K[(j + P) * (2 * P + 1) + (i + P)];
            if (Math.abs(w) < 1e-5) continue;
            vdV.addAssign(tile.element(uint(base.add((P + j) * AP + (P + i)))).mul(w));
          }
        }
        // old state at this cell
        const ox = cx.add(sx), oy = cy.add(sy);
        const oin = ox.greaterThanEqual(0).and(ox.lessThan(N)).and(oy.greaterThanEqual(0)).and(oy.lessThan(N));
        const old = select(oin, src.element(uint(oy.mul(N).add(ox))), vec4(0)).toVar();
        const h = old.x, hPrev = old.y, foam = old.z;
        const world = this.origin.add(vec2(float(cx).add(0.5), float(cy).add(0.5)).mul(WAKE_CELL)).toVar();
        // seabed: walls on land, surf-zone absorption, slower in the shallows
        const bed = this.terrain.sampleLevel(world).x;
        const depth = bed.negate().toVar();
        const wet = smoothstep(0.02, 0.25, depth);
        const shallowDamp = smoothstep(2.2, 0.35, depth).mul(2.5);
        // sponge at the domain edges so nothing reflects off them
        const e = min(min(float(cx), float(N - 1).sub(float(cx))), min(float(cy), float(N - 1).sub(float(cy))));
        const sponge = smoothstep(28, 0, e).mul(6);
        const alpha = this.damping.add(shallowDamp).add(sponge);
        const dt = this.dt;
        const gEff = float(G).mul(tanh(depth.max(0).mul(0.8)).mul(0.9).add(0.1));
        const denom = float(1).add(alpha.mul(dt));
        let hNew = h.mul(float(2).sub(alpha.mul(dt))).div(denom)
          .sub(hPrev.div(denom))
          .sub(gEff.mul(dt).mul(dt).mul(vdV).div(denom.mul(WAKE_CELL)));
        // hull sources: the moving hull displaces the surface (difference of
        // its footprint now and a step ago, so a hull at rest makes no waves)
        let src2 = float(0);
        let foamSrc = float(0);
        for (const hull of this.hulls) {
          const fp = (pose) => {
            const d = world.sub(pose.xy);
            const c = cos(pose.z), s = sin(pose.z);
            // boat frame: +u forward (heading 0 = -z), +v starboard
            const u = d.x.mul(s).sub(d.y.mul(c));
            const v = d.x.mul(c).add(d.y.mul(s));
            const L = hull.size.x.mul(0.5), B = hull.size.y.mul(0.5);
            // fuller at the stern, finer at the bow
            const bowTaper = smoothstep(-0.2, 1.0, u.div(L));
            const vn = v.div(B.mul(mix(float(1), float(0.35), bowTaper)));
            const un = u.div(L);
            const r2 = un.mul(un).add(vn.mul(vn));
            return max(float(1).sub(r2), 0).pow(0.6).mul(pose.w);
          };
          src2 = src2.add(fp(hull.now).sub(fp(hull.prev)));
          // propeller wash + stern turbulence behind the transom, bow flank spray
          const d = world.sub(hull.now.xy);
          const c = cos(hull.now.z), s = sin(hull.now.z);
          const u = d.x.mul(s).sub(d.y.mul(c));
          const v = d.x.mul(c).add(d.y.mul(s));
          const L = hull.size.x.mul(0.5);
          // (explicit squares: WGSL pow is undefined for negative bases)
          const su = u.add(L).add(1.2).div(1.6), sv = v.div(0.9);
          const stern = exp(su.mul(su).add(sv.mul(sv)).negate());
          const fu = u.sub(L.mul(0.35)).div(1.8);
          const flank = exp(fu.mul(fu).negate()).mul(smoothstep(1.6, 1.0, abs(v))).mul(smoothstep(0.7, 1.2, abs(v)));
          foamSrc = foamSrc.add(stern.mul(hull.size.z.abs().mul(0.8).add(hull.size.w.mul(0.12))).add(flank.mul(max(hull.size.w.sub(2.5), 0).mul(0.25))));
        }
        hNew = hNew.sub(src2.mul(this.strength));
        hNew = hNew.mul(wet).clamp(-1.5, 1.5).toVar();
        // slope for the renderer (central differences on the tile)
        const at = (i, j) => tile.element(uint(int(ly).add(P + j).mul(AP).add(int(lx).add(P + i))));
        const gx = at(1, 0).sub(at(-1, 0)).div(2 * WAKE_CELL);
        const gz = at(0, 1).sub(at(0, -1)).div(2 * WAKE_CELL);
        // breaking: steep wake crests and waves dying in the surf zone make foam
        const steep = max(length(vec2(gx, gz)).sub(0.22), 0).mul(3);
        const surf = abs(h).mul(shallowDamp).mul(2.2);
        const fNew = clamp(foam.mul(exp(this.foamDecay.negate().mul(dt))).add(foamSrc.add(steep).add(surf).mul(dt)), 0, 2).mul(wet);
        dst.element(uint(cy.mul(N).add(cx))).assign(vec4(hNew, h, fNew, 0));
        textureStore(this.texture, uvec2(uint(cx), uint(cy)), vec4(hNew, gx, gz, fNew));
      })().compute(N * N, [TILE * TILE]);
    };
    this.kernelAB = make(this.stateA, this.stateB);
    this.kernelBA = make(this.stateB, this.stateA);
  }

  /** set hull k's pose (world x, z, heading rad, immersion m) and motion */
  setHull(k, x, z, heading, draft, length, beam, throttle, speed) {
    const h = this.hulls[k];
    if (!h.init) { h.now.value.set(x, z, heading, draft); h.init = true; }
    h.prev.value.copy(h.now.value);
    h.now.value.set(x, z, heading, draft);
    h.size.value.set(length, beam, throttle, speed);
    this.active = true;
  }

  update(dt, focus) {
    if (!this.active) return;
    // keep the domain centred on the action, shifting in whole cells
    const N = this.N, C = WAKE_CELL;
    const cx = Math.round(focus.x / C), cz = Math.round(focus.z / C);
    const ocx = Math.round((this.cpuOrigin.x + N * C / 2) / C), ocz = Math.round((this.cpuOrigin.y + N * C / 2) / C);
    let sx = 0, sz = 0;
    if (Math.abs(cx - ocx) > 48 || Math.abs(cz - ocz) > 48) { sx = cx - ocx; sz = cz - ocz; }
    this.cpuOrigin.set((ocx + sx) * C - N * C / 2, (ocz + sz) * C - N * C / 2);
    this.origin.value.copy(this.cpuOrigin);
    // fixed 1/60 steps (the scheme is tuned for it), at most 3 per frame
    this.acc = Math.min((this.acc || 0) + dt, 3 / 60);
    let first = true;
    while (this.acc >= 1 / 60 - 1e-6) {
      this.acc -= 1 / 60;
      this.shift.value.set(first ? sx : 0, first ? sz : 0);
      first = false;
      this.renderer.compute(this.flip ? this.kernelBA : this.kernelAB);
      this.flip = !this.flip;
    }
  }

  /** TSL: (height, dh/dx, dh/dz, foam) at world xz; zero outside the domain */
  sample(xz) {
    const uv = xz.sub(this.origin).div(this.N * WAKE_CELL);
    const inside = uv.x.greaterThan(0.002).and(uv.x.lessThan(0.998)).and(uv.y.greaterThan(0.002)).and(uv.y.lessThan(0.998));
    return select(inside, texture(this.texture, uv).level(0), vec4(0));
  }
}
