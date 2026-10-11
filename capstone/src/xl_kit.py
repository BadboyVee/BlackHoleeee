"""Excel 2013-style building blocks shared by the capstone workbooks: Calibri cells with thin
lines, coloured heading rows, section titles, A4 landscape pages, and horizontal bar charts in
grey with the leading bars in the accent colour.

STYLE holds the colours: teal by default (part 1); set_style changes them.
"""
from openpyxl.chart import BarChart
from openpyxl.chart.label import DataLabelList
from openpyxl.chart.series import DataPoint
from openpyxl.chart.shapes import GraphicalProperties
from openpyxl.chart.text import RichText, Text
from openpyxl.chart.title import Title
from openpyxl.drawing.line import LineProperties
from openpyxl.drawing.text import CharacterProperties, Font as DrawingFont, Paragraph, ParagraphProperties, RegularTextRun
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.worksheet.page import PageMargins

TEAL, GREY, YELLOW = "0F766E", "B7C1CA", "FFF2CC"
STYLE = {"head": TEAL, "title": TEAL, "top": TEAL, "bar": GREY}


def set_style(**colours):
    """Heading fill (head), title colour (title), leading bar (top) and other bars (bar)."""
    STYLE.update(colours)
thin = Side(style="thin", color="D9DEE3")
BOX = Border(left=thin, right=thin, top=thin, bottom=thin)


def font(size=11, bold=False, italic=False, color="000000", underline=None):
    return Font(name="Calibri", size=size, bold=bold, italic=italic, color=color, underline=underline, family=2,
                scheme="minor")


def put(ws, ref, value, *, f=None, fill=None, fmt=None, h="left", wrap=True, bd=BOX):
    c = ws[ref]
    c.value = value
    c.font = f or font()
    if fill:
        c.fill = PatternFill("solid", fgColor=fill)
    if fmt:
        c.number_format = fmt
    c.alignment = Alignment(horizontal=h, vertical="center", wrap_text=wrap, indent=1 if h == "left" else 0)
    if bd:
        c.border = bd
    return c


def heads(ws, row, cols, texts, height=30):
    for col, text in zip(cols, texts):
        put(ws, f"{col}{row}", text, f=font(bold=True, color="FFFFFF"), fill=STYLE["head"], h="center")
    ws.row_dimensions[row].height = height


def section(ws, row, text, last_col):
    ws.merge_cells(f"A{row}:{last_col}{row}")
    put(ws, f"A{row}", text, f=font(12, bold=True, color=STYLE["title"]), bd=None)
    ws.row_dimensions[row].height = 20


def titles(ws, last_col, title, subtitle):
    for row, text, f in ((1, title, font(14, bold=True, color=STYLE["title"])), (2, subtitle, font(italic=True, color="404040"))):
        ws.merge_cells(f"A{row}:{last_col}{row}")
        put(ws, f"A{row}", text, f=f, bd=None)
    ws.row_dimensions[1].height = 21


def page(ws, widths, landscape=True):
    for col, w in widths.items():
        ws.column_dimensions[col].width = w
    ws.page_setup.orientation = "landscape" if landscape else "portrait"
    ws.page_setup.paperSize = ws.PAPERSIZE_A4
    ws.page_setup.fitToWidth, ws.page_setup.fitToHeight = 1, 0
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    ws.page_margins = PageMargins(left=0.5, right=0.5, top=0.6, bottom=0.6, header=0.3, footer=0.3)
    ws.sheet_view.showGridLines = False


def rich(size=1000, color="404040", bold=False):
    cp = CharacterProperties(latin=DrawingFont(typeface="+mn-lt"), sz=size, b=bold, solidFill=color)
    return RichText(p=[Paragraph(pPr=ParagraphProperties(defRPr=cp), endParaRPr=cp)])


def bars(ws, anchor, title, values, cats, fmt, vmax, top, width=16, height=7.5):
    """A horizontal bar chart: grey bars, the leading one teal, values at the bar ends."""
    ch = BarChart()
    ch.type, ch.grouping, ch.gapWidth = "bar", "clustered", 60
    cp = CharacterProperties(latin=DrawingFont(typeface="+mn-lt"), sz=1300, b=False, solidFill="404040")
    ch.title = Title(tx=Text(rich=RichText(p=[Paragraph(pPr=ParagraphProperties(defRPr=cp),
                                                        r=[RegularTextRun(rPr=cp, t=title)])])), overlay=False)
    ch.add_data(values, titles_from_data=False)
    ch.set_categories(cats)
    ch.legend = None
    s = ch.series[0]
    s.graphicalProperties = GraphicalProperties(solidFill=STYLE["bar"], ln=LineProperties(noFill=True))
    for i in top:
        s.dPt.append(DataPoint(idx=i, spPr=GraphicalProperties(solidFill=STYLE["top"], ln=LineProperties(noFill=True))))
    ch.dataLabels = DataLabelList(showVal=True, showSerName=False, showCatName=False, showLegendKey=False,
                                  showPercent=False)
    ch.dataLabels.numFmt = fmt
    ch.dataLabels.position = "outEnd"
    ch.dataLabels.txPr = rich(1000, "262626", bold=True)
    ch.x_axis.delete = False
    ch.x_axis.scaling.orientation = "maxMin"              # first row at the top, as in the table
    ch.x_axis.txPr = rich(1000)
    ch.x_axis.spPr = GraphicalProperties(ln=LineProperties(solidFill="D9D9D9", w=9525))
    ch.y_axis.delete = True
    ch.y_axis.scaling.min, ch.y_axis.scaling.max = 0, vmax
    ch.y_axis.majorGridlines = None
    ch.graphical_properties = GraphicalProperties(ln=LineProperties(solidFill="D9D9D9", w=9525))
    ch.width, ch.height = width, height
    ws.add_chart(ch, anchor)
