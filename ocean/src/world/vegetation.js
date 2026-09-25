// Vegetation: tropical canopy trees, umbrella (Terminalia-like) trees,
// ironwoods, coconut palms, shrubs and ferns, modelled in Blender
// (tools/blender/trees.py, leaves.py, impostors.py) and loaded from
// assets/vegetation.
//
// Each variant has two mesh LODs and the trees an octahedral impostor for
// the distance, so whole hillsides can be wooded. Instances cross-fade
// between LODs with an ordered dither whose threshold ranges partition
// [0, 1): every pixel is drawn by exactly one LOD, with no pop and no holes.
//
// Wind bends each plant by the flexibility painted into its vertices (stiff
// roots, loose twig tips), per scaffold limb out of phase; cards flutter.
// Leaves darken deep in the crown and let backlight through.

import * as THREE from 'three/webgpu';
import {
  attribute, positionGeometry, normalGeometry, positionWorld, vec2, vec3, vec4, float, cameraProjectionMatrix, cameraViewMatrix, sin, cos, mix, smoothstep,
  clamp, max, dot, normalize, cross, screenCoordinate, floor, fract, uniform, texture, uv, cameraPosition, pow,
  select, length, abs, mod, log2, dFdx, dFdy, varying, transformNormalToView, normalMap, sqrt, normalWorld,
} from 'three/tsl';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { DRACOLoader } from 'three/addons/loaders/DRACOLoader.js';
import { standard, deform, staticVelocity } from '../render/materials.js';
import { fbm2, vnoise2 } from '../render/tslnoise.js';
import { env } from '../env.js';
import { assetURL, dracoDecoderPath } from '../core/assets.js';
import { VILLAGE } from './island.js';

const asset = (name) => assetURL('assets/vegetation/' + name);
// where main.js puts the player on the beach (kept clear of plants)
const SPAWN = { x: 72, z: -3 };

// distances (m): mesh LOD0 until `near`, LOD1 until `mid`, then the
// impostor (trees) or a fade-out by `far` (undergrowth); saplings are small
// enough that the reduced mesh does from the start
const SPECIES = {
  broad: { atlas: 'leaves_broad', near: 38, mid: 105, far: 1500, impostor: true, rad: 4.2, trunk: 0.34, bark: [0.2, 0.17, 0.14], flutter: 0.035, H: 13 },
  umbrella: { atlas: 'leaves_broad', near: 42, mid: 115, far: 1500, impostor: true, rad: 5.2, trunk: 0.3, bark: [0.23, 0.19, 0.15], flutter: 0.035, H: 11 },
  ironwood: { atlas: 'leaves_needle', near: 38, mid: 105, far: 1500, impostor: true, rad: 2.8, trunk: 0.22, bark: [0.16, 0.12, 0.09], flutter: 0.05, H: 14 },
  palm: { atlas: 'frond_palm', near: 55, mid: 140, far: 1500, impostor: true, rad: 2.6, trunk: 0.2, bark: [0.3, 0.27, 0.22], flutter: 0.06, H: 10 },
  sapling: { model: 'broad', atlas: 'leaves_broad', near: 0.001, mid: 55, far: 700, impostor: true, rad: 1.6, trunk: 0.1, bark: [0.2, 0.17, 0.14], flutter: 0.04, H: 5 },
  shrub: { atlas: 'leaves_shrub', near: 28, mid: 75, far: 130, impostor: false, rad: 1.3, bark: [0.13, 0.1, 0.07], flutter: 0.04, H: 2 },
  fern: { atlas: 'frond_fern', near: 20, mid: 42, far: 58, impostor: false, rad: 0.8, bark: [0.1, 0.1, 0.05], flutter: 0.05, H: 0.9 },
};

const rndGen = (seed) => () => { seed |= 0; seed = seed + 0x6D2B79F5 | 0; let t = Math.imul(seed ^ seed >>> 15, 1 | seed); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; };
const smoothstepJS = (a, b, x) => { const t = Math.min(Math.max((x - a) / (b - a), 0), 1); return t * t * (3 - 2 * t); };

