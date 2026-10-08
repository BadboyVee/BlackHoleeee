// GPU FFT ocean: three cascades of 256² Tessendorf waves.
//
//  spectrum (CPU, on parameter change)  ->  h0 / wave buffers
//  per frame:
//    evolve    h(k,t) and the 8 derived spectra, packed as 4 complex signals
//    fftRows   256-point Stockham IFFT along x, whole row in workgroup memory
//    fftCols   same along z
//    assemble  sign permute, choppy displacement, derivatives, Jacobian foam
//
// Output per cascade (rgba16f, mipmapped, repeat-wrapped):
//    displacement  (Dx, Dy, Dz, foam)
//    derivatives   (dDy/dx, dDy/dz, dDx/dx, dDz/dz)
//    previous      last frame's displacement (motion vectors for TAA)

import * as THREE from 'three/webgpu';
import {
  Fn, uniform, storage, instanceIndex, invocationLocalIndex, workgroupId, workgroupArray,
  workgroupBarrier, textureStore, float, uint, vec2, vec4, uvec2, cos, sin, exp, max, min, clamp, mix, smoothstep,
} from 'three/tsl';
import { buildSpectrum, unresolvedSlopeTable } from './spectrum.js';

export const OCEAN_SIZE = 256;

export class OceanFFT {
  constructor(renderer, params) {
    this.renderer = renderer;
    this.params = params;
    const N = this.N = OCEAN_SIZE;
    this.lengthScales = params.lengthScales;
    const C = this.C = this.lengthScales.length;
    this.cutoffs = [0.0001];
    for (let c = 1; c < C; c++) this.cutoffs.push(4 * 2 * Math.PI / this.lengthScales[c]);
    this.cutoffs.push(9999);

    this.time = uniform(0);
    this.deltaTime = uniform(0.016);
    this.choppiness = uniform(params.choppiness);
    this.foamThreshold = uniform(params.foamThreshold);
    this.foamGain = uniform(params.foamGain);
    this.foamDecay = uniform(params.foamDecay);

    const count = C * N * N;
    this.h0Attr = new THREE.StorageBufferAttribute(new Float32Array(count * 4), 4);
    this.wavesAttr = new THREE.StorageBufferAttribute(new Float32Array(count * 4), 4);
    this.h0 = storage(this.h0Attr, 'vec4', count).toReadOnly();
    this.waves = storage(this.wavesAttr, 'vec4', count).toReadOnly();
    // 2 signals (vec4 = two complex numbers) per cascade
    this.dataAttr = new THREE.StorageBufferAttribute(new Float32Array(count * 2 * 4), 4);
    this.data = storage(this.dataAttr, 'vec4', count * 2);
    this.foamAttr = new THREE.StorageBufferAttribute(new Float32Array(count), 1);
    this.foam = storage(this.foamAttr, 'float', count);
    // the displacement written last frame, handed on as the "previous" texture
    this.lastAttr = new THREE.StorageBufferAttribute(new Float32Array(count * 4), 4);
    this.last = storage(this.lastAttr, 'vec4', count);

    this.displacement = [];
    this.derivatives = [];
    this.previous = [];
    for (let c = 0; c < C; c++) {
      this.displacement.push(makeTarget(N, `ocean.disp${c}`));
      this.derivatives.push(makeTarget(N, `ocean.deriv${c}`));
      this.previous.push(makeTarget(N, `ocean.dispPrev${c}`));
    }

    this._buildKernels();
    this.updateSpectrum();
  }

  updateSpectrum() {
    const p = this.params;
    const t0 = performance.now();
    const s = buildSpectrum({
      size: this.N, lengthScales: this.lengthScales, cutoffs: this.cutoffs, depth: p.depth, seed: p.seed,
      local: p.local, swellSpectrum: p.swellSpectrum,
    });
    this.h0Attr.array.set(s.h0);
    this.h0Attr.needsUpdate = true;
    this.wavesAttr.array.set(s.waves);
    this.wavesAttr.needsUpdate = true;
    this.stats = { hs: s.significantWaveHeight, peakWavelength: s.peakWavelength, ms: performance.now() - t0 };
    this.unresolvedSlope = unresolvedSlopeTable(s.slopeTable, 16, 0.05, 800);
  }

