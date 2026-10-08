// Renders every frame of index.html to frames/frame_0000.png ... frame_0539.png.
//
//   npm install            (once; installs Playwright)
//   npx playwright install chromium
//   node capture.js        [--from N] [--to N] [--out frames]
//
// The page is served from a throwaway local HTTP server rather than file://,
// so the canvas can be read back pixel-exact with toDataURL.

const fs = require('fs');
const http = require('http');
const path = require('path');
const { chromium } = require('playwright');

const ROOT = __dirname;
const FPS = 30;
const TOTAL = 540; // 18 s at 30 fps

const args = process.argv.slice(2);
const arg = (name, fallback) => {
  const i = args.indexOf(`--${name}`);
  return i >= 0 && args[i + 1] !== undefined ? args[i + 1] : fallback;
};
const FROM = Number(arg('from', 0));
const TO = Number(arg('to', TOTAL - 1));
const OUT = path.resolve(ROOT, arg('out', 'frames'));

const TYPES = {
  '.html': 'text/html; charset=utf-8', '.js': 'text/javascript', '.css': 'text/css',
  '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png', '.webp': 'image/webp', '.svg': 'image/svg+xml',
};

function serve() {
  const server = http.createServer((req, res) => {
    const rel = decodeURIComponent(new URL(req.url, 'http://x').pathname);
    const file = path.join(ROOT, rel === '/' ? 'index.html' : rel);
    if (!file.startsWith(ROOT + path.sep) && file !== ROOT) { res.writeHead(403); return res.end(); }
    fs.readFile(file, (err, data) => {
      if (err) { res.writeHead(404); return res.end(); } // a missing asset falls back in the page
      res.writeHead(200, { 'Content-Type': TYPES[path.extname(file).toLowerCase()] || 'application/octet-stream' });
      res.end(data);
    });
  });
  return new Promise((resolve) => server.listen(0, '127.0.0.1', () => resolve(server)));
}

(async () => {
  const server = await serve();
  const { port } = server.address();
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1280, height: 720 }, deviceScaleFactor: 1 });
  page.on('pageerror', (e) => console.error('page error:', e.message));

  await page.goto(`http://127.0.0.1:${port}/index.html?capture=1`, { waitUntil: 'load' });
  const info = await page.evaluate(() => window.timelineReady);
  if (info.missing.length) console.log(`missing assets (drawn as fallbacks): ${info.missing.join(', ')}`);

  fs.mkdirSync(OUT, { recursive: true });
  const started = Date.now();
  for (let n = FROM; n <= TO; n++) {
    const dataUrl = await page.evaluate((t) => {
      window.renderAt(t);
      return document.getElementById('c').toDataURL('image/png');
    }, n / FPS);
    const name = `frame_${String(n).padStart(4, '0')}.png`;
    fs.writeFileSync(path.join(OUT, name), Buffer.from(dataUrl.split(',')[1], 'base64'));
    if (n % FPS === 0 || n === TO) {
      process.stdout.write(`\r${name}  ${(n / FPS).toFixed(2)} s  (${((Date.now() - started) / 1000).toFixed(0)} s elapsed)`);
    }
  }
  process.stdout.write('\n');
  console.log(`done: ${TO - FROM + 1} frames in ${path.relative(process.cwd(), OUT) || '.'}`);
  console.log('next: ffmpeg -framerate 30 -i frames/frame_%04d.png -i track.mp3 -c:v libx264 -pix_fmt yuv420p -shortest out.mp4');

  await browser.close();
  server.close();
})().catch((e) => {
  console.error(e);
  process.exit(1);
});
