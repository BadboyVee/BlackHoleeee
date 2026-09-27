#!/usr/bin/env python3
"""Office 2013's default look, shared by the workbook and the deck.

- THEME_XML is the "Office Theme" that Excel 2013 and PowerPoint 2013 start every new file
  with: Calibri Light headings, Calibri body text and the 2013 colour palette (blue 5B9BD5,
  orange ED7D31, grey A5A5A5, gold FFC000, blue 4472C4, green 70AD47).
- make_template() turns python-pptx's built-in template (the 11 standard PowerPoint layouts,
  but in the older 4:3 Office 2007 design) into PowerPoint 2013's widescreen Office Theme:
  13.33 x 7.5 in slides, left-aligned 44pt titles, 28pt body text with 90% line spacing,
  and the 2013 placeholder positions on the master and every layout.

Usage: python office2013.py template.pptx
"""
import re
import sys
import zipfile
from pathlib import Path

from lxml import etree

FMT_SCHEME = (
    '<a:fmtScheme name="Office"><a:fillStyleLst><a:solidFill><a:schemeClr val="phClr"/></a:solidFill>'
    '<a:gradFill rotWithShape="1"><a:gsLst><a:gs pos="0"><a:schemeClr val="phClr"><a:lumMod val="110000"/>'
    '<a:satMod val="105000"/><a:tint val="67000"/></a:schemeClr></a:gs><a:gs pos="50000"><a:schemeClr val="phClr">'
    '<a:lumMod val="105000"/><a:satMod val="103000"/><a:tint val="73000"/></a:schemeClr></a:gs><a:gs pos="100000">'
    '<a:schemeClr val="phClr"><a:lumMod val="105000"/><a:satMod val="109000"/><a:tint val="81000"/>'
    '</a:schemeClr></a:gs></a:gsLst><a:lin ang="5400000" scaled="0"/></a:gradFill><a:gradFill rotWithShape="1">'
    '<a:gsLst><a:gs pos="0"><a:schemeClr val="phClr"><a:satMod val="103000"/><a:lumMod val="102000"/>'
    '<a:tint val="94000"/></a:schemeClr></a:gs><a:gs pos="50000"><a:schemeClr val="phClr"><a:satMod val="110000"/>'
    '<a:lumMod val="100000"/><a:shade val="100000"/></a:schemeClr></a:gs><a:gs pos="100000"><a:schemeClr val="phClr">'
    '<a:lumMod val="99000"/><a:satMod val="120000"/><a:shade val="78000"/></a:schemeClr></a:gs></a:gsLst>'
    '<a:lin ang="5400000" scaled="0"/></a:gradFill></a:fillStyleLst><a:lnStyleLst><a:ln w="6350" cap="flat" cmpd="sng" algn="ctr">'
    '<a:solidFill><a:schemeClr val="phClr"/></a:solidFill><a:prstDash val="solid"/><a:miter lim="800000"/>'
    '</a:ln><a:ln w="12700" cap="flat" cmpd="sng" algn="ctr"><a:solidFill><a:schemeClr val="phClr"/>'
    '</a:solidFill><a:prstDash val="solid"/><a:miter lim="800000"/></a:ln><a:ln w="19050" cap="flat" cmpd="sng" algn="ctr">'
    '<a:solidFill><a:schemeClr val="phClr"/></a:solidFill><a:prstDash val="solid"/><a:miter lim="800000"/>'
    '</a:ln></a:lnStyleLst><a:effectStyleLst><a:effectStyle><a:effectLst/></a:effectStyle><a:effectStyle>'
    '<a:effectLst/></a:effectStyle><a:effectStyle><a:effectLst><a:outerShdw blurRad="57150" dist="19050" dir="5400000" algn="ctr" rotWithShape="0">'
    '<a:srgbClr val="000000"><a:alpha val="63000"/></a:srgbClr></a:outerShdw></a:effectLst></a:effectStyle>'
    '</a:effectStyleLst><a:bgFillStyleLst><a:solidFill><a:schemeClr val="phClr"/></a:solidFill><a:solidFill>'
    '<a:schemeClr val="phClr"><a:tint val="95000"/><a:satMod val="170000"/></a:schemeClr></a:solidFill>'
    '<a:gradFill rotWithShape="1"><a:gsLst><a:gs pos="0"><a:schemeClr val="phClr"><a:tint val="93000"/>'
    '<a:satMod val="150000"/><a:shade val="98000"/><a:lumMod val="102000"/></a:schemeClr></a:gs>'
    '<a:gs pos="50000"><a:schemeClr val="phClr"><a:tint val="98000"/><a:satMod val="130000"/><a:shade val="90000"/>'
    '<a:lumMod val="103000"/></a:schemeClr></a:gs><a:gs pos="100000"><a:schemeClr val="phClr"><a:shade val="63000"/>'
    '<a:satMod val="120000"/></a:schemeClr></a:gs></a:gsLst><a:lin ang="5400000" scaled="0"/></a:gradFill>'
    '</a:bgFillStyleLst></a:fmtScheme>'
)

