// Physically based atmosphere after Hillaire, "A Scalable and Production Ready
// Sky and Atmosphere Rendering Technique" (EGSR 2020).
//
//   transmittance LUT   256×64   T(r, mu)                once
//   multi-scattering    32×32    Psi_ms(r, mu_s)         once
//   sky-view LUT        256×128  L(view az/el) at eye    every frame (cheap)
//
// Units: kilometres for geometry, radiance relative to a sun illuminance of 1.
// A small JS port of the transmittance integral gives the CPU the sun colour
// and sky irradiance used for the scene lights.

import * as THREE from 'three/webgpu';
import {
  Fn, uniform, vec2, vec3, vec4, float, int, uint, uvec2, ivec2, sqrt, max, min, clamp, exp, abs,
  dot, normalize, length, mix, cos, sin, acos, atan, sign, pow, textureStore, instanceIndex,
  texture, Loop, If, select, PI, textureLoad, fract, floor,
} from 'three/tsl';

export const ATMO = {
  bottom: 6360.0,
  top: 6460.0,
  rayleighScattering: [5.802e-3, 13.558e-3, 33.1e-3], // per km
  rayleighScale: 8.0,
  mieScattering: 3.996e-3,
  mieExtinction: 4.44e-3,
  mieScale: 1.2,
  mieG: 0.8,
  ozoneAbsorption: [0.650e-3, 1.881e-3, 0.085e-3],
  groundAlbedo: 0.3,
};

const TRANS_W = 256, TRANS_H = 64, MS_SIZE = 32, SKY_W = 256, SKY_H = 128;

function storageTex(w, h, name) {
  const t = new THREE.StorageTexture(w, h);
  t.type = THREE.HalfFloatType;
  t.format = THREE.RGBAFormat;
  t.magFilter = THREE.LinearFilter;
  t.minFilter = THREE.LinearFilter;
  t.generateMipmaps = false;
  t.wrapS = THREE.ClampToEdgeWrapping;
  t.wrapT = THREE.ClampToEdgeWrapping;
  t.name = name;
  return t;
}

// ---------------------------------------------------------------- TSL helpers
const cBottom = float(ATMO.bottom), cTop = float(ATMO.top);
const rayleighS = vec3(...ATMO.rayleighScattering);
const ozoneA = vec3(...ATMO.ozoneAbsorption);

export function scatteringAt(altitude) {
  const rd = exp(altitude.div(-ATMO.rayleighScale));
  const md = exp(altitude.div(-ATMO.mieScale));
  const od = max(float(0), float(1).sub(abs(altitude.sub(25)).div(15)));
  const rayleigh = rayleighS.mul(rd).toVar();
  const mie = float(ATMO.mieScattering).mul(md).toVar();
  const extinction = rayleigh.add(float(ATMO.mieExtinction).mul(md)).add(ozoneA.mul(od)).toVar();
  return { rayleigh, mie, extinction };
}

const extinctionAt = Fn(([altitude]) => {
  const rd = exp(altitude.div(-ATMO.rayleighScale));
  const md = exp(altitude.div(-ATMO.mieScale));
  const od = max(float(0), float(1).sub(abs(altitude.sub(25)).div(15)));
  return rayleighS.mul(rd).add(float(ATMO.mieExtinction).mul(md)).add(ozoneA.mul(od));
}).setLayout({ name: 'atmoExtinction', type: 'vec3', inputs: [{ name: 'altitude', type: 'float' }] });

// distance to a sphere of radius R from (r, mu); returns -1 if none.
// Uses the stable quadratic form with c = (r-R)(r+R): with the eye 2 m above a
// 6360 km planet the naive formula cancels to garbage in float32.
export const raySphere = Fn(([r, mu, R]) => {
  const b = r.mul(mu);
  const c = r.sub(R).mul(r.add(R));
  const disc = b.mul(b).sub(c);
  const res = float(-1).toVar();
  If(disc.greaterThanEqual(0), () => {
    const sq = sqrt(disc);
    const q = select(b.greaterThanEqual(0), b.add(sq).negate(), sq.sub(b));
    const qq = select(abs(q).lessThan(1e-12), float(1e-12), q);
    const t0 = qq, t1 = c.div(qq);
    const tmin = min(t0, t1), tmax = max(t0, t1);
    res.assign(select(tmin.greaterThan(0), tmin, select(tmax.greaterThan(0), tmax, float(-1))));
  });
  return res;
}).setLayout({ name: 'raySphere', type: 'float', inputs: [{ name: 'r', type: 'float' }, { name: 'mu', type: 'float' }, { name: 'R', type: 'float' }] });

