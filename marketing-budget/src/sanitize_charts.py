#!/usr/bin/env python3
"""Make every chart in a .pptx follow the strict Office chart schema, then check it.

pptxgenjs writes chart XML that LibreOffice and some PowerPoint versions forgive but
PowerPoint 2013 rejects with "PowerPoint found a problem with content": a label position
that line charts don't have (outEnd), bar-only elements inside a line series, series
children out of schema order, a line chart without <c:grouping>, and a third axis id that
names no axis. This rewrites those chart parts, then validates each one against
dml-chart.xsd and exits non-zero if any chart is still invalid.

It also cleans the small workbook behind each chart (the one "Edit Data" opens in Excel):
pptxgenjs adds a table part with a broken range that no worksheet uses, which is removed, and
leaves the default cell style out of the stylesheet, which is added.

Usage: python sanitize_charts.py deck.pptx out.pptx [--xsd path/to/dml-chart.xsd]
"""
import argparse
import io
import posixpath
import re
import shutil
import sys
import tempfile
import zipfile

from lxml import etree

C = "http://schemas.openxmlformats.org/drawingml/2006/chart"
MC = "http://schemas.openxmlformats.org/markup-compatibility/2006"
Q = f"{{{C}}}"
A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"

# Child order from dml-chart.xsd (ISO/IEC 29500 transitional).
SER_ORDER = {
    "barChart": ["idx", "order", "tx", "spPr", "invertIfNegative", "pictureOptions", "dPt",
                 "dLbls", "trendline", "errBars", "cat", "val", "shape", "extLst"],
    "lineChart": ["idx", "order", "tx", "spPr", "marker", "dPt", "dLbls", "trendline",
                  "errBars", "cat", "val", "smooth", "extLst"],
    "pieChart": ["idx", "order", "tx", "spPr", "explosion", "dPt", "dLbls", "cat", "val", "extLst"],
    "doughnutChart": ["idx", "order", "tx", "spPr", "explosion", "dPt", "dLbls", "cat", "val",
                      "extLst"],
}
GROUP_ORDER = {
    "barChart": ["barDir", "grouping", "varyColors", "ser", "dLbls", "gapWidth", "overlap",
                 "serLines", "axId", "extLst"],
    "lineChart": ["grouping", "varyColors", "ser", "dLbls", "dropLines", "hiLowLines",
                  "upDownBars", "marker", "smooth", "axId", "extLst"],
    "pieChart": ["varyColors", "ser", "dLbls", "firstSliceAng", "extLst"],
    "doughnutChart": ["varyColors", "ser", "dLbls", "firstSliceAng", "holeSize", "extLst"],
}
DLBLS_ORDER = ["dLbl", "delete", "numFmt", "spPr", "txPr", "dLblPos", "showLegendKey", "showVal",
               "showCatName", "showSerName", "showPercent", "showBubbleSize", "separator",
               "showLeaderLines", "leaderLines", "extLst"]
DLBL_ORDER = ["idx", "delete", "layout", "tx", "numFmt", "spPr", "txPr", "dLblPos",
              "showLegendKey", "showVal", "showCatName", "showSerName", "showPercent",
              "showBubbleSize", "separator", "extLst"]
AXIS_LIMIT = {"barChart": 2, "lineChart": 2}


def legal_positions(group):
    kind = etree.QName(group).localname
    if kind == "barChart":
        grouping = group.find(f"{Q}grouping")
        if grouping is not None and grouping.get("val") in ("stacked", "percentStacked"):
            return {"ctr", "inEnd", "inBase"}
        return {"outEnd", "inEnd", "ctr", "inBase"}
    if kind == "lineChart":
        return {"t", "b", "l", "r", "ctr"}
    if kind == "pieChart":
        return {"bestFit", "outEnd", "inEnd", "ctr"}
    return set()  # doughnut and the rest take no label position


def reorder(el, order, drop_unknown):
    """Sort el's children into schema order; drop children the schema doesn't allow here."""
    rank = {name: i for i, name in enumerate(order)}
    kids = list(el)
    keep = []
    for k in kids:
        if not isinstance(k.tag, str):
            continue  # comments / processing instructions
        name = etree.QName(k).localname
        if etree.QName(k).namespace == C and name in rank:
            keep.append(k)
        elif not drop_unknown:
            keep.append(k)
    for k in kids:
        el.remove(k)
    keep.sort(key=lambda k: rank.get(etree.QName(k).localname, len(order)))
    for k in keep:
        el.append(k)
    return len(kids) - len(keep)


