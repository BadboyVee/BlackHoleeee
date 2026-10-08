// Ocean surface material.
//
// Above water (front faces):
//   specular   GGX sun glints; roughness = slope variance the pixel can't
//              resolve (spectrum tail + Cox-Munk), so the glitter path widens
//              with distance instead of aliasing into sparkles
//   reflection sky/cloud panorama (+ screen-space reflections of local objects)
//   refraction depth-checked screen-space refraction of the scene below,
//              attenuated by Beer's law along the refracted path, plus
//              analytic single scattering of sun + sky light in the water
//              column (spectral absorption/scattering + broadband particulate
//              backscatter)
//   SSS        light transmitted through thin, backlit crests
//   foam       whitecaps (FFT Jacobian), shore and wake foam
// Below water (back faces): Snell's window with total internal reflection.

import * as THREE from 'three/webgpu';
import {
  Fn, float, vec2, vec3, vec4, int, uniform, uniformArray, normalize, dot, max, min, clamp, mix, abs,
  sqrt, pow, exp, log2, reflect, refract, smoothstep, length, fract, floor, select, If, Loop, Break,
  frontFacing, positionWorld, positionView, positionViewDirection, cameraPosition, cameraViewMatrix,
  cameraProjectionMatrix, transformNormalToView, screenUV, viewportSharedTexture, viewportDepthTexture,
  linearDepth, perspectiveDepthToViewZ, cameraNear, cameraFar, dFdx, dFdy, varying, texture, mrt, sin,
  cos, positionLocal, positionPrevious, exp2, luminance,
} from 'three/tsl';
import { env } from '../env.js';
import { gnoise2, vnoise2, voronoi2, fbm2 } from '../render/tslnoise.js';

const IOR = 1.333;

/** exact unpolarised Fresnel; n = n_t / n_i, c = cos(incidence) >= 0 */
export function fresnelExact(c, n) {
  const g2 = float(n * n - 1).add(c.mul(c));
  const tir = g2.lessThan(0);
  const g = sqrt(max(g2, 0));
  const a = g.sub(c).div(g.add(c));
  const b = c.mul(g.add(c)).sub(1).div(c.mul(g.sub(c)).add(1));
  const F = a.mul(a).mul(0.5).mul(b.mul(b).add(1));
  return select(tir, float(1), clamp(F, 0, 1));
}

// Beckmann: water slopes are Gaussian (Cox & Munk), so GGX's long tails would
// smear the sun over half the sea. m2 = mean square slope.
function D_Beckmann(NdotH, alpha) {
  const m2 = alpha.mul(alpha).max(1e-5);
  const c2 = NdotH.mul(NdotH).max(1e-5);
  const tan2 = float(1).sub(c2).div(c2);
  return exp(tan2.div(m2).negate()).div(m2.mul(c2).mul(c2).mul(Math.PI));
}

// Smith-Beckmann G1 (Walter et al. rational fit), combined into V = G / (4 NL NV)
function G1_Beckmann(NdotX, alpha) {
  const c = NdotX.max(1e-4);
  const a = c.div(alpha.mul(sqrt(float(1).sub(c.mul(c)).max(1e-6))));
  const g = a.mul(3.535).add(a.mul(a).mul(2.181)).div(a.mul(2.276).add(a.mul(a).mul(2.577)).add(1));
  return select(a.lessThan(1.6), g, float(1));
}

function V_SmithBeckmann(NdotL, NdotV, alpha) {
  return G1_Beckmann(NdotL, alpha).mul(G1_Beckmann(NdotV, alpha)).div(NdotL.mul(NdotV).mul(4).max(1e-5));
}

class WaterLightingModel extends THREE.LightingModel {
  constructor(material) {
    super();
    this.m = material;
  }

