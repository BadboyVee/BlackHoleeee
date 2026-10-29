import { FilmRenderer } from './engine.js';
import { SHOTS } from './shots/index.js';

const qs = new URLSearchParams(location.search);
const W = +(qs.get('w') || 1920), H = +(qs.get('h') || 1080);
const canvas = document.createElement('canvas');
canvas.width = W; canvas.height = H;
document.body.appendChild(canvas);
const engine = new FilmRenderer({ width: W, height: H, canvas, msaa: +(qs.get('msaa') ?? 4) });
let shot = null;

window.setupShot = async (name, opts = {}) => {
  shot = await SHOTS[name](engine, opts);
  return { duration: shot.duration, samples: shot.samples || 16 };
};
window.renderShotFrame = (frame, fps, samples) => {
  const t = frame / fps;
  const t0 = performance.now();
  engine.renderFrame(shot, t, { samples: samples || shot.samples || 16, frameIndex: frame, shutter: (shot.shutter ?? 0.5) / fps, onlySub: +(qs.get('onlySub') ?? -1) });
  return performance.now() - t0;
};
window.grabPixels = () => {
  const px = engine.readPixels();
  let s = '';
  const CH = 0x8000;
  for (let i = 0; i < px.length; i += CH) s += String.fromCharCode.apply(null, px.subarray(i, i + CH));
  return btoa(s);
};
window.getCues = () => (typeof shot.cues === 'function' ? shot.cues() : shot.cues || []);
window.engineReady = true;
