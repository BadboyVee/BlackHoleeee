// Saves the terminal UI canvas as a PNG for checking
import { chromium } from 'playwright-core';
import http from 'node:http'; import fs from 'node:fs'; import path from 'node:path';
const ROOT = path.resolve(path.dirname(new URL(import.meta.url).pathname), '..');
const srv = http.createServer((q, s) => { const u = decodeURIComponent(q.url.split('?')[0]); const f = path.join(ROOT, u.startsWith('/node_modules') ? u : path.join('src', u));
  fs.readFile(f, (e, d) => { if (e) { s.writeHead(404); s.end(); return; } s.writeHead(200, { 'Content-Type': f.endsWith('.js') ? 'text/javascript' : 'text/html' }); s.end(d); }); }).listen(8124);
const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium-1243/chrome-linux64/chrome' });
const p = await b.newPage();
p.on('pageerror', (e) => console.log(e.message));
await p.goto('http://localhost:8124/film.html?w=64&h=64');
const url = await p.evaluate(async () => {
  const m = await import('./screen-ui.js');
  const c = document.createElement('canvas'); c.width = m.UI_W; c.height = m.UI_H;
  m.drawTerminal(c.getContext('2d'), { cursor: 1, typed: 0, showJolly: 0 });
  return c.toDataURL('image/png');
});
fs.writeFileSync(process.argv[2] || 'out/ui.png', Buffer.from(url.split(',')[1], 'base64'));
await b.close(); srv.close();
