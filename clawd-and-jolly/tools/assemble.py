# Concatenate rendered shots (per edit.json) into one video, optionally with audio.
# usage: python tools/assemble.py TAG out.mp4 [--every N] [--audio file] [--crf 16] [--fps 24]
import json, os, sys, subprocess, argparse, tempfile
ap = argparse.ArgumentParser(); ap.add_argument('tag'); ap.add_argument('out'); ap.add_argument('--every', type=int, default=1)
ap.add_argument('--audio'); ap.add_argument('--crf', type=int, default=16); ap.add_argument('--preset', default='slow')
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
cmd = ['ffmpeg', '-y', '-v', 'error', '-framerate', str(fps), '-i', os.path.join(tmp, '%05d.png')]
if a.audio: cmd += ['-i', a.audio, '-c:a', 'aac', '-b:a', '320k', '-shortest']
cmd += ['-c:v', 'libx264', '-preset', a.preset, '-crf', str(a.crf), '-pix_fmt', 'yuv420p', '-movflags', '+faststart', a.out]
subprocess.run(cmd, check=True)
print(a.out, k, 'frames')
