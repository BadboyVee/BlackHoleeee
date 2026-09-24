// Terrain renderer: CDLOD patches over the island heightfield.
//
// Heights come from the island data texture (height, shore SDF, shore dir).
// Close to the camera the vertex shader adds procedural micro relief (sand
// ripples, rock knobs) so silhouettes and contact with props stay organic.

import * as THREE from 'three/webgpu';
import {
  Fn, attribute, positionGeometry, cameraPosition, uniform, vec2, vec3, vec4, float, fract, clamp,
  length, texture, varying, normalize, mix, smoothstep, max, min, abs, dot, positionWorld, transformNormalToView,
  int, select,
} from 'three/tsl';
import { createPatchGeometry, PatchSelector } from '../ocean/oceanMesh.js';
import { WORLD } from './island.js';
import { standard, staticVelocity } from '../render/materials.js';
import { fbm2, gnoise2, vnoise2 } from '../render/tslnoise.js';
import { TERRAIN_TILE } from './terrainTextures.js';

export class Terrain {
  constructor(island) {
    this.island = island;
    this.dataTexture = makeHalfDataTexture(island);
    this.auxTexture = makeAuxTexture(island);
    this.geometry = createPatchGeometry('terrainPatch');
    const S = WORLD.size;
    this.selector = new PatchSelector(this.geometry, {
      attrName: 'terrainPatch', leafSize: 6.25, levels: 9, rangeFactor: 2.6,
      bounds: { x0: WORLD.originX, z0: WORLD.originZ, x1: WORLD.originX + S, z1: WORLD.originZ + S },
      minHeight: -75, maxHeight: 105,
    });
    this._buildMinMax();
    this.selector.heightRange = (x, z, size) => this.rangeFor(x, z, size);
    // TSL accessors shared with the water
    this.origin = vec2(WORLD.originX, WORLD.originZ);
    this.invSize = float(1 / WORLD.size);
    this.material = this._buildMaterial();
    this.mesh = new THREE.Mesh(this.geometry, this.material);
    this.mesh.frustumCulled = false;
    this.mesh.receiveShadow = true;
    this.mesh.castShadow = true;
    this.mesh.name = 'terrain';
  }

  /** TSL: world xz -> data texel (height, sdf, dirX, dirZ) */
  sample(xz) {
    return texture(this.dataTexture, xz.sub(this.origin).mul(this.invSize));
  }
  sampleLevel(xz) {
    return texture(this.dataTexture, xz.sub(this.origin).mul(this.invSize)).level(0);
  }
  /** TSL: world xz -> baked maps (drainage, erosion, sky visibility, tree cover), 0..1 each */
  sampleAux(xz, level = null) {
    const t = texture(this.auxTexture, xz.sub(this.origin).mul(this.invSize));
    return level === null ? t : t.level(level);
  }

  _buildMinMax() {
    // min/max pyramid for tight LOD bounds
    const N = WORLD.res;
    const levels = [];
    let size = N, mn = new Float32Array(N * N), mx = new Float32Array(N * N);
    mn.set(this.island.height); mx.set(this.island.height);
    levels.push({ size, mn, mx });
    while (size > 1) {
      const ns = size >> 1;
      const nmn = new Float32Array(ns * ns), nmx = new Float32Array(ns * ns);
      for (let j = 0; j < ns; j++) for (let i = 0; i < ns; i++) {
        let a = Infinity, b = -Infinity;
        for (let dj = 0; dj < 2; dj++) for (let di = 0; di < 2; di++) {
          const k = (j * 2 + dj) * size + (i * 2 + di);
          a = Math.min(a, mn[k]); b = Math.max(b, mx[k]);
        }
        nmn[j * ns + i] = a; nmx[j * ns + i] = b;
      }
      size = ns; mn = nmn; mx = nmx;
      levels.push({ size, mn, mx });
    }
    this.minmax = levels;
  }

