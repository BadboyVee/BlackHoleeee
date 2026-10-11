#!/usr/bin/env python3
"""Build the capstone part 2 deck: the customer analysis for CyberStart (needs, segments, target,
persona and journey map), made the way it would be in PowerPoint 2013, in the charcoal and gold
design of ../../assignment/src/deck_kit.py.

Usage: python build_customer_deck.py Customer_Analysis.xlsx template.pptx wood.jpg STYLE out.pptx
  The workbook must have been through LibreOffice (build.sh does this), so the worked-out
  figures (need importance and ranks, segment scores, the target) can be read from it.

Slides: 1. title, 2. world and Nigerian data, 3. customer needs, 4. the five most important
needs, 5. need importance (bar chart), 6. segmentation bases, 7. the four segments, 8. segment
scores, 9. the scores (bar chart), 10. the target segment, 11. the persona, 12-13. the journey
map, 14. the feeling curve (line chart), 15. conclusion, 16. thank you. Every slide's objects
come in by themselves; the plan is saved as out.anim.json for finish_deck.py.
"""
import sys

from openpyxl import load_workbook
from pptx.chart.data import CategoryChartData
from pptx.enum.chart import XL_CHART_TYPE, XL_LABEL_POSITION, XL_MARKER_STYLE, XL_TICK_LABEL_POSITION, XL_TICK_MARK
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from lxml import etree
from pptx.util import Emu, Inches, Pt

import customer_data as C
from deck_kit import A_NS, C_NS, Deck, into_placeholder, placeholder, rgb

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


needs = rows_of("Customer Needs", C.NEEDS[0][1], len(C.NEEDS), [2, 7, 8])          # need, importance, rank
importance = {n: imp for n, imp, _rank in needs}
rank_of = {n: rank for n, _imp, rank in needs}
top5 = sorted((rank, n) for n, _imp, rank in needs)[:5]
scores = rows_of("Segment Scores", C.SEGMENTS[0][0], len(C.SEGMENTS), [1, 6, 7])      # segment, total, rank
total_of = {s: t for s, t, _r in scores}
TARGET = min(scores, key=lambda row: row[2])[0]
SECOND = next(s for s, _t, r in scores if r == 2)


# ------------------------------------------------------------------ helpers
def content_slide(title, subtitle):
    s = prs.slides.add_slide(LAYOUT["Title and Content"])
    top = deck.content(s, title, subtitle)
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
                                         f"{C.BUSINESS}  ·  Capstone Project, Part 2"], size=54)
deck.anim_chrome(s, title_card=True)
s.notes_slide.notes_text_frame.text = (
    f"Part 2 of my capstone analyses the customers of {C.PRODUCT}: their needs, four market segments, the target "
    "segment, a customer persona and a customer journey map.")

# ================================================================== 2. World and Nigerian data
s, top = content_slide("World and Nigerian Data", "Real, published figures behind the analysis")
rows = [("Fact", "Figure", "Where")] + [([[(fact, True)]], figure, where) for fact, figure, _n, where, _k in C.WORLD]
table_slide(s, top, rows, [Inches(5.0), Inches(5.0), Inches(1.6)], [Inches(0.42)] + [Inches(0.43)] * len(C.WORLD), 14,
            centre_from=2, note="Sources: World Economic Forum, ISC2, NUC, UN and World Bank data, DataReportal "
                                "(full list in Excel).")
s.notes_slide.notes_text_frame.text = (
    "Around the world, networks and cybersecurity is the second fastest-growing skill, and 95 percent of cyber teams "
    "have a skills gap, led by AI and cloud security. Nigeria is young, with a median age of about 19 and 2.1 "
    "million university students. The minimum wage is 70,000 naira a month, while junior analysts earn about "
    "150,000 to 300,000.")

# ================================================================== 3. Customer needs
s, top = content_slide("Customer Needs", "Three functional, economic, emotional and social needs")
by_type = {t: [n for n in C.NEEDS if n[0] == t] for t in C.NEED_TYPES}
rows = [tuple(C.NEED_TYPES)] + [tuple(by_type[t][i][1] for t in C.NEED_TYPES) for i in range(3)]
table_slide(s, top, rows, [Inches(2.95)] * 4, [Inches(0.5)] + [Inches(1.1)] * 3, 18, centre_from=0,
            note="Each need is backed by evidence from the research; see the Customer Needs sheet in Excel.")
s.notes_slide.notes_text_frame.text = (
    "Functional needs are about what the course does: hands-on skills, a flexible timetable and certificate "
    "preparation. Economic needs are about money, emotional needs about trust, support and hope, and social needs "
    "about community, status and inclusion.")

# ================================================================== 4. The five most important needs
s, top = content_slide("The 5 Most Important Needs", "Importance = how often it came up × its effect on buying "
                                                      "(of 25)")
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

