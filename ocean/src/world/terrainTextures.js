// Baked, tileable PBR sets for the terrain (albedo+roughness, normal+height+AO)
// packed into two texture arrays so the terrain shader can pick its two
// strongest materials per pixel with dynamic layer indices.
//
//   0 sand      2 m tile: wind ripples, lumps, shell grit, mineral speckle
//   1 rock      4 m tile: fractured basalt, strata, lichen, cracks
//   2 grass     2 m tile: short turf over soil
//   3 forest    2 m tile: leaf litter, twigs, soil
//   4 pebbles   2 m tile: rounded beach cobbles in sand
//   5 soil      2 m tile: red-brown volcanic soil, clods, grit, a few stones
//
// Sand and pebbles are baked here on the GPU; rock, grass, forest floor and
// soil are modelled and rendered in Blender (tools/blender/ground.py) and
// copied into their layers by loadGroundImages (the procedural versions
// below stay as the fallback and for the first frames).

import * as THREE from 'three/webgpu';
import {
  Fn, instanceIndex, uint, int, uvec2, vec2, vec3, vec4, float, textureStore, texture, clamp, mix,
  smoothstep, sin, pow, abs, max, min, normalize, storageTexture, sqrt, fract, floor, dot,
} from 'three/tsl';
import { makeStorage } from '../render/bake.js';
import { fbmP, voronoiP, gnoiseP, vnoiseP, hash21 } from '../render/tslnoise.js';

export const TERRAIN_LAYERS = { sand: 0, rock: 1, grass: 2, forest: 3, pebbles: 4, soil: 5 };
export const TERRAIN_TILE = [2.0, 4.0, 2.0, 2.0, 2.0, 2.0];

const lum = (c) => dot(c, vec3(0.2126, 0.7152, 0.0722));

