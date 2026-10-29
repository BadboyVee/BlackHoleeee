// The set: a walnut desk at night with a laptop running Claude Code, a moss bowl by the
// window, fairy lights and a few props. Units are centimetres, the desk top is y = 0.
import * as THREE from 'three';
import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js';
import { NOISE } from './glsl.js';
import { drawTerminal, UI_W, UI_H } from './screen-ui.js';
import { createFur, BACKLIGHT } from './fur.js';
import { Reflector } from 'three/addons/objects/Reflector.js';

export const LAPTOP = { w: 30.4, d: 21.2, h: 1.4, lidAngle: THREE.MathUtils.degToRad(18), screenW: 28.4, screenH: 17.75 };
export const BOWL = { x: 34, z: -6, r: 10, h: 5.2 };

function rng(seed) { let s = seed; return () => ((s = (s * 16807) % 2147483647) / 2147483647); }

// ---------- procedural walnut ---------------------------------------------------------
function walnutMaterial() {
  const m = new THREE.MeshPhysicalMaterial({ color: 0xffffff, roughness: 0.42, clearcoat: 0.35, clearcoatRoughness: 0.28 });
  m.onBeforeCompile = (sh) => {
    sh.vertexShader = sh.vertexShader.replace('#include <common>', '#include <common>\nvarying vec3 vWPos;')
      .replace('#include <worldpos_vertex>', '#include <worldpos_vertex>\nvWPos = (modelMatrix * vec4(transformed, 1.0)).xyz;');
    sh.fragmentShader = sh.fragmentShader.replace('#include <common>', '#include <common>\nvarying vec3 vWPos;\n' + NOISE + `
      float woodG(vec3 p){ return p.z + fbm3(p * vec3(0.02, 0.2, 0.07)) * 7.0 + fbm3(p * vec3(0.004, 0.05, 0.015)) * 24.0; }
      float woodH(vec3 p){
        float g = woodG(p);
        float ring = fract(g * 0.38);
        float late = pow(1.0 - abs(ring * 2.0 - 1.0), 5.0);
        float streak = vnoise(vec3(p.x * 0.035, p.y * 2.0, g * 2.5));
        float fibre = vnoise(vec3(p.x * 0.5, p.y * 40.0, g * 70.0));
        return clamp(0.55 * streak + 0.3 * (1.0 - late) + 0.15 * fibre, 0.0, 1.0);
      }`)
      .replace('#include <color_fragment>', `#include <color_fragment>
        float wh = woodH(vWPos);
        float g0 = woodG(vWPos);
        float late = pow(1.0 - abs(fract(g0 * 0.38) * 2.0 - 1.0), 5.0);
        float pores = smoothstep(0.8, 0.88, vnoise(vec3(vWPos.x * 0.8, vWPos.y * 30.0, g0 * 30.0)));
        vec3 dark = vec3(0.07, 0.032, 0.016), mid = vec3(0.19, 0.092, 0.044), light = vec3(0.30, 0.16, 0.08);
        vec3 wc = mix(dark, mid, smoothstep(0.2, 0.6, wh));
        wc = mix(wc, light, smoothstep(0.62, 0.9, wh) * 0.7);
        wc *= 1.0 - late * 0.35;
        wc *= 1.0 - pores * 0.4;
        wc *= 0.8 + 0.35 * fbm3(vWPos * vec3(0.01, 0.1, 0.05));
        diffuseColor.rgb *= wc;`)
      .replace('#include <roughnessmap_fragment>', `#include <roughnessmap_fragment>
        roughnessFactor = mix(0.34, 0.6, pores + (1.0 - smoothstep(0.2, 0.7, wh)) * 0.3);`)
      .replace('#include <normal_fragment_maps>', `#include <normal_fragment_maps>
        {
          float h0 = woodH(vWPos) * 0.006 + pores * -0.004;
          vec3 dpx = dFdx(-vViewPosition), dpy = dFdy(-vViewPosition);
          float dhx = dFdx(h0), dhy = dFdy(h0);
          vec3 r1 = cross(dpy, normal), r2 = cross(normal, dpx);
          float det = dot(dpx, r1);
          vec3 grad = sign(det) * (dhx * r1 + dhy * r2);
          normal = normalize(abs(det) * normal - grad);
        }`);
  };
  m.customProgramCacheKey = () => 'walnut';
  return m;
}

// ---------- laptop screen --------------------------------------------------------------
function screenMaterial(tex) {
  const m = new THREE.MeshPhysicalMaterial({ color: 0x000000, roughness: 0.06, metalness: 0, clearcoat: 1, clearcoatRoughness: 0.03,
    emissive: 0xffffff, emissiveMap: tex, emissiveIntensity: 1 });
  m.userData.uniforms = { uRes: { value: new THREE.Vector2(UI_W, UI_H) }, uBright: { value: 1.0 } };
  m.onBeforeCompile = (sh) => {
    Object.assign(sh.uniforms, m.userData.uniforms);
    sh.fragmentShader = sh.fragmentShader.replace('#include <common>', '#include <common>\nuniform vec2 uRes; uniform float uBright;')
      .replace('#include <emissivemap_fragment>', `
        {
          vec2 px = vEmissiveMapUv * uRes;
          vec2 fw = fwidth(px);
          float macro = 1.0 - smoothstep(0.1, 0.33, max(fw.x, fw.y));
          vec2 cen = (floor(px) + 0.5) / uRes;
          vec3 sharp = texture2D(emissiveMap, cen).rgb;
          vec3 soft = texture2D(emissiveMap, vEmissiveMapUv).rgb;
          vec3 c = mix(soft, sharp, macro);
          // RGB stripe subpixels with a black matrix between them
          vec2 f = fract(px);
          float sx = f.x * 3.0;
          vec3 stripe = vec3(smoothstep(0.08, 0.22, sx) * smoothstep(0.92, 0.78, sx),
                             smoothstep(1.08, 1.22, sx) * smoothstep(1.92, 1.78, sx),
                             smoothstep(2.08, 2.22, sx) * smoothstep(2.92, 2.78, sx));
          float row = smoothstep(0.04, 0.12, f.y) * smoothstep(0.96, 0.88, f.y);
          vec3 mask = stripe * row * 3.6;
          c *= mix(vec3(1.0), mask, macro);
          totalEmissiveRadiance *= c * uBright;
        }`);
  };
  m.customProgramCacheKey = () => 'lcd';
  return m;
}

