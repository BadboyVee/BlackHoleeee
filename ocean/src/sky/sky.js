// Sky system: atmosphere LUTs + a cached sky/cloud panorama.
//
// Clouds sit kilometres away, so they are raymarched into a 4096×1024
// hemispherical panorama instead of the screen. Each frame refreshes 1/32 of
// the texels (spread over the image) and blends them into the history, so the
// result is smooth and noise-free, costs a fixed ~130k rays per frame, and is
// shared by the background, the water reflections and the environment light.

import * as THREE from 'three/webgpu';
import {
  Fn, uniform, vec2, vec3, vec4, float, int, uint, sqrt, max, min, clamp, exp, abs, dot, normalize,
  length, mix, cos, sin, asin, atan, pow, texture, texture3D, uv, Loop, If, Break, Discard, select,
  floor, fract, smoothstep, step, screenCoordinate, fwidth, positionWorldDirection, hash, mul, sign,
} from 'three/tsl';
import { Atmosphere, ATMO, raySphere, transmittanceUV, csPhase, hgPhase, sunTransmittanceAt, cpuTransmittance } from './atmosphere.js';
import { createCloudNoise, sampleAtlas } from './noise3d.js';
import { hash21 } from '../render/tslnoise.js';

export let PANO_W = 4096, PANO_H = 1024;
// panorama texels are refreshed in an interleaved PX x PY pattern, one cell
// of it per frame (tests on software GPUs split the work more finely)
let PX = 8, PY = 4, PHASES = 32;

// ------------------------------------------------------------------ mapping
export const panoDirection = (u, v) => {
  const el = v.mul(v).mul(Math.PI / 2);
  const az = u.mul(2 * Math.PI);
  const ce = cos(el);
  return vec3(ce.mul(sin(az)), sin(el), ce.mul(cos(az)).negate());
};

export const panoUV = (dir) => {
  const el = asin(clamp(dir.y, 0, 1));
  const v = sqrt(el.div(Math.PI / 2));
  const u = fract(atan(dir.x, dir.z.negate()).div(2 * Math.PI).add(1));
  return vec2(u, v);
};

const remap = (v, a, b, c, d) => c.add(v.sub(a).div(b.sub(a)).mul(d.sub(c)));
export const hash12 = (p) => fract(sin(dot(p, vec2(12.9898, 78.233))).mul(43758.5453));

export class Sky {
  constructor(renderer, { test = false, panoWidth = 4096 } = {}) {
    this.renderer = renderer;
    PANO_W = panoWidth; PANO_H = panoWidth / 4;
    if (test && panoWidth > 2048) { PX = 16; PY = 8; } else { PX = 8; PY = 4; }
    PHASES = PX * PY;
    this.phaseBits = Math.log2(PHASES);
    this.atmo = new Atmosphere(renderer);
    this.test = test;

    // light & weather state
    this.sunDirection = this.atmo.sunDirection;          // main light for the atmosphere
    this.lightIlluminance = uniform(12);                  // scene units
    this.lightColor = uniform(new THREE.Color(1, 1, 1));  // transmittance-tinted at eye (CPU)
    this.sunDiskDirection = uniform(new THREE.Vector3(0, 0.3, -1));
    this.moonDirection = uniform(new THREE.Vector3(0, 0.3, 1));
    this.nightFactor = uniform(0);
    this.sunDiskIntensity = uniform(1);
    this.coverage = uniform(0.5);
    this.cloudBase = uniform(1.35);   // km
    this.cloudTop = uniform(2.5);     // km
    this.cloudDensity = uniform(40);  // extinction per km at density 1
    this.cirrusAmount = uniform(0.55);
    this.windOffset = uniform(new THREE.Vector2(0, 0)); // km
    this.eyeXZ = uniform(new THREE.Vector2(0, 0));       // km
    this.phase = uniform(0);
    this.cloudsOn = uniform(1).toBool ? uniform(true, 'bool') : uniform(1);
    this.frame = 0;
    this.time = uniform(0);
    this.frameU = uniform(0);
    this.skyIrradiance = new THREE.Color();
    this.windKmh = 18;

    this.panorama = new THREE.RenderTarget(PANO_W, PANO_H, {
      type: THREE.HalfFloatType, depthBuffer: false, generateMipmaps: true,
      minFilter: THREE.LinearMipmapLinearFilter, magFilter: THREE.LinearFilter,
      wrapS: THREE.RepeatWrapping, wrapT: THREE.ClampToEdgeWrapping,
    });
    this.panorama.texture.name = 'sky.panorama';
    this.warm = 0;
    this.warmRate = test ? (PANO_W > 2048 ? 2 : 2) : 4;
  }