export const transmittanceUV = Fn(([r, mu]) => {
  const H = sqrt(cTop.mul(cTop).sub(cBottom.mul(cBottom)));
  const rho = sqrt(max(r.mul(r).sub(cBottom.mul(cBottom)), 0));
  const disc = r.mul(r).mul(mu.mul(mu).sub(1)).add(cTop.mul(cTop));
  const d = max(float(0), r.negate().mul(mu).add(sqrt(max(disc, 0))));
  const dMin = cTop.sub(r), dMax = rho.add(H);
  return vec2(d.sub(dMin).div(dMax.sub(dMin)), rho.div(H));
}).setLayout({ name: 'transmittanceUV', type: 'vec2', inputs: [{ name: 'r', type: 'float' }, { name: 'mu', type: 'float' }] });

export const rayleighPhase = (c) => float(3 / (16 * Math.PI)).mul(c.mul(c).add(1));
export const hgPhase = (c, g) => {
  const g2 = g * g;
  return float((1 - g2) / (4 * Math.PI)).div(pow(float(1 + g2).sub(c.mul(2 * g)).max(1e-4), 1.5));
};
// Cornette-Shanks, a better Mie phase for haze
export const csPhase = (c, g) => {
  const g2 = g * g;
  const k = (3 / (8 * Math.PI)) * (1 - g2) / (2 + g2);
  return float(k).mul(c.mul(c).add(1)).div(pow(float(1 + g2).sub(c.mul(2 * g)).max(1e-4), 1.5));
};

export class Atmosphere {
  constructor(renderer) {
    this.renderer = renderer;
    this.transmittance = storageTex(TRANS_W, TRANS_H, 'atmo.transmittance');
    this.multiScattering = storageTex(MS_SIZE, MS_SIZE, 'atmo.multiscattering');
    this.skyView = storageTex(SKY_W, SKY_H, 'atmo.skyview');
    this.sunDirection = uniform(new THREE.Vector3(0, 0.3, -1).normalize());
    this.eyeAltitude = uniform(0.002); // km
    this._build();
    this.baked = false;
  }

  /** TSL: transmittance from altitude r (km from centre) toward direction cosine mu */
  sampleTransmittance(r, mu) {
    return texture(this.transmittance, transmittanceUV(r, mu)).level(0).rgb;
  }

