// Surf: whitewater that outlives the breaking crest, and spray thrown up
// where the plunging lip hits the water.
//
// Foam: a world-aligned field (1600 m at 0.78 m/texel) updated on the GPU.
// Each texel in the surf band evaluates the same breaker model the water
// surface uses; its foam decays slowly (a broken bore leaves a white, then
// lacy trail that fades over ~15 s) but is refreshed wherever the breaker
// profile says the water is churning. The water's vertex stage reads it.
//
// Spray: 8k emitter points scattered through the breaking zone. When a
// point sees the lip impact (breaking index in the plunge range, just
// shoreward of the crest) it throws droplets up and forward from the actual
// displaced surface, plus some mist. Nothing is emitted from the smooth
// crest or the face of the wave.

import * as THREE from 'three/webgpu';
import {
  Fn, instancedArray, instanceIndex, uniform, vec2, vec3, vec4, float, uint, int, If, textureStore, texture, uvec2,
  smoothstep, exp, max, min, clamp, mix, select, abs, length, normalize, fract, sin, cos, hash,
} from 'three/tsl';
import { WORLD } from '../world/island.js';
import { hash21 } from '../render/tslnoise.js';

const N = 2048;

export class Surf {
  constructor(renderer, { ocean, shore, terrain, island, spray, time, slices = 4 }) {
    this.slices = slices;
    this.renderer = renderer;
    this.shore = shore;
    this.terrain = terrain;
    this.time = time;
    this.dt = uniform(0);
    this.parity = uniform(0);
    this.state = instancedArray(N * N, 'float');
    this.texture = new THREE.StorageTexture(N, N);
    // rgba8unorm: filterable and a core storage format (r16float is not)
    this.texture.type = THREE.UnsignedByteType;
    this.texture.format = THREE.RGBAFormat;
    this.texture.magFilter = this.texture.minFilter = THREE.LinearFilter;
    this.texture.generateMipmaps = false;
    this.texture.wrapS = this.texture.wrapT = THREE.ClampToEdgeWrapping;
    this.texture.name = 'surf.foam';
    this.origin = vec2(WORLD.originX, WORLD.originZ);
    this._buildFoam(island);
    if (spray) this._buildSpray(ocean, island, spray);
  }

  _buildFoam(island) {
    const shore = this.shore;
    const T = WORLD.size / N;
    // only texels in the surf band are simulated: a precomputed index list,
    // refreshed in SLICES interleaved slices (each slice sees SLICES x dt)
    const idx = [];
    const R = WORLD.res, TS = WORLD.size / R;
    for (let y = 0; y < N; y++) {
      const zz = WORLD.originZ + (y + 0.5) * T;
      const jj = Math.min(R - 1, Math.max(0, Math.floor((zz - WORLD.originZ) / TS)));
      for (let x = 0; x < N; x++) {
        const xx = WORLD.originX + (x + 0.5) * T;
        const ii = Math.min(R - 1, Math.max(0, Math.floor((xx - WORLD.originX) / TS)));
        const sd = island.sdf[jj * R + ii];
        if (sd > -6 && sd < 260) idx.push(y * N + x);
      }
    }
    this.bandCount = idx.length;
    const band = instancedArray(new Uint32Array(idx), 'uint');
    this.slice = uniform(0, 'uint');
    const SL = this.slices;
    this.foamKernel = Fn(() => {
      const k = instanceIndex.mul(uint(SL)).add(this.slice);
      If(k.lessThan(uint(idx.length)), () => {
        const i = band.element(k);
        const x = i.mod(uint(N)), y = i.div(uint(N));
        const xz = this.origin.add(vec2(float(x), float(y)).add(0.5).mul(T));
        const old = this.state.element(i);
        const st = shore.state(xz, this.time, true);
        const br = shore.breaker(st, true);
        // churning water right now: the profile's whitewater, scaled by wave size
        const src = br.foam.mul(smoothstep(0.08, 0.45, st.H)).mul(1.15);
        // decay: slow in the inner surf zone (bores keep stirring it), faster outside
        const tau = mix(float(7), float(16), smoothstep(2.5, 0.6, st.depth));
        const kept = old.mul(exp(this.dt.mul(SL).negate().div(tau)));
        const out = clamp(max(kept, src), 0, 1.4);
        this.state.element(i).assign(out);
        textureStore(this.texture, uvec2(x, y), vec4(out.div(1.5), 0, 0, 1));
      });
    })().compute(Math.ceil(idx.length / SL), [64]);
  }