  rangeFor(x, z, size) {
    const texels = size / (WORLD.size / WORLD.res);
    let lvl = Math.max(0, Math.min(this.minmax.length - 1, Math.ceil(Math.log2(Math.max(texels, 1)))));
    const L = this.minmax[lvl];
    const cell = WORLD.size / L.size;
    const i0 = Math.floor((x - WORLD.originX) / cell), j0 = Math.floor((z - WORLD.originZ) / cell);
    const i1 = Math.floor((x + size - WORLD.originX) / cell), j1 = Math.floor((z + size - WORLD.originZ) / cell);
    let a = Infinity, b = -Infinity;
    for (let j = j0; j <= j1; j++) for (let i = i0; i <= i1; i++) {
      if (i < 0 || j < 0 || i >= L.size || j >= L.size) { a = Math.min(a, WORLD.deep); b = Math.max(b, WORLD.deep); continue; }
      a = Math.min(a, L.mn[j * L.size + i]); b = Math.max(b, L.mx[j * L.size + i]);
    }
    return [a - 0.5, b + 0.8];
  }

  /** TSL: close-range micro relief added to the heightfield */
  microRelief(xz, height, weight) {
    // under water: wave-formed ripples; dry sand: faint, irregular wind
    // ripples in patches (their direction wanders), plus gentle lumps
    const warp = vec2(gnoise2(xz.mul(0.05)), gnoise2(xz.mul(0.05).add(7.3))).mul(6.0);
    const q = xz.add(warp);
    const wave = gnoise2(q.mul(vec2(0.9, 2.6))).mul(0.018);
    const wind = gnoise2(q.mul(vec2(1.6, 5.5))).mul(0.005).mul(smoothstep(0.1, 0.55, gnoise2(xz.mul(0.09)).mul(0.5).add(0.5)));
    const submerged = smoothstep(-0.2, -0.9, height);
    const ripple = mix(wind, wave, submerged).add(gnoise2(xz.mul(0.35)).mul(0.03));
    const lumps = fbm2(xz.mul(0.12), 3).mul(0.1);
    return ripple.add(lumps).mul(weight);
  }

  _buildMaterial() {
    const mat = staticVelocity(standard({ roughness: 0.9, metalness: 0 }));
    mat.name = 'terrain';
    const patch = attribute('terrainPatch', 'vec4');
    const g = positionGeometry.xz;
    const origin = patch.xy, spacing = patch.z, morphEnd = patch.w;
    const world0 = origin.add(g.mul(spacing));
    const d0 = this.sampleLevel(world0).x;
    const dist = length(vec3(world0.x, d0, world0.y).sub(cameraPosition));
    const morphK = clamp(dist.sub(morphEnd.mul(0.62)).div(morphEnd.mul(0.34)), 0, 1);
    const odd = fract(g.mul(0.5)).mul(2);
    const xz = origin.add(g.sub(odd.mul(morphK)).mul(spacing));
    const data = this.sampleLevel(xz);
    // the wave-washed beach face stays smooth (and matches the swash sheet)
    const washed = smoothstep(-9, -3, data.y).mul(smoothstep(2.6, 1.8, data.x));
    const detailW = smoothstep(60, 12, dist).mul(washed.oneMinus());
    const h = data.x.add(this.microRelief(xz, data.x, detailW));
    mat.positionNode = vec3(xz.x, h, xz.y);
    this.vXZ = varying(xz, 'vTerrainXZ');
    // the baked maps are smooth (1.6 m texels): fetch them per vertex, which
    // also keeps the fragment stage under its 16 sampled-texture limit
    this.vAux = varying(this.sampleAux(xz, 0), 'vTerrainAux');
    this.material = mat;
    return mat;
  }

