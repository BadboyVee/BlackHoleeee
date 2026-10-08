#!/usr/bin/env python3
"""Build the market segmentation deck for SkillUp Academy in one of three colour palettes, made
the way it would be in PowerPoint 2013.

Usage: python build_deck.py deck_data.json template.pptx wood.jpg STYLE out.pptx
  STYLE is marketing, pz or mixed: the palettes in ../../assignment/src/deck_kit.py (the
  Marketing Budget deck's, the PZ Nigeria deck's wood design, and both mixed).

Slides: 1. title, 2. the new business, 3. the segmentation matrix, 4. the Google Trends research
(bar chart), 5. the attractiveness scores, 6. the most attractive segment (bar chart), 7. why it
is the most attractive, 8. thank you. deck_data.json comes from export_deck_data.py, which reads
every figure out of the finished Segmentation_Matrix.xlsx, so the slides match the workbook.
"""
import json
import sys

from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Emu, Inches, Pt

from deck_kit import Deck, place, placeholder, rgb

data_path, template_path, wood_path, style_name, out_path = sys.argv[1:6]
deck = Deck(style_name, template_path, wood_path)
S, prs, W, H, LAYOUT = deck.S, deck.prs, deck.W, deck.H, deck.layout
data = json.load(open(data_path))
SEG = data["segments"]
BEST = min(SEG, key=lambda s: s["rank"])
SECOND = next(s for s in SEG if s["rank"] == 2)
TOP = SEG.index(BEST)
BUSINESS = data["business"]


def boxed_text(slide, top, paragraphs, size, height=Inches(4.45)):
    """The content placeholder's text in a tinted box; programme names in bold, in the style's
    colour."""
    box = deck.rect(slide, Inches(1.0), top + Inches(0.05), W - Inches(2.0), height, fill=S["box"])
    body = placeholder(slide, 1)
    place(body, Inches(1.35), top + Inches(0.25), W - Inches(2.7), height - Inches(0.4))
    box._element.getparent().remove(box._element)
    body._element.addprevious(box._element)              # the box behind the text
    deck.write(body.text_frame, paragraphs, size=size, colour=S["text"], after=10)
    body.text_frame.vertical_anchor = MSO_ANCHOR.MIDDLE
    for para in body.text_frame.paragraphs:
        for run in para.runs:
            if run.font.bold:
                run.font.color.rgb = rgb(S["names"])
    return body


def side_note(slide, top, paragraphs, size=17):
    """A tinted box beside a chart, holding a few short points."""
    x, w, h = Inches(8.55), W - Inches(8.55) - Inches(0.85), Inches(4.4)
    deck.rect(slide, x, top + Inches(0.05), w, h, fill=S["box"])
    note = deck.textbox(slide, x + Inches(0.25), top + Inches(0.25), w - Inches(0.5), h - Inches(0.4), paragraphs,
                        size=size, colour=S["text"], after=12)
    note.text_frame.vertical_anchor = MSO_ANCHOR.MIDDLE
    return note


def chart_area(top):
    return Inches(0.9), top - Inches(0.05), Inches(7.45), Inches(4.55)


# ================================================================== 1. Title
s = prs.slides.add_slide(LAYOUT["Title Slide"])
deck.title_card(s, "Market Segmentation", [f"{BUSINESS}: a new digital-skills training business",
                                           "Market Research Lab  ·  Google Trends, Nigeria, past 12 months"],
                size=44)
s.notes_slide.notes_text_frame.text = (
    f"My assignment is a market segmentation for a new business, {BUSINESS}, a digital-skills training "
    "academy. I designed a segmentation matrix with five target customer segments and used Google Trends to "
    "find the most attractive one.")