def fix_chart(xml: bytes):
    root = etree.fromstring(xml)
    notes = []
    plot = root.find(f".//{Q}plotArea")
    declared = {ax.find(f"{Q}axId").get("val")
                for ax in plot if etree.QName(ax).localname in ("catAx", "valAx", "dateAx", "serAx")
                and ax.find(f"{Q}axId") is not None}
    for group in plot:
        kind = etree.QName(group).localname
        if kind not in GROUP_ORDER:
            continue
        if kind == "lineChart" and group.find(f"{Q}grouping") is None:
            g = etree.SubElement(group, f"{Q}grouping", val="standard")
            group.remove(g)
            group.insert(0, g)
            notes.append("added <c:grouping> to lineChart")
        if kind in AXIS_LIMIT:
            ids = group.findall(f"{Q}axId")
            live = [a for a in ids if a.get("val") in declared][:AXIS_LIMIT[kind]]
            for a in ids:
                if a not in live:
                    group.remove(a)
                    notes.append(f"dropped axId {a.get('val')} from {kind}")
        legal = legal_positions(group)
        for pos in list(group.iter(f"{Q}dLblPos")):
            if pos.get("val") not in legal:
                pos.getparent().remove(pos)
                notes.append(f'removed dLblPos="{pos.get("val")}" from {kind}')
        for ser in group.findall(f"{Q}ser"):
            dropped = reorder(ser, SER_ORDER[kind], drop_unknown=True)
            if dropped:
                notes.append(f"dropped {dropped} element(s) a {kind} series may not hold")
        for dlbls in group.iter(f"{Q}dLbls"):
            reorder(dlbls, DLBLS_ORDER, drop_unknown=False)
        for dlbl in group.iter(f"{Q}dLbl"):
            reorder(dlbl, DLBL_ORDER, drop_unknown=False)
        # Keep short labels such as "36.0%" on one line (renderers may otherwise wrap them).
        for body in group.iter(f"{{{A_NS}}}bodyPr"):
            if etree.QName(body.getparent().getparent()).localname in ("dLbls", "dLbl"):
                body.set("wrap", "none")
        reorder(group, GROUP_ORDER[kind], drop_unknown=False)
    out = etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)
    return out, notes


S_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
S = f"{{{S_NS}}}"
R_ID = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"


STYLE_ORDER = ["numFmts", "fonts", "fills", "borders", "cellStyleXfs", "cellXfs", "cellStyles",
               "dxfs", "tableStyles", "colors", "extLst"]


def complete_stylesheet(xml: bytes):
    """Give a stylesheet the default cell style Excel writes in every workbook.

    pptxgenjs leaves out cellStyleXfs, cellXfs and cellStyles (so the cells point at a style
    that doesn't exist) and redefines built-in number format 0, "General".
    """
    root = etree.fromstring(xml)
    notes = []
    fmts = root.find(f"{S}numFmts")
    if fmts is not None:
        for fmt in fmts.findall(f"{S}numFmt"):
            if int(fmt.get("numFmtId")) < 164:   # ids below 164 are Excel's built-in formats
                fmts.remove(fmt)
                notes.append(f"removed redefinition of built-in number format {fmt.get('numFmtId')}")
        if len(fmts) == 0:
            root.remove(fmts)
        else:
            fmts.set("count", str(len(fmts)))
    defaults = {
        "cellStyleXfs": '<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>',
        "cellXfs": '<cellXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/></cellXfs>',
        "cellStyles": '<cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles>',
    }
    for name, markup in defaults.items():
        if root.find(f"{S}{name}") is None:
            root.append(etree.fromstring(markup.replace(">", f' xmlns="{S_NS}">', 1)))
            notes.append(f"added default {name}")
    reorder_children = sorted(root, key=lambda el: STYLE_ORDER.index(etree.QName(el).localname)
                              if etree.QName(el).localname in STYLE_ORDER else len(STYLE_ORDER))
    for el in reorder_children:
        root.append(el)
    return etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True), notes