THEME_XML = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<a:theme xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" name="Office Theme">'
    '<a:themeElements><a:clrScheme name="Office">'
    '<a:dk1><a:sysClr val="windowText" lastClr="000000"/></a:dk1>'
    '<a:lt1><a:sysClr val="window" lastClr="FFFFFF"/></a:lt1>'
    '<a:dk2><a:srgbClr val="44546A"/></a:dk2><a:lt2><a:srgbClr val="E7E6E6"/></a:lt2>'
    '<a:accent1><a:srgbClr val="5B9BD5"/></a:accent1><a:accent2><a:srgbClr val="ED7D31"/></a:accent2>'
    '<a:accent3><a:srgbClr val="A5A5A5"/></a:accent3><a:accent4><a:srgbClr val="FFC000"/></a:accent4>'
    '<a:accent5><a:srgbClr val="4472C4"/></a:accent5><a:accent6><a:srgbClr val="70AD47"/></a:accent6>'
    '<a:hlink><a:srgbClr val="0563C1"/></a:hlink><a:folHlink><a:srgbClr val="954F72"/></a:folHlink>'
    '</a:clrScheme>'
    '<a:fontScheme name="Office">'
    '<a:majorFont><a:latin typeface="Calibri Light" panose="020F0302020204030204"/><a:ea typeface=""/><a:cs typeface=""/></a:majorFont>'
    '<a:minorFont><a:latin typeface="Calibri" panose="020F0502020204030204"/><a:ea typeface=""/><a:cs typeface=""/></a:minorFont>'
    '</a:fontScheme>'
    + FMT_SCHEME +
    '</a:themeElements><a:objectDefaults/><a:extraClrSchemeLst/>'
    '<a:extLst><a:ext uri="{05A4C25C-085E-4340-85A3-A5531E510DB2}">'
    '<thm15:themeFamily xmlns:thm15="http://schemas.microsoft.com/office/thememl/2012/main" name="Office Theme" '
    'id="{62F939B6-93AF-4DB8-9C6B-D6C7DFDC589F}" vid="{4A3C46E8-61CC-4603-A589-7422A47A8E4A}"/>'
    '</a:ext></a:extLst></a:theme>'
)

A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
P_NS = "http://schemas.openxmlformats.org/presentationml/2006/main"
NS = {"a": A_NS, "p": P_NS}
WIDE = (12192000, 6858000)          # 13.33 x 7.5 in, PowerPoint 2013's default slide size
OLD_WIDTH = 9144000                 # the 4:3 template's width

