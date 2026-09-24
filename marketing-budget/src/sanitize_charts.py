#!/usr/bin/env python3
"""Make every chart in a .pptx follow the strict Office chart schema, then check it.

pptxgenjs writes chart XML that LibreOffice and some PowerPoint versions forgive but
PowerPoint 2013 rejects with "PowerPoint found a problem with content": a label position
that line charts don't have (outEnd), bar-only elements inside a line series, series
children out of schema order, a line chart without <c:grouping>, and a third axis id that
names no axis. This rewrites those chart parts, then validates each one against
dml-chart.xsd and exits non-zero if any chart is still invalid.

Usage: python sanitize_charts.py deck.pptx out.pptx [--xsd path/to/dml-chart.xsd]
"""
import argparse
import re
import shutil
import sys
import tempfile
import zipfile

from lxml import etree

C = "http://schemas.openxmlformats.org/drawingml/2006/chart"
MC = "http://schemas.openxmlformats.org/markup-compatibility/2006"
Q = f"{{{C}}}"

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
        reorder(group, GROUP_ORDER[kind], drop_unknown=False)
    out = etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)
    return out, notes


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