// ------------------------------------------------------------------ assets
async function loadAssets() {
  const json = async (n) => (await fetch(asset(n))).json();
  const [plants, atlases, impostors] = await Promise.all([json('plants.json'), json('atlases.json'), json('impostors.json')]);
  const texLoader = new THREE.TextureLoader();
  const tex = async (name, srgb) => {
    const t = await texLoader.loadAsync(asset(name));
    t.colorSpace = srgb ? THREE.SRGBColorSpace : THREE.NoColorSpace;
    t.flipY = false;                 // glTF UV convention (v = 0 at the top)
    t.wrapS = t.wrapT = THREE.ClampToEdgeWrapping;
    t.minFilter = THREE.LinearMipmapLinearFilter;
    t.generateMipmaps = true;
    t.anisotropy = 8;
    t.name = name;
    return t;
  };
  const draco = new DRACOLoader();
  draco.setDecoderPath(dracoDecoderPath());
  const gltf = await new GLTFLoader().setDRACOLoader(draco).loadAsync(asset('plants.glb'));
  draco.dispose();
  const geoms = {};
  gltf.scene.traverse((o) => { if (o.isMesh) geoms[o.name] = o.geometry; });
  const leafTex = {};
  await Promise.all([...new Set(Object.values(SPECIES).map((s) => s.atlas))].map(async (a) => {
    leafTex[a] = { c: await tex(`${a}_c.webp`, true), n: await tex(`${a}_n.webp`, false) };
  }));
  const impTex = {};
  await Promise.all(Object.entries(SPECIES).filter(([sp, cfg]) => cfg.impostor && !cfg.model && impostors[sp]).map(async ([sp]) => {
    impTex[sp] = await Promise.all(impostors[sp].map(async (_, vi) => ({
      c: await tex(`imp_${sp}_${vi}_c.webp`, true), n: await tex(`imp_${sp}_${vi}_n.webp`, false),
    })));
  }));
  return { plants, atlases, impostors, geoms, leafTex, impTex };
}

// ------------------------------------------------------------------ dither
// the pattern shifts every frame so TAA averages cross-fades into a blend
const ditherShift = uniform(new THREE.Vector2());
let ditherFrame = 0;
const BAYER_WALK = [0, 10, 2, 8, 5, 15, 7, 13, 1, 11, 3, 9, 4, 14, 6, 12];

const bayer4 = (p) => {
  const x = mod(floor(p.x), 4), y = mod(floor(p.y), 4);
  const m = [0, 8, 2, 10, 12, 4, 14, 6, 3, 11, 1, 9, 15, 7, 13, 5];
  let v = float(m[15]);
  for (let i = 14; i >= 0; i--) v = select(x.add(y.mul(4)).equal(float(i)), float(m[i]), v);
  return v.add(0.5).div(16);
};
// drawn when the pixel's threshold falls in this LOD's range [lo, hi)
export const inRange = (lo, hi) => {
  const b = bayer4(screenCoordinate.xy.add(ditherShift));
  return b.greaterThanEqual(lo).and(b.lessThan(hi));
};

// ------------------------------------------------------------------ wind
// per instance: vegData = (phase, yaw, lo, hi); per vertex COLOR_0 =
// (flexibility, limb phase, flutter weight, crown occlusion)
function windLocal(H, flutter) {
  const col = attribute('color', 'vec4');
  const data = attribute('vegData', 'vec4');
  const flex = col.x, limb = col.y, flw = col.z;
  const phase = data.x.add(limb.mul(6.283));
  const t = env.time;
  const gust = sin(t.mul(0.31).add(data.x.mul(0.2))).mul(0.35).add(sin(t.mul(0.83).add(data.x)).mul(0.25)).add(0.9);
  const sway = sin(t.mul(1.3).add(phase)).mul(0.35).add(0.65);
  const amp = flex.mul(flex).mul(H * 0.022).mul(gust).mul(sway).mul(env.windSpeed.div(7));
  // the wind in the plant's own frame (instances are yawed)
  const c = cos(data.y), s = sin(data.y);
  const w = env.windDir;
  const wl = vec3(w.x.mul(c).sub(w.y.mul(s)), 0, w.x.mul(s).add(w.y.mul(c)));
  let p = positionGeometry.add(wl.mul(amp)).sub(vec3(0, amp.mul(amp).mul(0.25 / H), 0));
  if (flutter) {
    const f = sin(t.mul(7.1).add(positionGeometry.x.mul(3.1)).add(positionGeometry.z.mul(2.3)).add(phase))
      .mul(flutter).mul(flw).mul(flex.add(0.3)).mul(env.windSpeed.div(7));
    p = p.add(normalGeometry.mul(f));
  }
  return p;
}