  _build() {
    const transTex = this.transmittance, msTex = this.multiScattering, skyTex = this.skyView;

    // ---------------------------------------------------------- transmittance
    this.transKernel = Fn(() => {
      const x = instanceIndex.mod(TRANS_W), y = instanceIndex.div(TRANS_W);
      const u = float(x).add(0.5).div(TRANS_W), v = float(y).add(0.5).div(TRANS_H);
      const H = sqrt(cTop.mul(cTop).sub(cBottom.mul(cBottom)));
      const rho = H.mul(v);
      const r = sqrt(rho.mul(rho).add(cBottom.mul(cBottom)));
      const dMin = cTop.sub(r), dMax = rho.add(H);
      const d = dMin.add(u.mul(dMax.sub(dMin)));
      const mu = select(d.equal(0), float(1), H.mul(H).sub(rho.mul(rho)).sub(d.mul(d)).div(r.mul(d).mul(2))).clamp(-1, 1);
      const len = raySphere(r, mu, cTop);
      const STEPS = 40;
      const dt = len.div(STEPS);
      const od = vec3(0).toVar();
      Loop(STEPS, ({ i }) => {
        const t = float(i).add(0.5).mul(dt);
        const h = sqrt(r.mul(r).add(t.mul(t)).add(r.mul(mu).mul(t).mul(2))).sub(cBottom);
        od.addAssign(extinctionAt(h).mul(dt));
      });
      textureStore(transTex, uvec2(x, y), vec4(exp(od.negate()), 1));
    })().compute(TRANS_W * TRANS_H, [64]);

    // -------------------------------------------------------- multi-scattering
    this.msKernel = Fn(() => {
      const x = instanceIndex.mod(MS_SIZE), y = instanceIndex.div(MS_SIZE);
      const u = float(x).add(0.5).div(MS_SIZE), v = float(y).add(0.5).div(MS_SIZE);
      const cosSun = u.mul(2).sub(1);
      const r = cBottom.add(v.mul(cTop.sub(cBottom))).add(0.01);
      const sunDir = vec3(0, cosSun, sqrt(max(cosSun.mul(cosSun).oneMinus(), 0)));
      const L2 = vec3(0).toVar(), fms = vec3(0).toVar();
      const SQRT = 8;
      Loop(SQRT * SQRT, ({ i }) => {
        const ii = float(i.mod(SQRT)).add(0.5).div(SQRT);
        const jj = float(i.div(SQRT)).add(0.5).div(SQRT);
        const theta = acos(jj.mul(2).sub(1));
        const phi = ii.mul(2 * Math.PI);
        const dir = vec3(sin(theta).mul(cos(phi)), cos(theta), sin(theta).mul(sin(phi)));
        const mu = dir.y;
        const tGround = raySphere(r, mu, cBottom);
        const tTop = raySphere(r, mu, cTop);
        const hitGround = tGround.greaterThan(0);
        const len = select(hitGround, tGround, tTop);
        const STEPS = 20;
        const dt = len.div(STEPS);
        const T = vec3(1).toVar();
        const lum = vec3(0).toVar(), fmsAcc = vec3(0).toVar();
        Loop(STEPS, ({ i: s }) => {
          const t = float(s).add(0.5).mul(dt);
          const p = vec3(0, r, 0).add(dir.mul(t));
          const pr = length(p);
          const h = pr.sub(cBottom);
          const sc = scatteringAt(h);
          const scat = sc.rayleigh.add(vec3(sc.mie));
          const stepT = exp(sc.extinction.mul(dt).negate());
          const up = p.div(pr);
          const muS = dot(up, sunDir);
          const sunT = texture(transTex, transmittanceUV(pr, muS)).level(0).rgb;
          const earthShadow = select(raySphere(pr, muS, cBottom).greaterThan(0), float(0), float(1));
          const phase = float(1 / (4 * Math.PI));
          const S = scat.mul(phase).mul(sunT).mul(earthShadow);
          const sInt = S.sub(S.mul(stepT)).div(sc.extinction.max(1e-7));
          lum.addAssign(T.mul(sInt));
          const fInt = scat.sub(scat.mul(stepT)).div(sc.extinction.max(1e-7));
          fmsAcc.addAssign(T.mul(fInt));
          T.mulAssign(stepT);
        });
        // ground bounce
        If(hitGround, () => {
          const p = vec3(0, r, 0).add(dir.mul(tGround));
          const up = normalize(p);
          const muS = dot(up, sunDir);
          const sunT = texture(transTex, transmittanceUV(float(ATMO.bottom), muS)).level(0).rgb;
          lum.addAssign(T.mul(sunT).mul(max(muS, 0)).mul(ATMO.groundAlbedo / Math.PI));
        });
        L2.addAssign(lum.div(SQRT * SQRT));
        fms.addAssign(fmsAcc.div(SQRT * SQRT));
      });
      const psi = L2.div(vec3(1).sub(fms).max(1e-3));
      textureStore(msTex, uvec2(x, y), vec4(psi, 1));
    })().compute(MS_SIZE * MS_SIZE, [64]);

    // ---------------------------------------------------------------- sky view
    const sunDirU = this.sunDirection, eyeAlt = this.eyeAltitude;
    this.skyKernel = Fn(() => {
      const x = instanceIndex.mod(SKY_W), y = instanceIndex.div(SKY_W);
      const u = float(x).add(0.5).div(SKY_W), v = float(y).add(0.5).div(SKY_H);
      const dir = skyViewDirection(vec2(u, v), sunDirU);
      const L = integrateScattering(cBottom.add(eyeAlt), dir, sunDirU, 32, transTex, msTex);
      textureStore(skyTex, uvec2(x, y), vec4(L, 1));
    })().compute(SKY_W * SKY_H, [64]);
  }

  update() {
    if (!this.baked) {
      this.renderer.compute(this.transKernel);
      this.renderer.compute(this.msKernel);
      this.baked = true;
    }
    this.renderer.compute(this.skyKernel);
  }

  /** TSL: sky radiance (sun illuminance 1) along a world direction, no sun disk */
  skyRadiance(dir) {
    return texture(this.skyView, skyViewUV(dir, this.sunDirection)).level(0).rgb;
  }
}

// sky-view parameterisation: u = azimuth relative to the sun, v = latitude
// with the horizon-concentrating sqrt mapping from Hillaire
export const skyViewUV = Fn(([dir, sunDir]) => {
  const lat = atan(dir.y, length(dir.xz));
  const v = float(0.5).add(float(0.5).mul(sign(lat)).mul(sqrt(abs(lat).div(Math.PI / 2))));
  const az = atan(dir.z, dir.x).sub(atan(sunDir.z, sunDir.x));
  const u = fract(az.div(2 * Math.PI).add(1));
  return vec2(u, clamp(v, 0.5 / SKY_H, 1 - 0.5 / SKY_H));
});

