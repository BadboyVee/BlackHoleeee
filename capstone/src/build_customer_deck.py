#!/usr/bin/env python3
"""Build the capstone part 2 deck: the customer analysis for CyberStart, as a visual report made
the way it would be in PowerPoint 2013, in the navy report design of
../../assignment/src/deck_kit.py with a picture on the cover.

Usage: python build_customer_deck.py Customer_Analysis.xlsx template.pptx cover.jpg STYLE out.pptx
  The workbook must have been through LibreOffice (build.sh does this), so the worked-out
  figures (need importance and ranks, segment scores, the target) can be read from it. cover.jpg
  (make_network.py) is the picture behind the cover, the section dividers and the last slide.

The slides follow the tasks in the order they were set, each opened by a divider with its number:
cover, contents, key figures; 1 the persona (profile and personality, goals and frustrations,
what makes them buy); 2 the customer journey map and its pain points and opportunities; 3 the
twelve needs by type, the five most important, and a bar chart of all twelve; 4 the four
segments as profile cards; 5 the segment scores as a heat map; 6 the target segment; then the
key findings and thank you. Shapes, not pictures, so everything stays editable; every slide's
objects come in by themselves (the plan is saved as out.anim.json for finish_deck.py).
"""
import sys

from openpyxl import load_workbook
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Emu, Inches, Pt

import customer_data as C
from deck_kit import Deck, placeholder, rgb, to_back

workbook_path, template_path, cover_path, style_name, out_path = sys.argv[1:6]
deck = Deck(style_name, template_path, cover_path)
S, prs, W, H, LAYOUT = deck.S, deck.prs, deck.W, deck.H, deck.layout
deck.footer = f"{C.BUSINESS}  ·  Capstone Project, Part 2"
P = C.PERSONA
FOOT = f"{C.BUSINESS}   |   Market Research Lab   |   October 2026"

# colours: the navy report, plus one colour for each need type and segment
NAVY, BLUE, TEAL, CORAL, AMBER = S["head_fill"], "1F6FB2", "168277", "D1462F", "F4A259"
LIGHT, GRID, INK, MUTED = "F3F5F8", S["grid"], S["text"], S["muted"]
TYPE_COLOUR = {"Functional": BLUE, "Economic": TEAL, "Emotional": CORAL, "Social": AMBER}
SEG_COLOUR = [BLUE, TEAL, AMBER, CORAL]
HEAT = {1: "EEF3F9", 2: "D3E2F2", 3: "A6C3E5", 4: "5B8FCC", 5: "1F5FA8"}


def on(colour):
    """Text colour that reads on a fill."""
    return INK if colour in (AMBER, LIGHT, "FFFFFF", "DCE7F5", "E3E8EF", HEAT[1], HEAT[2], HEAT[3]) else "FFFFFF"


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
def shape(s, kind, x, y, w, h, fill=None, line=None, width=0.75):
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


def text_in(sp, paragraphs, size, colour, *, bold=False, align=None, anchor=MSO_ANCHOR.MIDDLE, margin=0.08):
    """Type into a shape, with small even margins."""
    tf = sp.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = Inches(margin)
    tf.margin_top = tf.margin_bottom = Inches(0.03)
    deck.write(tf, paragraphs, size=size, colour=colour, bold=bold, align=align)
    tf.vertical_anchor = anchor
    return sp


def box(s, x, y, w, h, paragraphs, size, colour=None, **fmt):
    return deck.textbox(s, x, y, w, h, paragraphs, size=size, colour=colour or INK, **fmt)


def pill(s, x, y, w, h, text, fill, size=10):
    p = shape(s, MSO_SHAPE.ROUNDED_RECTANGLE, x, y, w, h, fill=fill)
    p.adjustments[0] = 0.5
    return text_in(p, [text], size, on(fill), bold=True, align=PP_ALIGN.CENTER, margin=0.04)