// ------------------------------------------------------------------ materials
function barkMaterial(kind) {
  const cfg = SPECIES[kind];
  const m = standard({ roughness: 0.9, metalness: 0 });
  const col = attribute('color', 'vec4');
  const tint = attribute('uv1', 'vec2').x;              // coconut husks
  const q = uv();
  // fissured bark: long vertical plates and cross cracks; palms: leaf-scar rings
  let pattern;
  if (kind === 'palm') {
    const rings = pow(abs(sin(q.y.mul(Math.PI / 0.14))), 8.0);
    pattern = float(0.78).add(fbm2(vec2(q.x.mul(6), q.y.mul(9)), 3).mul(0.18)).sub(rings.mul(0.22));
  } else {
    const plates = fbm2(vec2(q.x.mul(9), q.y.mul(1.6)), 4).mul(0.5).add(0.5);
    const cracks = smoothstep(0.42, 0.5, abs(fract(q.x.mul(5).add(plates.mul(0.9))).sub(0.5)));
    pattern = mix(float(0.55), float(1.05), plates).mul(float(1).sub(cracks.mul(0.4)));
  }
  const base = vec3(...cfg.bark).mul(pattern);
  m.colorNode = mix(base, vec3(0.32, 0.2, 0.09), tint);
  m.aoNode = col.w;
  deform(m, windLocal(cfg.H, 0));
  return m;
}

function leafMaterial(kind, tex) {
  const cfg = SPECIES[kind];
  const m = standard({ roughness: 0.62, metalness: 0, side: THREE.DoubleSide });
  const col = attribute('color', 'vec4');
  const tint = attribute('uv1', 'vec2').x;              // dead fronds
  const c = texture(tex.c);
  const n = texture(tex.n);
  // coverage shrinks in averaged mips: boost alpha with the mip level so
  // distant crowns keep their density (Golus)
  const texel = uv().mul(vec2(tex.c.image.width, tex.c.image.height));
  const mip = max(log2(max(length(dFdx(texel)), length(dFdy(texel)))), 0);
  const alpha = c.a.mul(mip.mul(0.28).add(1));
  const leafCol = c.rgb.mul(mix(float(0.88), float(1.1), vnoise2(positionWorld.xz.mul(0.09)).mul(0.5).add(0.5)));
  m.colorNode = mix(leafCol, vec3(dot(leafCol, vec3(0.3, 0.5, 0.2))).mul(vec3(1.6, 1.15, 0.6)), tint.mul(0.85));
  const nxy = n.xy.mul(2).sub(1);
  m.normalNode = normalMap(vec3(n.x, n.y, sqrt(max(float(1).sub(dot(nxy, nxy)), 0)).mul(0.5).add(0.5)));
  // deep in the crown the sky is hidden by the leaves around
  m.aoNode = col.w.mul(n.z.mul(0.5).add(0.5));
  // thin leaves pass light: seen from the shaded side, a sunlit leaf glows
  // yellow-green (diffuse transmission), brightest looking toward the sun
  const V = normalize(positionWorld.sub(cameraPosition));
  const N = normalWorld;
  const through = max(dot(N, env.sunDir), 0).mul(max(dot(N, V), 0));
  const toSun = pow(max(dot(V, env.sunDir), 0), 4);
  m.emissiveNode = leafCol.mul(vec3(0.95, 1.1, 0.45)).mul(env.sunColor)
    .mul(through.mul(0.4).add(toSun.mul(0.25)).add(0.006)).mul(col.w.mul(col.w));
  m.userData.noContactShadow = true;
  deform(m, windLocal(cfg.H, cfg.flutter));
  return { m, alpha };
}

// lod range (and alpha) mask, for the colour and the shadow pass alike
function applyMask(m, alpha) {
  const data = attribute('vegData', 'vec4');
  const lod = inRange(data.z, data.w);
  m.maskNode = alpha ? lod.and(alpha.greaterThan(0.5)) : lod;
  m.maskShadowNode = m.maskNode;
  return m;
}

