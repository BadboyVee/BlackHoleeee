#!/usr/bin/env bash
# Rebuild PZ_Nigeria_Analysis.xlsx, PZ_Nigeria_Analysis.pptx and the written report
# PZ_Nigeria_Analysis_Report.docx, in Office 2013's style (see office2013.py).
#
# Needs python3 with openpyxl, python-pptx, XlsxWriter and lxml; node with the docx package
# (run `npm install` in this folder first); and LibreOffice (soffice). The chart clean-up,
# animation and validation scripts are shared with ../../marketing-budget/src.
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
OUT="$(dirname "$HERE")"
SHARED="$(cd "$HERE/../../marketing-budget/src" && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
export NODE_PATH="${NODE_PATH:-$HERE/node_modules}"

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

# 3b. The written report (Word 2013 compatibility mode), from the same figures.
node "$HERE/build_report.js" "$TMP/slide_data.json" "$OUT/PZ_Nigeria_Analysis_Report.docx"

# 4. Slides on PowerPoint 2013's widescreen Office Theme; charts checked against the strict
#    chart schema; then a Push transition on every slide and the automatic entrance animations.
python3 "$HERE/office2013.py" "$TMP/template.pptx"
python3 "$HERE/build_deck.py" "$TMP/slide_data.json" "$TMP/template.pptx" "$TMP/deck.pptx"
python3 "$SHARED/sanitize_charts.py" "$TMP/deck.pptx" "$TMP/deck_clean.pptx" \
  ${SCHEMA_DIR:+--xsd "$SCHEMA_DIR/dml-chart.xsd"}
python3 "$SHARED/finish_deck.py" "$TMP/deck_clean.pptx" "$TMP/deck.anim.json" \
  "$OUT/PZ_Nigeria_Analysis.pptx"

# 5. Strict schema check of all three files (SCHEMA_DIR: the ISO/IEC 29500 transitional schemas).
if [ -n "${SCHEMA_DIR:-}" ]; then
  python3 "$SHARED/validate_strict.py" "$SCHEMA_DIR" \
    "$OUT/PZ_Nigeria_Analysis.pptx" "$OUT/PZ_Nigeria_Analysis.xlsx" "$OUT/PZ_Nigeria_Analysis_Report.docx"
fi