// ---------- sky outside the window -------------------------------------------------------
function skyMaterial() {
  const u = { uDawn: { value: 0 }, uTime: { value: 0 }, uSun: { value: new THREE.Vector3(0.15, 0.21, -1).normalize() } };
  const m = new THREE.ShaderMaterial({
    uniforms: u, depthWrite: false,
    vertexShader: `varying vec3 vP; void main(){ vP = (modelMatrix * vec4(position, 1.0)).xyz; gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0); }`,
    fragmentShader: NOISE + `
      uniform float uDawn, uTime; uniform vec3 uSun; varying vec3 vP;
      float ridge(float x, float f, float seed){
        float s = 0.0, a = 0.5;
        for (int i = 0; i < 5; i++){ float n = 1.0 - abs(vnoise2(vec2(x * f, seed)) * 2.0 - 1.0); s += a * n * n; f *= 2.1; a *= 0.5; }
        return s;
      }
      void main(){
        vec3 d = normalize(vP - cameraPosition);
        float h = d.y;
        float ang = atan(d.x, -d.z);
        // sky
        vec3 nightZ = vec3(0.003, 0.006, 0.018), nightH = vec3(0.018, 0.026, 0.055);
        vec3 night = mix(nightH, nightZ, smoothstep(0.0, 0.5, h));
        float st = pow(hash13(floor(d * 650.0)), 2500.0) * (3.0 + 5.0 * hash13(floor(d * 650.0) + 7.0)) * smoothstep(0.08, 0.35, h);
        night += vec3(0.85, 0.9, 1.0) * st * (0.75 + 0.25 * sin(uTime * 2.7 + hash13(floor(d * 650.0)) * 40.0));
        vec3 moonDir = normalize(vec3(0.42, 0.34, -1.0));
        float md = dot(d, moonDir);
        night += vec3(0.95, 0.96, 1.0) * smoothstep(0.99972, 0.99982, md) * 6.0 * pow(max(1.0 - uDawn * 12.0, 0.0), 2.0);
        night += vec3(0.10, 0.14, 0.26) * pow(max(md, 0.0), 200.0) * 1.5 + vec3(0.03, 0.04, 0.08) * pow(max(md, 0.0), 12.0);
        float sd = max(dot(d, uSun), 0.0);
        vec3 dawnZ = vec3(0.10, 0.22, 0.62), dawnM = vec3(0.95, 0.50, 0.42), dawnH = vec3(1.0, 0.42, 0.12);
        vec3 dawn = mix(dawnH, dawnM, smoothstep(0.0, 0.18, h));
        dawn = mix(dawn, dawnZ, smoothstep(0.15, 0.7, h));
        dawn *= 0.42;
        dawn += vec3(1.0, 0.55, 0.25) * pow(sd, 6.0) * 0.5 + vec3(1.0, 0.75, 0.45) * pow(sd, 90.0) * 1.6 + vec3(1.0, 0.85, 0.6) * pow(sd, 1500.0) * 6.0;
        dawn += vec3(1.0, 0.93, 0.8) * smoothstep(0.99994, 0.99997, sd) * 80.0;
        vec3 col = mix(night, dawn, uDawn);
        // clouds: soft stretched bands
        float cl = fbm2(vec2(ang * 3.0 + uTime * 0.004, h * 14.0)) * smoothstep(0.03, 0.12, h) * (1.0 - smoothstep(0.25, 0.5, h));
        cl = smoothstep(0.45, 0.8, cl);
        vec3 cloudN = vec3(0.025, 0.03, 0.05) + vec3(0.06, 0.07, 0.1) * pow(max(md, 0.0), 6.0);
        vec3 cloudD = mix(vec3(0.42, 0.26, 0.36), vec3(1.0, 0.55, 0.32), pow(sd, 3.0)) * 0.55;
        col = mix(col, mix(cloudN, cloudD, uDawn), cl * 0.85);
        // mountains, far to near, with aerial perspective
        vec3 hazeN = vec3(0.012, 0.018, 0.04), hazeD = vec3(0.55, 0.34, 0.26);
        vec3 haze = mix(hazeN, hazeD, uDawn);
        float m1 = 0.035 + 0.07 * ridge(ang, 1.4, 3.0);
        float m2 = 0.02 + 0.05 * ridge(ang + 1.3, 2.3, 7.0);
        float m3 = 0.005 + 0.03 * ridge(ang + 2.7, 4.0, 11.0) + 0.006 * vnoise2(vec2(ang * 120.0, 1.0));
        vec3 c1 = mix(vec3(0.010, 0.014, 0.030), vec3(0.30, 0.20, 0.26), uDawn);
        vec3 c2 = mix(vec3(0.006, 0.008, 0.018), vec3(0.16, 0.11, 0.16), uDawn);
        vec3 c3 = mix(vec3(0.002, 0.003, 0.007), vec3(0.05, 0.035, 0.05), uDawn);
        if (h < m1) col = mix(c1, haze, 0.35 * smoothstep(m1 - 0.03, m1, h));
        if (h < m2) col = mix(c2, haze, 0.2 * smoothstep(m2 - 0.02, m2, h));
        if (h < m3) col = c3;
        // morning mist in the valleys
        col = mix(col, haze * 0.9, uDawn * 0.5 * (1.0 - smoothstep(0.0, 0.04, h)) * smoothstep(-0.02, 0.02, h));
        gl_FragColor = vec4(col, 1.0);
      }`,
    side: THREE.BackSide,
  });
  m.userData.uniforms = u;
  return m;
}

// ---------- moss ------------------------------------------------------------------------
function mossMound(r, h, seg = 140) {
  const g = new THREE.CircleGeometry(r, seg);
  g.rotateX(-Math.PI / 2);
  // subdivide radially with a polar grid instead for smooth displacement
  const pos = [], idx = [];
  const rings = 40;
  for (let i = 0; i <= rings; i++) {
    const rr = (i / rings) * r;
    for (let j = 0; j < seg; j++) {
      const a = (j / seg) * Math.PI * 2;
      pos.push(Math.cos(a) * rr, 0, Math.sin(a) * rr);
    }
  }
  for (let i = 0; i < rings; i++) for (let j = 0; j < seg; j++) {
    const a = i * seg + j, b = i * seg + (j + 1) % seg, c = (i + 1) * seg + j, d = (i + 1) * seg + (j + 1) % seg;
    idx.push(a, c, b, b, c, d);
  }
  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3)); geo.setIndex(idx);
  const p = geo.attributes.position, v = new THREE.Vector3();
  const rb = rng(555);
  const cushions = [];
  for (let k = 0; k < 34; k++) {
    const a = rb() * Math.PI * 2, d = Math.sqrt(rb()) * r * 0.85;
    cushions.push([Math.cos(a) * d, Math.sin(a) * d, 1.0 + rb() * 2.2, 0.12 + rb() * 0.3]);
  }
  const bump = (x, z) => {
    const d = Math.hypot(x, z) / r;
    let y = h * Math.pow(Math.max(0, 1 - d * d), 0.7);
    for (const [cx, cz, cr, ch] of cushions) { const dd = ((x - cx) ** 2 + (z - cz) ** 2) / (cr * cr); y += ch * Math.exp(-dd * 1.6) * (1 - d * 0.6); }
    y += 0.08 * Math.sin(x * 4.1 + z * 2.3) * Math.cos(z * 3.7 - x);
    // a soft hollow where Jolly sleeps
    const jx = x - 2.2, jz = z - 1.0; y -= 0.35 * Math.exp(-(jx * jx + jz * jz) / 5);
    y *= Math.min(1, (1 - d) * 6);
    return y;
  };
  for (let i = 0; i < p.count; i++) { v.fromBufferAttribute(p, i); p.setY(i, bump(v.x, v.z)); }
  geo.computeVertexNormals();
  geo.userData.height = bump;
  return geo;
}