def fix_chart_workbook(data: bytes):
    """Clean the workbook behind a chart (the one "Edit Data" opens in Excel).

    - pptxgenjs writes xl/tables/table1.xml with a broken range (ref="A1:B7'") but never
      links it from the worksheet (no <tableParts>); the unused table is removed.
    - The stylesheet gets the default cell style Excel always writes (complete_stylesheet).
    The chart reads its data from the cells, which stay as they are.
    """
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        names = zf.namelist()
        infos = zf.infolist()
        parts = {name: zf.read(name) for name in names}
    notes = []
    if "xl/styles.xml" in parts:
        parts["xl/styles.xml"], notes = complete_stylesheet(parts["xl/styles.xml"])
    used = set()
    for sheet_name in [n for n in names if re.fullmatch(r"xl/worksheets/[^/]+\.xml", n)]:
        sheet = etree.fromstring(parts[sheet_name])
        ids = {tp.get(R_ID) for tp in sheet.iter(f"{S}tablePart")}
        folder, base = posixpath.split(sheet_name)
        rels_name = f"{folder}/_rels/{base}.rels"
        if rels_name not in parts:
            continue
        rels = etree.fromstring(parts[rels_name])
        for rel in list(rels):
            target = posixpath.normpath(posixpath.join(folder, rel.get("Target", "")))
            if rel.get("Type", "").endswith("/table"):
                if rel.get("Id") in ids:
                    used.add(target)
                else:
                    rels.remove(rel)
        parts[rels_name] = etree.tostring(rels, xml_declaration=True, encoding="UTF-8", standalone=True)
        if len(rels) == 0:
            del parts[rels_name]
    dropped = [n for n in names if re.fullmatch(r"xl/tables/[^/]+\.xml", n) and n not in used]
    for name in dropped:
        del parts[name]
    if not dropped and not notes:
        return data, []
    if dropped:
        ct = etree.fromstring(parts["[Content_Types].xml"])
        for override in list(ct):
            if override.get("PartName", "").lstrip("/") in dropped:
                ct.remove(override)
        parts["[Content_Types].xml"] = etree.tostring(ct, xml_declaration=True, encoding="UTF-8", standalone=True)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as out:
        for info in infos:
            if info.filename in parts:
                out.writestr(info, parts[info.filename])
    return buf.getvalue(), notes + [f"removed unused table part {n}" for n in dropped]


def schema_errors(xml: bytes, schema):
    doc = etree.fromstring(xml)
    # Office extensions sit in mc:AlternateContent, which the base schema doesn't describe.
    for alt in doc.xpath("//mc:AlternateContent", namespaces={"mc": MC}):
        alt.getparent().remove(alt)
    if schema.validate(etree.ElementTree(doc)):
        return []
    return [f"line {e.line}: {e.message}" for e in schema.error_log]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("deck")
    ap.add_argument("output")
    ap.add_argument("--xsd", help="dml-chart.xsd; when given, every chart must validate against it")
    args = ap.parse_args()
    schema = etree.XMLSchema(etree.parse(args.xsd)) if args.xsd else None

    failures = 0
    with zipfile.ZipFile(args.deck) as src, tempfile.NamedTemporaryFile(suffix=".pptx", delete=False) as tmp:
        out_path = tmp.name
        with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as dst:
            for info in src.infolist():
                data = src.read(info.filename)
                if re.fullmatch(r"ppt/embeddings/[^/]+\.xlsx", info.filename):
                    data, notes = fix_chart_workbook(data)
                    for n in sorted(set(notes)):
                        print(f"{info.filename}: {n}")
                if re.fullmatch(r"ppt/charts/chart\d+\.xml", info.filename):
                    data, notes = fix_chart(data)
                    for n in sorted(set(notes)):
                        print(f"{info.filename}: {n}")
                    if schema is not None:
                        errors = schema_errors(data, schema)
                        failures += bool(errors)
                        for e in errors[:5]:
                            print(f"{info.filename}: SCHEMA {e}")
                dst.writestr(info, data)
    shutil.move(out_path, args.output)
    if failures:
        sys.exit(f"{failures} chart part(s) still fail the chart schema")
    print(f"charts ok -> {args.output}")


if __name__ == "__main__":
    main()
