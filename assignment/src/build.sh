#!/usr/bin/env bash
# Rebuild the assignment files in Office 2013's style:
#   Student_Test_Results.xlsx          test results of 25 students in 7 subjects, graded with IF
#   Relative_Interest_Pie_Chart.xlsx   the relative-interest observations and their pie chart
#   Relative_Interest_Pie_Chart.pptx   the pie chart in a PowerPoint 2013 deck
#
# Needs python3 with openpyxl, python-pptx and lxml; node with the packages in package.json
# (run `npm install` in this folder first); and LibreOffice (soffice). The workbooks use the
# Office 2013 theme in ../../pz-analysis/src/office2013.py; the chart clean-up, finishing and
# validation scripts are shared with ../../marketing-budget/src.
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
OUT="$(dirname "$HERE")"
PZ="$(cd "$HERE/../../pz-analysis/src" && pwd)"
SHARED="$(cd "$HERE/../../marketing-budget/src" && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
export PYTHONPATH="$PZ${PYTHONPATH:+:$PYTHONPATH}"
export NODE_PATH="${NODE_PATH:-$HERE/node_modules}"

# 1. Workbooks with live formulas (openpyxl saves them without results).
python3 "$HERE/build_workbooks.py" "$TMP/results.xlsx" "$TMP/interest.xlsx"

# 2. LibreOffice computes every formula; its results are written into the original files so
#    previewers show them too. Excel recalculates on open anyway.
mkdir -p "$TMP/recalc"
SAL_USE_VCLPLUGIN=svp soffice "-env:UserInstallation=file://$TMP/lo_profile" --headless \
  --convert-to xlsx --outdir "$TMP/recalc" "$TMP/results.xlsx" "$TMP/interest.xlsx" >/dev/null 2>&1
python3 "$SHARED/add_cached_values.py" "$TMP/results.xlsx" "$TMP/recalc/results.xlsx" \
  "$OUT/Student_Test_Results.xlsx"
python3 "$SHARED/add_cached_values.py" "$TMP/interest.xlsx" "$TMP/recalc/interest.xlsx" \
  "$OUT/Relative_Interest_Pie_Chart.xlsx"

# 3. The deck. Its figures are read from the finished workbook; pptxgenjs builds the slides; the
#    chart is rewritten to the strict chart schema (PowerPoint 2013 rejects some of what
#    pptxgenjs writes); then one paragraph-settings block per paragraph and a Fade transition on
#    every slide.
python3 "$HERE/export_deck_data.py" "$OUT/Relative_Interest_Pie_Chart.xlsx" "$TMP/deck_data.json"
node "$HERE/build_deck.js" "$TMP/deck_data.json" "$TMP/deck.pptx"
python3 "$SHARED/sanitize_charts.py" "$TMP/deck.pptx" "$TMP/deck_clean.pptx" \
  ${SCHEMA_DIR:+--xsd "$SCHEMA_DIR/dml-chart.xsd"}
echo '{}' > "$TMP/no_animations.json"
python3 "$SHARED/finish_deck.py" "$TMP/deck_clean.pptx" "$TMP/no_animations.json" \
  "$OUT/Relative_Interest_Pie_Chart.pptx" --transition fade

# 4. Strict schema check of all three files (SCHEMA_DIR: the ISO/IEC 29500 transitional schemas).
if [ -n "${SCHEMA_DIR:-}" ]; then
  python3 "$SHARED/validate_strict.py" "$SCHEMA_DIR" "$OUT/Relative_Interest_Pie_Chart.pptx" \
    "$OUT/Student_Test_Results.xlsx" "$OUT/Relative_Interest_Pie_Chart.xlsx"
fi
