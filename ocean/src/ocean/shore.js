// Shoreline waves: shoaling swell trains that refract into the bay, steepen,
// curl, plunge and run up the beach as swash.
//
// CPU: a phase field Phi(x) = (1/2pi) ∫ k(D) ds from the shoreline along the
// shore normals (k from the finite-depth dispersion relation for the swell
// period), so crests follow the coastline, bunch up in shallow water and
// arrive together along a contour.
//
// GPU (TSL, shared by the water surface, terrain wetness and spray emitters):
//   crest index n + phase psi  ->  per-crest height (sets, along-shore peaks)
//   shoaling (Green's law) -> breaking index beta = f(H / (0.78 D))
//   keyframed breaker cross-section (shoreProfiles.js) -> folded geometry
//   beyond the shoreline: analytic run-up / backwash of the bore (swash)

import * as THREE from 'three/webgpu';
import {
  Fn, float, vec2, vec3, vec4, uniform, texture, floor, fract, round, clamp, smoothstep, mix, max, min,
  abs, pow, sqrt, exp, sin, cos, atan, normalize, length, select, dot, tanh,
} from 'three/tsl';
import { WORLD, ISLAND } from '../world/island.js';
import { buildProfileTexture, PROFILE } from './shoreProfiles.js';
import { gnoise2, vnoise2, hash21 } from '../render/tslnoise.js';
import { env } from '../env.js';

const G = 9.81;

function waveNumber(omega, depth) {
  // Fenton & McKee explicit approximation of w^2 = g k tanh(k d)
  const k0 = omega * omega / G;
  const d = Math.max(depth, 0.05);
  return k0 / Math.pow(Math.tanh(Math.pow(k0 * d, 0.75)), 2 / 3);
}

export class Shore {
  constructor(island, terrain) {
    this.island = island;
    this.terrain = terrain;
    this.period = uniform(9.5);
    this.swellHeight = uniform(0.85);     // deep-water height of the shore swell (m)
    this.peakWidth = uniform(62);         // along-shore size of breaking peaks (m)
    this.obliqueness = uniform(1 / 420);  // cycles per metre along shore
    this.setLength = uniform(7.3);        // waves per set
    this.intensity = uniform(1);
    this.phaseTexture = this._buildPhaseField(9.5);
    this.profileTexture = buildProfileTexture();
    this.origin = vec2(WORLD.originX, WORLD.originZ);
    this.invSize = float(1 / WORLD.size);
  }

