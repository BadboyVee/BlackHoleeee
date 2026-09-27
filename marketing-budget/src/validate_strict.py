#!/usr/bin/env python3
"""Validate every XML part of a .pptx or .xlsx against the ISO/IEC 29500 schemas.

PowerPoint 2013 refuses decks that newer tools forgive, so "it opens in LibreOffice" is not
enough. This checks each slide, layout, master, notes page, theme, chart and worksheet
against the transitional schemas and exits non-zero on the first package with an error.
Office extensions wrapped in mc:AlternateContent, and markup in namespaces a part marks as
ignorable, are removed before checking, as the base schema does not describe them.

Workbooks embedded in a deck (the data behind each chart, and embedded Excel objects) are
opened and checked the same way. Workbooks also get checks the schema can't make: a
worksheet must use each table, a table's range must be a real cell range and its column names
must match their header cells, and the stylesheet must define cell formats (cellXfs). Chart
axis ids must stay below 2^31, where every reader can follow them.

Usage: python validate_strict.py SCHEMA_DIR file.pptx [file.xlsx file.docx ...]
  SCHEMA_DIR holds pml.xsd, sml.xsd, wml.xsd, dml-main.xsd, dml-chart.xsd, ...
"""
import io
import posixpath
import re
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
    "http://schemas.openxmlformats.org/wordprocessingml/2006/main": "wml.xsd",
}
SKIP_PREFIXES = ("docProps/", "customXml/", "[Content_Types]", "_rels/")
P = "{http://schemas.openxmlformats.org/presentationml/2006/main}"
A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
S = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
CHART = "{http://schemas.openxmlformats.org/drawingml/2006/chart}"
XML_SPACE = "{http://www.w3.org/XML/1998/namespace}space"
REL = "{http://schemas.openxmlformats.org/package/2006/relationships}Relationship"
R_ID = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"


def strip_compat(root):
    """Remove Office extensions the base schema doesn't describe (Markup Compatibility)."""
    for alt in root.xpath("//mc:AlternateContent", namespaces={"mc": MC}):
        alt.getparent().remove(alt)
    ignorable = set()
    for el in root.iter():
        if not isinstance(el.tag, str):
            continue
        prefixes = el.attrib.pop(f"{{{MC}}}Ignorable", "")
        ignorable |= {el.nsmap.get(p) for p in prefixes.split() if el.nsmap.get(p)}
    if not ignorable:
        return
    for el in list(root.iter()):
        if not isinstance(el.tag, str):
            continue
        if etree.QName(el).namespace in ignorable and el.getparent() is not None:
            el.getparent().remove(el)
            continue
        for attr in list(el.attrib):
            if attr.startswith("{") and etree.QName(attr).namespace in ignorable:
                del el.attrib[attr]


def normalise(name, root):
    """Forms PowerPoint writes and reads that this schema edition spells differently.

    Only the in-memory copy is changed; the file is left as PowerPoint expects it.
    """
    # PowerPoint writes bullet size as thousandths of a percent (100000); the schema wants "100%".
    for el in root.iter(A + "buSzPct"):
        val = el.get("val", "")
        if val.isdigit():
            el.set("val", f"{int(val) // 1000}%")
    # Excel writes xml:space="preserve" on shared-string text, which this schema edition omits.
    for el in root.iter(S + "t"):
        el.attrib.pop(XML_SPACE, None)
    # pptxgenjs lists notes masters after the slides. PowerPoint reads that order, and
    # moving the element in the file breaks the deck, so only the checked copy is reordered.
    if name == "ppt/presentation.xml":
        notes, slides = root.find(P + "notesMasterIdLst"), root.find(P + "sldIdLst")
        if notes is not None and slides is not None and root.index(notes) > root.index(slides):
            root.remove(notes)
            slides.addprevious(notes)


def cell_texts(z):
    """Shared strings of a workbook package."""
    if "xl/sharedStrings.xml" not in z.namelist():
        return []
    sst = etree.fromstring(z.read("xl/sharedStrings.xml"))
    return ["".join(si.itertext()) for si in sst.findall(S + "si")]


