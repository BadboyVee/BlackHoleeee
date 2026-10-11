#!/usr/bin/env python3
"""Build the capstone part 2 deck: the customer analysis for CyberStart, in a plain PowerPoint 2013
style (the Marketing Budget deck's: Calibri, dark-blue titles, a thin light-blue frame, light-blue
boxes, simple tables and bar charts).

Usage: python build_customer_deck.py Customer_Analysis.xlsx template.pptx STYLE out.pptx
  The workbook must have been through LibreOffice (build.sh does this), so the worked-out
  figures (need importance and ranks, segment scores, the target) can be read from it. STYLE is
  marketing (deck_kit.py).

The slides follow the tasks in the order they were set: title, contents, key facts; 1 the
customer persona (two slides); 2 the customer journey map, its pain points and opportunities,
and a chart of how the customer feels; 3 the customer needs, the five most important, and a chart
of all twelve; 4 the four market segments; 5 the segment scores and a chart; 6 the target
segment; conclusion; sources and acknowledgement; thank you. Every slide's objects come in by
themselves (out.anim.json, for finish_deck.py).
"""
import sys

from openpyxl import load_workbook
from pptx.util import Emu, Inches, Pt

import capstone_data as D
import customer_data as C
from deck_kit import Deck, placeholder

workbook_path, template_path, style_name, out_path = sys.argv[1:5]
deck = Deck(style_name, template_path, None)
S, prs, W, H, LAYOUT = deck.S, deck.prs, deck.W, deck.H, deck.layout
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


needs = rows_of("3 Customer Needs", C.NEEDS[0][1], len(C.NEEDS), [2, 7, 8])        # need, importance, rank
importance = {n: imp for n, imp, _rank in needs}
top5 = [n for _rank, n in sorted((rank, n) for n, _imp, rank in needs)[:5]]
scores = rows_of("5-6 Segment Scores", C.SEGMENTS[0][0], len(C.SEGMENTS), [1, 6, 7])  # segment, total, rank
total_of = {s: t for s, t, _r in scores}
TARGET = min(scores, key=lambda row: row[2])[0]
SECOND = next(s for s, _t, r in scores if r == 2)
need_row = {n[1]: n for n in C.NEEDS}


# ------------------------------------------------------------------ helpers
def content_slide(title, subtitle):
    s = prs.slides.add_slide(LAYOUT["Title and Content"])
    top = deck.content(s, title, subtitle)
    deck.anim_chrome(s)
    return s, top


def bullets(s, top, points, size=20, height=Inches(4.45)):
    """The content placeholder's bullets on a light-blue box; the words before a colon in bold."""
    deck.anim(s, deck.boxed_text(s, top, [[(a, True), (b, False)] if b else [(a, False)] for a, b in points], size,
                                 height), 3)


def table_slide(s, top, rows, widths, heights, size, *, centre_from=1, bold_rows=(), note=None):
    heights = heights if isinstance(heights, list) else [heights] * len(rows)
    frame, _ = deck.table(s, placeholder(s, 1), (W - sum(widths, Emu(0))) // 2, top + Inches(0.05), rows, widths,
                          heights, size, centre_from=centre_from, bold_rows=bold_rows)
    deck.anim(s, frame, 3, "wipe-down")
    if note:
        deck.anim(s, deck.footnote(s, top + Inches(0.05) + sum(heights, Emu(0)) + Inches(0.12), note), 4)


def chart_slide(s, top, labels, values, number_format, maximum, top_bars, points):
    frame, chart = deck.bar_chart(s, placeholder(s, 1), *deck.chart_area(top), labels, values,
                                  number_format=number_format, maximum=maximum, top=top_bars)
    deck.anim(s, frame, 3, "wipe-left")
    deck.anim(s, deck.side_note(s, top, [[(a, True), (b, False)] for a, b in points], size=16), 4)
    return chart


# ================================================================== title
s = prs.slides.add_slide(LAYOUT["Title Slide"])
deck.title_card(s, "Customer Analysis", [f"{C.PRODUCT}: a beginner cybersecurity course by {C.BUSINESS}",
                                         "Capstone Project, Part 2  ·  Market Research Lab"])