# ================================================================== 2. The new business
s = prs.slides.add_slide(LAYOUT["Title and Content"])
top = deck.content(s, "The New Business", "What I plan to launch, and how I chose who to sell to")
boxed_text(s, top, [
    [(BUSINESS, True), (" will teach short, practical digital-skills courses.", False)],
    [("Classes will run online and at weekends, so students and workers can attend.", False)],
    [("Customers are grouped by the skill they want to learn, which gives ", False), ("five segments", True),
     (".", False)],
    [("Google Trends shows how much each segment searches, and a scoring matrix picks the best one.", False)],
], size=24)
s.notes_slide.notes_text_frame.text = (
    f"{BUSINESS} will run short, practical courses online and at weekends. I segmented the customers by the "
    "skill they want to learn, because each skill matches a search term I could measure on Google Trends.")

# ================================================================== 3. Segmentation matrix
s = prs.slides.add_slide(LAYOUT["Title and Content"])
top = deck.content(s, "Segmentation Matrix", f"Five target customer segments for {BUSINESS}")
rows = [("Segment", "Who they are", "What they want", "Search interest")]
rows += [([[(x["name"], True)]], x["who"], x["want"], str(x["interest"])) for x in SEG]
widths = [Inches(2.9), Inches(4.3), Inches(3.1), Inches(1.6)]
table_w = sum(widths, Emu(0))
heights = [Inches(0.55)] + [Inches(0.7)] * len(SEG)
deck.table(s, placeholder(s, 1), (W - table_w) // 2, top + Inches(0.05), rows, widths, heights, 15, centre_from=3)
deck.textbox(s, Inches(0.8), top + Inches(0.05) + sum(heights, Emu(0)) + Inches(0.15), W - Inches(1.6),
             Inches(0.4), ["Search interest: the average Google Trends score in Nigeria over the past 12 months "
                           "(0 to 100)."], size=14, colour=S["muted"], align=PP_ALIGN.CENTER)
s.notes_slide.notes_text_frame.text = (
    "These are the five target customer segments. For each one I describe who they are and what they want, and "
    "give the average Google Trends search interest for their skill in Nigeria over the past 12 months.")

# ================================================================== 4. Google Trends research
s = prs.slides.add_slide(LAYOUT["Title and Content"])
top = deck.content(s, "Google Trends Research", "Average search interest in Nigeria over the past 12 months "
                                                 "(0 to 100)")
interest = [x["interest"] for x in SEG]
deck.bar_chart(s, placeholder(s, 1), *chart_area(top), [x["name"] for x in SEG], interest, number_format="0",
               maximum=50, top=[interest.index(max(interest))])
side_note(s, top, [
    [("Highest interest: ", True), ("Cybersecurity led almost all year and reached 100 in April 2026.", False)],
    [("Widest reach: ", True), ("it was the most searched in most states; Digital Marketing led in some southern "
                                "states.", False)],
    [("What people want: ", True), ("many related searches ask for free courses.", False)],
])
s.notes_slide.notes_text_frame.text = (
    f"Google Trends shows that {BEST['name'].lower()} search the most, with an average of {BEST['interest']}, "
    f"followed by {SECOND['name'].lower()} at {SECOND['interest']}. Cybersecurity reached 100 in April 2026 "
    "after news of a breach at the Corporate Affairs Commission, and it was the most searched in most states.")

# ================================================================== 5. Attractiveness scores
s = prs.slides.add_slide(LAYOUT["Title and Content"])
top = deck.content(s, "Attractiveness Scores", "Each factor is scored 1 (poor) to 5 (best); its weight is "
                                                "in brackets")
factor_heads = ["Interest", "Growth", "Spread", "Ability to pay", "Competition"]
rows = [["Segment"] + [f"{f} ({int(w * 100)}%)" for f, w in zip(factor_heads, data["weights"])] + ["Score (of 5)"]]
rows += [[x["name"]] + [str(v) for v in x["scores"]] + [f"{x['total']:.2f}"] for x in SEG]
widths = [Inches(3.0)] + [Inches(1.45)] * 5 + [Inches(1.5)]
table_w = sum(widths, Emu(0))
heights = [Inches(0.8)] + [Inches(0.58)] * len(SEG)
deck.table(s, placeholder(s, 1), (W - table_w) // 2, top + Inches(0.05), rows, widths, heights, 16,
           bold_rows=(TOP + 1,))
deck.textbox(s, Inches(0.8), top + Inches(0.05) + sum(heights, Emu(0)) + Inches(0.15), W - Inches(1.6),
             Inches(0.7), ["Score = the weighted total (SUMPRODUCT in Excel). Search interest comes from Google "
                           "Trends; for competition, 5 means little competition."],
             size=14, colour=S["muted"], align=PP_ALIGN.CENTER)
s.notes_slide.notes_text_frame.text = (
    "I scored each segment from 1 to 5 on five factors: search interest, growth and spread across Nigeria from "
    "Google Trends, and ability to pay and competition from my own judgement. Each factor has a weight, and the "
    f"weighted total is out of 5. {BEST['name']} score {BEST['total']:.2f}, the highest.")

# ================================================================== 6. Most attractive segment
s = prs.slides.add_slide(LAYOUT["Title and Content"])
top = deck.content(s, "Most Attractive Segment", "Weighted attractiveness score of each segment (out of 5)")
totals = [x["total"] for x in SEG]
deck.bar_chart(s, placeholder(s, 1), *chart_area(top), [x["name"] for x in SEG], totals, number_format="0.00",
               maximum=5, top=[TOP])
note = side_note(s, top, [
    [(f"{BEST['total']:.2f}", True)],
    [("out of 5", False)],
    [(BEST["name"], True)],
    [("are the most attractive segment, ahead of ", False), (SECOND["name"].lower(), True),
     (f" ({SECOND['total']:.2f}).", False)],
])
big = note.text_frame.paragraphs[0].runs[0]
big.font.size, big.font.color.rgb = Pt(54), rgb(S["title"])          # the score, large
for para in note.text_frame.paragraphs[:3]:
    para.alignment = PP_ALIGN.CENTER
note.text_frame.paragraphs[1].space_after = Pt(0)
s.notes_slide.notes_text_frame.text = (
    f"This bar chart shows the weighted scores. {BEST['name']} come first with {BEST['total']:.2f} out of 5, then "
    f"{SECOND['name'].lower()} with {SECOND['total']:.2f}.")

# ================================================================== 7. Why
s = prs.slides.add_slide(LAYOUT["Title and Content"])
short = BEST["name"].replace(" learners", "")
top = deck.content(s, f"Why {short} Learners?", "The reasons, from the Google Trends research and the scores")
boxed_text(s, top, [
    [("Biggest demand: ", True), (f"the highest Google Trends interest (around {BEST['interest']}).", False)],
    [("Growing and urgent: ", True), ("it reached 100 in April 2026 after news of a breach at the CAC.", False)],
    [("Nationwide: ", True), ("it was the most searched programme in most states.", False)],
    [("Customers can pay: ", True), ("bank, telecom and government staff, and employers who sponsor training.",
                                     False)],
    [("My plan: ", True), (f"launch with a {short.lower()} course, then add {SECOND['name'].split(' learners')[0].lower()}"
                           f" ({SECOND['total']:.2f}), using “free class” offers in the adverts.", False)],
], size=21)
s.notes_slide.notes_text_frame.text = (
    f"{BEST['name']} are the most attractive segment because they search the most, their interest is growing "
    "and urgent after the CAC breach news, they are spread across the country, and they or their employers "
    "can pay. So I would launch with a cybersecurity course and add digital marketing next.")

# ================================================================== 8. Thank you
s = prs.slides.add_slide(LAYOUT["Title Slide"])
deck.title_card(s, "Thank You", ["Any questions?", f"{BUSINESS}  ·  Market Research Lab"])
s.notes_slide.notes_text_frame.text = "Thank you for listening."

deck.save(out_path, title=f"Market Segmentation: {BUSINESS}",
          subject="Segmentation matrix with five target customer segments, supported by Google Trends",
          keywords="market segmentation, Google Trends, bar chart")