# Placeholder positions (EMU) in PowerPoint 2013's widescreen Office Theme.
MASTER_POS = {
    "title": (838200, 365125, 10515600, 1325563),
    "body": (838200, 1825625, 10515600, 4351338),
    "dt": (838200, 6356350, 2743200, 365125),
    "ftr": (4038600, 6356350, 4114800, 365125),
    "sldNum": (8610600, 6356350, 2743200, 365125),
}
CAPTION_TITLE = (839788, 457200, 3932237, 1600200)
LAYOUT_POS = {
    "Title Slide": {"ctrTitle": (1524000, 1122363, 9144000, 2387600),
                    "subTitle": (1524000, 3602038, 9144000, 1655762)},
    "Section Header": {"title": (831850, 1709738, 10515600, 2852737),
                       ("body", "1"): (831850, 4589463, 10515600, 1500187)},
    "Two Content": {("obj", "1"): (838200, 1825625, 5181600, 4351338),
                    ("obj", "2"): (6172200, 1825625, 5181600, 4351338)},
    "Comparison": {"title": (839788, 365125, 10515600, 1325563),
                   ("body", "1"): (839788, 1681163, 5157787, 823912),
                   ("obj", "2"): (839788, 2505075, 5157787, 3684588),
                   ("body", "3"): (6172200, 1681163, 5183188, 823912),
                   ("obj", "4"): (6172200, 2505075, 5183188, 3684588)},
    "Content with Caption": {"title": CAPTION_TITLE,
                             ("obj", "1"): (5183188, 987425, 6172200, 4873625),
                             ("body", "2"): (839788, 2057400, 3932237, 3811588)},
    "Picture with Caption": {"title": CAPTION_TITLE,
                             ("pic", "1"): (5183188, 987425, 6172200, 4873625),
                             ("body", "2"): (839788, 2057400, 3932237, 3811588)},
    "Vertical Title and Text": {"title": (8724900, 365125, 2628900, 5811838),
                                ("body", "1"): (838200, 365125, 7734300, 5811838)},
}
FONT_REFS = ('<a:latin typeface="+{0}-lt"/><a:ea typeface="+{0}-ea"/><a:cs typeface="+{0}-cs"/>')
PPR_ATTRS = 'defTabSz="914400" rtl="0" eaLnBrk="1" latinLnBrk="0" hangingPunct="1"'


def title_style():
    return (f'<p:titleStyle xmlns:p="{P_NS}" xmlns:a="{A_NS}"><a:lvl1pPr algn="l" {PPR_ATTRS}>'
            '<a:lnSpc><a:spcPct val="90000"/></a:lnSpc><a:spcBef><a:spcPct val="0"/></a:spcBef><a:buNone/>'
            '<a:defRPr sz="4400" kern="1200"><a:solidFill><a:schemeClr val="tx1"/></a:solidFill>'
            f'{FONT_REFS.format("mj")}</a:defRPr></a:lvl1pPr></p:titleStyle>')


def body_style():
    sizes = [2800, 2400, 2000, 1800, 1800, 1800, 1800, 1800, 1800]
    levels = "".join(
        f'<a:lvl{i + 1}pPr marL="{228600 + i * 457200}" indent="-228600" algn="l" {PPR_ATTRS}>'
        f'<a:lnSpc><a:spcPct val="90000"/></a:lnSpc><a:spcBef><a:spcPts val="{1000 if i == 0 else 500}"/></a:spcBef>'
        '<a:buFont typeface="Arial" panose="020B0604020202020204" pitchFamily="34" charset="0"/><a:buChar char="•"/>'
        f'<a:defRPr sz="{size}" kern="1200"><a:solidFill><a:schemeClr val="tx1"/></a:solidFill>'
        f'{FONT_REFS.format("mn")}</a:defRPr></a:lvl{i + 1}pPr>'
        for i, size in enumerate(sizes))
    return f'<p:bodyStyle xmlns:p="{P_NS}" xmlns:a="{A_NS}">{levels}</p:bodyStyle>'