const MATS = [
  // ---------------------------------------------------------------- sand
  {
    height: (uv) => {
      const warp = fbmP(uv, [3, 3], 3).mul(0.9);
      const ripPhase = uv.y.mul(22).add(uv.x.mul(3)).add(warp.mul(1.6));
      const rip = pow(sin(ripPhase.mul(6.2831853)).mul(0.5).add(0.5), 1.8);
      const ripFade = smoothstep(0.35, 0.8, fbmP(uv.add(0.3), [2, 2], 3).mul(0.5).add(0.5));
      const lumps = fbmP(uv, [5, 5], 4).mul(0.5).add(0.5);
      const grains = vnoiseP(uv.mul(512), vec2(512, 512));
      const shells = voronoiP(uv.mul(26), vec2(26, 26));
      const isShell = smoothstep(0.975, 0.99, shells.z);
      const shellBump = smoothstep(0.22, 0.06, shells.x).mul(isShell);
      const h = rip.mul(ripFade).mul(0.35).add(lumps.mul(0.45)).add(grains.mul(0.05)).add(shellBump.mul(0.25));
      return vec4(h, shellBump, grains, ripFade);
    },
    shade: (uv, t, ao) => {
      const speck = vnoiseP(uv.mul(900), vec2(900, 900));
      const tint = fbmP(uv.add(0.61), [3, 3], 3).mul(0.5).add(0.5);
      let base = mix(vec3(0.46, 0.37, 0.26), vec3(0.56, 0.46, 0.33), tint);
      base = mix(base, vec3(0.16, 0.14, 0.12), smoothstep(0.93, 0.99, speck).mul(0.8));    // dark mineral grains
      base = mix(base, vec3(0.72, 0.68, 0.6), smoothstep(0.86, 0.9, speck).mul(0.25));     // quartz glints
      base = mix(base, vec3(0.66, 0.6, 0.52), t.y.mul(0.6));                               // shell grit
      base = base.mul(mix(0.82, 1.05, t.x));                                              // ripple crests catch light
      const rough = mix(0.82, 0.95, t.z);
      return vec4(base.mul(ao), rough);
    },
    normalStrength: 5,
  },
  // ---------------------------------------------------------------- rock
  {
    height: (uv) => {
      const warp = vec2(fbmP(uv, [2, 2], 3), fbmP(uv.add(0.5), [2, 2], 3)).mul(0.08);
      const p = uv.add(warp);
      const big = fbmP(p, [3, 3], 5).mul(0.5).add(0.5);
      const cells = voronoiP(p.mul(5), vec2(5, 5));
      const cracks = smoothstep(0.0, 0.05, cells.y.sub(cells.x));
      const cells2 = voronoiP(p.mul(13), vec2(13, 13));
      const cracks2 = smoothstep(0.0, 0.035, cells2.y.sub(cells2.x));
      const strata = sin(p.y.mul(40).add(big.mul(6)).mul(3.14159)).mul(0.5).add(0.5);
      const pits = vnoiseP(p.mul(96), vec2(96, 96));
      const h = big.mul(0.55).add(cells.x.mul(0.2)).add(strata.mul(0.06)).add(pits.mul(0.06)).mul(cracks.mul(0.7).add(0.3)).mul(cracks2.mul(0.25).add(0.75));
      return vec4(h, cracks.mul(cracks2), cells.z, big);
    },
    shade: (uv, t, ao) => {
      const tone = fbmP(uv.add(0.2), [4, 4], 4).mul(0.5).add(0.5);
      let base = mix(vec3(0.085, 0.08, 0.075), vec3(0.2, 0.185, 0.165), tone);
      base = mix(base, base.mul(vec3(1.2, 1.05, 0.9)), t.z.mul(0.5));                      // per-block hue
      const lichen = smoothstep(0.62, 0.78, fbmP(uv.add(0.8), [6, 6], 4).mul(0.5).add(0.5));
      base = mix(base, vec3(0.42, 0.36, 0.2), lichen.mul(0.55));
      const whiteLichen = smoothstep(0.7, 0.85, fbmP(uv.add(0.1), [9, 9], 3).mul(0.5).add(0.5));
      base = mix(base, vec3(0.45, 0.45, 0.42), whiteLichen.mul(0.35));
      base = base.mul(t.y.mul(0.7).add(0.3));                                              // dark cracks
      const rough = mix(0.72, 0.92, tone).sub(lichen.mul(-0.05));
      return vec4(base.mul(ao), rough);
    },
    normalStrength: 5,
  },
  // ---------------------------------------------------------------- grass turf
  {
    height: (uv) => {
      const clumps = fbmP(uv, [6, 6], 4).mul(0.5).add(0.5);
      const blades = vnoiseP(uv.mul(vec2(220, 60)), vec2(220, 60));
      const blades2 = vnoiseP(uv.mul(vec2(70, 250)).add(0.3), vec2(70, 250));
      const soil = smoothstep(0.35, 0.2, clumps);
      const h = clumps.mul(0.6).add(max(blades, blades2).mul(0.35).mul(soil.oneMinus()));
      return vec4(h, soil, blades, clumps);
    },
    shade: (uv, t, ao) => {
      const tone = fbmP(uv.add(0.4), [3, 3], 3).mul(0.5).add(0.5);
      const g = mix(vec3(0.045, 0.075, 0.02), vec3(0.13, 0.15, 0.045), tone);
      const dry = mix(g, vec3(0.2, 0.17, 0.08), smoothstep(0.55, 0.8, fbmP(uv.add(0.9), [4, 4], 3).mul(0.5).add(0.5)));
      const withBlades = dry.mul(mix(0.75, 1.2, t.z));
      const soil = vec3(0.09, 0.065, 0.045);
      return vec4(mix(withBlades, soil, t.y).mul(ao), 0.93);
    },
    normalStrength: 4,
  },
  // ---------------------------------------------------------------- forest floor
  {
    height: (uv) => {
      const leaves = voronoiP(uv.mul(18), vec2(18, 18));
      const leaf = smoothstep(0.42, 0.18, leaves.x);
      const leaves2 = voronoiP(uv.mul(31).add(0.5), vec2(31, 31));
      const leaf2 = smoothstep(0.4, 0.15, leaves2.x);
      const twigs = smoothstep(0.03, 0.0, abs(fract(uv.x.mul(7).add(fbmP(uv, [4, 4], 3).mul(0.6))).sub(0.5))).mul(smoothstep(0.6, 0.8, fbmP(uv.add(0.2), [5, 5], 3).mul(0.5).add(0.5)));
      const soil = fbmP(uv, [8, 8], 4).mul(0.5).add(0.5);
      const h = soil.mul(0.35).add(max(leaf.mul(0.5), leaf2.mul(0.4))).add(twigs.mul(0.5));
      return vec4(h, leaves.z, leaves2.z, twigs);
    },
    shade: (uv, t, ao) => {
      const hueA = mix(vec3(0.22, 0.12, 0.05), vec3(0.34, 0.24, 0.09), t.y);
      const hueB = mix(vec3(0.15, 0.1, 0.05), vec3(0.28, 0.2, 0.08), t.z);
      const soil = vec3(0.07, 0.055, 0.04);
      let c = mix(soil, mix(hueA, hueB, 0.5), smoothstep(0.25, 0.45, t.x));
      c = mix(c, vec3(0.2, 0.15, 0.1), t.w);
      return vec4(c.mul(ao), 0.88);
    },
    normalStrength: 5,
  },
  // ---------------------------------------------------------------- pebbles
  {
    height: (uv) => {
      const v = voronoiP(uv.mul(11), vec2(11, 11));
      const r = clamp(float(1).sub(v.x.mul(1.55)), 0, 1);
      const dome = sqrt(r).mul(smoothstep(0.02, 0.12, v.y.sub(v.x)));
      const v2 = voronoiP(uv.mul(27).add(0.3), vec2(27, 27));
      const small = sqrt(clamp(float(1).sub(v2.x.mul(1.7)), 0, 1)).mul(0.55);
      const sand = vnoiseP(uv.mul(300), vec2(300, 300)).mul(0.08);
      const h = max(dome, small.mul(smoothstep(0.1, 0.3, dome.oneMinus()))).add(sand);
      return vec4(h, v.z, v2.z, dome);
    },
    shade: (uv, t, ao) => {
      const stone = mix(mix(vec3(0.12, 0.115, 0.11), vec3(0.3, 0.28, 0.25), t.y), vec3(0.42, 0.36, 0.28), smoothstep(0.8, 0.95, t.y));
      const small = mix(vec3(0.2, 0.18, 0.15), vec3(0.36, 0.33, 0.29), t.z);
      const sand = vec3(0.45, 0.37, 0.27);
      const c = mix(sand, mix(small, stone, smoothstep(0.1, 0.3, t.w)), smoothstep(0.05, 0.2, t.x));
      return vec4(c.mul(ao), mix(0.9, 0.62, smoothstep(0.2, 0.6, t.w)));
    },
    normalStrength: 6,
  },
  // ---------------------------------------------------------------- soil
  {
    height: (uv) => {
      const clods = fbmP(uv, [6, 6], 5).mul(0.5).add(0.5);
      const stones = voronoiP(uv.mul(14), vec2(14, 14));
      const isStone = smoothstep(0.82, 0.9, stones.z);
      const stoneBump = smoothstep(0.34, 0.08, stones.x).mul(isStone);
      const cw = fbmP(uv, [3, 3], 3).mul(0.08);
      const cells = voronoiP(uv.mul(6).add(cw), vec2(6, 6));
      const crack = smoothstep(0.0, 0.03, cells.y.sub(cells.x));
      const grit = vnoiseP(uv.mul(300), vec2(300, 300));
      const h = clods.mul(0.5).add(stoneBump.mul(0.45)).add(grit.mul(0.06)).mul(crack.mul(0.3).add(0.7));
      return vec4(h, stoneBump, grit, crack);
    },
    shade: (uv, t, ao) => {
      const tone = fbmP(uv.add(0.33), [4, 4], 3).mul(0.5).add(0.5);
      let c = mix(vec3(0.15, 0.085, 0.05), vec3(0.23, 0.14, 0.085), tone);   // weathered volcanic soil
      c = mix(c, vec3(0.26, 0.24, 0.21), smoothstep(0.1, 0.5, t.y));          // stones
      c = c.mul(mix(0.85, 1.1, t.z)).mul(t.w.mul(0.45).add(0.55));
      return vec4(c.mul(ao), mix(0.88, 0.7, t.y));
    },
    normalStrength: 5,
  },
];

