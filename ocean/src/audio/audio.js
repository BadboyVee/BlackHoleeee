// Soundscape from real recordings (see assets/audio/CREDITS.md).
//
//  beds       surf (by distance to the shoreline), wind (height, boat speed),
//             wind in the trees, songbirds by day, crickets at night
//  3D         gulls around the village and pier, the whale's song (loud under
//             water, faint above), water lapping at the boat's hull
//  events     footsteps cut from walking recordings by onset detection and
//             filtered per surface (sand, pier planks, grass, shallow water);
//             splashes cut from the oar strokes of the rowing recording
// Under water every above-water sound goes through a steep low-pass.

import { assetURL } from '../core/assets.js';

const FILES = ['waves', 'wind', 'wind-in-trees', 'seagulls', 'birds', 'crickets', 'whale', 'walk-on-gravel', 'walk-on-leaves', 'rowing-boat'];

export class Audio {
  constructor({ base = 'assets/audio/' } = {}) {   // (under ocean/, see core/assets.js)
    this.base = base;
    this.ctx = null;
    this.buffers = {};
    this.volume = 0.8;
    this.started = false;
    this.ready = false;
    const kick = () => { this.start(); };
    addEventListener('pointerdown', kick, { once: false });
    addEventListener('keydown', kick, { once: false });
  }

  async start() {
    if (this.started) { if (this.ctx.state !== 'running') this.ctx.resume(); return; }
    this.started = true;
    const ctx = this.ctx = new AudioContext();
    this.master = ctx.createGain();
    this.master.gain.value = this.volume;
    const comp = ctx.createDynamicsCompressor();
    comp.threshold.value = -14; comp.ratio.value = 3;
    this.master.connect(comp).connect(ctx.destination);
    // the "above water" bus is low-passed when the head goes under
    this.air = ctx.createBiquadFilter();
    this.air.type = 'lowpass';
    this.air.frequency.value = 20000;
    this.air.Q.value = 0.5;
    this.air.connect(this.master);
    this.water = ctx.createGain();      // sounds that live under water (whale)
    this.water.connect(this.master);
    await Promise.all(FILES.map(async (f) => {
      try {
        const res = await fetch(assetURL(this.base + f + '.mp3'));
        this.buffers[f] = await ctx.decodeAudioData(await res.arrayBuffer());
      } catch (e) { console.warn('audio', f, e); }
    }));
    this._setup();
    this.ready = true;
  }

  setVolume(v) { this.volume = v; if (this.master) this.master.gain.setTargetAtTime(v, this.ctx.currentTime, 0.05); }

  _loop(name, dest, gain = 0) {
    const b = this.buffers[name];
    if (!b) return null;
    const src = this.ctx.createBufferSource();
    src.buffer = b; src.loop = true;
    const g = this.ctx.createGain();
    g.gain.value = gain;
    src.connect(g).connect(dest);
    src.start(0, Math.random() * b.duration);
    return { src, g };
  }

  _panner(dest, ref = 10, rolloff = 1.2, max = 800) {
    const p = this.ctx.createPanner();
    p.panningModel = 'HRTF';
    p.distanceModel = 'inverse';
    p.refDistance = ref; p.rolloffFactor = rolloff; p.maxDistance = max;
    p.connect(dest);
    return p;
  }

