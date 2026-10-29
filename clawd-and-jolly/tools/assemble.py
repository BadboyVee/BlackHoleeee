# Concatenate rendered shots (per edit.json) into one video, optionally with audio.
# usage: python tools/assemble.py TAG out.mp4 [--every N] [--audio file] [--crf 16] [--fps 24]
import json, os, sys, subprocess, argparse, tempfile
ap = argparse.ArgumentParser(); ap.add_argument('tag'); ap.add_argument('out'); ap.add_argument('--every', type=int, default=1)
ap.add_argument('--audio'); ap.add_argument('--crf', type=int, default=16); ap.add_argument('--preset', default='slow')
ap.add_argument('--bitrate', help='two-pass target video bitrate, e.g. 11M (overrides --crf)')
a = ap.parse_args()
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
edit = json.load(open(os.path.join(root, 'edit.json')))
tmp = tempfile.mkdtemp(prefix='asm_', dir=os.path.join(root, 'out'))
k = 0; last = None
for e in edit:
    n = round((e['t1'] - e['t0']) * 24)
    for f in range(0, n, a.every):
        src = os.path.join(root, 'out', a.tag, e['shot'], f'{f:05d}.png')
        if os.path.exists(src): last = src
        if last is None: continue
        os.symlink(last, os.path.join(tmp, f'{k:05d}.png')); k += 1
fps = 24 / a.every
src = ['ffmpeg', '-y', '-v', 'error', '-framerate', str(fps), '-i', os.path.join(tmp, '%05d.png')]
vopts = ['-c:v', 'libx264', '-preset', a.preset, '-pix_fmt', 'yuv420p', '-tune', 'film']
if a.bitrate:
    log = os.path.join(tmp, 'pass')
    subprocess.run(src + vopts + ['-b:v', a.bitrate, '-pass', '1', '-passlogfile', log, '-an', '-f', 'mp4', os.devnull], check=True)
    vopts += ['-b:v', a.bitrate, '-maxrate', a.bitrate, '-bufsize', '20M', '-pass', '2', '-passlogfile', log]
else:
    vopts += ['-crf', str(a.crf)]
cmd = src + (['-i', a.audio, '-c:a', 'aac', '-b:a', '320k', '-shortest'] if a.audio else []) + vopts + ['-movflags', '+faststart', a.out]
subprocess.run(cmd, check=True)
print(a.out, k, 'frames')