  /** Attach baked textures + shoreline effects (called once textures exist). */
  setupShading({ textures, shore, foamTexture, time }) {
    const mat = this.material;
    const vXZ = this.vXZ;
    const e = WORLD.size / WORLD.res;
    const dC = this.sample(vXZ);
    const hL = this.sample(vXZ.sub(vec2(e, 0))).x, hR = this.sample(vXZ.add(vec2(e, 0))).x;
    const hD = this.sample(vXZ.sub(vec2(0, e))).x, hU = this.sample(vXZ.add(vec2(0, e))).x;
    const nBase = normalize(vec3(hL.sub(hR), e * 2, hD.sub(hU)));
    const slope = float(1).sub(nBase.y);
    const hh = positionWorld.y;
    const sdf = dC.y;

    // --- baked maps: where water gathers, what erosion did, how much sky
    // the ground sees, where the trees stand
    const aux = this.vAux;
    const drain = aux.r.mul(255 / 12);                        // log2 catchment (texels)
    const moist = smoothstep(3.5, 10.0, drain);
    const eroded = aux.g.mul(255).sub(128).div(6);            // m, + laid down / - removed
    const skyVis = aux.b;
    const forestCov = aux.a;

    // --- material weights
    const n1 = fbm2(vXZ.mul(0.018), 3).mul(0.5).add(0.5);
    const n2 = fbm2(vXZ.mul(0.06).add(17.3), 3).mul(0.5).add(0.5);
    const beachZone = smoothstep(-75, -45, sdf).mul(smoothstep(5.0, 3.2, hh)).max(smoothstep(0.4, -0.4, hh));
    // rock: faces too steep to hold soil, the scoured walls of the deepest
    // gullies, crags on the summits and outcrops breaking through slopes
    const steep = smoothstep(0.27, 0.4, slope);
    const scour = smoothstep(-4.0, -8.0, eroded).mul(smoothstep(0.12, 0.22, slope));
    const crag = smoothstep(96, 108, hh).mul(smoothstep(0.1, 0.2, slope));
    const outcrop = smoothstep(0.64, 0.74, n2).mul(smoothstep(0.14, 0.24, slope)).mul(forestCov.mul(0.6).oneMinus());
    let wRock = max(max(steep, scour.mul(0.85)), max(crag, outcrop));
    wRock = wRock.max(smoothstep(-0.3, -3.5, hh).mul(smoothstep(0.55, 0.75, n1)).mul(0.9));   // rocky seabed patches
    const wPeb = smoothstep(0.66, 0.78, n2).mul(beachZone).mul(smoothstep(0.05, 0.14, slope).max(smoothstep(-30, -18, sdf).mul(smoothstep(0.7, 0.85, n1)))).mul(0.9);
    const wSand = beachZone.mul(wRock.oneMinus());
    const inland = beachZone.oneMinus().mul(wRock.oneMinus());
    // bare soil where slopes are too steep and dry for turf (landslip scars),
    // on fresh deposits at the foot of gullies, and along the forest edge
    const scar = smoothstep(0.17, 0.26, slope).mul(moist.oneMinus()).mul(smoothstep(0.55, 0.7, n1.add(n2.mul(0.3))));
    const fan = smoothstep(0.8, 2.5, eroded).mul(0.7);
    const wSoil = inland.mul(max(scar, fan)).mul(forestCov.mul(0.7).oneMinus());
    // under the canopy: leaf litter; the rest is turf
    const wForest = inland.mul(forestCov).mul(wSoil.oneMinus());
    const wGrass = inland.mul(forestCov.oneMinus()).mul(wSoil.oneMinus());
    const W = [wSand.mul(wPeb.oneMinus()), wRock, wGrass, wForest, wPeb, wSoil];
    // top-2 layers (pure expressions: this graph is built outside any Fn)
    let bestW = float(-1), bestL = int(0), secW = float(-1), secL = int(0);
    W.forEach((w, i) => {
      const better = w.greaterThan(bestW);
      const second = w.greaterThan(secW);
      const nSecW = select(better, bestW, select(second, w, secW));
      const nSecL = select(better, bestL, select(second, int(i), secL));
      bestW = select(better, w, bestW);
      bestL = select(better, int(i), bestL);
      secW = nSecW; secL = nSecL;
    });
    const tileOf = (l) => TERRAIN_TILE.slice(0, -1).reduceRight((acc, t, i) => select(l.equal(int(i)), float(t), acc), float(TERRAIN_TILE[TERRAIN_TILE.length - 1]));
    // biplanar for cliffs: side projection where steep
    const sideUV = select(abs(nBase.x).greaterThan(abs(nBase.z)), vec2(positionWorld.z, positionWorld.y.negate()), vec2(positionWorld.x, positionWorld.y.negate()));
    const useSide = steep.greaterThan(0.5);
    const anti = smoothstep(0.35, 0.65, vnoise2(vXZ.mul(0.11)));
    const sampleLayer = (L) => {
      const tile = tileOf(L);
      const baseUV = select(useSide.and(L.equal(int(1))), sideUV, vXZ);
      const uv1 = baseUV.div(tile);
      const c = 0.8, sn = 0.6;
      const uv2 = vec2(baseUV.x.mul(c).sub(baseUV.y.mul(sn)), baseUV.x.mul(sn).add(baseUV.y.mul(c))).div(tile.mul(1.23)).add(0.37);
      const li = L;
      const a1 = texture(textures.albedo, uv1).depth(li), a2 = texture(textures.albedo, uv2).depth(li);
      const m1 = texture(textures.normal, uv1).depth(li), m2 = texture(textures.normal, uv2).depth(li);
      // rotate the second normal back into the first frame
      const n2x = m2.x.mul(2).sub(1), n2y = m2.y.mul(2).sub(1);
      const n2r = vec2(n2x.mul(c).add(n2y.mul(sn)), n2y.mul(c).sub(n2x.mul(sn)));
      const nrm = mix(vec2(m1.x.mul(2).sub(1), m1.y.mul(2).sub(1)), n2r, anti);
      return { albedo: mix(a1.rgb, a2.rgb, anti), rough: mix(a1.a, a2.a, anti), n: nrm, height: mix(m1.z, m2.z, anti), ao: mix(m1.w, m2.w, anti) };
    };
    const A = sampleLayer(bestL), B = sampleLayer(secL);
    // height-aware blend between the two layers
    const wa = bestW.max(1e-3), wb = secW.max(0);
    const hb = clamp(wa.sub(wb).mul(2.2).add(A.height.sub(B.height).mul(0.6)).add(0.5), 0, 1);
    let albedo = mix(B.albedo, A.albedo, hb);
    let rough = mix(B.rough, A.rough, hb);
    const nT = mix(B.n, A.n, hb);
    const ao = mix(B.ao, A.ao, hb);
    // macro variation hides any remaining repetition
    const macro = fbm2(vXZ.mul(0.004), 4).mul(0.5).add(0.5);
    albedo = albedo.mul(mix(0.82, 1.12, macro)).mul(mix(vec3(1.0, 0.97, 0.93), vec3(0.95, 1.0, 1.03), n1));
    // turf follows the water: deep green in damp hollows, sun-bleached and
    // yellower on dry, exposed ridges; leaf litter lies in the canopy's shade
    const grassShare = wGrass.div(wa.add(wb).max(1e-3)).mul(select(bestL.equal(int(2)).or(secL.equal(int(2))), float(1), float(0)));
    const dryness = moist.oneMinus().mul(smoothstep(0.93, 0.99, skyVis)).mul(smoothstep(0.35, 0.7, n1.add(macro.mul(0.4)).sub(0.2)));
    const lush = vec3(0.78, 1.05, 0.72), dry = vec3(1.35, 1.12, 0.72);
    const grassTint = mix(mix(vec3(1), lush, moist.mul(0.9)), dry, dryness.mul(0.85));
    albedo = albedo.mul(mix(vec3(1), grassTint, grassShare));
    // far away the canopy's shade stands in for tree shadows the far
    // cascade cannot resolve; up close the real shadows do it
    // (and from afar the gaps between crowns show shaded undergrowth, not litter)
    const farShade = smoothstep(45, 110, length(positionWorld.sub(cameraPosition)));
    const under = forestCov.mul(inland).mul(farShade);
    albedo = mix(albedo, vec3(0.028, 0.045, 0.018).mul(mix(0.8, 1.2, macro)), under.mul(0.85));

    // --- shoreline: wet sand, swash film, rounded leading edge, foam
    const t = time;
    const st = shore.state(vXZ, t, true);
    const sw = shore.swash(st, t);
    const d = sdf.negate();
    const belowMSL = smoothstep(0.25, -0.15, hh);
    const wet = clamp(max(sw.wet, belowMSL), 0, 1).mul(beachZone.max(smoothstep(0.5, -0.5, hh)));
    const film = smoothstep(0.0, 0.004, sw.thick).mul(smoothstep(-2, 0.5, d));
    // leading edge: a thin rounded meniscus that catches the light, and a dark contact line in front of it
    const toEdge = sw.edge.sub(d);                         // >0 inside the water
    const rim = smoothstep(0.0, 0.03, toEdge).mul(smoothstep(0.14, 0.03, toEdge)).mul(smoothstep(0.02, 0.2, sw.hb)).mul(film.max(0.3));
    const contact = smoothstep(-0.09, -0.01, toEdge).mul(smoothstep(0.01, -0.01, toEdge)).mul(smoothstep(0.02, 0.2, sw.hb));
    albedo = albedo.mul(mix(float(1), 0.52, wet));
    albedo = albedo.mul(mix(float(1), 0.82, film)).mul(mix(vec3(1), vec3(0.8, 0.93, 0.95), film));
    albedo = albedo.mul(float(1).sub(contact.mul(0.35)));
    rough = mix(rough, 0.32, wet);
    rough = mix(rough, 0.05, film);
    // swash foam + foam stranded on the sand as the water drains
    const fA = texture(foamTexture, vXZ.div(3.1));
    const fB = texture(foamTexture, vec2(vXZ.x.mul(0.8).sub(vXZ.y.mul(0.6)), vXZ.x.mul(0.6).add(vXZ.y.mul(0.8))).div(4.7).add(0.37));
    const order = max(fA.x, fB.x.mul(0.92));
    const foamAmt = max(sw.foam.mul(film), sw.stranded.mul(0.7));
    const foamCov = smoothstep(float(1).sub(foamAmt), float(1.18).sub(foamAmt), order).mul(smoothstep(0.03, 0.2, foamAmt));
    albedo = mix(albedo, vec3(0.86, 0.9, 0.9).mul(mix(0.85, 1.0, fA.y)), foamCov);
    rough = mix(rough, 0.55, foamCov);
    // fully submerged: no air/water film on the grains, so no sheen - the
    // sand-to-water index contrast is tiny and the surface reads as matte
    const submerged = smoothstep(-0.25, -0.9, hh);
    rough = mix(rough, 0.95, submerged);

    // --- normal: base heightfield + detail (flattened under water film)
    const T = normalize(vec3(nBase.y, nBase.x.negate(), 0));
    const Bv = normalize(nBase.cross(T));
    const detailK = mix(float(1.0), 0.25, film).mul(mix(float(1), 0.6, wet));
    let nW = normalize(nBase.add(T.mul(nT.x.mul(detailK))).add(Bv.mul(nT.y.mul(detailK).negate())));
    // rounded meniscus: tilt towards the sea at the edge
    const sea3 = vec3(st.dir.x, 0, st.dir.y);
    nW = normalize(nW.add(sea3.mul(rim.mul(1.6))).add(vec3(0, rim.mul(0.4), 0)));

    mat.colorNode = albedo;
    mat.roughnessNode = rough;
    // cavity AO from the texture, terrain-scale sky visibility from the bake
    mat.aoNode = ao.mul(mix(float(0.3), float(1), skyVis.pow(1.5)));
    mat.normalNode = transformNormalToView(nW);
    this.wetness = wet;
  }