// ------------------------------------------------------------------ impostor
// hemi-octahedral impostor (conventions shared with tools/blender/impostors.py)
const hemiOctEncode = (v) => {
  const p = v.xz.div(abs(v.x).add(abs(v.y)).add(abs(v.z)));
  return vec2(p.x.add(p.y), p.x.sub(p.y)).mul(0.5).add(0.5);
};
const hemiOctDecode = (u) => {
  const e = u.mul(2).sub(1);
  const p = vec2(e.x.add(e.y), e.x.sub(e.y)).mul(0.5);
  return normalize(vec3(p.x, float(1).sub(abs(p.x)).sub(abs(p.y)), p.y));
};
const octDecode = (e01) => {
  const e = e01.mul(2).sub(1);
  const y = float(1).sub(abs(e.x)).sub(abs(e.y));
  const t = max(y.negate(), 0);
  const x = e.x.add(select(e.x.greaterThanEqual(0), t.negate(), t));
  const z = e.y.add(select(e.y.greaterThanEqual(0), t.negate(), t));
  return normalize(vec3(x, y, z));
};

function impostorMaterial(tex, meta, frames) {
  const N = frames;
  const m = standard({ roughness: 0.75, metalness: 0 });
  const iPos = attribute('iPos', 'vec4');                // x, y, z, scale
  const iRot = attribute('iRot', 'vec4');                // cos yaw, sin yaw, lo, hi
  const cs = iRot.x, sn = iRot.y, s = iPos.w;
  const C = meta.centre, R = meta.radius;
  // crown centre in the world (tree space -> yaw -> scale)
  const cw = iPos.xyz.add(vec3(float(C[0]).mul(cs).add(float(C[2]).mul(sn)), float(C[1]), float(C[0]).mul(sn).negate().add(float(C[2]).mul(cs))).mul(s));
  const Vw = normalize(cameraPosition.sub(cw));
  const right = normalize(cross(vec3(0, 1, 0), Vw).add(vec3(1e-5, 0, 0)));
  const up = cross(Vw, right);
  const q = positionGeometry.xy;                         // quad corners in [-1, 1]
  // pushed a little toward the eye so slopes do not swallow the lower crown
  // (the real depth is written per pixel below)
  m.positionNode = cw.add(right.mul(q.x.mul(R)).add(up.mul(q.y.mul(R))).mul(s)).add(Vw.mul(R * 0.3).mul(s));
  // without this the velocity pass would take the raw quad corners as last
  // frame's position and TAA would smear every crown toward the world origin
  staticVelocity(m);
  const vC = varying(cw, 'vImpCentre');
  const vW = varying(Vw, 'vImpViewWorld');
  const vRot = varying(vec3(cs, sn, s), 'vImpRot');
  const vLo = varying(iRot.zw, 'vImpRange');
  // world -> tree space (inverse yaw)
  const toLocal = (v, r) => vec3(v.x.mul(r.x).sub(v.z.mul(r.y)), v.y, v.x.mul(r.y).add(v.z.mul(r.x)));
  const Vl = varying(toLocal(Vw, vec3(cs, sn, s)), 'vImpView');
  // (plain expressions: the whole lookup is branch-free)
  const v = normalize(vec3(Vl.x, max(Vl.y, 0.02), Vl.z));
  const g = hemiOctEncode(v).mul(N - 1);
  const base = clamp(floor(g), 0, N - 2);
  const f = clamp(g.sub(base), 0, 1);
  const useX = f.x.greaterThan(f.y);
  const fB = base.add(select(useX, vec2(1, 0), vec2(0, 1)));
  const fC = base.add(vec2(1, 1));
  const wA = select(useX, float(1).sub(f.x), float(1).sub(f.y));
  const wB = select(useX, f.x.sub(f.y), f.y.sub(f.x));
  const wC = select(useX, f.y, f.x);
  // this fragment on the billboard, in tree space
  const P = toLocal(positionWorld.sub(vC), vRot).div(vRot.z);
  const sample = (fr) => {
    const d = hemiOctDecode(fr.div(N - 1));
    const r = normalize(cross(vec3(0, 1, 0), d));
    const u = cross(d, r);
    // project along the frame's own view direction onto its image plane
    const uvF = clamp(vec2(dot(P, r), dot(P, u)).div(R * 2).add(0.5), 0.002, 0.998);
    const at = fr.add(vec2(uvF.x, float(1).sub(uvF.y))).div(N);
    return [texture(tex.c, at), texture(tex.n, at), at];
  };
  const [cA, nA, atA] = sample(base), [cB, nB] = sample(fB), [cC, nC] = sample(fC);
  const r = { col: cA.mul(wA).add(cB.mul(wB)).add(cC.mul(wC)), nrm: nA.mul(wA).add(nB.mul(wB)).add(nC.mul(wC)) };
  const nl = octDecode(r.nrm.xy);
  // tree space -> world (yaw)
  const nw = normalize(vec3(nl.x.mul(vRot.x).add(nl.z.mul(vRot.y)), nl.y, nl.x.mul(vRot.y).negate().add(nl.z.mul(vRot.x))));
  // (the atlas colours are straight, bled into the empty texels)
  const albedo = r.col.rgb;
  // deep foliage is shaded by the leaves around it for the sun as much as
  // for the sky: without it a wood reads as a flat green carpet
  const occl = r.nrm.w;
  m.colorNode = albedo.mul(mix(float(0.3), float(1.05), pow(occl, 1.3)));
  m.normalNode = transformNormalToView(nw);
  m.aoNode = occl.mul(0.5).add(0.5);
  // true surface depth: neighbouring crowns intersect instead of stacking,
  // and the shadow pass sees the rounded crown (self-shadowing)
  const depth01 = r.nrm.z;
  const surface = positionWorld.sub(vW.mul(R * 0.3).mul(vRot.z)).add(vW.mul(depth01.sub(0.5).mul(R * 2)).mul(vRot.z));
  const clip = cameraProjectionMatrix.mul(cameraViewMatrix.mul(vec4(surface, 1)));
  m.depthNode = clip.z.div(clip.w);
  const V = normalize(positionWorld.sub(cameraPosition));
  m.emissiveNode = albedo.mul(albedo).mul(env.sunColor).mul(pow(max(dot(V, env.sunDir), 0), 4).mul(0.1));
  // keep distant crowns dense: averaged mips lose coverage (Golus)
  const mip = max(log2(max(length(dFdx(atA)), length(dFdy(atA))).mul(tex.c.image.width)), 0);
  const covered = r.col.a.mul(mip.mul(0.3).add(1)).greaterThan(0.45);
  m.maskNode = inRange(vLo.x, vLo.y).and(covered);
  m.maskShadowNode = covered.and(vLo.y.greaterThan(vLo.x));
  m.userData.noContactShadow = true;
  return m;
}

