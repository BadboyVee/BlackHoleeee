#!/usr/bin/env python3
"""Build the capstone part 2 deck: the customer analysis for CyberStart, in a bright business
template theme (white slides, blue gradient blocks, bold Century Gothic titles in charcoal,
outline-ring numbers and circle diagrams), made the way it would be in PowerPoint 2013. Shapes
and text only: no pictures.

Usage: python build_customer_deck.py Customer_Analysis.xlsx template.pptx STYLE out.pptx
  The workbook must have been through LibreOffice (build.sh does this), so the worked-out
  figures (need importance and ranks, segment scores, the target) can be read from it. STYLE is
  azure (deck_kit.py), which sets the theme's colours and fonts.

The slides follow the tasks in the order they were set, each opened by a half-blue divider:
cover, contents, key figures; 1 the persona (profile, what Tunde wants, why Tunde buys); 2 the
journey map as a timeline with a feeling curve, and the pain points turned into opportunities;
3 the needs by type, the top five on a half-donut, and a bar chart of all twelve; 4 the four
segments as numbered cards; 5 the segment scores as a heat map; 6 the target segment; key
findings and thank you. Every slide's objects come in by themselves (out.anim.json, for
finish_deck.py).
"""
import sys

from lxml import etree
from openpyxl import load_workbook
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Emu, Inches, Pt

import customer_data as C
from deck_kit import A_NS, Deck, place, placeholder, rgb, to_back

workbook_path, template_path, style_name, out_path = sys.argv[1:5]
deck = Deck(style_name, template_path, None)
S, prs, W, H, LAYOUT = deck.S, deck.prs, deck.W, deck.H, deck.layout
P = C.PERSONA

Y1, Y2, Y3, G2 = "8EC5F2", "2F7FCC", "1F6FB8", "174A8B"   # light blue, main blue, label blue, deep blue
CREAM, CHAR, TEXT, GREY, LINE = "EAF2FB", "28282C", "3A3A3F", "8A8A8F", "E6E6E6"
ON = "FFFFFF"                                        # text on the blue gradient
HEAD = "Century Gothic"
HEAT = {1: "EAF2FB", 2: "C6DDF4", 3: "8FBCE9", 4: "4A90D9", 5: "1F5FA8"}
FOOT = f"{C.BUSINESS}   |   Market Research Lab   |   October 2026"

# ------------------------------------------------------------------ figures from the workbook
wb = load_workbook(workbook_path, data_only=True)


def rows_of(sheet, first_label, count, cols):
    ws = wb[sheet]
    start = next(r for r in range(1, ws.max_row + 1) if ws.cell(r, 1).value == first_label or
                 ws.cell(r, 2).value == first_label)
    out = [[ws.cell(start + i, c).value for c in cols] for i in range(count)]
    if any(v is None for row in out for v in row):
        sys.exit(f"{sheet}: missing worked-out values; run the workbook through LibreOffice first")
    return out


needs = rows_of("3 Customer Needs", C.NEEDS[0][1], len(C.NEEDS), [2, 7, 8])        # need, importance, rank
importance = {n: imp for n, imp, _rank in needs}
top5 = [n for _rank, n in sorted((rank, n) for n, _imp, rank in needs)[:5]]
scores = rows_of("5-6 Segment Scores", C.SEGMENTS[0][0], len(C.SEGMENTS), [1, 6, 7])  # segment, total, rank
total_of = {s: t for s, t, _r in scores}
TARGET = min(scores, key=lambda row: row[2])[0]
SECOND = next(s for s, _t, r in scores if r == 2)
need_row = {n[1]: n for n in C.NEEDS}


# ------------------------------------------------------------------ building blocks
def shape(s, kind, x, y, w, h, fill=None, line=None, width=1.0):
    sp = s.shapes.add_shape(kind, x, y, w, h)
    if fill:
        sp.fill.solid()
        sp.fill.fore_color.rgb = rgb(fill)
    else:
        sp.fill.background()
    if line:
        sp.line.color.rgb = rgb(line)
        sp.line.width = Pt(width)
    else:
        sp.line.fill.background()
    return sp


def gradient(sp, c1=Y2, c2=G2, angle=45):
    """Shape Fill > Gradient: two stops, main to deep blue."""
    sp.fill.gradient()
    sp.fill.gradient_angle = angle
    stops = sp.fill.gradient_stops
    stops[0].color.rgb, stops[0].position = rgb(c1), 0.0
    stops[1].color.rgb, stops[1].position = rgb(c2), 1.0
    return sp


def see_through(sp, percent):
    """Shape Fill > Transparency."""
    colour = sp._element.spPr.find(qn("a:solidFill")).find(qn("a:srgbClr"))
    colour.append(etree.fromstring(f'<a:alpha xmlns:a="{A_NS}" val="{(100 - percent) * 1000}"/>'))
    return sp


def write_in(sp, paragraphs, size, colour=CHAR, *, bold=False, align=PP_ALIGN.CENTER, font=None, margin=0.06,
             anchor=MSO_ANCHOR.MIDDLE):
    tf = sp.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = Inches(margin)
    tf.margin_top = tf.margin_bottom = Inches(0.03)
    deck.write(tf, paragraphs, size=size, colour=colour, bold=bold, align=align, font=font)
    tf.vertical_anchor = anchor
    return sp


def text(s, x, y, w, h, paragraphs, size, colour=TEXT, **fmt):
    return deck.textbox(s, x, y, w, h, paragraphs, size=size, colour=colour, **fmt)