function fernGeometry(rnd, fronds = 6, size = 4) {
  // pinna: a small pointed leaf with a central fold, in the XZ plane pointing +x
  const leaf = new THREE.BufferGeometry();
  {
    const pos = [], idx = [];
    const n = 6;
    for (let i = 0; i <= n; i++) {
      const s = i / n, w = Math.sin(Math.PI * Math.pow(s, 0.8)) * 0.5 * (1 - s * 0.3);
      pos.push(s, 0, -w, s, 0.12 * w, 0, s, 0, w);
      if (i < n) { const k = i * 3; idx.push(k, k + 3, k + 1, k + 1, k + 3, k + 4, k + 1, k + 4, k + 2, k + 2, k + 4, k + 5); }
    }
    leaf.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3)); leaf.setIndex(idx);
  }
  const geos = [];
  for (let f = 0; f < fronds; f++) {
    const yaw = (f / fronds) * Math.PI * 2 + rnd() * 0.6;
    const len = size * (0.7 + 0.5 * rnd());
    const rise = 0.55 + rnd() * 0.35;
    const pts = [];
    for (let i = 0; i <= 12; i++) {
      const s = i / 12;
      pts.push(new THREE.Vector3(0, Math.sin(s * Math.PI * 0.62) * len * rise * 0.6 - s * s * len * 0.18, s * len));
    }
    const curve = new THREE.CatmullRomCurve3(pts);
    const fg = [];
    const pairs = 22;
    for (let i = 2; i < pairs; i++) {
      const s = i / pairs;
      const p = curve.getPoint(s), t = curve.getTangent(s);
      const w = len * 0.2 * Math.sin(Math.PI * Math.min(1, 0.15 + s * 0.95)) * (1.05 - s * 0.5);
      for (const side of [-1, 1]) {
        const g = leaf.clone().toNonIndexed();
        g.scale(w, w, w * 0.32);
        g.rotateY(side > 0 ? -0.95 : Math.PI + 0.95);
        const q = new THREE.Quaternion().setFromUnitVectors(new THREE.Vector3(0, 0, 1), t);
        g.applyQuaternion(q);
        g.translate(p.x, p.y, p.z);
        fg.push(g);
      }
    }
    fg.push(new THREE.TubeGeometry(curve, 16, len * 0.008, 4, false).toNonIndexed());
    for (const g of fg) { for (const k of Object.keys(g.attributes)) if (k !== 'position') g.deleteAttribute(k); g.rotateY(yaw); geos.push(g); }
  }
  const out = mergeGeos(geos);
  out.computeVertexNormals();
  return out;
}
function mergeGeos(list) {
  let n = 0; list.forEach((g) => (n += g.attributes.position.count));
  const pos = new Float32Array(n * 3); let o = 0;
  for (const g of list) { pos.set(g.attributes.position.array, o); o += g.attributes.position.count * 3; }
  const geo = new THREE.BufferGeometry(); geo.setAttribute('position', new THREE.BufferAttribute(pos, 3));
  return geo;
}