  _buildKernels() {
    const N = this.N, C = this.C, NN = N * N;
    const LOG2N = Math.log2(N);
    const { h0, waves, data, time } = this;

    // --- time evolution --------------------------------------------------------
    this.evolveKernel = Fn(() => {
      const i = instanceIndex;
      const w = waves.element(i);
      const h = h0.element(i);
      const phase = w.z.mul(time);
      const c = cos(phase), s = sin(phase);
      // h(k,t) = h0(k) e^{-iwt} + conj(h0(-k)) e^{iwt}
      const hr = h.x.mul(c).add(h.y.mul(s)).add(h.z.mul(c).sub(h.w.mul(s)));
      const hi = h.y.mul(c).sub(h.x.mul(s)).add(h.z.mul(s).add(h.w.mul(c)));
      const ihr = hi.negate(), ihi = hr; // i*h
      const kx = w.x, kz = w.y, oneOverK = w.w;
      // Dx = i kx/k h, Dz = i kz/k h, Dy = h
      const dxr = ihr.mul(kx).mul(oneOverK), dxi = ihi.mul(kx).mul(oneOverK);
      const dzr = ihr.mul(kz).mul(oneOverK), dzi = ihi.mul(kz).mul(oneOverK);
      // dDx/dz = -kx kz/k h
      const dxzr = hr.mul(kx).mul(kz).mul(oneOverK).negate(), dxzi = hi.mul(kx).mul(kz).mul(oneOverK).negate();
      // dDy/dx = i kx h, dDy/dz = i kz h
      const dyxr = ihr.mul(kx), dyxi = ihi.mul(kx);
      const dyzr = ihr.mul(kz), dyzi = ihi.mul(kz);
      // dDx/dx = -kx²/k h, dDz/dz = -kz²/k h
      const dxxr = hr.mul(kx).mul(kx).mul(oneOverK).negate(), dxxi = hi.mul(kx).mul(kx).mul(oneOverK).negate();
      const dzzr = hr.mul(kz).mul(kz).mul(oneOverK).negate(), dzzi = hi.mul(kz).mul(kz).mul(oneOverK).negate();
      // pack A + iB  =  (a.re - b.im, a.im + b.re)
      const cascade = i.div(NN);
      const local = i.mod(NN);
      const o0 = cascade.mul(2 * NN).add(local);
      data.element(o0).assign(vec4(dxr.sub(dzi), dxi.add(dzr), hr.sub(dxzi), hi.add(dxzr)));
      data.element(o0.add(NN)).assign(vec4(dyxr.sub(dyzi), dyxi.add(dyzr), dxxr.sub(dzzi), dxxi.add(dzzr)));
    })().compute(C * NN, [64]);

    // --- Stockham radix-2 IFFT, one line per workgroup -------------------------
    const makeFFT = (vertical) => Fn(() => {
      const shared = workgroupArray('vec4', N * 2);
      const lid = invocationLocalIndex;
      const line = workgroupId.x;
      let base, stride;
      if (!vertical) {
        base = line.mul(N);
        stride = uint(1);
      } else {
        base = line.div(N).mul(NN).add(line.mod(N));
        stride = uint(N);
      }
      const i0 = lid, i1 = lid.add(N / 2);
      shared.element(i0).assign(data.element(base.add(i0.mul(stride))));
      shared.element(i1).assign(data.element(base.add(i1.mul(stride))));
      workgroupBarrier();
      let src = 0, dst = N;
      for (let st = 0; st < LOG2N; st++) {
        const ns = 1 << st;
        const k = lid.bitAnd(uint(ns - 1));
        const v0 = shared.element(lid.add(src)).toVar();
        const v1 = shared.element(lid.add(src + N / 2)).toVar();
        const ang = float(k).mul(Math.PI / ns);
        const c = cos(ang).toVar(), s = sin(ang).toVar();
        const t = vec4(
          v1.x.mul(c).sub(v1.y.mul(s)), v1.x.mul(s).add(v1.y.mul(c)),
          v1.z.mul(c).sub(v1.w.mul(s)), v1.z.mul(s).add(v1.w.mul(c)),
        ).toVar();
        const idxD = lid.sub(k).mul(2).add(k);
        shared.element(idxD.add(dst)).assign(v0.add(t));
        shared.element(idxD.add(dst + ns)).assign(v0.sub(t));
        workgroupBarrier();
        [src, dst] = [dst, src];
      }
      data.element(base.add(i0.mul(stride))).assign(shared.element(i0.add(src)));
      data.element(base.add(i1.mul(stride))).assign(shared.element(i1.add(src)));
    })().compute(C * 2 * N * (N / 2), [N / 2]);

    this.fftRows = makeFFT(false);
    this.fftCols = makeFFT(true);

    // --- assemble per cascade (storage texture limit is 4 per stage) -----------
    this.assembleKernels = [];
    for (let c = 0; c < C; c++) {
      const dispTex = this.displacement[c];
      const derivTex = this.derivatives[c];
      const prevTex = this.previous[c];
      const kernel = Fn(() => {
        const i = instanceIndex;
        const x = i.mod(N), y = i.div(N);
        const sign = float(1).sub(float(x.add(y).bitAnd(uint(1))).mul(2));
        const s0 = data.element(uint(c * 2 * NN).add(i)).mul(sign).toVar();
        const s1 = data.element(uint((c * 2 + 1) * NN).add(i)).mul(sign).toVar();
        const lambda = this.choppiness;
        const dxx = s1.z.mul(lambda), dzz = s1.w.mul(lambda), dxz = s0.w.mul(lambda);
        const jacobian = dxx.add(1).mul(dzz.add(1)).sub(dxz.mul(dxz));
        // whitecaps: fresh foam where the surface is compressed, then an
        // exponential decay so it lingers and thins into lace behind the crest
        const fi = uint(c * NN).add(i);
        const prev = this.foam.element(fi);
        const fresh = clamp(this.foamThreshold.sub(jacobian).mul(this.foamGain), 0, 1);
        const decayed = prev.mul(exp(this.deltaTime.negate().div(this.foamDecay)));
        const f = max(decayed, fresh).toVar();
        this.foam.element(fi).assign(f);
        const coord = uvec2(x, y);
        const disp = vec4(s0.x.mul(lambda), s0.z, s0.y.mul(lambda), f).toVar();
        textureStore(prevTex, coord, this.last.element(fi));
        this.last.element(fi).assign(disp);
        textureStore(dispTex, coord, disp);
        textureStore(derivTex, coord, vec4(s1.x, s1.y, dxx, dzz));
      })().compute(NN, [64]);
      this.assembleKernels.push(kernel);
    }
  }

  update(dt, time) {
    this.time.value = time;
    this.deltaTime.value = Math.min(dt, 0.1);
    const q = new URLSearchParams(location.search);
    const skip = q.get('fftskip') || '';
    const list = [];
    if (!skip.includes('e')) list.push(this.evolveKernel);
    if (!skip.includes('r')) list.push(this.fftRows);
    if (!skip.includes('c')) list.push(this.fftCols);
    if (!skip.includes('a')) list.push(...this.assembleKernels);
    if (list.length) this.renderer.compute(list);
  }
}

function makeTarget(N, name) {
  const t = new THREE.StorageTexture(N, N);
  t.type = THREE.HalfFloatType;
  t.format = THREE.RGBAFormat;
  t.wrapS = t.wrapT = THREE.RepeatWrapping;
  t.magFilter = THREE.LinearFilter;
  t.minFilter = THREE.LinearMipmapLinearFilter;
  t.generateMipmaps = true;
  t.anisotropy = 8;
  t.name = name;
  return t;
}
