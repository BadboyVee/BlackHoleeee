#!/usr/bin/env bash
# Rebuild PZ_Nigeria_Analysis.xlsx and PZ_Nigeria_Analysis.pptx.
#
# Needs python3 with openpyxl, python-pptx and lxml; node with pptxgenjs (run `npm install`
# in ../../marketing-budget/src, whose chart and slide clean-up scripts this build reuses);
# and LibreOffice (soffice).
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
OUT="$(dirname "$HERE")"
SHARED="$(cd "$HERE/../../marketing-budget/src" && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
export NODE_PATH="${NODE_PATH:-$SHARED/node_modules}"

# 1. Workbook with live formulas (openpyxl saves them without results).
python3 "$HERE/build_workbook.py" "$TMP/raw.xlsx"

# 2. LibreOffice computes every formula; its results are written into the original file so
#    previewers show them too. Excel recalculates on open anyway.
mkdir -p "$TMP/recalc"
SAL_USE_VCLPLUGIN=svp soffice "-env:UserInstallation=file://$TMP/lo_profile" --headless \
  --convert-to xlsx --outdir "$TMP/recalc" "$TMP/raw.xlsx" >/dev/null 2>&1
python3 "$SHARED/add_cached_values.py" "$TMP/raw.xlsx" "$TMP/recalc/raw.xlsx" \
  "$OUT/PZ_Nigeria_Analysis.xlsx"

# 3. The figures and text the slides use, read from the finished workbook.
python3 "$HERE/export_slide_data.py" "$OUT/PZ_Nigeria_Analysis.xlsx" "$TMP/raw.xlsx.cells.json" \
  "$TMP/slide_data.json"

# 4. Slides; charts rewritten to the strict chart schema; one paragraph-settings block per
#    paragraph, a Push transition on every slide and the automatic entrance animations.
node "$HERE/build_deck.js" "$TMP/slide_data.json" "$TMP/deck.pptx"
python3 "$SHARED/sanitize_charts.py" "$TMP/deck.pptx" "$TMP/deck_clean.pptx" \
  ${SCHEMA_DIR:+--xsd "$SCHEMA_DIR/dml-chart.xsd"}
python3 "$SHARED/finish_deck.py" "$TMP/deck_clean.pptx" "$TMP/deck.anim.json" \
  "$OUT/PZ_Nigeria_Analysis.pptx"

# 5. Strict schema check of both files (SCHEMA_DIR: the ISO/IEC 29500 transitional schemas).
if [ -n "${SCHEMA_DIR:-}" ]; then
  python3 "$SHARED/validate_strict.py" "$SCHEMA_DIR" \
    "$OUT/PZ_Nigeria_Analysis.pptx" "$OUT/PZ_Nigeria_Analysis.xlsx"
fi
