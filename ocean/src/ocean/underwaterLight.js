// Light reaching submerged surfaces: sunlight refracted down through the
// water column (spectral Beer-Lambert along the refracted path, modulated by
// caustics) and sky light attenuated with depth. Hooked into every lit
// material through the pipeline's sun-shadow and AO contexts, so the
// flashlight and other local lights are unaffected.

import { float, vec3, exp, texture, smoothstep, mix, max, sqrt, normalize, positionWorld, select } from 'three/tsl';
import { env } from '../env.js';

export function approxWaterHeight(ocean, xz) {
  // two largest cascades are enough to follow the swell over a point
  const L0 = ocean.lengthScales[0], L1 = ocean.lengthScales[1];
  const h0 = texture(ocean.fft.displacement[0], xz.div(L0)).level(0).y.mul(ocean.cascadeWeights[0]);
  const h1 = texture(ocean.fft.displacement[1], xz.div(L1)).level(1).y.mul(ocean.cascadeWeights[1]);
  return h0.add(h1).mul(0.85);
}

export function underwaterSun(ocean, caustics, p = positionWorld) {
  const depth = approxWaterHeight(ocean, p.xz).sub(p.y);
  const wet = smoothstep(-0.05, 0.1, depth);
  const d = max(depth, 0);
  const sunW = env.sunDir;
  const cosT = sqrt(float(1).sub(float(1).sub(sunW.y.mul(sunW.y)).div(1.777)).max(0.05));
  const K = env.waterAbsorption.add(env.waterScattering.mul(0.3));
  const trans = exp(K.negate().mul(d).div(cosT));
  const c = caustics ? caustics.sample(p, d) : float(1);
  return mix(vec3(1), trans.mul(c), wet);
}

export function underwaterAmbient(ocean, p = positionWorld) {
  const depth = approxWaterHeight(ocean, p.xz).sub(p.y);
  const d = max(depth, 0);
  return exp(d.mul(-0.11)).mul(0.9).add(0.1).mul(smoothstep(-0.05, 0.1, depth)).add(smoothstep(0.1, -0.05, depth));
}