  direct({ lightDirection, lightColor, reflectedLight, lightNode }) {
    const s = this.m.shared;
    const L = lightDirection; // view space, toward the light
    const N = s.nView, V = s.vView;
    const NdotL = dot(N, L).max(0);
    const NdotV = dot(N, V).max(1e-4);
    const H = normalize(L.add(V));
    const NdotH = dot(N, H).max(0);
    const VdotH = dot(V, H).max(0);
    const isSun = lightNode && lightNode.light && lightNode.light.isDirectionalLight;
    // the sun is an area light: widen the lobe by its angular radius
    const alpha = isSun ? sqrt(s.alpha.mul(s.alpha).add(0.0003)) : s.alpha.max(0.08);
    const F = fresnelExact(VdotH, IOR);
    const spec = D_Beckmann(NdotH, alpha).mul(V_SmithBeckmann(NdotL, NdotV, alpha)).mul(F).mul(NdotL);
    const above = s.above;
    const noFoam = s.foam.oneMinus();
    // sun glitter: soft-clip the peak so the glitter path stays a path of
    // sparkles instead of a blown-out, blooming slab (a camera's highlight
    // roll-off; energy below the knee is untouched)
    let specL = lightColor.mul(spec);
    if (isSun) {
      const knee = this.m.glareKnee;
      specL = specL.mul(this.m.glare).div(specL.div(knee).add(1));
    }
    reflectedLight.directSpecular.addAssign(specL.mul(noFoam).mul(above));

    // light entering the water, scattered back towards the eye by the column
    const LdotN = NdotL.max(0.02);
    const Tin = fresnelExact(LdotN, IOR).oneMinus();
    // sun light scattered back out of the (lit, possibly shadowed) water column
    const scatter = s.scatterResponse.mul(Tin).mul(s.Tview).mul(s.bodyOpacity).mul(noFoam).mul(above);
    // crest subsurface: backlit thin water at the tops of waves
    const Lw = s.lightWorld(L);
    const backlit = pow(dot(s.vWorld.negate(), normalize(vec3(Lw.x, Lw.y.mul(0.2), Lw.z))).max(0), 4.0);
    const sss = s.sssColor.mul(backlit).mul(s.crest).mul(s.Fview.oneMinus()).mul(noFoam).mul(above).mul(isSun ? 1 : 0.3);
    // sunlight scattered back out of the bubble cloud under foam
    const bubbles = s.bubbleColor.mul(s.aer).mul(NdotL.mul(0.6).add(0.4)).mul(Tin).mul(s.Tview).mul(noFoam);
    // foam: rough diffuse with a little forward-scatter translucency
    const foamLit = NdotL.mul(0.8).add(0.2).mul(s.foam).mul(s.foamAlbedo).mul(1 / Math.PI);
    reflectedLight.directDiffuse.addAssign(lightColor.mul(scatter.add(sss).add(foamLit).add(bubbles)));

    // underwater side: the sun seen through the surface (Snell's window glow)
    const below = above.oneMinus();
    If(below.greaterThan(0.5), () => {
      const T = s.transmitDir;
      const sunDot = dot(T, Lw).max(0);
      const glow = pow(sunDot, 600.0).mul(40).add(pow(sunDot, 12.0).mul(0.25));
      reflectedLight.directSpecular.addAssign(lightColor.mul(glow).mul(s.Tview).mul(isSun ? 1 : 0.2));
    });
  }

  indirect(/* builder */) {
    // reflection / refraction / ambient are computed in the material (shared)
    // and injected through the reflectedLight context in setupLighting
  }
}

export class WaterMaterial extends THREE.NodeMaterial {
  static get type() { return 'WaterMaterial'; }

  constructor({ ocean, terrain, sky, shore = null, foamTexture }) {
    super();
    this.shore = shore;
    this.isWaterMaterial = true;
    this.lights = true;
    this.side = THREE.DoubleSide;
    this.ocean = ocean;
    this.terrain = terrain;
    this.sky = sky;
    this.shoreModifiers = [];   // (ctx) => { foam, normalOffset } contributions
    this.roughnessTable = uniformArray(Array.from(ocean.fft.unresolvedSlope), 'float');
    this.foamTexture = foamTexture;
    this.ssrEnabled = uniform(1);
    this.foamScale = uniform(1);
    this.sssStrength = uniform(1);
    this.glare = uniform(0.8);        // sun glitter strength
    this.glareKnee = uniform(24);     // soft-clip knee (scene radiance units)
    const v = ocean.buildVertex(shore, env.time, env.dt);
    this.v = v;   // varyings appear on v once the vertex stage is built
    this.positionNode = v.position;
    this.name = 'water';
    this.userData.noAO = true;
    this.userData.noContactShadow = true;
    this.hullMasks = [];
  }

