// Offline "distributed" rasteriser. Every output frame is the average of N sub-frames,
// each with its own shutter time, sub-pixel offset, lens position and light position,
// which gives real motion blur, depth of field, anti-aliasing and soft shadows.
import * as THREE from 'three';

const FS_VERT = /* glsl */`
varying vec2 vUv;
void main(){ vUv = uv; gl_Position = vec4(position.xy, 0.0, 1.0); }`;

function fsMaterial(frag, uniforms, extra = {}) {
  return new THREE.ShaderMaterial({
    vertexShader: FS_VERT, fragmentShader: frag, uniforms,
    depthTest: false, depthWrite: false, ...extra,
  });
}

// low-discrepancy helpers
export function halton(i, b) { let f = 1, r = 0; while (i > 0) { f /= b; r += f * (i % b); i = Math.floor(i / b); } return r; }
export function concentricDisk(u, v) {
  const a = 2 * u - 1, b = 2 * v - 1;
  if (a === 0 && b === 0) return [0, 0];
  let r, phi;
  if (a * a > b * b) { r = a; phi = (Math.PI / 4) * (b / a); } else { r = b; phi = Math.PI / 2 - (Math.PI / 4) * (a / b); }
  return [r * Math.cos(phi), r * Math.sin(phi)];
}

const BLOOM_PREFILTER = /* glsl */`
uniform sampler2D tSrc; uniform vec2 texel; uniform float threshold, knee;
varying vec2 vUv;
vec3 s(vec2 o){ return texture2D(tSrc, vUv + o*texel).rgb; }
void main(){
  // 13-tap downsample (Jimenez 2014) with a soft-knee threshold
  vec3 a=s(vec2(-2,-2)),b=s(vec2(0,-2)),c=s(vec2(2,-2)),d=s(vec2(-1,-1)),e=s(vec2(1,-1)),f=s(vec2(-2,0)),g=s(vec2(0,0)),
       h=s(vec2(2,0)),i=s(vec2(-1,1)),j=s(vec2(1,1)),k=s(vec2(-2,2)),l=s(vec2(0,2)),m=s(vec2(2,2));
  vec3 col = (d+e+i+j)*0.125 + (a+b+g+f)*0.03125 + (b+c+h+g)*0.03125 + (f+g+l+k)*0.03125 + (g+h+m+l)*0.03125;
  float br = max(col.r, max(col.g, col.b));
  float rq = clamp(br - threshold + knee, 0.0, 2.0*knee); rq = rq*rq/(4.0*knee+1e-5);
  float w = max(rq, br - threshold) / max(br, 1e-5);
  gl_FragColor = vec4(min(col*w, vec3(64.0)), 1.0);
}`;
const BLOOM_DOWN = /* glsl */`
uniform sampler2D tSrc; uniform vec2 texel; varying vec2 vUv;
vec3 s(vec2 o){ return texture2D(tSrc, vUv + o*texel).rgb; }
void main(){
  vec3 a=s(vec2(-2,-2)),b=s(vec2(0,-2)),c=s(vec2(2,-2)),d=s(vec2(-1,-1)),e=s(vec2(1,-1)),f=s(vec2(-2,0)),g=s(vec2(0,0)),
       h=s(vec2(2,0)),i=s(vec2(-1,1)),j=s(vec2(1,1)),k=s(vec2(-2,2)),l=s(vec2(0,2)),m=s(vec2(2,2));
  gl_FragColor = vec4((d+e+i+j)*0.125 + (a+b+g+f)*0.03125 + (b+c+h+g)*0.03125 + (f+g+l+k)*0.03125 + (g+h+m+l)*0.03125, 1.0);
}`;
const BLOOM_UP = /* glsl */`
uniform sampler2D tSrc; uniform sampler2D tAdd; uniform vec2 texel; uniform float radius; varying vec2 vUv;
vec3 s(vec2 o){ return texture2D(tSrc, vUv + o*texel*radius).rgb; }
void main(){
  vec3 c = s(vec2(-1,-1)) + 2.0*s(vec2(0,-1)) + s(vec2(1,-1)) + 2.0*s(vec2(-1,0)) + 4.0*s(vec2(0,0))
         + 2.0*s(vec2(1,0)) + s(vec2(-1,1)) + 2.0*s(vec2(0,1)) + s(vec2(1,1));
  gl_FragColor = vec4(c/16.0 + texture2D(tAdd, vUv).rgb, 1.0);
}`;

