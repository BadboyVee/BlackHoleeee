#!/usr/bin/env python3
"""Build Relative_Interest_Pie_Chart.pptx: the relative-interest pie chart from the Excel
workbook, in a short deck made the PowerPoint 2013 way.

Usage: python build_deck.py template.pptx out.pptx

The deck is built on PowerPoint 2013's widescreen Office Theme (office2013.py), using its
standard layouts (Title Slide, Title and Content). The pie chart sits in the content
placeholder as a real PowerPoint chart, with its data in an embedded Excel workbook (Chart
Tools > Design > Edit Data), as pasting the chart from Excel gives. It has the same slices,
colours and labels as the chart in Relative_Interest_Pie_Chart.xlsx: orange for the top
programme, dark to light blue for the rest, each slice labelled with its score and its share of
the total. Slide titles are dark blue (set once on the slide master).

Slides: 1. title, 2. the pie chart, 3. what it shows.
"""
import io
import re
import sys
import zipfile
from datetime import datetime, timezone

from lxml import etree
from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.enum.chart import XL_CHART_TYPE, XL_LABEL_POSITION, XL_LEGEND_POSITION
from pptx.enum.dml import MSO_THEME_COLOR
from pptx.enum.shapes import MSO_CONNECTOR
from pptx.enum.text import PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Inches, Pt

from assignment_data import PROGRAMMES, SLICES, SOURCE, share
from office2013 import THEME_XML

A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
NAVY = (MSO_THEME_COLOR.ACCENT_1, -0.5)       # "Blue, Accent 1, Darker 50%"    1F4E79
ORANGE = (MSO_THEME_COLOR.ACCENT_2, -0.25)    # "Orange, Accent 2, Darker 25%"  C55A11
WHITE = (MSO_THEME_COLOR.BACKGROUND_1, 0)
CHART_TEXT = (MSO_THEME_COLOR.TEXT_1, 0.35)   # Office 2013 chart text: 595959
LABEL_TEXT = (MSO_THEME_COLOR.TEXT_1, 0.25)   # 404040
ACCENT = {"accent1": MSO_THEME_COLOR.ACCENT_1, "accent2": MSO_THEME_COLOR.ACCENT_2}

template_path, out_path = sys.argv[1:3]
prs = Presentation(template_path)
LAYOUT = {layout.name: layout for layout in prs.slide_layouts}


# ------------------------------------------------------------------ helpers (as in the PZ deck)
def paint(color, colour):
    """Set a python-pptx colour to a theme colour (plus its Lighter/Darker setting)."""
    color.theme_color = colour[0]
    if colour[1]:
        color.brightness = colour[1]


def colour_slide_titles():
    """Dark blue titles on every slide, set once on the slide master (View > Slide Master)."""
    style = prs.slide_master.element.find(qn("p:txStyles")).find(qn("p:titleStyle"))
    rpr = style.find(qn("a:lvl1pPr")).find(qn("a:defRPr"))
    for old in rpr.findall(qn("a:solidFill")):
        rpr.remove(old)
    rpr.insert(0, etree.fromstring(f'<a:solidFill xmlns:a="{A_NS}"><a:schemeClr val="accent1">'
                                   '<a:lumMod val="50000"/></a:schemeClr></a:solidFill>'))


def new_slide(layout, title):
    slide = prs.slides.add_slide(LAYOUT[layout])
    slide.shapes.title.text = title
    return slide


def placeholder(slide, idx):
    return next(p for p in slide.placeholders if p.placeholder_format.idx == idx)


def write(frame, items, size):
    """items: [[(text, bold[, colour]), ...], ...]; one paragraph each."""
    frame.clear()
    for i, runs in enumerate(items):
        para = frame.paragraphs[0] if i == 0 else frame.add_paragraph()
        for text, bold, *colour in runs:
            run = para.add_run()
            run.text = text
            run.font.size = Pt(size)
            if bold:
                run.font.bold = True
            if colour:
                paint(run.font.color, colour[0])


def into_placeholder(slide, ph, frame):
    """Put a chart where a content placeholder was, as the placeholder's Insert Chart icon
    does: the chart takes over the placeholder's id, name and slot, and the placeholder goes."""
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


def accent_line(slide):
    """A short orange line between the title and subtitle of a Title Slide. The layout leaves
    no gap there, so the title moves up 0.3 in to make room (as dragging it up would)."""
    title = slide.shapes.title
    left, width, height = title.left, title.width, title.height      # inherited from the layout
    title.left, title.top, title.width, title.height = left, title.top - Inches(0.3), width, height
    y = title.top + height + Inches(0.16)
    line = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(5.17), y, Inches(8.17), y)
    paint(line.line.color, ORANGE)
    line.line.width = Pt(3)
    c_nv = line._element.find(qn("p:nvCxnSpPr")).find(qn("p:cNvPr"))   # PowerPoint's name for it
    c_nv.set("name", f"Straight Connector {int(c_nv.get('id')) - 1}")
    return line


