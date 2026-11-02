#!/usr/bin/env node
/*
  Render the trailer to video, or grab stills.

    node tools/render.cjs video [out.mp4] [--fps 30]
    node tools/render.cjs stills <dir> 0.5 3.2 7.8 ...

  Serves unknown-general/ on a local port, opens index.html?render in headless
  Chromium, draws each frame with TRAILER.frame(t), renders the score with an
  OfflineAudioContext, and muxes both with ffmpeg (H.264 + AAC, 1920x1080).
*/
const http = require('http');
const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');
const { chromium } = require('playwright');

const ROOT = path.resolve(__dirname, '..');
const TYPES = { '.html': 'text/html', '.png': 'image/png', '.jpg': 'image/jpeg', '.js': 'text/javascript' };

function serve() {
  return new Promise(res => {
    const srv = http.createServer((req, rsp) => {
      const p = path.join(ROOT, decodeURIComponent(req.url.split('?')[0]));
      if (!p.startsWith(ROOT) || !fs.existsSync(p) || fs.statSync(p).isDirectory()) { rsp.writeHead(404); rsp.end(); return; }
      rsp.writeHead(200, { 'Content-Type': TYPES[path.extname(p)] || 'application/octet-stream' });
      fs.createReadStream(p).pipe(rsp);
    }).listen(0, '127.0.0.1', () => res(srv));
  });
}

async function open() {
  const srv = await serve();
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
  page.on('pageerror', e => console.error('page error:', e.message));
  page.on('console', m => { if (m.type() === 'error') console.error('console:', m.text()); });
  await page.goto(`http://127.0.0.1:${srv.address().port}/index.html?render`);
  await page.waitForFunction(() => window.TRAILER);
  await page.evaluate(() => window.TRAILER.ready);
  return { srv, browser, page };
}

const b64 = s => Buffer.from(s.slice(s.indexOf(',') + 1), 'base64');

async function stills(dir, times) {
  fs.mkdirSync(dir, { recursive: true });
  const { srv, browser, page } = await open();
  for (const t of times) {
    const url = await page.evaluate(t => window.TRAILER.frame(t, .9), t);
    const f = path.join(dir, `t${t.toFixed(2).padStart(5, '0')}.jpg`);
    fs.writeFileSync(f, b64(url));
    console.log(f);
  }
  await browser.close(); srv.close();
}

async function video(out, fps) {
  const { srv, browser, page } = await open();
  const dur = await page.evaluate(() => window.TRAILER.DUR);
  const tmp = fs.mkdtempSync(path.join(require('os').tmpdir(), 'ug-'));
  const wav = path.join(tmp, 'score.wav');
  console.log('rendering score…');
  fs.writeFileSync(wav, Buffer.from(await page.evaluate(() => window.TRAILER.audio(48000)), 'base64'));
  const n = Math.round(dur * fps);
  const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-vcodec', 'mjpeg', '-framerate', String(fps), '-i', '-',
    '-i', wav, '-c:v', 'libx264', '-preset', 'slow', '-crf', '17', '-pix_fmt', 'yuv420p', '-profile:v', 'high',
    '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', '-shortest', out], { stdio: ['pipe', 'inherit', 'inherit'] });
  const t0 = Date.now();
  for (let i = 0; i < n; i++) {
    const url = await page.evaluate(t => window.TRAILER.frame(t, .95), i / fps);
    if (!ff.stdin.write(b64(url))) await new Promise(r => ff.stdin.once('drain', r));
    if (i % 30 === 0) console.log(`frame ${i}/${n}  ${((Date.now() - t0) / 1000).toFixed(0)}s`);
  }
  ff.stdin.end();
  await new Promise((res, rej) => ff.on('close', c => c ? rej(new Error('ffmpeg exited ' + c)) : res()));
  await browser.close(); srv.close();
  fs.rmSync(tmp, { recursive: true, force: true });
  console.log('wrote', out);
}