const RAYS = /* glsl */`
uniform sampler2D tSrc; uniform vec2 sun; uniform float threshold, decay, aspect; varying vec2 vUv;
void main(){
  vec2 d = (sun - vUv);
  vec3 acc = vec3(0.0); float w = 1.0;
  const int N = 96;
  vec2 st = d / float(N);
  float j = fract(sin(dot(gl_FragCoord.xy, vec2(12.9898, 78.233))) * 43758.5453);
  vec2 uv = vUv + st * j;
  for (int i = 0; i < N; i++){
    uv += st;
    vec3 c = texture2D(tSrc, clamp(uv, 0.0, 1.0)).rgb;
    float l = dot(c, vec3(0.2126, 0.7152, 0.0722));
    float near = smoothstep(0.22, 0.04, length((uv - sun) * vec2(aspect, 1.0)));
    acc += c * smoothstep(threshold, threshold * 3.0, l) * w * near;
    w *= decay;
  }
  gl_FragColor = vec4(acc / float(N), 1.0);
}`;
const COMPOSITE = /* glsl */`
uniform sampler2D tHDR; uniform sampler2D tBloom; uniform sampler2D tRays; uniform float raysStrength;
uniform float exposure, bloomStrength, saturation, contrast, vignette, grain, ca, time, fade;
uniform vec3 lift, gamma, gain, whiteBalance, tintShadows, tintHighlights;
uniform vec2 res;
varying vec2 vUv;

// AgX (Troy Sobotka) with polynomial fit of the default contrast curve
vec3 agxDefaultContrastApprox(vec3 x){
  vec3 x2 = x*x; vec3 x4 = x2*x2;
  return + 15.5*x4*x2 - 40.14*x4*x + 31.96*x4 - 6.868*x2*x + 0.4298*x2 + 0.1191*x - 0.00232;
}
vec3 agx(vec3 val){
  const mat3 agx_mat = mat3(0.842479062253094, 0.0423282422610123, 0.0423756549057051,
                            0.0784335999999992, 0.878468636469772, 0.0784336,
                            0.0792237451477643, 0.0791661274605434, 0.879142973793104);
  const float min_ev = -12.47393, max_ev = 4.026069;
  val = agx_mat * val;
  val = clamp(log2(max(val, 1e-10)), min_ev, max_ev);
  val = (val - min_ev) / (max_ev - min_ev);
  return agxDefaultContrastApprox(val);
}
vec3 agxEotf(vec3 val){
  const mat3 agx_mat_inv = mat3(1.19687900512017, -0.0528968517574562, -0.0529716355144438,
                                -0.0980208811401368, 1.15190312990417, -0.0980434501171241,
                                -0.0990297440797205, -0.0989611768448433, 1.15107367264116);
  val = agx_mat_inv * val;
  return pow(max(val, 0.0), vec3(2.2));
}
float hash12(vec2 p){ vec3 p3 = fract(vec3(p.xyx) * .1031); p3 += dot(p3, p3.yzx + 33.33); return fract((p3.x + p3.y) * p3.z); }
vec3 srgb(vec3 c){ return mix(c*12.92, 1.055*pow(c, vec3(1.0/2.4)) - 0.055, step(0.0031308, c)); }

void main(){
  vec2 uv = vUv;
  vec2 d = uv - 0.5;
  // subtle lateral chromatic aberration
  vec3 hdr;
  if (ca > 0.0) {
    vec2 off = d * ca * dot(d,d);
    hdr = vec3(texture2D(tHDR, uv - off).r, texture2D(tHDR, uv).g, texture2D(tHDR, uv + off).b);
  } else hdr = texture2D(tHDR, uv).rgb;
  vec3 col = hdr + texture2D(tBloom, uv).rgb * bloomStrength + texture2D(tRays, uv).rgb * raysStrength;
  col *= exposure * whiteBalance;
  // vignette (natural cos^4-ish falloff)
  float v = 1.0 - vignette * smoothstep(0.15, 0.95, length(d*vec2(1.0, res.y/res.x)*1.6));
  col *= v;
  // look: AgX
  vec3 a = agx(col);
  // contrast + saturation in AgX log space
  a = (a - 0.5) * contrast + 0.5;
  float l = dot(a, vec3(0.2126, 0.7152, 0.0722));
  a = mix(vec3(l), a, saturation);
  a = clamp(a, 0.0, 1.0);
  vec3 lin = agxEotf(a);
  // split toning + lift/gamma/gain
  float L = dot(lin, vec3(0.2126, 0.7152, 0.0722));
  lin *= mix(tintShadows, tintHighlights, smoothstep(0.0, 0.6, L));
  lin = pow(max(gain * (lin + lift * (1.0 - lin)), 0.0), 1.0 / gamma);
  vec3 o = srgb(clamp(lin, 0.0, 1.0));
  // film grain, stronger in mids
  float g = hash12(gl_FragCoord.xy + fract(time*7.31)*913.0) + hash12(gl_FragCoord.xy*1.37 + fract(time*3.17)*577.0) - 1.0;
  float lw = 4.0 * L * (1.0 - L) + 0.15;
  o += g * grain * lw;
  o *= fade;
  // dither to kill banding
  o += (hash12(gl_FragCoord.xy + time) - 0.5) / 255.0;
  gl_FragColor = vec4(o, 1.0);
}`;

