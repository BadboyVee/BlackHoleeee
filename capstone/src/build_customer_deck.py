#!/usr/bin/env python3
"""Build the capstone part 2 deck: the customer analysis for CyberStart (persona, journey map, the
five most important needs, four segments and their scores, the target segment), made the way it
would be in PowerPoint 2013, in a design of ../../assignment/src/deck_kit.py (build.sh uses the
navy report design).

Usage: python build_customer_deck.py Customer_Analysis.xlsx template.pptx wood.jpg STYLE out.pptx
  The workbook must have been through LibreOffice (build.sh does this), so the worked-out
  figures (need importance and ranks, segment scores, the target) can be read from it.

The slides follow the tasks in the order they were set, each section labelled with its number:
title, contents, world and Nigerian data; 1. the customer persona and what makes them buy; 2. the
customer journey map (stage arrows, what the customer does, the touchpoints, thoughts and a
feeling curve) and its pain points and opportunities; 3. the twelve customer needs, the five most
important and a bar chart of all twelve; 4. the segmentation bases and the four segments; 5. the
segment scores and a bar chart; 6. the target segment; then the conclusion and thank you. Every
slide's objects come in by themselves; the plan is saved as out.anim.json for finish_deck.py.
"""
import sys

from openpyxl import load_workbook
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Emu, Inches, Pt

import customer_data as C
from deck_kit import Deck, placeholder, rgb

workbook_path, template_path, wood_path, style_name, out_path = sys.argv[1:6]
deck = Deck(style_name, template_path, wood_path)
S, prs, W, H, LAYOUT = deck.S, deck.prs, deck.W, deck.H, deck.layout
deck.footer = f"{C.BUSINESS}  ·  Capstone Project, Part 2"
P = C.PERSONA

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


needs = rows_of("3 Customer Needs", C.NEEDS[0][1], len(C.NEEDS), [2, 7, 8])          # need, importance, rank
importance = {n: imp for n, imp, _rank in needs}
rank_of = {n: rank for n, _imp, rank in needs}
top5 = sorted((rank, n) for n, _imp, rank in needs)[:5]
scores = rows_of("5-6 Segment Scores", C.SEGMENTS[0][0], len(C.SEGMENTS), [1, 6, 7])      # segment, total, rank
total_of = {s: t for s, t, _r in scores}
TARGET = min(scores, key=lambda row: row[2])[0]
SECOND = next(s for s, _t, r in scores if r == 2)


# ------------------------------------------------------------------ helpers
def content_slide(title, subtitle, kicker):
    """A content slide: a small section label (kicker), a title that states the finding, a subtitle."""
    s = prs.slides.add_slide(LAYOUT["Title and Content"])
    top = deck.content(s, title, subtitle, kicker=kicker)
    deck.anim_chrome(s)
    return s, top


def table_slide(s, top, rows, widths, heights, size, *, centre_from=9, bold_rows=(), note=None):
    heights = heights if isinstance(heights, list) else [heights] * len(rows)
    table_w = sum(widths, Emu(0))
    frame, table = deck.table(s, placeholder(s, 1), (W - table_w) // 2, top + Inches(0.05), rows, widths, heights,
                              size, centre_from=centre_from, bold_rows=bold_rows)
    deck.anim(s, frame, 3, "wipe-down")
    if note:
        deck.anim(s, deck.footnote(s, top + Inches(0.05) + sum(heights, Emu(0)) + Inches(0.12), note), 4)
    return table


def chart_slide(s, top, labels, values, number_format, maximum, top_bars, points, size=16):
    frame, chart = deck.bar_chart(s, placeholder(s, 1), *deck.chart_area(top), labels, values,
                                  number_format=number_format, maximum=maximum, top=top_bars)
    deck.anim(s, frame, 3, "wipe-left")
    deck.anim(s, deck.side_note(s, top, [[(a, True), (b, False)] for a, b in points], size=size), 4)
    return chart


def bold_first(points):
    return [[(a, True), (b, False)] for a, b in points]


def mini_card(s, x, y, w, h, heading, items, size=14):
    """A small card: a bold heading in the accent text colour, then short bulleted lines."""
    shapes = deck.card(s, x, y, w, h)
    box = deck.textbox(s, x + Inches(0.25), y + Inches(0.12), w - Inches(0.4), h - Inches(0.2),
                       [[(heading, True)]] + [f"•  {item}" for item in items], size=size, colour=S["text"], after=4)
    box.text_frame.paragraphs[0].runs[0].font.color.rgb = rgb(S["names"])
    box.text_frame.paragraphs[0].runs[0].font.size = Pt(size + 2)
    return [*shapes, box]


