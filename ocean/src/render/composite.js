// HDR composite: the air/water boundary, the underwater volume and haze.
//
// Every pixel's ray starts on the camera near plane. Whether that start is in
// water decides how the ray segment up to the first surface is shaded:
//   - the first surface is the water seen from below  -> started in water
//   - the first surface is the water seen from above  -> started in air
//   - no water surface in between                     -> ask the near plane:
//     its height is interpolated from the exact mesh vertices around the eye
//     (WaterProbe), with the mesh's own triangulation, so the waterline drawn
//     here and the rendered surface can never split apart.
// On the near-plane waterline itself a glass-edge meniscus is drawn: a thin
// cylindrical lens with a dark total-internal-reflection core and a bright rim.

import * as THREE from 'three/webgpu';
import {
  Fn, uniform, vec2, vec3, vec4, float, int, screenUV, texture, normalize, dot, max, min, clamp, mix, exp,
  abs, sqrt, pow, smoothstep, select, floor, fract, dFdx, dFdy, length, perspectiveDepthToViewZ, Loop, If,
  sin, cos, uint, uniformArray,
} from 'three/tsl';
import { env } from '../env.js';
import { PROBE_GRID, PROBE_SPACING } from '../ocean/probe.js';
import { vnoise3, gnoise2, vnoise2 } from './tslnoise.js';

export class Composite {
  constructor({ camera, probe, sky, renderer }) {
    this.camera = camera;
    this.probe = probe;
    this.sky = sky;
    this.projInv = uniform(camera.projectionMatrixInverse);
    this.camWorld = uniform(camera.matrixWorld);
    this.camPos = uniform(new THREE.Vector3());
    this.near = uniform(camera.near);
    this.far = uniform(camera.far);
    this.eyeWaterHeight = uniform(0);
    this.hazeDensity = uniform(1);
    this.underwaterVisibility = uniform(1);
    this.shafts = uniform(1);
    this.flashIntensity = uniform(0);
    this.meniscusPx = uniform(9);
    this.pixelRatio = uniform(1);
    this.debugMode = uniform(0);
  }

  update(renderer) {
    this.camPos.value.setFromMatrixPosition(this.camera.matrixWorld);
    this.near.value = this.camera.near;
    this.far.value = this.camera.far;
    this.pixelRatio.value = renderer.getPixelRatio();
  }

  // exact mesh height at a world xz near the eye (probe grid, mesh triangulation)
  _probeHeight(xz) {
    const res = this.probe.results;
    const local = xz.sub(this.probe.gridOrigin).div(PROBE_SPACING);
    const cell = clamp(floor(local), 0, PROBE_GRID - 2);
    const f = clamp(local.sub(cell), 0, 1);
    const ci = int(cell.x), cj = int(cell.y);
    const idx = (di, dj) => cj.add(dj).mul(PROBE_GRID).add(ci.add(di));
    const ha = res.element(idx(0, 0)).x, hb = res.element(idx(1, 0)).x;
    const hc = res.element(idx(0, 1)).x, hd = res.element(idx(1, 1)).x;
    // world-grid parity decides the quad diagonal (see createPatchGeometry)
    const gi = floor(this.probe.gridOrigin.x.div(PROBE_SPACING).add(0.5)).add(cell.x);
    const gj = floor(this.probe.gridOrigin.y.div(PROBE_SPACING).add(0.5)).add(cell.y);
    const odd = fract(gi.add(gj).mul(0.5)).greaterThan(0.25);
    // odd: triangles (a,c,b) + (b,c,d), diagonal b-c
    const hOddLo = ha.add(hb.sub(ha).mul(f.x)).add(hc.sub(ha).mul(f.y));
    const hOddHi = hd.add(hc.sub(hd).mul(float(1).sub(f.x))).add(hb.sub(hd).mul(float(1).sub(f.y)));
    const hOdd = select(f.x.add(f.y).lessThanEqual(1), hOddLo, hOddHi);
    // even: triangles (a,c,d) + (a,d,b), diagonal a-d
    const hEvenUp = ha.add(hd.sub(hc).mul(f.x)).add(hc.sub(ha).mul(f.y));
    const hEvenDn = ha.add(hb.sub(ha).mul(f.x)).add(hd.sub(hb).mul(f.y));
    const hEven = select(f.y.greaterThanEqual(f.x), hEvenUp, hEvenDn);
    return select(odd, hOdd, hEven);
  }