  async init() {
    this.noise = await createCloudNoise(this.renderer, { shapeSize: this.test ? 64 : 128 });
    this._buildPanoramaPass();
    this._buildEnvironmentPass();
  }

  // Equirectangular environment for image-based lighting (PMREM'd by three).
  // Upper hemisphere = sky + clouds from the panorama; lower hemisphere = a
  // sea/sand bounce so shaded surfaces pick up warm reflected light.
  _buildEnvironmentPass() {
    const W = 256, H = 128;
    this.envTarget = new THREE.RenderTarget(W, H, { type: THREE.HalfFloatType, depthBuffer: false, generateMipmaps: false });
    this.envTarget.texture.mapping = THREE.EquirectangularReflectionMapping;
    this.envTarget.texture.name = 'sky.environment';
    const mat = new THREE.NodeMaterial();
    mat.depthTest = false; mat.depthWrite = false;
    mat.fragmentNode = Fn(() => {
      const p = uv();
      // three's equirect convention: u -> atan(dir.z, dir.x), v -> asin(dir.y)
      const phi = p.x.sub(0.5).mul(2 * Math.PI);
      const theta = p.y.sub(0.5).mul(Math.PI);
      const dir = vec3(cos(theta).mul(cos(phi)), sin(theta), cos(theta).mul(sin(phi))).toVar();
      const up = this.sample(normalize(vec3(dir.x, max(dir.y, 0.0), dir.z)), float(2)).rgb;
      const horizon = this.sample(normalize(vec3(dir.x, 0.02, dir.z)), float(3)).rgb;
      const E = this.lightIlluminance;
      const sunUp = max(this.sunDirection.y, 0);
      const ground = horizon.mul(0.18).add(vec3(0.42, 0.36, 0.26).mul(sunUp.mul(E).mul(0.035)));
      return vec4(mix(ground, up, smoothstep(-0.08, 0.02, dir.y)), 1);
    })();
    this.envQuad = new THREE.QuadMesh(mat);
    this.envAge = 1e9;
  }

  updateEnvironment(force = false) {
    this.envAge++;
    if (!force && this.envAge < 90) return false;
    this.envAge = 0;
    const renderer = this.renderer;
    const prev = renderer.getRenderTarget();
    renderer.setRenderTarget(this.envTarget);
    this.envQuad.render(renderer);
    renderer.setRenderTarget(prev);
    this.envTarget.texture.needsPMREMUpdate = true;
    return true;
  }

  // ------------------------------------------------------------ cloud model
  // Cumulus fields (Schneider's Nubis recipe, tuned for broad, low clouds):
  //  weather map (40 km tile)  -> coverage + local cloud-top height
  //  height gradient           -> flat condensation base, rounded tops
  //  Perlin-Worley shape (~1.8 km cells, squashed vertically), eroded by Worley fBm
  //  Worley detail (~30-200 m) -> smooth wispy bases, cauliflower tops
  _cloudDensity(pWorld, h, detail) {
    // pWorld: km (x,z horizontal, y altitude above ground)
    const { shape, detail: detailTex, weather } = this.noise;
    const base = this.cloudBase, top = this.cloudTop;
    const wind = vec3(this.windOffset.x, 0, this.windOffset.y);
    const w = texture(weather, pWorld.xz.add(this.windOffset).div(40)).level(0);
    const cov = this._coverage(w.r);
    const topF = mix(0.55, 1.0, w.g);
    const hf = clamp(h.sub(base).div(top.sub(base)), 0, 1);
    const ht = hf.div(topF);
    // flat condensation base; the threshold rises with height so only the
    // strongest cores reach the local top (domed, separate towers)
    const grad = smoothstep(0.0, 0.05, hf).mul(smoothstep(1.0, 0.12, ht));
    // ~1.8 km cells: broad cumulus (a squashed vertical period keeps domes
    // inside the thin layer; much wider cells merge into stratocumulus slabs)
    const s = sampleAtlas(shape, this.noise.shapeInfo, pWorld.add(wind).mul(vec3(1, 1.4, 1)).div(7.5));
    const lowFbm = s.g.mul(0.625).add(s.b.mul(0.25)).add(s.a.mul(0.125));
    // the eroded Perlin-Worley only spans ~0.72..0.92 (measured with
    // debugNoiseStats); stretch it to 0..1 so coverage has something to cut
    const baseN = clamp(remap(s.r, lowFbm.sub(1), float(1), float(0), float(1)).sub(0.72).div(0.21), 0, 1);
    let dens = clamp(remap(baseN, float(1).sub(cov.mul(grad)), float(1), float(0), float(1)), 0, 1);
    if (detail) {
      const d = sampleAtlas(detailTex, this.noise.detailInfo, pWorld.add(wind.mul(1.3)).div(0.42));
      const dF = clamp(d.r.mul(0.625).add(d.g.mul(0.25)).add(d.b.mul(0.125)).sub(0.28).div(0.42), 0, 1);
      // wispy (inverted billows) under the base, cauliflower higher up
      const dMod = mix(dF, float(1).sub(dF), smoothstep(0.06, 0.3, ht));
      const erosion = mix(0.16, 0.58, smoothstep(0.05, 0.7, ht));
      dens = clamp(remap(dens, dMod.mul(erosion), float(1), float(0), float(1)), 0, 1);
    }
    // real cumulus are optically thick right up to a crisp edge: compress the
    // km-scale density ramp of the base shape (and the eroded detail with it)
    // into a short transition instead of a soft, marshmallow falloff
    return smoothstep(0.0, 0.3, dens).mul(smoothstep(0.0, 0.5, cov).mul(0.6).add(0.4));
  }

