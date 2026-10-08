// Tileable foam texture, baked once.
//   r  fill order: as foam decays, it retreats from low values first, so a
//      dense sheet opens round holes, then thins into lace, then filaments
//   g  fine bubble structure (albedo / sparkle variation)
//   b  height (bubbly relief for shading)
//   a  macro variation

import { vec2, vec4, float, smoothstep, clamp } from 'three/tsl';
import { bake } from '../render/bake.js';
import { voronoiP, fbmP } from '../render/tslnoise.js';

export function bakeFoamTexture(renderer, size = 1024) {
  return bake(renderer, size, (uv) => {
    // warp so holes and knots are irregular, never a lattice
    const w = vec2(fbmP(uv, [4, 4], 3), fbmP(uv.add(0.37), [4, 4], 3)).mul(0.05);
    const p = uv.add(w);
    const v1 = voronoiP(p.mul(7), vec2(7, 7));
    const v2 = voronoiP(p.mul(15), vec2(15, 15));
    const v3 = voronoiP(p.mul(34), vec2(34, 34));
    const v4 = voronoiP(p.mul(71), vec2(71, 71));
    // Foam drains away from bubble-free cores: the fill order is the distance
    // to the nearest core. Thin foam keeps only filaments and the knots where
    // cells meet; thicker foam is a sheet with round holes that close up.
    const hole1 = smoothstep(0.08, 0.62, v1.x.mul(v1.z.mul(0.4).add(0.8)));
    const hole2 = smoothstep(0.05, 0.55, v2.x);
    const web1 = float(1).sub(smoothstep(0.0, 0.1, v1.y.sub(v1.x)));
    const cells3 = smoothstep(0.55, 0.15, v3.x);                 // round bubbles
    const rims4 = smoothstep(0.08, 0.0, v4.y.sub(v4.x)).mul(0.6).add(smoothstep(0.45, 0.1, v4.x).mul(0.4));
    const patch = fbmP(uv, [2, 2], 4).mul(0.5).add(0.5);
    const holes = smoothstep(0.3, 0.7, fbmP(uv.add(0.5), [5, 5], 3).mul(0.5).add(0.5));
    const order = clamp(
      hole1.mul(0.42).add(hole2.mul(0.2)).add(web1.mul(0.1)).add(cells3.mul(0.08)).add(patch.mul(0.3)).sub(holes.mul(0.16)).add(v1.w.mul(0.06)),
      0, 1);
    const fine = rims4.mul(0.7).add(cells3.mul(0.3));
    // relief: thick knots and hole rims stand up, bubbles bulge
    const height = hole1.mul(0.45).add(hole2.mul(0.2)).add(cells3.mul(0.25)).add(rims4.mul(0.1));
    return vec4(order, fine, clamp(height, 0, 1), patch);
  }, { name: 'foam' });
}
