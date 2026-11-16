#!/bin/bash
# The desert drive clip (true 24 fps, motion blur, animated crew), then the refreshed stills.
# With --wait it first waits for the house render queue to finish, since the two do not fit in memory together.
set -u
OUT=${1:-/home/user/out/final}
HERE="$(cd "$(dirname "$0")" && pwd)"
if [ "${2:-}" = "--wait" ]; then while pgrep -f render_house_videos.sh >/dev/null; do sleep 20; done; fi
cd "$HERE/sahara-voyage"
python3 build.py --anim --frames 110 --fps 24 --res 960x540 --samples 16 --out "$OUT" > "$OUT/log_sahara_anim.txt" 2>&1
ffmpeg -y -loglevel error -framerate 24 -i "$OUT/anim_sahara/f_%04d.png" -c:v libx264 -crf 17 -pix_fmt yuv420p "$OUT/sahara.mp4"
python3 build.py --cams drive,side,front --res 1600x900 --samples 64 --out "$OUT" > "$OUT/log_sahara_stills2.txt" 2>&1
echo done > "$OUT/SAHARA_DONE"
