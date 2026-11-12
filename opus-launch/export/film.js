// Render the film to files with a headless Chromium (Playwright), for the video export.
//   node film.js frames <outdir> <first> <last>   film frame i (t = i / 25) to f####.png, 1920 x 1080
//   node film.js score <out.wav>                  one pass of the score, 48 kHz stereo
//   node film.js stills <outdir> <name>=<t> ...    frames without their titles, to <name>.png
//   node film.js card <out.png>                   the preview card (card/index.html)
// Set FONTS_DIR to a folder holding newsreader.css and its woff2 files to work offline.
const { chromium } = require('playwright');
const http = require('http'), fs = require('fs'), path = require('path');
const FILM = path.resolve(__dirname, '..');
const [mode, out, ...rest] = process.argv.slice(2);
const types = { '.html': 'text/html', '.js': 'text/javascript', '.png': 'image/png', '.jpg': 'image/jpeg' };

function serve(root) {
  return new Promise(res => {
    const server = http.createServer((req, rsp) => {
      const p = path.join(root, decodeURIComponent(req.url.split('?')[0]).replace(/\/$/, '/index.html'));
      fs.readFile(p, (err, data) => {
        if (err) { rsp.writeHead(404); rsp.end(); return; }
        rsp.writeHead(200, { 'Content-Type': types[path.extname(p)] || 'application/octet-stream' }); rsp.end(data);
      });
    }).listen(0, () => res(server));
  });
}

async function open(url) {
  const browser = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
  const pg = await (await browser.newContext({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1 })).newPage();
  const FD = process.env.FONTS_DIR;
  if (FD) {
    await pg.route('**/fonts.googleapis.com/**', r => r.fulfill({ status: 200, contentType: 'text/css', body: fs.readFileSync(path.join(FD, 'newsreader.css'), 'utf8') }));
    await pg.route('**/fonts.gstatic.com/**', r => r.fulfill({ status: 200, contentType: 'font/woff2', body: fs.readFileSync(path.join(FD, new URL(r.request().url()).pathname.slice(1).replace(/\//g, '_'))) }));
  }
  const errors = [];
  pg.on('pageerror', e => errors.push(e.message));
  await pg.goto(url);
  return { browser, pg, errors };
}

(async () => {
  if (mode === 'card') {
    const server = await serve(path.join(__dirname, 'card'));
    const { browser, pg } = await open(`http://127.0.0.1:${server.address().port}/`);
    await pg.waitForFunction(() => window.__done === true, null, { timeout: 60000 });
    await pg.screenshot({ path: out });
    await browser.close(); server.close();
    return console.log('card', out);
  }
  // the film, with the export switch: one shader program per shot, so software GL keeps up
  const server = await serve(FILM);
  const { browser, pg, errors } = await open(`http://127.0.0.1:${server.address().port}/index.html?t=0&export`);
  await pg.waitForFunction(() => window.__filmStarted === true && window.__film, null, { timeout: 300000 });
  await pg.evaluate(async () => { await document.fonts.ready; await document.fonts.load('600 60px "Newsreader"'); document.getElementById('ui').style.display = 'none'; });
  if (mode === 'score') {
    const b64 = await pg.evaluate(async () => {
      const [L, R] = await window.__film.score(48000);
      const n = L.length, buf = new DataView(new ArrayBuffer(44 + n * 4));
      const w = (o, s) => { for (let i = 0; i < s.length; i++) buf.setUint8(o + i, s.charCodeAt(i)); };
      w(0, 'RIFF'); buf.setUint32(4, 36 + n * 4, true); w(8, 'WAVEfmt '); buf.setUint32(16, 16, true);
      buf.setUint16(20, 1, true); buf.setUint16(22, 2, true); buf.setUint32(24, 48000, true); buf.setUint32(28, 48000 * 4, true);
      buf.setUint16(32, 4, true); buf.setUint16(34, 16, true); w(36, 'data'); buf.setUint32(40, n * 4, true);
      for (let i = 0; i < n; i++) {
        buf.setInt16(44 + i * 4, Math.max(-1, Math.min(1, L[i])) * 32767, true);
        buf.setInt16(46 + i * 4, Math.max(-1, Math.min(1, R[i])) * 32767, true);
      }
      let s = ''; const u8 = new Uint8Array(buf.buffer);
      for (let i = 0; i < u8.length; i += 0x8000) s += String.fromCharCode.apply(null, u8.subarray(i, i + 0x8000));
      return btoa(s);
    });
    fs.writeFileSync(out, Buffer.from(b64, 'base64'));
    console.log('score', out);
  } else if (mode === 'frames' || mode === 'stills') {
    fs.mkdirSync(out, { recursive: true });
    const jobs = mode === 'frames'
      ? Array.from({ length: +rest[1] - +rest[0] + 1 }, (_, k) => [`f${String(+rest[0] + k).padStart(4, '0')}`, (+rest[0] + k) / 25, true])
      : rest.map(s => s.split('=')).map(([name, t]) => [name, +t, false]);
    const t0 = Date.now();
    for (const [name, t, titles] of jobs) {
      const file = path.join(out, name + '.png');
      if (fs.existsSync(file)) continue;
      const msg = await pg.evaluate(([t, titles]) => { window.__film.frameAt(t, { titles }); const m = document.getElementById('msg'); return m.hidden ? '' : m.textContent; }, [t, titles]);
      if (msg || errors.length) { console.log(`stopping at ${name}: ${msg || errors.join(' | ')}`); process.exit(1); }
      await pg.screenshot({ path: file + '.tmp.png', timeout: 600000 });
      fs.renameSync(file + '.tmp.png', file);
      console.log(`${name} t=${t.toFixed(2)} ${((Date.now() - t0) / 1000).toFixed(0)}s`);
    }
  } else {
    console.log('usage: node film.js frames|score|stills|card ...'); process.exitCode = 2;
  }
  await browser.close(); server.close();
})();