  update(camera) {
    this.selector.update(camera, 2);
  }
}

// drainage, erosion, sky visibility, tree cover (see islandData.js)
function makeAuxTexture(island) {
  const N = WORLD.res;
  const t = new THREE.DataTexture(island.aux, N, N, THREE.RGBAFormat, THREE.UnsignedByteType);
  t.magFilter = THREE.LinearFilter;
  t.minFilter = THREE.LinearMipmapLinearFilter;
  t.wrapS = t.wrapT = THREE.ClampToEdgeWrapping;
  t.generateMipmaps = true;
  t.needsUpdate = true;
  t.name = 'island.aux';
  return t;
}

function makeHalfDataTexture(island) {
  const N = WORLD.res;
  const data = new Uint16Array(N * N * 4);
  const toHalf = THREE.DataUtils.toHalfFloat;
  for (let i = 0; i < N * N; i++) {
    data[i * 4] = toHalf(island.height[i]);
    data[i * 4 + 1] = toHalf(Math.max(-2000, Math.min(2000, island.sdf[i])));
    data[i * 4 + 2] = toHalf(island.shoreDir[i * 2]);
    data[i * 4 + 3] = toHalf(island.shoreDir[i * 2 + 1]);
  }
  const t = new THREE.DataTexture(data, N, N, THREE.RGBAFormat, THREE.HalfFloatType);
  t.magFilter = THREE.LinearFilter;
  t.minFilter = THREE.LinearFilter;
  t.wrapS = t.wrapT = THREE.ClampToEdgeWrapping;
  t.generateMipmaps = false;
  t.needsUpdate = true;
  t.name = 'island.data';
  return t;
}
