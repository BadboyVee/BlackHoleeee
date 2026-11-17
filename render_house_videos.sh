#!/bin/bash
# House clips only: street drive-in, interior walk-through, then the changed stills.
set -u
OUT=${1:-/home/user/out/final}
HERE="$(cd "$(dirname "$0")" && pwd)"
cd "$HERE/duplex-house"
python3 build.py --anim street --frames 132 --res 960x540 --samples 16 --out "$OUT" > "$OUT/log_duplex_street.txt" 2>&1
ffmpeg -y -loglevel error -framerate 12 -i "$OUT/anim_street/f_%04d.png" \
  -vf "minterpolate=fps=24:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1" -c:v libx264 -crf 17 -pix_fmt yuv420p "$OUT/street.mp4"
python3 build.py --anim interior --frames 84 --res 960x540 --samples 16 --out "$OUT" > "$OUT/log_duplex_int.txt" 2>&1
ffmpeg -y -loglevel error -framerate 12 -i "$OUT/anim_interior/f_%04d.png" \
  -vf "minterpolate=fps=24:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1" -c:v libx264 -crf 17 -pix_fmt yuv420p "$OUT/interior.mp4"
python3 build.py --cams street_w,street_e,street_air,hero,front,living,pool,kitchen,dining,gate,drive,master,back --res 1600x900 --samples 64 --out "$OUT" > "$OUT/log_duplex_stills2.txt" 2>&1
echo done > "$OUT/HOUSE_DONE"