const skyViewDirection = Fn(([uv, sunDir]) => {
  const vc = uv.y.mul(2).sub(1);
  const lat = sign(vc).mul(vc.mul(vc)).mul(Math.PI / 2);
  const az = uv.x.mul(2 * Math.PI).add(atan(sunDir.z, sunDir.x));
  const cl = cos(lat);
  return vec3(cl.mul(cos(az)), sin(lat), cl.mul(sin(az)));
});

// single + multiple scattering along a view ray (Hillaire eq. 1-11)
function integrateScattering(r0, dir, sunDir, STEPS, transTex, msTex) {
  const mu = dir.y;
  const tGround = raySphere(r0, mu, cBottom);
  const tTop = raySphere(r0, mu, cTop);
  const len = select(tGround.greaterThan(0), tGround, tTop).min(400);
  const cosTheta = dot(dir, sunDir);
  const phaseR = rayleighPhase(cosTheta);
  const phaseM = csPhase(cosTheta, ATMO.mieG);
  const L = vec3(0).toVar(), T = vec3(1).toVar();
  const tPrev = float(0).toVar();
  Loop(STEPS, ({ i }) => {
    // quadratic step distribution: dense near the eye
    const t = float(i).add(0.3).div(STEPS).pow(2).mul(len).toVar();
    const dt = t.sub(tPrev).toVar(); // must be captured before tPrev changes
    tPrev.assign(t);
    const p = vec3(0, r0, 0).add(dir.mul(t));
    const pr = length(p);
    const h = pr.sub(cBottom);
    const sc = scatteringAt(h);
    const up = p.div(pr);
    const muS = dot(up, sunDir);
    const sunT = texture(transTex, transmittanceUV(pr, muS)).level(0).rgb;
    const earthShadow = select(raySphere(pr, muS, cBottom).greaterThan(0), float(0), float(1));
    const msUV = vec2(muS.mul(0.5).add(0.5), h.div(ATMO.top - ATMO.bottom)).clamp(0.5 / MS_SIZE, 1 - 0.5 / MS_SIZE);
    const psi = texture(msTex, msUV).level(0).rgb;
    const S = sc.rayleigh.mul(phaseR.mul(sunT).mul(earthShadow).add(psi))
      .add(vec3(sc.mie).mul(phaseM.mul(sunT).mul(earthShadow).add(psi)));
    const stepT = exp(sc.extinction.mul(dt).negate());
    L.addAssign(T.mul(S.sub(S.mul(stepT)).div(sc.extinction.max(1e-7))));
    T.mulAssign(stepT);
  });
  return L;
}

// ------------------------------------------------------------------ CPU side
// Enough of the model to light the scene: sun transmittance at the eye and a
// coarse sky irradiance from a few dozen rays.

function cpuExtinction(h) {
  const rd = Math.exp(-h / ATMO.rayleighScale), md = Math.exp(-h / ATMO.mieScale);
  const od = Math.max(0, 1 - Math.abs(h - 25) / 15);
  return ATMO.rayleighScattering.map((r, i) => r * rd + ATMO.mieExtinction * md + ATMO.ozoneAbsorption[i] * od);
}

function cpuRaySphere(r, mu, R) {
  const disc = r * r * (mu * mu - 1) + R * R;
  if (disc < 0) return -1;
  const s = Math.sqrt(disc);
  const t0 = -r * mu - s, t1 = -r * mu + s;
  return t0 > 0 ? t0 : t1;
}

export function cpuTransmittance(r, mu, steps = 48) {
  if (cpuRaySphere(r, mu, ATMO.bottom) > 0) return [0, 0, 0];
  const len = cpuRaySphere(r, mu, ATMO.top);
  const dt = len / steps;
  const od = [0, 0, 0];
  for (let i = 0; i < steps; i++) {
    const t = (i + 0.5) * dt;
    const h = Math.sqrt(r * r + t * t + 2 * r * mu * t) - ATMO.bottom;
    const e = cpuExtinction(h);
    od[0] += e[0] * dt; od[1] += e[1] * dt; od[2] += e[2] * dt;
  }
  return od.map((v) => Math.exp(-v));
}

/** Sun colour at the eye for a sun elevation (radians), including a soft horizon fade. */
export function sunTransmittanceAt(elevation, eyeAltKm = 0.002) {
  const r = ATMO.bottom + eyeAltKm;
  // average over the sun disk's vertical extent so it fades smoothly at sunset
  const out = [0, 0, 0];
  const n = 5;
  for (let i = 0; i < n; i++) {
    const e = elevation + ((i + 0.5) / n - 0.5) * 0.0093;
    const T = cpuTransmittance(r, Math.sin(e));
    out[0] += T[0] / n; out[1] += T[1] / n; out[2] += T[2] / n;
  }
  return out;
}