  // weather-map value -> local cloud coverage. Even in the cloudiest parts of
  // a field it stays below ~0.65 so cumulus remain separate cells instead of
  // merging into a stratocumulus deck; the global `coverage` sets how much of
  // the sky holds clouds.
  _coverage(wr) {
    const field = smoothstep(0.2, 0.8, wr);
    return clamp(this.coverage.mul(mix(0.15, 1.6, field)), 0, 0.65);
  }

  _buildPanoramaPass() {
    const atmo = this.atmo;
    const mat = new THREE.NodeMaterial();
    mat.name = 'sky.panorama';
    mat.depthTest = false; mat.depthWrite = false;
    mat.blending = THREE.CustomBlending;
    mat.blendSrc = THREE.ConstantColorFactor; mat.blendDst = THREE.OneMinusConstantColorFactor;
    mat.blendSrcAlpha = THREE.ConstantColorFactor; mat.blendDstAlpha = THREE.OneMinusConstantColorFactor;
    mat.blendColor = new THREE.Color(1, 1, 1); mat.blendAlpha = 1;
    this.panoMaterial = mat;

    const Rb = ATMO.bottom;
    mat.fragmentNode = Fn(() => {
      const puv = uv();
      const pix = floor(puv.mul(vec2(PANO_W, PANO_H)));
      const cell = pix.x.mod(PX).add(pix.y.mod(PY).mul(PX));
      const out = vec4(0).toVar();
      If(cell.equal(this.phase), () => {
      const dir = panoDirection(puv.x, puv.y).toVar();
      const sunDir = this.sunDirection;
      const E = this.lightIlluminance;
      const sky = atmo.skyRadiance(dir).mul(E).toVar();
      const r0 = float(Rb + 0.002);
      const mu = dir.y;
      const cosT = dot(dir, sunDir).toVar();   // (read in the cirrus branch and the march)

      // ------------------------------------------------ cirrus (2D, ~9 km)
      const tC = raySphere(r0, mu, float(Rb + 9.0));
      If(tC.greaterThan(0).and(this.cirrusAmount.greaterThan(0.001)), () => {
        const pc = this.eyeXZ.add(dir.xz.mul(tC));
        const field = texture(this.noise.weather, pc.add(this.windOffset.mul(0.6)).div(90)).level(0).b;
        const fib = texture(this.noise.cirrus, pc.add(this.windOffset.mul(1.4)).div(34)).level(0).r;
        const fib2 = texture(this.noise.cirrus, pc.mul(vec2(1.0, 1.0)).add(vec2(17.3, 5.1)).div(13)).level(0).r;
        const dens = clamp(fib.mul(0.75).add(fib2.mul(0.35)).mul(smoothstep(0.25, 0.75, field)).mul(this.cirrusAmount), 0, 1);
        const sunT = atmo.sampleTransmittance(float(Rb + 9.0), sunDir.y);
        const phase = hgPhase(cosT, 0.6).mul(0.7).add(hgPhase(cosT, -0.1).mul(0.3));
        const lit = sunT.mul(E).mul(phase).mul(3.2).add(sky.mul(0.9));
        const haze = exp(tC.mul(-0.012));
        const a = dens.mul(0.55).mul(haze);
        sky.assign(mix(sky, lit, a));
      });

      // ------------------------------------------------ cumulus raymarch
      // adaptive: long strides through clear air on the cheap shape, back up
      // and walk in with short strides once the shape says "cloud"
      const T = float(1).toVar();
      const L = vec3(0).toVar();
      const base = this.cloudBase, top = this.cloudTop;
      const tIn = raySphere(r0, mu, base.add(Rb)).toVar();
      const tOut = raySphere(r0, mu, top.add(Rb));
      const tDist = float(0).toVar();
      const t1 = min(tOut, tIn.add(30)).toVar();
      If(mu.greaterThan(-0.01).and(tIn.greaterThan(0)).and(tIn.lessThan(90)).and(this.cloudsOn), () => {
        // loop invariants must be real variables: TSL emits a shared
        // expression at its first use, which would be inside the march
        const dtBig = clamp(t1.sub(tIn).div(56), 0.025, 0.4).toVar();
        const dtSmall = max(dtBig.mul(0.33), 0.012).toVar();
        const jitter = hash21(pix.add(vec2(this.frameU.mod(64).mul(4099), this.frameU.mod(61).mul(577)))).toVar();
        // sun colour at mid-cloud altitude, sky ambient from the LUT
        const midR = base.add(top).mul(0.5).add(Rb);
        const sunC = atmo.sampleTransmittance(midR, sunDir.y).mul(E).toVar();
        const ambTop = atmo.skyRadiance(vec3(0, 1, 0)).mul(E).mul(2.6).add(atmo.skyRadiance(normalize(vec3(sunDir.x, 0.15, sunDir.z))).mul(E).mul(1.2)).toVar();
        // bases see the horizon sky and light bounced off the sea: grey, not black
        const ambBottom = ambTop.mul(0.3).add(sunC.mul(max(sunDir.y, 0)).mul(0.04)).toVar();
        const phaseF = hgPhase(cosT, 0.75).toVar(), phaseB = hgPhase(cosT, -0.25).toVar(), phaseM = hgPhase(cosT, 0.3).toVar();
        const sunV = vec3(sunDir.x, max(sunDir.y, 0.03), sunDir.z).normalize().toVar();
        const t = tIn.add(dtBig.mul(jitter)).toVar();
        const inside = int(0).toVar();
        Loop(170, () => {
          If(T.lessThan(0.01).or(t.greaterThan(t1)), () => { Break(); });
          const p = vec3(0, r0, 0).add(dir.mul(t));
          const pr = length(p);
          const h = pr.sub(Rb);
          const pw = vec3(this.eyeXZ.x.add(p.x), h, this.eyeXZ.y.add(p.z)).toVar();
          If(inside.greaterThan(0), () => {
            const dens = this._cloudDensity(pw, h, true).toVar();
            If(dens.greaterThan(0.002), () => {
              // light march toward the sun; the first two taps see the
              // detail so every billow shades itself
              const od = float(0).toVar();
              const stepsL = [0.025, 0.05, 0.1, 0.2, 0.4];
              let acc = 0;
              stepsL.forEach((sl, k) => {
                acc += sl;
                const q = pw.add(sunV.mul(acc - sl * 0.5));
                od.addAssign(this._cloudDensity(q, q.y, k < 2).mul(sl));
              });
              const sigma = this.cloudDensity;
              const tau = od.mul(sigma);
              // multiple-scattering octaves (Wrenninge) with dual-lobe phase
              const ms = exp(tau.negate()).mul(phaseF.mul(0.7).add(phaseB.mul(0.3)))
                .add(exp(tau.mul(-0.35)).mul(phaseM).mul(0.32))
                .add(exp(tau.mul(-0.12)).mul(0.05 / (4 * Math.PI) * 4.0));
              // "powder": in-scattering needs some cloud behind it to build
              // up, so thinly covered sunlit billows are darker than their
              // cores - this is what carves cauliflower tops (hidden when
              // looking into the sun, where forward scattering dominates)
              const powder = mix(float(1).sub(exp(tau.mul(-2.0))).mul(0.75).add(0.25), float(1), smoothstep(-0.2, 0.9, cosT));
              const hf = clamp(h.sub(base).div(top.sub(base)), 0, 1);
              const amb = mix(ambBottom, ambTop, hf.pow(0.6)).mul(0.9);
              const Lsample = sunC.mul(ms).mul(powder).mul(4 * Math.PI * 0.25).add(amb.mul(0.26));
              const Ts = exp(dens.mul(sigma).mul(dtSmall).negate());
              L.addAssign(Lsample.mul(T).mul(float(1).sub(Ts)));
              tDist.addAssign(t.mul(T.sub(T.mul(Ts))));
              T.mulAssign(Ts);
              inside.assign(10);
            }).Else(() => { inside.subAssign(1); });
            t.addAssign(dtSmall);
          }).Else(() => {
            If(this._cloudDensity(pw, h, false).greaterThan(0.0), () => {
              t.assign(max(t.sub(dtBig), tIn));
              inside.assign(10);
            }).Else(() => { t.addAssign(dtBig); });
          });
        });
        // aerial perspective between the eye and the cloud
        const cover = float(1).sub(T);
        const dMean = select(cover.greaterThan(0.001), tDist.div(cover.max(1e-4)), t1);
        const Tair = exp(dMean.mul(-0.045));
        sky.assign(sky.mul(float(1).sub(cover.mul(Tair))).add(L.mul(Tair)));
        T.assign(mix(float(1), T, Tair));
      });
      out.assign(vec4(sky, T));
      }).Else(() => { Discard(); });
      return out;
    })();
    this.panoQuad = new THREE.QuadMesh(mat);
  }

