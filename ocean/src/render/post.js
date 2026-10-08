// Camera effects: sharpening, motion blur, crepuscular rays, lens flare,
// vignette, grain.
//
//  sharpen      contrast-adaptive (CAS-style) 5-tap sharpen of the TAA
//               output: restores the crispness temporal AA averages away,
//               backing off where local contrast is already high
//
//  motion blur  8 taps along the prepass velocity (camera + object motion),
//               shutter set by the panel; skipped where nothing moves
//  god rays     radial march from each pixel toward the sun through a mask of
//               bright, unoccluded sky (scene depth at the far plane)
//  lens flare   the sun's occlusion is measured once from a ring of depth
//               taps + the cloud transmittance of the sky panorama; ghosts
//               (hexagonal apertures, chromatic dispersion) lie on the line
//               through the screen centre, plus halo ring and starburst
//  vignette     cos^4-like falloff; film grain scaled by luminance

import * as THREE from 'three/webgpu';
import {
  Fn, uniform, vec2, vec3, vec4, float, screenUV, length, max, min, clamp, mix, smoothstep, abs, dot, exp, pow,
  Loop, If, atan, cos, sin, fract, floor, normalize, select, luminance,
} from 'three/tsl';
import { hash21, vnoise2 } from './tslnoise.js';
import { env } from '../env.js';

export class Post {
  constructor({ camera, sky }) {
    this.camera = camera;
    this.sky = sky;
    this.sharpen = uniform(0.5);
    this.motionBlur = uniform(0.45);
    this.flare = uniform(1);
    this.vignette = uniform(0.35);
    this.grain = uniform(0.25);
    this.godRays = uniform(0.6);
    this.sunUV = uniform(new THREE.Vector2(0.5, 0.5));
    this.sunOnScreen = uniform(0);      // 0..1 how much the sun disk is in front of the camera
    this.aspect = uniform(16 / 9);
    this.time = uniform(0);
    this._v = new THREE.Vector3();
  }

  update(renderer, dt, time) {
    const cam = this.camera;
    const p = this._v.copy(env.sunDiskDir.value).multiplyScalar(1e4).add(cam.position).project(cam);
    const front = new THREE.Vector3().copy(env.sunDiskDir.value).dot(cam.getWorldDirection(new THREE.Vector3()));
    this.sunUV.value.set(p.x * 0.5 + 0.5, 0.5 - p.y * 0.5);
    this.sunOnScreen.value = THREE.MathUtils.smoothstep(front, 0.0, 0.25) * THREE.MathUtils.smoothstep(env.sunDiskDir.value.y, -0.02, 0.03) * (1 - env.cameraUnderwater.value);
    this.aspect.value = cam.aspect;
    this.time.value = time;
  }

  /** after TAA (HDR): motion blur, then crepuscular rays */
  hdrNode() {
    return (color, ctx) => Fn(() => {
      const uv = screenUV;
      const col = vec3(color.rgb).toVar();
      // ---- contrast-adaptive sharpening (weights from tone-compressed luma)
      If(this.sharpen.greaterThan(0.001), () => {
        const px = vec2(1).div(ctx.resolution);
        const n = ctx.postTexture.sample(uv.sub(vec2(0, px.y))).rgb, s = ctx.postTexture.sample(uv.add(vec2(0, px.y))).rgb;
        const e = ctx.postTexture.sample(uv.add(vec2(px.x, 0))).rgb, w = ctx.postTexture.sample(uv.sub(vec2(px.x, 0))).rgb;
        const tl = (c) => { const l = luminance(c); return l.div(l.add(1)); };
        const lc = tl(col), ln = tl(n), ls = tl(s), le = tl(e), lw = tl(w);
        const mn = min(min(min(ln, ls), min(le, lw)), lc), mx = max(max(max(ln, ls), max(le, lw)), lc);
        const amp = clamp(min(mn, float(1).sub(mx)).div(max(mx, 1e-4)), 0, 1).sqrt();
        const k = amp.mul(this.sharpen.mul(0.15)).negate();
        col.assign(max(col.add(n.add(s).add(e).add(w).mul(k)).div(k.mul(4).add(1)), vec3(0)));
      });
      // ---- motion blur
      const vel = ctx.velocity.sample(uv).xy.mul(vec2(0.5, -0.5)).mul(this.motionBlur).toVar();
      const vlen = length(vel.mul(ctx.resolution));
      If(vlen.greaterThan(1.5), () => {
        const acc = col.toVar();
        const j = hash21(uv.mul(ctx.resolution).add(this.time.mul(61.7))).sub(0.5);
        const N = 8;
        for (let i = 1; i <= N; i++) {
          const t = float(i / N - 0.5).add(j.div(N));
          acc.addAssign(ctx.postTexture.sample(uv.sub(vel.mul(t))).rgb);
        }
        col.assign(acc.div(N + 1));
      });
      // ---- crepuscular rays (sun behind clouds / trees / the island)
      If(this.sunOnScreen.mul(this.godRays).greaterThan(0.01), () => {
        const toSun = this.sunUV.sub(uv);
        const dist = length(toSun.mul(vec2(this.aspect, 1)));
        const N = 20;
        const stepV = toSun.div(N).mul(0.85);
        const jr = hash21(uv.mul(ctx.resolution).add(this.time.mul(13.1)));
        const acc = float(0).toVar();
        const p = uv.add(stepV.mul(jr)).toVar();
        const w = float(1).toVar();
        Loop(N, () => {
          const d = ctx.sceneDepth.sample(p).r;
          const sky = select(d.greaterThan(0.99999), float(1), float(0));
          const lum = luminance(ctx.postTexture.sample(p).rgb);
          acc.addAssign(sky.mul(smoothstep(0.5, 6.0, lum)).mul(w));
          w.mulAssign(0.93);
          p.addAssign(stepV);
        });
        const rays = acc.div(N).mul(exp(dist.mul(-2.2))).mul(this.sunOnScreen).mul(this.godRays);
        col.addAssign(env.sunColor.mul(rays).mul(0.35));
      });
      return vec4(col, 1);
    })();
  }