def circle(s, cx, cy, d, fill, label=None, size=14, line=None):
    c = shape(s, MSO_SHAPE.OVAL, cx - d // 2, cy - d // 2, d, d, fill=fill, line=line, width=1.5)
    if label is not None:
        text_in(c, [label], size, on(fill), bold=True, align=PP_ALIGN.CENTER, margin=0.02)
    return c


def band_card(s, x, y, w, h, heading, items, colour, size=14):
    """A white card with a coloured heading band and bulleted lines."""
    body = shape(s, MSO_SHAPE.RECTANGLE, x, y, w, h, fill="FFFFFF", line=GRID)
    band = text_in(shape(s, MSO_SHAPE.RECTANGLE, x, y, w, Inches(0.5), fill=colour), [heading], 15, on(colour),
                   bold=True, margin=0.18)
    lines = box(s, x + Inches(0.15), y + Inches(0.62), w - Inches(0.3), h - Inches(0.7),
                [f"•  {item}" for item in items], size, after=6)
    return [body, band, lines]


def content_slide(title, subtitle, kicker, keep_placeholder=False):
    s = prs.slides.add_slide(LAYOUT["Title and Content"])
    top = deck.content(s, title, subtitle, kicker=kicker)
    deck.anim_chrome(s)
    if not keep_placeholder:                             # drawn with shapes, so no content placeholder
        ph = placeholder(s, 1)
        ph._element.getparent().remove(ph._element)
    return s, top


def divider(number, title, subtitle):
    """A section divider on the cover picture: the task number, large, and its title."""
    s = prs.slides.add_slide(LAYOUT["Title Slide"])
    deck.title_card(s, title, [subtitle, FOOT], size=48, kicker=f"Task {number} of 6")
    deck.anim_chrome(s, title_card=True)
    big = box(s, W - Inches(5.6), Inches(1.3), Inches(4.6), Inches(3.6), [f"{int(number):02d}"], 200, "24598F",
              font=S["head_font"], align=PP_ALIGN.RIGHT)
    to_back(big)                                         # a watermark behind the title
    deck.anim(s, big, 1)
    s.notes_slide.notes_text_frame.text = f"Task {number}: {title.lower()}."
    return s


# ================================================================== Cover
s = prs.slides.add_slide(LAYOUT["Title Slide"])
deck.title_card(s, "Customer Analysis", [f"Persona, journey map, needs, segments and target for {C.PRODUCT}",
                                         FOOT], size=54, kicker="Capstone Project  ·  Part 2")
deck.anim_chrome(s, title_card=True)
s.notes_slide.notes_text_frame.text = (
    f"Part 2 of my capstone analyses the customers of {C.PRODUCT}, SkillUp Academy's beginner cybersecurity "
    "course: a persona, a journey map, the most important needs, four segments, their scores and the target.")

# ================================================================== Contents
s, top = content_slide("Six tasks, in the order they were set", f"{C.PRODUCT}, {C.PRODUCT_LINE}", "Contents")
gap = Inches(0.25)
cw = (W - 2 * deck.left - 2 * gap) // 3
ch = (H - top - Inches(0.8) - gap) // 2
task_colours = [BLUE, TEAL, CORAL, AMBER, NAVY, BLUE]
for i, (number, task, about) in enumerate(C.TASKS):
    x = deck.left + (cw + gap) * (i % 3)
    y = top + (ch + gap) * (i // 3)
    tile = [shape(s, MSO_SHAPE.RECTANGLE, x, y, cw, ch, fill="FFFFFF", line=GRID),
            shape(s, MSO_SHAPE.RECTANGLE, x, y, cw, Inches(0.1), fill=task_colours[i]),
            circle(s, x + Inches(0.6), y + Inches(0.75), Inches(0.75), task_colours[i], number, 24)]
    words = box(s, x + Inches(1.15), y + Inches(0.4), cw - Inches(1.3), ch - Inches(0.5), [[(task, True)], about], 16,
                after=4)
    words.text_frame.paragraphs[0].runs[0].font.color.rgb = rgb(NAVY)
    words.text_frame.paragraphs[1].runs[0].font.size = Pt(13)
    words.text_frame.paragraphs[1].runs[0].font.color.rgb = rgb(MUTED)
    deck.anim(s, tile + [words], 3 + i // 3)
s.notes_slide.notes_text_frame.text = (
    "I answer the six tasks in the order they were set: the customer persona, the customer journey map, the five "
    "most important needs, four market segments, the segment scores and the target segment.")

# ================================================================== Key figures
s, top = content_slide("Cyber skills are in demand worldwide, and Nigeria is young",
                       "Key figures behind the analysis, from published world and Nigerian data", "Context")
gap = Inches(0.22)
cw = (W - 2 * deck.left - 3 * gap) // 4
ch = (H - top - Inches(0.95) - gap) // 2
for i, (big, what, where, _key) in enumerate(C.KPIS):
    x = deck.left + (cw + gap) * (i % 4)
    y = top + (ch + gap) * (i // 4)
    colour = BLUE if where == "World" else TEAL
    deck.anim(s, [shape(s, MSO_SHAPE.RECTANGLE, x, y, cw, ch, fill="FFFFFF", line=GRID),
                  shape(s, MSO_SHAPE.RECTANGLE, x, y, Inches(0.08), ch, fill=colour),
                  pill(s, x + cw - Inches(1.05), y + Inches(0.15), Inches(0.9), Inches(0.28), where.upper(), colour, 9),
                  box(s, x + Inches(0.2), y + Inches(0.42), cw - Inches(0.3), Inches(0.75), [big], 32, NAVY, bold=True),
                  box(s, x + Inches(0.2), y + Inches(1.15), cw - Inches(0.3), ch - Inches(1.2), [what], 13, MUTED)],
              3 + i // 4)
deck.anim(s, deck.footnote(s, H - Inches(0.85), "Sources: World Economic Forum, ISC2, NUC, UN and World Bank data, "
                                               "payroll and career guides (full list in Excel)."), 5)
s.notes_slide.notes_text_frame.text = (
    "Around the world, networks and cybersecurity is the second fastest-growing skill, and 95 percent of cyber teams "
    "have a skills gap, led by AI and cloud security. Nigeria is young, with a median age of about 19 and 2.1 "
    "million university students. The minimum wage is 70,000 naira a month; junior analysts earn 150,000 or more.")

# ================================================================== Task 1: persona
divider("1", "Customer Persona", "Who the typical buyer is, and what makes them buy")

s, top = content_slide(f"Meet Tunde, a typical {TARGET[:-1]}",
                       f"A fictional {TARGET[:-1]} (the target segment, task 6), built from the research",
                       "1  ·  Customer persona")
y0, ph = top, H - top - Inches(0.75)
lw = Inches(3.9)                                         # left: the person
cx = deck.left + lw // 2
person = [shape(s, MSO_SHAPE.RECTANGLE, deck.left, y0, lw, ph, fill=NAVY),
          circle(s, cx, y0 + Inches(1.15), Inches(1.75), "DCE7F5"),
          circle(s, cx, y0 + Inches(0.86), Inches(0.62), BLUE)]
torso = shape(s, MSO_SHAPE.ROUND_2_SAME_RECTANGLE, cx - Inches(0.55), y0 + Inches(1.25), Inches(1.1), Inches(0.62),
              fill=BLUE)
torso.adjustments[0] = 0.45
quote = box(s, deck.left + Inches(0.3), y0 + Inches(3.2), lw - Inches(0.6), ph - Inches(3.3), [P["quote"]], 16,
            "DCE7F5", align=PP_ALIGN.CENTER)
quote.text_frame.paragraphs[0].runs[0].font.italic = True
person += [torso,
           box(s, deck.left + Inches(0.2), y0 + Inches(2.15), lw - Inches(0.4), Inches(0.5), [P["name"]], 24, "FFFFFF",
               bold=True, align=PP_ALIGN.CENTER),
           pill(s, cx - Inches(0.95), y0 + Inches(2.72), Inches(1.9), Inches(0.32), P["segment"].upper(), TEAL, 10),
           quote]
deck.anim(s, person, 3)
mx, mw = deck.left + lw + Inches(0.25), Inches(4.0)    # middle: the profile
mid = [shape(s, MSO_SHAPE.RECTANGLE, mx, y0, mw, ph, fill="FFFFFF", line=GRID),
       box(s, mx + Inches(0.25), y0 + Inches(0.15), mw - Inches(0.5), Inches(0.4), ["PROFILE"], 12, BLUE, bold=True)]
fy = y0 + Inches(0.6)
for label, value in P["facts"]:
    fact = box(s, mx + Inches(0.25), fy, mw - Inches(0.5), Inches(0.66), [[(label.upper(), True)], value], 12, after=0)
    fact.text_frame.paragraphs[0].runs[0].font.size = Pt(9)
    fact.text_frame.paragraphs[0].runs[0].font.color.rgb = rgb(MUTED)
    mid.append(fact)
    fy += Inches(0.66)
deck.anim(s, mid, 4)
rx = mx + mw + Inches(0.25)                              # right: personality, as five-dot scales
rw = W - deck.left - rx
right = [shape(s, MSO_SHAPE.RECTANGLE, rx, y0, rw, ph, fill="FFFFFF", line=GRID),
         box(s, rx + Inches(0.25), y0 + Inches(0.15), rw - Inches(0.5), Inches(0.4), ["PERSONALITY"], 12, BLUE,
             bold=True)]
ty, dot = y0 + Inches(0.65), Inches(0.24)
for trait, level in C.TRAITS:
    right.append(box(s, rx + Inches(0.25), ty, rw - Inches(0.5), Inches(0.36), [trait], 14))
    for k in range(5):
        right.append(circle(s, rx + Inches(0.42) + (dot + Inches(0.12)) * k, ty + Inches(0.55), dot,
                            CORAL if k < level else "E3E8EF"))
    ty += Inches(0.84)
deck.anim(s, right, 5)
s.notes_slide.notes_text_frame.text = (
    f"Meet {P['name']}, a fictional customer from the target segment: 27, a customer service officer in Lagos with "
    "an HND, steady pay and about 50,000 naira a month to spare. Tunde is careful with money and ambitious, but not "
    "yet confident with tech, short of free time, and wary of online courses.")

gap = Inches(0.25)
cw = (W - 2 * deck.left - gap) // 2
for title, sub, cards, size in (
        ("Tunde wants a better job, but fears wasting money", "Goals, frustrations, needs, and where to reach Tunde",
         (("Goals", P["goals"], TEAL), ("Frustrations", P["frustrations"], CORAL), ("Needs", P["needs"], BLUE),
          ("Where to reach Tunde", P["channels"], AMBER)), 16),
        ("What makes Tunde buy", "Buying triggers, objections and our answers, how Tunde chooses and pays",
         (("Buying triggers", P["triggers"], BLUE), ("Objections, and our answer", P["objections"], CORAL),
          ("How Tunde chooses", P["criteria"], TEAL), ("How Tunde pays", P["payment"], AMBER)), 15)):
    s, top = content_slide(title, sub, "1  ·  Customer persona")
    ch = (H - top - Inches(0.75) - gap) // 2
    for i, (heading, items, colour) in enumerate(cards):
        deck.anim(s, band_card(s, deck.left + (cw + gap) * (i % 2), top + (ch + gap) * (i // 2), cw, ch, heading,
                               items, colour, size), 3 + i)
    s.notes_slide.notes_text_frame.text = (
        "Tunde's goal is a cybersecurity job within a year. The frustrations are not knowing where to start, fear of "
        "scams, and a full-time job; Tunde needs weekend labs, a fair price in parts and help into a job."
        if title.startswith("Tunde wants") else
        "Breach news, a friend's new tech job, or a free first class push Tunde to act. Each worry has an answer. "
        "Tunde chooses on labs, the full price, reviews and the certificate, and pays from salary in three parts.")

# ================================================================== Task 2: journey map
divider("2", "Customer Journey Map", "From first hearing about the course to a new job")

s, top = content_slide("From curiosity to a new job: Tunde's journey",
                       "What Tunde does at each stage, where, what Tunde thinks, and how it feels",
                       "2  ·  Customer journey map")
journey = dict(C.JOURNEY)
stage_colours = [BLUE, TEAL, AMBER, CORAL, NAVY]
x0, label_w, gap = deck.left - Inches(0.1), Inches(1.55), Inches(0.06)
col_w = (W - 2 * x0 - label_w - gap * len(C.STAGES)) // len(C.STAGES)
col_x = [x0 + label_w + gap + (col_w + gap) * i for i in range(len(C.STAGES))]
arrows = []
for i, stage in enumerate(C.STAGES):
    width = col_w + (Inches(0.12) if i < len(C.STAGES) - 1 else 0)          # each arrow tucks into the next
    arrows.append(text_in(shape(s, MSO_SHAPE.PENTAGON if i == 0 else MSO_SHAPE.CHEVRON, col_x[i], top, width,
                                Inches(0.5), fill=stage_colours[i]), [stage], 13, on(stage_colours[i]), bold=True,
                          align=PP_ALIGN.CENTER))
deck.anim(s, arrows, 3, "wipe-left")
y = top + Inches(0.58)
cells = []
for label, height in (("Doing", Inches(0.88)), ("Touchpoints", Inches(0.72)), ("Thinking and feeling", Inches(0.84))):
    cells.append(text_in(shape(s, MSO_SHAPE.RECTANGLE, x0, y, label_w, height, fill=LIGHT), [label], 13, NAVY,
                         bold=True))
    for i, text in enumerate(journey[label]):
        cells.append(text_in(shape(s, MSO_SHAPE.RECTANGLE, col_x[i], y, col_w, height, fill="FFFFFF", line=GRID),
                             [text], 12, INK, align=PP_ALIGN.CENTER))
    y += height + gap
deck.anim(s, cells, 4)
feel_h = Inches(1.45)
frame = [text_in(shape(s, MSO_SHAPE.RECTANGLE, x0, y, label_w, feel_h, fill=LIGHT), ["Feeling (1-5)"], 13, NAVY,
                 bold=True),
         shape(s, MSO_SHAPE.RECTANGLE, col_x[0], y, col_x[-1] + col_w - col_x[0], feel_h, fill="FFFFFF", line=GRID)]
pad_top, pad_bottom = Inches(0.42), Inches(0.18)
span = feel_h - pad_top - pad_bottom
centres = [(col_x[i] + col_w // 2, y + pad_top + span * (5 - v) // 4) for i, v in enumerate(C.FEELING)]
curve = []
for (xa, ya), (xb, yb) in zip(centres, centres[1:]):
    line = s.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, xa, ya, xb, yb)
    line.line.color.rgb = rgb(BLUE)
    line.line.width = Pt(3)
    curve.append(line)
for (xc, yc), v in zip(centres, C.FEELING):
    curve.append(circle(s, xc, yc, Inches(0.28), CORAL if v <= 2 else (AMBER if v == 3 else TEAL), line="FFFFFF"))
    curve.append(box(s, xc - Inches(0.25), yc - Inches(0.5), Inches(0.5), Inches(0.34), [str(v)], 13, NAVY, bold=True,
                     align=PP_ALIGN.CENTER))
deck.anim(s, frame, 5)
deck.anim(s, curve, 6, "wipe-left")
s.notes_slide.notes_text_frame.text = (
    "The map follows Tunde through five stages: awareness, consideration, purchase, learning and after the course. "
    "Tunde starts curious, is most anxious when comparing courses, gains confidence while learning, and ends proud "
    "on getting a job.")

s, top = content_slide("Every pain point is an opportunity",
                       "What goes wrong at each stage of the journey, and what SkillUp Academy will do",
                       "2  ·  Customer journey map")
gap = Inches(0.12)
cw = (W - 2 * deck.left - gap * 4) // 5
for i, stage in enumerate(C.STAGES):
    x = deck.left + (cw + gap) * i
    py = top + Inches(0.65)
    oy = py + Inches(2.05)
    deck.anim(s, [
        text_in(shape(s, MSO_SHAPE.PENTAGON if i == 0 else MSO_SHAPE.CHEVRON, x, top,
                      cw + (Inches(0.1) if i < 4 else 0), Inches(0.5), fill=stage_colours[i]), [stage], 13,
                on(stage_colours[i]), bold=True, align=PP_ALIGN.CENTER),
        shape(s, MSO_SHAPE.RECTANGLE, x, py, cw, Inches(1.45), fill="FBE7E3"),
        shape(s, MSO_SHAPE.RECTANGLE, x, py, cw, Inches(0.07), fill=CORAL),
        box(s, x + Inches(0.1), py + Inches(0.15), cw - Inches(0.2), Inches(0.3), ["PAIN POINT"], 10, CORAL, bold=True),
        box(s, x + Inches(0.1), py + Inches(0.45), cw - Inches(0.2), Inches(0.95), [journey["Pain points"][i]], 14),
        shape(s, MSO_SHAPE.DOWN_ARROW, x + cw // 2 - Inches(0.2), py + Inches(1.55), Inches(0.4), Inches(0.4),
              fill="C5CCD6"),
        shape(s, MSO_SHAPE.RECTANGLE, x, oy, cw, Inches(1.85), fill="E1F2EF"),
        shape(s, MSO_SHAPE.RECTANGLE, x, oy, cw, Inches(0.07), fill=TEAL),
        box(s, x + Inches(0.1), oy + Inches(0.15), cw - Inches(0.2), Inches(0.3), ["OPPORTUNITY"], 10, TEAL, bold=True),
        box(s, x + Inches(0.1), oy + Inches(0.45), cw - Inches(0.2), Inches(1.35), [journey["Opportunities"][i]], 14),
    ], 3 + i)
s.notes_slide.notes_text_frame.text = (
    "Each pain point is an opportunity: beginner videos for awareness, clear prices and reviews for consideration, "
    "a free class and instalments for purchase, weekly labs and fast support for learning, and job help after.")

# ================================================================== Task 3: needs
divider("3", "The 5 Most Important Needs", "Chosen from 12 functional, economic, emotional and social needs")

s, top = content_slide("Customers have four kinds of needs",
                       "Three needs of each type, with each need's importance score (of 25)",
                       "3  ·  The 5 most important needs")
gap = Inches(0.25)
cw = (W - 2 * deck.left - gap) // 2
ch = (H - top - Inches(0.95) - gap) // 2
about = {"Functional": "what the course does", "Economic": "money", "Emotional": "feelings", "Social": "other people"}
for i, kind in enumerate(C.NEED_TYPES):
    x = deck.left + (cw + gap) * (i % 2)
    y = top + (ch + gap) * (i // 2)
    colour = TYPE_COLOUR[kind]
    card = [shape(s, MSO_SHAPE.RECTANGLE, x, y, cw, ch, fill="FFFFFF", line=GRID),
            text_in(shape(s, MSO_SHAPE.RECTANGLE, x, y, cw, Inches(0.5), fill=colour),
                    [[(f"{kind} needs", True), (f"   {about[kind]}", False)]], 15, on(colour), margin=0.18)]
    ny = y + Inches(0.6)
    for need in [n for n in C.NEEDS if n[0] == kind]:
        card.append(box(s, x + Inches(0.2), ny, cw - Inches(1.3), Inches(0.42), [need[1]], 15))
        card.append(pill(s, x + cw - Inches(1.0), ny + Inches(0.06), Inches(0.8), Inches(0.3),
                         str(importance[need[1]]), NAVY if need[1] in top5 else "E3E8EF", 11))
        ny += Inches(0.45)
    deck.anim(s, card, 3 + i)
deck.anim(s, deck.footnote(s, H - Inches(0.85), "Navy score: one of the 5 most important needs. Importance = how "
                                               "often it came up in the research × its effect on buying."), 7)
s.notes_slide.notes_text_frame.text = (
    "Functional needs are about what the course does, economic needs about money, emotional needs about feelings, "
    "and social needs about other people. The navy scores mark the five most important.")

s, top = content_slide("Skills and money matter most to customers",
                       "The 5 most important needs, ranked by importance (of 25)", "3  ·  The 5 most important needs")
row_h = Inches(0.9)
bar_x, bar_w = Inches(8.95), Inches(2.85)
for k, name in enumerate(top5):
    y = top + row_h * k
    kind = need_row[name][0]
    colour = TYPE_COLOUR[kind]
    score = importance[name]
    deck.anim(s, [
        shape(s, MSO_SHAPE.RECTANGLE, deck.left, y + Inches(0.04), W - 2 * deck.left, row_h - Inches(0.08),
              fill=LIGHT if k % 2 == 0 else "FFFFFF"),
        circle(s, deck.left + Inches(0.45), y + row_h // 2, Inches(0.56), NAVY, str(k + 1), 20),
        box(s, deck.left + Inches(0.9), y + Inches(0.06), Inches(5.8), Inches(0.42), [name], 16, NAVY, bold=True),
        box(s, deck.left + Inches(0.9), y + Inches(0.39), Inches(5.8), Inches(0.5), [need_row[name][4]], 11, MUTED),
        pill(s, Inches(7.55), y + Inches(0.3), Inches(1.2), Inches(0.3), kind.upper(), colour, 9),
        shape(s, MSO_SHAPE.RECTANGLE, bar_x, y + Inches(0.33), bar_w, Inches(0.24), fill="E3E8EF"),
        shape(s, MSO_SHAPE.RECTANGLE, bar_x, y + Inches(0.33), bar_w * score // 25, Inches(0.24), fill=colour),
        box(s, bar_x + bar_w + Inches(0.05), y + Inches(0.22), Inches(0.75), Inches(0.45), [f"{score}"], 16, NAVY,
            bold=True),
    ], 3 + k, "wipe-left")
s.notes_slide.notes_text_frame.text = (
    "The five most important needs are hands-on skills and an affordable price, both 25 out of 25, then certificate "
    "preparation, a better-paid job and feeling supported, each 20: two functional, two economic and one emotional.")

s, top = content_slide("Five needs score 20 or more out of 25", "Importance of each need, out of 25; the top five in navy",
                       "3  ·  The 5 most important needs", keep_placeholder=True)
frame, chart = deck.bar_chart(s, placeholder(s, 1), *deck.chart_area(top), [n[2] for n in C.NEEDS],
                              [importance[n[1]] for n in C.NEEDS], number_format="0", maximum=25,
                              top=[i for i, n in enumerate(C.NEEDS) if n[1] in top5])
chart.category_axis.tick_labels.font.size = Pt(13)
chart.plots[0].data_labels.font.size = Pt(13)
deck.anim(s, frame, 3, "wipe-left")
deck.anim(s, deck.side_note(s, top, [[("Top 5: ", True), ("two functional, two economic and one emotional need.", False)],
                                     [("Skills and money ", True), ("matter most.", False)],
                                     [("Social needs ", True), ("score lowest, but still shape the brand.", False)]],
                            size=17), 4)
s.notes_slide.notes_text_frame.text = (
    "The chart shows all twelve needs. Skills and money matter most; social needs matter less, but still shape how "
    "the brand talks to people.")

# ================================================================== Task 4: segments
divider("4", "Four Market Segments", "Demographic, geographic, psychographic and behavioural")

s, top = content_slide("The market splits into four segments",
                       "Each segment on the four bases: demographic, geographic, psychographic and behavioural",
                       "4  ·  Four market segments")
gap = Inches(0.2)
cw = (W - 2 * deck.left - 3 * gap) // 4
ch = H - top - Inches(0.75)
for i, seg in enumerate(C.SEGMENTS):
    x = deck.left + (cw + gap) * i
    colour = SEG_COLOUR[i]
    is_target = seg[0] == TARGET
    card = [shape(s, MSO_SHAPE.RECTANGLE, x, top, cw, ch, fill="FFFFFF", line=NAVY if is_target else GRID,
                  width=2.25 if is_target else 0.75),
            text_in(shape(s, MSO_SHAPE.RECTANGLE, x, top, cw, Inches(0.62), fill=colour), [seg[0]], 15, on(colour),
                    bold=True, margin=0.15),
            box(s, x + Inches(0.12), top + Inches(0.7), cw - Inches(0.24), Inches(0.5), [seg[5]], 11,
                "9A5A1E" if colour == AMBER else colour, bold=True)]
    by = top + Inches(1.2)
    for b, (base, _about) in enumerate(C.BASES):
        part = box(s, x + Inches(0.12), by, cw - Inches(0.24), Inches(0.84), [[(base.upper(), True)], seg[1 + b]], 12,
                   after=0)
        part.text_frame.paragraphs[0].runs[0].font.size = Pt(9)
        part.text_frame.paragraphs[0].runs[0].font.color.rgb = rgb(MUTED)
        card.append(part)
        by += Inches(0.84)
    deck.anim(s, card, 3 + i)
s.notes_slide.notes_text_frame.text = (
    "The four segments are Campus Starters, students and new graduates; Career Switchers, working adults in non-IT "
    "jobs; Corporate Upskillers, staff whose employers pay; and Women in Tech Starters.")

# ================================================================== Task 5: scores
divider("5", "Segment Scores", "Market size, accessibility, buying potential and competition")

s, top = content_slide(f"{TARGET} have the best overall score",
                       "Scores 1 (low) to 5 (high), darker = better; for competition, 5 = little competition",
                       "5  ·  Segment scores")
widths = [Inches(3.0)] + [Inches(1.75)] * 4 + [Inches(1.9)]
xs = [deck.left + sum(widths[:i], Emu(0)) for i in range(len(widths))]
head_h, row_h = Inches(0.66), Inches(0.88)
heads = [["Segment"]] + [[c, f"({int(w * 100)}%)"] for c, w in C.CRITERIA] + [["Weighted score"]]
deck.anim(s, [text_in(shape(s, MSO_SHAPE.RECTANGLE, x, top, w, head_h, fill=NAVY, line="FFFFFF"), text, 13, "FFFFFF",
                      bold=True, align=None if i == 0 else PP_ALIGN.CENTER, margin=0.12)
              for i, (x, w, text) in enumerate(zip(xs, widths, heads))], 3)
for r, (seg, sc) in enumerate(zip(C.SEGMENTS, C.SCORES)):
    y = top + head_h + row_h * r
    is_target = seg[0] == TARGET
    total = total_of[seg[0]]
    row = [shape(s, MSO_SHAPE.RECTANGLE, xs[0], y, widths[0], row_h, fill="FFFFFF", line=GRID),
           shape(s, MSO_SHAPE.RECTANGLE, xs[0], y, Inches(0.1), row_h, fill=SEG_COLOUR[r]),
           box(s, xs[0] + Inches(0.2), y + Inches(0.1), widths[0] - Inches(0.3), Inches(0.4), [seg[0]], 15, NAVY,
               bold=True)]
    if is_target:
        row.append(pill(s, xs[0] + Inches(0.28), y + Inches(0.52), Inches(0.9), Inches(0.26), "TARGET", CORAL, 9))
    row += [text_in(shape(s, MSO_SHAPE.RECTANGLE, xs[1 + c], y, widths[1 + c], row_h, fill=HEAT[v], line="FFFFFF",
                          width=1.5), [str(v)], 22, on(HEAT[v]), bold=True, align=PP_ALIGN.CENTER)
            for c, v in enumerate(sc)]
    row += [shape(s, MSO_SHAPE.RECTANGLE, xs[-1], y, widths[-1], row_h, fill="FFFFFF", line=GRID),
            shape(s, MSO_SHAPE.RECTANGLE, xs[-1] + Inches(0.15), y + Inches(0.58), int((widths[-1] - Inches(0.3)) *
                                                                                     total / 5),
                  Inches(0.16), fill=NAVY if is_target else "C5CCD6"),
            box(s, xs[-1] + Inches(0.1), y + Inches(0.06), widths[-1] - Inches(0.2), Inches(0.48), [f"{total:.2f}"], 18,
                NAVY, bold=True, align=PP_ALIGN.CENTER)]
    deck.anim(s, row, 4 + r)
deck.anim(s, deck.footnote(s, top + head_h + row_h * 4 + Inches(0.12),
                           "Weighted score (of 5) = SUMPRODUCT of the weights and the scores, worked out in Excel."), 8)
s.notes_slide.notes_text_frame.text = (
    f"Each segment is scored on market size, accessibility, buying potential and competition. {TARGET} score "
    f"{total_of[TARGET]:.2f}, the highest, with four on every criterion. {SECOND} are biggest but have little money.")

# ================================================================== Task 6: target
divider("6", "Target Segment", "The segment the business should prioritise")

s, top = content_slide(f"Prioritise {TARGET}", "Why this is the segment SkillUp Academy should focus on",
                       "6  ·  Target segment")
cx, cy = deck.left + Inches(2.1), top + Inches(1.95)
deck.anim(s, [circle(s, cx, cy, Inches(3.7), "DCE7F5"), circle(s, cx, cy, Inches(2.75), "A6C3E5"),
              circle(s, cx, cy, Inches(1.85), BLUE), circle(s, cx, cy, Inches(1.05), NAVY, f"{total_of[TARGET]:.2f}", 22),
              box(s, deck.left, cy + Inches(1.95), Inches(4.2), Inches(0.42), [f"{TARGET}  ·  score of 5"], 16, NAVY,
                  bold=True, align=PP_ALIGN.CENTER)], 3)
reasons = [("Who", "working adults of 25 to 35 in non-IT jobs, in Lagos, Abuja and Port Harcourt"),
           ("Can pay", "steady pay above the ₦70,000 minimum wage; ₦50,000 a month in 3 parts"),
           ("Strong reason to buy", "a junior analyst job pays about ₦150,000 to ₦300,000 a month"),
           ("Easy to reach", "Google, Facebook, LinkedIn and WhatsApp; evening and weekend classes"),
           ("Little competition", "few practical, mid-price courses fit around a full-time job")]
rx = deck.left + Inches(4.6)
for k, (head, text) in enumerate(reasons):
    y = top + Inches(0.9) * k
    deck.anim(s, [circle(s, rx + Inches(0.3), y + Inches(0.4), Inches(0.5), [TEAL, BLUE, CORAL, AMBER, NAVY][k],
                         str(k + 1), 16),
                  box(s, rx + Inches(0.7), y + Inches(0.0), W - deck.left - rx - Inches(0.7), Inches(0.88),
                      [[(head, True)], text], 14, after=0)], 4 + k)
s.notes_slide.notes_text_frame.text = (
    f"SkillUp Academy should prioritise {TARGET}. They can pay in parts, have a strong reason to buy, are easy to "
    "reach online, and few rivals offer practical courses that fit around a job.")

# ================================================================== Key findings
s, top = content_slide(f"Target {TARGET} with a practical course", "The key findings of the customer analysis",
                       "Conclusion")
gap = Inches(0.25)
cw = (W - 2 * deck.left - gap) // 2
ch = (H - top - Inches(0.75) - gap) // 2
low = C.STAGES[C.FEELING.index(min(C.FEELING))]
findings = [("Top need", "Hands-on skills", f"{importance[top5[0]]} of 25, level with an affordable price", BLUE),
            ("Target segment", TARGET, f"{total_of[TARGET]:.2f} of 5, ahead of {SECOND} ({total_of[SECOND]:.2f})", TEAL),
            ("Persona", "Tunde, 27, Lagos", "Customer service officer who wants a cyber job within a year", AMBER),
            ("Journey low point", low, "Fear of scams and hidden prices: fix with clear prices, reviews and a free "
                                       "first class", CORAL)]
for i, (label, value, text, colour) in enumerate(findings):
    x = deck.left + (cw + gap) * (i % 2)
    y = top + (ch + gap) * (i // 2)
    deck.anim(s, [shape(s, MSO_SHAPE.RECTANGLE, x, y, cw, ch, fill="FFFFFF", line=GRID),
                  shape(s, MSO_SHAPE.RECTANGLE, x, y, Inches(0.1), ch, fill=colour),
                  box(s, x + Inches(0.35), y + Inches(0.2), cw - Inches(0.5), Inches(0.35), [label.upper()], 11, MUTED,
                      bold=True),
                  box(s, x + Inches(0.35), y + Inches(0.52), cw - Inches(0.5), Inches(0.62), [value], 28, NAVY,
                      bold=True),
                  box(s, x + Inches(0.35), y + Inches(1.15), cw - Inches(0.5), ch - Inches(1.2), [text], 14, MUTED)],
              3 + i)
s.notes_slide.notes_text_frame.text = (
    f"In short: customers need hands-on skills at a fair price; SkillUp Academy should target {TARGET}, like Tunde; "
    "and the weakest point of the journey, choosing a course, is fixed with clear prices, reviews and a free class.")

# ================================================================== Thank you
s = prs.slides.add_slide(LAYOUT["Title Slide"])
deck.title_card(s, "Thank You", ["Any questions?", FOOT], kicker="Capstone Project  ·  Part 2")
deck.anim_chrome(s, title_card=True)
s.notes_slide.notes_text_frame.text = "Thank you for listening."

deck.save(out_path, title=f"Capstone Part 2: Customer Analysis for {C.PRODUCT}",
          subject="Customer persona, journey map, the 5 most important needs, four segments, scores and target",
          keywords="customer persona, customer journey map, customer needs, segmentation, target segment")