export function bakeTerrainTextures(renderer, size = 1024) {
  const L = MATS.length;
  const albedo = makeStorage(size, { name: 'terrain.albedo', layers: L });
  const normal = makeStorage(size, { name: 'terrain.normal', layers: L });
  const temp = makeStorage(size, { name: 'terrain.tmp', type: THREE.HalfFloatType, mips: false });
  MATS.forEach((m, layer) => {
    // pass 1: height + feature masks
    const k1 = Fn(() => {
      const S = uint(size);
      const x = instanceIndex.mod(S), y = instanceIndex.div(S);
      const uv = vec2(float(x), float(y)).add(0.5).div(size);
      textureStore(temp, uvec2(x, y), m.height(uv));
    })().compute(size * size, [64]);
    // pass 2: normal, cavity AO, albedo/roughness
    const k2 = Fn(() => {
      const S = uint(size);
      const x = instanceIndex.mod(S), y = instanceIndex.div(S);
      const uv = vec2(float(x), float(y)).add(0.5).div(size);
      const e = 1 / size;
      const t = texture(temp, uv).level(0);
      const hx = texture(temp, fract(uv.add(vec2(e, 0)))).level(0).x.sub(texture(temp, fract(uv.sub(vec2(e, 0)))).level(0).x);
      const hy = texture(temp, fract(uv.add(vec2(0, e)))).level(0).x.sub(texture(temp, fract(uv.sub(vec2(0, e)))).level(0).x);
      const s = m.normalStrength * size / 512;
      const n = normalize(vec3(hx.mul(-s), hy.mul(-s), 1));
      // cavity AO: compare with a ring of neighbours
      let ring = float(0);
      const R = 6 / size;
      for (let i = 0; i < 8; i++) {
        const a = (i / 8) * Math.PI * 2;
        ring = ring.add(texture(temp, fract(uv.add(vec2(Math.cos(a) * R, Math.sin(a) * R)))).level(0).x);
      }
      const cavity = clamp(t.x.sub(ring.div(8)).mul(4).add(1), 0.45, 1);
      const shade = m.shade(uv, t, cavity);
      textureStore(storageTexture(albedo).depth(int(layer)), uvec2(x, y), clamp(shade, 0, 1));
      textureStore(storageTexture(normal).depth(int(layer)), uvec2(x, y), clamp(vec4(n.x.mul(0.5).add(0.5), n.y.mul(0.5).add(0.5), t.x, cavity), 0, 1));
    })().compute(size * size, [64]);
    renderer.compute(k1);
    renderer.compute(k2);
  });
  return { albedo, normal, layers: L };
}

