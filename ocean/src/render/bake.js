// GPU texture baker: tileable procedural textures computed once at load.

import * as THREE from 'three/webgpu';
import { Fn, instanceIndex, uint, int, uvec2, vec2, vec4, float, textureStore, texture, clamp, storageTexture } from 'three/tsl';

export function makeStorage(size, { name = 'baked', type = THREE.UnsignedByteType, wrap = THREE.RepeatWrapping, mips = true, layers = 0 } = {}) {
  const t = layers > 0 ? new THREE.StorageArrayTexture(size, size, layers) : new THREE.StorageTexture(size, size);
  t.format = THREE.RGBAFormat;
  t.type = type;
  t.wrapS = t.wrapT = wrap;
  t.magFilter = THREE.LinearFilter;
  t.minFilter = mips ? THREE.LinearMipmapLinearFilter : THREE.LinearFilter;
  t.generateMipmaps = mips;
  // StorageArrayTexture does not declare this flag, so compute writes would
  // never regenerate its mip chain
  t.mipmapsAutoUpdate = mips;
  t.anisotropy = 8;
  t.name = name;
  return t;
}

/**
 * Runs fn(uv, texel) -> vec4 for every texel of a new storage texture.
 * uv is the texel centre in [0,1).
 */
export function bake(renderer, size, fn, opts = {}) {
  const tex = makeStorage(size, opts);
  const kernel = Fn(() => {
    const S = uint(size);
    const x = instanceIndex.mod(S), y = instanceIndex.div(S);
    const uv = vec2(float(x), float(y)).add(0.5).div(size);
    const v = fn(uv, vec2(float(x), float(y)));
    textureStore(tex, uvec2(x, y), opts.type === THREE.HalfFloatType ? v : clamp(v, 0, 1));
  })().compute(size * size, [64]);
  renderer.compute(kernel);
  return tex;
}

/** Bakes one layer of an array storage texture. */
export function bakeLayer(renderer, tex, size, layer, fn) {
  const kernel = Fn(() => {
    const S = uint(size);
    const x = instanceIndex.mod(S), y = instanceIndex.div(S);
    const uv = vec2(float(x), float(y)).add(0.5).div(size);
    const v = fn(uv);
    textureStore(storageTexture(tex).depth(int(layer)), uvec2(x, y), clamp(v, 0, 1));
  })().compute(size * size, [64]);
  renderer.compute(kernel);
}

/** tangent-space normal (xy packed) from a baked height channel, wrapping */
export function normalFromHeight(renderer, heightTex, size, strength, channel = 'x', extra = null, opts = {}) {
  return bake(renderer, size, (uv) => {
    const e = 1 / size;
    const h = (o) => texture(heightTex, uv.add(o)).level(0)[channel];
    const dx = h(vec2(e, 0)).sub(h(vec2(-e, 0))).mul(strength);
    const dy = h(vec2(0, e)).sub(h(vec2(0, -e))).mul(strength);
    const n = vec2(dx.negate(), dy.negate()).mul(0.5).add(0.5);
    const hc = h(vec2(0, 0));
    return extra ? extra(uv, n, hc) : vec4(n, hc, 1);
  }, opts);
}
