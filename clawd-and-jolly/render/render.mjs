// Drives headless Chromium (ANGLE on Mesa llvmpipe) frame by frame and writes PNGs.
// usage: node render/render.mjs --shot name [--w 1920 --h 1080 --spp 16 --from 0 --to N --fps 24 --out out/name --every 1]
import { chromium } from 'playwright-core';
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { spawn } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const args = Object.fromEntries(process.argv.slice(2).reduce((a, v, i, arr) => (v.startsWith('--') ? [...a, [v.slice(2), arr[i + 1]?.startsWith('--') || arr[i + 1] === undefined ? true : arr[i + 1]]] : a), []));
const W = +(args.w || 1920), H = +(args.h || 1080), FPS = +(args.fps || 24);
const shotName = args.shot;
const outDir = path.resolve(ROOT, args.out || `out/${shotName}`);
fs.mkdirSync(outDir, { recursive: true });

const MIME = { '.js': 'text/javascript', '.html': 'text/html', '.json': 'application/json', '.png': 'image/png', '.jpg': 'image/jpeg', '.hdr': 'application/octet-stream', '.bin': 'application/octet-stream', '.glb': 'model/gltf-binary' };
const server = http.createServer((req, res) => {
  const u = decodeURIComponent(req.url.split('?')[0]);
  const f = path.join(ROOT, u.startsWith('/node_modules') ? u : path.join('src', u));
  fs.readFile(f, (e, d) => {
    if (e) { res.writeHead(404); res.end(); return; }
    res.writeHead(200, { 'Content-Type': MIME[path.extname(f)] || 'application/octet-stream' });
    res.end(d);
  });
}).listen(0);
await new Promise((r) => server.on('listening', r));
const port = server.address().port;

const browser = await chromium.launch({
  executablePath: '/opt/pw-browsers/chromium-1243/chrome-linux64/chrome',
  args: ['--use-gl=angle', '--use-angle=gl-egl', '--ignore-gpu-blocklist', '--disable-gpu-watchdog', '--disable-renderer-backgrounding', '--js-flags=--max-old-space-size=8192'],
});
const page = await browser.newPage({ viewport: { width: Math.min(W, 1920), height: Math.min(H, 1080) } });
page.on('console', (m) => console.log('[page]', m.text()));
page.on('pageerror', (e) => console.log('[pageerror]', e.message));
page.setDefaultTimeout(0);
await page.goto(`http://localhost:${port}/film.html?w=${W}&h=${H}&msaa=${args.msaa ?? 4}&debug=${args.debug ? 1 : 0}&onlySub=${args.onlySub ?? -1}`);
await page.waitForFunction('window.engineReady === true');
const info = await page.evaluate(([n, o]) => window.setupShot(n, o), [shotName, JSON.parse(args.opts || '{}')]);
if (args.cues) {
  const cues = await page.evaluate(() => window.getCues());
  fs.writeFileSync(path.resolve(ROOT, args.cues), JSON.stringify(cues));
  console.log('cues', cues.length);
  await browser.close(); server.close(); process.exit(0);
}
const total = Math.round(info.duration * FPS);
const from = +(args.from ?? 0), to = Math.min(+(args.to ?? total - 1), total - 1), every = +(args.every || 1);
const spp = +(args.spp || info.samples);
console.log(`shot ${shotName}: ${info.duration}s = ${total} frames, rendering ${from}..${to} step ${every} at ${W}x${H} spp ${spp}`);

for (let f = from; f <= to; f += every) {
  const file0 = path.join(outDir, `${String(f).padStart(5, '0')}.png`);
  if (args['skip-existing'] && fs.existsSync(file0)) continue;
  const tw = Date.now();
  const ms = await page.evaluate(([f, fps, spp]) => window.renderShotFrame(f, fps, spp), [f, FPS, spp]);
  const b64 = await page.evaluate(() => window.grabPixels());
  const buf = Buffer.from(b64, 'base64');
  const file = path.join(outDir, `${String(f).padStart(5, '0')}.png`);
  await new Promise((resolve, reject) => {
    const ff = spawn('ffmpeg', ['-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgba', '-s', `${W}x${H}`, '-i', '-', '-vf', 'vflip', '-frames:v', '1', file]);
    ff.on('close', (c) => (c === 0 ? resolve() : reject(new Error('ffmpeg ' + c))));
    ff.stdin.end(buf);
  });
  console.log(`frame ${f} ${((Date.now() - tw) / 1000).toFixed(2)}s`);
}
await browser.close();
server.close();