  // Swell travel time field tau (in wave cycles) from the open ocean to every
  // point: fast marching on |grad tau| = k(D) / 2pi. Wavefronts refract around
  // the headlands and bunch up over shallow water; land is crossed with a tiny
  // slowness so each beach point inherits its shoreline arrival phase.
  _buildPhaseField(period) {
    const N = WORLD.res, TEX = WORLD.size / N;
    const { height } = this.island;
    const omega = 2 * Math.PI / period;
    const F = new Float32Array(N * N);
    const sea = new Uint8Array(N * N);
    for (let i = 0; i < N * N; i++) {
      const h = height[i];
      sea[i] = h < 0 ? 1 : 0;
      F[i] = waveNumber(omega, Math.max(-h, 0.05)) / (2 * Math.PI);
    }
    const tau = new Float32Array(N * N).fill(Infinity);
    const state = new Uint8Array(N * N); // 0 far, 1 trial, 2 known
    // binary min-heap of indices keyed by tau
    const heap = new Int32Array(N * N * 2);
    let hs = 0;
    const pos = new Int32Array(N * N).fill(-1);
    const swap = (a, b) => { const ia = heap[a], ib = heap[b]; heap[a] = ib; heap[b] = ia; pos[ib] = a; pos[ia] = b; };
    const up = (i) => { while (i > 0) { const p = (i - 1) >> 1; if (tau[heap[p]] <= tau[heap[i]]) break; swap(i, p); i = p; } };
    const down = (i) => { for (;;) { const l = i * 2 + 1, r = l + 1; let m = i; if (l < hs && tau[heap[l]] < tau[heap[m]]) m = l; if (r < hs && tau[heap[r]] < tau[heap[m]]) m = r; if (m === i) break; swap(i, m); i = m; } };
    const push = (k) => { heap[hs] = k; pos[k] = hs; hs++; up(hs - 1); };
    const pop = () => { const k = heap[0]; hs--; if (hs > 0) { heap[0] = heap[hs]; pos[heap[0]] = 0; down(0); } pos[k] = -1; return k; };
    // source: the southern edge of the map (open ocean swell from the south)
    for (let i = 0; i < N; i++) { const k = (N - 1) * N + i; tau[k] = 0; state[k] = 1; push(k); }
    const solve = (k) => {
      const i = k % N, j = (k / N) | 0;
      const a = Math.min(i > 0 && state[k - 1] === 2 ? tau[k - 1] : Infinity, i < N - 1 && state[k + 1] === 2 ? tau[k + 1] : Infinity);
      const b = Math.min(j > 0 && state[k - N] === 2 ? tau[k - N] : Infinity, j < N - 1 && state[k + N] === 2 ? tau[k + N] : Infinity);
      const f = F[k] * TEX;
      if (!isFinite(a) && !isFinite(b)) return Infinity;
      if (!isFinite(a)) return b + f;
      if (!isFinite(b)) return a + f;
      if (Math.abs(a - b) >= f) return Math.min(a, b) + f;
      return 0.5 * (a + b + Math.sqrt(2 * f * f - (a - b) * (a - b)));
    };
    while (hs > 0) {
      const k = pop();
      state[k] = 2;
      const i = k % N, j = (k / N) | 0;
      const nb = [i > 0 ? k - 1 : -1, i < N - 1 ? k + 1 : -1, j > 0 ? k - N : -1, j < N - 1 ? k + N : -1];
      for (const q of nb) {
        if (q < 0 || state[q] === 2 || !sea[q]) continue;
        const t = solve(q);
        if (t < tau[q]) {
          tau[q] = t;
          if (state[q] === 1) up(pos[q]); else { state[q] = 1; push(q); }
        }
      }
    }
    // extend onto land: each land texel inherits the arrival phase of the
    // nearest wet shoreline (processed in order of distance from the sea)
    const sdf = this.island.sdf;
    const landIdx = [];
    for (let k = 0; k < N * N; k++) if (!sea[k] || !isFinite(tau[k])) landIdx.push(k);
    landIdx.sort((a, b) => sdf[b] - sdf[a]);
    const known = new Uint8Array(N * N);
    for (let k = 0; k < N * N; k++) known[k] = sea[k] && isFinite(tau[k]) ? 1 : 0;
    for (let pass = 0; pass < 2; pass++) {
      for (const k of landIdx) {
        if (known[k]) continue;
        const i = k % N, j = (k / N) | 0;
        let acc = 0, n = 0;
        if (i > 0 && known[k - 1]) { acc += tau[k - 1]; n++; }
        if (i < N - 1 && known[k + 1]) { acc += tau[k + 1]; n++; }
        if (j > 0 && known[k - N]) { acc += tau[k - N]; n++; }
        if (j < N - 1 && known[k + N]) { acc += tau[k + N]; n++; }
        if (n > 0) { tau[k] = acc / n; known[k] = 1; }
      }
    }
    for (let k = 0; k < N * N; k++) if (!known[k]) tau[k] = 0;
    // propagation direction = grad tau (normalised)
    const data = new Uint16Array(N * N * 4);
    const toH = THREE.DataUtils.toHalfFloat;
    for (let j = 0; j < N; j++) for (let i = 0; i < N; i++) {
      const k = j * N + i;
      const l = tau[j * N + Math.max(i - 1, 0)], r = tau[j * N + Math.min(i + 1, N - 1)];
      const d = tau[Math.max(j - 1, 0) * N + i], u = tau[Math.min(j + 1, N - 1) * N + i];
      let gx = r - l, gz = u - d;
      const len = Math.hypot(gx, gz) || 1;
      const hi = Math.round(tau[k] * 16) / 16;
      data[k * 4] = toH(hi); data[k * 4 + 1] = toH(tau[k] - hi);
      data[k * 4 + 2] = toH(gx / len); data[k * 4 + 3] = toH(gz / len);
    }
    const t = new THREE.DataTexture(data, N, N, THREE.RGBAFormat, THREE.HalfFloatType);
    t.magFilter = THREE.LinearFilter;
    t.minFilter = THREE.LinearFilter;
    t.wrapS = t.wrapT = THREE.ClampToEdgeWrapping;
    t.generateMipmaps = false;
    t.needsUpdate = true;
    t.name = 'shore.phase';
    this.tauCPU = tau;
    return t;
  }