deck.solid_background(s, "E4EEF8")                        # a calm, light blue background on the first slide
deck.anim_chrome(s, title_card=True)
s.notes_slide.notes_text_frame.text = (
    f"Part 2 of my capstone is a customer analysis for {C.PRODUCT}: a customer persona, a journey map, the most "
    "important needs, four market segments, their scores and the target segment.")

# ================================================================== contents
s, top = content_slide("Contents", "The six tasks, in the order they were set")
bullets(s, top, [(f"{n}. {task}: ", about.lower() + ".") for n, task, about in C.TASKS], size=20)
s.notes_slide.notes_text_frame.text = "I answer the six tasks in the order they were set."

# ================================================================== key facts
s, top = content_slide("Key Facts", "World and Nigerian data used in this analysis")
rows = [("Fact", "Figure", "Where")] + [(fact, figure, where) for fact, figure, _n, where, _k in C.WORLD]
table_slide(s, top, rows, [Inches(5.0), Inches(5.0), Inches(1.6)], [Inches(0.42)] + [Inches(0.44)] * len(C.WORLD), 14,
            centre_from=2)
s.notes_slide.notes_text_frame.text = (
    "Around the world, networks and cybersecurity is the second fastest-growing skill, and 95 percent of cyber teams "
    "have a skills gap. Nigeria is young, with a median age of about 19 and 2.1 million university students. The "
    "minimum wage is 70,000 naira a month, while junior analysts earn about 150,000 to 300,000.")

# ================================================================== 1. persona
facts = dict(P["facts"])
s, top = content_slide("1. Customer Persona", f"{P['name']}: a typical {TARGET[:-1].lower()} (made up from the "
                                              "research)")
bullets(s, top, [("Who: ", f"{facts['Age']} years old, {facts['Job'].lower()}, lives in {facts['Lives in']}."),
                 ("Education: ", facts["Education"] + "."),
                 ("Money: ", facts["Money"].replace(";", ",") + "."),
                 ("Goals: ", "; ".join(g[0].lower() + g[1:] for g in P["goals"][:2]) + "."),
                 ("Frustrations: ", "; ".join(f[0].lower() + f[1:] for f in P["frustrations"]) + "."),
                 ("In Tunde's words: ", P["quote"])], size=17)
s.notes_slide.notes_text_frame.text = (
    f"My persona is {P['name']}, a made-up customer based on the research. Tunde is 27, works in customer service in "
    "Lagos, and wants a cybersecurity job within a year, but is afraid of paying for a scam course.")

s, top = content_slide("1. Customer Persona (continued)", "What makes Tunde buy")
bullets(s, top, [("Triggers: ", "; ".join(t[0].lower() + t[1:] for t in P["triggers"]) + "."),
                 ("Worries: ", "is it a scam? Can I fit it round work? Will I get a job?"),
                 ("How Tunde chooses: ", "; ".join(c[0].lower() + c[1:] for c in P["criteria"]) + "."),
                 ("How Tunde pays: ", f"₦{D.PRICE:,} in {D.INSTALMENTS} parts, from salary."),
                 ("Where to reach Tunde: ", "Google, YouTube, TikTok, Facebook groups, WhatsApp and LinkedIn.")],
        size=18)
s.notes_slide.notes_text_frame.text = (
    "Tunde is pushed to act by breach news, a friend's new tech job, or a free first class. Tunde chooses on labs, "
    "the full price, reviews and the certificate, and pays in three parts.")

# ================================================================== 2. journey map
journey = dict(C.JOURNEY)
s, top = content_slide("2. Customer Journey Map", "What Tunde does and thinks at each stage")
rows = [("", ) + tuple(C.STAGES)]
rows += [([[(label, True)]],) + tuple(journey[label]) for label in ("Doing", "Touchpoints", "Thinking and feeling")]
rows += [([[("Feeling (1-5)", True)]],) + tuple(str(v) for v in C.FEELING)]
table_slide(s, top, rows, [Inches(1.7)] + [Inches(2.0)] * 5, [Inches(0.42), Inches(1.15), Inches(0.95), Inches(1.0),
                                                                Inches(0.42)], 12, centre_from=1)
s.notes_slide.notes_text_frame.text = (
    "The journey has five stages: awareness, consideration, purchase, learning and after the course. Tunde starts "
    "curious, is most worried when comparing courses, and ends proud on getting a job.")