def ring(s, cx, cy, d, label, size, filled=False):
    """A numbered circle: an outline ring, or filled with the yellow gradient."""
    c = shape(s, MSO_SHAPE.OVAL, cx - d // 2, cy - d // 2, d, d, fill=None if filled else "FFFFFF", line=Y2, width=3)
    if filled:
        gradient(c)
        c.line.fill.background()
    return write_in(c, [label], size, ON if filled else CHAR, bold=True, font=HEAD, margin=0.02)


def rings(s, cx, cy, d):
    """Decoration: two outline rings and a small solid circle."""
    return [shape(s, MSO_SHAPE.OVAL, cx - d // 2, cy - d // 2, d, d, line=Y2, width=4),
            shape(s, MSO_SHAPE.OVAL, cx - d * 7 // 20, cy - d * 7 // 20, d * 7 // 10, d * 7 // 10, line=Y1, width=2),
            gradient(shape(s, MSO_SHAPE.OVAL, cx + d * 3 // 10, cy + d * 3 // 10, d // 5, d // 5))]


def footer(s):
    text(s, Inches(0.6), H - Inches(0.45), Inches(8), Inches(0.3), [f"{C.BUSINESS}  ·  Capstone Project, Part 2"], 9,
         GREY)
    text(s, W - Inches(1.6), H - Inches(0.45), Inches(1.0), Inches(0.3), [str(len(prs.slides))], 9, GREY,
         align=PP_ALIGN.RIGHT)


def slide(title, subtitle, kicker=None, layout="Title Only"):
    """A content slide: a small yellow label, a bold charcoal title and a grey subtitle, centred."""
    s = prs.slides.add_slide(LAYOUT[layout])
    x, w = Inches(0.8), W - 2 * Inches(0.8)
    parts = []
    if kicker:
        parts.append(text(s, x, Inches(0.42), w, Inches(0.32), [kicker.upper()], 11, Y3, bold=True,
                          align=PP_ALIGN.CENTER))
    head = s.shapes.title
    place(head, x, Inches(0.7), w, Inches(0.72))
    deck.write(head.text_frame, [title], size=30, colour=CHAR, font=HEAD, bold=True, align=PP_ALIGN.CENTER)
    head.text_frame.vertical_anchor = MSO_ANCHOR.MIDDLE
    sub = text(s, x, Inches(1.42), w, Inches(0.4), [subtitle], 13, GREY, align=PP_ALIGN.CENTER)
    deck.anim(s, [head] + parts, 1)
    deck.anim(s, sub, 2)
    footer(s)
    return s, Inches(2.1)


def divider(number, title, subtitle):
    """A section divider: the number in a ring on the left, a yellow panel with the title."""
    s = prs.slides.add_slide(LAYOUT["Title Only"])
    left = shape(s, MSO_SHAPE.RECTANGLE, 0, 0, W // 2, H, fill=CREAM)
    panel = gradient(shape(s, MSO_SHAPE.RECTANGLE, W // 2, 0, W - W // 2, H), angle=60)
    for sp in (panel, left):
        to_back(sp)
    cx, cy, d = W // 4, H // 2, Inches(4.2)
    deco = [shape(s, MSO_SHAPE.OVAL, cx - d // 2, cy - d // 2, d, d, line=Y2, width=5),
            shape(s, MSO_SHAPE.OVAL, cx - d * 2 // 5, cy - d * 2 // 5, d * 4 // 5, d * 4 // 5, line=Y1, width=2),
            gradient(shape(s, MSO_SHAPE.OVAL, cx + d * 3 // 10, cy + d * 3 // 10, Inches(0.55), Inches(0.55))),
            text(s, cx - Inches(1.8), cy - Inches(1.05), Inches(3.6), Inches(2.0), [f"{int(number):02d}"], 110, Y2,
                 font=HEAD, bold=True, align=PP_ALIGN.CENTER)]
    x, w = W // 2 + Inches(0.7), W - W // 2 - Inches(1.2)
    label = text(s, x, Inches(2.2), w, Inches(0.4), [f"TASK {number} OF 6"], 13, Y1, bold=True)
    head = s.shapes.title
    place(head, x, Inches(2.6), w, Inches(1.45))
    deck.write(head.text_frame, [title], size=38, colour=ON, font=HEAD, bold=True)
    head.text_frame.vertical_anchor = MSO_ANCHOR.TOP
    bar = shape(s, MSO_SHAPE.RECTANGLE, x + Inches(0.08), Inches(4.25), Inches(1.0), Inches(0.08), fill=ON)
    sub = text(s, x, Inches(4.45), w, Inches(1.0), [subtitle], 16, ON)
    deck.anim(s, deco, 1)
    deck.anim(s, [label, head, bar], 2)
    deck.anim(s, sub, 3)
    s.notes_slide.notes_text_frame.text = f"Task {number}: {title.lower()}."
    return s


# ================================================================== Cover
s = prs.slides.add_slide(LAYOUT["Title Slide"])
block = gradient(shape(s, MSO_SHAPE.RECTANGLE, Inches(8.4), 0, W - Inches(8.4), H), angle=60)
card = shape(s, MSO_SHAPE.RECTANGLE, Inches(7.2), Inches(1.45), Inches(4.4), Inches(4.4), fill=CHAR)
for sp in (card, block):
    to_back(sp)
inner = shape(s, MSO_SHAPE.OVAL, Inches(7.75), Inches(2.0), Inches(3.3), Inches(3.3), line=Y1, width=5)
part = text(s, Inches(7.75), Inches(2.7), Inches(3.3), Inches(1.85), ["02"], 96, "FFFFFF", font=HEAD, bold=True,
            align=PP_ALIGN.CENTER)
part_label = text(s, Inches(7.2), Inches(5.95), Inches(4.4), Inches(0.4), ["CAPSTONE  ·  PART 2"], 12, ON,
                  bold=True, align=PP_ALIGN.CENTER)
kicker = text(s, Inches(0.9), Inches(1.45), Inches(5.5), Inches(0.35), ["CAPSTONE PROJECT  ·  PART 2"], 12, Y3,
              bold=True)
head, sub = placeholder(s, 0), placeholder(s, 1)
place(head, Inches(0.9), Inches(1.8), Inches(5.8), Inches(1.9))
deck.write(head.text_frame, ["Customer Analysis"], size=48, colour=CHAR, font=HEAD, bold=True, align=PP_ALIGN.LEFT)
head.text_frame.vertical_anchor = MSO_ANCHOR.BOTTOM
bar = shape(s, MSO_SHAPE.RECTANGLE, Inches(0.98), Inches(3.85), Inches(1.2), Inches(0.1), fill=Y2)
place(sub, Inches(0.9), Inches(4.1), Inches(5.6), Inches(1.0))
deck.write(sub.text_frame, [f"Persona, journey map, needs, segments and target for {C.PRODUCT}"], size=16,
           colour=GREY, align=PP_ALIGN.LEFT)
sub.text_frame.vertical_anchor = MSO_ANCHOR.TOP
foot = text(s, Inches(0.9), H - Inches(0.9), Inches(6.2), Inches(0.35), [FOOT], 11, GREY)
deck.anim(s, [block, card, inner, part, part_label], 1)
deck.anim(s, [kicker, head, bar], 2)
deck.anim(s, [sub, foot], 3)
s.notes_slide.notes_text_frame.text = (
    f"Part 2 of my capstone analyses the customers of {C.PRODUCT}, SkillUp Academy's beginner cybersecurity "
    "course: a persona, a journey map, the most important needs, four segments, their scores and the target.")

# ================================================================== Contents
s = prs.slides.add_slide(LAYOUT["Title Only"])
band = gradient(shape(s, MSO_SHAPE.RECTANGLE, W - Inches(2.9), 0, Inches(2.9), H), angle=90)
to_back(band)
vertical = text(s, W - Inches(2.9) + Inches(1.45) - Inches(3.25), H // 2 - Inches(0.3), Inches(6.5), Inches(0.6),
                ["CUSTOMER ANALYSIS"], 22, "FFFFFF", font=HEAD, bold=True, align=PP_ALIGN.CENTER)
vertical.rotation = 270
frame = shape(s, MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(0.8), Inches(3.4), Inches(0.85), line=Y2, width=2.5)
head = s.shapes.title
place(head, Inches(0.8), Inches(0.8), Inches(3.4), Inches(0.85))
deck.write(head.text_frame, ["CONTENTS"], size=24, colour=CHAR, font=HEAD, bold=True, align=PP_ALIGN.CENTER)
head.text_frame.vertical_anchor = MSO_ANCHOR.MIDDLE
deck.anim(s, [band, vertical], 1)
deck.anim(s, [frame, head], 2)
for i, (number, task, about) in enumerate(C.TASKS):
    x = Inches(0.8) + Inches(4.85) * (i % 2)
    y = Inches(2.15) + Inches(1.5) * (i // 2)
    num = text(s, x, y, Inches(1.1), Inches(0.8), [f"0{number}"], 32, Y2, font=HEAD, bold=True)
    body = text(s, x + Inches(1.15), y + Inches(0.05), Inches(3.4), Inches(1.2), [[(task, True)], about], 16, CHAR,
                after=3)
    body.text_frame.paragraphs[1].runs[0].font.size = Pt(12)
    body.text_frame.paragraphs[1].runs[0].font.color.rgb = rgb(GREY)
    deck.anim(s, [num, body], 3 + i // 2)
footer(s)
s.notes_slide.notes_text_frame.text = (
    "I answer the six tasks in the order they were set: the customer persona, the customer journey map, the five "
    "most important needs, four market segments, the segment scores and the target segment.")

# ================================================================== Key figures
s, top = slide("Key Figures", "Published world and Nigerian data behind the customer analysis", "Context")
for row, (where, filled) in enumerate((("World", True), ("Nigeria", False))):
    items = [k for k in C.KPIS if k[2] == where]
    ly = top + Inches(0.05) + Inches(2.3) * row
    group = [text(s, Inches(0.8), ly, Inches(2.0), Inches(0.35), [where.upper()], 12, Y3, bold=True),
             shape(s, MSO_SHAPE.RECTANGLE, Inches(0.85), ly + Inches(0.38), Inches(0.5), Inches(0.05), fill=Y2)]
    for i, (big, what, _where, _key) in enumerate(items):
        cx = Inches(3.0) + Inches(2.85) * i
        group += [ring(s, cx, ly + Inches(0.75), Inches(1.25), big, 18 if len(big) < 6 else 13, filled),
                  text(s, cx - Inches(1.3), ly + Inches(1.42), Inches(2.6), Inches(0.62), [what], 11, GREY,
                       align=PP_ALIGN.CENTER)]
    deck.anim(s, group, 3 + row)
s.notes_slide.notes_text_frame.text = (
    "Around the world, networks and cybersecurity is the second fastest-growing skill, and 95 percent of cyber teams "
    "have a skills gap, led by AI and cloud security. Nigeria is young, with a median age of about 19 and 2.1 "
    "million university students. The minimum wage is 70,000 naira a month; junior analysts earn 150,000 or more.")

# ================================================================== Task 1: persona
divider("1", "Customer Persona", "Who the typical buyer is, and what makes them buy")

s = prs.slides.add_slide(LAYOUT["Title Only"])
square = gradient(shape(s, MSO_SHAPE.RECTANGLE, Inches(0.7), Inches(1.55), Inches(4.0), Inches(4.9)), angle=60)
mono = shape(s, MSO_SHAPE.RECTANGLE, Inches(1.05), Inches(1.1), Inches(4.0), Inches(4.9), fill=CHAR)
initials = text(s, Inches(1.05), Inches(1.9), Inches(4.0), Inches(2.0), [P["initials"]], 110, Y1, font=HEAD, bold=True,
                align=PP_ALIGN.CENTER)
name = text(s, Inches(1.05), Inches(4.05), Inches(4.0), Inches(0.5), [P["name"]], 20, "FFFFFF", font=HEAD, bold=True,
            align=PP_ALIGN.CENTER)
seg_tag = text(s, Inches(1.05), Inches(4.55), Inches(4.0), Inches(0.36), [P["segment"].upper()], 11, Y1, bold=True,
               align=PP_ALIGN.CENTER)
deck.anim(s, [square, mono, initials, name, seg_tag], 1)
rx, rw = Inches(5.7), W - Inches(5.7) - Inches(0.7)
facts = dict(P["facts"])
kick = text(s, rx, Inches(0.9), rw, Inches(0.32), ["CUSTOMER PERSONA"], 11, Y3, bold=True)
head = s.shapes.title
place(head, rx, Inches(1.18), rw, Inches(0.75))
deck.write(head.text_frame, [f"Meet {P['name']}"], size=32, colour=CHAR, font=HEAD, bold=True)
line1 = text(s, rx, Inches(1.92), rw, Inches(0.4), [f"{facts['Age']}  ·  {facts['Job']}  ·  {facts['Lives in']}"],
             14, GREY)
deck.anim(s, [kick, head, line1], 2)
qbar = shape(s, MSO_SHAPE.RECTANGLE, rx, Inches(2.5), Inches(0.08), Inches(0.62), fill=Y2)
quote = text(s, rx + Inches(0.2), Inches(2.45), rw - Inches(0.2), Inches(0.72), [P["quote"]], 17, CHAR)
quote.text_frame.paragraphs[0].runs[0].font.italic = True
deck.anim(s, [qbar, quote], 3)
cw = (rw - Inches(0.4)) // 2
prof = [text(s, rx, Inches(3.45), cw, Inches(0.3), ["PROFILE"], 11, Y3, bold=True)]
fy = Inches(3.8)
for label in ("Education", "Money", "Devices"):
    item = text(s, rx, fy, cw, Inches(0.78), [[(label.upper(), True)], facts[label]], 12, CHAR, after=0)
    item.text_frame.paragraphs[0].runs[0].font.size = Pt(9)
    item.text_frame.paragraphs[0].runs[0].font.color.rgb = rgb(GREY)
    prof.append(item)
    fy += Inches(0.78)
deck.anim(s, prof, 4)
px = rx + cw + Inches(0.4)
pers = [text(s, px, Inches(3.45), cw, Inches(0.3), ["PERSONALITY"], 11, Y3, bold=True)]
ty = Inches(3.85)
bar_w = cw - Inches(1.95)
for trait, level in C.TRAITS:
    pers += [text(s, px, ty - Inches(0.08), Inches(1.9), Inches(0.36), [trait], 11, CHAR),
             shape(s, MSO_SHAPE.ROUNDED_RECTANGLE, px + Inches(1.95), ty, bar_w, Inches(0.16), fill="EDEDED"),
             gradient(shape(s, MSO_SHAPE.ROUNDED_RECTANGLE, px + Inches(1.95), ty, bar_w * level // 5, Inches(0.16)),
                      angle=0)]
    ty += Inches(0.45)
deck.anim(s, pers, 5, "wipe-left")
footer(s)
s.notes_slide.notes_text_frame.text = (
    f"Meet {P['name']}, a fictional customer from the target segment: 27, a customer service officer in Lagos with "
    "an HND, steady pay and about 50,000 naira a month to spare. Tunde is careful with money and ambitious, but not "
    "yet confident with tech, short of free time, and wary of online courses.")

s, top = slide("What Tunde Wants", "Goals, frustrations, needs, and where to reach Tunde", "Customer persona")
cols = (("Goals", P["goals"]), ("Frustrations", P["frustrations"]), ("Needs", P["needs"]),
        ("Channels", P["channels"]))
cw = Inches(2.75)
xs = [Inches(0.8) + (cw + Inches(0.2)) * i for i in range(4)]
link = s.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, xs[0] + cw // 2, top + Inches(0.65), xs[-1] + cw // 2,
                              top + Inches(0.65))
link.line.color.rgb = rgb(LINE)
link.line.width = Pt(2)
deck.anim(s, link, 3, "wipe-left")
for i, (heading, items) in enumerate(cols):
    x = xs[i]
    deck.anim(s, [ring(s, x + cw // 2, top + Inches(0.65), Inches(1.0), str(i + 1), 26, filled=i % 2 == 0),
                  text(s, x, top + Inches(1.3), cw, Inches(0.5), [heading], 15, CHAR, bold=True, font=HEAD,
                       align=PP_ALIGN.CENTER),
                  text(s, x + Inches(0.1), top + Inches(1.85), cw - Inches(0.2), Inches(2.6),
                       [f"•  {item}" for item in items], 13, TEXT, after=8)], 4 + i)
s.notes_slide.notes_text_frame.text = (
    "Tunde's goal is a cybersecurity job within a year. The frustrations are not knowing where to start, fear of "
    "scams, and a full-time job; Tunde needs weekend labs, a fair price in parts and help into a job.")

s, top = slide("Why Tunde Buys", "Buying triggers, objections and our answers, how Tunde chooses and pays",
               "Customer persona")
cx, cy, d = W // 2, top + Inches(2.25), Inches(3.3)
arcs = []
for start, colour in ((185, Y1), (275, Y2), (5, G2), (95, CHAR)):
    arc = shape(s, MSO_SHAPE.BLOCK_ARC, cx - d // 2, cy - d // 2, d, d, fill=colour)
    arc.adjustments[0] = start * 0.6
    arc.adjustments[1] = ((start + 80) % 360) * 0.6
    arc.adjustments[2] = 0.18
    arcs.append(arc)
centre = write_in(shape(s, MSO_SHAPE.OVAL, cx - Inches(0.95), cy - Inches(0.95), Inches(1.9), Inches(1.9),
                        fill="FFFFFF"), [[("WHY", True)], [("TUNDE", True)], [("BUYS", True)]], 15, CHAR, font=HEAD)
deck.anim(s, arcs + [centre], 3)
blocks = (("Buying triggers", P["triggers"], Inches(0.8), top + Inches(0.1)),
          ("Objections, and our answer", P["objections"], W - Inches(4.6), top + Inches(0.1)),
          ("How Tunde chooses", P["criteria"], Inches(0.8), top + Inches(2.45)),
          ("How Tunde pays", P["payment"], W - Inches(4.6), top + Inches(2.45)))
for k, (heading, items, x, y) in enumerate(blocks):
    right = x > W // 2
    deck.anim(s, [text(s, x, y, Inches(3.8), Inches(0.42), [heading], 16, CHAR, bold=True, font=HEAD,
                       align=PP_ALIGN.LEFT if right else PP_ALIGN.RIGHT),
                  text(s, x, y + Inches(0.45), Inches(3.8), Inches(1.8), items, 12, TEXT, after=5,
                       align=PP_ALIGN.LEFT if right else PP_ALIGN.RIGHT)], 4 + k)
s.notes_slide.notes_text_frame.text = (
    "Breach news, a friend's new tech job, or a free first class push Tunde to act. Each worry has an answer. "
    "Tunde chooses on labs, the full price, reviews and the certificate, and pays from salary in three parts.")

# ================================================================== Task 2: journey map
divider("2", "Customer Journey Map", "From first hearing about the course to a new job")

s, top = slide("Tunde's Journey", "What Tunde does at each stage, where, what Tunde thinks, and how it feels "
                                  "(the curve: 1 low to 5 high)", "Customer journey map")
journey = dict(C.JOURNEY)
cw = Inches(2.35)
xs = [Inches(0.8) + cw * i + cw // 2 for i in range(5)]
pills = []
for x, stage in zip(xs, C.STAGES):
    p = write_in(gradient(shape(s, MSO_SHAPE.ROUNDED_RECTANGLE, x - Inches(1.05), top, Inches(2.1), Inches(0.42)),
                          angle=0), [stage], 13, ON, bold=True)
    p.adjustments[0] = 0.5
    pills.append(p)
deck.anim(s, pills, 3)
ys = [top + Inches(1.3) - (v - 3) * Inches(0.32) for v in C.FEELING]
curve = []
for (xa, ya), (xb, yb) in zip(zip(xs, ys), list(zip(xs, ys))[1:]):
    seg = s.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, xa, ya, xb, yb)
    seg.line.color.rgb = rgb(CHAR)
    seg.line.width = Pt(2)
    curve.append(seg)
for x, y, v, thought in zip(xs, ys, C.FEELING, journey["Thinking and feeling"]):
    curve += [ring(s, x, y, Inches(0.62), str(v), 16, filled=True),
              text(s, x - Inches(1.15), y + Inches(0.36), Inches(2.3), Inches(0.62), [thought], 10, GREY,
                   align=PP_ALIGN.CENTER)]
deck.anim(s, curve, 4, "wipe-left")
by = top + Inches(2.75)
rows = [shape(s, MSO_SHAPE.RECTANGLE, Inches(0.8), by - Inches(0.08), W - Inches(1.6), Inches(0.03), fill=LINE)]
for x, doing, where in zip(xs, journey["Doing"], journey["Touchpoints"]):
    t = text(s, x - Inches(1.1), by, Inches(2.2), Inches(1.6), [[(doing, True)], f"Where: {where}"], 11, CHAR, after=5,
             align=PP_ALIGN.CENTER)
    t.text_frame.paragraphs[1].runs[0].font.color.rgb = rgb(GREY)
    rows.append(t)
deck.anim(s, rows, 5)
s.notes_slide.notes_text_frame.text = (
    "The map follows Tunde through five stages: awareness, consideration, purchase, learning and after the course. "
    "Tunde starts curious, is most anxious when comparing courses, gains confidence while learning, and ends proud "
    "on getting a job.")

s, top = slide("Every Pain Point Is an Opportunity", "What goes wrong at each stage, and what SkillUp Academy will do",
               "Customer journey map")
cw, gap = Inches(2.25), Inches(0.17)
for i, stage in enumerate(C.STAGES):
    x = Inches(0.8) + (cw + gap) * i
    head_pill = write_in(shape(s, MSO_SHAPE.ROUNDED_RECTANGLE, x, top, cw, Inches(0.42), fill=CHAR), [stage], 13,
                         "FFFFFF", bold=True)
    head_pill.adjustments[0] = 0.5
    pain = write_in(shape(s, MSO_SHAPE.RECTANGLE, x, top + Inches(0.6), cw, Inches(1.45), fill="F2F2F2"),
                    [[("PAIN POINT", True)], journey["Pain points"][i]], 13, TEXT, align=PP_ALIGN.LEFT, margin=0.15,
                    anchor=MSO_ANCHOR.TOP)
    pain.text_frame.paragraphs[0].runs[0].font.size = Pt(9)
    pain.text_frame.paragraphs[0].runs[0].font.color.rgb = rgb(GREY)
    arrow = shape(s, MSO_SHAPE.DOWN_ARROW, x + cw // 2 - Inches(0.2), top + Inches(2.15), Inches(0.4), Inches(0.42),
                  fill=Y2)
    opp = write_in(gradient(shape(s, MSO_SHAPE.RECTANGLE, x, top + Inches(2.7), cw, Inches(1.95)), angle=60),
                   [[("OPPORTUNITY", True)], journey["Opportunities"][i]], 14, ON, align=PP_ALIGN.LEFT, margin=0.15,
                   anchor=MSO_ANCHOR.TOP)
    opp.text_frame.paragraphs[0].runs[0].font.size = Pt(9)
    deck.anim(s, [head_pill, pain, arrow, opp], 3 + i)
s.notes_slide.notes_text_frame.text = (
    "Each pain point is an opportunity: beginner videos for awareness, clear prices and reviews for consideration, "
    "a free class and instalments for purchase, weekly labs and fast support for learning, and job help after.")

# ================================================================== Task 3: needs
divider("3", "The 5 Most Important Needs", "Chosen from 12 functional, economic, emotional and social needs")

s, top = slide("Four Kinds of Needs", "Three needs of each type, each scored for importance (of 25); "
                                      "dark badges mark the top five", "The 5 most important needs")
about = {"Functional": "what the course does", "Economic": "money", "Emotional": "feelings", "Social": "other people"}
cw, ch, gap = (W - Inches(1.6) - Inches(0.3)) // 2, Inches(2.15), Inches(0.3)
for i, kind in enumerate(C.NEED_TYPES):
    x = Inches(0.8) + (cw + gap) * (i % 2)
    y = top + (ch + Inches(0.2)) * (i // 2)
    card = [gradient(shape(s, MSO_SHAPE.RECTANGLE, x, y, cw, ch), angle=45) if i in (0, 3) else
            shape(s, MSO_SHAPE.RECTANGLE, x, y, cw, ch, fill=CREAM),
            text(s, x + Inches(0.3), y + Inches(0.15), cw - Inches(0.6), Inches(0.48),
                 [[(f"{kind} needs", True), (f"   {about[kind]}", False)]], 16, ON if i in (0, 3) else CHAR,
                 font=HEAD)]
    card[-1].text_frame.paragraphs[0].runs[1].font.size = Pt(11)
    card[-1].text_frame.paragraphs[0].runs[1].font.color.rgb = rgb("DCEBFA" if i in (0, 3) else TEXT)
    ny = y + Inches(0.7)
    for need in [n for n in C.NEEDS if n[0] == kind]:
        top_need = need[1] in top5
        badge = write_in(shape(s, MSO_SHAPE.OVAL, x + cw - Inches(0.8), ny, Inches(0.42), Inches(0.42),
                               fill=CHAR if top_need else "FFFFFF"), [str(importance[need[1]])], 11,
                         "FFFFFF" if top_need else CHAR, bold=True, margin=0.0)
        card += [text(s, x + Inches(0.3), ny, cw - Inches(1.2), Inches(0.42), [need[1]], 14,
                      ON if i in (0, 3) else CHAR, bold=top_need),
                 badge]
        ny += Inches(0.46)
    deck.anim(s, card, 3 + i)
s.notes_slide.notes_text_frame.text = (
    "Functional needs are about what the course does, economic needs about money, emotional needs about feelings, "
    "and social needs about other people. The dark badges mark the five most important.")

s, top = slide("The 5 Most Important Needs", "Importance = how often it came up in the research × its effect on "
                                             "buying (of 25)", "The 5 most important needs")
cx, cy, r_out = W // 2, H - Inches(0.75), Inches(2.45)
arcs = []
for k, colour in enumerate((G2, Y2, Y1, Y2, G2)):
    start = 180 + k * 36 + 2
    arc = shape(s, MSO_SHAPE.BLOCK_ARC, cx - r_out, cy - r_out, 2 * r_out, 2 * r_out, fill=colour)
    arc.adjustments[0] = start * 0.6
    arc.adjustments[1] = (start + 32) * 0.6
    arc.adjustments[2] = 0.2
    arcs.append(arc)
core = text(s, cx - Inches(1.4), cy - Inches(1.15), Inches(2.8), Inches(0.9), [[("TOP 5", True)], "needs"], 22, CHAR,
            font=HEAD, align=PP_ALIGN.CENTER, after=0)
core.text_frame.paragraphs[1].runs[0].font.size = Pt(14)
core.text_frame.paragraphs[1].runs[0].font.color.rgb = rgb(GREY)
deck.anim(s, arcs + [core], 3)
spots = [(Inches(0.8), Inches(4.85)), (Inches(1.3), Inches(2.55)), (cx - Inches(1.6), top - Inches(0.05)),
         (W - Inches(4.5), Inches(2.55)), (W - Inches(4.0), Inches(4.85))]
for k, (name, (x, y)) in enumerate(zip(top5, spots)):
    kind = need_row[name][0]
    lab = text(s, x, y, Inches(3.3), Inches(1.05),
               [[(f"0{k + 1}  ", True), (name, True)], f"{kind}  ·  {importance[name]} of 25"], 14, CHAR, after=2,
               align=PP_ALIGN.CENTER if k == 2 else (PP_ALIGN.RIGHT if k < 2 else PP_ALIGN.LEFT))
    lab.text_frame.paragraphs[0].runs[0].font.color.rgb = rgb(Y3)
    lab.text_frame.paragraphs[1].runs[0].font.size = Pt(11)
    lab.text_frame.paragraphs[1].runs[0].font.color.rgb = rgb(GREY)
    deck.anim(s, lab, 4 + k)
s.notes_slide.notes_text_frame.text = (
    "The five most important needs are hands-on skills and an affordable price, both 25 out of 25, then certificate "
    "preparation, a better-paid job and feeling supported, each 20: two functional, two economic and one emotional.")

s, top = slide("All Twelve Needs, Scored", "Importance of each need (of 25); the top five in blue",
               "The 5 most important needs", layout="Title and Content")
frame, chart = deck.bar_chart(s, placeholder(s, 1), Inches(0.8), top - Inches(0.05), Inches(7.6), Inches(4.75),
                              [n[2] for n in C.NEEDS], [importance[n[1]] for n in C.NEEDS], number_format="0",
                              maximum=25, top=[i for i, n in enumerate(C.NEEDS) if n[1] in top5])
chart.category_axis.tick_labels.font.size = Pt(13)
chart.plots[0].data_labels.font.size = Pt(13)
deck.anim(s, frame, 3, "wipe-left")
note = write_in(gradient(shape(s, MSO_SHAPE.RECTANGLE, Inches(8.8), top + Inches(0.2), W - Inches(9.6),
                               Inches(4.2)), angle=60),
                [[("Skills and money", True)], "matter most: two functional, two economic and one emotional need make "
                                               "the top five.", [("Social needs", True)],
                 "score lowest, but still shape how the brand talks to people."], 15, ON, align=PP_ALIGN.LEFT,
                margin=0.3)
deck.anim(s, note, 4)
s.notes_slide.notes_text_frame.text = (
    "The chart shows all twelve needs. Skills and money matter most; social needs matter less, but still shape how "
    "the brand talks to people.")

# ================================================================== Task 4: segments
divider("4", "Four Market Segments", "Demographic, geographic, psychographic and behavioural")

s, top = slide("Four Market Segments", "Each segment on the four bases: demographic, geographic, psychographic and "
                                       "behavioural", "Four market segments")
cw, gap = Inches(2.78), Inches(0.2)
for i, seg in enumerate(C.SEGMENTS):
    x = Inches(0.8) + (cw + gap) * i
    is_target = seg[0] == TARGET
    tile = shape(s, MSO_SHAPE.RECTANGLE, x, top - Inches(0.1), cw, Inches(1.25), fill=CHAR if is_target else None)
    if not is_target:
        gradient(tile, angle=60)
    card = [tile,
            text(s, x + Inches(0.2), top - Inches(0.05), Inches(1.6), Inches(0.9), [f"0{i + 1}"], 40,
                 Y1 if is_target else ON, font=HEAD, bold=True),
            text(s, x + Inches(0.2), top + Inches(0.72), cw - Inches(0.3), Inches(0.4),
                 ["TARGET SEGMENT" if is_target else "SEGMENT"], 10, Y1 if is_target else ON, bold=True),
            text(s, x, top + Inches(1.22), cw, Inches(0.42), [seg[0]], 13, CHAR, bold=True, font=HEAD),
            text(s, x, top + Inches(1.62), cw, Inches(0.46), [seg[5]], 10, Y3, bold=True)]
    by = top + Inches(2.1)
    for b, (base, _about) in enumerate(C.BASES):
        part = text(s, x, by, cw, Inches(0.66), [[(base.upper(), True)], seg[1 + b]], 10.5, TEXT, after=0)
        part.text_frame.paragraphs[0].runs[0].font.size = Pt(8.5)
        part.text_frame.paragraphs[0].runs[0].font.color.rgb = rgb(GREY)
        card.append(part)
        by += Inches(0.66)
    card.append(shape(s, MSO_SHAPE.RECTANGLE, x, by + Inches(0.02), cw, Inches(0.07), fill=Y2 if is_target else LINE))
    deck.anim(s, card, 3 + i)
s.notes_slide.notes_text_frame.text = (
    "The four segments are Campus Starters, students and new graduates; Career Switchers, working adults in non-IT "
    "jobs; Corporate Upskillers, staff whose employers pay; and Women in Tech Starters.")

# ================================================================== Task 5: scores
divider("5", "Segment Scores", "Market size, accessibility, buying potential and competition")

s, top = slide(f"{TARGET} Score Highest", "Scores 1 (low) to 5 (high), deeper blue = better; for competition, "
                                          "5 = little competition", "Segment scores")
widths = [Inches(3.0)] + [Inches(1.75)] * 4 + [Inches(1.95)]
xs = [Inches(0.8) + sum(widths[:i], Emu(0)) for i in range(len(widths))]
head_h, row_h = Inches(0.68), Inches(0.9)
heads = [["Segment"]] + [[c, f"{int(w * 100)}%"] for c, w in C.CRITERIA] + [["Weighted score"]]
cells = []
for i, (x, w, label) in enumerate(zip(xs, widths, heads)):
    cell = write_in(shape(s, MSO_SHAPE.RECTANGLE, x, top, w, head_h, fill=CHAR, line="FFFFFF", width=1.5), label, 13,
                    "FFFFFF", bold=True, align=PP_ALIGN.LEFT if i == 0 else PP_ALIGN.CENTER, margin=0.15)
    if len(label) > 1:
        cell.text_frame.paragraphs[1].runs[0].font.color.rgb = rgb(Y1)
    cells.append(cell)
deck.anim(s, cells, 3)
for r, (seg, sc) in enumerate(zip(C.SEGMENTS, C.SCORES)):
    y = top + head_h + row_h * r
    is_target = seg[0] == TARGET
    total = total_of[seg[0]]
    row = [write_in(shape(s, MSO_SHAPE.RECTANGLE, xs[0], y, widths[0], row_h, fill=CREAM if is_target else "FFFFFF",
                          line=LINE), [seg[0]], 15, CHAR, bold=True, align=PP_ALIGN.LEFT, margin=0.2)]
    row += [write_in(shape(s, MSO_SHAPE.RECTANGLE, xs[1 + c], y, widths[1 + c], row_h, fill=HEAT[v], line="FFFFFF",
                           width=1.5), [str(v)], 22, ON if v >= 4 else CHAR, bold=True, font=HEAD)
            for c, v in enumerate(sc)]
    row += [shape(s, MSO_SHAPE.RECTANGLE, xs[-1], y, widths[-1], row_h, fill="FFFFFF", line=LINE),
            text(s, xs[-1], y + Inches(0.05), widths[-1], Inches(0.48), [f"{total:.2f}"], 18, CHAR, bold=True,
                 font=HEAD, align=PP_ALIGN.CENTER),
            shape(s, MSO_SHAPE.RECTANGLE, xs[-1] + Inches(0.2), y + Inches(0.6),
                  int((widths[-1] - Inches(0.4)) * total / 5), Inches(0.14), fill=Y2 if is_target else "D0D0D0")]
    deck.anim(s, row, 4 + r)
deck.anim(s, text(s, Inches(0.8), top + head_h + row_h * 4 + Inches(0.15), W - Inches(1.6), Inches(0.35),
                  ["Weighted score (of 5) = SUMPRODUCT of the weights and the scores, worked out in Excel."], 11, GREY),
          8)
s.notes_slide.notes_text_frame.text = (
    f"Each segment is scored on market size, accessibility, buying potential and competition. {TARGET} score "
    f"{total_of[TARGET]:.2f}, the highest, with four on every criterion. {SECOND} are biggest but have little money.")

# ================================================================== Task 6: target
divider("6", "Target Segment", "The segment the business should prioritise")

s = prs.slides.add_slide(LAYOUT["Title Only"])
blobs = []
for (cx, cy), colour, label, (lx, ly) in (((Inches(2.75), Inches(3.4)), Y1, "Can pay", (-0.95, -0.55)),
                                          ((Inches(4.45), Inches(3.4)), Y2, "Reason to buy", (-0.3, -0.55)),
                                          ((Inches(3.6), Inches(4.85)), G2, "Easy to reach", (-0.7, 0.75))):
    d = Inches(2.5)
    blobs.append(see_through(shape(s, MSO_SHAPE.OVAL, cx - d // 2, cy - d // 2, d, d, fill=colour), 15))
    blobs.append(text(s, cx + Inches(lx), cy + Inches(ly), Inches(1.4), Inches(0.36), [label], 12,
                      CHAR if colour == Y1 else ON, bold=True, align=PP_ALIGN.CENTER))
centre = write_in(shape(s, MSO_SHAPE.OVAL, Inches(3.0), Inches(3.3), Inches(1.2), Inches(1.2), fill=CHAR),
                  [f"{total_of[TARGET]:.2f}"], 20, "FFFFFF", bold=True, font=HEAD)
deck.anim(s, blobs + [centre], 1)
rx, rw = Inches(6.6), W - Inches(6.6) - Inches(0.7)
kick = text(s, rx, Inches(0.9), rw, Inches(0.32), ["TARGET SEGMENT"], 11, Y3, bold=True)
head = s.shapes.title
place(head, rx, Inches(1.18), rw, Inches(0.75))
deck.write(head.text_frame, [f"Prioritise {TARGET}"], size=24, colour=CHAR, font=HEAD, bold=True)
sub = text(s, rx, Inches(1.92), rw, Inches(0.4), [f"Score {total_of[TARGET]:.2f} of 5, the highest of the four"], 14,
           GREY)
deck.anim(s, [kick, head, sub], 2)
reasons = [("Who", "working adults of 25 to 35 in non-IT jobs, in Lagos, Abuja and Port Harcourt"),
           ("Can pay", "steady pay above the ₦70,000 minimum wage; ₦50,000 a month in 3 parts"),
           ("Strong reason to buy", "a junior analyst job pays about ₦150,000 to ₦300,000 a month"),
           ("Easy to reach", "Google, Facebook, LinkedIn and WhatsApp; evening and weekend classes"),
           ("Little competition", "few practical, mid-price courses fit around a full-time job")]
for k, (title, why) in enumerate(reasons):
    y = Inches(2.6) + Inches(0.8) * k
    deck.anim(s, [ring(s, rx + Inches(0.28), y + Inches(0.3), Inches(0.52), str(k + 1), 15, filled=k % 2 == 0),
                  text(s, rx + Inches(0.75), y - Inches(0.04), rw - Inches(0.75), Inches(0.8), [[(title, True)], why],
                       13, TEXT, after=0)], 3 + k)
footer(s)
s.notes_slide.notes_text_frame.text = (
    f"SkillUp Academy should prioritise {TARGET}. They can pay in parts, have a strong reason to buy, are easy to "
    "reach online, and few rivals offer practical courses that fit around a job.")

# ================================================================== Key findings
s, top = slide("Key Findings", "What the customer analysis shows", "Conclusion")
low = C.STAGES[C.FEELING.index(min(C.FEELING))]
findings = [("Top need", "Hands-on skills", f"{importance[top5[0]]} of 25, level with an affordable price"),
            ("Target segment", TARGET, f"{total_of[TARGET]:.2f} of 5, ahead of {SECOND} ({total_of[SECOND]:.2f})"),
            ("Persona", "Tunde, 27", "Customer service officer in Lagos who wants a cyber job within a year"),
            ("Journey low point", low, "Fear of scams and hidden prices: fix with clear prices, reviews, a free class")]
cw = Inches(2.75)
for i, (label, value, why) in enumerate(findings):
    x = Inches(0.8) + (cw + Inches(0.2)) * i
    deck.anim(s, [ring(s, x + cw // 2, top + Inches(0.75), Inches(1.15), f"0{i + 1}", 24, filled=i % 2 == 1),
                  text(s, x, top + Inches(1.5), cw, Inches(0.32), [label.upper()], 10, Y3, bold=True,
                       align=PP_ALIGN.CENTER),
                  text(s, x, top + Inches(1.82), cw, Inches(0.5), [value], 18, CHAR, bold=True, font=HEAD,
                       align=PP_ALIGN.CENTER),
                  text(s, x + Inches(0.1), top + Inches(2.35), cw - Inches(0.2), Inches(1.4), [why], 13, GREY,
                       align=PP_ALIGN.CENTER)], 3 + i)
s.notes_slide.notes_text_frame.text = (
    f"In short: customers need hands-on skills at a fair price; SkillUp Academy should target {TARGET}, like Tunde; "
    "and the weakest point of the journey, choosing a course, is fixed with clear prices, reviews and a free class.")

# ================================================================== Thank you
s = prs.slides.add_slide(LAYOUT["Title Slide"])
panel = gradient(shape(s, MSO_SHAPE.RECTANGLE, 0, 0, W // 2, H), angle=60)
right = shape(s, MSO_SHAPE.RECTANGLE, W // 2, 0, W - W // 2, H, fill=CREAM)
for sp in (right, panel):
    to_back(sp)
deco = rings(s, W * 3 // 4, H // 2, Inches(4.2))
head, sub = placeholder(s, 0), placeholder(s, 1)
place(head, Inches(0.9), Inches(2.3), W // 2 - Inches(1.5), Inches(1.3))
deck.write(head.text_frame, ["Thank You"], size=54, colour=ON, font=HEAD, bold=True, align=PP_ALIGN.LEFT)
head.text_frame.vertical_anchor = MSO_ANCHOR.BOTTOM
bar = shape(s, MSO_SHAPE.RECTANGLE, Inches(0.98), Inches(3.75), Inches(1.2), Inches(0.1), fill=ON)
place(sub, Inches(0.9), Inches(4.0), W // 2 - Inches(1.5), Inches(0.6))
deck.write(sub.text_frame, ["Any questions?"], size=20, colour=ON, align=PP_ALIGN.LEFT)
foot = text(s, Inches(0.9), H - Inches(0.9), W // 2 - Inches(1.2), Inches(0.35), [FOOT], 10, ON)
deck.anim(s, deco, 1)
deck.anim(s, [head, bar], 2)
deck.anim(s, [sub, foot], 3)
s.notes_slide.notes_text_frame.text = "Thank you for listening."

deck.save(out_path, title=f"Capstone Part 2: Customer Analysis for {C.PRODUCT}",
          subject="Customer persona, journey map, the 5 most important needs, four segments, scores and target",
          keywords="customer persona, customer journey map, customer needs, segmentation, target segment")
