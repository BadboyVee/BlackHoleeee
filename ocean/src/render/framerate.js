// Frame rate: a cap, and a governor that holds it.
//
// FramePacer caps the frame rate by skipping display refreshes. It keeps a
// running schedule rather than waiting a full interval after each frame, so on
// a 60 Hz screen a 50 fps cap draws five refreshes out of six (waiting 20 ms
// after each frame would land every other refresh: 30 fps).
//
// Governor holds the chosen rate. It measures what each frame really costs:
// from the start of the frame until the GPU has finished its work. With the
// cap in place the GPU is idle between frames, so that is the frame's own
// cost, not the cap's waiting. It walks a ladder of settings (render
// resolution, then a quality tier) down when frames run over budget and back
// up when there is room to spare, with hysteresis so it never flip-flops.

const SLACK = 7;   // ms: a refresh may be drawn this early (under half a 60 Hz refresh)

export class FramePacer {
  constructor() {
    this.fps = 0;          // 0: no cap
    this.next = 0;
  }

  /** true when the frame for this display refresh should be drawn */
  ready(now) {
    if (!this.fps) return true;
    if (now < this.next - SLACK) return false;
    this.next = Math.max(this.next + 1000 / this.fps, now - SLACK);
    return true;
  }
}

// rungs, best first: quality tier and render resolution (a fraction of the
// Resolution setting). Resolution goes first: it costs the least to look at.
const AUTO = [
  ['high', 1], ['high', 0.85], ['medium', 0.85], ['medium', 0.72], ['low', 0.72],
  ['low', 0.6], ['low', 0.5], ['low', 0.4],
];
const FIXED = [1, 0.85, 0.72, 0.6, 0.5, 0.4];

export class Governor {
  /**
   * @param {GPUDevice} device
   * @param {(tier: string, scale: number) => void} apply
   */
  constructor(device, apply) {
    this.device = device;
    this.apply = apply;
    this.target = 60;          // frames per second to hold
    this.mode = 'auto';        // 'auto' or a fixed tier: 'low' | 'medium' | 'high'
    this.rung = 0;
    this.samples = [];
    this.wait = 3000;          // ms before the next decision (first: let shaders settle)
    this.lastStep = 0;
    this.downAt = -1e9;        // when the last step down happened
    this.roomy = 0;            // consecutive windows with room to spare
    this.work = 0;             // ms, the last window's typical frame cost
  }

  get ladder() { return this.mode === 'auto' ? AUTO : FIXED.map((s) => [this.mode, s]); }
  get tier() { return this.ladder[this.rung][0]; }
  get scale() { return this.ladder[this.rung][1]; }

  /** the ladder rung to start from (0 = best) */
  start(rung = 0) {
    this.rung = Math.min(rung, this.ladder.length - 1);
    this.samples.length = 0;
    this.lastStep = performance.now();
    this.wait = 3000;
    this.apply(this.tier, this.scale);
  }

  setMode(mode) {
    // keep roughly the same resolution when switching between ladders
    const scale = this.scale;
    this.mode = mode;
    const l = this.ladder;
    let best = 0;
    for (let i = 0; i < l.length; i++) if (Math.abs(l[i][1] - scale) < Math.abs(l[best][1] - scale)) best = i;
    if (mode === 'auto') best = l.findIndex(([, s]) => s <= scale + 1e-3);
    this.start(Math.max(best, 0));
  }

  setTarget(fps) {
    this.target = fps;
    this.samples.length = 0;
    this.roomy = 0;
    this.downAt = -1e9;
    this.lastStep = performance.now();
    this.wait = 1500;
  }

  /** call at the start of a drawn frame, and done() after its GPU work is submitted */
  begin() { this.t0 = performance.now(); }

  done() {
    const t0 = this.t0;
    this.device.queue.onSubmittedWorkDone().then(() => this._sample(performance.now() - t0));
  }

  _sample(ms) {
    const now = performance.now();
    this.samples.push(ms);
    if (now - this.lastStep < this.wait || this.samples.length < 12) return;
    // a typical frame of the window: the median ignores one-off hitches
    const s = this.samples.slice().sort((a, b) => a - b);
    const work = this.work = s[s.length >> 1];
    this.samples.length = 0;
    this.lastStep = now;
    this.wait = 1500;
    const budget = 1000 / this.target;
    const last = this.ladder.length - 1;
    if (work > budget * 0.92 && this.rung < last) {
      this.rung++;
      this.downAt = now;
      this.roomy = 0;
      this.wait = 2000;
      this.apply(this.tier, this.scale);
    } else if (this.rung > 0) {
      // step back up only with clear room, and more cautiously soon after a step down
      const room = now - this.downAt < 20000 ? 0.5 : 0.62;
      this.roomy = work < budget * room ? this.roomy + 1 : 0;
      if (this.roomy >= 2) {
        this.rung--;
        this.roomy = 0;
        this.wait = 2500;
        this.apply(this.tier, this.scale);
      }
    }
  }
}
