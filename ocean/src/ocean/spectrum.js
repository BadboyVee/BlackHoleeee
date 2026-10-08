// CPU side of the ocean spectrum.
//
// The FFT cascades are seeded here: for every wave vector k of every cascade we
// evaluate a JONSWAP wind-sea + swell spectrum with depth (TMA) attenuation and
// Hasselmann/Donelan directional spreading, then draw a complex Gaussian
// amplitude. The GPU only animates h(k,t) and runs the inverse FFTs.
//
// It also integrates the slope variance per wavenumber band. The water shader
// uses that to turn the part of the spectrum that a pixel cannot resolve into
// microfacet roughness, which is what produces a physically sized glitter path
// instead of aliasing sparkles (Bruneton, Neyret & Holzschuch 2010).

const G = 9.81;

function mulberry32(seed) {
  let a = seed >>> 0;
  return () => {
    a |= 0; a = (a + 0x6D2B79F5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function gaussianPair(rand) {
  // Box-Muller
  let u1 = rand(); if (u1 < 1e-12) u1 = 1e-12;
  const u2 = rand();
  const r = Math.sqrt(-2 * Math.log(u1));
  return [r * Math.cos(2 * Math.PI * u2), r * Math.sin(2 * Math.PI * u2)];
}

function dispersion(k, depth) {
  return Math.sqrt(G * k * Math.tanh(Math.min(k * depth, 20)));
}

function dispersionDerivative(k, depth) {
  const th = Math.tanh(Math.min(k * depth, 20));
  const ch = Math.cosh(Math.min(k * depth, 20));
  const w = Math.sqrt(G * k * th);
  return G * (depth * k / ch / ch + th) / w / 2;
}

// Kitaigorodskii depth attenuation (TMA spectrum)
function tmaCorrection(omega, depth) {
  const omegaH = omega * Math.sqrt(depth / G);
  if (omegaH <= 1) return 0.5 * omegaH * omegaH;
  if (omegaH < 2) return 1.0 - 0.5 * (2.0 - omegaH) * (2.0 - omegaH);
  return 1;
}

function jonswap(omega, p) {
  const sigma = omega <= p.peakOmega ? 0.07 : 0.09;
  const r = Math.exp(-((omega - p.peakOmega) ** 2) / (2 * sigma * sigma * p.peakOmega * p.peakOmega));
  const oneOverOmega = 1 / omega;
  const peakOmegaOverOmega = p.peakOmega / omega;
  return p.scale * tmaCorrection(omega, p.depth) * p.alpha * G * G
    * oneOverOmega ** 5
    * Math.exp(-1.25 * peakOmegaOverOmega ** 4)
    * Math.pow(Math.abs(p.gamma), r);
}

function lgamma(x) {
  // Lanczos approximation of log Gamma, valid for x > 0
  const c = [76.18009172947146, -86.50532032941677, 24.01409824083091, -1.231739572450155, 0.1208650973866179e-2, -0.5395239384953e-5];
  let y = x, tmp = x + 5.5;
  tmp -= (x + 0.5) * Math.log(tmp);
  let ser = 1.000000000190015;
  for (let j = 0; j < 6; j++) ser += c[j] / ++y;
  return -tmp + Math.log(2.5066282746310005 * ser / x);
}

// normalisation of cos^(2s)(theta/2) over [-pi, pi]:  Gamma(s+1) / (2 sqrt(pi) Gamma(s+1/2))
function spreadNormalization(s) {
  return Math.exp(lgamma(s + 1) - lgamma(s + 0.5)) / (2 * Math.sqrt(Math.PI));
}

function spreadPower(omega, peakOmega, windSpeed) {
  if (omega > peakOmega) return 9.77 * Math.pow(Math.abs(omega / peakOmega), -2.5);
  return 6.97 * Math.pow(Math.abs(omega / peakOmega), 5);
}

function directionSpectrum(theta, omega, p) {
  const s = spreadPower(omega, p.peakOmega, p.windSpeed) + 16 * Math.tanh(Math.min(omega / p.peakOmega, 20)) * p.swell * p.swell;
  const cosT = Math.abs(Math.cos(0.5 * theta));
  const spread = spreadNormalization(s) * Math.pow(cosT, 2 * s);
  // blend towards a broad cos^2 distribution
  const broad = (2 / Math.PI) * Math.cos(theta) ** 2 * (Math.abs(theta) < Math.PI / 2 ? 1 : 0);
  return p.spreadBlend * spread + (1 - p.spreadBlend) * broad;
}

function prepareDisplay(d) {
  const U = Math.max(0.3, d.windSpeed);
  const F = Math.max(1000, d.fetch * 1000);
  const alpha = 0.076 * Math.pow(G * F / (U * U), -0.22);
  const peakOmega = 22 * Math.pow(Math.abs(U * F / G / G), -0.33);
  return {
    scale: d.scale,
    angle: d.windDirection * Math.PI / 180,
    spreadBlend: d.spreadBlend,
    swell: Math.min(1, Math.max(0, d.swell)),
    alpha,
    peakOmega,
    gamma: d.peakEnhancement,
    shortWavesFade: d.shortWavesFade,
    windSpeed: U,
    depth: d.depth,
  };
}

function shortWavesFade(kLength, fade) {
  return Math.exp(-fade * fade * kLength * kLength);
}

/**
 * Builds the initial spectrum for every cascade.
 * @param {object} opts { size, lengthScales[], cutoffs[] (k boundaries, length cascades+1), local, swell, seed, depth }
 */
export function buildSpectrum(opts) {
  const N = opts.size;
  const C = opts.lengthScales.length;
  const local = prepareDisplay({ ...opts.local, depth: opts.depth });
  const swell = prepareDisplay({ ...opts.swellSpectrum, depth: opts.depth });
  const h0 = new Float32Array(C * N * N * 4);
  const waves = new Float32Array(C * N * N * 4);
  // slope variance accumulated in log-spaced k bins, for the roughness tail
  const BINS = 48, kLo = 0.01, kHi = 2000;
  const binSlope = new Float64Array(BINS);
  const binOf = (k) => Math.max(0, Math.min(BINS - 1, Math.floor(Math.log(k / kLo) / Math.log(kHi / kLo) * BINS)));
  let heightVariance = 0;

  for (let c = 0; c < C; c++) {
    const L = opts.lengthScales[c];
    const dk = 2 * Math.PI / L;
    const kMin = opts.cutoffs[c], kMax = opts.cutoffs[c + 1];
    const rand = mulberry32((opts.seed || 1) * 7919 + c * 104729);
    const noise = new Float32Array(N * N * 2);
    for (let i = 0; i < N * N; i++) {
      const [a, b] = gaussianPair(rand);
      noise[i * 2] = a; noise[i * 2 + 1] = b;
    }
    const amp = new Float32Array(N * N * 2);
    for (let y = 0; y < N; y++) {
      for (let x = 0; x < N; x++) {
        const i = y * N + x;
        const kx = (x - N / 2) * dk;
        const kz = (y - N / 2) * dk;
        const k = Math.hypot(kx, kz);
        const base = (c * N * N + i) * 4;
        waves[base] = kx; waves[base + 1] = kz;
        if (k <= kMin || k > kMax || k < 1e-6) {
          waves[base + 2] = dispersion(Math.max(k, 1e-6), opts.depth); waves[base + 3] = 0;
          continue;
        }
        const kAngle = Math.atan2(kz, kx);
        const omega = dispersion(k, opts.depth);
        const dOmegadk = dispersionDerivative(k, opts.depth);
        waves[base + 2] = omega;
        waves[base + 3] = 1 / k;
        let spectrum = jonswap(omega, local) * directionSpectrum(wrapAngle(kAngle - local.angle), omega, local) * shortWavesFade(k, local.shortWavesFade);
        if (swell.scale > 0) {
          spectrum += jonswap(omega, swell) * directionSpectrum(wrapAngle(kAngle - swell.angle), omega, swell) * shortWavesFade(k, swell.shortWavesFade);
        }
        // S(k) d^2k = S(w) D(theta) dw dtheta  =>  S(k) = S(w) D(theta) (dw/dk) / k
        const Sk = spectrum * Math.abs(dOmegadk) / k;
        const variance = Sk * dk * dk;             // contribution of this wave to <eta^2>
        const A = Math.sqrt(variance / 2);
        amp[i * 2] = noise[i * 2] * A / Math.SQRT2;
        amp[i * 2 + 1] = noise[i * 2 + 1] * A / Math.SQRT2;
        heightVariance += variance;
        binSlope[binOf(k)] += variance * k * k;
      }
    }
    for (let y = 0; y < N; y++) {
      for (let x = 0; x < N; x++) {
        const i = y * N + x;
        const mi = ((N - y) % N) * N + ((N - x) % N);
        const base = (c * N * N + i) * 4;
        h0[base] = amp[i * 2];
        h0[base + 1] = amp[i * 2 + 1];
        h0[base + 2] = amp[mi * 2];          // conj(h0(-k))
        h0[base + 3] = -amp[mi * 2 + 1];
      }
    }
  }

  // cumulative resolved slope variance as a function of cutoff wavenumber
  const cumulative = new Float32Array(BINS);
  let acc = 0;
  for (let b = 0; b < BINS; b++) { acc += binSlope[b]; cumulative[b] = acc; }
  // Cox & Munk (1954) total mean square slope of a clean sea surface
  const U = local.windSpeed;
  const coxMunk = 0.003 + 0.00512 * U;
  return {
    h0, waves, heightVariance,
    significantWaveHeight: 4 * Math.sqrt(heightVariance),
    slopeTable: { bins: BINS, kLo, kHi, cumulative, total: acc, coxMunk },
    peakWavelength: 2 * Math.PI * G / (local.peakOmega * local.peakOmega),
  };
}

function wrapAngle(a) {
  while (a > Math.PI) a -= 2 * Math.PI;
  while (a < -Math.PI) a += 2 * Math.PI;
  return a;
}

/**
 * Unresolved slope variance for a set of cutoff wavenumbers, sampled at
 * log-spaced cutoffs so the shader can index it with log2(k).
 */
export function unresolvedSlopeTable(slopeTable, samples = 16, kFrom = 0.05, kTo = 800) {
  const out = new Float32Array(samples);
  const { bins, kLo, kHi, cumulative, total, coxMunk } = slopeTable;
  for (let i = 0; i < samples; i++) {
    const kc = kFrom * Math.pow(kTo / kFrom, i / (samples - 1));
    const b = Math.max(0, Math.min(bins - 1, Math.floor(Math.log(kc / kLo) / Math.log(kHi / kLo) * bins)));
    const resolved = b > 0 ? cumulative[b - 1] : 0;
    // everything the sim can't resolve at this footprint, plus the capillary
    // content beyond the smallest cascade, is folded into the Cox-Munk budget
    const unresolved = Math.max(coxMunk - resolved, (total - resolved)) ;
    out[i] = Math.max(0.0015, Math.min(0.12, unresolved));
  }
  return out;
}