  _setup() {
    const ctx = this.ctx;
    this.beds = {
      surf: this._loop('waves', this.air),
      wind: this._loop('wind', this.air),
      trees: this._loop('wind-in-trees', this.air),
      birds: this._loop('birds', this.air),
      crickets: this._loop('crickets', this.air),
    };
    // gulls: a few wandering 3D emitters over the village, pier and beach
    this.gulls = [];
    for (let k = 0; k < 3; k++) {
      const pan = this._panner(this.air, 18, 1.3);
      const l = this._loop('seagulls', pan, 0.5);
      if (l) this.gulls.push({ pan, l, phase: k * 2.1 });
    }
    // whale: loud in the water, faint through the air
    this.whaleUnder = this._panner(this.water, 60, 0.8, 3000);
    this.whaleAir = this._panner(this.air, 25, 1.5, 1500);
    const w1 = this._loop('whale', this.whaleUnder, 0), w2 = this._loop('whale', this.whaleAir, 0);
    this.whaleLoops = [w1, w2];
    // boat: water lapping on the hull
    this.boatPan = this._panner(this.air, 4, 1.6, 200);
    this.boatLoop = this._loop('rowing-boat', this.boatPan, 0);
    // one-shot slices
    this.steps = { gravel: this._onsets(this.buffers['walk-on-gravel']), leaves: this._onsets(this.buffers['walk-on-leaves']) };
    this.splashes = this._onsets(this.buffers['rowing-boat'], 0.7);
  }

  // find sharp onsets (steps, oar strokes) in a recording
  _onsets(buf, len = 0.28) {
    if (!buf) return [];
    const d = buf.getChannelData(0), sr = buf.sampleRate;
    const hop = Math.floor(sr * 0.01);
    const env = [];
    for (let i = 0; i + hop < d.length; i += hop) {
      let e = 0;
      for (let k = 0; k < hop; k++) e += d[i + k] * d[i + k];
      env.push(Math.sqrt(e / hop));
    }
    const sorted = [...env].sort((a, b) => a - b);
    const med = sorted[Math.floor(sorted.length * 0.5)];
    const out = [];
    let last = -1e9;
    for (let i = 2; i < env.length - 2; i++) {
      const rise = env[i] - env[i - 2];
      if (env[i] > med * 3 && rise > med * 1.5 && env[i] >= env[i + 1] && i - last > 25) {
        out.push({ offset: Math.max(0, (i - 2) * hop / sr), dur: len });
        last = i;
      }
    }
    return out.slice(0, 80);
  }

  _slice(bufName, slices, { gain = 0.5, rate = 1, filter = null, pos = null }) {
    if (!this.ready || !slices.length) return;
    const ctx = this.ctx;
    const s = slices[Math.floor(Math.random() * slices.length)];
    const src = ctx.createBufferSource();
    src.buffer = this.buffers[bufName];
    src.playbackRate.value = rate * (0.92 + Math.random() * 0.16);
    const g = ctx.createGain();
    const t = ctx.currentTime;
    g.gain.setValueAtTime(0, t);
    g.gain.linearRampToValueAtTime(gain, t + 0.008);
    g.gain.setTargetAtTime(0, t + s.dur * 0.55, s.dur * 0.18);
    let node = src.connect(g);
    if (filter) { const f = ctx.createBiquadFilter(); Object.assign(f, {}); f.type = filter.type; f.frequency.value = filter.f; f.Q.value = filter.q || 0.7; if (filter.gain) f.gain.value = filter.gain; node = node.connect(f); }
    if (pos) { const p = this._panner(this.air, 6, 1.4, 300); p.positionX.value = pos.x; p.positionY.value = pos.y; p.positionZ.value = pos.z; node.connect(p); } else node.connect(this.air);
    src.start(t, s.offset, s.dur / src.playbackRate.value + 0.2);
  }

  /** player footstep: surface = 'sand' | 'wood' | 'grass' | 'water' */
  footstep(surface, speed = 1.5) {
    const k = Math.min(1, 0.55 + speed * 0.1);
    if (surface === 'wood') this._slice('walk-on-gravel', this.steps.gravel, { gain: 0.32 * k, rate: 0.72, filter: { type: 'peaking', f: 380, q: 1.2, gain: 9 } });
    else if (surface === 'grass') this._slice('walk-on-leaves', this.steps.leaves, { gain: 0.22 * k, rate: 1.0, filter: { type: 'lowpass', f: 2600 } });
    else if (surface === 'water') this._slice('rowing-boat', this.splashes, { gain: 0.35 * k, rate: 1.3, filter: { type: 'highpass', f: 400 } });
    else this._slice('walk-on-gravel', this.steps.gravel, { gain: 0.16 * k, rate: 0.85, filter: { type: 'lowpass', f: 900 } });
  }