// ---------- the set ----------------------------------------------------------------------
export function buildDesk(renderer, opts = {}) {
  const rnd = rng(1234);
  const scene = new THREE.Scene();
  const parts = {};

  // desk
  const desk = new THREE.Mesh(new RoundedBoxGeometry(170, 4, 85, 2, 0.6), walnutMaterial());
  desk.position.set(10, -2, -12);
  desk.receiveShadow = true; desk.castShadow = true;
  scene.add(desk);

  // back wall with a window opening
  const wallMat = new THREE.MeshStandardMaterial({ color: new THREE.Color(0.55, 0.52, 0.48), roughness: 0.95 });
  const wallZ = -55;
  const win = { x0: 4, x1: 92, y0: 6, y1: 104 };
  const wallPieces = [
    [-120, win.x0, -80, 160], [win.x1, 160, -80, 160], [win.x0, win.x1, -80, win.y0], [win.x0, win.x1, win.y1, 160],
  ];
  for (const [x0, x1, y0, y1] of wallPieces) {
    const m = new THREE.Mesh(new THREE.BoxGeometry(x1 - x0, y1 - y0, 4), wallMat);
    m.position.set((x0 + x1) / 2, (y0 + y1) / 2, wallZ - 2);
    m.receiveShadow = true; m.castShadow = true;
    scene.add(m);
  }
  // window frame, mullions, sill
  const frameMat = new THREE.MeshStandardMaterial({ color: new THREE.Color(0.8, 0.78, 0.74), roughness: 0.5 });
  const addBox = (w, h, d, x, y, z, mat = frameMat) => { const m = new THREE.Mesh(new RoundedBoxGeometry(w, h, d, 2, Math.min(w, h, d) * 0.2), mat); m.position.set(x, y, z); m.castShadow = m.receiveShadow = true; scene.add(m); return m; };
  const fw = 3.2;
  addBox(win.x1 - win.x0 + fw * 2, fw, 6, (win.x0 + win.x1) / 2, win.y0 - fw / 2, wallZ + 1);
  addBox(win.x1 - win.x0 + fw * 2, fw, 6, (win.x0 + win.x1) / 2, win.y1 + fw / 2, wallZ + 1);
  addBox(fw, win.y1 - win.y0, 6, win.x0 - fw / 2, (win.y0 + win.y1) / 2, wallZ + 1);
  addBox(fw, win.y1 - win.y0, 6, win.x1 + fw / 2, (win.y0 + win.y1) / 2, wallZ + 1);
  addBox(2.2, win.y1 - win.y0, 4, (win.x0 + win.x1) / 2, (win.y0 + win.y1) / 2, wallZ + 0.5);
  addBox(win.x1 - win.x0, 2.2, 4, (win.x0 + win.x1) / 2, win.y0 + (win.y1 - win.y0) * 0.62, wallZ + 0.5);
  addBox(win.x1 - win.x0 + 12, 2.4, 14, (win.x0 + win.x1) / 2, win.y0 - fw - 1.2, wallZ + 5);
  // glass (faint reflection only)
  const glass = new THREE.Mesh(new THREE.PlaneGeometry(win.x1 - win.x0, win.y1 - win.y0),
    new THREE.MeshPhysicalMaterial({ color: 0x000000, roughness: 0.02, transparent: true, opacity: 0.08, depthWrite: false }));
  glass.position.set((win.x0 + win.x1) / 2, (win.y0 + win.y1) / 2, wallZ - 0.5);
  scene.add(glass);
  // sky
  const sky = new THREE.Mesh(new THREE.SphereGeometry(900, 64, 32), skyMaterial());
  sky.position.set(40, 0, -60);
  scene.add(sky);
  parts.sky = sky;
  parts.window = win; parts.wallZ = wallZ;

  // fairy lights along the window
  const bulbs = [];
  const wire = [];
  const nB = 26;
  for (let i = 0; i <= 60; i++) {
    const s = i / 60;
    const x = win.x0 - 6 + (win.x1 - win.x0 + 12) * s;
    const y = win.y1 + 2 - Math.sin(s * Math.PI * 3) ** 2 * 7 - 3;
    wire.push(new THREE.Vector3(x, y, wallZ + 4.5));
  }
  const wireCurve = new THREE.CatmullRomCurve3(wire);
  const wireMesh = new THREE.Mesh(new THREE.TubeGeometry(wireCurve, 200, 0.12, 5, false), new THREE.MeshStandardMaterial({ color: 0x2a2620, roughness: 0.6 }));
  scene.add(wireMesh);
  const bulbGeo = new THREE.SphereGeometry(0.45, 16, 12);
  const bulbMesh = new THREE.InstancedMesh(bulbGeo, new THREE.MeshBasicMaterial({ color: 0xffffff }), nB);
  for (let i = 0; i < nB; i++) {
    const p = wireCurve.getPoint((i + 0.5) / nB);
    p.y -= 0.6;
    bulbs.push(p);
    bulbMesh.setMatrixAt(i, new THREE.Matrix4().makeTranslation(p.x, p.y, p.z));
    bulbMesh.setColorAt(i, new THREE.Color(1.0, 0.55, 0.22).multiplyScalar(40));
  }
  scene.add(bulbMesh);
  parts.bulbs = bulbMesh; parts.bulbPositions = bulbs;
  const haloTex = (() => {
    const c = document.createElement('canvas'); c.width = c.height = 64;
    const g = c.getContext('2d'); const grd = g.createRadialGradient(32, 32, 0, 32, 32, 32);
    grd.addColorStop(0, 'rgba(255,255,255,1)'); grd.addColorStop(0.25, 'rgba(255,255,255,0.35)'); grd.addColorStop(1, 'rgba(255,255,255,0)');
    g.fillStyle = grd; g.fillRect(0, 0, 64, 64);
    return new THREE.CanvasTexture(c);
  })();
  const haloMat = new THREE.SpriteMaterial({ map: haloTex, color: new THREE.Color(1.0, 0.55, 0.22).multiplyScalar(1.6), blending: THREE.AdditiveBlending, depthWrite: false, transparent: true });
  parts.haloMat = haloMat;
  const addHalo = (p, s2) => { const h = new THREE.Sprite(haloMat); h.position.copy(p); h.scale.setScalar(s2); scene.add(h); return h; };
  bulbs.forEach((p) => addHalo(p, 3.2));

  // a second string of fairy lights lying on the desk behind the bowl
  const deskWire = [];
  for (let i = 0; i <= 50; i++) {
    const s2 = i / 50;
    const a = -0.4 + s2 * 3.6;
    deskWire.push(new THREE.Vector3(BOWL.x + Math.cos(a) * (BOWL.r + 6 + 6 * s2) - 4 * s2, 0.25 + 0.15 * Math.sin(s2 * 20), BOWL.z - Math.sin(a) * (BOWL.r + 5) - 6 - 10 * s2));
  }
  const dwc = new THREE.CatmullRomCurve3(deskWire);
  scene.add(new THREE.Mesh(new THREE.TubeGeometry(dwc, 200, 0.1, 5, false), new THREE.MeshStandardMaterial({ color: 0x2a2620, roughness: 0.6 })));
  const nD = 18;
  const deskBulbs = new THREE.InstancedMesh(bulbGeo, new THREE.MeshBasicMaterial({ color: 0xffffff }), nD);
  const deskBulbPos = [];
  for (let i = 0; i < nD; i++) {
    const p = dwc.getPoint((i + 0.5) / nD); p.y = 0.5;
    deskBulbPos.push(p);
    deskBulbs.setMatrixAt(i, new THREE.Matrix4().makeTranslation(p.x, p.y, p.z));
    deskBulbs.setColorAt(i, new THREE.Color(1.0, 0.55, 0.22).multiplyScalar(40));
  }
  scene.add(deskBulbs);
  parts.deskBulbs = deskBulbs; parts.deskBulbPositions = deskBulbPos;
  deskBulbPos.forEach((p) => addHalo(p, 3.2));

  // ---- laptop ----
  const L = LAPTOP;
  const alu = new THREE.MeshPhysicalMaterial({ color: new THREE.Color(0.36, 0.37, 0.39), metalness: 1, roughness: 0.34, clearcoat: 0.0 });
  const laptop = new THREE.Group();
  scene.add(laptop);
  parts.laptop = laptop;
  const base = new THREE.Mesh(new RoundedBoxGeometry(L.w, L.h, L.d, 4, 0.55), alu);
  base.position.set(0, L.h / 2, 0);
  base.castShadow = base.receiveShadow = true;
  laptop.add(base);
  // keyboard well
  const well = new THREE.Mesh(new RoundedBoxGeometry(27.6, 0.2, 11.6, 2, 0.08), new THREE.MeshStandardMaterial({ color: 0x0b0b0c, roughness: 0.7 }));
  well.position.set(0, L.h - 0.2, -4.0);
  laptop.add(well);
  // keys
  const keyDefs = [];
  const pitch = 1.86, cap = 1.6;
  const rows = [
    { z: -8.95, h: 0.85, keys: [1.3, ...Array(12).fill(1), 1.0] },
    { z: -7.45, h: 1, keys: [...Array(13).fill(1), 1.55] },
    { z: -5.59, h: 1, keys: [1.55, ...Array(13).fill(1)] },
    { z: -3.73, h: 1, keys: [1.85, ...Array(11).fill(1), 1.85] },
    { z: -1.87, h: 1, keys: [2.4, ...Array(10).fill(1), 2.4] },
    { z: 0.0, h: 1, keys: [1, 1, 1, 1.25, 5.3, 1.25, 1, 1, 1] },
  ];
  const keyGeo = new RoundedBoxGeometry(1, 1, 1, 3, 0.12);
  for (const r of rows) {
    const total = r.keys.reduce((a, k) => a + k * pitch, 0);
    let x = -total / 2;
    for (const kw of r.keys) {
      const w = kw * pitch - (pitch - cap);
      keyDefs.push({ x: x + (kw * pitch) / 2, z: r.z, w, d: cap * r.h, row: r });
      x += kw * pitch;
    }
  }
  const keyMat = new THREE.MeshPhysicalMaterial({ color: new THREE.Color(0.025, 0.025, 0.028), roughness: 0.52, clearcoat: 0.15, clearcoatRoughness: 0.5 });
  const keys = new THREE.InstancedMesh(keyGeo, keyMat, keyDefs.length);
  keys.castShadow = keys.receiveShadow = true;
  laptop.add(keys);
  const glowGeo = new THREE.PlaneGeometry(1, 1);
  glowGeo.rotateX(-Math.PI / 2);
  const glows = new THREE.InstancedMesh(glowGeo, new THREE.MeshBasicMaterial({ color: 0xffffff }), keyDefs.length);
  laptop.add(glows);
  const keyTop = L.h + 0.15;
  parts.keys = { defs: keyDefs, mesh: keys, glows, top: keyTop, press: new Float32Array(keyDefs.length), glow: new Float32Array(keyDefs.length) };
  parts.updateKeys = (baseGlow = 0.05, glowColor = new THREE.Color(1.0, 0.85, 0.7), hitColor = new THREE.Color(1.0, 0.28, 0.05)) => {
    const k = parts.keys, m4 = new THREE.Matrix4(), c = new THREE.Color();
    k.defs.forEach((d, i) => {
      const press = k.press[i];
      m4.compose(new THREE.Vector3(d.x, L.h + 0.04 - press * 0.06, d.z), new THREE.Quaternion(), new THREE.Vector3(d.w, 0.22, d.d));
      k.mesh.setMatrixAt(i, m4);
      m4.compose(new THREE.Vector3(d.x, L.h - 0.05, d.z), new THREE.Quaternion(), new THREE.Vector3(d.w + 0.3, 1, d.d + 0.3));
      k.glows.setMatrixAt(i, m4);
      c.copy(glowColor).multiplyScalar(baseGlow).lerp(hitColor.clone().multiplyScalar(5.0), Math.min(1, k.glow[i]));
      k.glows.setColorAt(i, c);
    });
    k.mesh.instanceMatrix.needsUpdate = true; k.glows.instanceMatrix.needsUpdate = true; k.glows.instanceColor.needsUpdate = true;
  };
  parts.keyWorld = (i) => { const d = parts.keys.defs[i]; return new THREE.Vector3(d.x, keyTop, d.z); };
  parts.updateKeys();
  // trackpad
  const pad = new THREE.Mesh(new RoundedBoxGeometry(13.4, 0.05, 8.2, 2, 0.02), new THREE.MeshPhysicalMaterial({ color: new THREE.Color(0.33, 0.34, 0.36), metalness: 0.3, roughness: 0.25 }));
  pad.position.set(0, L.h + 0.005, 5.6);
  laptop.add(pad);
  // lid
  const lid = new THREE.Group();
  lid.position.set(0, L.h, -L.d / 2 + 0.3);
  lid.rotation.x = -L.lidAngle;
  laptop.add(lid);
  const lidShell = new THREE.Mesh(new RoundedBoxGeometry(L.w, L.d - 0.4, 0.5, 4, 0.22), alu);
  lidShell.position.set(0, (L.d - 0.4) / 2 + 0.25, -0.25);
  lidShell.castShadow = lidShell.receiveShadow = true;
  lid.add(lidShell);
  const bezel = new THREE.Mesh(new RoundedBoxGeometry(L.w - 0.3, L.d - 0.7, 0.06, 2, 0.02), new THREE.MeshPhysicalMaterial({ color: 0x050505, roughness: 0.08, clearcoat: 1, clearcoatRoughness: 0.02 }));
  bezel.position.set(0, (L.d - 0.4) / 2 + 0.25, 0.03);
  lid.add(bezel);
  // screen
  const uiCanvas = document.createElement('canvas'); uiCanvas.width = UI_W; uiCanvas.height = UI_H;
  const uiCtx = uiCanvas.getContext('2d');
  const uiTex = new THREE.CanvasTexture(uiCanvas);
  uiTex.colorSpace = THREE.SRGBColorSpace; uiTex.anisotropy = 16; uiTex.generateMipmaps = true; uiTex.minFilter = THREE.LinearMipmapLinearFilter;
  const scrMat = screenMaterial(uiTex);
  const screen = new THREE.Mesh(new THREE.PlaneGeometry(L.screenW, L.screenH), scrMat);
  screen.position.set(0, (L.d - 0.4) / 2 + 0.25 + 0.55, 0.07);
  lid.add(screen);
  parts.lid = lid; parts.screen = screen; parts.screenMat = scrMat;
  let lastKey = '';
  parts.drawScreen = (state) => {
    const key = JSON.stringify({ ...state, spriteMask: undefined, maskKey: state.maskKey });
    if (key === lastKey) return;
    lastKey = key;
    drawTerminal(uiCtx, state);
    uiTex.needsUpdate = true;
  };
  parts.drawScreen({ cursor: 1 });
  // UI pixel -> world position on the screen surface
  parts.uiToWorld = (x, y, out = new THREE.Vector3()) => {
    out.set((x / UI_W - 0.5) * L.screenW, (0.5 - y / UI_H) * L.screenH, 0.08);
    screen.updateWorldMatrix(true, false);
    return out.applyMatrix4(screen.matrixWorld);
  };
  parts.screenNormal = () => new THREE.Vector3(0, 0, 1).applyQuaternion(screen.getWorldQuaternion(new THREE.Quaternion()));
  // glossy glass: a real mirror reflection of whatever is in front of the screen (layer 1 only)
  parts.enableScreenReflection = (w = 960, h = 540, strength = 1.0) => {
    const refl = new Reflector(new THREE.PlaneGeometry(L.screenW + 0.25, L.screenH + 0.25), {
      textureWidth: w, textureHeight: h, multisample: 0, clipBias: 0.0003,
      shader: {
        name: 'ScreenGlass',
        uniforms: { color: { value: null }, tDiffuse: { value: null }, textureMatrix: { value: null }, strength: { value: strength } },
        vertexShader: `uniform mat4 textureMatrix; varying vec4 vUv; varying vec3 vW; varying vec3 vN;
          void main(){ vUv = textureMatrix * vec4(position, 1.0); vW = (modelMatrix * vec4(position,1.0)).xyz; vN = normalize(mat3(modelMatrix) * vec3(0.0,0.0,1.0));
          gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }`,
        fragmentShader: `uniform sampler2D tDiffuse; uniform float strength; varying vec4 vUv; varying vec3 vW; varying vec3 vN;
          void main(){
            vec3 v = normalize(cameraPosition - vW);
            float c = clamp(dot(v, vN), 0.0, 1.0);
            float F = 0.045 + 0.955 * pow(1.0 - c, 5.0);
            vec3 r = texture2DProj(tDiffuse, vUv).rgb;
            gl_FragColor = vec4(r * F * strength, 1.0);
          }`,
      },
    });
    refl.material.transparent = true;
    refl.material.blending = THREE.AdditiveBlending;
    refl.material.depthWrite = false;
    refl.camera.layers.set(1);
    refl.position.copy(screen.position).add(new THREE.Vector3(0, 0, 0.012));
    lid.add(refl);
    parts.reflector = refl;
    // things that may appear in the glass
    for (const o of [desk, keys, glows, bulbMesh, deskBulbs, pad, base]) o.layers.enable(1);
    sky.layers.enable(1);
    return refl;
  };

  // ---- moss bowl ----
  const B = BOWL;
  const bowl = new THREE.Group(); bowl.position.set(B.x, 0, B.z); scene.add(bowl); parts.bowl = bowl;
  const prof = [];
  const outer = [[0, 0], [B.r * 0.55, 0], [B.r * 0.6, 0.15], [B.r * 0.86, 0.9], [B.r * 0.98, 2.4], [B.r * 1.02, 4.2], [B.r, B.h], [B.r * 0.96, B.h + 0.05]];
  const inner = [[B.r * 0.9, B.h - 0.1], [B.r * 0.88, 3.6], [B.r * 0.75, 1.4], [0, 1.0]];
  for (const [x, y] of outer) prof.push(new THREE.Vector2(x, y));
  for (const [x, y] of inner) prof.push(new THREE.Vector2(x, y));
  const bowlGeo = new THREE.LatheGeometry(prof, 128);
  const glaze = new THREE.MeshPhysicalMaterial({ color: new THREE.Color(0.55, 0.58, 0.5), roughness: 0.22, clearcoat: 0.8, clearcoatRoughness: 0.1 });
  glaze.onBeforeCompile = (sh) => {
    sh.vertexShader = sh.vertexShader.replace('#include <common>', '#include <common>\nvarying vec3 vOP;').replace('#include <begin_vertex>', '#include <begin_vertex>\nvOP = position;');
    sh.fragmentShader = sh.fragmentShader.replace('#include <common>', '#include <common>\nvarying vec3 vOP;\n' + NOISE)
      .replace('#include <color_fragment>', `#include <color_fragment>
        float sp = smoothstep(0.82, 0.9, vnoise(vOP * 6.0)) * 0.7 + smoothstep(0.86, 0.92, vnoise(vOP * 17.0 + 3.0));
        float drip = smoothstep(0.3, 0.7, fbm3(vec3(vOP.x * 0.6, vOP.y * 0.15, vOP.z * 0.6)));
        vec3 g1 = vec3(0.42, 0.47, 0.40), g2 = vec3(0.70, 0.66, 0.56);
        vec3 gc = mix(g1, g2, drip * smoothstep(1.5, 4.5, vOP.y));
        gc = mix(gc, vec3(0.62, 0.42, 0.28), smoothstep(B_H - 0.25, B_H, vOP.y) * 0.8);
        gc = mix(gc, vec3(0.6, 0.45, 0.32), step(vOP.y, 0.2));
        diffuseColor.rgb = gc * (1.0 - sp * 0.55);`.replace(/B_H/g, B.h.toFixed(2)));
  };
  glaze.customProgramCacheKey = () => 'glaze';
  const bowlMesh = new THREE.Mesh(bowlGeo, glaze);
  bowlMesh.castShadow = bowlMesh.receiveShadow = true;
  bowl.add(bowlMesh);
  // moss mound (local to bowl)
  const moundGeo = mossMound(B.r * 0.92, 1.25);
  const mossBase = new THREE.Mesh(moundGeo, new THREE.MeshStandardMaterial({ color: new THREE.Color(0.06, 0.13, 0.02), roughness: 1 }));
  mossBase.position.y = B.h - 0.6;
  mossBase.receiveShadow = true; mossBase.castShadow = true;
  bowl.add(mossBase);
  parts.mossHeight = (x, z) => moundGeo.userData.height(x - B.x, z - B.z) + B.h - 0.6; // world xz -> world y
  const mossFur = createFur(moundGeo, {
    count: opts.mossStrands ?? 150000, length: 0.16, width: 0.024, segs: 2, seed: 9, curl: 14, jitter: 0.45, clump: 0.5, clumpCount: 9000,
    colorFn: (p, n, r) => {
      const k = r();
      const patch = 0.5 + 0.5 * Math.sin(p.x * 0.9 + 2.0) * Math.cos(p.z * 0.8 - 1.0);
      const tip = new THREE.Color().setRGB(0.22 + 0.18 * patch + 0.08 * k, 0.40 + 0.12 * k + 0.05 * patch, 0.05 + 0.03 * k);
      if (r() < 0.06) tip.setRGB(0.5, 0.55, 0.16);
      return [new THREE.Color(0.035, 0.075, 0.012), tip];
    },
    lengthFn: () => 1, combFn: () => new THREE.Vector3(0, 0.6, 0),
    material: { sheen: 0.6, sheenColor: new THREE.Color(0.55, 0.85, 0.3), sheenRoughness: 0.5, roughness: 0.75 },
    shadowFraction: 0.2,
  });
  mossFur.userData.furUniforms.uForce.value.set(0, 0, 0);
  mossFur.userData.furUniforms.uFrizz.value = 0.1;
  mossFur.userData.furUniforms.uBackGain.value = 0.35;
  mossFur.position.y = B.h - 0.6;
  bowl.add(mossFur);
  parts.mossFur = mossFur;
  // moss sporophytes: hair-thin red stalks with tiny capsules
  {
    const nS = 160, r3 = rng(901);
    const stalk = new THREE.CylinderGeometry(0.0035, 0.005, 1, 4, 1); stalk.translate(0, 0.5, 0);
    const caps = new THREE.SphereGeometry(1, 10, 8); caps.scale(0.018, 0.04, 0.018);
    const stalks = new THREE.InstancedMesh(stalk, new THREE.MeshStandardMaterial({ color: new THREE.Color(0.35, 0.09, 0.04), roughness: 0.6 }), nS);
    const capM = new THREE.InstancedMesh(caps, new THREE.MeshPhysicalMaterial({ color: new THREE.Color(0.45, 0.22, 0.06), roughness: 0.4, clearcoat: 0.5 }), nS);
    const m4 = new THREE.Matrix4();
    for (let i = 0; i < nS; i++) {
      const a = r3() * Math.PI * 2, d = Math.sqrt(r3()) * B.r * 0.8;
      const x = Math.cos(a) * d, z = Math.sin(a) * d, y = moundGeo.userData.height(x, z) + B.h - 0.6;
      const hgt = 0.3 + r3() * 0.45;
      const q = new THREE.Quaternion().setFromEuler(new THREE.Euler((r3() - 0.5) * 0.5, 0, (r3() - 0.5) * 0.5));
      m4.compose(new THREE.Vector3(x, y, z), q, new THREE.Vector3(1, hgt, 1)); stalks.setMatrixAt(i, m4);
      const top = new THREE.Vector3(0, hgt, 0).applyQuaternion(q).add(new THREE.Vector3(x, y, z));
      m4.compose(top, q, new THREE.Vector3(1, 1, 1)); capM.setMatrixAt(i, m4);
    }
    stalks.castShadow = capM.castShadow = true;
    bowl.add(stalks, capM);
  }
  // ferns
  const fernMat = new THREE.MeshPhysicalMaterial({ color: new THREE.Color(0.10, 0.26, 0.04), roughness: 0.5, side: THREE.DoubleSide, sheen: 0.5, sheenColor: new THREE.Color(0.5, 0.8, 0.3) });
  [[-5.5, -3.5, 4.2, 7], [5.2, -4.8, 3.2, 6], [-6.5, 3.5, 2.6, 5]].forEach(([x, z, s, n], i) => {
    const f = new THREE.Mesh(fernGeometry(rng(77 + i), n, s), fernMat);
    f.position.set(x, moundGeo.userData.height(x, z) + B.h - 0.7, z);
    f.rotation.y = i * 1.7;
    f.castShadow = f.receiveShadow = true;
    bowl.add(f);
  });
  // pebbles
  const pebMat = new THREE.MeshPhysicalMaterial({ color: new THREE.Color(0.35, 0.34, 0.32), roughness: 0.55, clearcoat: 0.2 });
  [[6.8, 2.2, 0.9], [7.4, 0.6, 0.55], [-2.5, 6.4, 0.7], [-7.2, -0.5, 0.6], [2.2, -6.5, 0.8], [5.0, 5.2, 0.45]].forEach(([x, z, s], i) => {
    const g = new THREE.SphereGeometry(1, 40, 28);
    const p = g.attributes.position, v = new THREE.Vector3(), r2 = rng(300 + i);
    const a = r2() * 6, b2 = r2() * 6;
    for (let k = 0; k < p.count; k++) { v.fromBufferAttribute(p, k); const d = 1 + 0.08 * Math.sin(v.x * 3 + a) * Math.cos(v.z * 2.5 + b2); v.multiplyScalar(d); v.y *= 0.62; p.setXYZ(k, v.x, v.y, v.z); }
    g.computeVertexNormals();
    const m = new THREE.Mesh(g, pebMat);
    m.scale.setScalar(s);
    m.position.set(x, moundGeo.userData.height(x, z) + B.h - 0.45, z);
    m.rotation.y = r2() * 6;
    m.castShadow = m.receiveShadow = true;
    bowl.add(m);
  });

  // ---- props ----
  // mug
  const mugProf = [[0, 0], [3.6, 0], [3.9, 0.3], [4.0, 9], [3.75, 9.2], [3.55, 8.9], [3.5, 1.0], [0, 0.9]].map(([x, y]) => new THREE.Vector2(x, y));
  const mugMat = new THREE.MeshPhysicalMaterial({ color: new THREE.Color(0.75, 0.72, 0.66), roughness: 0.35, clearcoat: 0.6 });
  const mug = new THREE.Mesh(new THREE.LatheGeometry(mugProf, 64), mugMat);
  mug.position.set(-30, 0, -6); mug.castShadow = mug.receiveShadow = true; scene.add(mug);
  const handle = new THREE.Mesh(new THREE.TorusGeometry(2.3, 0.45, 16, 32, Math.PI * 1.2), mugMat);
  handle.position.set(-26.2, 4.6, -6); handle.rotation.z = -Math.PI * 0.6; handle.castShadow = true; scene.add(handle);
  const coffee = new THREE.Mesh(new THREE.CircleGeometry(3.52, 48), new THREE.MeshPhysicalMaterial({ color: 0x1a0d06, roughness: 0.05, clearcoat: 1 }));
  coffee.rotation.x = -Math.PI / 2; coffee.position.set(-30, 7.6, -6); scene.add(coffee);
  // pencil
  const pencil = new THREE.Group();
  const body = new THREE.Mesh(new THREE.CylinderGeometry(0.38, 0.38, 15, 6), new THREE.MeshPhysicalMaterial({ color: new THREE.Color(0.85, 0.55, 0.08), roughness: 0.4, clearcoat: 0.5 }));
  body.rotation.z = Math.PI / 2; pencil.add(body);
  const tip = new THREE.Mesh(new THREE.ConeGeometry(0.38, 1.8, 6), new THREE.MeshStandardMaterial({ color: 0xd8b48a, roughness: 0.8 }));
  tip.rotation.z = -Math.PI / 2; tip.position.x = 8.4; pencil.add(tip);
  const lead = new THREE.Mesh(new THREE.ConeGeometry(0.12, 0.55, 8), new THREE.MeshStandardMaterial({ color: 0x222222, roughness: 0.4 }));
  lead.rotation.z = -Math.PI / 2; lead.position.x = 9.3; pencil.add(lead);
  pencil.position.set(22, 0.38, 13); pencil.rotation.y = 0.5;
  pencil.traverse((o) => { o.castShadow = o.receiveShadow = true; });
  scene.add(pencil);
  // notebook
  const nb = new THREE.Mesh(new RoundedBoxGeometry(15, 1.2, 21, 2, 0.15), new THREE.MeshStandardMaterial({ color: new THREE.Color(0.12, 0.16, 0.22), roughness: 0.75 }));
  nb.position.set(-38, 0.6, 14); nb.rotation.y = 0.25; nb.castShadow = nb.receiveShadow = true; scene.add(nb);
  // books on the left
  [[0.55, 0.22, 0.12, 4.0], [0.2, 0.3, 0.42, 3.2], [0.75, 0.68, 0.55, 2.6]].reduce((y, [r, g, b, t], i) => {
    const bk = new THREE.Mesh(new RoundedBoxGeometry(24 - i * 1.5, t, 17 - i, 2, 0.2), new THREE.MeshStandardMaterial({ color: new THREE.Color(r, g, b).multiplyScalar(0.6), roughness: 0.8 }));
    bk.position.set(-52, y + t / 2, -30); bk.rotation.y = 0.1 * (i - 1); bk.castShadow = bk.receiveShadow = true; scene.add(bk);
    return y + t;
  }, 0);

  // ---- lights ----
  const moon = new THREE.DirectionalLight(new THREE.Color(0.55, 0.66, 1.0), 1.0);
  moon.position.set(60, 90, -160); moon.target.position.set(20, 0, -5);
  moon.castShadow = true; moon.shadow.mapSize.set(2048, 2048);
  Object.assign(moon.shadow.camera, { left: -60, right: 60, top: 50, bottom: -50, near: 50, far: 400 });
  moon.shadow.bias = -0.0004; moon.shadow.normalBias = 0.02;
  scene.add(moon, moon.target);
  const screenLight = new THREE.SpotLight(new THREE.Color(0.85, 0.8, 0.78), 900, 0, Math.PI * 0.42, 1.0, 2);
  screenLight.castShadow = true; screenLight.shadow.mapSize.set(2048, 2048); screenLight.shadow.bias = -0.0003; screenLight.shadow.normalBias = 0.01;
  screenLight.shadow.camera.near = 1; screenLight.shadow.camera.far = 120;
  scene.add(screenLight, screenLight.target);
  const bulbLight = new THREE.PointLight(new THREE.Color(1.0, 0.6, 0.3), 600, 0, 2);
  bulbLight.position.set((win.x0 + win.x1) / 2, win.y1 - 6, wallZ + 12);
  scene.add(bulbLight);
  // warm glow from the desk string, two soft points behind the bowl
  const glowA = new THREE.PointLight(new THREE.Color(1.0, 0.55, 0.25), 260, 0, 2);
  glowA.position.set(BOWL.x + 8, 3.5, BOWL.z - 14);
  const glowB = new THREE.PointLight(new THREE.Color(1.0, 0.55, 0.25), 200, 0, 2);
  glowB.position.set(BOWL.x - 10, 3.0, BOWL.z - 18);
  scene.add(glowA, glowB);
  // a warm lamp somewhere off to the left, very low
  const lamp = new THREE.SpotLight(new THREE.Color(1.0, 0.7, 0.45), 9000, 0, 0.6, 1.0, 2);
  lamp.position.set(-90, 70, 40); lamp.target.position.set(10, 0, -5);
  lamp.castShadow = true; lamp.shadow.mapSize.set(1024, 1024); lamp.shadow.bias = -0.0004; lamp.shadow.camera.near = 40; lamp.shadow.camera.far = 300;
  scene.add(lamp, lamp.target);
  const ambient = new THREE.HemisphereLight(new THREE.Color(0.25, 0.3, 0.45), new THREE.Color(0.12, 0.08, 0.05), 0.15);
  scene.add(ambient);
  const sun = new THREE.DirectionalLight(new THREE.Color(1.0, 0.72, 0.45), 0);
  sun.position.set(-40, 45, -200); sun.target.position.set(25, 0, -5);
  sun.castShadow = true; sun.shadow.mapSize.set(2048, 2048);
  Object.assign(sun.shadow.camera, { left: -70, right: 70, top: 60, bottom: -60, near: 50, far: 450 });
  sun.shadow.bias = -0.0004; sun.shadow.normalBias = 0.02;
  scene.add(sun, sun.target);
  // a soft fill for the moss bowl, from the front right (off by default, the bowl shots switch it on)
  const bowlFill = new THREE.SpotLight(new THREE.Color(1.0, 0.82, 0.66), 0, 0, 0.45, 1.0, 2);
  bowlFill.position.set(64, 32, 40); bowlFill.target.position.set(BOWL.x, 6, BOWL.z);
  bowlFill.castShadow = true; bowlFill.shadow.mapSize.set(1024, 1024); bowlFill.shadow.bias = -0.0004; bowlFill.shadow.normalBias = 0.01;
  bowlFill.shadow.camera.near = 20; bowlFill.shadow.camera.far = 140;
  scene.add(bowlFill, bowlFill.target);
  parts.bowlFillBase = bowlFill.position.clone();
  parts.lights = { moon, screenLight, bulbLight, ambient, sun, glowA, glowB, lamp, bowlFill };
  parts.lampBase = lamp.position.clone();
  parts.moonBase = moon.position.clone(); parts.sunBase = sun.position.clone();

  // place the screen light on the screen surface, jittered over its area for soft shadows
  parts.jitterScreenLight = (j) => {
    const p = parts.uiToWorld((0.5 + j[0] * 0.45) * UI_W, (0.5 + j[1] * 0.45) * UI_H);
    const n = parts.screenNormal();
    screenLight.position.copy(p).addScaledVector(n, 0.5);
    screenLight.target.position.copy(p).addScaledVector(n, 20);
    screenLight.target.updateMatrixWorld();
  };
  parts.jitterDirectional = (light, base, target, j, spread) => {
    const dir = new THREE.Vector3().subVectors(base, target);
    const len = dir.length(); dir.normalize();
    const t1 = new THREE.Vector3().crossVectors(dir, new THREE.Vector3(0, 1, 0)).normalize();
    const t2 = new THREE.Vector3().crossVectors(dir, t1);
    light.position.copy(base).addScaledVector(t1, j[0] * spread * len).addScaledVector(t2, j[1] * spread * len);
  };

  // environment for reflections: dark room, window, screen glow
  parts.envNight = makeRoomEnv(renderer, 0);
  parts.envDawn = makeRoomEnv(renderer, 1);
  scene.environment = parts.envNight;
  scene.environmentIntensity = 1.0;

  parts.setDawn = (k, t = 0, sunElev = 0.21) => {
    sky.material.userData.uniforms.uDawn.value = k;
    const sdir = new THREE.Vector3(0.15, sunElev, -1).normalize();
    parts.sunDir = sdir;
    sky.material.userData.uniforms.uSun.value.copy(sdir);
    parts.sunBase.copy(sun.target.position).addScaledVector(sdir, 220);
    sky.material.userData.uniforms.uTime.value = t;
    moon.intensity = 2.2 * (1 - k);
    lamp.intensity = 9000 * (1 - k * 0.7);
    sun.intensity = 14.0 * k;
    ambient.intensity = 0.15 + 0.04 * k;
    ambient.color.setRGB(0.25 + 0.6 * k, 0.3 + 0.45 * k, 0.45 + 0.2 * k);
    scene.environment = k > 0.5 ? parts.envDawn : parts.envNight;
    scene.environmentIntensity = 1.0 + 0.2 * k;
    const fb = 40 * (1 - 0.75 * k);
    for (let i = 0; i < nB; i++) bulbMesh.setColorAt(i, new THREE.Color(1.0, 0.55, 0.22).multiplyScalar(fb));
    for (let i = 0; i < nD; i++) deskBulbs.setColorAt(i, new THREE.Color(1.0, 0.55, 0.22).multiplyScalar(fb));
    bulbMesh.instanceColor.needsUpdate = true; deskBulbs.instanceColor.needsUpdate = true;
    parts.haloMat.color.setRGB(1.0, 0.55, 0.22).multiplyScalar(1.6 * (1 - 0.75 * k));
    glowA.intensity = 260 * (1 - 0.8 * k); glowB.intensity = 200 * (1 - 0.8 * k);
    BACKLIGHT.dir.copy(parts.sunDir || new THREE.Vector3(0, 1, 0)); BACKLIGHT.strength = k;
  };
  parts.setDawn(0);
  // the per-sub-frame light rig shared by every shot
  parts.stdUpdate = (t, ctx, o = {}) => {
    const dawn = o.dawn ?? 0;
    parts.setDawn(dawn, t, o.sunElev ?? 0.21);
    parts.jitterScreenLight(ctx.lightJitter);
    parts.jitterDirectional(moon, parts.moonBase, moon.target.position, [ctx.rand(0) * 2 - 1, ctx.rand(1) * 2 - 1], 0.01);
    parts.jitterDirectional(sun, parts.sunBase, sun.target.position, [ctx.rand(1) * 2 - 1, ctx.rand(0) * 2 - 1], 0.012);
    sun.castShadow = dawn > 0.01; moon.castShadow = dawn < 0.99;
    lamp.castShadow = !!o.lampShadow;
    lamp.position.copy(parts.lampBase).add(new THREE.Vector3(ctx.rand(2) - 0.5, ctx.rand(3) - 0.5, 0).multiplyScalar(25));
    lamp.intensity = (o.lamp ?? 30000) * (1 - dawn);
    screenLight.intensity = (o.screen ?? 900) * (1 - dawn * 0.85);
    if (o.screenState !== false) {
      const blink = 0.5 + 0.5 * Math.cos((t % 1.06) / 1.06 * Math.PI * 2);
      const cursor = blink < 0.35 ? 0 : blink > 0.65 ? 1 : (blink - 0.35) / 0.3;
      parts.drawScreen({ cursor, maskKey: o.maskKey ?? 'all', spriteMask: o.spriteMask ?? (() => false), showJolly: o.showJolly ?? 0 });
    }
    parts.screenMat.userData.uniforms.uBright.value = o.screenBright ?? 2.2;
  };
  return { scene, parts };
}