  /** Called when sun elevation/azimuth change. elevation/azimuth in degrees. */
  setSun(elevationDeg, azimuthDeg) {
    const el = THREE.MathUtils.degToRad(elevationDeg), az = THREE.MathUtils.degToRad(azimuthDeg);
    const sun = new THREE.Vector3(Math.sin(az) * Math.cos(el), Math.sin(el), -Math.cos(az) * Math.cos(el));
    this.sunDiskDirection.value.copy(sun);
    // moon roughly opposite, a little higher so it rises as the sun sets
    const moonEl = THREE.MathUtils.degToRad(Math.max(8, 28 - elevationDeg * 0.5));
    const moonAz = az + Math.PI * 0.92;
    const moon = new THREE.Vector3(Math.sin(moonAz) * Math.cos(moonEl), Math.sin(moonEl), -Math.cos(moonAz) * Math.cos(moonEl));
    this.moonDirection.value.copy(moon);
    const night = THREE.MathUtils.smoothstep(-elevationDeg, 3, 10);
    this.nightFactor.value = night;
    const useMoon = elevationDeg < -4;
    const main = useMoon ? moon : sun;
    this.sunDirection.value.copy(main);
    this.mainIsMoon = useMoon;
    // scene light colour from the atmosphere transmittance
    const T = sunTransmittanceAt(Math.asin(main.y));
    const E = useMoon ? 0.035 : 12;
    this.lightIlluminance.value = E;
    const fade = useMoon ? THREE.MathUtils.smoothstep(elevationDeg, -12, -4) * 0 + THREE.MathUtils.smoothstep(-elevationDeg, 4, 9) : THREE.MathUtils.smoothstep(elevationDeg, -2.5, 1.5);
    this.lightFade = fade;
    this.lightColor.value.setRGB(T[0], T[1], T[2]);
    if (useMoon) this.lightColor.value.multiply(new THREE.Color(0.75, 0.85, 1.1));
    this.mainLightDirection = main.clone();
    this.sunElevation = elevationDeg;
    this.sunVector = sun;
    this._estimateIrradiance();
  }