def table_errors(z):
    """Excel tables: used by a worksheet, a real range, one column per range column, and names
    equal to their header cells."""
    errors = []
    strings = cell_texts(z)
    linked = set()
    for sheet_name in [n for n in z.namelist() if re.fullmatch(r"xl/worksheets/[^/]+\.xml", n)]:
        sheet = etree.fromstring(z.read(sheet_name))
        folder, base = posixpath.split(sheet_name)
        rels_name = f"{folder}/_rels/{base}.rels"
        if rels_name not in z.namelist():
            continue
        targets = {r.get("Id"): posixpath.normpath(posixpath.join(folder, r.get("Target")))
                   for r in etree.fromstring(z.read(rels_name)).iter(REL)}
        cells = {c.get("r"): c for c in sheet.iter(S + "c")}
        for tp in sheet.iter(S + "tablePart"):
            name = targets.get(tp.get(R_ID))
            linked.add(name)
            table = etree.fromstring(z.read(name))
            ref = table.get("ref", "")
            m = re.fullmatch(r"([A-Z]{1,3})([0-9]+):([A-Z]{1,3})([0-9]+)", ref)
            if not m:
                errors.append(f"{name}: table range {ref!r} is not a cell range")
                continue
            first = sum((ord(ch) - 64) * 26 ** i for i, ch in enumerate(reversed(m.group(1))))
            last = sum((ord(ch) - 64) * 26 ** i for i, ch in enumerate(reversed(m.group(3))))
            columns = table.find(S + "tableColumns").findall(S + "tableColumn")
            if last - first + 1 != len(columns):
                errors.append(f"{name}: range {ref} has {last - first + 1} columns but the table names {len(columns)}")
            for i, column in enumerate(columns):
                n, letters = first + i, ""
                while n:
                    n, rem = divmod(n - 1, 26)
                    letters = chr(65 + rem) + letters
                cell = cells.get(f"{letters}{m.group(2)}")
                text = ""
                if cell is not None:
                    if cell.get("t") == "s":
                        text = strings[int(cell.findtext(S + "v"))]
                    elif cell.get("t") == "inlineStr":
                        text = "".join(cell.find(S + "is").itertext())
                    else:
                        text = cell.findtext(S + "v") or ""
                if text != column.get("name"):
                    errors.append(f"{name}: column {column.get('name')!r} but header cell "
                                  f"{letters}{m.group(2)} holds {text!r}")
    for name in z.namelist():
        if re.fullmatch(r"xl/tables/[^/]+\.xml", name) and name not in linked:
            errors.append(f"{name}: table part that no worksheet uses")
    # Every cell style index points into cellXfs, so Excel always writes one; so should we.
    if "xl/styles.xml" in z.namelist():
        styles = etree.fromstring(z.read("xl/styles.xml"))
        xfs = styles.find(S + "cellXfs")
        if xfs is None or len(xfs) == 0:
            errors.append("xl/styles.xml: no cell formats (cellXfs)")
    return errors


def check_package(label, data, schema_dir, cache):
    """Validate one package (and any workbook embedded in it); return the number of bad parts."""
    checked = bad = 0
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        for name in sorted(z.namelist()):
            if re.fullmatch(r"(ppt|word|xl)/embeddings/[^/]+\.xlsx", name):
                bad += check_package(f"{label} > {posixpath.basename(name)}", z.read(name), schema_dir, cache)
                continue
            if not name.endswith(".xml") or name.startswith(SKIP_PREFIXES) or "/_rels/" in name:
                continue
            root = etree.fromstring(z.read(name))
            xsd = SCHEMA_BY_NS.get(etree.QName(root).namespace)
            if xsd is None:
                continue
            if xsd not in cache:
                cache[xsd] = etree.XMLSchema(etree.parse(str(schema_dir / xsd)))
            strip_compat(root)
            normalise(name, root)
            checked += 1
            schema = cache[xsd]
            if not schema.validate(etree.ElementTree(root)):
                bad += 1
                for err in list(schema.error_log)[:3]:
                    print(f"{label}:{name}:{err.line}: {err.message[:220]}")
            elif xsd == "dml-chart.xsd":
                # Valid unsigned, but readers that take axis ids as signed ints lose the axes.
                big = {el.get("val") for tag in ("axId", "crossAx") for el in root.iter(CHART + tag)
                       if int(el.get("val")) >= 2 ** 31}
                if big:
                    bad += 1
                    print(f"{label}:{name}: axis ids above 2147483647: {sorted(big)}")
        for err in table_errors(z):
            bad += 1
            print(f"{label}:{err}")
    print(f"{label}: {checked} parts checked, {bad} invalid")
    return bad


def main():
    schema_dir = Path(sys.argv[1])
    cache = {}
    failed = 0
    for package in sys.argv[2:]:
        failed += check_package(Path(package).name, Path(package).read_bytes(), schema_dir, cache)
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
