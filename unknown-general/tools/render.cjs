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

const [mode, ...rest] = process.argv.slice(2);
const fpsArg = rest.indexOf('--fps');
const fps = fpsArg >= 0 ? parseFloat(rest.splice(fpsArg, 2)[1]) : 30;
(mode === 'stills' ? stills(rest[0], rest.slice(1).map(Number))
  : mode === 'video' ? video(path.resolve(rest[0] || path.join(ROOT, 'the-unknown-general.mp4')), fps)
  : Promise.reject(new Error('usage: render.cjs video [out.mp4] | stills <dir> <t...>')))
  .catch(e => { console.error(e); process.exit(1); });