# ================================================================== 1. Title
s = prs.slides.add_slide(LAYOUT["Title Slide"])
deck.title_card(s, "Customer Analysis", [f"Needs, segments, persona and journey map for {C.PRODUCT}",
                                         f"{C.BUSINESS}   |   Market Research Lab   |   October 2026"], size=54,
                kicker="Capstone Project  ·  Part 2")
deck.anim_chrome(s, title_card=True)
s.notes_slide.notes_text_frame.text = (
    f"Part 2 of my capstone analyses the customers of {C.PRODUCT}: their needs, four market segments, the target "
    "segment, a customer persona and a customer journey map.")

# ================================================================== 2. Contents
s, top = content_slide("Six tasks, in the order they were set", f"Customer analysis for {C.PRODUCT}, "
                       f"{C.PRODUCT_LINE}", "Contents")
gap = Inches(0.25)
cw = (W - 2 * deck.left - 2 * gap) // 3
ch = (H - top - Inches(0.8) - gap) // 2
tiles = []
for i, (number, task, about) in enumerate(C.TASKS):
    x = deck.left + (cw + gap) * (i % 3)
    y = top + Inches(0.05) + (ch + gap) * (i // 3)
    shapes = deck.card(s, x, y, cw, ch)
    num = deck.textbox(s, x + Inches(0.25), y + Inches(0.1), Inches(1.0), Inches(0.85), [number], size=40,
                       colour=S["rule"], font=S["head_font"])
    text = deck.textbox(s, x + Inches(0.25), y + Inches(1.0), cw - Inches(0.45), ch - Inches(1.1),
                        [[(task, True)], about], size=17, colour=S["text"], after=4)
    text.text_frame.paragraphs[0].runs[0].font.color.rgb = rgb(S["names"])
    text.text_frame.paragraphs[1].runs[0].font.size = Pt(14)
    text.text_frame.paragraphs[1].runs[0].font.color.rgb = rgb(S["muted"])
    tiles += [*shapes, num, text]
deck.anim(s, tiles, 3)
s.notes_slide.notes_text_frame.text = (
    "I answer the six tasks in the order they were set: the customer persona, the customer journey map, the five "
    "most important needs, four market segments, the segment scores, and the target segment.")

# ================================================================== 3. World and Nigerian data
s, top = content_slide("Cyber skills are in demand worldwide; Nigeria is young",
                       "World and Nigerian data behind the analysis", "Context")
rows = [("Fact", "Figure", "Where")] + [([[(fact, True)]], figure, where) for fact, figure, _n, where, _k in C.WORLD]
table_slide(s, top, rows, [Inches(5.0), Inches(5.0), Inches(1.6)], [Inches(0.42)] + [Inches(0.43)] * len(C.WORLD), 14,
            centre_from=2, note="Sources: World Economic Forum, ISC2, NUC, UN and World Bank data, DataReportal "
                                "(full list in Excel).")
s.notes_slide.notes_text_frame.text = (
    "Around the world, networks and cybersecurity is the second fastest-growing skill, and 95 percent of cyber teams "
    "have a skills gap, led by AI and cloud security. Nigeria is young, with a median age of about 19 and 2.1 "
    "million university students. The minimum wage is 70,000 naira a month, while junior analysts earn about "
    "150,000 to 300,000.")

# ================================================================== Task 1. Customer persona
s, top = content_slide(f"Meet Tunde, a typical {TARGET[:-1]}",
                       f"A fictional {TARGET[:-1]}, the target segment chosen in task 6, built from the research", "1  ·  Customer persona")
y0 = top + Inches(0.05)
left_w, gap = Inches(4.3), Inches(0.25)
lx = deck.left
card_h = H - y0 - Inches(0.75)
left = deck.card(s, lx, y0, left_w, card_h)
avatar = s.shapes.add_shape(MSO_SHAPE.OVAL, lx + Inches(0.35), y0 + Inches(0.3), Inches(1.2), Inches(1.2))
avatar.fill.solid()
avatar.fill.fore_color.rgb = rgb(S["head_fill"] or S["rule"])
avatar.line.fill.background()
deck.write(avatar.text_frame, [P["initials"]], size=28, colour=S.get("avatar_text", S["rule"]), bold=True,
           align=PP_ALIGN.CENTER)
avatar.text_frame.vertical_anchor = MSO_ANCHOR.MIDDLE
who = deck.textbox(s, lx + Inches(1.7), y0 + Inches(0.35), left_w - Inches(1.85), Inches(1.15),
                   [[(P["name"], True)], f"{P['segment']}"], size=22, colour=S["text"], after=2)
who.text_frame.paragraphs[1].runs[0].font.size = Pt(14)
who.text_frame.paragraphs[1].runs[0].font.color.rgb = rgb(S["muted"])
facts = deck.textbox(s, lx + Inches(0.3), y0 + Inches(1.65), left_w - Inches(0.5), Inches(2.25),
                     [[(f"{k}: ", True), (v, False)] for k, v in P["facts"]], size=13, colour=S["text"], after=3)
quote = deck.textbox(s, lx + Inches(0.3), y0 + card_h - Inches(0.95), left_w - Inches(0.5), Inches(0.8),
                     [P["quote"]], size=14, colour=S["names"])
quote.text_frame.paragraphs[0].runs[0].font.italic = True
deck.anim(s, left + [avatar, who, facts, quote], 3)
gx = lx + left_w + gap
gw = (W - deck.left - gx - gap) // 2
gh = (card_h - gap) // 2
cards = []
for i, (heading, items) in enumerate((("Goals", P["goals"]), ("Frustrations", P["frustrations"]),
                                      ("Needs", P["needs"]), ("Where to reach them", P["channels"]))):
    x = gx + (gw + gap) * (i % 2)
    y = y0 + (gh + gap) * (i // 2)
    cards += mini_card(s, x, y, gw, gh, heading, items)
deck.anim(s, cards, 4)
s.notes_slide.notes_text_frame.text = (
    f"Meet {P['name']}, a fictional customer from the target segment: 27, in customer service in Lagos, and keen "
    "to get a cybersecurity job within a year. Tunde is afraid of paying for a scam course, works 8 to 5, and finds "
    "courses on Google, YouTube, TikTok and WhatsApp.")

# ================================================================== Task 1. What makes the persona buy
s, top = content_slide("What makes Tunde buy", "Buying triggers, objections, how Tunde chooses and pays",
                       "1  ·  Customer persona")
y0 = top + Inches(0.05)
gap = Inches(0.25)
cw = (W - 2 * deck.left - gap) // 2
ch = (H - y0 - Inches(0.75) - gap) // 2
cards = []
for i, (heading, items) in enumerate((("Buying triggers", P["triggers"]),
                                      ("Objections, and our answer", P["objections"]),
                                      ("How Tunde chooses", P["criteria"]), ("How Tunde pays", P["payment"]))):
    cards.append(mini_card(s, deck.left + (cw + gap) * (i % 2), y0 + (ch + gap) * (i // 2), cw, ch, heading, items,
                           size=16))
deck.anim(s, cards[0] + cards[1], 3)
deck.anim(s, cards[2] + cards[3], 4)
s.notes_slide.notes_text_frame.text = (
    "Tunde is pushed to act by breach news, a friend's new tech job, or a free first class. The worries are scams, "
    "fitting study round work, and whether a job will follow, and each has an answer. Tunde chooses on labs, the "
    "full price, reviews and the certificate, and pays from salary in three parts.")

# ================================================================== Task 2. Customer journey map
s, top = content_slide("From curiosity to a new job: Tunde's journey",
                       f"Customer journey map of {P['name']}: what Tunde does, where, what Tunde thinks, and how it "
                       "feels", "2  ·  Customer journey map")
journey = dict(C.JOURNEY)
x0, label_w, gap = Inches(0.7), Inches(1.55), Inches(0.06)
col_w = (W - 2 * x0 - label_w - gap * len(C.STAGES)) // len(C.STAGES)
col_x = [x0 + label_w + gap + (col_w + gap) * i for i in range(len(C.STAGES))]
# the stages, as arrows (Insert > Shapes > Pentagon and Chevron)
arrows = []
for i, stage in enumerate(C.STAGES):
    width = col_w + (Inches(0.12) if i < len(C.STAGES) - 1 else 0)      # each arrow tucks into the next
    shape = s.shapes.add_shape(MSO_SHAPE.PENTAGON if i == 0 else MSO_SHAPE.CHEVRON, col_x[i], top, width,
                               Inches(0.5))
    shape.fill.solid()
    shape.fill.fore_color.rgb = rgb(S["head_fill"])
    shape.line.fill.background()
    deck.write(shape.text_frame, [stage], size=13, colour="FFFFFF", bold=True, align=PP_ALIGN.CENTER)
    shape.text_frame.vertical_anchor = MSO_ANCHOR.MIDDLE
    arrows.append(shape)
deck.anim(s, arrows, 3, "wipe-left")
# the rows: a label, then one cell for each stage
y = top + Inches(0.58)
cells = []
for label, height in (("Doing", Inches(0.88)), ("Touchpoints", Inches(0.72)), ("Thinking and feeling", Inches(0.84))):
    lab = deck.rect(s, x0, y, label_w, height, fill=S["band"])
    deck.write(lab.text_frame, [label], size=13, colour=S["title"], bold=True)
    lab.text_frame.vertical_anchor = MSO_ANCHOR.MIDDLE
    lab.text_frame.word_wrap = True
    cells.append(lab)
    for i, text in enumerate(journey[label]):
        cell = deck.rect(s, col_x[i], y, col_w, height, fill="FFFFFF", line=S["grid"], width=0.75)
        deck.write(cell.text_frame, [text], size=12, colour=S["text"])
        cell.text_frame.vertical_anchor = MSO_ANCHOR.MIDDLE
        cell.text_frame.word_wrap = True
        cells.append(cell)
    y += height + gap
deck.anim(s, cells, 4)
# the feeling curve: a dot for each stage, higher for better feelings, joined by lines
feel_h = Inches(1.45)
lab = deck.rect(s, x0, y, label_w, feel_h, fill=S["band"])
deck.write(lab.text_frame, ["Feeling (1-5)"], size=13, colour=S["title"], bold=True)
lab.text_frame.vertical_anchor = MSO_ANCHOR.MIDDLE
area = deck.rect(s, col_x[0], y, col_x[-1] + col_w - col_x[0], feel_h, fill="FFFFFF", line=S["grid"], width=0.75)
dot, pad_top, pad_bottom = Inches(0.24), Inches(0.42), Inches(0.18)       # room above each dot for its score
span = feel_h - pad_top - pad_bottom
centres = [(col_x[i] + col_w // 2, y + pad_top + span * (5 - v) // 4) for i, v in enumerate(C.FEELING)]
curve = []
for (xa, ya), (xb, yb) in zip(centres, centres[1:]):
    line = s.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, xa, ya, xb, yb)
    line.line.color.rgb = rgb(S["rule"])
    line.line.width = Pt(2.5)
    curve.append(line)
for (xc, yc), v in zip(centres, C.FEELING):
    d = s.shapes.add_shape(MSO_SHAPE.OVAL, xc - dot // 2, yc - dot // 2, dot, dot)
    d.fill.solid()
    d.fill.fore_color.rgb = rgb(S["head_fill"])
    d.line.color.rgb = rgb("FFFFFF")
    d.line.width = Pt(1.5)
    note = deck.textbox(s, xc - Inches(0.25), yc - Inches(0.42), Inches(0.5), Inches(0.3), [str(v)], size=12,
                        colour=S["title"], bold=True, align=PP_ALIGN.CENTER)
    curve += [d, note]
deck.anim(s, [lab, area], 5)
deck.anim(s, curve, 6, "wipe-left")
s.notes_slide.notes_text_frame.text = (
    "The map follows Tunde through five stages: awareness, consideration, purchase, learning and after the course. "
    "Tunde starts curious, is most anxious when comparing courses, gains confidence while learning, and ends proud "
    "on getting a job.")

# ================================================================== Task 2. Pain points and opportunities
s, top = content_slide("Every pain point is an opportunity",
                       "What goes wrong at each stage of the journey, and what SkillUp Academy can do",
                       "2  ·  Customer journey map")
journey = dict(C.JOURNEY)
rows = [("Stage",) + tuple(C.STAGES)]
rows += [([[(label, True)]],) + tuple(journey[label]) for label in ("Pain points", "Opportunities")]
table_slide(s, top, rows, [Inches(1.7)] + [Inches(2.02)] * 5, [Inches(0.45)] + [Inches(1.6)] * 2, 14, centre_from=9)
s.notes_slide.notes_text_frame.text = (
    "Each pain point is an opportunity: beginner videos, clear prices and reviews, instalments, weekly labs and fast "
    "support, and job help.")

# ================================================================== Task 3. Customer needs
s, top = content_slide("Customers have four kinds of needs",
                       "Three functional, economic, emotional and social needs", "3  ·  The 5 most important needs")
by_type = {t: [n for n in C.NEEDS if n[0] == t] for t in C.NEED_TYPES}
rows = [tuple(C.NEED_TYPES)] + [tuple(by_type[t][i][1] for t in C.NEED_TYPES) for i in range(3)]
table_slide(s, top, rows, [Inches(2.95)] * 4, [Inches(0.5)] + [Inches(1.1)] * 3, 18, centre_from=0,
            note="Each need is backed by evidence from the research; see the Customer Needs sheet in Excel.")
s.notes_slide.notes_text_frame.text = (
    "Functional needs are about what the course does: hands-on skills, a flexible timetable and certificate "
    "preparation. Economic needs are about money, emotional needs about trust, support and hope, and social needs "
    "about community, status and inclusion.")

# ================================================================== Task 3. The five most important needs
s, top = content_slide("Skills and money matter most to customers",
                       "The 5 most important needs: importance = how often it came up × its effect on buying "
                       "(of 25)", "3  ·  The 5 most important needs")
need_row = {n[1]: n for n in C.NEEDS}
rows = [("Rank", "Need", "Type", "Score", "Evidence")]
rows += [(str(rank), [[(name, True)]], need_row[name][0], str(importance[name]), need_row[name][4])
         for rank, name in top5]
table_slide(s, top, rows, [Inches(0.8), Inches(3.4), Inches(1.5), Inches(1.0), Inches(5.2)],
            [Inches(0.45)] + [Inches(0.84)] * 5, 14, centre_from=9)
s.notes_slide.notes_text_frame.text = (
    "I scored each need for how often it came up in the research and how much it affects the decision to buy. The "
    "five most important are hands-on skills, an affordable price, certificate preparation, a better-paid job and "
    "feeling supported.")

# ================================================================== Task 3. Need importance chart
s, top = content_slide("Five needs score 20 or more out of 25",
                       "Importance of each need, out of 25; the top five highlighted", "3  ·  The 5 most important needs")
short = [n[2] for n in C.NEEDS]
values = [importance[n[1]] for n in C.NEEDS]
top_idx = [i for i, n in enumerate(C.NEEDS) if rank_of[n[1]] <= 5]
chart = chart_slide(s, top, short, values, "0", 25, top_idx, [
    ("Top 5: ", "two functional, two economic and one emotional need."),
    ("Money and skills ", "matter most."),
    ("Social needs ", "score lowest, but still shape the brand."),
], size=17)
chart.category_axis.tick_labels.font.size = Pt(13)
chart.plots[0].data_labels.font.size = Pt(13)
s.notes_slide.notes_text_frame.text = (
    "The chart shows every need. Skills and money matter most; social needs matter less, but still shape how the "
    "brand talks to people.")

# ================================================================== Task 4. Segmentation bases
s, top = content_slide("Four bases describe the customers", "Four ways to group the customers", "4  ·  Four market segments")
rows = [("Base", "What it looks at")] + [([[(b, True)]], about) for b, about in C.BASES]
table_slide(s, top, rows, [Inches(3.2), Inches(8.6)], [Inches(0.55)] + [Inches(0.8)] * 4, 20,
            note=f"Together they give four segments of {C.PRODUCT}'s possible customers.")
s.notes_slide.notes_text_frame.text = (
    "I used all four bases: demographic, geographic, psychographic and behavioural.")

# ================================================================== Task 4. The four segments
s, top = content_slide("The market splits into four segments", "Each segment described on the four bases",
                       "4  ·  Four market segments")
rows = [("Base",) + tuple(seg[0] for seg in C.SEGMENTS)]
rows += [([[(b, True)]],) + tuple(seg[1 + i] for seg in C.SEGMENTS) for i, (b, _a) in enumerate(C.BASES)]
table_slide(s, top, rows, [Inches(1.75)] + [Inches(2.5)] * 4, [Inches(0.45)] + [Inches(1.0)] * 4, 13, centre_from=9)
s.notes_slide.notes_text_frame.text = (
    "The four segments are Campus Starters, Career Switchers, Corporate Upskillers and Women in Tech Starters.")

# ================================================================== Task 5. Segment scores
s, top = content_slide(f"{TARGET} have the best overall score",
                       "Scored 1 (poor) to 5 (best); weights in brackets; for competition, 5 = little competition",
                       "5  ·  Segment scores")
rows = [("Segment",) + tuple(f"{c} ({int(w * 100)}%)" for c, w in C.CRITERIA) + ("Score (of 5)",)]
rows += [(seg[0],) + tuple(str(v) for v in sc) + (f"{total_of[seg[0]]:.2f}",) for seg, sc in zip(C.SEGMENTS, C.SCORES)]
target_row = 1 + [seg[0] for seg in C.SEGMENTS].index(TARGET)
table_slide(s, top, rows, [Inches(3.0)] + [Inches(1.75)] * 4 + [Inches(1.6)], [Inches(0.75)] + [Inches(0.6)] * 4, 16,
            centre_from=1, bold_rows=(target_row,), note="Score = SUMPRODUCT of the weights and the scores in Excel.")
s.notes_slide.notes_text_frame.text = (
    f"I scored each segment on market size, accessibility, buying potential and competition. {TARGET} score "
    f"{total_of[TARGET]:.2f}, the highest.")

# ================================================================== Task 5. Scores chart
s, top = content_slide(f"{TARGET} lead with {total_of[TARGET]:.2f} out of 5",
                       "Weighted score of each segment (of 5)", "5  ·  Segment scores")
names = [seg[0] for seg in C.SEGMENTS]
chart_slide(s, top, names, [total_of[n] for n in names], "0.00", 5, [names.index(TARGET)], [
    ("Highest: ", f"{TARGET} ({total_of[TARGET]:.2f})."),
    ("Next: ", f"{SECOND} ({total_of[SECOND]:.2f}): many people, but little money."),
    ("Corporate Upskillers ", "pay well, but the market is small and served."),
], size=17)
s.notes_slide.notes_text_frame.text = (
    f"{TARGET} come first. {SECOND} are the biggest group but have little money, and Corporate Upskillers pay well "
    "but are few and already served.")

# ================================================================== Task 6. Target segment
s, top = content_slide(f"Prioritise {TARGET}", "The target segment the business should focus on, and why",
                       "6  ·  Target segment")
deck.anim(s, deck.boxed_text(s, top, bold_first([
    ("Who: ", "working adults of 25 to 35 in non-IT jobs, in Lagos, Abuja and Port Harcourt."),
    ("Can pay: ", "steady pay above the ₦70,000 minimum wage; ₦50,000 a month in 3 parts."),
    ("Strong reason to buy: ", "a junior analyst job pays about ₦150,000 to ₦300,000 a month."),
    ("Easy to reach: ", "Google, Facebook, LinkedIn and WhatsApp; classes in the evenings and at weekends."),
    ("Little competition: ", "few practical, mid-price courses fit around a full-time job."),
]), size=20), 3)
s.notes_slide.notes_text_frame.text = (
    f"SkillUp Academy should prioritise {TARGET}. They can pay in parts, have a strong reason to buy, are easy to "
    "reach online, and few rivals offer practical courses that fit around a job.")

# ================================================================== Conclusion
s, top = content_slide(f"Target {TARGET} with a practical course", "What the customer analysis shows", "Conclusion")
deck.anim(s, deck.boxed_text(s, top, bold_first(C.CONCLUSION), size=20), 3)
s.notes_slide.notes_text_frame.text = (
    f"SkillUp Academy should target {TARGET} with a practical, affordable course paid in parts, and fix the low "
    "point of the journey with clear prices, reviews and a free first class.")

# ================================================================== Thank you
s = prs.slides.add_slide(LAYOUT["Title Slide"])
deck.title_card(s, "Thank You", ["Any questions?", f"{C.BUSINESS}   |   Market Research Lab   |   October 2026"],
                kicker="Capstone Project  ·  Part 2")
deck.anim_chrome(s, title_card=True)
s.notes_slide.notes_text_frame.text = "Thank you for listening."

deck.save(out_path, title=f"Capstone Part 2: Customer Analysis for {C.PRODUCT}",
          subject="Customer needs, market segments, target segment, persona and journey map",
          keywords="customer needs, segmentation, persona, customer journey map")