  /** returns (color, ctx) => color node */
  node() {
    return (color, ctx) => Fn(() => {
      const uv = screenUV;
      const aux = ctx.aux.sample(uv);
      const depth = ctx.sceneDepth.sample(uv).r;
      const ndc = vec2(uv.x.mul(2).sub(1), uv.y.mul(-2).add(1));
      const nearV = this.projInv.mul(vec4(ndc, 0, 1));
      const nearView = nearV.xyz.div(nearV.w);
      const pNear = this.camWorld.mul(vec4(nearView, 1)).xyz.toVar();
      const dir = normalize(pNear.sub(this.camPos)).toVar();
      const viewZ = perspectiveDepthToViewZ(depth, this.near, this.far).negate();
      const fwdCos = nearView.z.negate().div(length(nearView)).max(1e-3);
      const dist = viewZ.div(fwdCos).toVar();          // eye -> first surface, along the ray
      const isSky = depth.greaterThan(0.99999);

      // ---- is the start of this ray in the water?
      const hNear = this._probeHeight(pNear.xz);
      const sNear = pNear.y.sub(hNear).toVar();        // metres above water, on the near plane
      const face = aux.r;
      const startWet = select(face.greaterThan(0.75), float(0), select(face.greaterThan(0.25), float(1), select(sNear.lessThan(0), float(1), float(0)))).toVar();

      const col = vec3(color.rgb).toVar();
      const c = env.waterAbsorption.add(env.waterScattering.mul(this.underwaterVisibility.reciprocal()));
      const b = env.waterScattering.mul(this.underwaterVisibility.reciprocal());

      // ---- underwater volume from the eye to the first surface
      If(startWet.greaterThan(0.5), () => {
        const L = select(isSky, float(400), min(dist, 400));
        const zc = max(this.eyeWaterHeight.sub(this.camPos.y), 0);    // eye depth
        const mu = dir.y.negate();                                      // + looking down
        const T = exp(c.negate().mul(L));
        // light arriving in the water column (sun refracted down + sky)
        const sunW = env.sunDir;
        const sunRefr = normalize(vec3(sunW.x.mul(0.75), sunW.y.max(0.2), sunW.z.mul(0.75)));
        const Kd = c.mul(1.1);
        const cosS = dot(dir, sunRefr);
        // strongly forward-peaked seawater phase (two-lobe HG)
        const g1 = 0.88, g2 = 0.3;
        const hg = (g) => float((1 - g * g) / (4 * Math.PI)).div(pow(float(1 + g * g).sub(cosS.mul(2 * g)).max(1e-3), 1.5));
        const phase = hg(g1).mul(0.6).add(hg(g2).mul(0.4));
        const k = Kd.mul(mu);
        const depthAtten = exp(Kd.negate().mul(zc));
        const integ = float(1).sub(exp(c.add(k).negate().mul(L))).div(c.add(k).max(1e-4));
        const sunIn = env.sunColor.mul(sunW.y.max(0).mul(0.8).add(0.2)).mul(phase).mul(b).mul(depthAtten).mul(integ);
        const skyIn = env.skyIrradiance.mul(float(0.9 / (4 * Math.PI))).mul(b).mul(depthAtten).mul(integ);
        // light shafts: march the sun term through a moving occlusion pattern
        const shaft = float(0).toVar();
        If(this.shafts.greaterThan(0.5), () => {
          const N = 10;
          const Ls = min(L, 45);
          const j = vnoise2(uv.mul(vec2(911.0, 677.0)).add(env.time.mul(37.0)));
          Loop(N, ({ i }) => {
            const t = float(i).add(j).div(N).mul(Ls);
            const p = this.camPos.add(dir.mul(t));
            // project along the refracted sun ray onto the surface plane
            const tt = this.eyeWaterHeight.sub(p.y).div(sunRefr.y);
            const q = p.xz.add(sunRefr.xz.mul(tt));
            const pat = gnoise2(q.mul(0.55).add(env.time.mul(vec2(0.15, 0.09))))
              .add(gnoise2(q.mul(1.4).sub(env.time.mul(vec2(0.07, 0.2)))).mul(0.6));
            const lit = smoothstep(-0.1, 0.9, pat);
            shaft.addAssign(lit.mul(exp(c.y.negate().mul(t))).mul(exp(Kd.y.negate().mul(max(this.eyeWaterHeight.sub(p.y), 0)))));
          });
          shaft.assign(shaft.div(N).mul(Ls).mul(0.45));
        });
        const shaftLight = env.sunColor.mul(phase).mul(b).mul(shaft).mul(1.6);
        // flashlight beam scattering
        const flash = vec3(0).toVar();
        If(env.flashlight.greaterThan(0.5), () => {
          const N = 8;
          const Lf = min(L, 18);
          const jf = vnoise2(uv.mul(vec2(523.0, 811.0)).add(env.time.mul(53.0)));
          Loop(N, ({ i }) => {
            const t = float(i).add(jf).div(N).mul(Lf);
            const p = this.camPos.add(dir.mul(t));
            const toP = p.sub(env.flashlightPos);
            const d2 = dot(toP, toP).max(0.04);
            const cosA = dot(normalize(toP), env.flashlightDir);
            const cone = smoothstep(0.86, 0.97, cosA);
            flash.addAssign(vec3(cone.div(d2)).mul(exp(c.negate().mul(t.add(sqrt(d2))))));
          });
          flash.assign(flash.div(N).mul(Lf).mul(b).mul(this.flashIntensity).mul(0.9));
        });
        col.assign(col.mul(T).add(sunIn).add(skyIn).add(shaftLight).add(flash));
      }).Else(() => {
        // ---- aerial perspective above water (ground haze + Rayleigh tint)
        If(isSky.not(), () => {
          const d = dist.max(0);
          const h = max(this.camPos.y.add(dir.y.mul(d.mul(0.5))), 0);
          const dens = exp(h.negate().div(900)).mul(this.hazeDensity);
          const ext = vec3(0.011, 0.016, 0.026).mul(dens).add(0.009 * 1.0);
          const Tair = exp(ext.negate().mul(d.div(1000)));
          const horizonDir = normalize(vec3(dir.x, max(dir.y, 0.02), dir.z));
          const inscatter = this.sky.atmo.skyRadiance(horizonDir).mul(this.sky.lightIlluminance).mul(1.05);
          col.assign(col.mul(Tair).add(inscatter.mul(Tair.oneMinus())));
        });
      });

      // ---- near-plane meniscus (the lens-like edge of water on the "glass")
      const grad = vec2(dFdx(sNear), dFdy(sNear));
      const gl = length(grad).max(1e-7);
      const distPx = sNear.div(gl);
      const W = this.meniscusPx.mul(this.pixelRatio);
      const t = clamp(distPx.div(W), -1.5, 1.5);
      const band = smoothstep(1.2, 0.0, abs(t));
      If(band.greaterThan(0.001), () => {
        const n2 = grad.div(gl);                      // screen direction towards "above"
        const lens = sqrt(max(float(1).sub(t.mul(t)), 0));
        const offsPx = t.sign().negate().mul(lens).mul(W).mul(0.9);
        const uv2 = uv.add(n2.mul(offsPx).mul(vec2(1, -1)).div(ctx.resolution));
        const through = ctx.sceneColorNode.sample(uv2).level(0).rgb;
        const core = smoothstep(0.55, 0.0, abs(t.add(0.08)));
        const rim = smoothstep(0.35, 0.0, abs(t.sub(0.62)));
        const skyTint = env.skyIrradiance.mul(0.25);
        const lensed = mix(col, through.mul(vec3(0.8, 0.92, 0.95)), smoothstep(1.0, 0.3, abs(t)).mul(0.85));
        const shaded = lensed.mul(float(1).sub(core.mul(0.72))).add(skyTint.mul(rim).mul(0.6));
        col.assign(mix(col, shaded, band));
      });
      If(this.debugMode.greaterThan(0.5), () => {
        col.assign(vec3(face, startWet, sNear.mul(0.2).add(0.5)));
      });
      return vec4(col, 1);
    })();
  }
}