def lst_style(sizes, *, centred=False, bullets=False, bold=False, grey=False):
    """A placeholder's own list style: one entry per level, as PowerPoint 2013 writes them."""
    out = []
    for i in range(9):
        size = sizes[min(i, len(sizes) - 1)]
        attrs = f'marL="{i * 457200}" indent="0"' if not bullets else ""
        attrs += ' algn="ctr"' if centred else ""
        colour = ('<a:solidFill><a:schemeClr val="tx1"><a:tint val="75000"/></a:schemeClr></a:solidFill>'
                  if grey else "")
        weight = ' b="1"' if bold else ""
        out.append(f'<a:lvl{i + 1}pPr {attrs}>{"" if bullets else "<a:buNone/>"}'
                   f'<a:defRPr sz="{size}"{weight}>{colour}</a:defRPr></a:lvl{i + 1}pPr>')
    return f'<a:lstStyle xmlns:a="{A_NS}">{"".join(out)}</a:lstStyle>'


def set_xfrm(sp, box):
    sppr = sp.find("p:spPr", NS)
    for old in sppr.findall("a:xfrm", NS):
        sppr.remove(old)
    if box is None:
        return
    x, y, cx, cy = box
    xfrm = etree.SubElement(sppr, f"{{{A_NS}}}xfrm")
    etree.SubElement(xfrm, f"{{{A_NS}}}off", x=str(x), y=str(y))
    etree.SubElement(xfrm, f"{{{A_NS}}}ext", cx=str(cx), cy=str(cy))
    sppr.remove(xfrm)
    sppr.insert(0, xfrm)


def placeholder_key(sp):
    ph = sp.find("p:nvSpPr/p:nvPr/p:ph", NS)
    if ph is None:
        return None, None
    kind = ph.get("type", "obj")
    return kind, (kind if kind in ("title", "ctrTitle", "subTitle", "dt", "ftr", "sldNum")
                  else (kind, ph.get("idx", "0")))


def text_body(sp, *, anchor=None, lst=None):
    body = sp.find("p:txBody", NS)
    if anchor is not None:
        body.find("a:bodyPr", NS).set("anchor", anchor)
    if lst is not None:
        old = body.find("a:lstStyle", NS)
        new = etree.fromstring(lst)
        old.addprevious(new)
        body.remove(old)


def fix_layout(root):
    name = root.find("p:cSld", NS).get("name")
    positions = LAYOUT_POS.get(name, {})
    for sp in root.iter(f"{{{P_NS}}}sp"):
        kind, key = placeholder_key(sp)
        if kind is None:
            continue
        if key in positions:
            set_xfrm(sp, positions[key])
        elif kind in ("dt", "ftr", "sldNum") or not positions:
            set_xfrm(sp, None)           # inherit the master's position
        else:
            xfrm = sp.find("p:spPr/a:xfrm", NS)
            if xfrm is not None:         # a layout we don't use: stretch it to the wider slide
                off, ext = xfrm.find("a:off", NS), xfrm.find("a:ext", NS)
                off.set("x", str(round(int(off.get("x")) * WIDE[0] / OLD_WIDTH)))
                ext.set("cx", str(round(int(ext.get("cx")) * WIDE[0] / OLD_WIDTH)))
        if name == "Title Slide" and kind == "ctrTitle":
            text_body(sp, anchor="b", lst=f'<a:lstStyle xmlns:a="{A_NS}"><a:lvl1pPr algn="ctr"><a:defRPr sz="6000"/></a:lvl1pPr></a:lstStyle>')
        elif name == "Title Slide" and kind == "subTitle":
            text_body(sp, lst=lst_style([2400, 2000, 1800, 1600], centred=True))
        elif name == "Section Header" and kind == "title":
            text_body(sp, anchor="b", lst=f'<a:lstStyle xmlns:a="{A_NS}"><a:lvl1pPr><a:defRPr sz="6000"/></a:lvl1pPr></a:lstStyle>')
        elif name == "Section Header" and kind == "body":
            text_body(sp, lst=lst_style([2400, 2000, 1800, 1600], grey=True))
        elif name == "Comparison" and kind == "body":
            text_body(sp, anchor="b", lst=lst_style([2400, 2000, 1800, 1600], bold=True))
        elif name in ("Content with Caption", "Picture with Caption") and kind == "title":
            text_body(sp, anchor="b", lst=f'<a:lstStyle xmlns:a="{A_NS}"><a:lvl1pPr><a:defRPr sz="3200"/></a:lvl1pPr></a:lstStyle>')
        elif name in ("Content with Caption", "Picture with Caption") and kind == "body":
            text_body(sp, lst=lst_style([1600, 1400, 1200, 1000]))
        elif name in ("Two Content", "Comparison") and kind == "obj":
            text_body(sp, lst=f'<a:lstStyle xmlns:a="{A_NS}"/>')


