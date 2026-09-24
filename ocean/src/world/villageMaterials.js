// Procedural PBR materials for the fishing village. Everything is computed
// from world/local position, so merged meshes need no UV unwrapping and
// nothing ever tiles visibly.

import * as THREE from 'three/webgpu';
import {
  Fn, positionWorld, positionLocal, normalWorld, attribute, vec2, vec3, vec4, float, mix, smoothstep, clamp,
  abs, fract, floor, sin, cos, max, min, sqrt, dot, normalize, transformNormalToView, pow, step, uv, select,
} from 'three/tsl';
import { standard } from '../render/materials.js';
import { fbm2, fbm3, vnoise2, vnoise3, gnoise2, voronoi2, hash21 } from '../render/tslnoise.js';
import { env } from '../env.js';

// world-space triplanar-ish 2D coordinate: pick the plane facing the normal
function planarUV(p = positionWorld, n = normalWorld) {
  const an = abs(n);
  return select(an.y.greaterThan(max(an.x, an.z)), p.xz, select(an.x.greaterThan(an.z), p.zy, p.xy));
}

/** painted lap siding (weatherboard). Paint colour from the 'paint' vertex attribute. */
export function weatherboard() {
  const m = standard({ roughness: 0.62, metalness: 0 });
  const p = positionWorld;
  const paint = attribute('paint', 'vec3');
  const groundY = attribute('groundY', 'float');
  const board = 0.165;
  const f = fract(p.y.div(board));
  const row = floor(p.y.div(board));
  const along = dot(p.xz, vec2(normalWorld.z, normalWorld.x.negate()));   // horizontal coordinate on the wall
  const peel = fbm2(vec2(along.mul(1.6), p.y.mul(4.0)).add(row.mul(3.1)), 4).mul(0.5).add(0.5);
  const bare = smoothstep(0.68, 0.74, peel.add(smoothstep(1.4, 0.0, p.y.sub(groundY)).mul(0.12)));
  const grain = fbm2(vec2(along.mul(0.6), p.y.mul(40)), 3).mul(0.5).add(0.5);
  const wood = mix(vec3(0.33, 0.3, 0.26), vec3(0.47, 0.44, 0.39), grain);
  const tone = hash21(vec2(row, floor(along.div(3.7)))).mul(0.12).add(0.9);
  const streak = fbm2(vec2(along.mul(4.0), p.y.mul(0.35)), 3).mul(0.5).add(0.5);
  let col = mix(paint.mul(tone), wood, bare);
  col = col.mul(mix(float(1), float(0.72), smoothstep(0.55, 0.9, streak).mul(0.5)));
  col = col.mul(mix(float(0.68), float(1), smoothstep(0.0, 0.9, p.y.sub(groundY))));
  // shadow line under each board's lower edge
  col = col.mul(mix(float(0.55), float(1), smoothstep(0.0, 0.1, f)));
  m.colorNode = col;
  m.roughnessNode = mix(float(0.55), float(0.8), bare);
  // lap profile: each board leans out at its bottom edge
  const tilt = smoothstep(0.0, 0.08, f).mul(0.16).sub(0.04);
  const nW = normalize(normalWorld.add(vec3(0, tilt.negate(), 0)));
  m.normalNode = transformNormalToView(nW);
  m.name = 'village.weatherboard';
  return m;
}

/** corrugated metal roofing, galvanised or painted (paint attr), with rust */
export function corrugated() {
  const m = standard({ roughness: 0.45, metalness: 0.55 });
  const p = positionLocal;
  const paint = attribute('paint', 'vec3');
  const dir = attribute('corrDir', 'vec2');        // horizontal direction across the corrugations
  const u = dot(p.xz, dir);
  const w = u.div(0.076).mul(Math.PI * 2);
  const rust = fbm3(positionWorld.mul(0.8), 4).mul(0.5).add(0.5);
  const rustMask = smoothstep(0.58, 0.8, rust.add(smoothstep(0.3, 0.0, fract(u.div(0.84))).mul(0.15)));
  const galv = vec3(0.62, 0.64, 0.64).mul(fbm2(positionWorld.xz.mul(2.3), 3).mul(0.1).add(0.95));
  const base = select(paint.x.lessThan(0), galv, paint);
  const rustCol = mix(vec3(0.36, 0.16, 0.07), vec3(0.52, 0.28, 0.12), fbm2(positionWorld.xz.mul(7), 2).mul(0.5).add(0.5));
  m.colorNode = mix(base, rustCol, rustMask);
  m.metalnessNode = mix(select(paint.x.lessThan(0), float(0.8), float(0.1)), float(0.05), rustMask);
  m.roughnessNode = mix(float(0.38), float(0.85), rustMask);
  const slope = cos(w).mul(0.42);
  const d3 = vec3(dir.x, 0, dir.y);
  m.normalNode = transformNormalToView(normalize(normalWorld.add(d3.mul(slope))));
  m.name = 'village.corrugated';
  return m;
}

