// Caustics from the actual wave surface (Evan Wallace's area-ratio method).
//
// A grid covering one tile of the fine FFT cascade refracts the sun through
// the surface normals and projects each vertex onto a plane FOCUS metres
// down. Each triangle's brightness is (area before / area after), added into
// a tileable render target, so the pattern is energy conserving, animates
// with the real waves and has no finite edge. Underwater surfaces sample it
// along the refracted sun ray, blurred and flattened with depth.

import * as THREE from 'three/webgpu';
import {
  Fn, attribute, uniform, vec2, vec3, vec4, float, texture, normalize, refract, varying, dFdx, dFdy,
  length, cross, clamp, instanceIndex, positionGeometry, exp, mix, max, smoothstep, log2, fract, min,
  cameraPosition,
} from 'three/tsl';
import { env } from '../env.js';

const FOCUS = 3.5;
const GRID = 192;
const SIZE = 512;

export class Caustics {
  constructor(renderer, ocean) {
    this.renderer = renderer;
    this.ocean = ocean;
    this.cascade = 2;
    this.L = ocean.lengthScales[this.cascade];
    this.target = new THREE.RenderTarget(SIZE, SIZE, {
      type: THREE.HalfFloatType, depthBuffer: false, generateMipmaps: true,
      minFilter: THREE.LinearMipmapLinearFilter, magFilter: THREE.LinearFilter,
      wrapS: THREE.RepeatWrapping, wrapT: THREE.RepeatWrapping,
    });
    this.target.texture.name = 'caustics';
    this.intensity = uniform(1);
    this.pixelAngle = uniform(0.0015);   // metres per pixel per metre of distance
    this._size = new THREE.Vector2();
    this._build();
  }

  _build() {
    // grid geometry (positions in tile uv), 9 instances cover wrap-around
    const g = new THREE.InstancedBufferGeometry();
    const V = GRID + 1;
    const pos = new Float32Array(V * V * 3);
    for (let j = 0; j < V; j++) for (let i = 0; i < V; i++) {
      const k = (j * V + i) * 3;
      pos[k] = i / GRID; pos[k + 1] = j / GRID; pos[k + 2] = 0;
    }
    const idx = [];
    for (let j = 0; j < GRID; j++) for (let i = 0; i < GRID; i++) {
      const a = j * V + i, b = a + 1, c = a + V, d = c + 1;
      idx.push(a, b, d, a, d, c);
    }
    g.setIndex(idx);
    g.setAttribute('position', new THREE.BufferAttribute(pos, 3));
    const offs = new Float32Array(18);
    let o = 0;
    for (let y = -1; y <= 1; y++) for (let x = -1; x <= 1; x++) { offs[o++] = x; offs[o++] = y; }
    g.setAttribute('tileOffset', new THREE.InstancedBufferAttribute(offs, 2));
    g.instanceCount = 9;

    const mat = new THREE.NodeMaterial();
    mat.name = 'caustics';
    mat.depthTest = false; mat.depthWrite = false;
    mat.blending = THREE.AdditiveBlending;
    mat.side = THREE.DoubleSide;
    const L = this.L;
    const der = this.ocean.fft.derivatives[this.cascade];
    const uvRest = positionGeometry.xy;
    const d = texture(der, uvRest).level(0);
    const n = normalize(vec3(d.x.div(d.z.add(1)).negate(), 1, d.y.div(d.w.add(1)).negate()));
    const sunDown = normalize(env.sunDir.negate().add(vec3(0, -0.2, 0)));
    const t = refract(sunDown, n, 1 / 1.333);
    const t0 = refract(sunDown, vec3(0, 1, 0), 1 / 1.333);
    const hit = uvRest.mul(L).add(t.xz.mul(FOCUS / 1).div(t.y.negate().max(0.2)));
    const hit0 = t0.xz.mul(FOCUS).div(t0.y.negate().max(0.2));
    const uvHit = hit.sub(hit0).div(L).add(attribute('tileOffset', 'vec2'));
    mat.vertexNode = vec4(uvHit.mul(2).sub(1).mul(vec2(1, -1)), 0, 1);
    const vRest = varying(vec3(uvRest.mul(L), 0), 'vCausticRest');
    const vHit = varying(vec3(uvHit.mul(L), 0), 'vCausticHit');
    mat.fragmentNode = Fn(() => {
      const a0 = length(cross(dFdx(vRest), dFdy(vRest)));
      const a1 = length(cross(dFdx(vHit), dFdy(vHit))).max(1e-9);
      const ratio = clamp(a0.div(a1), 0, 12);
      return vec4(ratio, ratio, ratio, 1);
    })();
    this.mesh = new THREE.Mesh(g, mat);
    this.mesh.frustumCulled = false;
    this.scene = new THREE.Scene();
    this.scene.add(this.mesh);
    this.cam = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);
  }

  update(camera = null) {
    const r = this.renderer;
    if (camera) this.pixelAngle.value = 2 * Math.tan(THREE.MathUtils.degToRad(camera.fov) / 2) / Math.max(r.getDrawingBufferSize(this._size).y, 1);
    const prev = r.getRenderTarget();
    const prevClear = r.getClearColor(new THREE.Color());
    const prevAlpha = r.getClearAlpha();
    r.setRenderTarget(this.target);
    r.setClearColor(0x000000, 1);
    r.clear();
    r.render(this.scene, this.cam);
    r.setRenderTarget(prev);
    r.setClearColor(prevClear, prevAlpha);
  }

  /**
   * TSL: caustic light factor (mean ~1) for a point `depth` metres under the
   * surface. Two decorrelated lookups break the tile repetition.
   */
  sample(pWorld, depth) {
    const sunDown = normalize(env.sunDir.negate().add(vec3(0, -0.2, 0)));
    const t0 = refract(sunDown, vec3(0, 1, 0), 1 / 1.333);
    const shift = t0.xz.mul(depth.sub(FOCUS)).div(t0.y.negate().max(0.2));
    const p = pWorld.xz.sub(shift);
    const defocus = log2(float(1).add(max(depth.sub(FOCUS), 0).mul(0.9)).add(max(float(FOCUS).sub(depth), 0).mul(1.8))).add(0.4);
    // never finer than a screen pixel (derivative-free, so it is safe in any
    // lighting branch): distant seabed averages out instead of aliasing
    const footprint = length(cameraPosition.sub(pWorld)).mul(this.pixelAngle).mul(1.6);
    const blur = max(defocus, log2(footprint.div(this.L / SIZE)));
    const c1 = texture(this.target.texture, p.div(this.L)).level(blur).r;
    const q = vec2(p.x.mul(0.8).sub(p.y.mul(0.6)), p.x.mul(0.6).add(p.y.mul(0.8)));
    const c2 = texture(this.target.texture, q.div(this.L * 1.37).add(0.31)).level(blur).r;
    const c = c1.mul(0.62).add(c2.mul(0.38));
    // contrast falls with depth as the pattern defocuses and scattering fills in
    const contrast = exp(depth.negate().div(14)).mul(smoothstep(0.0, 0.4, depth)).mul(this.intensity);
    return max(mix(float(1), c, contrast), 0);
  }
}
