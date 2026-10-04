#!/usr/bin/env python3
"""Build Relative_Interest_Pie_Chart.pptx: a short, plain deck around the relative-interest pie
chart, made the way it would be in PowerPoint 2013.

Usage: python build_deck.py deck_data.json template.pptx out.pptx

deck_data.json comes from export_deck_data.py, which reads each programme's score, rank and
share out of the finished Relative_Interest_Pie_Chart.xlsx, so the slides match the workbook.

The deck uses PowerPoint 2013's widescreen Office Theme (office2013.py) and its standard layouts.
It is black and white: the first and last slides (Title Slide layout) have a black background
(Format Background > Solid fill > Black, Text 1) with white text, and the others (Title and
Content) are black on white. The table and the pie chart sit in the content placeholders, as
the placeholder's Insert Table and Insert Chart icons put them; the chart is in black and greys,
like the chart in the workbook. build.sh then gives each slide a transition (finish_deck.py).

Slides: 1. title, 2. the scores, 3. the pie chart, 4. observations, 5. thank you.
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
from pptx.enum.chart import XL_CHART_TYPE, XL_LABEL_POSITION, XL_LEGEND_POSITION
from pptx.enum.dml import MSO_THEME_COLOR
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Emu, Inches, Pt

from office2013 import THEME_XML

A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
TABLE_GRID = "{5940675A-B579-460E-94D1-54222C63F5DA}"   # PowerPoint's "No Style, Table Grid"

# Colours, as picked from the theme palette (theme colour, Lighter/Darker setting).
BLACK = (MSO_THEME_COLOR.TEXT_1, 0)                     # Black, Text 1
WHITE = (MSO_THEME_COLOR.BACKGROUND_1, 0)               # White, Background 1
LIGHT = (MSO_THEME_COLOR.BACKGROUND_1, -0.15)           # White, Background 1, Darker 15% (D9D9D9)
GREY = (MSO_THEME_COLOR.TEXT_1, 0.35)                   # Black, Text 1, Lighter 35% (595959)
LINE = (MSO_THEME_COLOR.BACKGROUND_1, -0.25)            # White, Background 1, Darker 25% (BFBFBF)

data_path, template_path, out_path = sys.argv[1:4]
data = json.load(open(data_path))
P = data["programmes"]                                  # pie order: largest share first
prs = Presentation(template_path)
LAYOUT = {layout.name: layout for layout in prs.slide_layouts}


def pct(share):
    return f"{int(share * 100 + 0.5)}%"                 # rounded as Excel shows 0%


# ------------------------------------------------------------------ helpers
def paint(color, colour):
    """Set a python-pptx colour to a theme colour (plus its Lighter/Darker setting)."""
    color.theme_color = colour[0]
    if colour[1]:
        color.brightness = colour[1]


def placeholder(slide, idx):
    return next(p for p in slide.placeholders if p.placeholder_format.idx == idx)


def write(frame, paragraphs, size=None, colour=None):
    """paragraphs: a list of paragraphs, each a string or a list of (text, bold) runs."""
    frame.clear()
    for i, runs in enumerate(paragraphs):
        para = frame.paragraphs[0] if i == 0 else frame.add_paragraph()
        for text, bold in ([(runs, False)] if isinstance(runs, str) else runs):
            run = para.add_run()
            run.text = text
            if size:
                run.font.size = Pt(size)
            if bold:
                run.font.bold = True
            if colour:
                paint(run.font.color, colour)
    return frame


def black_background(slide):
    """Format Background > Solid fill > Black, Text 1."""
    fill = slide.background.fill
    fill.solid()
    paint(fill.fore_color, BLACK)


def into_placeholder(slide, ph, frame):
    """Put a table or chart where a content placeholder was, as the placeholder's Insert Table
    and Insert Chart icons do: the new frame takes over the placeholder's id, name and slot, and
    the empty placeholder goes."""
    nv = frame._element.find(qn("p:nvGraphicFramePr"))
    c_nv = nv.find(qn("p:cNvPr"))
    c_nv.set("id", str(ph.shape_id))
    c_nv.set("name", ph.name)
    nv_pr = nv.find(qn("p:nvPr"))
    nv_pr.insert(0, etree.fromstring(
        f'<p:ph xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" idx="{ph.placeholder_format.idx}"/>'))
    ph._element.addprevious(frame._element)
    ph._element.getparent().remove(ph._element)
    return frame


def cell_border(cell):
    """Thin light-grey lines on all four sides of a table cell."""
    tc_pr = cell._tc.get_or_add_tcPr()
    for tag in ("a:lnL", "a:lnR", "a:lnT", "a:lnB"):
        for old in tc_pr.findall(qn(tag)):
            tc_pr.remove(old)
    for side in reversed(("lnL", "lnR", "lnT", "lnB")):
        tc_pr.insert(0, etree.fromstring(
            f'<a:{side} xmlns:a="{A_NS}" w="12700" cap="flat" cmpd="sng" algn="ctr">'
            '<a:solidFill><a:schemeClr val="bg1"><a:lumMod val="75000"/></a:schemeClr></a:solidFill>'
            '<a:prstDash val="solid"/><a:round/><a:headEnd type="none" w="med" len="med"/>'
            f'<a:tailEnd type="none" w="med" len="med"/></a:{side}>'))


def note(slide, text, top):
    """A small grey note across the slide, under the content."""
    box = slide.shapes.add_textbox(Inches(0.92), top, Inches(11.5), Inches(0.45))
    box.text_frame.word_wrap = True
    write(box.text_frame, [text], size=16, colour=GREY)
    return box


# ================================================================== 1. Title
s = prs.slides.add_slide(LAYOUT["Title Slide"])
black_background(s)
write(s.shapes.title.text_frame, ["Relative Interest in Digital Skills Programmes"], colour=WHITE)
write(placeholder(s, 1).text_frame, ["Market Research Lab, Task 1: Google Trends", "Nigeria, past 12 months"],
      colour=LIGHT)
s.notes_slide.notes_text_frame.text = (
    "My presentation is on the relative interest in five digital skills programmes in Nigeria, using Google Trends.")

# ================================================================== 2. The scores
s = prs.slides.add_slide(LAYOUT["Title and Content"])
s.shapes.title.text = "Relative-Interest Observations"
ph = placeholder(s, 1)
rows = [("Programme", "Average score", "Rank")] + [(p["name"], str(p["score"]), str(p["rank"])) for p in P]
widths = [Inches(6.3), Inches(2.6), Inches(2.6)]
ROW_H = Inches(0.65)
frame = s.shapes.add_table(len(rows), len(widths), ph.left, ph.top, sum(widths, Emu(0)), ROW_H * len(rows))
table = frame.table
frame._element.graphic.graphicData.tbl.tblPr.find(qn("a:tableStyleId")).text = TABLE_GRID
table.first_row = True
table.horz_banding = False
for c, w in enumerate(widths):
    table.columns[c].width = w
for r, values in enumerate(rows):
    table.rows[r].height = ROW_H
    for c, value in enumerate(values):
        cell = table.cell(r, c)
        cell.vertical_anchor = MSO_ANCHOR.MIDDLE
        if r == 0:                                      # header row: black, white bold text
            cell.fill.solid()
            paint(cell.fill.fore_color, BLACK)
        else:
            cell.fill.background()
        cell_border(cell)
        write(cell.text_frame, [[(value, r == 0)]], size=22, colour=WHITE if r == 0 else BLACK)
        if c > 0:
            cell.text_frame.paragraphs[0].alignment = PP_ALIGN.CENTER
into_placeholder(s, ph, frame)
note(s, "Google Trends gives each programme a score from 0 to 100, where 100 means the highest interest.",
     ph.top + ROW_H * len(rows) + Inches(0.35))
s.notes_slide.notes_text_frame.text = (
    "These are the average scores I got from Google Trends for the past 12 months. Cybersecurity had the "
    "highest score, and Generative AI & Prompt Engineering and Web Development had the lowest.")

# ================================================================== 3. The pie chart
s = prs.slides.add_slide(LAYOUT["Title and Content"])
s.shapes.title.text = "Relative Interest by Programme"
ph = placeholder(s, 1)
chart_data = CategoryChartData(number_format="0")
chart_data.categories = [p["name"] for p in P]
chart_data.add_series("Average score", [p["score"] for p in P])
CHART_W = Inches(10.2)                                  # narrower than the placeholder: legend by the pie
frame = s.shapes.add_chart(XL_CHART_TYPE.PIE, (prs.slide_width - CHART_W) // 2, ph.top, CHART_W,
                           ph.height - Inches(0.4), chart_data)
chart = frame.chart
chart.has_title = False
chart.font.size = Pt(18)
paint(chart.font.color, BLACK)
chart.has_legend = True
chart.legend.position = XL_LEGEND_POSITION.RIGHT
chart.legend.include_in_layout = False
plot = chart.plots[0]
plot.vary_by_categories = True
series = plot.series[0]
for i, p in enumerate(P):
    point = series.points[i].format
    point.fill.solid()
    point.fill.fore_color.rgb = RGBColor.from_string(p["colour"])
    paint(point.line.color, WHITE)                      # white lines between the slices
    point.line.width = Pt(1.5)
plot.has_data_labels = True
labels = plot.data_labels
labels.show_percentage = True
labels.show_value = False
labels.show_category_name = False
labels.position = XL_LABEL_POSITION.OUTSIDE_END
labels.font.size = Pt(18)
labels.font.bold = True
paint(labels.font.color, BLACK)
# A bigger pie: place the plot area by hand (Format Plot Area, dragged to size), leaving room for
# the labels around it and the legend on the right.
plot_area = chart._chartSpace.chart.plotArea
for old in plot_area.findall(qn("c:layout")):
    plot_area.remove(old)
plot_area.insert(0, etree.fromstring(
    '<c:layout xmlns:c="http://schemas.openxmlformats.org/drawingml/2006/chart"><c:manualLayout>'
    '<c:layoutTarget val="inner"/><c:xMode val="edge"/><c:yMode val="edge"/>'
    '<c:x val="0.14"/><c:y val="0.11"/><c:w val="0.333"/><c:h val="0.78"/></c:manualLayout></c:layout>'))
into_placeholder(s, ph, frame)
note(s, "Source: Google Trends, Nigeria, past 12 months (28 September 2025 to 28 September 2026).",
     ph.top + ph.height - Inches(0.3))
s.notes_slide.notes_text_frame.text = (
    f"This pie chart shows the share of interest for each programme. {P[0]['name']} has the biggest share at "
    f"{pct(P[0]['share'])}, then {P[1]['name']} at {pct(P[1]['share'])} and {P[2]['name']} at "
    f"{pct(P[2]['share'])}. {P[3]['name']} and {P[4]['name']} have {pct(P[4]['share'])} each.")

# ================================================================== 4. Observations
lowest = [p for p in P if p["score"] == P[-1]["score"]]
assert len(P) == 5 and len(lowest) == 2, "the sentences below expect a tie for last place"
s = prs.slides.add_slide(LAYOUT["Title and Content"])
s.shapes.title.text = "Observations"
write(placeholder(s, 1).text_frame, [
    [(P[0]["name"], True), (f" had the highest interest, with {pct(P[0]['share'])} of the total.", False)],
    [(P[1]["name"], True), (f" came second with {pct(P[1]['share'])}.", False)],
    [(P[2]["name"], True), (f" came third with {pct(P[2]['share'])}.", False)],
    [(lowest[0]["name"], True), (" and ", False), (lowest[1]["name"], True),
     (f" had the lowest interest, with {pct(lowest[0]['share'])} each.", False)],
    [(f"This means {P[0]['name']} and {P[1]['name']} should be promoted first.", False)],
], size=26)
s.notes_slide.notes_text_frame.text = (
    f"From the chart, {P[0]['name']} is the most popular programme, followed by {P[1]['name']}. The organisation "
    "should promote these two first.")

# ================================================================== 5. Thank you
s = prs.slides.add_slide(LAYOUT["Title Slide"])
black_background(s)
write(s.shapes.title.text_frame, ["Thank You"], colour=WHITE)
write(placeholder(s, 1).text_frame, ["Any questions?"], colour=LIGHT)
s.notes_slide.notes_text_frame.text = "Thank you for listening."

# ------------------------------------------------------------------ document properties, save
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

# The notes pages python-pptx adds use its own (Office 2007) theme; give them the 2013 one too,
# and record the slide count in the document statistics.
with zipfile.ZipFile(buf) as zin, zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as zout:
    for info in zin.infolist():
        blob = zin.read(info.filename)
        if re.fullmatch(r"ppt/theme/theme\d+\.xml", info.filename):
            blob = THEME_XML.encode()
        elif info.filename == "docProps/app.xml":
            n = len(prs.slides)
            blob = re.sub(rb"<Slides>\d+</Slides>", f"<Slides>{n}</Slides>".encode(), blob)
            blob = re.sub(rb"<Notes>\d+</Notes>", f"<Notes>{n}</Notes>".encode(), blob)
        zout.writestr(info, blob)
print(f"wrote {out_path} ({len(prs.slides)} slides)")