  /** CPU travel-time lookup (cycles from the open ocean) */
  tauAt(x, z) {
    const N = WORLD.res, TEX = WORLD.size / N;
    const i = Math.max(0, Math.min(N - 1, Math.floor((x - WORLD.originX) / TEX)));
    const j = Math.max(0, Math.min(N - 1, Math.floor((z - WORLD.originZ) / TEX)));
    return this.tauCPU[j * N + i];
  }

  /**
   * TSL wave state at a world position.
   * @param levelSample use explicit-LOD sampling (vertex/compute/non-uniform)
   */
  state(xz, time, levelSample = true) {
    const uvw = xz.sub(this.origin).mul(this.invSize);
    const tdata = levelSample ? texture(this.terrain.dataTexture, uvw).level(0) : texture(this.terrain.dataTexture, uvw);
    const phiT = levelSample ? texture(this.phaseTexture, uvw).level(0) : texture(this.phaseTexture, uvw);
    const bed = tdata.x, sdf = tdata.y;
    const dir = normalize(vec2(tdata.z, tdata.w).add(vec2(1e-5, 0)));   // seaward (shore normal)
    const fwd = normalize(phiT.zw.add(vec2(1e-5, 0)));                  // swell travel direction
    const depth = max(bed.negate(), 0.04);
    // along-shore coordinate from the island's polar frame
    const rel = xz.sub(vec2(ISLAND.cx, ISLAND.cz));
    const u = atan(rel.x, rel.y).mul(ISLAND.R);
    const tau = phiT.x.add(phiT.y);
    const pc = time.div(this.period).sub(tau);
    const n = round(pc);
    const psi = pc.sub(n); // (-0.5, 0.5]: >0 seaward (behind) crest n, <0 shoreward
    const phi = sdf; // metres offshore, for the fade-in
    // per-crest height: sets of larger waves + along-shore peaks
    const setEnv = sin(n.div(this.setLength).mul(6.2831853).add(1.3)).mul(0.5).add(0.5);
    const crestRand = hash21(vec2(n, 3.7));
    const peak = smoothstep(-0.35, 0.55, gnoise2(vec2(u.div(this.peakWidth), n.mul(0.61)).add(vec2(0, 11.3))));
    const amp = mix(0.55, 1.12, setEnv).mul(mix(0.8, 1.1, crestRand)).mul(mix(0.28, 1.0, peak));
    // shoaling (Green's law, referenced to 9 m) and offshore fade-in
    const shoal = clamp(pow(float(9).div(max(depth, 0.3)), 0.25), 1.0, 1.75);
    const fadeIn = smoothstep(240, 120, sdf).mul(smoothstep(-1.0, 1.5, sdf));
    const H0 = this.swellHeight.mul(amp).mul(shoal).mul(fadeIn).mul(this.intensity);
    const ratio = H0.div(depth.mul(0.78));
    const beta = clamp(ratio.sub(0.82).mul(2.6), 0, PROFILE.betaMax);
    // once broken, the bore height is limited by the depth
    const H = mix(H0, min(H0, depth.mul(0.55).add(0.06)), smoothstep(2.2, 3.1, beta));
    // local wavelength (m per cycle) from the dispersion relation
    const omega = float(6.2831853).div(this.period);
    const k0 = omega.mul(omega).div(G);
    const kd = pow(k0.mul(depth), 0.75);
    const k = k0.div(pow(tanh(kd).max(1e-3), 2 / 3));
    const lambda = float(6.2831853).div(k);
    return { bed, sdf, dir, fwd, depth, u, pc, n, psi, H, beta, lambda, phi, amp };
  }