// sprites for the Blender version (tools/blender/build.py reads them from <dir>)
async function sprites(dir) {
  fs.mkdirSync(dir, { recursive: true });
  const { srv, browser, page } = await open();
  const meta = { figures: {}, rider: {}, front: {}, banners: {} };
  const save = (name, r) => { fs.writeFileSync(path.join(dir, name), b64(r.url)); delete r.url; return r; };
  for (const n of ['fish', 'bear', 'bucket', 'pixel']) for (const v of ['warm', 'green', 'sil']) for (const part of (v === 'sil' ? ['back'] : ['back', 'front'])) {
    const r = await page.evaluate(([n, v, p]) => window.TRAILER.sprite.figure(n, v, p), [n, v, part]);
    meta.figures[`${n}-${v}-${part}`] = save(`fig-${n}-${v}-${part}.png`, r);
  }
  fs.mkdirSync(path.join(dir, 'rider'), { recursive: true }); fs.mkdirSync(path.join(dir, 'front'), { recursive: true });
  for (let f = 240; f <= 340; f++) {                       // profile, 8.0 s – 11.33 s
    const t = f / 30, toss = .12 * Math.max(0, Math.sin(Math.PI * (t - 10.85) / .4)) * (t > 10.85 && t < 11.25);
    const r = await page.evaluate(([t, toss]) => window.TRAILER.sprite.rider(t, { toss, rim: '#ffb070' }), [t, toss]);
    meta.rider = save(`rider/${String(f).padStart(4, '0')}.png`, r);
  }
  for (let f = 200; f <= 250; f++) {                       // head-on, out of the gate
    const t = f / 30, e = Math.min(1, Math.max(0, (t - 7.0) / .6));
    meta.front = save(`front/${String(f).padStart(4, '0')}.png`, await page.evaluate(([t, e]) => window.TRAILER.sprite.riderFront(t, e), [t, e]));
  }
  for (const [k, c] of [['crimson', '#8e1b24'], ['dark', '#5e1018'], ['black', '#18100f']])
    meta.banners[k] = save(`banner-${k}.png`, await page.evaluate(([c, p]) => window.TRAILER.sprite.banner(c, p), [c, k === 'black']));
  fs.writeFileSync(path.join(dir, 'meta.json'), JSON.stringify(meta, null, 1));
  fs.writeFileSync(path.join(dir, 'score.wav'), Buffer.from(await page.evaluate(() => window.TRAILER.audio(48000)), 'base64'));
  await browser.close(); srv.close();
  console.log('sprites in', dir);
}

// composite rendered Blender shots (crossfades + shared overlay) and mux with the score
async function compose(shotsDir, out, fps) {
  const shots = JSON.parse(fs.readFileSync(path.join(shotsDir, 'shots.json')));
  const { srv, browser, page } = await open();
  const port = srv.address().port;
  // serve the shots folder too
  srv.removeAllListeners('request');
  srv.on('request', (req, rsp) => {
    const u = decodeURIComponent(req.url.split('?')[0]);
    const base = u.startsWith('/__shots/') ? shotsDir : ROOT, p = path.join(base, u.replace(/^\/__shots\//, '/'));
    if (!fs.existsSync(p) || fs.statSync(p).isDirectory()) { rsp.writeHead(404); rsp.end(); return; }
    rsp.writeHead(200, { 'Content-Type': TYPES[path.extname(p)] || 'application/octet-stream' }); fs.createReadStream(p).pipe(rsp);
  });
  const dur = await page.evaluate(() => window.TRAILER.DUR);
  const wav = path.join(shotsDir, 'score.wav');
  fs.writeFileSync(wav, Buffer.from(await page.evaluate(() => window.TRAILER.audio(48000)), 'base64'));
  const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-vcodec', 'mjpeg', '-framerate', String(fps), '-i', '-',
    '-i', wav, '-c:v', 'libx264', '-preset', 'slow', '-crf', '16', '-pix_fmt', 'yuv420p', '-profile:v', 'high',
    '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', '-shortest', out], { stdio: ['pipe', 'inherit', 'inherit'] });
  const n = Math.round(dur * fps), from = +(process.env.FROM || 0), to = Math.min(n, +(process.env.TO || n));
  for (let i = from; i < to; i++) {
    const t = i / fps, live = shots.filter(s => i >= s.f0 && i <= s.f1);
    const layers = live.map((s, k) => ({ url: `http://127.0.0.1:${port}/__shots/${s.name}/${String(i).padStart(4, '0')}.png`,
      alpha: k === 0 ? 1 : (() => { const a = Math.min(1, Math.max(0, (i - s.f0) / Math.max(1, live[k - 1].f1 - s.f0))); return a < .5 ? 4 * a * a * a : 1 - Math.pow(-2 * a + 2, 3) / 2; })() }));
    const url = await page.evaluate(([t, l]) => window.TRAILER.compose(t, l), [t, layers]);
    if (!ff.stdin.write(b64(url))) await new Promise(r => ff.stdin.once('drain', r));
    if (i % 60 === 0) console.log(`frame ${i}/${n}`);
  }
  ff.stdin.end();
  await new Promise((res, rej) => ff.on('close', c => c ? rej(new Error('ffmpeg exited ' + c)) : res()));
  await browser.close(); srv.close(); console.log('wrote', out);
}

const [mode, ...rest] = process.argv.slice(2);
const fpsArg = rest.indexOf('--fps');
const fps = fpsArg >= 0 ? parseFloat(rest.splice(fpsArg, 2)[1]) : 30;
(mode === 'stills' ? stills(rest[0], rest.slice(1).map(Number))
  : mode === 'audio' ? (async () => { const { srv, browser, page } = await open();
      fs.writeFileSync(path.resolve(rest[0]), Buffer.from(await page.evaluate(() => window.TRAILER.audio(48000)), 'base64')); await browser.close(); srv.close(); console.log('wrote', rest[0]); })()
  : mode === 'sprites' ? sprites(path.resolve(rest[0]))
  : mode === 'compose' ? compose(path.resolve(rest[0]), path.resolve(rest[1]), fps)
  : mode === 'video' ? video(path.resolve(rest[0] || path.join(ROOT, 'the-unknown-general.mp4')), fps)
  : Promise.reject(new Error('usage: render.cjs video [out.mp4] | stills <dir> <t...>')))
  .catch(e => { console.error(e); process.exit(1); });