# ================================================================== 5. Need importance chart
s, top = content_slide("Importance of Each Need", "Score out of 25; the top five highlighted")
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

# ================================================================== 6. Segmentation bases
s, top = content_slide("Segmentation Bases", "Four ways to group the customers")
rows = [("Base", "What it looks at")] + [([[(b, True)]], about) for b, about in C.BASES]
table_slide(s, top, rows, [Inches(3.2), Inches(8.6)], [Inches(0.55)] + [Inches(0.8)] * 4, 20,
            note=f"Together they give four segments of {C.PRODUCT}'s possible customers.")
s.notes_slide.notes_text_frame.text = (
    "I used all four bases: demographic, geographic, psychographic and behavioural.")

# ================================================================== 7. The four segments
s, top = content_slide("Four Market Segments", "Each segment described on the four bases")
rows = [("Base",) + tuple(seg[0] for seg in C.SEGMENTS)]
rows += [([[(b, True)]],) + tuple(seg[1 + i] for seg in C.SEGMENTS) for i, (b, _a) in enumerate(C.BASES)]
table_slide(s, top, rows, [Inches(1.75)] + [Inches(2.5)] * 4, [Inches(0.45)] + [Inches(1.0)] * 4, 13, centre_from=9)
s.notes_slide.notes_text_frame.text = (
    "The four segments are Campus Starters, Career Switchers, Corporate Upskillers and Women in Tech Starters.")

# ================================================================== 8. Segment scores
s, top = content_slide("Segment Scores", "Scored 1 (poor) to 5 (best); weights in brackets; for competition, 5 = "
                                         "little competition")
rows = [("Segment",) + tuple(f"{c} ({int(w * 100)}%)" for c, w in C.CRITERIA) + ("Score (of 5)",)]
rows += [(seg[0],) + tuple(str(v) for v in sc) + (f"{total_of[seg[0]]:.2f}",) for seg, sc in zip(C.SEGMENTS, C.SCORES)]
target_row = 1 + [seg[0] for seg in C.SEGMENTS].index(TARGET)
table_slide(s, top, rows, [Inches(3.0)] + [Inches(1.75)] * 4 + [Inches(1.6)], [Inches(0.75)] + [Inches(0.6)] * 4, 16,
            centre_from=1, bold_rows=(target_row,), note="Score = SUMPRODUCT of the weights and the scores in Excel.")
s.notes_slide.notes_text_frame.text = (
    f"I scored each segment on market size, accessibility, buying potential and competition. {TARGET} score "
    f"{total_of[TARGET]:.2f}, the highest.")

# ================================================================== 9. Scores chart
s, top = content_slide("The Segments Compared", "Weighted score of each segment (of 5)")
names = [seg[0] for seg in C.SEGMENTS]
chart_slide(s, top, names, [total_of[n] for n in names], "0.00", 5, [names.index(TARGET)], [
    ("Highest: ", f"{TARGET} ({total_of[TARGET]:.2f})."),
    ("Next: ", f"{SECOND} ({total_of[SECOND]:.2f}): many people, but little money."),
    ("Corporate Upskillers ", "pay well, but the market is small and served."),
], size=17)
s.notes_slide.notes_text_frame.text = (
    f"{TARGET} come first. {SECOND} are the biggest group but have little money, and Corporate Upskillers pay well "
    "but are few and already served.")

# ================================================================== 10. Target segment
s, top = content_slide(f"Target Segment: {TARGET}", "The segment the business should prioritise, and why")
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

# ================================================================== 11. Persona
s, top = content_slide("Customer Persona", "A fictional customer from the target segment, built from the research")
y0 = top + Inches(0.05)
left_w, gap = Inches(4.3), Inches(0.25)
lx = deck.left
card_h = H - y0 - Inches(0.75)
left = deck.card(s, lx, y0, left_w, card_h)
avatar = s.shapes.add_shape(MSO_SHAPE.OVAL, lx + Inches(0.35), y0 + Inches(0.3), Inches(1.2), Inches(1.2))
avatar.fill.solid()
avatar.fill.fore_color.rgb = rgb(S["head_fill"] or S["rule"])
avatar.line.fill.background()
deck.write(avatar.text_frame, [P["initials"]], size=28, colour=S["rule"], bold=True, align=PP_ALIGN.CENTER)
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