function impostorGeometry(count) {
  const g = new THREE.InstancedBufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute([-1, -1, 0, 1, -1, 0, 1, 1, 0, -1, 1, 0], 3));
  g.setAttribute('normal', new THREE.Float32BufferAttribute([0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1], 3));
  g.setIndex([0, 1, 2, 0, 2, 3]);
  const pos = new THREE.InstancedBufferAttribute(new Float32Array(count * 4), 4);
  const rot = new THREE.InstancedBufferAttribute(new Float32Array(count * 4), 4);
  pos.setUsage(THREE.DynamicDrawUsage);
  rot.setUsage(THREE.DynamicDrawUsage);
  g.setAttribute('iPos', pos);
  g.setAttribute('iRot', rot);
  g.instanceCount = 0;
  return g;
}

// ------------------------------------------------------------------ system
export class Vegetation {
  static async create(opts) {
    const assets = await loadAssets();
    return new Vegetation(assets, opts);
  }

  constructor(assets, { scene, island, collision }) {
    this.assets = assets;
    this.scene = scene;
    this.island = island;
    this.collision = collision;
    this.group = new THREE.Group();
    this.group.name = 'vegetation';
    scene.add(this.group);
    this._place();
    this._build();
    this.frame = 0;
    this.lodScale = 1;          // Graphics > Vegetation detail: scales the LOD distances
  }

  setDetail(v) { this.lodScale = v; this.lastX = undefined; }

