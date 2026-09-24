// Ocean: FFT cascades + CDLOD surface + TSL sampling helpers shared by every
// system that needs to know where the water is (surface shader, underwater
// mask, caustics, buoyancy queries).

import * as THREE from 'three/webgpu';
import {
  Fn, attribute, positionGeometry, cameraPosition, uniform, vec2, vec3, vec4, float,
  fract, clamp, length, log2, max, texture, varying, smoothstep, mix, select, normalize, exp, sin,
} from 'three/tsl';
import { OceanFFT, OCEAN_SIZE } from './fft.js';
import { createPatchGeometry, PatchSelector } from './oceanMesh.js';

const EARTH_RADIUS = 6371000;

export class Ocean {
  constructor(renderer, params) {
    this.params = params;
    this.fft = new OceanFFT(renderer, params);
    this.lengthScales = this.fft.lengthScales;
    this.geometry = createPatchGeometry();
    this.selector = new PatchSelector(this.geometry, { maxHeight: 10 });
    // per-cascade amplitude weights (used by UI + gust modulation)
    this.cascadeWeights = this.lengthScales.map(() => uniform(1));
    // extra displacement contributors (shore waves, wake) register here
    this.displacementModifiers = [];
    this.eyeXZ = uniform(new THREE.Vector2());
    this.nearFadeOff = uniform(1);
    // splash events (whale breaches): foam patch + an expanding ring wave
    this.blobs = Array.from({ length: 4 }, () => uniform(new THREE.Vector4(0, 0, 0, -1000)));
    this.time = 0;
  }

  /** a splash at (x, z) of radius r (m): foam and a ring wave for ~40 s */
  addFoamBlob(x, z, r) {
    let slot = this.blobs[0];
    for (const b of this.blobs) if (b.value.w < slot.value.w) slot = b;
    slot.value.set(x, z, r, this.time);
  }

  _blobs(xz, timeNode) {
    let dy = float(0), foam = float(0);
    for (const b of this.blobs) {
      const age = timeNode.sub(b.w);
      const live = age.greaterThan(0).and(age.lessThan(45));
      const d = length(xz.sub(b.xy));
      const r = b.z;
      const f = smoothstep(r.mul(1.1), r.mul(0.3), d).mul(exp(age.mul(-0.12))).mul(1.6);
      // ring: a short wave packet running outward at ~4 m/s, decaying
      const front = d.sub(age.mul(4.0));
      const ring = sin(front.mul(1.3)).mul(exp(front.mul(front).mul(-0.05))).mul(r.mul(0.05)).mul(exp(age.mul(-0.12)));
      dy = dy.add(select(live, ring, float(0)));
      foam = foam.add(select(live, f, float(0)));
    }
    return { dy, foam };
  }

  /** TSL: summed cascade displacement at undisplaced world xz. */
  displacement(xz, spacing = null) {
    let d = vec3(0);
    this.lengthScales.forEach((L, c) => {
      const uv = xz.div(L);
      let s = texture(this.fft.displacement[c], uv);
      if (spacing) {
        const texel = L / OCEAN_SIZE;
        s = s.level(max(log2(spacing.div(texel)), 0));
      }
      d = d.add(s.xyz.mul(this.cascadeWeights[c]));
    });
    return d;
  }

  /** TSL: summed derivatives (dDy/dx, dDy/dz, dDx/dx, dDz/dz) and foam. */
  derivatives(xz) {
    let d = vec4(0);
    this.lengthScales.forEach((L, c) => {
      d = d.add(texture(this.fft.derivatives[c], xz.div(L)).mul(this.cascadeWeights[c]));
    });
    return d;
  }

  foam(xz) {
    let f = float(0);
    this.lengthScales.forEach((L, c) => {
      f = f.add(texture(this.fft.displacement[c], xz.div(L)).w.mul(this.cascadeWeights[c]));
    });
    return f;
  }

  foamAt(xz, spacing) {
    let f = float(0);
    this.lengthScales.forEach((L, c) => {
      const texel = L / OCEAN_SIZE;
      const lod = max(log2(spacing.div(texel)), 0);
      f = f.add(texture(this.fft.displacement[c], xz.div(L)).level(lod).w.mul(this.cascadeWeights[c]));
    });
    return f;
  }