# ================================================================== 12-13. Journey map
journey = dict(C.JOURNEY)
for title, labels, sub in (("Customer Journey Map", ["Doing", "Touchpoints", "Thinking and feeling"],
                            f"{P['name']}'s journey: what Tunde does, where, and how it feels"),
                           ("Journey Map: Pain Points and Opportunities", ["Pain points", "Opportunities"],
                            "What goes wrong at each stage, and what SkillUp Academy can do")):
    s, top = content_slide(title, sub)
    rows = [("Stage",) + tuple(C.STAGES)] + [([[(label, True)]],) + tuple(journey[label]) for label in labels]
    row_h = Inches(1.35) if len(labels) == 3 else Inches(1.6)
    table_slide(s, top, rows, [Inches(1.7)] + [Inches(2.02)] * 5, [Inches(0.45)] + [row_h] * len(labels), 13,
                centre_from=9)
    s.notes_slide.notes_text_frame.text = (
        "The journey has five stages: awareness, consideration, purchase, learning and after the course. "
        + ("Tunde starts curious, becomes anxious when choosing a course, and ends proud on getting a job."
           if len(labels) == 3 else
           "Each pain point is an opportunity: beginner videos, clear prices and reviews, instalments, weekly labs "
           "and fast support, and job help."))

# ================================================================== 14. Feeling curve
s, top = content_slide("How the Customer Feels", "Feeling at each stage: 1 (very negative) to 5 (very positive)")
data = CategoryChartData(number_format="0")
data.categories = C.STAGES
data.add_series("Feeling", C.FEELING)
frame = s.shapes.add_chart(XL_CHART_TYPE.LINE_MARKERS, *deck.chart_area(top), data)
chart = frame.chart
chart.font.name, chart.font.size, chart.font.color.rgb = S["body_font"], Pt(15), rgb(S["text"])
chart.has_legend = False
chart.has_title = False
series = chart.plots[0].series[0]
series.smooth = False
series.format.line.color.rgb = rgb(S["rule"])
series.format.line.width = Pt(3.5)
series.marker.style = XL_MARKER_STYLE.CIRCLE
series.marker.size = 12
series.marker.format.fill.solid()
series.marker.format.fill.fore_color.rgb = rgb(S["head_fill"] or S["text"])
series.marker.format.line.color.rgb = rgb(S["head_fill"] or S["text"])
plot = chart.plots[0]
plot.has_data_labels = True
plot.data_labels.position = XL_LABEL_POSITION.ABOVE
plot.data_labels.font.size, plot.data_labels.font.bold = Pt(16), True
cat, val = chart.category_axis, chart.value_axis
cat.major_tick_mark = XL_TICK_MARK.NONE
cat.format.line.color.rgb = rgb("BFBFBF")
val.minimum_scale, val.maximum_scale, val.major_unit = 0, 5.5, 1
val.has_major_gridlines = False
val.major_tick_mark = XL_TICK_MARK.NONE
val.tick_label_position = XL_TICK_LABEL_POSITION.NONE
val.format.line.fill.background()
if S.get("background"):                                  # Format Chart Area > No fill
    chart._chartSpace.find(qn("c:chart")).addnext(etree.fromstring(
        f'<c:spPr xmlns:c="{C_NS}" xmlns:a="{A_NS}"><a:noFill/><a:ln><a:noFill/></a:ln></c:spPr>'))
into_placeholder(placeholder(s, 1), frame)
deck.anim(s, frame, 3, "wipe-left")
low = C.STAGES[C.FEELING.index(min(C.FEELING))]
deck.anim(s, deck.side_note(s, top, bold_first([
    ("Lowest point: ", f"{low.lower()}, choosing a course: fear of scams and hidden prices."),
    ("Fix: ", "clear prices, real reviews and a free first class."),
    ("Highest point: ", "after the course, with a job."),
]), size=17), 4)
s.notes_slide.notes_text_frame.text = (
    "Tunde's feelings dip when he compares courses, because he fears scams and cannot find prices. Clear prices, "
    "reviews and a free first class lift that low point.")

# ================================================================== 15. Conclusion
s, top = content_slide("Conclusion", "What the customer analysis shows")
deck.anim(s, deck.boxed_text(s, top, bold_first(C.CONCLUSION), size=20), 3)
s.notes_slide.notes_text_frame.text = (
    f"SkillUp Academy should target {TARGET} with a practical, affordable course paid in parts, and fix the low "
    "point of the journey with clear prices, reviews and a free first class.")

# ================================================================== 16. Thank you
s = prs.slides.add_slide(LAYOUT["Title Slide"])
deck.title_card(s, "Thank You", ["Any questions?", f"{C.BUSINESS}  ·  Capstone Project, Part 2"])
deck.anim_chrome(s, title_card=True)
s.notes_slide.notes_text_frame.text = "Thank you for listening."

deck.save(out_path, title=f"Capstone Part 2: Customer Analysis for {C.PRODUCT}",
          subject="Customer needs, market segments, target segment, persona and journey map",
          keywords="customer needs, segmentation, persona, customer journey map")