  /**
   * Keep the sea out of a hull: water fragments inside the hull's plan
   * outline and below its sheer line are discarded (the hull is watertight,
   * the rendered surface isn't). halfBeam(s) is the hull's plan shape, s = 0
   * at the transom, 1 at the stem; length/sheer in metres.
   */
  addHullMask({ matrixWorldInverse, length, halfBeam, sheer }) {
    this.hullMasks.push({ inv: uniform(matrixWorldInverse), length, halfBeam, sheer });
    const masks = this.hullMasks;
    this.maskNode = Fn(() => {
      let keep = float(1);
      for (const m of masks) {
        const lp = m.inv.mul(vec4(positionWorld, 1)).xyz;
        const s = float(0.5).sub(lp.z.div(m.length));
        const within = s.greaterThan(0.002).and(s.lessThan(0.995));
        const hb = m.halfBeam(clamp(s, 0, 1));
        const inside = within.and(abs(lp.x).lessThan(hb)).and(lp.y.lessThan(m.sheer(clamp(s, 0, 1))));
        keep = keep.mul(select(inside, float(0), float(1)));
      }
      return keep.greaterThan(0.5);
    })();
    this.needsUpdate = true;
  }

  updateRoughnessTable() {
    const t = this.ocean.fft.unresolvedSlope;
    for (let i = 0; i < t.length; i++) this.roughnessTable.array[i] = t[i];
  }

  setupPosition(builder) {
    const r = super.setupPosition(builder);
    if (builder.needsPreviousData()) positionPrevious.assign(this.v.prevPosition ?? positionLocal);
    return r;
  }

  setupLightingModel() {
    return new WaterLightingModel(this);
  }

