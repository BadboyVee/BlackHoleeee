#!/bin/bash
# Renders every still and the three video clips. Usage: ./render_all.sh [out_dir]
# Stills: 1600x900. Clips: 960x540 rendered at 12 fps, motion-interpolated to 24 fps.
set -u
OUT=${1:-/home/user/out/final}
HERE="$(cd "$(dirname "$0")" && pwd)"
mkdir -p "$OUT"
cd "$HERE/duplex-house"
python3 build.py --cams hero,aerial,living,pool,front,kitchen,master,gate,dining,aerial2,drive,back,hall,bath,bed2,street \
    --res 1600x900 --samples 64 --out "$OUT" > "$OUT/log_duplex_stills.txt" 2>&1
cd "$HERE/sahara-voyage"
python3 build.py --cams drive,wide,side,front,aerial,rear --res 1600x900 --samples 64 --out "$OUT" > "$OUT/log_sahara_stills.txt" 2>&1
python3 build.py --mode stop --cams stop,stopwide --res 1600x900 --samples 64 --out "$OUT" > "$OUT/log_sahara_stop.txt" 2>&1
python3 build.py --anim --frames 72 --fps 12 --res 960x540 --samples 16 --out "$OUT" > "$OUT/log_sahara_anim.txt" 2>&1
cd "$HERE/duplex-house"
python3 build.py --anim exterior --frames 72 --res 960x540 --samples 16 --out "$OUT" > "$OUT/log_duplex_ext.txt" 2>&1
python3 build.py --anim interior --frames 84 --res 960x540 --samples 16 --out "$OUT" > "$OUT/log_duplex_int.txt" 2>&1
for n in sahara exterior interior; do
  ffmpeg -y -loglevel error -framerate 12 -i "$OUT/anim_$n/f_%04d.png" \
    -vf "minterpolate=fps=24:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1" -c:v libx264 -crf 18 -pix_fmt yuv420p "$OUT/$n.mp4"
done
echo done > "$OUT/DONE"
