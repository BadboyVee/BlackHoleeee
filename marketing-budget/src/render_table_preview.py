#!/usr/bin/env python3
"""Render one block of the workbook (the budget table, A4:G15) to a PNG picture.

PowerPoint shows a picture of an embedded Excel worksheet object until someone double-clicks
it. This builds that picture from the workbook itself: it prints only the table block to PDF
with LibreOffice at 100% scale, rasterises the page and trims the white paper around it.

Usage: python render_table_preview.py workbook.xlsx output.png [--range A4:G15] [--dpi 300]
Prints the block's natural size in points, which the slide uses for the object's aspect ratio.
"""
import argparse
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from openpyxl import load_workbook
from openpyxl.worksheet.page import PageMargins
from PIL import Image, ImageChops


def soffice_pdf(xlsx: Path, outdir: Path):
    env = dict(os.environ, SAL_USE_VCLPLUGIN="svp")
    with tempfile.TemporaryDirectory(prefix="lo_profile_") as profile:
        subprocess.run(
            ["soffice", f"-env:UserInstallation={Path(profile).as_uri()}", "--headless",
             "--convert-to", "pdf", "--outdir", str(outdir), str(xlsx)],
            check=True, capture_output=True, env=env, timeout=180,
        )
    return outdir / (xlsx.stem + ".pdf")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("workbook")
    ap.add_argument("output")
    ap.add_argument("--range", default="A4:G15")
    ap.add_argument("--dpi", type=int, default=300)
    # Excel draws a column-width unit of Arial 10 as 7 px; LibreOffice uses the exact digit
    # width (~7.41 px). Scaling the widths makes the picture match Excel's proportions.
    ap.add_argument("--width-scale", type=float, default=7 / 7.408)
    args = ap.parse_args()

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        wb = load_workbook(args.workbook)
        ws = wb.active
        for dim in ws.column_dimensions.values():
            if dim.width:
                dim.width = dim.width * args.width_scale
        ws.print_area = args.range
        ws.sheet_properties.pageSetUpPr.fitToPage = False
        ws.page_setup.scale = 100
        ws.page_setup.orientation = "landscape"
        ws.print_options.horizontalCentered = False
        ws.page_margins = PageMargins(left=0.2, right=0.2, top=0.2, bottom=0.2, header=0, footer=0)
        ws.oddFooter.center.text = None
        ws.oddHeader.center.text = None
        staged = tmp / "table_block.xlsx"
        wb.save(staged)

        pdf = soffice_pdf(staged, tmp)
        subprocess.run(["pdftoppm", "-png", "-r", str(args.dpi), "-f", "1", "-l", "1",
                        "-singlefile", str(pdf), str(tmp / "page")], check=True)
        page = Image.open(tmp / "page.png").convert("RGB")

    # Trim the paper: keep everything that is not (near-)white, plus a 2px safety edge.
    white = Image.new("RGB", page.size, (255, 255, 255))
    diff = ImageChops.difference(page, white).convert("L").point(lambda p: 255 if p > 6 else 0)
    left, top, right, bottom = diff.getbbox()
    pad = 2
    table = page.crop((max(left - pad, 0), max(top - pad, 0),
                       min(right + pad, page.width), min(bottom + pad, page.height)))
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    table.save(args.output, optimize=True)

    size = {
        "png": str(args.output),
        "px": [table.width, table.height],
        "points": [round(table.width * 72 / args.dpi, 2), round(table.height * 72 / args.dpi, 2)],
    }
    print(json.dumps(size))


if __name__ == "__main__":
    main()