  // shared per-fragment quantities, built once and read by the lighting model
  _setupShared(builder) {
    const s = {};
    const v = this.v;
    this.vXZ = v.worldXZ; this.vFoam = v.foam; this.vHeight = v.height;
    const xz = this.vXZ;
    const der = this.ocean.derivatives(xz);
    let slope = vec2(der.x.div(der.z.add(1)), der.y.div(der.w.add(1)));
    let foam = this.vFoam.mul(0.55);
    let base = vec3(0, 1, 0);
    let aboveBool = frontFacing;
    if (v.shoreNormal) {
      // shallow-water swell carries less wind chop, but its faces keep some texture
      slope = slope.mul(v.fftAtten.mul(0.6).add(0.4));
      foam = foam.add(v.shoreFoam.mul(1.05));
      base = normalize(v.shoreNormal);
      // overturned lip: its triangles flip winding but it is still seen from air
      // inside a breaking crest winding flips where the lip overturns: from
      // the air every face there is seen from above the water
      aboveBool = frontFacing.or(v.breakZone.greaterThan(0.01).and(env.cameraUnderwater.lessThan(0.5)));
    }
    if (v.roughAmp) {
      // the boiling roller of a broken wave (same relief as the mesh, but
      // resolved per pixel)
      const amp = v.roughAmp;
      const tslope = vec2(0).toVar('rollerSlope');
      If(amp.greaterThan(0.003), () => {
        const e = 0.15;
        const h0 = this.shore.turbulence(xz, env.time);
        const hx = this.shore.turbulence(xz.add(vec2(e, 0)), env.time);
        const hz = this.shore.turbulence(xz.add(vec2(0, e)), env.time);
        tslope.assign(vec2(hx.sub(h0), hz.sub(h0)).mul(amp.div(e)));
      });
      slope = slope.add(tslope);
    }
    if (v.wakeSlope) {
      slope = slope.add(v.wakeSlope);
      foam = foam.add(v.wakeFoam.mul(0.9));
    }
    const ctx = { xz, slope, foam, height: this.vHeight };
    for (const mod of this.shoreModifiers) mod(ctx);
    slope = ctx.slope; foam = ctx.foam;
    // detail slopes perturb the (possibly curled) base surface
    const nUp = normalize(base.add(vec3(slope.x.negate(), 0, slope.y.negate()).mul(base.y.abs().max(0.35)))).toVar('waterN');
    const above = select(aboveBool, float(1), float(0)).toVar('waterAbove');
    const vWorld = normalize(cameraPosition.sub(positionWorld)).toVar('waterV');
    // a visible surface faces the eye, but detail normals can tilt away at
    // silhouettes (crests seen from behind, the lip): bend them back, or the
    // pixel reflects the sea below the horizon and draws a black seam
    const nRaw = select(aboveBool, nUp, nUp.negate());
    const nWorld = normalize(nRaw.add(vWorld.mul(max(float(0.04).sub(dot(nRaw, vWorld)), 0)))).toVar('waterNWorld');
    s.above = above;
    s.nWorld = nWorld;
    s.nView = transformNormalToView(nWorld).toVar('waterNView');
    s.vView = positionViewDirection;
    s.vWorld = vWorld;
    s.lightWorld = (Lview) => normalize(cameraViewMatrix.transpose().mul(vec4(Lview, 0)).xyz);

    // ---- roughness from unresolved slope variance
    const dx = dFdx(xz), dy = dFdy(xz);
    const footprint = max(length(dx), length(dy)).max(1e-4);
    const kc = float(Math.PI).div(footprint);
    const idx = clamp(log2(kc.div(0.05)).div(Math.log2(800 / 0.05)).mul(15), 0, 15);
    const i0 = int(floor(idx)), i1 = int(min(floor(idx).add(1), 15));
    const mss = mix(this.roughnessTable.element(i0), this.roughnessTable.element(i1), fract(idx));
    // gusts: patches of smoother / rougher water drifting with the wind
    const gust = fbm2(xz.mul(0.012).add(env.windDir.mul(env.time.mul(0.02))), 3).mul(0.5).add(0.5);
    const alpha = clamp(sqrt(mss.mul(mix(0.55, 1.35, gust))), 0.035, 0.6).toVar('waterAlpha');
    s.alpha = alpha;

    // ---- foam look: baked lace texture, two drifting rotated lookups so it
    // never tiles; coverage retreats from the texture's low "fill order"
    // values first, so decaying foam thins into lace and filaments
    const drift = env.windDir.mul(env.time.mul(0.12));
    // a slow warp of the lookups so the lace never reads as a lattice
    const wq = xz.mul(0.07);
    const fx = xz.add(vec2(vnoise2(wq), vnoise2(wq.add(vec2(5.3, -2.1)))).sub(0.5).mul(1.8));
    const fA = texture(this.foamTexture, fx.add(drift).div(3.1));
    const rot = vec2(fx.x.mul(0.8).sub(fx.y.mul(0.6)), fx.x.mul(0.6).add(fx.y.mul(0.8)));
    const fB = texture(this.foamTexture, rot.sub(drift.mul(0.6)).div(4.7).add(0.37));
    const order = max(fA.x, fB.x.mul(0.92));
    const amount = clamp(foam.mul(this.foamScale), 0, 1.6).toVar('waterFoamAmount');
    // thin, old lace has soft edges; dense foam is crisp
    const edge = mix(float(0.3), float(0.16), smoothstep(0.2, 1.0, amount));
    // even dense foam keeps bubble holes and lace (threshold only reaches 0 at 1.2)
    const thr = float(1).sub(amount.mul(0.82));
    const coverage = smoothstep(thr, thr.add(edge), order);
    // lace is a film of bubbles the water shows through
    const opacity = mix(float(0.6), float(1), smoothstep(0.25, 0.9, amount));
    const foamC = clamp(coverage.mul(smoothstep(0.03, 0.25, amount)).mul(opacity), 0, 1).mul(above).toVar('waterFoam');
    s.foam = foamC;
    // dense foam is bright; thin lace and bubble rims pick up a little water tint
    const fine = mix(fA.y, fB.y, 0.5);
    s.foamHeight = mix(fA.z, fB.z, 0.5);
    // bubbly relief: clumps catch the light, the gaps between them are shaded
    const cavity = mix(float(0.7), float(1.04), s.foamHeight);
    s.foamAlbedo = mix(vec3(0.62, 0.74, 0.76), vec3(0.93, 0.95, 0.96), clamp(order.mul(0.7).add(fine.mul(0.3)).add(amount.mul(0.2)), 0, 1)).mul(cavity);

    // ---- view fresnel
    const NdotV = dot(nWorld, vWorld).max(1e-4);
    const Fview = select(frontFacing, fresnelExact(NdotV, IOR), fresnelExact(NdotV, 1 / IOR)).toVar('waterF');
    s.Fview = Fview;
    s.Tview = Fview.oneMinus();

    // ---- water column optics
    // beam attenuation c = a + b governs what we see *through* the water;
    // the colour of the water body itself comes from backscatter b_b
    // (Gordon et al.: R_rs ~ 0.095 b_b / (a + b_b)).
    // bubbles mixed down under foam: the water loses clarity and the bubble
    // cloud scatters light back out, a pale aqua halo round whitecaps and bores
    const aer = smoothstep(0.05, 1.0, amount).mul(above);
    const a = env.waterAbsorption;
    const c = a.add(env.waterScattering).add(aer.mul(0.9));
    const bb = env.waterBackscatter.add(env.particleBackscatter).add(aer.mul(0.01));
    s.c = c;
    s.aer = aer;
    s.bubbleColor = vec3(0.5, 0.82, 0.8).mul(0.3 / Math.PI);
    const tDir = refract(vWorld.negate(), nUp, 1 / IOR);
    const muView = abs(tDir.y).max(0.05);
    const sunW = env.sunDir;
    const muSun = sqrt(float(1).sub(float(1).sub(sunW.y.mul(sunW.y)).div(IOR * IOR))).max(0.2);
    const rrs = bb.div(a.add(bb)).mul(0.095);
    // grazing views look through a shallower slab of lit water: slightly brighter
    const angular = muView.mul(-0.35).add(1.15);
    s.scatterResponse = rrs.mul(angular).mul(float(1).div(muSun).mul(0.5).add(0.5));
    s.ambientScatter = rrs.mul(env.skyIrradiance).mul(angular);
    // crest thickness proxy for SSS (thin breaking lips glow strongly)
    let crest = clamp(this.vHeight.mul(0.45).add(0.25), 0, 1);
    // the lip is only translucent where it's genuinely thin: vary it along
    // the crest so a breaking line doesn't glow as one uniform band
    if (v.thin) crest = crest.add(v.thin.mul(0.7).mul(vnoise2(xz.mul(0.06).add(env.time.mul(0.05))).mul(0.5).add(0.5).mul(0.8).add(0.2)));
    s.crest = crest.mul(this.sssStrength);
    s.sssColor = vec3(0.07, 0.5, 0.42).mul(0.12);
    s.transmitDir = refract(vWorld.negate(), nUp.negate(), IOR); // underwater looking up
    s.tDir = tDir;
    this.shared = s;
    this._refraction(s);
    return s;
  }