  splash(pos, strength = 1) {
    this._slice('rowing-boat', this.splashes, { gain: Math.min(1, 0.4 * strength), rate: 1 / (0.7 + strength * 0.3), filter: { type: 'lowpass', f: 3000 }, pos });
  }

  /**
   * per frame: listener from the camera; bed levels from the surroundings
   * s = { camera, underwater, depth, shoreDist, heightAboveGround, wind, night, treeDensity, boat, boatSpeed, whale, dt }
   */
  update(s) {
    if (!this.ready) return;
    const ctx = this.ctx, t = ctx.currentTime;
    const L = ctx.listener, c = s.camera;
    const f = c.getWorldDirection(this._tmp || (this._tmp = c.position.clone()));
    const up = c.up;
    if (L.positionX) {
      L.positionX.setTargetAtTime(c.position.x, t, 0.02); L.positionY.setTargetAtTime(c.position.y, t, 0.02); L.positionZ.setTargetAtTime(c.position.z, t, 0.02);
      L.forwardX.setTargetAtTime(f.x, t, 0.02); L.forwardY.setTargetAtTime(f.y, t, 0.02); L.forwardZ.setTargetAtTime(f.z, t, 0.02);
      L.upX.value = up.x; L.upY.value = up.y; L.upZ.value = up.z;
    }
    const set = (node, v, tc = 0.4) => node && node.g.gain.setTargetAtTime(v, t, tc);
    const under = s.underwater;
    // under water: above-water world muffled to a rumble
    this.air.frequency.setTargetAtTime(under ? 320 : 20000, t, under ? 0.03 : 0.12);
    const shore = Math.exp(-Math.abs(s.shoreDist) / 70) * 0.85 + 0.12;
    set(this.beds.surf, (under ? 0.9 : shore) * (0.6 + 0.4 * Math.min(s.surf || 1, 1.5)));
    const windK = Math.min(1, 0.25 + s.wind / 14 + Math.max(s.heightAboveGround, 0) / 60 + s.boatSpeed / 12);
    set(this.beds.wind, under ? 0 : windK * 0.45);
    set(this.beds.trees, under ? 0 : Math.min(1, s.treeDensity) * 0.5 * (0.5 + s.wind / 14));
    const land = s.shoreDist < -20 ? 1 : 0.35;
    set(this.beds.birds, under ? 0 : (1 - s.night) * land * 0.35, 1.5);
    set(this.beds.crickets, under ? 0 : s.night * land * 0.3, 1.5);
    // gulls wheel around points above the village and pier
    const time = t;
    this.gulls.forEach((g, k) => {
      const cx = 110 + k * 25, cz = 10 + k * 20, r = 30 + k * 12;
      g.pan.positionX.value = cx + Math.cos(time * 0.13 + g.phase) * r;
      g.pan.positionY.value = 18 + 6 * Math.sin(time * 0.2 + k);
      g.pan.positionZ.value = cz + Math.sin(time * 0.11 + g.phase) * r;
      g.l.g.gain.setTargetAtTime((1 - s.night * 0.9) * 0.55, t, 1);
    });
    // whale song
    if (s.whale) {
      const w = s.whale;
      for (const p of [this.whaleUnder, this.whaleAir]) { p.positionX.value = w.x; p.positionY.value = w.y; p.positionZ.value = w.z; }
      set(this.whaleLoops[0], under ? 1.0 : 0, 0.2);
      set(this.whaleLoops[1], under ? 0 : 0.35, 0.2);
    }
    // hull lapping: strongest at rest
    if (s.boat) {
      this.boatPan.positionX.value = s.boat.x; this.boatPan.positionY.value = s.boat.y; this.boatPan.positionZ.value = s.boat.z;
      set(this.boatLoop, Math.max(0, 0.5 - s.boatSpeed * 0.05));
    }
  }
}
