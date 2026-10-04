#!/usr/bin/env python3
"""Build the relative-interest pie chart deck in one of three colour palettes, made the way it
would be in PowerPoint 2013.

Usage: python build_deck.py deck_data.json template.pptx wood.jpg STYLE out.pptx
  STYLE is one of:
  marketing  the palette of the Marketing Department Budget deck: Calibri, dark-blue (1F3864)
             titles over a dark-blue line, a thin light-blue frame round each slide, light-blue
             (DEEBF7) boxes, and the pie chart in black and greys.
  pz         the palette of the PZ Nigeria Limited deck (PowerPoint's wood design): a wood
             background (make_wood.py), white cards with a thin orange border, Cambria titles,
             orange-brown (C55A11) lines and table headers, and the pie chart in browns and
             oranges.
  mixed      both together: the wood title and closing slides of the PZ deck, and white
             content slides with dark-blue titles, orange lines, peach and light-blue boxes and
             a navy, orange and grey pie chart.

All three have the same five simple slides: 1. title, 2. the scores, 3. the pie chart,
4. observations, 5. thank you. Text is in Office's own fonts, Calibri, with Cambria titles in the
pz and mixed styles; check_fit.py confirms every text box fits its text. deck_data.json comes from export_deck_data.py, which reads the
scores, ranks and shares out of the finished Relative_Interest_Pie_Chart.xlsx, so the slides
match the workbook. The deck's theme carries the style's colours and fonts, so PowerPoint's
colour palette (Shape Fill, Font Color) offers them. build.sh then gives each slide its
transition (finish_deck.py).
"""
import io
import json
import re
import sys
import zipfile
from datetime import datetime, timezone

from lxml import etree
from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE, XL_LABEL_POSITION
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Emu, Inches, Pt

from office2013 import THEME_XML

A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
P_NS = "http://schemas.openxmlformats.org/presentationml/2006/main"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
TABLE_GRID = "{5940675A-B579-460E-94D1-54222C63F5DA}"   # PowerPoint's "No Style, Table Grid"

STYLES = {
    "marketing": {
        "palette": None,                                 # the Office 2013 colours, as that deck
        "head_font": "Calibri", "body_font": "Calibri",
        "title_size": 36, "card_caps": False, "card_shadow": False,
        "title": "1F3864", "text": "000000", "muted": "404040", "names": "000000",
        "rule": "1F3864", "frame": "8FAADC", "wood": (), "cards": False,
        "head_fill": "1F3864", "band": "DEEBF7", "grid": "BFBFBF", "box": "DEEBF7",
        "pie": ["262626", "A6A6A6", "595959", "D9D9D9", "7F7F7F"], "key_line": "7F7F7F",
    },
    "pz": {
        "palette": ("PZ Wood", {"dk2": "4E3B30", "lt2": "F2E6D9", "accent1": "C55A11", "accent2": "6B3A1E",
                                "accent3": "BF8F00", "accent4": "A0662F", "accent5": "F4B183",
                                "accent6": "7F7F7F", "hlink": "C55A11", "folHlink": "6B3A1E"}),
        "head_font": "Cambria", "body_font": "Calibri",
        "title_size": 36, "card_caps": True, "card_shadow": True,
        "title": "3F3F3F", "text": "3B2A20", "muted": "5E4B3F", "names": "6B3A1E",
        "rule": "C55A11", "frame": None, "wood": ("title", "content", "end"), "cards": True,
        "head_fill": "C55A11", "band": "FBE5D6", "grid": "D9C3A5", "box": "FBE5D6",
        "pie": ["6B3A1E", "F4B183", "C55A11", "E2C290", "A0662F"], "key_line": "8C6E5A",
    },
    "mixed": {
        "palette": ("Navy and Wood", {"dk2": "1F3864", "lt2": "DEEBF7", "accent1": "1F3864", "accent2": "C55A11",
                                      "accent3": "9DC3E6", "accent4": "F4B183", "accent5": "7F7F7F",
                                      "accent6": "6B3A1E", "hlink": "2E75B6", "folHlink": "7F7F7F"}),
        "head_font": "Cambria", "body_font": "Calibri",
        "title_size": 36, "card_caps": True, "card_shadow": False,
        "title": "1F3864", "text": "000000", "muted": "404040", "names": "1F3864",
        "rule": "C55A11", "frame": "F4B183", "wood": ("title", "end"), "cards": False,
        "head_fill": "1F3864", "band": "FBE5D6", "grid": "BFBFBF", "box": "DEEBF7",
        "pie": ["1F3864", "F4B183", "C55A11", "9DC3E6", "7F7F7F"], "key_line": "7F7F7F",
    },
}