def fix_master(root):
    for sp in root.iter(f"{{{P_NS}}}sp"):
        kind, _ = placeholder_key(sp)
        if kind in MASTER_POS:
            set_xfrm(sp, MASTER_POS[kind])
    styles = root.find("p:txStyles", NS)
    for tag, markup in (("titleStyle", title_style()), ("bodyStyle", body_style())):
        old = styles.find(f"p:{tag}", NS)
        old.addprevious(etree.fromstring(markup))
        styles.remove(old)


def tostring(root):
    return etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)


def make_template(out):
    import pptx
    src = Path(pptx.__file__).parent / "templates" / "default.pptx"
    dropped = ("docProps/thumbnail.jpeg", "ppt/printerSettings/printerSettings1.bin")
    with zipfile.ZipFile(src) as zin, zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zout:
        for info in zin.infolist():
            name = info.filename
            if name in dropped:
                continue
            data = zin.read(name)
            if name == "ppt/theme/theme1.xml":
                data = THEME_XML.encode()
            elif name == "ppt/presentation.xml":
                root = etree.fromstring(data)
                size = root.find("p:sldSz", NS)
                size.attrib.clear()
                size.set("cx", str(WIDE[0]))
                size.set("cy", str(WIDE[1]))
                data = tostring(root).replace(b'defTabSz="457200"', b'defTabSz="914400"')
            elif name == "ppt/slideMasters/slideMaster1.xml":
                root = etree.fromstring(data)
                fix_master(root)
                data = tostring(root).replace(b'defTabSz="457200"', b'defTabSz="914400"')
            elif re.fullmatch(r"ppt/slideLayouts/slideLayout\d+\.xml", name):
                root = etree.fromstring(data)
                fix_layout(root)
                data = tostring(root)
            elif name in ("_rels/.rels", "ppt/_rels/presentation.xml.rels"):
                root = etree.fromstring(data)
                for rel in list(root):
                    if rel.get("Target", "").lstrip("/") in dropped or rel.get("Target", "").endswith(
                            ("thumbnail.jpeg", "printerSettings1.bin")):
                        root.remove(rel)
                data = tostring(root)
            elif name == "[Content_Types].xml":
                data = re.sub(rb'<Default Extension="(jpeg|bin)"[^>]*/>', b"", data)
            elif name == "docProps/app.xml":
                data = (b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                        b'<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties" '
                        b'xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">'
                        b'<TotalTime>0</TotalTime><Words>0</Words><Application>Microsoft Office PowerPoint</Application>'
                        b'<PresentationFormat>Widescreen</PresentationFormat><Paragraphs>0</Paragraphs>'
                        b'<Slides>0</Slides><Notes>0</Notes><HiddenSlides>0</HiddenSlides><MMClips>0</MMClips>'
                        b'<ScaleCrop>false</ScaleCrop><LinksUpToDate>false</LinksUpToDate><SharedDoc>false</SharedDoc>'
                        b'<HyperlinksChanged>false</HyperlinksChanged></Properties>')
            zout.writestr(info, data)


if __name__ == "__main__":
    make_template(sys.argv[1])
    print(f"wrote {sys.argv[1]}")