export const DEFAULT_LOOK = {
  exposure: 1.0, bloomStrength: 0.04, bloomThreshold: 1.0, bloomKnee: 0.6, bloomRadius: 1.0,
  saturation: 1.05, contrast: 1.0, vignette: 0.35, grain: 0.018, ca: 0.0, fade: 1.0,
  lift: [0, 0, 0], gamma: [1, 1, 1], gain: [1, 1, 1], whiteBalance: [1, 1, 1],
  tintShadows: [1, 1, 1], tintHighlights: [1, 1, 1],
};

export class FilmRenderer {
  constructor({ width, height, canvas, msaa = 4 }) {
    this.width = width; this.height = height;
    const r = this.renderer = new THREE.WebGLRenderer({
      canvas, antialias: false, preserveDrawingBuffer: true, alpha: false, powerPreference: 'high-performance',
    });
    r.setPixelRatio(1); r.setSize(width, height, false);
    r.outputColorSpace = THREE.LinearSRGBColorSpace;
    r.toneMapping = THREE.NoToneMapping;
    r.shadowMap.enabled = true; r.shadowMap.type = THREE.PCFShadowMap; r.shadowMap.autoUpdate = true;
    r.autoClear = false; // every target is cleared explicitly; the accumulation pass must not be cleared

    const hdrOpts = { type: THREE.HalfFloatType, format: THREE.RGBAFormat, minFilter: THREE.LinearFilter, magFilter: THREE.LinearFilter, depthBuffer: true };
    this.sceneRT = new THREE.WebGLRenderTarget(width, height, { ...hdrOpts, samples: msaa });
    this.accumRT = new THREE.WebGLRenderTarget(width, height, { ...hdrOpts, type: THREE.FloatType, depthBuffer: false });

    this.quadCam = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);
    this.quad = new THREE.Mesh(new THREE.PlaneGeometry(2, 2));
    this.quad.frustumCulled = false;
    this.quadScene = new THREE.Scene(); this.quadScene.add(this.quad);

    this.accumMat = fsMaterial(`uniform sampler2D tSrc; uniform float w; varying vec2 vUv;
      void main(){ vec3 c = texture2D(tSrc, vUv).rgb; if (any(isnan(c)) || any(isinf(c))) c = vec3(0.0); c = clamp(c, vec3(0.0), vec3(256.0)); gl_FragColor = vec4(c*w, 1.0); }`,
      { tSrc: { value: null }, w: { value: 1 } },
      { blending: THREE.CustomBlending, blendEquation: THREE.AddEquation, blendSrc: THREE.OneFactor, blendDst: THREE.OneFactor });