data_path, template_path, wood_path, style_name, out_path = sys.argv[1:6]
S = STYLES[style_name]
data = json.load(open(data_path))
P = data["programmes"]                                  # pie order: largest share first
prs = Presentation(template_path)
LAYOUT = {layout.name: layout for layout in prs.slide_layouts}
W, H = prs.slide_width, prs.slide_height


def pct(share):
    return f"{int(share * 100 + 0.5)}%"                 # rounded as Excel shows 0%


def rgb(hex_):
    return RGBColor.from_string(hex_)


# ------------------------------------------------------------------ text and shapes
TEXT_SHADOW = (f'<a:effectLst xmlns:a="{A_NS}"><a:outerShdw blurRad="38100" dist="38100" dir="2700000" algn="tl" '
               'rotWithShape="0"><a:srgbClr val="000000"><a:alpha val="40000"/></a:srgbClr></a:outerShdw></a:effectLst>')
SHAPE_SHADOW = (f'<a:effectLst xmlns:a="{A_NS}"><a:outerShdw blurRad="63500" dist="25400" dir="5400000" algn="t" '
                'rotWithShape="0"><a:srgbClr val="000000"><a:alpha val="35000"/></a:srgbClr></a:outerShdw></a:effectLst>')


def write(frame, paragraphs, *, size, colour, font=None, bold=False, align=None, shadow=False, after=None):
    """paragraphs: a list of paragraphs, each a string or a list of (text, bold) runs."""
    frame.clear()
    for i, runs in enumerate(paragraphs):
        para = frame.paragraphs[0] if i == 0 else frame.add_paragraph()
        if align is not None:
            para.alignment = align
        if after is not None:
            para.space_after = Pt(after)
        for text, run_bold in ([(runs, bold)] if isinstance(runs, str) else runs):
            run = para.add_run()
            run.text = text
            run.font.size = Pt(size)
            run.font.bold = run_bold
            run.font.color.rgb = rgb(colour)
            run.font.name = font or S["body_font"]
            if shadow:                                   # Font > Text Effects > Shadow
                r_pr = run._r.get_or_add_rPr()
                r_pr.find(qn("a:solidFill")).addnext(etree.fromstring(TEXT_SHADOW))
    return frame


def textbox(slide, x, y, w, h, paragraphs, **fmt):
    box = slide.shapes.add_textbox(x, y, w, h)
    box.text_frame.word_wrap = True
    write(box.text_frame, paragraphs, **fmt)
    return box


def rect(slide, x, y, w, h, *, fill=None, line=None, width=1.0, shadow=False):
    shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, x, y, w, h)
    if fill:
        shape.fill.solid()
        shape.fill.fore_color.rgb = rgb(fill)
    else:
        shape.fill.background()
    if line:
        shape.line.color.rgb = rgb(line)
        shape.line.width = Pt(width)
    else:
        shape.line.fill.background()
    if shadow:
        sp_pr = shape._element.spPr
        sp_pr.find(qn("a:ln")).addnext(etree.fromstring(SHAPE_SHADOW))
    return shape


def rule(slide, x1, x2, y, colour, width=1.5):
    """A straight line (Insert > Shapes > Line), named as PowerPoint names it."""
    line = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, x1, y, x2, y)
    line.line.color.rgb = rgb(colour)
    line.line.width = Pt(width)
    c_nv = line._element.find(qn("p:nvCxnSpPr")).find(qn("p:cNvPr"))
    c_nv.set("name", f"Straight Connector {int(c_nv.get('id')) - 1}")
    return line


def to_back(shape):
    """Arrange > Send to Back."""
    tree = shape._element.getparent()
    tree.remove(shape._element)
    tree.insert(2, shape._element)                      # after the group's own properties


def wood_background(slide):
    """Format Background > Picture or texture fill: the wood picture."""
    _, r_id = slide.part.get_or_add_image_part(wood_path)
    c_sld = slide._element.find(qn("p:cSld"))
    for old in c_sld.findall(qn("p:bg")):
        c_sld.remove(old)
    c_sld.insert(0, etree.fromstring(
        f'<p:bg xmlns:p="{P_NS}" xmlns:a="{A_NS}" xmlns:r="{R_NS}"><p:bgPr><a:blipFill dpi="0" rotWithShape="1">'
        f'<a:blip r:embed="{r_id}"/><a:srcRect/><a:stretch><a:fillRect/></a:stretch></a:blipFill>'
        '<a:effectLst/></p:bgPr></p:bg>'))