  // crude CPU sky irradiance for the hemisphere/ambient light, from the same model
  _estimateIrradiance() {
    const main = this.sunDirection.value;
    const E = this.lightIlluminance.value;
    const r = ATMO.bottom + 0.002;
    const col = [0, 0, 0];
    const n = 24;
    // integrate single scattering over a coarse set of sky directions (cosine weighted)
    for (let i = 0; i < n; i++) {
      const u1 = (i + 0.5) / n;
      const cosT = Math.sqrt(1 - u1), sinT = Math.sqrt(u1);
      const phi = i * 2.399963;
      const d = new THREE.Vector3(sinT * Math.cos(phi), cosT, sinT * Math.sin(phi));
      const c = d.dot(main);
      const phaseR = 3 / (16 * Math.PI) * (1 + c * c);
      const g = ATMO.mieG, g2 = g * g;
      const phaseM = (3 / (8 * Math.PI)) * (1 - g2) / (2 + g2) * (1 + c * c) / Math.pow(Math.max(1e-4, 1 + g2 - 2 * g * c), 1.5);
      // march 12 steps to 30 km
      const steps = 12;
      let T = [1, 1, 1];
      const Lr = [0, 0, 0];
      for (let s = 0; s < steps; s++) {
        const t = ((s + 0.5) / steps) ** 2 * 40;
        const dt = (2 * (s + 0.5) / steps / steps) * 40;
        const h = t * d.y + 0.002;
        const rd = Math.exp(-h / ATMO.rayleighScale), md = Math.exp(-h / ATMO.mieScale);
        const sunT = cpuTransmittance(ATMO.bottom + h, main.y, 16);
        for (let k = 0; k < 3; k++) {
          const sr = ATMO.rayleighScattering[k] * rd, sm = ATMO.mieScattering * md;
          const ext = sr + ATMO.mieExtinction * md;
          Lr[k] += T[k] * (sr * phaseR + sm * phaseM) * sunT[k] * dt * 1.6; // 1.6 ~ multi-scatter boost
          T[k] *= Math.exp(-ext * dt);
        }
      }
      for (let k = 0; k < 3; k++) col[k] += Lr[k] * Math.PI / n;
    }
    this.skyIrradiance.setRGB(col[0] * E, col[1] * E, col[2] * E);
  }