colour_slide_titles()

# ================================================================== 1. Title
s = new_slide("Title Slide", "Relative-Interest Observations")
accent_line(s)
write(placeholder(s, 1).text_frame, [[("Google Trends: five digital-skills programmes", False)],
                                     [("Nigeria, past 12 months", False)]], 24)

# ================================================================== 2. The pie chart
s = new_slide("Title and Content", "Relative Interest by Programme")
ph = placeholder(s, 1)
chart_data = CategoryChartData(number_format="0")
chart_data.categories = [name for name, _ in PROGRAMMES]
chart_data.add_series("Average score", [score for _, score in PROGRAMMES])
NOTE_H = Inches(0.4)
CHART_W = Inches(9.6)       # narrower than the placeholder, so the legend sits by the pie
frame = s.shapes.add_chart(XL_CHART_TYPE.PIE, (prs.slide_width - CHART_W) // 2, ph.top, CHART_W,
                           ph.height - NOTE_H, chart_data)
chart = frame.chart
chart.has_title = False
chart.font.size = Pt(18)
paint(chart.font.color, CHART_TEXT)
chart.has_legend = True
chart.legend.position = XL_LEGEND_POSITION.RIGHT
chart.legend.include_in_layout = False
plot = chart.plots[0]
plot.vary_by_categories = True
series = plot.series[0]
for i, (accent, brightness) in enumerate(SLICES):
    point = series.points[i].format
    point.fill.solid()
    paint(point.fill.fore_color, (ACCENT[accent], brightness))
    paint(point.line.color, WHITE)                       # white edges, as Excel 2013's pie style
    point.line.width = Pt(1.5)
plot.has_data_labels = True
labels = plot.data_labels
labels.show_value = True
labels.show_percentage = True
labels.show_category_name = False
labels.position = XL_LABEL_POSITION.OUTSIDE_END
labels.font.size = Pt(18)
labels.font.bold = True
paint(labels.font.color, LABEL_TEXT)
# Score and share on two lines (Format Data Labels > Separator: (New Line)); python-pptx has
# already switched the leader lines on. The labels keep the data's own number formats (the
# score as typed, the share as a whole percentage).
etree.SubElement(labels._element, qn("c:separator")).text = "\n"
into_placeholder(s, ph, frame)
note = s.shapes.add_textbox(ph.left, ph.top + ph.height - NOTE_H, ph.width, NOTE_H)
note.text_frame.word_wrap = True
write(note.text_frame, [[(f"Source: {SOURCE}. Average interest from 0 to 100.", False, CHART_TEXT)]], 14)
note.text_frame.paragraphs[0].alignment = PP_ALIGN.CENTER     # a caption, centred under the chart

# ================================================================== 3. What it shows
ranked = sorted(PROGRAMMES, key=lambda p: -p[1])
(first, a), (second, b), (third, c) = ranked[:3]
lowest = [name for name, score in ranked if score == ranked[-1][1]]
low = ranked[-1][1]
assert len(lowest) == 2 and len(ranked) == 5, "the sentences below expect a tie for last place"
s = new_slide("Title and Content", "What the Pie Chart Shows")
write(placeholder(s, 1).text_frame, [
    [(first, True, ORANGE), (f" had the highest interest: around {a}, or {share(a)}% of the total.", False)],
    [(second, True, NAVY), (f" came second: around {b} ({share(b)}%).", False)],
    [(third, True, NAVY), (f" came third: around {c} ({share(c)}%).", False)],
    [(lowest[0], True, NAVY), (" and ", False), (lowest[1], True, NAVY),
     (f" had the lowest interest: around {low} each ({share(low)}% each).", False)],
    [(f"So {first} and {second} should be promoted first.", False)],
], 24)

# ------------------------------------------------------------------ document properties, save
props = prs.core_properties
now = datetime.now(timezone.utc).replace(microsecond=0, tzinfo=None)
props.title = "Relative-Interest Observations"
props.subject = "Pie chart of the Google Trends relative-interest observations"
props.author = props.last_modified_by = ""
props.comments = ""
props.keywords = "Google Trends, relative interest, pie chart"
props.revision = 1
props.created = props.modified = now
buf = io.BytesIO()
prs.save(buf)

# Every theme part gets the 2013 Office Theme, and the document statistics the slide count.
with zipfile.ZipFile(buf) as zin, zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as zout:
    for info in zin.infolist():
        blob = zin.read(info.filename)
        if re.fullmatch(r"ppt/theme/theme\d+\.xml", info.filename):
            blob = THEME_XML.encode()
        elif info.filename == "docProps/app.xml":
            blob = re.sub(rb"<Slides>\d+</Slides>", f"<Slides>{len(prs.slides)}</Slides>".encode(), blob)
        zout.writestr(info, blob)
print(f"wrote {out_path} ({len(prs.slides)} slides)")