def placeholder(slide, idx):
    return next(p for p in slide.placeholders if p.placeholder_format.idx == idx)


def place(shape, x, y, w, h):
    shape.left, shape.top, shape.width, shape.height = x, y, w, h


# ------------------------------------------------------------------ slide frames
def caps(text):
    """The first and last slides' titles: capitals on the wood cards, as in the PZ deck."""
    return text.upper() if S["card_caps"] else text


def title_card(slide, title, lines):
    """The first and last slides. Wood style: a white card held by two straps on the wood, as in
    the PZ deck. Marketing style: a centred title over a line, in the thin frame."""
    head, sub = placeholder(slide, 0), placeholder(slide, 1)
    if "title" in S["wood"]:
        wood_background(slide)
        card_x, card_y, card_w, card_h = Inches(2.0), Inches(1.7), W - Inches(4.0), Inches(4.0)
        card = rect(slide, card_x, card_y, card_w, card_h, fill="FFFFFF", shadow=True)
        border = rect(slide, card_x + Inches(0.1), card_y + Inches(0.1), card_w - Inches(0.2), card_h - Inches(0.2),
                      line=S["rule"], width=1)
        for strap_y, strap_h in ((0, Inches(1.95)), (Inches(5.45), H - Inches(5.45))):
            rect(slide, W // 2 - Inches(0.3), strap_y, Inches(0.6), strap_h, fill="4E3B30", shadow=True)
        for shape in reversed((card, border)):
            to_back(shape)
        place(head, Inches(2.25), Inches(2.5), W - Inches(4.5), Inches(1.1))
        write(head.text_frame, [caps(title)], size=48, colour=S["title"], font=S["head_font"],
              bold=True, align=PP_ALIGN.CENTER, shadow=S["card_shadow"])
        rule(slide, Inches(3.2), W - Inches(3.2), Inches(3.75), S["rule"])
        place(sub, Inches(2.3), Inches(3.9), W - Inches(4.6), Inches(1.55))
        write(sub.text_frame, lines, size=24, colour=S["text"], align=PP_ALIGN.CENTER, after=6)
        sub.text_frame.paragraphs[-1].runs[0].font.size = Pt(16)      # the small source line
    else:
        frame(slide)
        place(head, Inches(0.8), Inches(2.15), W - Inches(1.6), Inches(1.1))
        write(head.text_frame, [caps(title)], size=48, colour=S["title"], font=S["head_font"],
              bold=True, align=PP_ALIGN.CENTER)
        rule(slide, Inches(2.5), W - Inches(2.5), Inches(3.45), S["rule"])
        place(sub, Inches(0.8), Inches(3.65), W - Inches(1.6), Inches(2.4))
        write(sub.text_frame, lines, size=28, colour=S["text"], align=PP_ALIGN.CENTER, after=14)
        sub.text_frame.paragraphs[-1].runs[0].font.size = Pt(16)
    head.text_frame.vertical_anchor = MSO_ANCHOR.BOTTOM     # the title sits just above the line
    sub.text_frame.vertical_anchor = MSO_ANCHOR.TOP


def frame(slide):
    """The thin line round the slide, as in the Marketing Budget deck."""
    if S["frame"]:
        to_back(rect(slide, Inches(0.3), Inches(0.3), W - Inches(0.6), H - Inches(0.6), line=S["frame"], width=1))


def content(slide, title, subtitle):
    """A content slide's frame, title, line and subtitle; returns the top of the free space."""
    head = slide.shapes.title
    if "content" in S["wood"]:
        wood_background(slide)
        card = rect(slide, Inches(0.45), Inches(0.35), W - Inches(0.9), H - Inches(0.7), fill="FFFFFF", shadow=True)
        border = rect(slide, Inches(0.55), Inches(0.45), W - Inches(1.1), H - Inches(0.9), line=S["rule"], width=1)
        for shape in reversed((card, border)):
            to_back(shape)
    else:
        frame(slide)
    place(head, Inches(0.8), Inches(0.55), W - Inches(1.6), Inches(0.8))
    write(head.text_frame, [title], size=S["title_size"], colour=S["title"], font=S["head_font"], bold=True,
          align=PP_ALIGN.CENTER)
    head.text_frame.vertical_anchor = MSO_ANCHOR.MIDDLE
    rule(slide, Inches(1.0), W - Inches(1.0), Inches(1.42), S["rule"])
    textbox(slide, Inches(0.8), Inches(1.5), W - Inches(1.6), Inches(0.45), [subtitle], size=18, colour=S["muted"],
            align=PP_ALIGN.CENTER)
    return Inches(2.1)


def cell_border(cell, colour):
    tc_pr = cell._tc.get_or_add_tcPr()
    for tag in ("a:lnL", "a:lnR", "a:lnT", "a:lnB"):
        for old in tc_pr.findall(qn(tag)):
            tc_pr.remove(old)
    for side in reversed(("lnL", "lnR", "lnT", "lnB")):
        tc_pr.insert(0, etree.fromstring(
            f'<a:{side} xmlns:a="{A_NS}" w="12700" cap="flat" cmpd="sng" algn="ctr"><a:solidFill>'
            f'<a:srgbClr val="{colour}"/></a:solidFill><a:prstDash val="solid"/><a:round/>'
            f'<a:headEnd type="none" w="med" len="med"/><a:tailEnd type="none" w="med" len="med"/></a:{side}>'))


# ================================================================== 1. Title
s = prs.slides.add_slide(LAYOUT["Title Slide"])
title_card(s, "Relative Interest", ["Digital Skills Programmes on Google Trends",
                                     "Market Research Lab, Task 1  ·  Nigeria, past 12 months"])
s.notes_slide.notes_text_frame.text = (
    "My presentation is on the relative interest in five digital skills programmes in Nigeria, using Google Trends.")

# ================================================================== 2. The scores
s = prs.slides.add_slide(LAYOUT["Title and Content"])
top = content(s, "Relative-Interest Observations", "The average Google Trends score of each programme")
ph = placeholder(s, 1)
rows = [("Programme", "Average score", "Rank")] + [(p["name"], str(p["score"]), str(p["rank"])) for p in P]
widths = [Inches(5.9), Inches(2.6), Inches(2.1)]
ROW_H = Inches(0.6)
table_w = sum(widths, Emu(0))
frame_ = s.shapes.add_table(len(rows), len(widths), (W - table_w) // 2, top + Inches(0.1), table_w, ROW_H * len(rows))
table = frame_.table
frame_._element.graphic.graphicData.tbl.tblPr.find(qn("a:tableStyleId")).text = TABLE_GRID
table.first_row = True
table.horz_banding = False
for c, w in enumerate(widths):
    table.columns[c].width = w
for r, values in enumerate(rows):
    table.rows[r].height = ROW_H
    for c, value in enumerate(values):
        cell = table.cell(r, c)
        cell.vertical_anchor = MSO_ANCHOR.MIDDLE
        fill = S["head_fill"] if r == 0 else (S["band"] if r % 2 == 0 else None)
        if fill:
            cell.fill.solid()
            cell.fill.fore_color.rgb = rgb(fill)
        else:
            cell.fill.background()
        cell_border(cell, S["grid"])
        write(cell.text_frame, [value], size=20, colour="FFFFFF" if r == 0 else S["text"], bold=r == 0,
              align=PP_ALIGN.LEFT if c == 0 else PP_ALIGN.CENTER)
# Into the content placeholder's slot, as the Insert Table icon puts it (then moved to the middle).
nv = frame_._element.find(qn("p:nvGraphicFramePr"))
nv.find(qn("p:cNvPr")).set("id", str(ph.shape_id))
nv.find(qn("p:cNvPr")).set("name", ph.name)
nv.find(qn("p:nvPr")).insert(0, etree.fromstring(f'<p:ph xmlns:p="{P_NS}" idx="1"/>'))
ph._element.addprevious(frame_._element)
ph._element.getparent().remove(ph._element)
textbox(s, Inches(0.8), top + Inches(0.1) + ROW_H * len(rows) + Inches(0.3), W - Inches(1.6), Inches(0.45),
        ["Google Trends gives each programme a score from 0 to 100, where 100 means the highest interest."],
        size=16, colour=S["muted"], align=PP_ALIGN.CENTER)
s.notes_slide.notes_text_frame.text = (
    "These are the average scores I got from Google Trends for the past 12 months. Cybersecurity had the "
    "highest score, and Generative AI & Prompt Engineering and Web Development had the lowest.")

# ================================================================== 3. The pie chart
s = prs.slides.add_slide(LAYOUT["Title and Content"])
top = content(s, "Relative Interest by Programme", "Each programme's share of the total interest")
ph = placeholder(s, 1)
chart_data = CategoryChartData(number_format="0")
chart_data.categories = [p["name"] for p in P]
chart_data.add_series("Average score", [p["score"] for p in P])
CHART = (Inches(1.0), top - Inches(0.05), Inches(6.6), Inches(4.65))
gframe = s.shapes.add_chart(XL_CHART_TYPE.PIE, *CHART, chart_data)
chart = gframe.chart
chart.font.name = S["body_font"]
chart.font.size = Pt(16)
chart.font.color.rgb = rgb(S["text"])
chart.has_title = True
write(chart.chart_title.text_frame, ["Share of Total Interest"], size=16, colour=S["text"])
chart.has_legend = False                                # the key beside the chart names the slices
plot = chart.plots[0]
plot.vary_by_categories = True
series = plot.series[0]
for i, colour in enumerate(S["pie"]):
    point = series.points[i].format
    point.fill.solid()
    point.fill.fore_color.rgb = rgb(colour)
    point.line.color.rgb = rgb("FFFFFF")                # white lines between the slices
    point.line.width = Pt(1.5)
plot.has_data_labels = True
labels = plot.data_labels
labels.show_percentage = True
labels.show_value = False
labels.show_category_name = False
labels.position = XL_LABEL_POSITION.OUTSIDE_END
labels.font.size = Pt(16)
labels.font.bold = True
labels.font.name = S["body_font"]
labels.font.color.rgb = rgb(S["text"])
# A big pie under the chart title: the plot area placed by hand (Format Plot Area).
plot_area = chart._chartSpace.chart.plotArea
for old in plot_area.findall(qn("c:layout")):
    plot_area.remove(old)
plot_area.insert(0, etree.fromstring(
    '<c:layout xmlns:c="http://schemas.openxmlformats.org/drawingml/2006/chart"><c:manualLayout>'
    '<c:layoutTarget val="inner"/><c:xMode val="edge"/><c:yMode val="edge"/>'
    '<c:x val="0.235"/><c:y val="0.18"/><c:w val="0.53"/><c:h val="0.74"/></c:manualLayout></c:layout>'))
# Into the content placeholder's slot, as the Insert Chart icon puts it.
nv = gframe._element.find(qn("p:nvGraphicFramePr"))
nv.find(qn("p:cNvPr")).set("id", str(ph.shape_id))
nv.find(qn("p:cNvPr")).set("name", ph.name)
nv.find(qn("p:nvPr")).insert(0, etree.fromstring(f'<p:ph xmlns:p="{P_NS}" idx="1"/>'))
ph._element.addprevious(gframe._element)
ph._element.getparent().remove(ph._element)
# The key: each programme's shade, name, score and share.
for i, (p, colour) in enumerate(zip(P, S["pie"])):
    y = top + Inches(0.25) + Inches(0.86) * i
    rect(s, Inches(7.85), y + Inches(0.06), Inches(0.28), Inches(0.28), fill=colour, line=S["key_line"], width=0.75)
    key = textbox(s, Inches(8.25), y - Inches(0.04), Inches(4.5), Inches(0.82),
                  [[(p["name"], True)], f"Score {p['score']}  ·  {pct(p['share'])}"], size=16, colour=S["text"])
    key.text_frame.paragraphs[1].runs[0].font.size = Pt(15)
textbox(s, Inches(1.0), H - Inches(0.8), W - Inches(2.0), Inches(0.3),
        ["Source: Google Trends, Nigeria, past 12 months (28 September 2025 to 28 September 2026)."],
        size=12, colour=S["muted"], align=PP_ALIGN.CENTER)
s.notes_slide.notes_text_frame.text = (
    f"This pie chart shows the share of interest for each programme. {P[0]['name']} has the biggest share at "
    f"{pct(P[0]['share'])}, then {P[1]['name']} at {pct(P[1]['share'])} and {P[2]['name']} at "
    f"{pct(P[2]['share'])}. {P[3]['name']} and {P[4]['name']} have {pct(P[4]['share'])} each.")

# ================================================================== 4. Observations
lowest = [p for p in P if p["score"] == P[-1]["score"]]
assert len(P) == 5 and len(lowest) == 2, "the sentences below expect a tie for last place"
s = prs.slides.add_slide(LAYOUT["Title and Content"])
top = content(s, "Observations", "What the pie chart shows")
box = rect(s, Inches(1.0), top + Inches(0.05), W - Inches(2.0), Inches(4.45), fill=S["box"])
body = placeholder(s, 1)
place(body, Inches(1.35), top + Inches(0.3), W - Inches(2.7), Inches(4.0))
box._element.getparent().remove(box._element)
body._element.addprevious(box._element)                 # the box behind the text
name = lambda p: (p["name"], True)
write(body.text_frame, [
    [name(P[0]), (f" had the highest interest, with {pct(P[0]['share'])} of the total.", False)],
    [name(P[1]), (f" came second with {pct(P[1]['share'])}.", False)],
    [name(P[2]), (f" came third with {pct(P[2]['share'])}.", False)],
    [name(lowest[0]), (" and ", False), name(lowest[1]),
     (f" had the lowest interest, with {pct(lowest[0]['share'])} each.", False)],
    [(f"This means {P[0]['name']} and {P[1]['name']} should be promoted first.", False)],
], size=24, colour=S["text"], after=10)
body.text_frame.vertical_anchor = MSO_ANCHOR.MIDDLE     # the sentences centred in their box
for para in body.text_frame.paragraphs:                 # programme names in the style's colour
    for run in para.runs:
        if run.font.bold:
            run.font.color.rgb = rgb(S["names"])
s.notes_slide.notes_text_frame.text = (
    f"From the chart, {P[0]['name']} is the most popular programme, followed by {P[1]['name']}. The organisation "
    "should promote these two first.")

# ================================================================== 5. Thank you
s = prs.slides.add_slide(LAYOUT["Title Slide"])
title_card(s, "Thank You", ["Any questions?", "Market Research Lab, Task 1"])
s.notes_slide.notes_text_frame.text = "Thank you for listening."

# ------------------------------------------------------------------ the theme, properties, save
theme = THEME_XML
theme = theme.replace('<a:latin typeface="Calibri Light" panose="020F0302020204030204"/>',
                      f'<a:latin typeface="{S["head_font"]}"/>')
theme = theme.replace('<a:latin typeface="Calibri" panose="020F0502020204030204"/>',
                      f'<a:latin typeface="{S["body_font"]}"/>')
if S["palette"]:                                        # Design > Variants > Colors > Customize Colors
    palette_name, colours = S["palette"]
    scheme = (f'<a:clrScheme name="{palette_name}"><a:dk1><a:sysClr val="windowText" lastClr="000000"/></a:dk1>'
              '<a:lt1><a:sysClr val="window" lastClr="FFFFFF"/></a:lt1>'
              + "".join(f'<a:{k}><a:srgbClr val="{v}"/></a:{k}>' for k, v in colours.items()) + "</a:clrScheme>")
    theme = re.sub(r'<a:clrScheme name="Office">.*?</a:clrScheme>', scheme, theme, flags=re.S)

props = prs.core_properties
now = datetime.now(timezone.utc).replace(microsecond=0, tzinfo=None)
props.title = "Relative Interest in Digital Skills Programmes"
props.subject = "Pie chart of the Google Trends relative-interest observations"
props.author = props.last_modified_by = ""
props.comments = ""
props.keywords = "Google Trends, relative interest, pie chart"
props.revision = 1
props.created = props.modified = now
buf = io.BytesIO()
prs.save(buf)

# Every theme part (slides and notes pages) gets the style's theme, and the document statistics
# the slide count.
with zipfile.ZipFile(buf) as zin, zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as zout:
    for info in zin.infolist():
        blob = zin.read(info.filename)
        if re.fullmatch(r"ppt/theme/theme\d+\.xml", info.filename):
            blob = theme.encode()
        elif info.filename == "docProps/app.xml":
            n = len(prs.slides)
            blob = re.sub(rb"<Slides>\d+</Slides>", f"<Slides>{n}</Slides>".encode(), blob)
            blob = re.sub(rb"<Notes>\d+</Notes>", f"<Notes>{n}</Notes>".encode(), blob)
        zout.writestr(info, blob)
print(f"wrote {out_path} ({style_name}, {len(prs.slides)} slides)")
