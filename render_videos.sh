#!/bin/bash
# Renders the three clips one after another (they do not fit in memory side by side),
# then the stills that changed. Frames already on disk are skipped, so it can be re-run.
set -u
OUT=${1:-/home/user/out/final}
HERE="$(cd "$(dirname "$0")" && pwd)"
mkdir -p "$OUT"
cd "$HERE/sahara-voyage"
python3 build.py --anim --frames 110 --fps 24 --res 960x540 --samples 16 --out "$OUT" > "$OUT/log_sahara_anim.txt" 2>&1
ffmpeg -y -loglevel error -framerate 24 -i "$OUT/anim_sahara/f_%04d.png" -c:v libx264 -crf 17 -pix_fmt yuv420p "$OUT/sahara.mp4"
cd "$HERE/duplex-house"
python3 build.py --anim street --frames 132 --res 960x540 --samples 16 --out "$OUT" > "$OUT/log_duplex_street.txt" 2>&1
ffmpeg -y -loglevel error -framerate 12 -i "$OUT/anim_street/f_%04d.png" \
  -vf "minterpolate=fps=24:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1" -c:v libx264 -crf 17 -pix_fmt yuv420p "$OUT/street.mp4"
python3 build.py --anim interior --frames 84 --res 960x540 --samples 16 --out "$OUT" > "$OUT/log_duplex_int.txt" 2>&1
ffmpeg -y -loglevel error -framerate 12 -i "$OUT/anim_interior/f_%04d.png" \
  -vf "minterpolate=fps=24:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1" -c:v libx264 -crf 17 -pix_fmt yuv420p "$OUT/interior.mp4"
python3 build.py --cams street_w,street_e,street_air,front,kitchen --res 1600x900 --samples 64 --out "$OUT" > "$OUT/log_duplex_stills2.txt" 2>&1
cd "$HERE/sahara-voyage"
python3 build.py --cams drive,side --res 1600x900 --samples 64 --out "$OUT" > "$OUT/log_sahara_stills2.txt" 2>&1
echo done > "$OUT/VIDEOS_DONE"