  setupLighting(builder) {
    if (builder.context.prepass === true) return vec3(0);
    const s = this._setupShared(builder);
    const lit = super.setupLighting(builder);
    // debug views: 1 breaker state (beta, shore foam, thin sheet),
    // 2 facing (above, front face, break zone)
    if (this.debugShore === 1 && this.v.debug) return this.v.debug.mul(3);
    if (this.debugShore === 2) return vec3(s.above, select(frontFacing, float(1), float(0)), this.v.breakZone ?? float(0));
    return lit.add(this._indirect(builder, s));
  }

  _indirect(builder, s) {
    const above = s.above;
    const sky = this.sky;
    // ------------------------------------------------ reflection
    const R = reflect(s.vWorld.negate(), s.nWorld).toVar('waterR');
    // rays that dip below the horizon land on other waves, which at that
    // grazing angle mirror the sky themselves: weight the water body by
    // their Fresnel (grazing -> sky, steep -> body) instead of going dark,
    // which would draw black seams along silhouetted crests
    const Rm = normalize(vec3(R.x, max(abs(R.y), 0.004), R.z));
    const lod = clamp(log2(s.alpha.mul(1400)), 0, 7);
    const skyRefl = sky.sample(Rm, lod).rgb;
    const Fsec = select(R.y.lessThan(0), fresnelExact(clamp(R.y.negate(), 1e-3, 1), IOR), float(1));
    // what those rays find: the sun- and sky-lit body of another wave
    const deepCol = s.ambientScatter.mul(1.2).add(env.sunColor.mul(s.scatterResponse).mul(0.6));
    let refl = mix(deepCol, skyRefl, Fsec).toVar('waterRefl');
    // screen-space reflections of local geometry (boat, pier, rocks)
    const ssr = this._ssr(R);
    refl.assign(mix(refl, ssr.rgb, ssr.a));

    // ------------------------------------------------ refraction (above)
    const refr = s.refracted;

    // ------------------------------------------------ assemble
    const noFoam = s.foam.oneMinus();
    const Fv = s.Fview;
    const aboveCol = refl.mul(Fv).add(refr.mul(Fv.oneMinus())).mul(noFoam)
      .add(s.foamAlbedo.mul(env.skyIrradiance).mul(1 / Math.PI).mul(s.foam));

    // ------------------------------------------------ underwater side
    const T = s.transmitDir;
    const tir = dot(T, T).lessThan(0.5);
    const through = sky.sample(normalize(vec3(T.x, max(T.y, 0.01), T.z)), float(1)).rgb;
    const scrUnder = this._underRefraction(s);
    const window = mix(through, scrUnder.rgb, scrUnder.a);
    const infScatter = s.ambientScatter.add(env.sunColor.mul(s.scatterResponse)).mul(2.5);
    const belowCol = select(tir, infScatter.mul(1.2), window.mul(s.Tview).add(infScatter.mul(s.Fview)));
    return mix(belowCol, aboveCol, above);
  }

