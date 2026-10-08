#!/usr/bin/env bash
# Rebuild the market segmentation assignment for SkillUp Academy:
#   Segmentation_Matrix.xlsx                      the segmentation matrix, scores and bar charts
#   Market_Segmentation.pptx                      the report as a PowerPoint 2013 deck, in a minimal design
#
# Needs python3 with openpyxl, python-pptx, XlsxWriter, lxml, numpy and Pillow, and LibreOffice
# (soffice). It reuses ../../pz-analysis/src/office2013.py (the Office 2013 theme and slide
# template), ../../assignment/src (the slide styles, the wood picture and the fit check) and
# ../../marketing-budget/src (chart clean-up, transitions and validation).
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
python3 "$SHARED/add_cached_values.py" "$TMP/raw.xlsx" "$TMP/recalc/raw.xlsx" "$OUT/Segmentation_Matrix.xlsx"

# 2. The deck, in the minimal design, with every figure read from the finished workbook; its
#    charts checked against the strict chart schema; then a transition, the animations (the plan
#    build_deck.py saves) and a timing on every slide. (build_deck.py can also build the older
#    marketing, pz and mixed designs: add them to STYLES below.)
python3 "$HERE/export_deck_data.py" "$OUT/Segmentation_Matrix.xlsx" "$TMP/deck_data.json"
python3 "$KIT/make_wood.py" "$TMP/wood.jpg"
python3 "$PZ/office2013.py" "$TMP/template.pptx"
# Slide timings (Transitions > Advance Slide > After), in seconds, for the nine slides: each
# slide moves on by itself, or sooner on a click.
ADVANCE=10,25,35,35,35,35,25,35,10
# Transitions: Fade on the title and closing slides, Push between the content slides.
TRANSITIONS=fade,push,push,push,push,push,push,push,fade
DECKS=()
STYLES=(minimal)
for style in "${STYLES[@]}"; do
  case "$style" in
    minimal) deck="$OUT/Market_Segmentation.pptx" ;;
    marketing) deck="$OUT/Market_Segmentation_Marketing.pptx" ;;
    pz) deck="$OUT/Market_Segmentation_PZ.pptx" ;;
    mixed) deck="$OUT/Market_Segmentation_Mixed.pptx" ;;
  esac
  python3 "$HERE/build_deck.py" "$TMP/deck_data.json" "$TMP/template.pptx" "$TMP/wood.jpg" "$style" \
    "$TMP/$style.pptx"
  python3 "$SHARED/sanitize_charts.py" "$TMP/$style.pptx" "$TMP/${style}_clean.pptx" \
    ${SCHEMA_DIR:+--xsd "$SCHEMA_DIR/dml-chart.xsd"}
  python3 "$SHARED/finish_deck.py" "$TMP/${style}_clean.pptx" "$TMP/$style.anim.json" "$deck" \
    --transition "$TRANSITIONS" --advance "$ADVANCE"
  DECKS+=("$deck")
done
# Every text box must fit its text, measured with fonts as wide as Office's Calibri and Cambria.
python3 "$KIT/check_fit.py" "${DECKS[@]}"

# 3. Strict schema check of every file (SCHEMA_DIR: the ISO/IEC 29500 transitional schemas).
if [ -n "${SCHEMA_DIR:-}" ]; then
  python3 "$SHARED/validate_strict.py" "$SCHEMA_DIR" "${DECKS[@]}" "$OUT/Segmentation_Matrix.xlsx"
fi