  update(dt, camera, time) {
    this.time.value = time;
    // clouds drift with the wind
    const w = this.windKmh / 3600; // km/s
    this.windOffset.value.x += w * dt * 0.8;
    this.windOffset.value.y += w * dt * 0.35;
    this.eyeXZ.value.set(camera.position.x / 1000, camera.position.z / 1000);
    // a big jump (teleport, fast flight) re-renders the whole panorama quickly
    // instead of letting the parallax error fade out over several cycles
    if (!this.lastWarmEye) this.lastWarmEye = camera.position.clone();
    if (camera.position.distanceTo(this.lastWarmEye) > 60) { this.warm = 0; this.lastWarmEye.copy(camera.position); }
    this.atmo.update();
    if (this.debugSkip && this.debugSkip.includes('pano')) return;
    // while loading, refresh several phases per frame so the sky starts
    // complete without one huge submission (GPU watchdogs)
    const warming = this.warm < PHASES / this.warmRate;
    const passes = warming ? this.warmRate : 1;
    const renderer = this.renderer;
    const prevTarget = renderer.getRenderTarget();
    const prevClear = renderer.autoClear;
    renderer.autoClear = false; // the panorama accumulates: never clear it
    renderer.setRenderTarget(this.panorama);
    for (let i = 0; i < passes; i++) {
      this.phase.value = bitReverse(this.frame % PHASES, this.phaseBits);
      this.frameU.value = Math.floor(this.frame / PHASES);
      this.panoMaterial.blendColor.setScalar(warming ? 1 : 0.4);
      this.panoQuad.render(renderer);
      this.frame++;
    }
    renderer.setRenderTarget(prevTarget);
    renderer.autoClear = prevClear;
    this.warm++;
    this._updateShadowMap(camera);
  }

  /** TSL: sky (+clouds) radiance along a direction, optional blur level */
  sample(dir, level = null) {
    const t = texture(this.panorama.texture, panoUV(dir));
    return level ? t.level(level) : t;
  }

  /** TSL: sharp (Catmull-Rom, 9 bilinear taps) panorama lookup for the background */
  sampleSharp(dir) {
    const size = vec2(PANO_W, PANO_H);
    const uvp = panoUV(dir);
    const sp = uvp.mul(size);
    const t1 = floor(sp.sub(0.5)).add(0.5);
    const f = sp.sub(t1);
    const w0 = f.mul(f.mul(f.mul(-0.5).add(1.0)).sub(0.5));
    const w1 = f.mul(f).mul(f.mul(1.5).sub(2.5)).add(1.0);
    const w2 = f.mul(f.mul(f.mul(-1.5).add(2.0)).add(0.5));
    const w3 = f.mul(f).mul(f.mul(0.5).sub(0.5));
    const w12 = w1.add(w2);
    const o12 = w2.div(w12);
    const p0 = t1.sub(1).div(size), p3 = t1.add(2).div(size), p12 = t1.add(o12).div(size);
    const tap = (x, y) => texture(this.panorama.texture, vec2(x, clamp(y, 0.5 / PANO_H, 1 - 0.5 / PANO_H))).level(0);
    const r = tap(p0.x, p0.y).mul(w0.x.mul(w0.y))
      .add(tap(p12.x, p0.y).mul(w12.x.mul(w0.y)))
      .add(tap(p3.x, p0.y).mul(w3.x.mul(w0.y)))
      .add(tap(p0.x, p12.y).mul(w0.x.mul(w12.y)))
      .add(tap(p12.x, p12.y).mul(w12.x.mul(w12.y)))
      .add(tap(p3.x, p12.y).mul(w3.x.mul(w12.y)))
      .add(tap(p0.x, p3.y).mul(w0.x.mul(w3.y)))
      .add(tap(p12.x, p3.y).mul(w12.x.mul(w3.y)))
      .add(tap(p3.x, p3.y).mul(w3.x.mul(w3.y)));
    return max(r, vec4(0));
  }

