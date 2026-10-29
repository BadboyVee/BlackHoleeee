// Strand fur: every hair is an instanced camera-facing ribbon bent by gravity, wind and
// jiggle in the vertex shader. Uses MeshPhysicalMaterial underneath so lights, shadows
// and environment lighting all work, plus a matching depth material for shadow casting.
import * as THREE from 'three';

export const BACKLIGHT = { dir: new THREE.Vector3(0, 1, 0), color: new THREE.Color(1.0, 0.62, 0.32), strength: 0 };

const FUR_COMMON = /* glsl */`
attribute vec3 aRoot; attribute vec3 aNrm; attribute vec3 aDir; attribute vec4 aPrm; // len, width, phase, curl
attribute vec3 aColR; attribute vec3 aColT; attribute vec3 aClump;
uniform vec3 uCamObj; uniform vec3 uForce; uniform vec3 uWind; uniform float uTime; uniform float uGrow;
uniform float uFrizz;
varying float vS; varying vec3 vColR; varying vec3 vColT;
void furCompute(float s, float side, out vec3 pos, out vec3 nrm){
  float L = aPrm.x * uGrow;
  vec3 d = normalize(aDir);
  float ph = aPrm.z * 6.2831;
  float w = sin(uTime * 2.1 + ph + dot(aRoot, vec3(5.1, 3.7, 4.3))) * 0.6 + sin(uTime * 3.7 + ph * 1.7) * 0.4;
  vec3 f = uForce + uWind * (0.65 + 0.35 * w);
  vec3 t1 = normalize(cross(d, abs(d.y) < 0.95 ? vec3(0.0, 1.0, 0.0) : vec3(1.0, 0.0, 0.0)));
  vec3 t2 = cross(d, t1);
  float c = aPrm.w;
  float a1 = s * c + ph, a2 = s * c * 0.7 + ph * 1.3;
  float sa1 = sin(a1), ca1 = cos(a1), sa2 = sin(a2), ca2 = cos(a2);
  vec3 off = d * s + (f + aClump) * (s * s) + (t1 * sa1 + t2 * ca2) * (uFrizz * s);
  vec3 dof = d + (f + aClump) * (2.0 * s) + (t1 * sa1 + t2 * ca2) * uFrizz + (t1 * (c * ca1) - t2 * (0.7 * c * sa2)) * (uFrizz * s);
  float dn = dot(off, aNrm);
  off += aNrm * max(0.0, 0.15 * s - dn);
  vec3 p = aRoot + off * L;
  vec3 T = normalize(dof + 1e-5);
  vec3 V = normalize(uCamObj - p);
  vec3 S = cross(T, V);
  float sl = length(S);
  S = sl > 1e-5 ? S / sl : t1;
  float wdt = aPrm.y * (1.0 - 0.8 * s) * uGrow;
  pos = p + S * side * wdt * 0.5;
  vec3 N = cross(S, T);
  N *= sign(dot(N, V) + 1e-6);
  nrm = normalize(N + aNrm * 1.2 + 1e-4);
  vS = s; vColR = aColR; vColT = aColT;
}`;

export function makeFurUniforms() {
  return {
    uCamObj: { value: new THREE.Vector3(0, 0, 10) },
    uForce: { value: new THREE.Vector3(0, -0.25, 0) },
    uWind: { value: new THREE.Vector3(0, 0, 0) },
    uTime: { value: 0 },
    uGrow: { value: 1 },
    uFrizz: { value: 0.06 },
    uCheek: { value: 0 },
    uGlow: { value: 0 },
    uBackDir: { value: new THREE.Vector3(0, 0, 1) },
    uBackCol: { value: new THREE.Color(0, 0, 0) },
    uBackGain: { value: 1 },
  };
}