  /** Where everything grows: trees from the baked forest cover, palms on
   *  the coastal strip and in damp hollows, scrub along forest edges and
   *  the back of the beach, ferns under the canopy. */
  _place() {
    const isl = this.island, col = this.collision;
    const rnd = rndGen(2024);
    const inst = {};
    for (const k of Object.keys(SPECIES)) inst[k] = [];
    const CELL = 6, grid = new Map();
    const key = (i, j) => i * 73856093 ^ j * 19349663;
    const blocked = (x, z, r) => {
      if (Math.abs(x - VILLAGE.pierX) < 5 && z > 10) return true;
      // keep the player's arrival spot on the beach clear
      if ((x - SPAWN.x) ** 2 + (z - SPAWN.z) ** 2 < 9 * 9) return true;
      const g = col.groundAt(x, z, 100, 0, r);
      return g.surface !== null || col.ceilingAt(x, z, isl.heightAt(x, z) - 1) < Infinity;
    };
    const free = (x, z, r, tree) => {
      const ci = Math.floor(x / CELL), cj = Math.floor(z / CELL);
      for (let dj = -1; dj <= 1; dj++) for (let di = -1; di <= 1; di++) {
        for (const o of grid.get(key(ci + di, cj + dj)) || []) {
          // trees keep their crowns apart (with overlap); undergrowth only
          // keeps off trunks and away from its own kind
          let rr;
          if (tree && o.tree) rr = (r + o.r) * 0.62;
          else if (o.tree) rr = o.r * 0.3;
          else rr = (r + o.r) * 0.7;
          if ((o.x - x) ** 2 + (o.z - z) ** 2 < rr * rr) return false;
        }
      }
      return true;
    };
    const add = (kind, x, z, h, s, tree) => {
      const sp = SPECIES[kind];
      const variants = this.assets.plants[sp.model || kind].variants.length;
      const r = sp.rad * s;
      if (!free(x, z, r, tree) || blocked(x, z, tree ? 1.2 : 0.5)) return false;
      const k = key(Math.floor(x / CELL), Math.floor(z / CELL));
      if (!grid.has(k)) grid.set(k, []);
      grid.get(k).push({ x, z, r, tree });
      inst[kind].push({ x, z, y: h - 0.1, yaw: rnd() * Math.PI * 2, s, v: Math.floor(rnd() * variants), phase: rnd() * 100 });
      if (tree) col.addCylinder({ x, z, y0: h - 1, y1: h + 7, r: sp.trunk * s });
      return true;
    };
    const slopeAt = (x, z) => 1 - isl.normalAt(x, z).y;
    // trees first, then the undergrowth fills in around them
    const passes = [
      { spacing: 3.2, fn: (x, z, h, sdf, forest, wet, slope) => {
        if (slope > 0.5) return;
        // coconut palms: the coastal strip behind the beach
        const coast = sdf < -9 && sdf > -70 && h < 7;
        if (coast && rnd() < 0.06) { add('palm', x, z, h, 0.85 + rnd() * 0.35, true); return; }
        if (forest < 0.05) {
          // open grassland: the odd lone tree
          if (sdf < -60 && rnd() < 0.004) add(rnd() < 0.5 ? 'umbrella' : 'broad', x, z, h, 0.8 + rnd() * 0.4, true);
          return;
        }
        if (rnd() > forest * 0.42) return;
        const r = rnd();
        let kind;
        if (h > 72 && wet < 0.4) kind = r < 0.55 ? 'ironwood' : 'broad';          // dry upper slopes and ridges
        else if (h < 30 && sdf > -170) kind = r < 0.3 ? 'umbrella' : r < 0.45 ? 'palm' : 'broad';   // coastal lowland
        else if (wet > 0.55) kind = r < 0.1 ? 'palm' : 'broad';                    // damp hollows
        else kind = r < 0.12 ? 'ironwood' : r < 0.2 ? 'umbrella' : 'broad';
        add(kind, x, z, h, 0.75 + rnd() * 0.5, true);
      } },
      { spacing: 3.0, fn: (x, z, h, sdf, forest, wet, slope) => {
        // saplings and small trees: the middle storey of the woods
        if (slope > 0.5 || forest < 0.3) return;
        if (rnd() < forest * 0.35) add('sapling', x, z, h, 0.28 + rnd() * 0.22, true);
      } },
      { spacing: 2.2, fn: (x, z, h, sdf, forest, wet, slope) => {
        if (slope > 0.55) return;
        // scrub: the back of the beach, forest edges, gaps in the canopy
        const beachBack = sdf < -18 && sdf > -65 ? 0.05 : 0;
        const edge = forest * (1 - forest) * 4;
        const p = beachBack + edge * 0.16 + forest * 0.05 + (sdf < -60 ? 0.01 : 0);
        if (rnd() < p) add('shrub', x, z, h, 0.6 + rnd() * 0.9, false);
      } },
      { spacing: 1.4, fn: (x, z, h, sdf, forest, wet, slope) => {
        if (slope > 0.6 || forest < 0.3) return;
        if (rnd() < forest * (0.22 + wet * 0.3)) add('fern', x, z, h, 0.7 + rnd() * 0.8, false);
      } },
    ];
    for (const pass of passes) {
      const S = pass.spacing;
      for (let z = -800; z < 170; z += S) {
        for (let x = -570; x < 570; x += S) {
          const px = x + rnd() * S, pz = z + rnd() * S;
          const h = isl.heightAt(px, pz);
          if (h < 0.7) continue;
          const sdf = isl.sdfAt(px, pz);
          if (sdf > -8) continue;
          const forest = isl.forestAt(px, pz);
          const wet = smoothstepJS(3.5, 10, isl.auxAt(px, pz, 0) * 255 / 12);
          pass.fn(px, pz, h, sdf, forest, wet, slopeAt(px, pz));
        }
      }
    }
    this.instances = inst;
    this.counts = Object.fromEntries(Object.entries(inst).map(([k, v]) => [k, v.length]));
  }

