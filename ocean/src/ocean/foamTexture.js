// Tileable foam texture, baked once.
//   r  fill order: as foam decays, it retreats from low values first, so dense
//      foam thins into lace, then filaments, then scattered bubbles
//   g  fine bubble structure (albedo / sparkle variation)
//   b  height (bubbly relief for shading)
//   a  macro variation

import { vec2, vec4, float, smoothstep, clamp, mix, pow } from 'three/tsl';
import { bake } from '../render/bake.js';
import { voronoiP, fbmP, gnoiseP } from '../render/tslnoise.js';

export function bakeFoamTexture(renderer, size = 1024) {
  return bake(renderer, size, (uv) => {
    // gently warp so the cell lattice never reads as a grid
    const w = vec2(fbmP(uv, [3, 3], 3), fbmP(uv.add(0.37), [3, 3], 3)).mul(0.035);
    const p = uv.add(w);
    const v1 = voronoiP(p.mul(6), vec2(6, 6));
    const v2 = voronoiP(p.mul(13), vec2(13, 13));
    const v3 = voronoiP(p.mul(34), vec2(34, 34));
    const v4 = voronoiP(p.mul(71), vec2(71, 71));
    const web1 = float(1).sub(smoothstep(0.0, 0.16, v1.y.sub(v1.x)));
    const web2 = float(1).sub(smoothstep(0.0, 0.12, v2.y.sub(v2.x)));
    const cells3 = smoothstep(0.55, 0.15, v3.x);                 // round bubbles
    const rims4 = smoothstep(0.08, 0.0, v4.y.sub(v4.x)).mul(0.6).add(smoothstep(0.45, 0.1, v4.x).mul(0.4));
    const patch = fbmP(uv, [2, 2], 4).mul(0.5).add(0.5);
    const holes = smoothstep(0.3, 0.7, fbmP(uv.add(0.5), [5, 5], 3).mul(0.5).add(0.5));
    const order = clamp(
      web1.mul(0.42).add(web2.mul(0.24)).add(cells3.mul(0.14)).add(patch.mul(0.34)).sub(holes.mul(0.18)).add(v1.z.mul(0.08)),
      0, 1);
    const fine = rims4.mul(0.7).add(cells3.mul(0.3));
    const height = web1.mul(0.5).add(web2.mul(0.25)).add(cells3.mul(0.35)).add(rims4.mul(0.15));
    return vec4(order, fine, clamp(height.mul(0.8), 0, 1), patch);
  }, { name: 'foam' });
}