/** weathered wooden planks (decks). Planks run along local x, stacked along planeAxis. */
export function planks({ width = 0.19, gap = 0.012, axis = 'z', tint = [0.46, 0.41, 0.35] } = {}) {
  const m = standard({ roughness: 0.78, metalness: 0 });
  const p = positionWorld;
  const across = axis === 'z' ? p.z : p.x;
  const along = axis === 'z' ? p.x : p.z;
  const idx = floor(across.div(width));
  const f = fract(across.div(width));
  const r = hash21(vec2(idx, 7.1));
  const seg = floor(along.div(3.1).add(r.mul(3)));
  const r2 = hash21(vec2(idx, seg));
  const grain = fbm2(vec2(along.mul(0.8).add(r.mul(10)), across.mul(24)), 4).mul(0.5).add(0.5);
  const base = vec3(...tint).mul(mix(0.72, 1.12, r2)).mul(mix(0.82, 1.1, grain));
  const wear = fbm2(p.xz.mul(0.7), 3).mul(0.5).add(0.5);
  const col = mix(base, base.mul(vec3(0.82, 0.86, 0.9)), smoothstep(0.4, 0.8, wear).mul(0.5));
  const gapMask = smoothstep(gap / width, gap / width + 0.03, f).mul(smoothstep(1.0, 1.0 - 0.03, f));
  m.colorNode = col.mul(mix(float(0.22), float(1), gapMask));
  m.roughnessNode = mix(float(0.62), float(0.9), grain);
  // slightly cupped planks
  const cup = f.sub(0.5).mul(0.18);
  const tangent = axis === 'z' ? vec3(0, 0, 1) : vec3(1, 0, 0);
  m.normalNode = transformNormalToView(normalize(normalWorld.add(tangent.mul(cup))));
  m.name = 'village.planks';
  return m;
}

/** pier pilings / posts: dark wood, wet below the tide line, algae + barnacles */
export function piling() {
  const m = standard({ roughness: 0.7, metalness: 0 });
  const p = positionWorld;
  const ang = vec2(p.x.mul(13.1).add(p.z.mul(7.7)), p.y);
  const grain = fbm2(vec2(ang.x.mul(2), p.y.mul(2.5)), 4).mul(0.5).add(0.5);
  const dry = vec3(0.3, 0.25, 0.2).mul(mix(0.75, 1.15, grain));
  const wetZone = smoothstep(0.7, 0.2, p.y);
  const algae = smoothstep(0.45, -0.1, p.y).mul(smoothstep(-1.8, -0.4, p.y));
  const cells = voronoi2(vec2(ang.x.mul(9), p.y.mul(9)));
  const barn = smoothstep(0.22, 0.12, cells.x).mul(smoothstep(0.55, 0.1, p.y)).mul(smoothstep(-0.9, -0.2, p.y));
  let col = mix(dry, dry.mul(0.45), wetZone);
  col = mix(col, vec3(0.1, 0.16, 0.06), algae.mul(0.85));
  col = mix(col, vec3(0.7, 0.68, 0.6), barn);
  m.colorNode = col;
  m.roughnessNode = mix(float(0.75), float(0.3), wetZone.mul(float(1).sub(barn)));
  m.name = 'village.piling';
  return m;
}

/** rough stone masonry for foundations and walls */
export function stone(scale = 1.4) {
  const m = standard({ roughness: 0.88, metalness: 0 });
  const uvp = planarUV().mul(scale);
  const v = voronoi2(uvp.mul(vec2(1, 1.6)));
  const mortar = smoothstep(0.02, 0.07, v.y.sub(v.x));
  const tone = v.z.mul(0.25).add(0.75);
  const grit = fbm2(uvp.mul(6), 3).mul(0.5).add(0.5);
  const stoneCol = vec3(0.48, 0.46, 0.42).mul(tone).mul(mix(0.85, 1.1, grit));
  m.colorNode = mix(vec3(0.32, 0.3, 0.27), stoneCol, mortar);
  m.name = 'village.stone';
  return m;
}

export function rope() {
  const m = standard({ roughness: 0.92, metalness: 0 });
  const p = positionLocal;
  const twist = sin(p.x.add(p.y).add(p.z).mul(60)).mul(0.5).add(0.5);
  m.colorNode = mix(vec3(0.5, 0.42, 0.28), vec3(0.66, 0.57, 0.4), twist);
  return m;
}

