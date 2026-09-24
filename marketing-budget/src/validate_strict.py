#!/usr/bin/env python3
"""Validate every XML part of a .pptx or .xlsx against the ISO/IEC 29500 schemas.

PowerPoint 2013 refuses decks that newer tools forgive, so "it opens in LibreOffice" is not
enough. This checks each slide, layout, master, notes page, theme, chart and worksheet
against the transitional schemas and exits non-zero on the first package with an error.
Office extensions wrapped in mc:AlternateContent are removed before checking, as the base
schema does not describe them.

Usage: python validate_strict.py SCHEMA_DIR file.pptx [file.xlsx ...]
  SCHEMA_DIR holds pml.xsd, sml.xsd, dml-main.xsd, dml-chart.xsd, ...
"""
import sys
import zipfile
from pathlib import Path

from lxml import etree

MC = "http://schemas.openxmlformats.org/markup-compatibility/2006"
SCHEMA_BY_NS = {
    "http://schemas.openxmlformats.org/presentationml/2006/main": "pml.xsd",
    "http://schemas.openxmlformats.org/spreadsheetml/2006/main": "sml.xsd",
    "http://schemas.openxmlformats.org/drawingml/2006/main": "dml-main.xsd",
    "http://schemas.openxmlformats.org/drawingml/2006/chart": "dml-chart.xsd",
    "http://schemas.openxmlformats.org/drawingml/2006/spreadsheetDrawing": "dml-spreadsheetDrawing.xsd",
}
SKIP_PREFIXES = ("docProps/", "customXml/", "[Content_Types]", "_rels/")
P = "{http://schemas.openxmlformats.org/presentationml/2006/main}"
A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"


def normalise(name, root):
    """Forms PowerPoint writes and reads that this schema edition spells differently.

    Only the in-memory copy is changed; the file is left as PowerPoint expects it.
    """
    # PowerPoint writes bullet size as thousandths of a percent (100000); the schema wants "100%".
    for el in root.iter(A + "buSzPct"):
        val = el.get("val", "")
        if val.isdigit():
            el.set("val", f"{int(val) // 1000}%")
    # pptxgenjs lists notes masters after the slides. PowerPoint reads that order, and
    # moving the element in the file breaks the deck, so only the checked copy is reordered.
    if name == "ppt/presentation.xml":
        notes, slides = root.find(P + "notesMasterIdLst"), root.find(P + "sldIdLst")
        if notes is not None and slides is not None and root.index(notes) > root.index(slides):
            root.remove(notes)
            slides.addprevious(notes)


def main():
    schema_dir = Path(sys.argv[1])
    cache = {}
    failed = 0
    for package in sys.argv[2:]:
        checked = bad = 0
        with zipfile.ZipFile(package) as z:
            for name in sorted(z.namelist()):
                if not name.endswith(".xml") or name.startswith(SKIP_PREFIXES) or "/_rels/" in name:
                    continue
                root = etree.fromstring(z.read(name))
                xsd = SCHEMA_BY_NS.get(etree.QName(root).namespace)
                if xsd is None:
                    continue
                if xsd not in cache:
                    cache[xsd] = etree.XMLSchema(etree.parse(str(schema_dir / xsd)))
                for alt in root.xpath("//mc:AlternateContent", namespaces={"mc": MC}):
                    alt.getparent().remove(alt)
                normalise(name, root)
                checked += 1
                schema = cache[xsd]
                if not schema.validate(etree.ElementTree(root)):
                    bad += 1
                    for err in list(schema.error_log)[:3]:
                        print(f"{Path(package).name}:{name}:{err.line}: {err.message[:220]}")
        print(f"{Path(package).name}: {checked} parts checked, {bad} invalid")
        failed += bad
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
