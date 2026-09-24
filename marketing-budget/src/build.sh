#!/usr/bin/env bash
# Rebuild Marketing_Department_Budget.xlsx and Marketing_Department_Budget.pptx.
#
# Needs python3 with openpyxl, python-pptx, lxml and pillow; node with the packages in
# package.json (run `npm install` in this folder first); LibreOffice (soffice); and
# poppler (pdftoppm).
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
OUT="$(dirname "$HERE")"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
TABLE_RANGE="A4:G15"

# 1. Workbook with live formulas (openpyxl saves them without results).
python3 "$HERE/build_workbook.py" "$TMP/raw.xlsx"

# 2. LibreOffice computes every formula when it opens the file; its saved copy holds the
#    results, which are then written into the original so previewers show the numbers.
mkdir -p "$TMP/recalc"
SAL_USE_VCLPLUGIN=svp soffice "-env:UserInstallation=file://$TMP/lo_profile" --headless \
  --convert-to xlsx --outdir "$TMP/recalc" "$TMP/raw.xlsx" >/dev/null 2>&1
python3 "$HERE/add_cached_values.py" "$TMP/raw.xlsx" "$TMP/recalc/raw.xlsx" \
  "$OUT/Marketing_Department_Budget.xlsx"
python3 "$HERE/add_cached_values.py" "$TMP/raw.xlsx" "$TMP/recalc/raw.xlsx" \
  "$TMP/embed.xlsx" --ole-range "$TABLE_RANGE"

# 3. Picture of the budget table, and the figures the slides use.
python3 "$HERE/render_table_preview.py" "$TMP/raw.xlsx" "$TMP/table_preview.png" \
  --range "$TABLE_RANGE" > "$TMP/table_size.json"
python3 "$HERE/export_slide_data.py" "$OUT/Marketing_Department_Budget.xlsx" "$TMP/slide_data.json"

# 4. Slides; charts rewritten to the strict chart schema (PowerPoint 2013 rejects some of
#    what pptxgenjs writes); then the embedded Excel table on slide 7.
node "$HERE/build_deck.js" "$TMP/slide_data.json" "$TMP/table_preview.png" \
  "$TMP/table_size.json" "$TMP/deck.pptx"
python3 "$HERE/sanitize_charts.py" "$TMP/deck.pptx" "$TMP/deck_clean.pptx" \
  ${SCHEMA_DIR:+--xsd "$SCHEMA_DIR/dml-chart.xsd"}
python3 "$HERE/embed_excel_table.py" "$TMP/deck_clean.pptx" "$TMP/embed.xlsx" \
  "$TMP/table_preview.png" "$TMP/table_size.json" "$TMP/deck_embedded.pptx"

# 5. Fade transitions, PowerPoint's text shadow on the headline text, one paragraph-settings
#    block per paragraph.
python3 "$HERE/finish_deck.py" "$TMP/deck_embedded.pptx" "$OUT/Marketing_Department_Budget.pptx"

# 6. Strict schema check of both files (set SCHEMA_DIR to the ISO/IEC 29500 transitional
#    schemas: pml.xsd, sml.xsd, dml-main.xsd, dml-chart.xsd, ...).
if [ -n "${SCHEMA_DIR:-}" ]; then
  python3 "$HERE/validate_strict.py" "$SCHEMA_DIR" \
    "$OUT/Marketing_Department_Budget.pptx" "$OUT/Marketing_Department_Budget.xlsx"
fi
