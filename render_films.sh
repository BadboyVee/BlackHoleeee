#!/bin/bash
# The three films at 1280x720, one after another (they do not fit in memory side by side), then the stills.
# Every frame is a file, so re-running continues where it stopped.
set -u
OUT=${1:-/home/user/out/films}
HERE="$(cd "$(dirname "$0")" && pwd)"
mkdir -p "$OUT"
mi="minterpolate=fps=24:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1"
cd "$HERE/duplex-house"
python3 build.py --anim street --res 1280x720 --samples 10 --out "$OUT" >> "$OUT/log_street.txt" 2>&1
[ -s "$OUT/street.mp4" ] || ffmpeg -y -loglevel error -framerate 12 -i "$OUT/anim_street/f_%04d.png" -vf "$mi" \
  -c:v libx264 -preset slow -crf 16 -pix_fmt yuv420p "$OUT/street.mp4.tmp.mp4" && mv "$OUT/street.mp4.tmp.mp4" "$OUT/street.mp4"
python3 build.py --anim interior --res 1280x720 --samples 12 --out "$OUT" >> "$OUT/log_interior.txt" 2>&1
[ -s "$OUT/interior.mp4" ] || ffmpeg -y -loglevel error -framerate 12 -i "$OUT/anim_interior/f_%04d.png" -vf "$mi" \
  -c:v libx264 -preset slow -crf 16 -pix_fmt yuv420p "$OUT/interior.mp4.tmp.mp4" && mv "$OUT/interior.mp4.tmp.mp4" "$OUT/interior.mp4"
cd "$HERE/sahara-voyage"
python3 build.py --anim --frames 480 --fps 24 --res 1280x720 --samples 10 --out "$OUT" >> "$OUT/log_sahara.txt" 2>&1
[ -s "$OUT/sahara.mp4" ] || ffmpeg -y -loglevel error -framerate 24 -i "$OUT/anim_sahara/f_%04d.png" \
  -c:v libx264 -preset slow -crf 16 -pix_fmt yuv420p "$OUT/sahara.mp4.tmp.mp4" && mv "$OUT/sahara.mp4.tmp.mp4" "$OUT/sahara.mp4"
cd "$HERE/duplex-house"
python3 build.py --cams street_w,street_e,street_air,hero,front,living,pool,kitchen,dining,gate,drive,master,back \
  --res 1920x1080 --samples 96 --out "$OUT/stills" >> "$OUT/log_stills.txt" 2>&1
cd "$HERE/sahara-voyage"
python3 build.py --cams drive,side,front,wide --res 1920x1080 --samples 96 --out "$OUT/stills" >> "$OUT/log_stills.txt" 2>&1
python3 build.py --mode stop --cams stop,stopwide --res 1920x1080 --samples 96 --out "$OUT/stills" >> "$OUT/log_stills.txt" 2>&1
echo done > "$OUT/ALL_DONE"