s, top = content_slide("2. Customer Journey Map (continued)", "Pain points, and what SkillUp Academy can do")
rows = [("", ) + tuple(C.STAGES)]
rows += [([[(label, True)]],) + tuple(journey[label]) for label in ("Pain points", "Opportunities")]
table_slide(s, top, rows, [Inches(1.7)] + [Inches(2.0)] * 5, [Inches(0.42), Inches(1.2), Inches(1.5)], 14,
            centre_from=1)
s.notes_slide.notes_text_frame.text = (
    "Each pain point is a chance to do better: beginner videos, clear prices and reviews, instalments, weekly labs "
    "and fast support, and help to find a job.")

s, top = content_slide("2. How Tunde Feels", "Feeling at each stage, from 1 (very bad) to 5 (very good)")
chart_slide(s, top, C.STAGES, C.FEELING, "0", 5, [C.FEELING.index(min(C.FEELING))], [
    ("Lowest: ", "consideration (2), when Tunde fears scams and can't find prices."),
    ("Highest: ", "after the course (5), with a job."),
    ("Fix: ", "clear prices, real reviews and a free first class."),
])
s.notes_slide.notes_text_frame.text = (
    "Tunde feels worst when comparing courses and best after getting a job. Clear prices, reviews and a free class "
    "would lift the low point.")

# ================================================================== 3. needs
s, top = content_slide("3. Customer Needs", "Three functional, economic, emotional and social needs")
by_type = {t: [n for n in C.NEEDS if n[0] == t] for t in C.NEED_TYPES}
rows = [tuple(C.NEED_TYPES)] + [tuple(by_type[t][i][1] for t in C.NEED_TYPES) for i in range(3)]
table_slide(s, top, rows, [Inches(2.95)] * 4, [Inches(0.5)] + [Inches(1.0)] * 3, 17, centre_from=0)
s.notes_slide.notes_text_frame.text = (
    "Functional needs are about what the course does, economic needs about money, emotional needs about feelings, "
    "and social needs about other people.")

s, top = content_slide("3. The 5 Most Important Needs", "Score = how often it came up × how much it affects buying "
                                                         "(out of 25)")
rows = [("Rank", "Need", "Type", "Score")]
rows += [(str(k + 1), name, need_row[name][0], str(importance[name])) for k, name in enumerate(top5)]
table_slide(s, top, rows, [Inches(1.0), Inches(5.6), Inches(2.0), Inches(1.4)], [Inches(0.5)] + [Inches(0.62)] * 5,
            18, centre_from=2)
s.notes_slide.notes_text_frame.text = (
    "The five most important needs are hands-on skills and an affordable price, then certificate preparation, a "
    "better-paid job and feeling supported.")

s, top = content_slide("3. All Twelve Needs", "Score of each need (out of 25); the top five are dark blue")
chart = chart_slide(s, top, [n[2] for n in C.NEEDS], [importance[n[1]] for n in C.NEEDS], "0", 25,
                    [i for i, n in enumerate(C.NEEDS) if n[1] in top5], [
    ("Skills and money ", "matter most."),
    ("Top 5: ", "two functional, two economic and one emotional need."),
])
chart.category_axis.tick_labels.font.size = Pt(13)
chart.plots[0].data_labels.font.size = Pt(13)
s.notes_slide.notes_text_frame.text = "The chart shows all twelve needs. Skills and money matter most."

# ================================================================== 4. segments
s, top = content_slide("4. Four Market Segments", "Each segment on the four bases")
rows = [("Base",) + tuple(seg[0] for seg in C.SEGMENTS)]
rows += [([[(b, True)]],) + tuple(seg[1 + i] for seg in C.SEGMENTS) for i, (b, _a) in enumerate(C.BASES)]
table_slide(s, top, rows, [Inches(1.75)] + [Inches(2.5)] * 4, [Inches(0.45)] + [Inches(1.0)] * 4, 13, centre_from=9)
s.notes_slide.notes_text_frame.text = (
    "The four segments are Campus Starters, Career Switchers, Corporate Upskillers and Women in Tech Starters, each "
    "described by age and job, location, attitudes and behaviour.")

# ================================================================== 5. scores
s, top = content_slide("5. Segment Scores", "Each scored 1 (poor) to 5 (best); for competition, 5 = little "
                                            "competition")