/**
 * Replaces the rock, grass, forest-floor and soil layers with the Blender
 * renders in assets/terrain (<name>_c: albedo + roughness, <name>_n: normal
 * xy, height, AO). Their normal y points up the image, the baked layers'
 * down the rows: flipped while copying.
 */
export async function loadGroundImages(renderer, textures, size) {
  const base = new URL('../../assets/terrain/', import.meta.url);
  const loader = new THREE.TextureLoader();
  const load = async (name, srgb) => {
    const t = await loader.loadAsync(new URL(name, base).href);
    t.colorSpace = srgb ? THREE.SRGBColorSpace : THREE.NoColorSpace;
    t.flipY = false;
    t.generateMipmaps = false;
    t.minFilter = THREE.LinearFilter;
    return t;
  };
  const layers = { rock: 1, grass: 2, forest: 3, soil: 5 };
  await Promise.all(Object.entries(layers).map(async ([name, layer]) => {
    let c, n;
    try {
      [c, n] = await Promise.all([load(`${name}_c.webp`, true), load(`${name}_n.webp`, false)]);
    } catch (e) {
      console.warn(`terrain: ${name} textures missing, keeping the procedural layer`);
      return;
    }
    const k = Fn(() => {
      const S = uint(size);
      const x = instanceIndex.mod(S), y = instanceIndex.div(S);
      const uv = vec2(float(x), float(y)).add(0.5).div(size);
      const ca = texture(c, uv).level(0);
      const na = texture(n, uv).level(0);
      textureStore(storageTexture(textures.albedo).depth(int(layer)), uvec2(x, y), clamp(ca, 0, 1));
      textureStore(storageTexture(textures.normal).depth(int(layer)), uvec2(x, y), clamp(vec4(na.x, float(1).sub(na.y), na.z, na.w), 0, 1));
    })().compute(size * size, [64]);
    renderer.compute(k);
    c.dispose(); n.dispose();
  }));
}