    // bloom pyramid
    this.bloomMips = [];
    let bw = width >> 1, bh = height >> 1;
    for (let i = 0; i < 7 && bw > 4 && bh > 4; i++) {
      this.bloomMips.push({
        down: new THREE.WebGLRenderTarget(bw, bh, { ...hdrOpts, depthBuffer: false }),
        up: new THREE.WebGLRenderTarget(bw, bh, { ...hdrOpts, depthBuffer: false }),
        w: bw, h: bh,
      });
      bw >>= 1; bh >>= 1;
    }
    this.prefilterMat = fsMaterial(BLOOM_PREFILTER, { tSrc: { value: null }, texel: { value: new THREE.Vector2() }, threshold: { value: 1 }, knee: { value: 0.5 } });
    this.downMat = fsMaterial(BLOOM_DOWN, { tSrc: { value: null }, texel: { value: new THREE.Vector2() } });
    this.upMat = fsMaterial(BLOOM_UP, { tSrc: { value: null }, tAdd: { value: null }, texel: { value: new THREE.Vector2() }, radius: { value: 1 } });

    this.compMat = fsMaterial(COMPOSITE, {
      tHDR: { value: null }, tBloom: { value: null }, tRays: { value: null }, raysStrength: { value: 0 }, res: { value: new THREE.Vector2(width, height) },
      exposure: { value: 1 }, bloomStrength: { value: 0.05 }, saturation: { value: 1 }, contrast: { value: 1 },
      vignette: { value: 0.3 }, grain: { value: 0.02 }, ca: { value: 0 }, time: { value: 0 }, fade: { value: 1 },
      lift: { value: new THREE.Vector3() }, gamma: { value: new THREE.Vector3(1, 1, 1) }, gain: { value: new THREE.Vector3(1, 1, 1) },
      whiteBalance: { value: new THREE.Vector3(1, 1, 1) }, tintShadows: { value: new THREE.Vector3(1, 1, 1) }, tintHighlights: { value: new THREE.Vector3(1, 1, 1) },
    });
    this.extraPasses = [];
    this.raysRT = new THREE.WebGLRenderTarget(width >> 1, height >> 1, { ...hdrOpts, depthBuffer: false });
    this.raysMat = fsMaterial(RAYS, { tSrc: { value: null }, sun: { value: new THREE.Vector2(0.5, 0.5) }, threshold: { value: 3 }, decay: { value: 0.97 }, aspect: { value: width / height } }); // per-subframe passes added to the scene buffer (e.g. volumetric light)
  }

  blit(mat, target) {
    this.quad.material = mat;
    this.renderer.setRenderTarget(target);
    this.renderer.render(this.quadScene, this.quadCam);
  }

  // Apply sub-pixel jitter and thin-lens offset to a perspective camera (after its matrices are up to date).
  jitterCamera(camera, jx, jy, lensX, lensY, focusDist) {
    if (lensX || lensY) {
      const right = new THREE.Vector3().setFromMatrixColumn(camera.matrixWorld, 0);
      const up = new THREE.Vector3().setFromMatrixColumn(camera.matrixWorld, 1);
      camera.position.addScaledVector(right, lensX).addScaledVector(up, lensY);
      camera.updateMatrixWorld(true);
    }
    camera.updateProjectionMatrix();
    const e = camera.projectionMatrix.elements;
    e[8] -= e[0] * lensX / focusDist;
    e[9] -= e[5] * lensY / focusDist;
    e[8] += 2 * jx / this.width;
    e[9] += 2 * jy / this.height;
    camera.projectionMatrixInverse.copy(camera.projectionMatrix).invert();
  }

  // shot: { scene, camera, update(t, ctx), lens: {fstop, focalLength(mm), focus}, shutter }
  renderFrame(shot, t, { samples = 16, shutter = 0.5 / 24, frameIndex = 0, onlySub = -1 } = {}) {
    const r = this.renderer;
    r.setRenderTarget(this.accumRT); r.setClearColor(0x000000, 1); r.clear();
    const N = samples;
    for (let s = 0; s < N; s++) {
      if (onlySub >= 0 && s !== onlySub) continue;
      // Cranley-Patterson rotation per frame keeps patterns from repeating frame to frame
      const rot = (k) => (halton(frameIndex + 1, k === 0 ? 17 : k === 1 ? 19 : k === 2 ? 23 : k === 3 ? 29 : 31));
      const fr = (x, k) => (x + rot(k)) % 1;
      const ts = t + ((s + fr(halton(s + 1, 37) * 0.999, 4)) / N - 0.5) * shutter;
      const jx = fr(halton(s + 1, 2), 0) - 0.5, jy = fr(halton(s + 1, 3), 1) - 0.5;
      const [lx, ly] = concentricDisk(fr(halton(s + 1, 5), 2), fr(halton(s + 1, 7), 3));
      const ctx = {
        sub: s, samples: N, frameIndex,
        lightJitter: [halton(s + 1, 11) * 2 - 1, halton(s + 1, 13) * 2 - 1],
        rand: (k) => fr(halton(s + 1, [41, 43, 47, 53, 59, 61][k % 6]), k % 5),
      };
      shot.update(ts, ctx);
      const cam = shot.camera;
      cam.updateMatrixWorld(true);
      const lens = shot.lens || {};
      let apR = 0;
      if (lens.fstop && lens.focus) {
        const fmm = lens.focalLength || 50;
        apR = (fmm / 10) / (2 * lens.fstop) * (lens.apertureScale ?? 0.22); // aperture radius in cm; stopped down for tabletop macro
      }
      const savedPos = cam.position.clone();
      this.jitterCamera(cam, jx, jy, lx * apR, ly * apR * (lens.anamorphic ?? 1), lens.focus || 100);
      r.setRenderTarget(this.sceneRT);
      r.setClearColor(shot.clearColor ?? 0x000000, 1);
      r.clear();
      r.render(shot.scene, cam);
      for (const p of this.extraPasses) p(this, shot, ctx);
      cam.position.copy(savedPos); cam.updateMatrixWorld(true); cam.updateProjectionMatrix();
      this.accumMat.uniforms.tSrc.value = this.sceneRT.texture;
      // 0.25 keeps the exposure calibration the looks were tuned with
      this.accumMat.uniforms.w.value = 0.25 * (onlySub >= 0 ? 1 : 1 / N);
      this.blit(this.accumMat, this.accumRT);
    }
    this.post(shot.look || {}, t);
  }

  post(lookIn, t) {
    const look = { ...DEFAULT_LOOK, ...lookIn };
    const mips = this.bloomMips;
    // bloom
    this.prefilterMat.uniforms.tSrc.value = this.accumRT.texture;
    this.prefilterMat.uniforms.texel.value.set(1 / this.width, 1 / this.height);
    this.prefilterMat.uniforms.threshold.value = look.bloomThreshold;
    this.prefilterMat.uniforms.knee.value = look.bloomKnee;
    this.blit(this.prefilterMat, mips[0].down);
    for (let i = 1; i < mips.length; i++) {
      this.downMat.uniforms.tSrc.value = mips[i - 1].down.texture;
      this.downMat.uniforms.texel.value.set(1 / mips[i - 1].w, 1 / mips[i - 1].h);
      this.blit(this.downMat, mips[i].down);
    }
    let src = mips[mips.length - 1].down;
    for (let i = mips.length - 2; i >= 0; i--) {
      this.upMat.uniforms.tSrc.value = src.texture;
      this.upMat.uniforms.tAdd.value = mips[i].down.texture;
      this.upMat.uniforms.texel.value.set(1 / mips[i + 1].w, 1 / mips[i + 1].h);
      this.upMat.uniforms.radius.value = look.bloomRadius;
      this.blit(this.upMat, mips[i].up);
      src = mips[i].up;
    }
    const u = this.compMat.uniforms;
    u.raysStrength.value = look.godRays || 0;
    if (look.godRays) {
      this.raysMat.uniforms.tSrc.value = this.accumRT.texture;
      this.raysMat.uniforms.sun.value.fromArray(look.sunUV || [0.5, 0.5]);
      this.raysMat.uniforms.threshold.value = look.godThreshold ?? 3;
      this.blit(this.raysMat, this.raysRT);
    }
    u.tRays.value = this.raysRT.texture;
    u.tHDR.value = this.accumRT.texture; u.tBloom.value = src.texture;
    for (const k of ['exposure', 'bloomStrength', 'saturation', 'contrast', 'vignette', 'grain', 'ca', 'fade']) u[k].value = look[k];
    for (const k of ['lift', 'gamma', 'gain', 'whiteBalance', 'tintShadows', 'tintHighlights']) u[k].value.fromArray(look[k]);
    u.time.value = t;
    this.blit(this.compMat, null);
  }

  readPixels() {
    const gl = this.renderer.getContext();
    const px = new Uint8Array(this.width * this.height * 4);
    gl.readPixels(0, 0, this.width, this.height, gl.RGBA, gl.UNSIGNED_BYTE, px);
    return px;
  }
}