// Sample strand roots over a mesh, area weighted.
// opts: count, length, width, segs, seed, colorFn(p, n) -> [rootColor, tipColor], lengthFn(p, n) -> scale (0 = no hair),
//       combFn(p, n) -> THREE.Vector3 direction bias
export function createFur(geometry, opts) {
  const {
    count = 50000, length = 0.3, width = 0.01, segs = 5, seed = 1,
    colorFn = () => [new THREE.Color(0.8, 0.7, 0.6), new THREE.Color(1, 0.95, 0.85)],
    lengthFn = () => 1, combFn = () => new THREE.Vector3(0, -0.3, 0),
    material: matOpts = {}, uniforms = makeFurUniforms(), curl = 9, jitter = 0.16, clump = 0.0, clumpCount = 2500,
  } = opts;
  let sd = seed * 9301 + 49297;
  const rnd = () => ((sd = (sd * 16807) % 2147483647) / 2147483647);
  const g = geometry.index ? geometry.toNonIndexed() : geometry;
  const P = g.attributes.position, Nn = g.attributes.normal;
  const triCount = P.count / 3;
  const areas = new Float32Array(triCount);
  const a = new THREE.Vector3(), b = new THREE.Vector3(), c = new THREE.Vector3();
  let total = 0;
  for (let i = 0; i < triCount; i++) {
    a.fromBufferAttribute(P, i * 3); b.fromBufferAttribute(P, i * 3 + 1); c.fromBufferAttribute(P, i * 3 + 2);
    total += new THREE.Triangle(a, b, c).getArea();
    areas[i] = total;
  }
  const roots = [], nrms = [], dirs = [], prms = [], colR = [], colT = [];
  const p = new THREE.Vector3(), n = new THREE.Vector3(), na = new THREE.Vector3(), nb = new THREE.Vector3(), nc = new THREE.Vector3();
  let made = 0, tries = 0;
  while (made < count && tries < count * 4) {
    tries++;
    const r = rnd() * total;
    let lo = 0, hi = triCount - 1;
    while (lo < hi) { const mid = (lo + hi) >> 1; if (areas[mid] < r) lo = mid + 1; else hi = mid; }
    const i = lo;
    let u = rnd(), v = rnd(); if (u + v > 1) { u = 1 - u; v = 1 - v; }
    a.fromBufferAttribute(P, i * 3); b.fromBufferAttribute(P, i * 3 + 1); c.fromBufferAttribute(P, i * 3 + 2);
    na.fromBufferAttribute(Nn, i * 3); nb.fromBufferAttribute(Nn, i * 3 + 1); nc.fromBufferAttribute(Nn, i * 3 + 2);
    p.copy(a).multiplyScalar(1 - u - v).addScaledVector(b, u).addScaledVector(c, v);
    n.copy(na).multiplyScalar(1 - u - v).addScaledVector(nb, u).addScaledVector(nc, v).normalize();
    const ls = lengthFn(p, n);
    if (ls <= 0.02) continue;
    const comb = combFn(p, n);
    const d = n.clone().add(comb).add(new THREE.Vector3(rnd() - 0.5, rnd() - 0.5, rnd() - 0.5).multiplyScalar(jitter)).normalize();
    roots.push(p.x, p.y, p.z); nrms.push(n.x, n.y, n.z); dirs.push(d.x, d.y, d.z);
    prms.push(length * ls * (0.7 + 0.6 * rnd()), width * (0.75 + 0.5 * rnd()), rnd(), curl * (0.6 + 0.8 * rnd()));
    const [cr, ct] = colorFn(p, n, rnd);
    colR.push(cr.r, cr.g, cr.b); colT.push(ct.r, ct.g, ct.b);
    made++;
  }
  // clumping: pull each tip towards the nearest of a set of clump centres
  const clumpArr = new Float32Array(made * 3);
  if (clump > 0) {
    const cells = new Map(); const cs = Math.sqrt(total / clumpCount);
    const key = (x, y, z) => `${Math.floor(x / cs)},${Math.floor(y / cs)},${Math.floor(z / cs)}`;
    const centres = [];
    for (let k = 0; k < Math.min(clumpCount, made); k++) {
      const j = Math.floor(rnd() * made);
      const c = [roots[j * 3], roots[j * 3 + 1], roots[j * 3 + 2]];
      centres.push(c);
      const kk = key(...c); if (!cells.has(kk)) cells.set(kk, []); cells.get(kk).push(c);
    }
    for (let j = 0; j < made; j++) {
      const x = roots[j * 3], y = roots[j * 3 + 1], z = roots[j * 3 + 2];
      let best = null, bd = 1e9;
      for (let dx = -1; dx <= 1; dx++) for (let dy = -1; dy <= 1; dy++) for (let dz = -1; dz <= 1; dz++) {
        const lst = cells.get(`${Math.floor(x / cs) + dx},${Math.floor(y / cs) + dy},${Math.floor(z / cs) + dz}`);
        if (!lst) continue;
        for (const c of lst) { const dd = (c[0] - x) ** 2 + (c[1] - y) ** 2 + (c[2] - z) ** 2; if (dd < bd) { bd = dd; best = c; } }
      }
      if (!best) continue;
      const L = prms[j * 4];
      clumpArr[j * 3] = (best[0] - x) / L * clump; clumpArr[j * 3 + 1] = (best[1] - y) / L * clump; clumpArr[j * 3 + 2] = (best[2] - z) / L * clump;
    }
  }
  // base ribbon
  const pos = [], idx = [];
  for (let i = 0; i <= segs; i++) {
    const s = i / segs;
    pos.push(-1, s, 0, 1, s, 0);
    if (i < segs) { const k = i * 2; idx.push(k, k + 1, k + 2, k + 1, k + 3, k + 2); }
  }
  const geo = new THREE.InstancedBufferGeometry();
  geo.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  geo.setAttribute('normal', new THREE.Float32BufferAttribute(new Array(pos.length).fill(0).map((_, k) => (k % 3 === 2 ? 1 : 0)), 3));
  geo.setIndex(idx);
  geo.setAttribute('aRoot', new THREE.InstancedBufferAttribute(new Float32Array(roots), 3));
  geo.setAttribute('aNrm', new THREE.InstancedBufferAttribute(new Float32Array(nrms), 3));
  geo.setAttribute('aDir', new THREE.InstancedBufferAttribute(new Float32Array(dirs), 3));
  geo.setAttribute('aPrm', new THREE.InstancedBufferAttribute(new Float32Array(prms), 4));
  geo.setAttribute('aColR', new THREE.InstancedBufferAttribute(new Float32Array(colR), 3));
  geo.setAttribute('aColT', new THREE.InstancedBufferAttribute(new Float32Array(colT), 3));
  geo.setAttribute('aClump', new THREE.InstancedBufferAttribute(clumpArr, 3));
  geo.instanceCount = made;
  {
    const bb = new THREE.Box3();
    for (let j = 0; j < made; j++) bb.expandByPoint(new THREE.Vector3(roots[j * 3], roots[j * 3 + 1], roots[j * 3 + 2]));
    const sph = bb.getBoundingSphere(new THREE.Sphere());
    sph.radius += length * 4 + 0.5;
    geo.boundingSphere = sph;
  }

  const mat = new THREE.MeshPhysicalMaterial({
    color: 0xffffff, roughness: 0.72, metalness: 0, side: THREE.DoubleSide,
    sheen: 1.0, sheenRoughness: 0.45, sheenColor: new THREE.Color(1, 0.95, 0.86),
    ...matOpts,
  });
  mat.onBeforeCompile = (sh) => {
    Object.assign(sh.uniforms, uniforms);
    sh.vertexShader = sh.vertexShader
      .replace('#include <common>', '#include <common>\n' + FUR_COMMON)
      .replace('#include <beginnormal_vertex>', 'vec3 furPos, furNrm; furCompute(position.y, position.x, furPos, furNrm);\nvec3 objectNormal = furNrm;')
      .replace('#include <begin_vertex>', 'vec3 transformed = furPos;');
    sh.fragmentShader = sh.fragmentShader
      .replace('#include <common>', '#include <common>\nvarying float vS; varying vec3 vColR; varying vec3 vColT; uniform float uCheek; uniform float uGlow; uniform vec3 uBackDir; uniform vec3 uBackCol; uniform float uBackGain;')
      .replace('#include <color_fragment>', `#include <color_fragment>
        float ao = mix(0.72, 1.0, pow(vS, 0.6));
        diffuseColor.rgb *= mix(vColR, vColT, smoothstep(0.0, 1.0, vS)) * ao;`)
      .replace('#include <emissivemap_fragment>', `#include <emissivemap_fragment>
        float pinkness = clamp((vColT.r - vColT.g) * 3.0 - 0.35, 0.0, 1.0);
        totalEmissiveRadiance += vec3(1.0, 0.32, 0.38) * pinkness * uCheek * 0.35;
        totalEmissiveRadiance += mix(vColR, vColT, vS) * uGlow * (1.0 - 0.4 * vS);
        float fwd = pow(max(dot(-normalize(vViewPosition), uBackDir), 0.0), 4.0);
        float rim = 1.0 - abs(dot(normal, normalize(vViewPosition)));
        fwd *= rim * rim * 1.6;
        totalEmissiveRadiance += uBackCol * uBackGain * fwd * mix(vColR, vColT, vS) * pow(vS, 0.7);`);
  };
  mat.customProgramCacheKey = () => 'fur';
  const depthMat = new THREE.MeshDepthMaterial({ depthPacking: THREE.RGBADepthPacking, side: THREE.DoubleSide });
  depthMat.onBeforeCompile = (sh) => {
    Object.assign(sh.uniforms, uniforms);
    sh.uniforms.uWidthScale = depthMat.userData.widthScale;
    sh.vertexShader = sh.vertexShader
      .replace('#include <common>', '#include <common>\nuniform float uWidthScale;\n' + FUR_COMMON)
      .replace('#include <begin_vertex>', 'vec3 furPos, furNrm; furCompute(position.y, position.x * uWidthScale, furPos, furNrm);\nvec3 transformed = furPos;');
  };
  depthMat.customProgramCacheKey = () => 'furdepth';
  const mesh = new THREE.Mesh(geo, mat);
  mesh.customDepthMaterial = depthMat;
  mesh.castShadow = true; mesh.receiveShadow = true;
  mesh.frustumCulled = true;
  mesh.userData.furUniforms = uniforms;
  // keep uCamObj in object space of the mesh for whichever camera renders it
  const inv = new THREE.Matrix4(), cp = new THREE.Vector3();
  mesh.onBeforeRender = (renderer, scene, camera) => {
    inv.copy(mesh.matrixWorld).invert();
    cp.setFromMatrixPosition(camera.matrixWorld).applyMatrix4(inv);
    uniforms.uCamObj.value.copy(cp);
    uniforms.uBackDir.value.copy(BACKLIGHT.dir).transformDirection(camera.matrixWorldInverse);
    uniforms.uBackCol.value.copy(BACKLIGHT.color).multiplyScalar(BACKLIGHT.strength * 3.0);
  };
  const shadowFrac = opts.shadowFraction ?? 0.3;
  depthMat.userData.widthScale = { value: 1 / Math.sqrt(shadowFrac) };
  mesh.onBeforeShadow = (renderer, object, camera, shadowCamera) => {
    inv.copy(mesh.matrixWorld).invert();
    cp.setFromMatrixPosition(shadowCamera.matrixWorld).applyMatrix4(inv);
    uniforms.uCamObj.value.copy(cp);
    geo.instanceCount = Math.max(1, Math.round(made * shadowFrac));
  };
  mesh.onAfterShadow = () => { geo.instanceCount = made; };
  return mesh;
}
