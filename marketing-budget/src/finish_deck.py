#!/usr/bin/env python3
"""Final pass over the deck: clean paragraphs, add transitions and automatic animations.

- Keeps one paragraph-settings block (<a:pPr>) per paragraph. pptxgenjs writes one before
  every text run, which the schema forbids and PowerPoint 2013 may reject.
- Adds a Push transition to every slide.
- Adds entrance animations from the plan build_deck.js wrote (deck.anim.json). Objects that
  share a step appear together. Step 1 starts by itself when the slide appears, and each
  later step starts when the one before it ends ("After Previous"), so nothing needs a
  click. Moving to the next slide still takes a click.

Usage: python finish_deck.py deck.pptx plan.json out.pptx
"""
import json
import sys
from collections import defaultdict

from lxml import etree
from pptx import Presentation
from pptx.oxml.ns import nsdecls, qn

EFFECT_MS = 500
# effect -> (presetID, presetSubtype, filter), as PowerPoint writes them
EFFECTS = {
    "fade": (10, 0, "fade"),
    "wipe-left": (22, 8, "wipe(right)"),   # Wipe, From Left
    "wipe-up": (22, 4, "wipe(up)"),        # Wipe, From Bottom
}
CHART_URI = "http://schemas.openxmlformats.org/drawingml/2006/chart"


def single_ppr(root):
    """Keep each paragraph's first <a:pPr> (it holds the real settings) and drop the rest."""
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


def effect_xml(ctn, spid, effect, node_type, has_build):
    preset, subtype, flt = EFFECTS[effect]
    grp = ' grpId="0"' if has_build else ""   # grpId ties the effect to its <p:bldLst> entry
    return (
        f'<p:par><p:cTn id="{ctn}" presetID="{preset}" presetClass="entr" presetSubtype="{subtype}" '
        f'fill="hold"{grp} nodeType="{node_type}">'
        f'<p:stCondLst><p:cond delay="0"/></p:stCondLst><p:childTnLst>'
        f'<p:set><p:cBhvr><p:cTn id="{ctn + 1}" dur="1" fill="hold"><p:stCondLst><p:cond delay="0"/></p:stCondLst></p:cTn>'
        f'<p:tgtEl><p:spTgt spid="{spid}"/></p:tgtEl>'
        f'<p:attrNameLst><p:attrName>style.visibility</p:attrName></p:attrNameLst></p:cBhvr>'
        f'<p:to><p:strVal val="visible"/></p:to></p:set>'
        f'<p:animEffect transition="in" filter="{flt}"><p:cBhvr><p:cTn id="{ctn + 2}" dur="{EFFECT_MS}"/>'
        f'<p:tgtEl><p:spTgt spid="{spid}"/></p:tgtEl></p:cBhvr></p:animEffect>'
        f'</p:childTnLst></p:cTn></p:par>'
    )


def build_entry(shape):
    """The <p:bldLst> entry PowerPoint writes for an animated shape, if any."""
    el = shape._element
    tag = etree.QName(el).localname
    if tag == "sp":
        return f'<p:bldP spid="{shape.shape_id}" grpId="0" animBg="1"/>'
    data = el.find(f".//{qn('a:graphicData')}") if tag == "graphicFrame" else None
    if data is not None and data.get("uri") == CHART_URI:
        return f'<p:bldGraphic spid="{shape.shape_id}" grpId="0"><p:bldAsOne/></p:bldGraphic>'
    return ""


def timing(slide, plan):
    by_name = {shape.name: shape for shape in slide.shapes}
    missing = [e["name"] for e in plan if e["name"] not in by_name]
    if missing:
        sys.exit(f"animation plan names shapes this slide doesn't have: {missing}")
    steps = defaultdict(list)
    for entry in plan:
        steps[entry["step"]].append(entry)

    ctn = 4
    groups, builds = [], []
    for i, step in enumerate(sorted(steps)):
        group_ctn, ctn = ctn, ctn + 1
        effects = []
        for j, entry in enumerate(steps[step]):
            shape = by_name[entry["name"]]
            build = build_entry(shape)
            effects.append(effect_xml(ctn, shape.shape_id, entry["effect"],
                                      "afterEffect" if j == 0 else "withEffect", bool(build)))
            builds.append(build)
            ctn += 3
        groups.append(
            f'<p:par><p:cTn id="{group_ctn}" fill="hold"><p:stCondLst><p:cond delay="{i * EFFECT_MS}"/></p:stCondLst>'
            f'<p:childTnLst>{"".join(effects)}</p:childTnLst></p:cTn></p:par>'
        )
    bld = "".join(builds)
    xml = (
        f'<p:timing {nsdecls("p")}><p:tnLst><p:par>'
        f'<p:cTn id="1" dur="indefinite" restart="never" nodeType="tmRoot"><p:childTnLst>'
        f'<p:seq concurrent="1" nextAc="seek"><p:cTn id="2" dur="indefinite" nodeType="mainSeq"><p:childTnLst>'
        # One "click group" that starts on its own when the slide begins.
        f'<p:par><p:cTn id="3" fill="hold"><p:stCondLst><p:cond delay="indefinite"/>'
        f'<p:cond evt="onBegin" delay="0"><p:tn val="2"/></p:cond></p:stCondLst>'
        f'<p:childTnLst>{"".join(groups)}</p:childTnLst></p:cTn></p:par>'
        f'</p:childTnLst></p:cTn>'
        f'<p:prevCondLst><p:cond evt="onPrev" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:prevCondLst>'
        f'<p:nextCondLst><p:cond evt="onNext" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:nextCondLst>'
        f'</p:seq></p:childTnLst></p:cTn></p:par></p:tnLst>'
        f'{f"<p:bldLst>{bld}</p:bldLst>" if bld else ""}</p:timing>'
    )
    return etree.fromstring(xml), len(steps), len(plan)


def set_transition_and_timing(sld, timing_el):
    for tag in ("p:transition", "p:timing"):
        for old in sld.findall(qn(tag)):
            sld.remove(old)
    trans = etree.fromstring(f'<p:transition {nsdecls("p")} spd="med"><p:push dir="u"/></p:transition>')
    # CT_Slide order: cSld, clrMapOvr, transition, timing, extLst
    anchor = sld.find(qn("p:clrMapOvr"))
    if anchor is None:
        anchor = sld.find(qn("p:cSld"))
    anchor.addnext(trans)
    if timing_el is not None:
        trans.addnext(timing_el)


def main(deck, plan_path, out):
    prs = Presentation(deck)
    with open(plan_path) as fh:
        plan = json.load(fh)
    dropped = animated = 0
    for number, slide in enumerate(prs.slides, start=1):
        dropped += single_ppr(slide._element)
        if slide.has_notes_slide:
            dropped += single_ppr(slide.notes_slide._element)
        entries = plan.get(str(number), [])
        timing_el = None
        if entries:
            timing_el, steps, shapes = timing(slide, entries)
            animated += shapes
        set_transition_and_timing(slide._element, timing_el)
    prs.save(out)
    print(f"push transition on {len(prs.slides)} slides, {animated} shapes animated, "
          f"{dropped} duplicate paragraph blocks removed -> {out}")


if __name__ == "__main__":
    main(*sys.argv[1:4])
