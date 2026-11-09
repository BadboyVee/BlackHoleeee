#!/usr/bin/env python3
"""Render the orbit video: the camera swings around the pagoda and back again.

    python3 tools/flythrough.py ./pt scene.bin flythrough.mp4 [frames] [spp] [width] [height]

Each frame is path-traced by `pt`, tone-mapped with the same curve as the still, and
piped straight into ffmpeg. The frames are played forward then backward, so the clip loops.
"""
import math
import os
import subprocess
import sys
import tempfile

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tonemap import pbr_neutral, to_srgb  # noqa: E402

PX, PZ, G = 280, 254, 28          # pagoda centre and garden level (see index.html)
DIST, HEIGHT = 494, 210
AZ0, AZ1 = 21.0, 49.0             # degrees off the pagoda's front face
FPS = 24


def main():
    pt, scene, out = sys.argv[1], sys.argv[2], sys.argv[3]
    frames = int(sys.argv[4]) if len(sys.argv) > 4 else 96
    spp = int(sys.argv[5]) if len(sys.argv) > 5 else 8
    w = int(sys.argv[6]) if len(sys.argv) > 6 else 1920
    h = int(sys.argv[7]) if len(sys.argv) > 7 else 1080
    tmp = os.path.join(tempfile.mkdtemp(), 'frame.f32')
    shots = []
    for i in range(frames):
        t = i / (frames - 1)
        t = t * t * (3 - 2 * t)                       # ease in and out, so the turn-around is gentle
        az = math.radians(AZ0 + (AZ1 - AZ0) * t)
        dist = DIST - 26 * math.sin(math.pi * t)      # drift a little closer mid-swing
        eye = (PX + math.sin(az) * dist, G + HEIGHT - 8 * math.sin(math.pi * t), PZ + math.cos(az) * dist)
        subprocess.run([pt, f'scene={scene}', f'out={tmp}', f'w={w}', f'h={h}', f'spp={spp}', f'pass={spp}',
                        f'seed={i}', 'bounces=4', 'eye=%f,%f,%f' % eye], check=True, stderr=subprocess.DEVNULL)
        img = np.fromfile(tmp, dtype=np.float32, count=w * h * 3).reshape(h, w, 3)
        shots.append((to_srgb(pbr_neutral(img * 0.62)) * 255.0 + 0.5).astype(np.uint8).tobytes())
        print(f'\rframe {i + 1}/{frames}', end='', file=sys.stderr, flush=True)
    enc = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{w}x{h}',
                            '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-preset', 'slow', '-crf', '19',
                            '-pix_fmt', 'yuv420p', '-movflags', '+faststart', out], stdin=subprocess.PIPE)
    for frame in shots + shots[-2:0:-1]:
        enc.stdin.write(frame)
    enc.stdin.close()
    enc.wait()
    print(f'\n{out}', file=sys.stderr)


if __name__ == '__main__':
    main()
