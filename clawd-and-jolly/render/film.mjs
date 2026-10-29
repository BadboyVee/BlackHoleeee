// Renders the whole edit with N parallel workers.
// usage: node render/film.mjs --tag NAME [--w 1920 --h 1080 --spp 16 --every 1 --jobs 2 --shots s01,s04]
import { spawn } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const args = Object.fromEntries(process.argv.slice(2).reduce((a, v, i, arr) => (v.startsWith('--') ? [...a, [v.slice(2), arr[i + 1]]] : a), []));
const edit = JSON.parse(fs.readFileSync(path.join(ROOT, 'edit.json'), 'utf8'));
const tag = args.tag || 'film', W = args.w || 1920, H = args.h || 1080, every = +(args.every || 1), jobs = +(args.jobs || 2);
const only = args.shots ? args.shots.split(',') : null;
// split every shot into chunks so workers stay busy
const tasks = [];
for (const e of edit) {
  if (only && !only.includes(e.shot)) continue;
  const n = Math.round((e.t1 - e.t0) * 24);
  const chunk = +(args.chunk || 48);
  for (let a = 0; a < n; a += chunk) tasks.push({ shot: e.shot, from: a, to: Math.min(n - 1, a + chunk - 1), spp: args.spp || e.spp });
}
let next = 0, running = 0;
const t0 = Date.now();
function done() { if (next >= tasks.length && running === 0) { console.log(`all done in ${((Date.now() - t0) / 60000).toFixed(1)} min`); } }
function launch() {
  while (running < jobs && next < tasks.length) {
    const tk = tasks[next++];
    const out = path.join('out', tag, tk.shot);
    // skip chunks whose frames already exist (resume)
    let missing = false;
    for (let f = tk.from; f <= tk.to; f += every) if (!fs.existsSync(path.join(ROOT, out, `${String(f).padStart(5, '0')}.png`))) { missing = true; break; }
    if (!missing) continue;
    running++;
    const p = spawn('node', ['render/render.mjs', '--shot', tk.shot, '--w', W, '--h', H, '--from', tk.from, '--to', tk.to, '--every', every, '--out', out, '--msaa', '0', ...(tk.spp ? ['--spp', tk.spp] : []), '--skip-existing', '1'], { cwd: ROOT });
    let buf = '';
    p.stdout.on('data', (d) => { buf += d; const lines = buf.split('\n'); buf = lines.pop(); for (const l of lines) if (/^frame|rror/.test(l)) console.log(`${tk.shot} ${l}`); });
    p.stderr.on('data', (d) => process.stdout.write(`${tk.shot} ERR ${d}`));
    p.on('close', (c) => { running--; console.log(`chunk ${tk.shot} ${tk.from}-${tk.to} exit ${c}`); launch(); done(); });
  }
  done();
}
launch();