  /**
   * The water surface at an undisplaced grid position (pure TSL, usable in
   * vertex and compute stages). Everything that must agree about where the
   * water is (mesh, waterline probe, buoyancy) goes through this.
   */
  surface(xz, spacing, shore, timeNode, { wakeScale = null } = {}) {
    let disp = this.displacement(xz, spacing);
    let fftFoam = this.foamAt(xz, spacing);
    if (timeNode) {
      const bl = this._blobs(xz, timeNode);
      disp = disp.add(vec3(0, bl.dy, 0));
      fftFoam = fftFoam.add(bl.foam);
    }
    const out = {};
    let y;
    if (shore) {
      const st = shore.state(xz, timeNode, true);
      // wind chop dies down in the shallows; the shore swell takes over
      const fftAtten = smoothstep(0.25, 6.0, st.depth).mul(smoothstep(-2, 3, st.sdf));
      disp = disp.mul(vec3(fftAtten, mix(0.25, 1, fftAtten).mul(smoothstep(-3, 0.5, st.sdf)), fftAtten));
      fftFoam = fftFoam.mul(fftAtten);
      const br = shore.breaker(st, true);
      disp = disp.add(br.disp);
      if (this.wake) {
        // interactive wake waves (boats) ride on top of everything else
        const wk = this.wake.sample(xz);
        disp = disp.add(vec3(0, wakeScale ? wk.x.mul(wakeScale) : wk.x, 0));
        out.wake = wk;
      }
      const sw = shore.swash(st, timeNode);
      // swash sheet riding over the beach face; hide the ocean under dry sand
      const bedTop = st.bed.add(sw.thick);
      const onLand = st.bed.greaterThan(disp.y.sub(0.02));
      // thin sheets (<2 cm) are drawn by the terrain shader (per-pixel edge);
      // feather the sheet edge flush into the (smooth, wave-washed) beach face
      // instead of a vertical step; everywhere else on land hide far below
      const nearSwash = st.sdf.greaterThan(sw.rmax.add(2.5).negate()).and(st.bed.lessThan(2.5));
      y = select(onLand, select(sw.thick.greaterThan(0.02), bedTop, select(nearSwash, st.bed.sub(0.004), float(-4))), disp.y);
      // the prepass never sees the swash sheet: it would cast AO / contact
      // shadows onto the sand around its edge
      out.prepassY = select(onLand, st.bed.sub(0.05), disp.y);
      Object.assign(out, { st, br, sw, fftAtten, onLand });
    } else {
      y = disp.y;
    }
    // right at the camera the surface must be a true height field so the
    // waterline probe can reproduce the mesh exactly: fade out the
    // horizontal (choppy) displacement within ~2 m of the eye
    const near = smoothstep(0.6, 2.2, length(xz.sub(this.eyeXZ))).max(this.nearFadeOff);
    disp = vec3(disp.x.mul(near), disp.y, disp.z.mul(near));
    Object.assign(out, { disp, y, fftFoam });
    return out;
  }

  /**
   * Vertex stage: patch grid -> morphed world xz -> displaced world position,
   * plus the varyings the water shader needs.
   */
  buildVertex(shore = null, timeNode = null) {
    const patch = attribute('oceanPatch', 'vec4');
    const g = positionGeometry.xz;
    const origin = patch.xy, spacing = patch.z, morphEnd = patch.w;
    const world0 = origin.add(g.mul(spacing));
    const dist = length(vec3(world0.x, 0, world0.y).sub(cameraPosition));
    const morphK = clamp(dist.sub(morphEnd.mul(0.62)).div(morphEnd.mul(0.34)), 0, 1);
    const odd = fract(g.mul(0.5)).mul(2);
    const gm = g.sub(odd.mul(morphK));
    const xz = origin.add(gm.mul(spacing));
    const effSpacing = spacing.mul(morphK.add(1));
    const srf = this.surface(xz, effSpacing, shore, timeNode);
    const { disp, y } = srf;
    const out = { spacing: effSpacing };
    if (shore) {
      const { st, br, sw, fftAtten, onLand } = srf;
      const nShore = normalize(vec3(st.fwd.x.mul(br.normalFwd), br.normalUp, st.fwd.y.mul(br.normalFwd)));
      out.shoreNormal = varying(nShore, 'vShoreN');
      let shoreFoam = max(br.foam.mul(st.H.mul(1.2).min(1)), sw.foam.mul(select(onLand, float(1), float(0))));
      // whitewater left behind by broken bores (persistent surf foam field)
      if (this.surf) shoreFoam = max(shoreFoam, this.surf.sample(xz).mul(select(onLand, float(0), float(1))));
      out.shoreFoam = varying(shoreFoam, 'vShoreFoam');
      out.thin = varying(br.thin, 'vShoreThin');
      out.folded = varying(select(br.flipped, float(1), float(0)), 'vShoreFold');
      out.breakZone = varying(smoothstep(0.6, 1.2, st.beta).mul(smoothstep(0.3, 0.8, st.H)), 'vBreakZone');
      out.swash = varying(select(onLand, sw.thick, float(1)), 'vSwash');
      out.fftAtten = varying(fftAtten, 'vFftAtten');
      out.depth = varying(st.depth, 'vWaterDepth');
      if (srf.wake) {
        out.wakeSlope = varying(srf.wake.yz, 'vWakeSlope');
        out.wakeFoam = varying(srf.wake.w, 'vWakeFoam');
      }
    }
    const rel = xz.sub(cameraPosition.xz);
    const curvature = rel.dot(rel).div(2 * EARTH_RADIUS);
    const position = vec3(xz.x.add(disp.x), y.sub(curvature), xz.y.add(disp.z));
    if (srf.prepassY) {
      const pre = vec3(xz.x.add(disp.x), srf.prepassY.sub(curvature), xz.y.add(disp.z));
      out.position = Fn((inputs, builder) => (builder.context.prepass === true ? pre : position))();
    } else {
      out.position = position;
    }
    // whitecap foam is sampled per vertex (fragment texture slots are scarce);
    // the fragment shader adds the fine bubbly structure
    out.foam = varying(srf.fftFoam, 'vOceanFoam');
    out.worldXZ = varying(xz, 'vOceanXZ');
    out.height = varying(disp.y, 'vOceanH');
    return out;
  }

  update(dt, time, camera, waterHeightAtEye = 0) {
    this.time = time;
    this.fft.update(dt, time);
    this.selector.update(camera, 6);
    this.eyeXZ.value.set(camera.position.x, camera.position.z);
    // only flatten the chop around the eye when the eye is near the surface
    this.nearFadeOff.value = Math.abs(camera.position.y - waterHeightAtEye) < 3 ? 0 : 1;
  }
}
