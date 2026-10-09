"""The slide styles and building blocks shared by the assignment decks, made the way they would be
in PowerPoint 2013 (on the widescreen Office Theme template from office2013.py).

Three colour palettes (STYLES):
  marketing  the Marketing Department Budget deck's: Calibri, dark-blue (1F3864) titles over a
             dark-blue line, a thin light-blue frame round each slide, light-blue (DEEBF7) boxes,
             and charts in black and greys.
  pz         the PZ Nigeria Limited deck's wood design: a wood background (make_wood.py), white
             cards with a thin orange border, Cambria titles, orange-brown (C55A11) lines and table
             headers, and charts in browns and oranges.
  mixed      both together: the wood title and closing slides, and white content slides with
             dark-blue titles, orange lines, peach and light-blue boxes, and navy, orange and grey
             charts.
  minimal    a clean, modern design with one teal (0F766E) accent: title and closing slides on
             a solid teal background with two soft circles, white text and a light line; content
             slides on a soft teal-grey background (E4EFEC) with left-aligned Calibri Light
             titles under a short teal line, white cards with a teal edge, white tables with teal
             headings and thin grey lines, grey bars with the leading bar in teal, and a small
             footer and slide number.

Text is in Office's own fonts: Calibri, with Cambria titles in the pz and mixed styles and
Calibri Light titles in the minimal style. Each
deck's theme carries the style's colours and fonts, so PowerPoint's colour palette (Shape Fill,
Font Color) offers them.
"""
import io
import json
import re
import zipfile
from datetime import datetime, timezone

from lxml import etree
from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE, XL_LABEL_POSITION, XL_TICK_LABEL_POSITION, XL_TICK_MARK
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Emu, Inches, Pt

from office2013 import THEME_XML

A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
P_NS = "http://schemas.openxmlformats.org/presentationml/2006/main"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
C_NS = "http://schemas.openxmlformats.org/drawingml/2006/chart"
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
        "bar": "7F7F7F", "bar_top": "1F3864",
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
        "bar": "A0662F", "bar_top": "C55A11",
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
        "bar": "1F3864", "bar_top": "C55A11",
    },
    "minimal": {
        "palette": ("Minimal Teal", {"dk2": "1F2933", "lt2": "F2F5F5", "accent1": "0F766E", "accent2": "5EAAA8",
                                     "accent3": "9AA5B1", "accent4": "1F2933", "accent5": "C5CCD3",
                                     "accent6": "52606D", "hlink": "0F766E", "folHlink": "52606D"}),
        "head_font": "Calibri Light", "body_font": "Calibri",
        "title_size": 34, "card_caps": False, "card_shadow": False,
        "title": "1F2933", "text": "1F2933", "muted": "55606E", "names": "0F766E",
        "rule": "0F766E", "frame": None, "wood": (), "cards": False,
        "head_fill": None, "band": None, "grid": "D9DEE3", "box": "FFFFFF", "table_fill": "FFFFFF",
        "pie": ["0F766E", "9AA5B1", "5EAAA8", "C5CCD3", "1F2933"], "key_line": "7B8794",
        "bar": "B7C1CA", "bar_top": "0F766E",
        "minimal": True,
        "background": "E4EFEC",                          # content slides: Format Background > Solid fill
        "cover": "0F766E", "cover_circle": "13827A",     # title and closing slides
        "cover_text": "FFFFFF", "cover_muted": "D3EBE7", "cover_rule": "8ED1C7",
    },
}

TEXT_SHADOW = (f'<a:effectLst xmlns:a="{A_NS}"><a:outerShdw blurRad="38100" dist="38100" dir="2700000" algn="tl" '
               'rotWithShape="0"><a:srgbClr val="000000"><a:alpha val="40000"/></a:srgbClr></a:outerShdw></a:effectLst>')
SHAPE_SHADOW = (f'<a:effectLst xmlns:a="{A_NS}"><a:outerShdw blurRad="63500" dist="25400" dir="5400000" algn="t" '
                'rotWithShape="0"><a:srgbClr val="000000"><a:alpha val="35000"/></a:srgbClr></a:outerShdw></a:effectLst>')


def rgb(hex_):
    return RGBColor.from_string(hex_)