function makeRoomEnv(renderer, dawn) {
  const s = new THREE.Scene();
  const room = new THREE.Mesh(new THREE.BoxGeometry(400, 200, 300), new THREE.MeshBasicMaterial({ color: new THREE.Color(0.012, 0.012, 0.016).lerp(new THREE.Color(0.10, 0.075, 0.06), dawn), side: THREE.BackSide }));
  room.position.set(0, 60, 40);
  s.add(room);
  const win = new THREE.Mesh(new THREE.PlaneGeometry(90, 90), new THREE.MeshBasicMaterial({ color: new THREE.Color(0.03, 0.05, 0.12).lerp(new THREE.Color(3.0, 2.0, 1.3), dawn) }));
  win.position.set(48, 60, -109); s.add(win);
  const scr = new THREE.Mesh(new THREE.PlaneGeometry(30, 19), new THREE.MeshBasicMaterial({ color: new THREE.Color(0.35, 0.33, 0.32) }));
  scr.position.set(0, 12, -20); scr.lookAt(0, 10, 50); s.add(scr);
  const desk = new THREE.Mesh(new THREE.PlaneGeometry(300, 200), new THREE.MeshBasicMaterial({ color: new THREE.Color(0.02, 0.012, 0.008).lerp(new THREE.Color(0.25, 0.14, 0.08), dawn) }));
  desk.rotation.x = -Math.PI / 2; desk.position.y = -5; s.add(desk);
  const pm = new THREE.PMREMGenerator(renderer);
  const tex = pm.fromScene(s, 0, 0.1, 1000).texture;
  pm.dispose();
  return tex;
}
