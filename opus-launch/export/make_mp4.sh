#!/bin/bash
# Assemble the postable MP4 (see the README's "Video file"):
#   the preview card for 1.6 s, dissolving over 0.4 s into the film; the film's frames, with the
#   Blender horse's full-size frames (given the film's grain) in 203-217; a 1 s hold on the last
#   frame, fading out; the score delayed to match; the card embedded as cover art.
#   ./make_mp4.sh <out.mp4>
# FRAMES, HORSE, CARD and SCORE override the inputs. BITRATE is the video's average bitrate
# (default 9M: about 26 MB in all). It's a two-pass encode, so the file size lands on target.
set -e
cd "$(dirname "$0")"
OUT=$1; shift
FRAMES=${FRAMES:-out/frames}; HORSE=${HORSE:-../horse/blender/out}; CARD=${CARD:-out/card.png}; SCORE=${SCORE:-out/score.wav}
BITRATE=${BITRATE:-9M}
SEQ=$(mktemp -d)
trap 'rm -rf "$SEQ"' EXIT
python3 grain.py "$HORSE" "$SEQ/horse" > /dev/null        # the film's grain, as on every other frame
for i in $(seq 0 500); do
  n=$(printf %04d $i)
  src=$FRAMES/f$n.png
  if [ $i -ge 203 ] && [ $i -le 217 ]; then src=$SEQ/horse/h$(printf %02d $((i - 202))).png; fi
  [ -f "$src" ] || { echo "missing $src"; exit 1; }
  ln -s "$(realpath "$src")" "$SEQ/f$n.png"
done
IN=(-loop 1 -framerate 25 -t 2.0 -i "$CARD" -framerate 25 -i "$SEQ/f%04d.png" -i "$CARD" -i "$SCORE")
VIDEO="[0:v]format=gbrp,setsar=1[card];\
[1:v]format=gbrp,setsar=1,tpad=stop_mode=clone:stop_duration=1.0,fade=t=out:st=20.44:d=0.6[film];\
[card][film]xfade=transition=fade:duration=0.4:offset=1.6,scale=out_color_matrix=bt709:out_range=tv,format=yuv420p[v]"
AUDIO="[3:a]adelay=1600|1600,atrim=0:22.64,afade=t=out:st=22.1:d=0.54[a]"
X264=(-c:v:0 libx264 -preset:v:0 slow -profile:v:0 high -tune:v:0 film -b:v:0 "$BITRATE" -maxrate:v:0 14M -bufsize:v:0 18M -passlogfile:v:0 "$SEQ/x264")
ffmpeg -hide_banner -loglevel warning -stats -y "${IN[@]}" -filter_complex "$VIDEO" -map "[v]" "${X264[@]}" -pass:v:0 1 "$@" -f null /dev/null
ffmpeg -hide_banner -loglevel warning -stats -y "${IN[@]}" -filter_complex "$VIDEO;$AUDIO" \
  -map "[v]" -map "[a]" -map 2:v "${X264[@]}" -pass:v:0 2 \
  -colorspace:v:0 bt709 -color_primaries:v:0 bt709 -color_trc:v:0 bt709 -color_range:v:0 tv \
  -c:v:1 mjpeg -q:v:1 2 -disposition:v:1 attached_pic \
  -c:a aac -b:a 192k -ar 48000 \
  -movflags +faststart "$@" "$OUT"