def to_back(shape):
    """Arrange > Send to Back."""
    tree = shape._element.getparent()
    tree.remove(shape._element)
    tree.insert(2, shape._element)                      # after the group's own properties


def placeholder(slide, idx):
    return next(p for p in slide.placeholders if p.placeholder_format.idx == idx)


def place(shape, x, y, w, h):
    shape.left, shape.top, shape.width, shape.height = x, y, w, h


def into_placeholder(ph, frame):
    """Put a table or chart in a content placeholder's slot, as the placeholder's Insert Table and
    Insert Chart icons do: the frame takes over the placeholder's id and name, and the placeholder
    goes."""
    nv = frame._element.find(qn("p:nvGraphicFramePr"))
    nv.find(qn("p:cNvPr")).set("id", str(ph.shape_id))
    nv.find(qn("p:cNvPr")).set("name", ph.name)
    nv.find(qn("p:nvPr")).insert(0, etree.fromstring(f'<p:ph xmlns:p="{P_NS}" idx="{ph.placeholder_format.idx}"/>'))
    ph._element.addprevious(frame._element)
    ph._element.getparent().remove(ph._element)
    return frame


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


def cell_lines(cell, **sides):
    """Set a table cell's borders one side at a time (left, right, top, bottom): (colour, width in
    points), or None for no line."""
    tc_pr = cell._tc.get_or_add_tcPr()
    for tag in ("a:lnL", "a:lnR", "a:lnT", "a:lnB"):
        for old in tc_pr.findall(qn(tag)):
            tc_pr.remove(old)
    for side, tag in reversed((("left", "lnL"), ("right", "lnR"), ("top", "lnT"), ("bottom", "lnB"))):
        line = sides.get(side)
        if line is None:
            xml = f'<a:{tag} xmlns:a="{A_NS}" w="12700" cmpd="sng"><a:noFill/></a:{tag}>'
        else:
            colour, width = line
            xml = (f'<a:{tag} xmlns:a="{A_NS}" w="{int(width * 12700)}" cap="flat" cmpd="sng" algn="ctr">'
                   f'<a:solidFill><a:srgbClr val="{colour}"/></a:solidFill><a:prstDash val="solid"/><a:round/>'
                   f'<a:headEnd type="none" w="med" len="med"/><a:tailEnd type="none" w="med" len="med"/></a:{tag}>')
        tc_pr.insert(0, etree.fromstring(xml))


def plot_layout(chart, x, y, w, h):
    """Place a chart's plot area by hand (Format Plot Area), as fractions of the chart."""
    plot_area = chart._chartSpace.chart.plotArea
    for old in plot_area.findall(qn("c:layout")):
        plot_area.remove(old)
    plot_area.insert(0, etree.fromstring(
        f'<c:layout xmlns:c="{C_NS}"><c:manualLayout><c:layoutTarget val="inner"/><c:xMode val="edge"/>'
        f'<c:yMode val="edge"/><c:x val="{x}"/><c:y val="{y}"/><c:w val="{w}"/><c:h val="{h}"/></c:manualLayout>'
        '</c:layout>'))


