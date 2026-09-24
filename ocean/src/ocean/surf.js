// Surf: whitewater that outlives the breaking crest, and spray thrown up
// where the plunging lip hits the water.
//
// Foam: a world-aligned field (1600 m at 0.78 m/texel) updated on the GPU.
// Each texel in the surf band evaluates the same breaker model the water
// surface uses; its foam is refreshed wherever the breaker profile says the
// water is churning, then drifts and decays: every passing bore shoves it
// shoreward, slow eddies (the curl of a noise stream function) stretch it
// into streaks, and it fades over ~15 s. A second channel tracks how fresh
// it is, so new whitewater is dense and older foam opens into lace. The
// water's vertex stage reads both.
//
// Spray: 8k emitter points scattered through the breaking zone. When a
// point sees the lip impact (breaking index in the plunge range, just
// shoreward of the crest) it throws droplets up and forward from the actual
// displaced surface, plus some mist. Nothing is emitted from the face of the
// wave - except spindrift: an offshore wind tears a veil of mist off the
// crests of steepening and pitching waves and blows it back out to sea.

import * as THREE from 'three/webgpu';
import {
  Fn, instancedArray, instanceIndex, uniform, vec2, vec3, vec4, float, uint, int, If, textureStore, texture, uvec2,
  smoothstep, exp, max, min, clamp, mix, select, abs, length, normalize, fract, sin, cos, hash, floor, dot,
} from 'three/tsl';
import { WORLD } from '../world/island.js';
import { hash21, gnoise2 } from '../render/tslnoise.js';
import { env } from '../env.js';

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
    this.state = instancedArray(N * N, 'vec2');   // (foam, freshness)
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
    this.band = instancedArray(new Uint32Array(idx), 'uint');
    this.slice = uniform(0, 'uint');
    this.foamKernel = this._makeKernel(this.slices, this.slice);
  }

  // one foam update of every SL-th band texel starting at `slice`
  _makeKernel(SL, slice) {
    const shore = this.shore, band = this.band, count = this.bandCount;
    const T = WORLD.size / N;
    return Fn(() => {
      const k = instanceIndex.mul(uint(SL)).add(slice);
      If(k.lessThan(uint(count)), () => {
        const i = band.element(k);
        const x = i.mod(uint(N)), y = i.div(uint(N));
        const xz = this.origin.add(vec2(float(x), float(y)).add(0.5).mul(T));
        const st = shore.state(xz, this.time, true);
        const br = shore.breaker(st, true);
        const dtS = this.dt.mul(SL);
        // churning water right now: the profile's whitewater, scaled by wave size
        const src = br.foam.mul(smoothstep(0.08, 0.45, st.H)).mul(1.15);
        // drift: a passing bore shoves the foam shoreward; slow eddies (curl
        // of a stream function, ~0.3 m/s) stretch it into streaks
        const boreNow = br.foam.mul(smoothstep(2.0, 2.5, st.beta));
        const E = 1.5, F = 0.03;
        const q = xz.mul(F).add(vec2(this.time.mul(0.011), this.time.mul(-0.007)));
        const p0 = gnoise2(q), px = gnoise2(q.add(vec2(E * F, 0))), pz = gnoise2(q.add(vec2(0, E * F)));
        const swirl = vec2(pz.sub(p0), p0.sub(px)).mul(4.0 / E);
        const vel = st.fwd.mul(boreNow.mul(2.0).add(0.12)).add(swirl);
        // semi-Lagrangian: bilinear fetch from where this water came from
        const g = xz.sub(vel.mul(dtS)).sub(this.origin).div(T).sub(0.5);
        const g0 = floor(g), f = g.sub(g0);
        const gx = clamp(g0.x, 0, N - 2), gy = clamp(g0.y, 0, N - 2);
        const b = uint(gy).mul(uint(N)).add(uint(gx));
        const s00 = this.state.element(b), s10 = this.state.element(b.add(uint(1)));
        const s01 = this.state.element(b.add(uint(N))), s11 = this.state.element(b.add(uint(N + 1)));
        const old = mix(mix(s00, s10, f.x), mix(s01, s11, f.x), f.y);
        // decay: slow in the inner surf zone (bores keep stirring it), faster outside
        const tau = mix(float(7), float(16), smoothstep(2.5, 0.6, st.depth));
        const foam = clamp(max(old.x.mul(exp(dtS.negate().div(tau))), src), 0, 1.4);
        // freshness: ~1.5 s after the churning stops the foam blanket opens up
        const fresh = clamp(max(old.y.mul(exp(dtS.negate().div(1.5))), src), 0, 1);
        this.state.element(i).assign(vec2(foam, fresh));
        textureStore(this.texture, uvec2(x, y), vec4(foam.div(1.5), fresh, 0, 1));
      });
    })().compute(Math.ceil(count / SL), [64]);
  }

  /**
   * Integrate the foam field over the last `seconds` up to time `now` in
   * whole-band steps (after a jump in time or a teleport, and for captures).
   */
  prewarm(seconds, step, now) {
    if (!this.fullKernel) this.fullKernel = this._makeKernel(1, uint(0));
    const t0 = this.time.value, dt0 = this.dt.value;
    for (let t = now - seconds; t <= now + 1e-6; t += step) {
      this.time.value = t;
      this.dt.value = step;
      this.renderer.compute(this.fullKernel);
    }
    this.time.value = t0;
    this.dt.value = dt0;
  }

  _buildSpray(ocean, island, spray) {
    // emitter points: where the water is 0.25..3.5 m deep within 200 m of shore
    const pts = [];
    let guard = 0;
    while (pts.length < 4 * 8192 && guard++ < 600000) {
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
      const splash = impact.mul(front).add(bore).mul(smoothstep(0.15, 0.6, H)).mul(H.mul(90));
      // spindrift off the crest, where the wind blows against the wave
      const offshore = max(dot(env.windDir, st.fwd.negate()), 0).mul(smoothstep(3.0, 9.0, env.windSpeed));
      const fc = s.div(0.45);
      const drift = smoothstep(0.8, 1.3, st.beta).mul(smoothstep(2.4, 1.9, st.beta)).mul(exp(fc.mul(fc).negate()))
        .mul(offshore).mul(smoothstep(0.3, 0.8, H)).mul(H.mul(70));
      const rate = splash.add(drift).mul(this.sprayRate).toVar();
      const r = hash21(vec2(float(i), fract(this.frameU.mul(0.618)).mul(1000)));
      If(r.lessThan(rate.mul(this.dt)), () => {
        const srf = ocean.surface(xz, float(0.5), shore, this.time);
        const pos = vec3(xz.x.add(srf.disp.x), srf.y.add(0.05), xz.y.add(srf.disp.z));
        const side = vec3(st.fwd.y.negate(), 0, st.fwd.x);
        const isDrift = hash21(vec2(float(i).add(1.9), r.mul(71))).mul(rate).lessThan(drift.mul(this.sprayRate));
        const wind3 = vec3(env.windDir.x, 0, env.windDir.y).mul(env.windSpeed);
        // a small burst per trigger: drops of different sizes and speeds,
        // now and then a puff of mist
        for (let j = 0; j < 3; j++) {
          const r2 = hash21(vec2(float(i).add(7.7 + j * 13.1), r.mul(97 + j * 11)));
          const r3 = hash21(vec2(float(i).add(3.1 + j * 5.3), r.mul(53 + j * 7)));
          const a = r2.mul(6.283);
          const up = mix(float(2.0), float(5.5), r3).mul(H.sqrt());
          const along = mix(float(0.5), float(3.2), r2).mul(H.sqrt());
          const velS = vec3(st.fwd.x, 0, st.fwd.y).mul(along).add(vec3(0, up, 0)).add(side.mul(cos(a).mul(0.9)));
          const mist = r3.lessThan(0.18);
          const sizeS = select(mist, mix(float(-0.25), float(-0.5), r2), mix(float(0.012), float(0.05), r2.mul(r2)));
          // spindrift: mostly fine mist lifted off the lip and carried downwind
          const velD = wind3.mul(mix(0.25, 0.6, r2)).add(vec3(0, mix(float(0.6), float(2.4), r3), 0)).add(side.mul(cos(a).mul(0.5)));
          const sizeD = select(r3.lessThan(0.7), mix(float(-0.2), float(-0.45), r2), mix(float(0.008), float(0.025), r2));
          const jit = side.mul(r2.sub(0.5).mul(0.8)).add(vec3(st.fwd.x, 0, st.fwd.y).mul(r3.sub(0.5).mul(0.5)));
          write(pos.add(jit), select(isDrift, velD, velS), select(isDrift, mix(float(1.2), float(2.6), r3), mix(float(0.9), float(2.2), r3)), select(isDrift, sizeD, sizeS));
        }
      });
    })(), (dt) => { this.frameU.value++; });
  }

  update(dt) {
    this.dt.value = Math.min(dt, 0.05);
    if (dt <= 0) return;
    this.slice.value = (this.slice.value + 1) % this.slices;
    this.renderer.compute(this.foamKernel);
  }

  /** TSL: persistent surf foam at world xz: vec2(amount, freshness) */
  sample(xz) {
    const uv = xz.sub(this.origin).div(WORLD.size);
    const t = texture(this.texture, uv).level(0);
    return vec2(t.r.mul(1.5), t.g);
  }
}