  // depth-checked refraction of the scene below the surface
  _refraction(s) {
    const depthTex = viewportDepthTexture();
    const surfZ = positionView.z.negate();
    const sceneZ = linearDepthAt(screenUV);
    const thickness = max(sceneZ.sub(surfZ), 0);
    // bend the lookup with the surface normal; strength grows with thickness
    const nV = s.nView;
    const bend = clamp(thickness.mul(0.12), 0, 0.9).mul(0.06);
    const offs = nV.xy.mul(bend).mul(vec2(1, -1)).div(max(surfZ.mul(0.02), 1));
    const uv2 = screenUV.add(offs);
    const sceneZ2 = linearDepthAt(uv2);
    // reject samples that land on something in front of the water
    const valid = sceneZ2.greaterThan(surfZ.add(0.05));
    const uvR = select(valid, uv2, screenUV);
    const zR = select(valid, sceneZ2, sceneZ);
    const scene = viewportSharedTexture(uvR).rgb;
    // path length inside the water (refracted view ray)
    let pathLen = max(zR.sub(surfZ), 0).mul(float(1).div(max(abs(s.tDir.y).mul(0.6).add(0.4), 0.2)));
    let scene2 = scene;
    if (this.v.thin) {
      // thin breaking lip / crest: we look through a sheet of water at the sky
      // and the wave behind it, not down to the seabed
      const thin = clamp(this.v.thin, 0, 1);
      pathLen = mix(pathLen, float(0.35), thin);
      const behind = this.sky.sample(normalize(vec3(s.vWorld.x.negate(), max(s.vWorld.y.negate(), 0.05), s.vWorld.z.negate())), float(2)).rgb;
      scene2 = mix(scene, behind.mul(vec3(0.25, 0.5, 0.45)), thin);
    }
    const Tpath = exp(s.c.negate().mul(pathLen)).toVar('waterTpath');
    s.bodyOpacity = Tpath.oneMinus();
    // sky-lit part of the body colour here; the sun part is a direct light
    s.refracted = scene2.mul(Tpath).add(s.ambientScatter.mul(s.bodyOpacity)).add(env.skyIrradiance.mul(s.bubbleColor).mul(s.aer)).toVar('waterRefr');
  }