  _buildSpray(ocean, island, spray) {
    // emitter points: where the water is 0.25..3.5 m deep within 200 m of shore
    const pts = [];
    let guard = 0;
    while (pts.length < 8192 && guard++ < 400000) {
      const x = WORLD.originX + Math.random() * WORLD.size, z = WORLD.originZ + Math.random() * WORLD.size;
      const h = island.heightAt(x, z);
      if (h > -0.25 || h < -3.5) continue;
      const sdf = island.sdfAt(x, z);
      if (sdf < 0 || sdf > 200) continue;
      pts.push(x, z, Math.random(), 0);
    }
    const M = pts.length / 4;
    const P = instancedArray(new Float32Array(pts), 'vec4');
    const shore = this.shore;
    this.frameU = uniform(0);
    this.sprayRate = uniform(1);
    spray.addGpuEmitter(M, (write) => Fn(() => {
      const i = instanceIndex;
      const e = P.element(i);
      const xz = e.xy;
      const st = shore.state(xz, this.time, true);
      const H = st.H;
      // the plunge: lip meets the trough just shoreward of the crest
      const s = st.psi.mul(st.lambda).div(H.max(0.05));
      const impact = smoothstep(1.85, 2.25, st.beta).mul(smoothstep(3.0, 2.55, st.beta));
      const fa = s.add(0.6).div(0.55);   // (WGSL pow is undefined for negative bases)
      const front = exp(fa.mul(fa).negate());
      // turbulent bore further in: occasional droplets and mist
      const fb = s.add(0.2).div(0.8);
      const bore = smoothstep(2.4, 2.9, st.beta).mul(exp(fb.mul(fb).negate())).mul(0.18);
      const rate = impact.mul(front).add(bore).mul(smoothstep(0.15, 0.6, H)).mul(H.mul(90)).mul(this.sprayRate);
      const r = hash21(vec2(float(i), fract(this.frameU.mul(0.618)).mul(1000)));
      If(r.lessThan(rate.mul(this.dt)), () => {
        const srf = ocean.surface(xz, float(0.5), shore, this.time);
        const pos = vec3(xz.x.add(srf.disp.x), srf.y.add(0.05), xz.y.add(srf.disp.z));
        const r2 = hash21(vec2(float(i).add(7.7), r.mul(97)));
        const r3 = hash21(vec2(float(i).add(3.1), r.mul(53)));
        const a = r2.mul(6.283);
        const side = vec3(st.fwd.y.negate(), 0, st.fwd.x);
        const up = mix(float(2.0), float(5.5), r3).mul(H.sqrt());
        const along = mix(float(0.5), float(3.2), r2).mul(H.sqrt());
        const vel = vec3(st.fwd.x, 0, st.fwd.y).mul(along).add(vec3(0, up, 0)).add(side.mul(cos(a).mul(0.9)));
        const mist = r3.lessThan(0.22);
        const size = select(mist, float(-0.07), mix(float(0.012), float(0.05), r2.mul(r2)));
        write(pos, vel, mix(float(0.9), float(2.2), r3), size);
      });
    })(), (dt) => { this.frameU.value++; });
  }

  update(dt) {
    this.dt.value = Math.min(dt, 0.05);
    if (dt <= 0) return;
    this.slice.value = (this.slice.value + 1) % this.slices;
    this.renderer.compute(this.foamKernel);
  }

  /** TSL: persistent surf foam at world xz */
  sample(xz) {
    const uv = xz.sub(this.origin).div(WORLD.size);
    return texture(this.texture, uv).level(0).r.mul(1.5);
  }
}