  _build() {
    const A = this.assets;
    this.sets = [];
    for (const [kind, cfg] of Object.entries(SPECIES)) {
      const model = cfg.model || kind;
      const tex = A.leafTex[cfg.atlas];
      const { m: leaf, alpha } = leafMaterial(kind, tex);
      applyMask(leaf, alpha);
      const bark = applyMask(barkMaterial(kind), null);
      A.plants[model].variants.forEach((meta, vi) => {
        const list = this.instances[kind].filter((o) => o.v === vi);
        if (!list.length) return;
        const mk = (name, mat, lod) => {
          const g = A.geoms[name];
          if (!g) return null;
          const geom = g.clone();
          const m = new THREE.InstancedMesh(geom, mat, list.length);
          m.count = 0;
          m.frustumCulled = false;
          m.castShadow = true;
          m.receiveShadow = true;
          const data = new THREE.InstancedBufferAttribute(new Float32Array(list.length * 4), 4);
          data.setUsage(THREE.DynamicDrawUsage);
          geom.setAttribute('vegData', data);
          m.userData = { lod, data };
          m.name = name;
          this.group.add(m);
          return m;
        };
        const set = {
          kind, cfg, list, height: meta.height,
          lod0: [mk(`${model}_${vi}_lod0_bark`, bark, 0), mk(`${model}_${vi}_lod0_leaves`, leaf, 0)].filter(Boolean),
          lod1: [mk(`${model}_${vi}_lod1_bark`, bark, 1), mk(`${model}_${vi}_lod1_leaves`, leaf, 1)].filter(Boolean),
          imp: null,
        };
        if (cfg.impostor && A.impTex[model]) {
          const g = impostorGeometry(list.length);
          const mat = impostorMaterial(A.impTex[model][vi], A.impostors[model][vi], A.impostors.frames);
          const mesh = new THREE.Mesh(g, mat);
          mesh.frustumCulled = false;
          mesh.castShadow = true;
          mesh.receiveShadow = true;
          mesh.name = `${kind}_${vi}_impostor`;
          this.group.add(mesh);
          set.imp = mesh;
        }
        this.sets.push(set);
      });
    }
  }