  // looking up from below: objects above the water through the window
  _underRefraction(s) {
    const surfZ = positionView.z.negate();
    const offs = s.nView.xy.mul(0.05).mul(vec2(1, -1));
    const uv2 = screenUV.add(offs);
    const z2 = linearDepthAt(uv2);
    const valid = z2.greaterThan(surfZ.add(0.1)).and(z2.lessThan(cameraFar.mul(0.95)));
    const col = viewportSharedTexture(select(valid, uv2, screenUV)).rgb;
    return vec4(col, select(valid, float(1), float(0)));
  }

  // screen-space reflection march (view space)
  _ssr(Rworld) {
    const out = vec4(0).toVar('ssrOut');
    If(this.ssrEnabled.greaterThan(0.5).and(frontFacing), () => {
      const Rv = normalize(cameraViewMatrix.mul(vec4(Rworld, 0)).xyz);
      const p0 = positionView.xyz;
      const stepLen = float(0.35).add(p0.z.negate().mul(0.02)).toVar();
      const p = p0.add(Rv.mul(stepLen.mul(0.5))).toVar();
      const hit = float(0).toVar();
      const hitUV = vec2(0).toVar();
      Loop(18, () => {
        p.addAssign(Rv.mul(stepLen));
        stepLen.mulAssign(1.18);
        const clip = cameraProjectionMatrix.mul(vec4(p, 1));
        const ndc = clip.xy.div(clip.w);
        const uv = vec2(ndc.x.mul(0.5).add(0.5), ndc.y.mul(-0.5).add(0.5));
        If(uv.x.lessThan(0).or(uv.x.greaterThan(1)).or(uv.y.lessThan(0)).or(uv.y.greaterThan(1)).or(p.z.greaterThan(-0.05)), () => { Break(); });
        const sceneZ = linearDepthAt(uv);
        const rayZ = p.z.negate();
        const diff = rayZ.sub(sceneZ);
        If(diff.greaterThan(0).and(diff.lessThan(stepLen.mul(1.5).add(0.3))), () => {
          // the opaque depth also holds whatever is under the water (the
          // submerged part of a pile seen through the surface): the
          // reflected ray can't see that, keep marching past it
          const seen = this.preDepth
            ? perspectiveDepthToViewZ(this.preDepth.sample(uv).r, cameraNear, cameraFar).negate().greaterThan(sceneZ.sub(0.15))
            : null;
          If(seen ?? float(1).greaterThan(0), () => {
            hit.assign(1);
            hitUV.assign(uv);
            Break();
          });
        });
      });
      If(hit.greaterThan(0.5), () => {
        const edge = smoothstep(0.0, 0.08, hitUV.x).mul(smoothstep(1.0, 0.92, hitUV.x)).mul(smoothstep(0.0, 0.08, hitUV.y)).mul(smoothstep(1.0, 0.9, hitUV.y));
        const col = viewportSharedTexture(hitUV).rgb;
        out.assign(vec4(col, edge.mul(smoothstep(-0.02, 0.12, Rworld.y))));
      });
    });
    return out;
  }
}

// linear view depth of the opaque scene at a screen uv (copied depth buffer)
export function linearDepthAt(uv) {
  const d = viewportDepthTexture(uv).r;
  return perspectiveDepthToViewZ(d, cameraNear, cameraFar).negate();
}