  /** Full background: panorama + sun disk + moon + stars */
  backgroundNode() {
    return Fn(() => {
      const dir = normalize(positionWorldDirection).toVar();
      // explicit LOD: implicit derivatives jump across the background mesh's
      // triangles and the u-wrap, which showed up as faint seams
      const s = this.sampleSharp(dir).toVar();
      const col = s.rgb.toVar();
      const Tcloud = s.a;
      // sun disk with limb darkening (real angular radius 0.2666 deg)
      const sd = this.sunDiskDirection;
      const cosA = dot(dir, sd);
      const r = sqrt(max(float(1).sub(cosA.mul(cosA)), 0)).div(0.00465);
      const disk = smoothstep(1.0, 0.94, r).mul(cosA.greaterThan(0).select(1, 0));
      const limb = pow(max(float(1).sub(r.mul(r)), 0.0), 0.25).mul(0.6).add(0.4);
      const sunT = this.atmo.sampleTransmittance(float(ATMO.bottom + 0.002), sd.y);
      col.addAssign(sunT.mul(disk).mul(limb).mul(Tcloud).mul(this.sunDiskIntensity).mul(9000));
      // moon: lit hemisphere facing the sun, mottled maria
      const md = this.moonDirection;
      const cosM = dot(dir, md);
      const rm = sqrt(max(float(1).sub(cosM.mul(cosM)), 0)).div(0.0049);
      const moonMask = smoothstep(1.0, 0.9, rm).mul(cosM.greaterThan(0).select(1, 0));
      const right = normalize(vec3(md.z.negate(), 0, md.x));
      const up = normalize(right.cross(md).negate());
      const mx = dot(dir, right).div(0.0049), my = dot(dir, up).div(0.0049);
      const mz = sqrt(max(float(1).sub(mx.mul(mx)).sub(my.mul(my)), 0));
      const n = right.mul(mx).add(up.mul(my)).sub(md.mul(mz));
      const lit = max(dot(n, this.sunDiskDirection), 0).mul(0.9).add(0.03);
      const maria = hash12(floor(dir.xy.mul(900))).mul(0.25).add(0.75);
      col.addAssign(vec3(0.9, 0.92, 1.0).mul(moonMask).mul(lit).mul(maria).mul(Tcloud).mul(this.nightFactor).mul(1.6));
      // stars
      const sp = dir.mul(520);
      const cellId = floor(sp);
      const hv = hash12(cellId.xy.add(cellId.z.mul(37.1)));
      const starOn = step(0.9965, hv);
      const f = fract(sp).sub(0.5);
      const sparkle = smoothstep(0.22, 0.0, length(f)).mul(starOn);
      const tw = sin(this.time.mul(hv.mul(40).add(3)).add(hv.mul(60))).mul(0.25).add(0.75);
      const starCol = mix(vec3(0.75, 0.82, 1.0), vec3(1.0, 0.9, 0.75), fract(hv.mul(113.1)));
      col.addAssign(starCol.mul(sparkle).mul(tw).mul(Tcloud).mul(this.nightFactor).mul(smoothstep(-0.02, 0.15, dir.y)).mul(0.35));
      return col;
    })();
  }

  /** debug: percentiles of the cloud noise channels at random points */
  async debugNoiseStats(n = 16384) {
    const { instancedArray, instanceIndex: ii } = await import('three/tsl');
    const out = instancedArray(n, 'vec4');
    const k = Fn(() => {
      const i = float(ii);
      const p = vec3(fract(i.mul(0.7548776662)), fract(i.mul(0.5698402910)), fract(i.mul(0.3183098862).add(0.5)));
      const s = sampleAtlas(this.noise.shape, this.noise.shapeInfo, p);
      const lowFbm = s.g.mul(0.625).add(s.b.mul(0.25)).add(s.a.mul(0.125));
      const baseN = clamp(remap(s.r, lowFbm.sub(1), float(1), float(0), float(1)), 0, 1);
      const d = sampleAtlas(this.noise.detail, this.noise.detailInfo, p.mul(3.1));
      const dF = d.r.mul(0.625).add(d.g.mul(0.25)).add(d.b.mul(0.125));
      out.element(ii).assign(vec4(s.r, lowFbm, baseN, dF));
    })().compute(n, [64]);
    this.renderer.compute(k);
    const buf = new Float32Array(await this.renderer.getArrayBufferAsync(out.value));
    const res = {};
    ['r', 'lowFbm', 'baseN', 'detail'].forEach((name, c) => {
      const v = []; for (let i = 0; i < n; i++) v.push(buf[i * 4 + c]);
      v.sort((a, b) => a - b);
      res[name] = [0.01, 0.1, 0.25, 0.5, 0.75, 0.9, 0.99].map((q) => +v[Math.floor(q * (n - 1))].toFixed(3));
    });
    return res;
  }