  /** draw one instance of every mesh (so their pipelines compile while loading) */
  prime(on) {
    this.primed = on;
    if (on) {
      for (const e of this.sets) {
        for (const m of [...e.lod0, ...e.lod1]) {
          m.count = Math.max(m.count, 1);
          m.userData.data.setXYZW(0, 0, 0, 0, 1);
          m.userData.data.needsUpdate = true;
        }
        if (e.imp) {
          const g = e.imp.geometry, o = e.list[0];
          g.instanceCount = Math.max(g.instanceCount, 1);
          g.attributes.iPos.setXYZW(0, o.x, o.y, o.z, o.s);
          g.attributes.iRot.setXYZW(0, 1, 0, 0, 1);
          g.attributes.iPos.needsUpdate = g.attributes.iRot.needsUpdate = true;
        }
      }
    } else { this.frame = 0; this.lastX = undefined; }
  }

  /** the plants never move: build every instance matrix once */
  _composeMatrices() {
    const m4 = new THREE.Matrix4(), q = new THREE.Quaternion(), sc = new THREE.Vector3(), p = new THREE.Vector3();
    const up = new THREE.Vector3(0, 1, 0);
    for (const e of this.sets) {
      for (const o of e.list) {
        q.setFromAxisAngle(up, o.yaw); sc.setScalar(o.s); p.set(o.x, o.y, o.z);
        o.m = new Float32Array(m4.compose(p, q, sc).elements);
      }
    }
    this.matrices = true;
  }

  /** assign instances to LODs (threshold ranges for the dithered cross-fades) */
  update(camera) {
    ditherFrame = (ditherFrame + 1) % 16;
    ditherShift.value.set(BAYER_WALK[ditherFrame] % 4, Math.floor(BAYER_WALK[ditherFrame] / 4));
    if (this.primed) return;
    if (this.frame++ % 3 !== 0) return;
    const cx = camera.position.x, cz = camera.position.z;
    // LOD assignment only depends on distance: nothing to do while the eye stays put
    if (this.lastX !== undefined && Math.hypot(cx - this.lastX, cz - this.lastZ) < 1.5) return;
    this.lastX = cx; this.lastZ = cz;
    if (!this.matrices) this._composeMatrices();
    const k = this.lodScale;
    for (const e of this.sets) {
      const near = e.cfg.near * k, mid = e.cfg.mid * k, far = e.cfg.impostor ? e.cfg.far : e.cfg.far * k;
      const b0 = near * 0.12, b1 = mid * 0.12;
      let n0 = 0, n1 = 0, ni = 0;
      const imp = e.imp ? e.imp.geometry : null;
      for (const o of e.list) {
        const d = Math.hypot(o.x - cx, o.z - cz);
        if (d > far) continue;
        // shares of the [0, 1) threshold range: LOD0 | LOD1 | impostor
        const f0 = 1 - smoothstepJS(near - b0, near + b0, d);
        const toFar = smoothstepJS(mid - b1, mid + b1, d);
        let f1 = (1 - f0) * (1 - toFar);
        let fi = (1 - f0) * toFar;
        if (!imp) { f1 = (f1 + fi) * (1 - smoothstepJS(far * 0.8, far, d)); fi = 0; } else fi *= 1 - smoothstepJS(far * 0.9, far, d);
        if (f0 > 0.001) {
          for (const m of e.lod0) { m.instanceMatrix.array.set(o.m, n0 * 16); m.userData.data.setXYZW(n0, o.phase, o.yaw, 0, f0); }
          n0++;
        }
        if (f1 > 0.001) {
          for (const m of e.lod1) { m.instanceMatrix.array.set(o.m, n1 * 16); m.userData.data.setXYZW(n1, o.phase, o.yaw, f0, f0 + f1); }
          n1++;
        }
        if (imp && fi > 0.001) {
          imp.attributes.iPos.setXYZW(ni, o.x, o.y, o.z, o.s);
          imp.attributes.iRot.setXYZW(ni, Math.cos(o.yaw), Math.sin(o.yaw), f0 + f1, f0 + f1 + fi);
          ni++;
        }
      }
      for (const m of e.lod0) { m.count = n0; m.instanceMatrix.needsUpdate = true; m.userData.data.needsUpdate = true; }
      for (const m of e.lod1) { m.count = n1; m.instanceMatrix.needsUpdate = true; m.userData.data.needsUpdate = true; }
      if (imp) { imp.instanceCount = ni; imp.attributes.iPos.needsUpdate = true; imp.attributes.iRot.needsUpdate = true; }
    }
  }
}
