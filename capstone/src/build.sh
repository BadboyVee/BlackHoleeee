#!/usr/bin/env bash
# Rebuild the capstone project for CyberStart by SkillUp Academy:
#   Capstone_Market_Research.xlsx   the customer research, market gaps and opportunities
#   Capstone_Market_Research.pptx   the report as a PowerPoint 2013 deck, in the minimal teal design
#
# Needs python3 with openpyxl, python-pptx, lxml, numpy and Pillow, and LibreOffice (soffice). It
# reuses ../../pz-analysis/src/office2013.py (the Office 2013 theme and template),
# ../../assignment/src (the slide design and the fit check) and ../../marketing-budget/src (chart
# clean-up, transitions, animations and validation).
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
OUT="$(dirname "$HERE")"
PZ="$(cd "$HERE/../../pz-analysis/src" && pwd)"
KIT="$(cd "$HERE/../../assignment/src" && pwd)"
SHARED="$(cd "$HERE/../../marketing-budget/src" && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
export PYTHONPATH="$HERE:$KIT:$PZ${PYTHONPATH:+:$PYTHONPATH}"

# 1. The workbook with live formulas; LibreOffice works out the results, which are written into
#    the file so previewers show them too. Excel recalculates on open anyway.
python3 "$HERE/build_workbook.py" "$TMP/raw.xlsx"
mkdir -p "$TMP/recalc"
SAL_USE_VCLPLUGIN=svp soffice "-env:UserInstallation=file://$TMP/lo_profile" --headless \
  --convert-to xlsx --outdir "$TMP/recalc" "$TMP/raw.xlsx" >/dev/null 2>&1
python3 "$SHARED/add_cached_values.py" "$TMP/raw.xlsx" "$TMP/recalc/raw.xlsx" "$OUT/Capstone_Market_Research.xlsx"

# 2. The deck, with the worked-out figures read from the finished workbook; its charts checked
#    against the strict chart schema; then a transition, the animations and a timing on every
#    slide (seconds per slide: about 7 minutes in all, or sooner on a click).
ADVANCE=10,25,25,30,25,30,30,30,30,30,35,30,30,30,25,10
TRANSITIONS=fade,push,push,push,push,push,push,push,push,push,push,push,push,push,push,fade
python3 "$HERE/export_deck_data.py" "$OUT/Capstone_Market_Research.xlsx" "$TMP/deck_data.json"
python3 "$KIT/make_wood.py" "$TMP/wood.jpg"
python3 "$PZ/office2013.py" "$TMP/template.pptx"
deck="$OUT/Capstone_Market_Research.pptx"
python3 "$HERE/build_deck.py" "$TMP/deck_data.json" "$TMP/template.pptx" "$TMP/wood.jpg" minimal "$TMP/deck.pptx"
python3 "$SHARED/sanitize_charts.py" "$TMP/deck.pptx" "$TMP/deck_clean.pptx" \
  ${SCHEMA_DIR:+--xsd "$SCHEMA_DIR/dml-chart.xsd"}
python3 "$SHARED/finish_deck.py" "$TMP/deck_clean.pptx" "$TMP/deck.anim.json" "$deck" \
  --transition "$TRANSITIONS" --advance "$ADVANCE"
# Every text box must fit its text, measured with fonts as wide as Office's Calibri.
python3 "$KIT/check_fit.py" "$deck"

# 3. Strict schema check of both files (SCHEMA_DIR: the ISO/IEC 29500 transitional schemas).
if [ -n "${SCHEMA_DIR:-}" ]; then
  python3 "$SHARED/validate_strict.py" "$SCHEMA_DIR" "$deck" "$OUT/Capstone_Market_Research.xlsx"
fi