  // Cloud shadow map: sun transmittance through the cloud layer for a 24 km
  // square of ground around the eye, marched from the real density field and
  // refreshed in slices. Surfaces look it up with one texture fetch.
  _buildShadowMap() {
    const S = this.test ? 256 : 512;
    this.shadowSize = 24;                        // km
    this.shadowOrigin = uniform(new THREE.Vector2(-12, -12));
    this.shadowSlice = uniform(0);
    this.shadowTarget = new THREE.RenderTarget(S, S, {
      type: THREE.HalfFloatType, depthBuffer: false, generateMipmaps: false,
      minFilter: THREE.LinearFilter, magFilter: THREE.LinearFilter,
    });
    this.shadowTarget.texture.name = 'sky.cloudShadow';
    const mat = new THREE.NodeMaterial();
    mat.depthTest = false; mat.depthWrite = false;
    const origin = this.shadowOrigin, size = this.shadowSize;
    mat.fragmentNode = Fn(() => {
      const puv = uv();
      const out = vec4(1).toVar();
      const row = floor(puv.y.mul(S)).mod(4);
      If(row.equal(this.shadowSlice), () => {
        const ground = origin.add(puv.mul(size));        // km
        const sd = normalize(vec3(this.sunDirection.x, max(this.sunDirection.y, 0.06), this.sunDirection.z)).toVar();
        const base = this.cloudBase, top = this.cloudTop;
        const N = 12;
        const od = float(0).toVar();
        Loop(N, ({ i }) => {
          const h = base.add(top.sub(base).mul(float(i).add(0.5).div(N)));
          const t = h.div(sd.y);
          const q = vec3(ground.x.add(sd.x.mul(t)), h, ground.y.add(sd.z.mul(t)));
          od.addAssign(this._cloudDensity(q, h, false));
        });
        const thick = top.sub(base).div(sd.y).div(N);
        const Tr = exp(od.mul(thick).mul(this.cloudDensity).negate());
        // multiple scattering keeps cloud shadows from going black
        out.assign(vec4(mix(float(0.18), float(1), Tr), 0, 0, 1));
      }).Else(() => { Discard(); });
      return out;
    })();
    this.shadowQuad = new THREE.QuadMesh(mat);
    this.shadowFrame = 0;
  }

  _updateShadowMap(camera) {
    if (!this.shadowQuad) this._buildShadowMap();
    const renderer = this.renderer;
    // snap the square to a 1 km grid; re-centre when the eye wanders off
    const cx = Math.round(camera.position.x / 1000), cz = Math.round(camera.position.z / 1000);
    const ox = cx - this.shadowSize / 2, oz = cz - this.shadowSize / 2;
    const moved = ox !== this.shadowOrigin.value.x || oz !== this.shadowOrigin.value.y;
    this.shadowOrigin.value.set(ox, oz);
    const slices = moved || this.shadowFrame < 4 ? 4 : 1;
    const prevTarget = renderer.getRenderTarget();
    const prevClear = renderer.autoClear;
    renderer.autoClear = false;
    renderer.setRenderTarget(this.shadowTarget);
    for (let k = 0; k < slices; k++) {
      this.shadowSlice.value = this.shadowFrame % 4;
      this.shadowQuad.render(renderer);
      this.shadowFrame++;
    }
    renderer.setRenderTarget(prevTarget);
    renderer.autoClear = prevClear;
  }

  /** TSL: cloud shadow factor for a world position (metres) */
  cloudShadow(positionWorld) {
    if (!this.shadowQuad) this._buildShadowMap();
    const sd = this.sunDirection;
    const p = positionWorld.xz.div(1000).sub(positionWorld.y.div(1000).div(max(sd.y, 0.06)).mul(sd.xz));
    const suv = p.sub(this.shadowOrigin).div(this.shadowSize);
    const inside = suv.x.greaterThan(0).and(suv.x.lessThan(1)).and(suv.y.greaterThan(0)).and(suv.y.lessThan(1));
    const tr = texture(this.shadowTarget.texture, suv).level(0).r;
    return mix(float(1), select(inside, tr, float(1)), smoothstep(0.0, 0.08, sd.y));
  }
}

function bitReverse(i, bits) {
  let r = 0;
  for (let b = 0; b < bits; b++) r |= ((i >> b) & 1) << (bits - 1 - b);
  return r;
}