  /** after bloom (HDR, before tone mapping): flare, vignette, grain */
  finalNode() {
    return (color, ctx) => Fn(() => {
      const uv = screenUV;
      const col = vec3(color.rgb).toVar();
      // ---- sun visibility (depth ring around the sun + cloud transmittance)
      If(this.sunOnScreen.mul(this.flare).greaterThan(0.01), () => {
        const s = this.sunUV;
        const vis = float(0).toVar();
        for (let k = 0; k < 12; k++) {
          const a = k / 12 * Math.PI * 2, r = 0.004 + (k % 3) * 0.004;
          const q = s.add(vec2(Math.cos(a) * r, Math.sin(a) * r * 1.7));
          const inside = q.x.greaterThan(0).and(q.x.lessThan(1)).and(q.y.greaterThan(0)).and(q.y.lessThan(1));
          vis.addAssign(select(inside.and(ctx.sceneDepth.sample(q).r.greaterThan(0.99999)), float(1 / 12), float(0)));
        }
        const cloudT = this.sky.sample(env.sunDiskDir, float(0)).a;
        const k = vis.mul(cloudT).mul(this.sunOnScreen).mul(this.flare).toVar();
        If(k.greaterThan(0.002), () => {
          const asp = vec2(this.aspect, 1);
          const d = uv.sub(s).mul(asp);
          const r = length(d);
          const sunC = env.sunColor.div(max(luminance(env.sunColor), 1e-3));
          // starburst: thin radial streaks from the aperture blades
          const ang = atan(d.y, d.x);
          const burst = pow(abs(cos(ang.mul(3))), 60).add(pow(abs(cos(ang.mul(3).add(0.52))), 90).mul(0.6))
            .mul(exp(r.mul(-9))).mul(0.35).add(exp(r.mul(-40)).mul(0.6));
          // halo ring
          const halo = smoothstep(0.02, 0.0, abs(r.sub(0.36))).mul(0.035);
          const hueRing = vec3(smoothstep(0.34, 0.37, r), smoothstep(0.35, 0.36, r).mul(smoothstep(0.37, 0.355, r)), smoothstep(0.38, 0.35, r));
          // ghosts along the axis through the centre, hexagonal with dispersion
          const axis = vec2(0.5).sub(s);
          let ghosts = vec3(0);
          const G = [[-0.45, 0.045, 0.8], [0.35, 0.03, 0.6], [0.72, 0.075, 0.35], [1.25, 0.12, 0.25], [1.62, 0.05, 0.45], [2.1, 0.16, 0.12]];
          for (const [t, rad, amp] of G) {
            const disp = [0.985, 1.0, 1.02];
            const ch = disp.map((f) => {
              const c = s.add(axis.mul(t * f));
              const dd = uv.sub(c).mul(asp);
              // hexagon distance
              const q = abs(dd);
              const hex = max(q.x.mul(0.866).add(q.y.mul(0.5)), q.y);
              return smoothstep(rad, rad * 0.8, hex).mul(0.65).add(smoothstep(rad * 1.02, rad * 0.97, hex).mul(0.35).mul(smoothstep(rad * 0.7, rad, hex)));
            });
            ghosts = ghosts.add(vec3(ch[0], ch[1], ch[2]).mul(amp));
          }
          const flareCol = sunC.mul(burst.add(halo)).add(hueRing.mul(halo).mul(1.2)).add(ghosts.mul(vec3(0.9, 0.95, 1.0)).mul(0.035));
          col.addAssign(flareCol.mul(k).mul(luminance(env.sunColor).mul(0.35)));
        });
      });
      // ---- vignette
      const v = uv.sub(0.5).mul(vec2(this.aspect.mul(0.8), 1));
      const r2 = dot(v, v);
      col.mulAssign(mix(float(1), pow(max(float(1).sub(r2.mul(0.9)), 0), 2.0), this.vignette));
      // ---- grain (stronger in the shadows, like film)
      const g = hash21(uv.mul(ctx.resolution).add(fract(this.time.mul(7.13)).mul(311))).sub(0.5);
      const L = luminance(col);
      col.addAssign(vec3(g.mul(this.grain).mul(0.06).mul(smoothstep(0.0, 0.25, L).add(0.1)).mul(L.add(0.02).sqrt())));
      return vec4(max(col, vec3(0)), 1);
    })();
  }
}
