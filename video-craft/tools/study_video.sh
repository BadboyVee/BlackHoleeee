#!/bin/bash
# Study a reference video: frames, contact sheets, cut metrics, motion/palette, audio grid, sync.
#   ./study_video.sh <video> <outdir> [python]
# Needs ffmpeg and a Python with numpy, scipy, opencv-python-headless, pillow:
#   python3 -m venv /tmp/cv && /tmp/cv/bin/pip install numpy scipy opencv-python-headless pillow
set -e
V=$1; O=$2; PY=${3:-python3}; HERE="$(cd "$(dirname "$0")" && pwd)"
mkdir -p "$O/frames" "$O/audio" "$O/aud"
FPS=$(ffmpeg -hide_banner -i "$V" 2>&1 | grep -oE '[0-9.]+ fps' | head -1 | cut -d' ' -f1)
echo "fps $FPS"
ffmpeg -hide_banner -loglevel error -y -i "$V" -vsync 0 -q:v 2 "$O/frames/f%04d.jpg"
ffmpeg -hide_banner -loglevel error -y -i "$V" -vn -ac 2 -c:a pcm_s16le "$O/audio/ref.wav"
$PY -I "$HERE/sheets.py" "$O/frames" "$O/sheets" "$FPS"           # 8x6 thumbnails per sheet: look at every one
$PY -I "$HERE/cuts.py" "$O/frames" "$O/metrics.json"               # luma diff, histogram distance, edge change, colour
$PY -I "$HERE/motion.py" "$O/frames" "$O/motion.json"              # per-frame zoom/roll/shift, ink box, 5-colour palette
$PY -I "$HERE/audio.py" "$O/audio/ref.wav" "$O/aud"                # spectrogram, onset envelope, tempo, bands
$PY -I "$HERE/onsets.py" "$O/audio/ref.wav" "$O/aud"               # sample-accurate kick/clap/hat onsets
$PY -I "$HERE/beatgrid.py" "$O/aud/onsets.json" "$O/metrics.json" "$O/aud/grid.json" "$FPS" | tee "$O/aud/grid.txt"
ffmpeg -hide_banner -nostats -i "$O/audio/ref.wav" -af ebur128=peak=true -f null - 2>&1 | sed -n '/Summary/,$p' | grep -E "I:|LRA:|Peak:"
echo "done: view $O/sheets/*.jpg and $O/aud/spec_*.png, then read $O/aud/grid.txt"
