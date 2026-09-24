#!/usr/bin/env python3
"""Add the touches people usually add by hand in PowerPoint.

- A Fade transition on every slide.
- PowerPoint's Text Shadow (Home › Font › S) on every run in shapes whose name starts with
  "Shadow" (build_deck.js names the title and the headline figures that way).

Usage: python finish_deck.py deck.pptx out.pptx
"""
import sys

from lxml import etree
from pptx import Presentation
from pptx.oxml.ns import qn

# The shadow PowerPoint applies with its Text Shadow button.
SHADOW_XML = (
    '<a:effectLst xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">'
    '<a:outerShdw blurRad="38100" dist="38100" dir="2700000" algn="tl">'
    '<a:srgbClr val="000000"><a:alpha val="43137"/></a:srgbClr></a:outerShdw></a:effectLst>'
)
# a:rPr children that come after effectLst (CT_TextCharacterProperties order).
AFTER_EFFECTS = {"highlight", "uLnTx", "uLn", "uFillTx", "uFill", "latin", "ea", "cs", "sym",
                 "hlinkClick", "hlinkMouseOver", "rtl", "extLst"}


def add_shadow(rpr):
    for old in rpr.findall(qn("a:effectLst")):
        rpr.remove(old)
    effect = etree.fromstring(SHADOW_XML)
    for child in rpr:
        if etree.QName(child).localname in AFTER_EFFECTS:
            child.addprevious(effect)
            return
    rpr.append(effect)


def add_fade(sld):
    for old in sld.findall(qn("p:transition")):
        sld.remove(old)
    trans = etree.SubElement(sld, qn("p:transition"), spd="med")
    etree.SubElement(trans, qn("p:fade"))
    sld.remove(trans)
    # CT_Slide order: cSld, clrMapOvr, transition, timing, extLst
    anchor = sld.find(qn("p:clrMapOvr"))
    if anchor is None:
        anchor = sld.find(qn("p:cSld"))
    anchor.addnext(trans)


def single_ppr(root):
    """pptxgenjs writes an <a:pPr> before every run; the schema allows one, first.

    The first run's block carries the paragraph's real settings (bullet, alignment,
    spacing); the later ones only reset them, so those are dropped.
    """
    fixed = 0
    for para in root.iter(qn("a:p")):
        pprs = para.findall(qn("a:pPr"))
        if not pprs:
            continue
        keep = pprs[0]
        for extra in pprs[1:]:
            para.remove(extra)
            fixed += 1
        if para.index(keep) != 0:
            para.remove(keep)
            para.insert(0, keep)
    return fixed


def main(deck, out):
    prs = Presentation(deck)
    shadowed = 0
    dropped = 0
    for slide in prs.slides:
        dropped += single_ppr(slide._element)
        if slide.has_notes_slide:
            dropped += single_ppr(slide.notes_slide._element)
        add_fade(slide._element)
        for shape in slide.shapes:
            if shape.name.startswith("Shadow") and shape.has_text_frame:
                for para in shape.text_frame.paragraphs:
                    for run in para.runs:
                        add_shadow(run._r.get_or_add_rPr())
                        shadowed += 1
    prs.save(out)
    print(f"fade on {len(prs.slides)} slides, text shadow on {shadowed} runs, "
          f"{dropped} duplicate paragraph blocks removed -> {out}")


if __name__ == "__main__":
    main(*sys.argv[1:3])
