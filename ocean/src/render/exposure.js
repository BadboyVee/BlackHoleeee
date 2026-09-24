// Eye adaptation.
//
// A one-thread compute pass averages the log luminance of the anti-aliased
// HDR frame over a centre-weighted 16 x 16 grid; the value comes back to the
// CPU a frame or two later (async readback, no stall). Exposure adapts
// toward it relative to what an open, sunlit (or moonlit) scene would read
// at this time of day - so walking into the forest opens the eyes up, while
// the day/night exposure curve in main.js keeps doing the big changes.
// Adaptation is partial (dark places stay darker) and takes about a second,
// faster toward the light than toward the dark, like eyes.

import * as THREE from 'three/webgpu';
import { Fn, float, vec2, vec3, dot, log, exp, max, texture, instancedArray, Loop } from 'three/tsl';

const GRID = 16;

export class AutoExposure {
  constructor(renderer, sourceTexture) {
    this.renderer = renderer;
    this.buffer = instancedArray(1, 'float');
    this.kernel = Fn(() => {
      const acc = float(0).toVar(), wsum = float(0).toVar();
      // (one flat loop: nested TSL loops would share the index name)
      Loop(GRID * GRID, ({ i }) => {
        const uv = vec2(float(i.mod(GRID)).add(0.5), float(i.div(GRID)).add(0.5)).div(GRID);
        const c = texture(sourceTexture, uv).level(0).rgb;
        const lum = dot(c, vec3(0.2126, 0.7152, 0.0722));
        // centre-weighted: what you look at matters most
        const d = uv.sub(0.5).mul(2);
        const w = max(float(1).sub(dot(d, d).mul(0.6)), 0.15);
        acc.addAssign(log(max(lum, 1e-5)).mul(w));
        wsum.addAssign(w);
      });
      this.buffer.element(0).assign(exp(acc.div(wsum)));
    })().compute(1);
    this.lum = null;
    this.factor = 1;
    this.pending = false;
    this.frame = 0;
    this.enabled = true;
  }

  /** reference: the log-average an open scene reads under this sky */
  update(dt, refLuminance) {
    if (!this.enabled) { this.factor = 1; return 1; }
    if ((this.frame++ & 3) === 0 && !this.pending) {
      this.renderer.compute(this.kernel);
      this.pending = true;
      this.renderer.getArrayBufferAsync(this.buffer.value).then((ab) => {
        const v = new Float32Array(ab)[0];
        if (Number.isFinite(v) && v > 0) this.lum = v;
        this.pending = false;
      }).catch(() => { this.pending = false; });
    }
    if (this.lum !== null && refLuminance > 0) {
      // partial adaptation: dark places are opened up, but still read darker
      const target = THREE.MathUtils.clamp(Math.pow(refLuminance / this.lum, 0.55), 0.75, 2.4);
      const tau = target > this.factor ? 1.4 : 0.6;     // (seconds) slower opening, faster closing
      this.factor += (target - this.factor) * (1 - Math.exp(-dt / tau));
    }
    return this.factor;
  }
}
