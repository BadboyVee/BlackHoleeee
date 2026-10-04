#!/usr/bin/env bash
# Rebuild the assignment files in Office 2013's style:
#   Student_Test_Results.xlsx          test results of 25 students in 7 subjects, graded with IF
#   Relative_Interest_Pie_Chart.xlsx   the relative-interest observations and their pie chart
#   Relative_Interest_Pie_Chart.pptx   the pie chart in a PowerPoint 2013 deck
#
# Needs python3 with openpyxl, python-pptx, XlsxWriter and lxml, and LibreOffice (soffice). The
# Office 2013 theme and slide template come from ../../pz-analysis/src/office2013.py; the chart
# clean-up, finishing and validation scripts are shared with ../../marketing-budget/src.
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
OUT="$(dirname "$HERE")"
PZ="$(cd "$HERE/../../pz-analysis/src" && pwd)"
SHARED="$(cd "$HERE/../../marketing-budget/src" && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
export PYTHONPATH="$PZ${PYTHONPATH:+:$PYTHONPATH}"

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

# 3. The deck, on PowerPoint 2013's widescreen Office Theme. Its figures are read from the
#    finished workbook; its chart is checked against the strict chart schema; then each slide
#    gets a transition: Fade, Push, Wipe, Split and Cover.
python3 "$HERE/export_deck_data.py" "$OUT/Relative_Interest_Pie_Chart.xlsx" "$TMP/deck_data.json"
python3 "$PZ/office2013.py" "$TMP/template.pptx"
python3 "$HERE/build_deck.py" "$TMP/deck_data.json" "$TMP/template.pptx" "$TMP/deck.pptx"
python3 "$SHARED/sanitize_charts.py" "$TMP/deck.pptx" "$TMP/deck_clean.pptx" \
  ${SCHEMA_DIR:+--xsd "$SCHEMA_DIR/dml-chart.xsd"}
echo '{}' > "$TMP/no_animations.json"
python3 "$SHARED/finish_deck.py" "$TMP/deck_clean.pptx" "$TMP/no_animations.json" \
  "$OUT/Relative_Interest_Pie_Chart.pptx" --transition fade,push,wipe,split,cover

# 4. Strict schema check of all three files (SCHEMA_DIR: the ISO/IEC 29500 transitional schemas).
if [ -n "${SCHEMA_DIR:-}" ]; then
  python3 "$SHARED/validate_strict.py" "$SCHEMA_DIR" "$OUT/Relative_Interest_Pie_Chart.pptx" \
    "$OUT/Student_Test_Results.xlsx" "$OUT/Relative_Interest_Pie_Chart.xlsx"
fi