class Deck:
    """A deck in one of the STYLES, on the Office 2013 template."""

    def __init__(self, style_name, template_path, wood_path):
        self.style_name = style_name
        self.S = STYLES[style_name]
        self.prs = Presentation(template_path)
        self.layout = {layout.name: layout for layout in self.prs.slide_layouts}
        self.W, self.H = self.prs.slide_width, self.prs.slide_height
        self.wood_path = wood_path
        self.plan = []                                   # (slide, shape, step, effect)
        self.chrome = ()                                 # the last slide's title, line and subtitle
        self.footer = ""                                 # minimal style: the footer on content slides

    # -------------------------------------------------------------- animations
    def anim(self, slide, shapes, step, effect="fade"):
        """Entrance animations for finish_deck.py: step 1 starts after the slide transition, and
        each later step after the one before (Start: After Previous); shapes in one step appear
        together. effect is fade, wipe-left, wipe-up or wipe-down."""
        for shape in shapes if isinstance(shapes, (list, tuple)) else [shapes]:
            self.plan.append((slide, shape, step, effect))

    def anim_chrome(self, slide, title_card=False):
        """The title and its line first, then the subtitle (title cards: title, line, subtitle)."""
        head, line, sub = self.chrome
        if title_card:
            self.anim(slide, head, 1)
            self.anim(slide, line, 2, "wipe-left")
            self.anim(slide, sub, 3)
        else:
            self.anim(slide, head, 1)
            self.anim(slide, line, 1, "wipe-left")
            self.anim(slide, sub, 2)

    # -------------------------------------------------------------- text and shapes
    def write(self, frame, paragraphs, *, size, colour, font=None, bold=False, align=None, shadow=False, after=None):
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
                run.font.name = font or self.S["body_font"]
                if shadow:                               # Font > Text Effects > Shadow
                    r_pr = run._r.get_or_add_rPr()
                    r_pr.find(qn("a:solidFill")).addnext(etree.fromstring(TEXT_SHADOW))
        return frame

    def textbox(self, slide, x, y, w, h, paragraphs, **fmt):
        box = slide.shapes.add_textbox(x, y, w, h)
        box.text_frame.word_wrap = True
        self.write(box.text_frame, paragraphs, **fmt)
        return box

    @staticmethod
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

    @staticmethod
    def rule(slide, x1, x2, y, colour, width=1.5):
        """A straight line (Insert > Shapes > Line), named as PowerPoint names it."""
        line = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, x1, y, x2, y)
        line.line.color.rgb = rgb(colour)
        line.line.width = Pt(width)
        c_nv = line._element.find(qn("p:nvCxnSpPr")).find(qn("p:cNvPr"))
        c_nv.set("name", f"Straight Connector {int(c_nv.get('id')) - 1}")
        return line

    def wood_background(self, slide):
        """Format Background > Picture or texture fill: the wood picture."""
        _, r_id = slide.part.get_or_add_image_part(self.wood_path)
        c_sld = slide._element.find(qn("p:cSld"))
        for old in c_sld.findall(qn("p:bg")):
            c_sld.remove(old)
        c_sld.insert(0, etree.fromstring(
            f'<p:bg xmlns:p="{P_NS}" xmlns:a="{A_NS}" xmlns:r="{R_NS}"><p:bgPr><a:blipFill dpi="0" rotWithShape="1">'
            f'<a:blip r:embed="{r_id}"/><a:srcRect/><a:stretch><a:fillRect/></a:stretch></a:blipFill>'
            '<a:effectLst/></p:bgPr></p:bg>'))

    @staticmethod
    def solid_background(slide, colour):
        """Format Background > Solid fill."""
        c_sld = slide._element.find(qn("p:cSld"))
        for old in c_sld.findall(qn("p:bg")):
            c_sld.remove(old)
        c_sld.insert(0, etree.fromstring(
            f'<p:bg xmlns:p="{P_NS}" xmlns:a="{A_NS}"><p:bgPr><a:solidFill><a:srgbClr val="{colour}"/></a:solidFill>'
            '<a:effectLst/></p:bgPr></p:bg>'))

    # -------------------------------------------------------------- slide frames
    def caps(self, text):
        """The first and last slides' titles: capitals on the wood cards, as in the PZ deck."""
        return text.upper() if self.S["card_caps"] else text

    def frame(self, slide):
        """The thin line round the slide, as in the Marketing Budget deck."""
        if self.S["frame"]:
            to_back(self.rect(slide, Inches(0.3), Inches(0.3), self.W - Inches(0.6), self.H - Inches(0.6),
                              line=self.S["frame"], width=1))

    def title_card(self, slide, title, lines, size=48):
        """The first and last slides. Wood style: a white card held by two straps on the wood, as
        in the PZ deck. Marketing style: a centred title over a line, in the thin frame."""
        S, W, H = self.S, self.W, self.H
        head, sub = placeholder(slide, 0), placeholder(slide, 1)
        if S.get("minimal"):
            self.solid_background(slide, S["cover"])
            # Two soft circles, a shade lighter than the background, off the right-hand edge.
            big = slide.shapes.add_shape(MSO_SHAPE.OVAL, W - Inches(4.6), Inches(-1.8), Inches(7.2), Inches(7.2))
            ring = slide.shapes.add_shape(MSO_SHAPE.OVAL, W - Inches(3.0), Inches(4.2), Inches(4.5), Inches(4.5))
            big.fill.solid()
            big.fill.fore_color.rgb = rgb(S["cover_circle"])
            big.line.fill.background()
            ring.fill.background()
            ring.line.color.rgb = rgb(S["cover_rule"])
            ring.line.width = Pt(1.25)
            for shape in (ring, big):
                to_back(shape)
            place(head, Inches(1.1), Inches(2.25), W - Inches(2.2), Inches(1.5))
            self.write(head.text_frame, [title], size=size, colour=S["cover_text"], font=S["head_font"],
                       align=PP_ALIGN.LEFT)
            line = self.rule(slide, Inches(1.2), Inches(2.7), Inches(3.97), S["cover_rule"], width=3)
            place(sub, Inches(1.1), Inches(4.2), W - Inches(2.2), Inches(2.0))
            self.write(sub.text_frame, lines, size=24, colour=S["cover_muted"], align=PP_ALIGN.LEFT, after=8)
            sub.text_frame.paragraphs[-1].runs[0].font.size = Pt(16)
        elif "title" in S["wood"]:
            self.wood_background(slide)
            card_x, card_y, card_w, card_h = Inches(2.0), Inches(1.7), W - Inches(4.0), Inches(4.0)
            card = self.rect(slide, card_x, card_y, card_w, card_h, fill="FFFFFF", shadow=True)
            border = self.rect(slide, card_x + Inches(0.1), card_y + Inches(0.1), card_w - Inches(0.2),
                               card_h - Inches(0.2), line=S["rule"], width=1)
            for strap_y, strap_h in ((0, Inches(1.95)), (Inches(5.45), H - Inches(5.45))):
                self.rect(slide, W // 2 - Inches(0.3), strap_y, Inches(0.6), strap_h, fill="4E3B30", shadow=True)
            for shape in reversed((card, border)):
                to_back(shape)
            place(head, Inches(2.25), Inches(2.5), W - Inches(4.5), Inches(1.1))
            self.write(head.text_frame, [self.caps(title)], size=size, colour=S["title"], font=S["head_font"],
                       bold=True, align=PP_ALIGN.CENTER, shadow=S["card_shadow"])
            line = self.rule(slide, Inches(3.2), W - Inches(3.2), Inches(3.75), S["rule"])
            place(sub, Inches(2.3), Inches(3.9), W - Inches(4.6), Inches(1.55))
            self.write(sub.text_frame, lines, size=24, colour=S["text"], align=PP_ALIGN.CENTER, after=6)
            sub.text_frame.paragraphs[-1].runs[0].font.size = Pt(16)      # the small source line
        else:
            self.frame(slide)
            place(head, Inches(0.8), Inches(2.15), W - Inches(1.6), Inches(1.1))
            self.write(head.text_frame, [self.caps(title)], size=size, colour=S["title"], font=S["head_font"],
                       bold=True, align=PP_ALIGN.CENTER)
            line = self.rule(slide, Inches(2.5), W - Inches(2.5), Inches(3.45), S["rule"])
            place(sub, Inches(0.8), Inches(3.65), W - Inches(1.6), Inches(2.4))
            self.write(sub.text_frame, lines, size=28, colour=S["text"], align=PP_ALIGN.CENTER, after=14)
            sub.text_frame.paragraphs[-1].runs[0].font.size = Pt(16)
        head.text_frame.vertical_anchor = MSO_ANCHOR.BOTTOM     # the title sits just above the line
        sub.text_frame.vertical_anchor = MSO_ANCHOR.TOP
        self.chrome = (head, line, sub)

    def content(self, slide, title, subtitle):
        """A content slide's frame, title, line and subtitle; returns the top of the free space."""
        S, W, H = self.S, self.W, self.H
        head = slide.shapes.title
        if S.get("minimal"):
            self.solid_background(slide, S["background"])
            line = self.rule(slide, Inches(0.8), Inches(1.5), Inches(0.62), S["rule"], width=3)
            place(head, Inches(0.7), Inches(0.68), W - Inches(1.4), Inches(0.72))
            self.write(head.text_frame, [title], size=S["title_size"], colour=S["title"], font=S["head_font"],
                       align=PP_ALIGN.LEFT)
            head.text_frame.vertical_anchor = MSO_ANCHOR.MIDDLE
            sub = self.textbox(slide, Inches(0.7), Inches(1.4), W - Inches(1.4), Inches(0.42), [subtitle], size=16,
                               colour=S["muted"], align=PP_ALIGN.LEFT)
            if self.footer:                              # footer text and the slide number
                self.textbox(slide, Inches(0.7), H - Inches(0.5), Inches(8.0), Inches(0.3), [self.footer], size=10,
                             colour=S["muted"])
                self.textbox(slide, W - Inches(1.7), H - Inches(0.5), Inches(1.0), Inches(0.3),
                             [str(len(self.prs.slides))], size=10, colour=S["muted"], align=PP_ALIGN.RIGHT)
            self.chrome = (head, line, sub)
            return Inches(2.1)
        if "content" in S["wood"]:
            self.wood_background(slide)
            card = self.rect(slide, Inches(0.45), Inches(0.35), W - Inches(0.9), H - Inches(0.7), fill="FFFFFF",
                             shadow=True)
            border = self.rect(slide, Inches(0.55), Inches(0.45), W - Inches(1.1), H - Inches(0.9), line=S["rule"],
                               width=1)
            for shape in reversed((card, border)):
                to_back(shape)
        else:
            self.frame(slide)
        place(head, Inches(0.8), Inches(0.55), W - Inches(1.6), Inches(0.8))
        self.write(head.text_frame, [title], size=S["title_size"], colour=S["title"], font=S["head_font"], bold=True,
                   align=PP_ALIGN.CENTER)
        head.text_frame.vertical_anchor = MSO_ANCHOR.MIDDLE
        line = self.rule(slide, Inches(1.0), W - Inches(1.0), Inches(1.42), S["rule"])
        sub = self.textbox(slide, Inches(0.8), Inches(1.5), W - Inches(1.6), Inches(0.45), [subtitle], size=18,
                           colour=S["muted"], align=PP_ALIGN.CENTER)
        self.chrome = (head, line, sub)
        return Inches(2.1)

    # -------------------------------------------------------------- cards and notes
    @property
    def left(self):
        """The left edge of full-width cards: in line with the title in the minimal style."""
        return Inches(0.8) if self.S.get("minimal") else Inches(1.0)

    def card(self, slide, x, y, w, h):
        """A tinted box; in the minimal style, a card with a teal edge. Returns its shapes."""
        shapes = [self.rect(slide, x, y, w, h, fill=self.S["box"])]
        if self.S.get("minimal"):
            shapes.append(self.rect(slide, x, y, Inches(0.07), h, fill=self.S["rule"]))
        return shapes

    @staticmethod
    def bullet_colour(frame, colour):
        """Format > Bullets > Color, for every paragraph."""
        for para in frame.paragraphs:
            p_pr = para._p.get_or_add_pPr()
            spacing = [p_pr.find(qn(t)) for t in ("a:lnSpc", "a:spcBef", "a:spcAft")]
            spacing = [el for el in spacing if el is not None]
            bu = etree.fromstring(f'<a:buClr xmlns:a="{A_NS}"><a:srgbClr val="{colour}"/></a:buClr>')
            if spacing:
                spacing[-1].addnext(bu)
            else:
                p_pr.insert(0, bu)

    def boxed_text(self, slide, top, paragraphs, size, height=Inches(4.45)):
        """The content placeholder's bulleted text on a full-width card; bold words in the style's
        colour. Returns the card's shapes and the text."""
        S, W, left = self.S, self.W, self.left
        shapes = self.card(slide, left, top + Inches(0.05), W - 2 * left, height)
        body = placeholder(slide, 1)
        place(body, left + Inches(0.35), top + Inches(0.25), W - 2 * left - Inches(0.7), height - Inches(0.4))
        for shape in shapes:                             # the card behind the text
            shape._element.getparent().remove(shape._element)
            body._element.addprevious(shape._element)
        self.write(body.text_frame, paragraphs, size=size, colour=S["text"], after=10)
        body.text_frame.vertical_anchor = MSO_ANCHOR.MIDDLE
        for para in body.text_frame.paragraphs:
            for run in para.runs:
                if run.font.bold:
                    run.font.color.rgb = rgb(S["names"])
        if S.get("minimal"):
            self.bullet_colour(body.text_frame, S["rule"])
        return (*shapes, body)

    def side_note(self, slide, top, paragraphs, size=17):
        """A card beside a chart, holding a few short points. Returns its shapes and the text."""
        x = Inches(8.55)
        w, h = self.W - x - Inches(0.85), Inches(4.4)
        shapes = self.card(slide, x, top + Inches(0.05), w, h)
        note = self.textbox(slide, x + Inches(0.25), top + Inches(0.25), w - Inches(0.5), h - Inches(0.4), paragraphs,
                            size=size, colour=self.S["text"], after=12)
        note.text_frame.vertical_anchor = MSO_ANCHOR.MIDDLE
        return (*shapes, note)

    @staticmethod
    def chart_area(top):
        """Where a chart goes when a side note sits beside it: x, y, width, height."""
        return Inches(0.9), top - Inches(0.05), Inches(7.45), Inches(4.55)

    def footnote(self, slide, y, text, height=Inches(0.4)):
        """A small grey note under a table or chart."""
        S, W = self.S, self.W
        if S.get("minimal"):                             # lined up with the title
            return self.textbox(slide, Inches(0.7), y, W - Inches(1.4), height, [text], size=14, colour=S["muted"])
        return self.textbox(slide, Inches(0.8), y, W - Inches(1.6), height, [text], size=14, colour=S["muted"],
                            align=PP_ALIGN.CENTER)

    # -------------------------------------------------------------- tables and charts
    def table(self, slide, ph, x, y, rows, widths, row_h, size, *, centre_from=1, bold_rows=()):
        """A Table Grid table in the content placeholder's slot: the style's header row, banded
        rows, thin lines. Columns from centre_from on are centred; row_h is a height or a list."""
        heights = row_h if isinstance(row_h, list) else [row_h] * len(rows)
        S = self.S
        minimal = S.get("minimal")                       # open table: teal headings, thin grey lines
        frame = slide.shapes.add_table(len(rows), len(widths), x, y, sum(widths, Emu(0)), sum(heights, Emu(0)))
        table = frame.table
        frame._element.graphic.graphicData.tbl.tblPr.find(qn("a:tableStyleId")).text = TABLE_GRID
        table.first_row = True
        table.horz_banding = False
        for c, w in enumerate(widths):
            table.columns[c].width = w
        for r, values in enumerate(rows):
            table.rows[r].height = heights[r]
            for c, value in enumerate(values):
                cell = table.cell(r, c)
                cell.vertical_anchor = MSO_ANCHOR.MIDDLE
                fill = S.get("table_fill") or (S["head_fill"] if r == 0 else (S["band"] if r % 2 == 0 else None))
                if fill:
                    cell.fill.solid()
                    cell.fill.fore_color.rgb = rgb(fill)
                else:
                    cell.fill.background()
                if minimal:
                    under = lambda row: (S["rule"], 1.5) if row == 0 else (S["grid"], 0.75)
                    cell_lines(cell, top=under(r - 1) if r else None, bottom=under(r))
                else:
                    cell_border(cell, S["grid"])
                head_colour = S["rule"] if minimal else "FFFFFF"
                self.write(cell.text_frame, value if isinstance(value, list) else [value], size=size,
                           colour=head_colour if r == 0 else S["text"], bold=r == 0 or r in bold_rows,
                           align=PP_ALIGN.LEFT if c < centre_from else PP_ALIGN.CENTER)
        return into_placeholder(ph, frame), table

    def bar_chart(self, slide, ph, x, y, w, h, labels, values, *, number_format, maximum, top, title=None):
        """A horizontal bar chart in the content placeholder's slot: the style's bar colour, the
        bars at the positions in top picked out, values at the bar ends, first item at the top."""
        S = self.S
        data = CategoryChartData(number_format=number_format)
        data.categories = labels
        data.add_series("Value", values)
        frame = slide.shapes.add_chart(XL_CHART_TYPE.BAR_CLUSTERED, x, y, w, h, data)
        chart = frame.chart
        chart.font.name = S["body_font"]
        chart.font.size = Pt(16)
        chart.font.color.rgb = rgb(S["text"])
        chart.has_legend = False
        chart.has_title = bool(title)
        if title:
            self.write(chart.chart_title.text_frame, [title], size=16, colour=S["text"])
        plot = chart.plots[0]
        plot.gap_width = 60
        plot.vary_by_categories = False
        series = plot.series[0]
        series.format.fill.solid()
        series.format.fill.fore_color.rgb = rgb(S["bar"])
        for i in top:
            point = series.points[i].format
            point.fill.solid()
            point.fill.fore_color.rgb = rgb(S["bar_top"])
        plot.has_data_labels = True
        labels_ = plot.data_labels
        labels_.number_format = number_format
        labels_.number_format_is_linked = False
        labels_.position = XL_LABEL_POSITION.OUTSIDE_END
        labels_.font.size = Pt(16)
        labels_.font.bold = True
        labels_.font.color.rgb = rgb(S["text"])
        cat, val = chart.category_axis, chart.value_axis
        cat.reverse_order = True                         # first item at the top, as in the table
        cat.major_tick_mark = XL_TICK_MARK.NONE
        cat.format.line.color.rgb = rgb("BFBFBF")
        cat.tick_labels.font.size = Pt(16)
        val.minimum_scale = 0
        val.maximum_scale = maximum
        val.has_major_gridlines = False
        val.major_tick_mark = XL_TICK_MARK.NONE
        val.tick_label_position = XL_TICK_LABEL_POSITION.NONE
        val.format.line.fill.background()
        if S.get("background"):                          # Format Chart Area > No fill, on a coloured slide
            space = chart._chartSpace
            space.find(qn("c:chart")).addnext(etree.fromstring(
                f'<c:spPr xmlns:c="{C_NS}" xmlns:a="{A_NS}"><a:noFill/><a:ln><a:noFill/></a:ln></c:spPr>'))
        return into_placeholder(ph, frame), chart

    # -------------------------------------------------------------- the theme, properties, save
    def save(self, out_path, *, title, subject, keywords):
        S, prs = self.S, self.prs
        theme = THEME_XML
        theme = theme.replace('<a:latin typeface="Calibri Light" panose="020F0302020204030204"/>',
                              f'<a:latin typeface="{S["head_font"]}"/>')
        theme = theme.replace('<a:latin typeface="Calibri" panose="020F0502020204030204"/>',
                              f'<a:latin typeface="{S["body_font"]}"/>')
        if S["palette"]:                                 # Design > Variants > Colors > Customize Colors
            palette_name, colours = S["palette"]
            scheme = (f'<a:clrScheme name="{palette_name}"><a:dk1><a:sysClr val="windowText" lastClr="000000"/></a:dk1>'
                      '<a:lt1><a:sysClr val="window" lastClr="FFFFFF"/></a:lt1>'
                      + "".join(f'<a:{k}><a:srgbClr val="{v}"/></a:{k}>' for k, v in colours.items())
                      + "</a:clrScheme>")
            theme = re.sub(r'<a:clrScheme name="Office">.*?</a:clrScheme>', scheme, theme, flags=re.S)

        props = prs.core_properties
        now = datetime.now(timezone.utc).replace(microsecond=0, tzinfo=None)
        props.title, props.subject, props.keywords = title, subject, keywords
        props.author = props.last_modified_by = ""
        props.comments = ""
        props.revision = 1
        props.created = props.modified = now
        buf = io.BytesIO()
        prs.save(buf)

        # Every theme part (slides and notes pages) gets the style's theme, and the document
        # statistics the slide count.
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
        if self.plan:                                    # the animations, for finish_deck.py
            slides = list(prs.slides)
            plan = {}
            for slide, shape, step, effect in self.plan:
                plan.setdefault(str(slides.index(slide) + 1), []).append(
                    {"name": shape.name, "step": step, "effect": effect})
            with open(re.sub(r"\.pptx$", ".anim.json", out_path), "w") as fh:
                json.dump(plan, fh, indent=2)
        print(f"wrote {out_path} ({self.style_name}, {len(prs.slides)} slides)")