/** fishing net: diamond mesh cut out with alpha test (no AO: holes would be occluded) */
export function net(color = [0.24, 0.34, 0.3]) {
  const m = standard({ roughness: 0.85, metalness: 0, side: THREE.DoubleSide });
  const q = uv().mul(vec2(60, 60));
  const d1 = fract(q.x.add(q.y)), d2 = fract(q.x.sub(q.y));
  const line = min(min(d1, float(1).sub(d1)), min(d2, float(1).sub(d2)));
  const knot = step(line, 0.12);
  m.colorNode = vec3(...color).mul(fbm2(uv().mul(7), 2).mul(0.2).add(0.9));
  m.opacityNode = knot;
  m.alphaTest = 0.5;
  m.userData.noAO = true;
  m.userData.noContactShadow = true;
  m.name = 'village.net';
  return m;
}

export function rustyMetal(color = [0.2, 0.2, 0.21]) {
  const m = standard({ roughness: 0.5, metalness: 0.7 });
  const r = fbm3(positionWorld.mul(3.1), 4).mul(0.5).add(0.5);
  const rust = smoothstep(0.5, 0.75, r);
  m.colorNode = mix(vec3(...color), vec3(0.4, 0.18, 0.07), rust);
  m.metalnessNode = mix(float(0.75), float(0.1), rust);
  m.roughnessNode = mix(float(0.42), float(0.9), rust);
  return m;
}

export function paintedWood(color, rough = 0.6) {
  const m = standard({ roughness: rough, metalness: 0 });
  const p = positionWorld;
  const c = new THREE.Color(color);
  const g = fbm2(vec2(p.x.add(p.z).mul(0.7), p.y.mul(9)), 4).mul(0.5).add(0.5);
  const chip = smoothstep(0.7, 0.76, fbm2(p.xz.add(p.y).mul(2.6), 4).mul(0.5).add(0.5));
  m.colorNode = mix(vec3(c.r, c.g, c.b).mul(mix(0.85, 1.05, g)), vec3(0.36, 0.32, 0.27), chip);
  return m;
}

export function rawWood(tint = [0.42, 0.33, 0.24]) {
  const m = standard({ roughness: 0.8, metalness: 0 });
  const p = positionLocal;
  const g = fbm2(vec2(p.x.add(p.z).mul(0.9), p.y.mul(14)), 4).mul(0.5).add(0.5);
  const g2 = fbm2(vec2(p.y.mul(0.9), p.x.add(p.z).mul(14)), 4).mul(0.5).add(0.5);
  m.colorNode = vec3(...tint).mul(mix(0.7, 1.15, g.mul(0.5).add(g2.mul(0.5))));
  return m;
}

/** window glass: dark, glossy; warm interior glow after dusk (per-window flicker phase) */
export function windowGlass() {
  const m = standard({ roughness: 0.08, metalness: 0.1 });
  const p = positionWorld;
  const id = hash21(floor(p.xz.div(1.3)).add(floor(p.y.div(2)).mul(17)));
  const lit = step(0.35, id);
  const glow = vec3(1.0, 0.62, 0.3).mul(lit).mul(env.nightFactor).mul(id.mul(1.5).add(1.2));
  m.colorNode = vec3(0.03, 0.04, 0.05);
  m.emissiveNode = glow.mul(smoothstep(0.1, 0.3, env.nightFactor));
  m.name = 'village.glass';
  return m;
}

export function canvasCloth(color) {
  const m = standard({ roughness: 0.9, metalness: 0, side: THREE.DoubleSide });
  const c = new THREE.Color(color);
  const w = fbm2(positionWorld.xz.mul(3).add(positionWorld.y), 3).mul(0.5).add(0.5);
  m.colorNode = vec3(c.r, c.g, c.b).mul(mix(0.8, 1.05, w));
  return m;
}

export function barkWood() {
  const m = standard({ roughness: 0.92, metalness: 0 });
  const p = positionLocal;
  const ridges = fbm2(vec2(p.x.mul(3.0).add(p.z.mul(3.0)), p.y.mul(0.5)), 4).mul(0.5).add(0.5);
  const bleached = fbm2(positionWorld.xz.mul(0.8), 3).mul(0.5).add(0.5);
  m.colorNode = mix(vec3(0.33, 0.28, 0.22), vec3(0.62, 0.58, 0.52), bleached.mul(0.8)).mul(mix(0.7, 1.1, ridges));
  return m;
}