rows = [("Segment",) + tuple(f"{c} ({int(w * 100)}%)" for c, w in C.CRITERIA) + ("Score (of 5)",)]
rows += [(seg[0],) + tuple(str(v) for v in sc) + (f"{total_of[seg[0]]:.2f}",) for seg, sc in zip(C.SEGMENTS, C.SCORES)]
table_slide(s, top, rows, [Inches(3.0)] + [Inches(1.75)] * 4 + [Inches(1.6)], [Inches(0.75)] + [Inches(0.6)] * 4, 16,
            bold_rows=(1 + [seg[0] for seg in C.SEGMENTS].index(TARGET),),
            note="Score = SUMPRODUCT of the weights and the scores (see Excel).")
s.notes_slide.notes_text_frame.text = (
    f"I scored each segment on market size, accessibility, buying potential and competition. {TARGET} score "
    f"{total_of[TARGET]:.2f}, the highest.")

s, top = content_slide("5. Segment Scores Compared", "Weighted score of each segment (out of 5)")
names = [seg[0] for seg in C.SEGMENTS]
chart_slide(s, top, names, [total_of[n] for n in names], "0.00", 5, [names.index(TARGET)], [
    ("Highest: ", f"{TARGET} ({total_of[TARGET]:.2f})."),
    ("Next: ", f"{SECOND} ({total_of[SECOND]:.2f}): many people, but little money."),
])
s.notes_slide.notes_text_frame.text = f"{TARGET} come first, then {SECOND}."

# ================================================================== 6. target
s, top = content_slide(f"6. Target Segment: {TARGET}", "The segment SkillUp Academy should focus on first")
bullets(s, top, [("Who: ", "working adults aged 25 to 35 in non-IT jobs, in Lagos, Abuja and Port Harcourt."),
                 ("They can pay: ", "they earn more than the ₦70,000 minimum wage and can pay ₦50,000 a month."),
                 ("Good reason to buy: ", "a junior analyst job pays about ₦150,000 to ₦300,000 a month."),
                 ("Easy to reach: ", "Google, Facebook, LinkedIn and WhatsApp; evening and weekend classes."),
                 ("Little competition: ", "few practical, affordable courses fit around a full-time job.")], size=19)
s.notes_slide.notes_text_frame.text = (
    f"SkillUp Academy should target {TARGET} first: they can pay in parts, have a strong reason to buy, are easy to "
    "reach, and few courses suit them.")

# ================================================================== conclusion
s, top = content_slide("Conclusion", "What I found")
bullets(s, top, [(a, b) for a, b in C.CONCLUSION], size=20)
s.notes_slide.notes_text_frame.text = (
    f"In short, customers need hands-on skills at a fair price, {TARGET} are the best target, and the hardest part "
    "of the journey is choosing a course.")

# ================================================================== sources and acknowledgement
s, top = content_slide("Sources", "Where the data came from")
bullets(s, top, [("World: ", "World Economic Forum, Future of Jobs Report 2025; ISC2 Cybersecurity Workforce Study "
                             "2025."),
                 ("Nigeria: ", "NUC student numbers; the National Minimum Wage Act 2024; UN and World Bank data; "
                               "DataReportal."),
                 ("My own research: ", "Google Trends, Google search, social media, competitor and course reviews "
                                       "(part 1)."),
                 ("Help: ", "I used an AI assistant to help with research and slide design.")], size=18)
s.notes_slide.notes_text_frame.text = (
    "The full list of sources, with links, is in the Sources sheet of the Excel file. I used an AI assistant to help "
    "with the research and the slide design.")

# ================================================================== thank you
s = prs.slides.add_slide(LAYOUT["Title Slide"])
deck.title_card(s, "Thank You", ["Any questions?", f"{C.BUSINESS}  ·  Capstone Project, Part 2"])
deck.anim_chrome(s, title_card=True)
s.notes_slide.notes_text_frame.text = "Thank you for listening."

deck.save(out_path, title=f"Capstone Part 2: Customer Analysis for {C.PRODUCT}",
          subject="Customer persona, journey map, the 5 most important needs, four segments, scores and target",
          keywords="customer persona, customer journey map, customer needs, segmentation, target segment")