  /**
   * Breaker geometry: displacement (world), analytic normal slopes, whitewater and
   * sheet thinness at a surface point, given its wave state.
   */
  breaker(st, levelSample = true) {
    const H = st.H.max(1e-3);
    // rest distance from the crest in wave heights (s > 0 seaward)
    const s = st.psi.mul(st.lambda).div(H);
    const S = PROFILE.S, span = PROFILE.sMax - PROFILE.sMin;
    const sampleAt = (sv) => {
      const uvp = vec2(clamp(sv.sub(PROFILE.sMin).div(span), 0, 1).mul((S - 1) / S).add(0.5 / S), st.beta.div(PROFILE.betaMax).mul((PROFILE.B - 1) / PROFILE.B).add(0.5 / PROFILE.B));
      return texture(this.profileTexture, uvp).level(0);
    };
    const inZone = s.greaterThan(PROFILE.sMin).and(s.lessThan(PROFILE.sMax));
    const p = sampleAt(s);
    const ds = 0.12;
    const pA = sampleAt(s.add(ds)), pB = sampleAt(s.sub(ds));
    // outside the keyframed zone: long, shallow trough with a gentle rise
    const troughY = cos(st.psi.mul(6.2831853)).mul(0.06).sub(0.1);
    const w = smoothstep(PROFILE.sMin, PROFILE.sMin + 1.2, s).mul(smoothstep(PROFILE.sMax, PROFILE.sMax - 1.2, s));
    const dxi = select(inZone, p.x, float(0)).mul(w);
    const y = mix(troughY, p.y, w).sub(0.12);
    // tangent along increasing s (seaward): rest moves -1 per unit s
    const dDxi = pA.x.sub(pB.x).div(2 * ds).mul(w);
    const dY = pA.y.sub(pB.y).div(2 * ds).mul(w);
    const a = dDxi.sub(1), b = dY; // tangent = a*fwd + b*up
    // normal = b*fwd - a*up (points up for undisturbed water)
    const nf = b, nu = a.negate();
    const disp = vec3(st.fwd.x.mul(dxi.mul(H)), y.mul(H), st.fwd.y.mul(dxi.mul(H)));
    // slope form (for combining with FFT slopes): -dN/dN.y along fwd
    const slopeAlong = nf.div(nu.max(0.05)).negate();
    const slope = st.fwd.mul(slopeAlong);
    const flipped = nu.lessThan(0);
    const foam = p.z.mul(w);
    const thin = p.w.mul(w);
    return { disp, slope, foam, thin, normalFwd: nf, normalUp: nu, flipped };
  }

  /**
   * Swash on the beach face: the bore runs up the slope and drains back.
   * Returns thickness (m), swash foam and wetness for a land-side point.
   */
  swash(st, time) {
    const d = st.sdf.negate();                      // metres inland from the MSL shoreline
    const T = this.period;
    // time since the bore of crest n reached the shoreline
    const pcShore = st.pc;
    const tau = fract(pcShore).mul(T);
    const nShore = floor(pcShore);
    // bore height at the shoreline for this crest (same set / peak logic)
    const setEnv = sin(nShore.div(this.setLength).mul(6.2831853).add(1.3)).mul(0.5).add(0.5);
    const peak = smoothstep(-0.35, 0.55, gnoise2(vec2(st.u.div(this.peakWidth), nShore.mul(0.61)).add(vec2(0, 11.3))));
    const hb = this.swellHeight.mul(mix(0.55, 1.12, setEnv)).mul(mix(0.35, 1.0, peak)).mul(0.42).mul(this.intensity);
    const slope = float(0.082);
    const g = G * 0.082;
    const v0 = sqrt(hb.mul(2 * G)).mul(0.85);
    const tUp = v0.div(g);
    // up-rush ballistic, backwash slower (friction + infiltration)
    const up = v0.mul(tau).sub(tau.mul(tau).mul(0.5 * g));
    const tb = tau.sub(tUp);
    const rmax = v0.mul(v0).div(2 * g);
    const back = rmax.sub(tb.mul(tb).mul(0.32 * g));
    const edge = max(select(tau.lessThan(tUp), up, back), 0);
    const frac = clamp(d.div(max(edge, 1e-3)), 0, 1);
    const thick = select(d.lessThan(edge), pow(float(1).sub(frac), 0.55).mul(hb.mul(0.55)).mul(exp(tau.mul(-0.22))), float(0));
    // foam rides the front up the beach and is stranded as it drains
    const front = smoothstep(0.5, 0.95, frac).mul(select(tau.lessThan(tUp), float(1), float(0.6)));
    const foam = clamp(front.add(float(0.35).mul(exp(tau.mul(-0.35)))), 0, 1).mul(select(d.lessThan(edge.add(0.4)), float(1), float(0)));
    // wetness: the sand stays dark where recent swash reached, drying slowly
    const reached = smoothstep(rmax.add(0.3), rmax.sub(0.5), d);
    const wet = max(reached.mul(exp(tau.mul(-0.03))), smoothstep(1.2, 0.2, d));
    // stranded foam fading into the sand after the water has gone
    const stranded = select(d.greaterThan(edge), smoothstep(rmax.add(0.2), rmax.sub(0.8), d).mul(exp(tau.mul(-0.45))), float(0));
    return { thick, foam, wet, stranded, edge, tau, rmax, hb, slope };
  }
}
