#!/bin/bash
# usage: tools/preview.sh "shot1 shot2" every sheetname [w h spp]
cd "$(dirname "$0")/.."
SHOTS="$1"; EVERY="${2:-12}"; NAME="${3:-prev}"; W="${4:-960}"; H="${5:-540}"; SPP="${6:-4}"
DIRS=""
for s in $SHOTS; do
  D="out/prev_${NAME}/$s"
  mkdir -p "$D"
  node render/render.mjs --shot "$s" --w "$W" --h "$H" --spp "$SPP" --every "$EVERY" --out "$D" --msaa 0 2>&1 | grep -E "rror" 
  DIRS="$DIRS,$D"
done
/opt/venv/bin/python tools/sheet.py "${DIRS#,}" "out/${NAME}_sheet.png" 4 480
echo "out/${NAME}_sheet.png"
