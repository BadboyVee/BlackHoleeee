// Ocean: FFT cascades + CDLOD surface + TSL sampling helpers shared by every
// system that needs to know where the water is (surface shader, underwater
// mask, caustics, buoyancy queries).

import * as THREE from 'three/webgpu';
import {
  Fn, attribute, positionGeometry, cameraPosition, uniform, vec2, vec3, vec4, float,
  fract, clamp, length, log2, max, texture, varying, smoothstep, mix, select, normalize,
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
   * Vertex stage: patch grid -> morphed world xz -> displaced world position.
   * Returns { position, worldXZ (varying) }.
   */
  /**
   * Returns { position } where position is an Fn node; the varyings it creates
   * are published on the returned object when the vertex stage is built (the
   * fragment stage of the same build reads them).
   */
  buildVertex(shore = null, timeNode = null) {
    // pure expressions only (no statements), so this can be built eagerly and
    // its varyings handed to the fragment stage
    const out = this._buildVertex(shore, timeNode);
    out.position = out._position;
    return out;
  }

  _buildVertex(shore, timeNode) {
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
    let disp = this.displacement(xz, effSpacing);
    let fftFoam = this.foamAt(xz, effSpacing);
    const out = { spacing: effSpacing };
    let y;
    if (shore) {
      const st = shore.state(xz, timeNode, true);
      // wind chop dies down in the shallows; the shore swell takes over
      const fftAtten = smoothstep(0.25, 6.0, st.depth).mul(smoothstep(-2, 3, st.sdf));
      disp = disp.mul(vec3(fftAtten, mix(0.25, 1, fftAtten).mul(smoothstep(-3, 0.5, st.sdf)), fftAtten));
      fftFoam = fftFoam.mul(fftAtten);
      const br = shore.breaker(st, true);
      disp = disp.add(br.disp);
      const sw = shore.swash(st, timeNode);
      // swash sheet riding over the beach face; hide the ocean under dry sand
      const bedTop = st.bed.add(sw.thick);
      const onLand = st.bed.greaterThan(disp.y.sub(0.02));
      // thin sheets (<2 cm) are drawn by the terrain shader (per-pixel edge)
      // feather the sheet edge flush into the (smooth, wave-washed) beach face
      // instead of a vertical step; everywhere else on land hide far below
      const nearSwash = st.sdf.greaterThan(sw.rmax.add(2.5).negate()).and(st.bed.lessThan(2.5));
      y = select(onLand, select(sw.thick.greaterThan(0.02), bedTop, select(nearSwash, st.bed.sub(0.004), float(-4))), disp.y);
      // the prepass never sees the swash sheet: it would cast AO / contact
      // shadows onto the sand around its edge
      out.prepassY = select(onLand, st.bed.sub(0.05), disp.y);
      const nShore = normalize(vec3(st.fwd.x.mul(br.normalFwd), br.normalUp, st.fwd.y.mul(br.normalFwd)));
      out.shoreNormal = varying(nShore, 'vShoreN');
      out.shoreFoam = varying(max(br.foam.mul(st.H.mul(1.2).min(1)), sw.foam.mul(select(onLand, float(1), float(0)))), 'vShoreFoam');
      out.thin = varying(br.thin, 'vShoreThin');
      out.folded = varying(select(br.flipped, float(1), float(0)), 'vShoreFold');
      out.breakZone = varying(smoothstep(0.6, 1.2, st.beta).mul(smoothstep(0.3, 0.8, st.H)), 'vBreakZone');
      out.swash = varying(select(onLand, sw.thick, float(1)), 'vSwash');
      out.fftAtten = varying(fftAtten, 'vFftAtten');
      out.depth = varying(st.depth, 'vWaterDepth');
    } else {
      y = disp.y;
    }
    const rel = xz.sub(cameraPosition.xz);
    const curvature = rel.dot(rel).div(2 * EARTH_RADIUS);
    const position = vec3(xz.x.add(disp.x), y.sub(curvature), xz.y.add(disp.z));
    if (out.prepassY) {
      const pre = vec3(xz.x.add(disp.x), out.prepassY.sub(curvature), xz.y.add(disp.z));
      out._position = Fn((inputs, builder) => (builder.context.prepass === true ? pre : position))();
    }
    // whitecap foam is sampled per vertex (fragment texture slots are scarce);
    // the fragment shader adds the fine bubbly structure
    out.foam = varying(fftFoam, 'vOceanFoam');
    if (!out._position) out._position = position;
    out.worldXZ = varying(xz, 'vOceanXZ');
    out.height = varying(disp.y, 'vOceanH');
    return out;
  }

  update(dt, time, camera) {
    this.fft.update(dt, time);
    this.selector.update(camera, 6);
  }
}
