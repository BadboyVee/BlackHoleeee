# Market Segmentation: SkillUp Academy

The assignment: plan a new business or product, design a segmentation matrix with five target
customer segments, decide which segment is the most attractive and why, support the answer with
Google Trends research, and present the report as bar charts in PowerPoint 2013.

| File | What it is |
|---|---|
| [Market_Segmentation.pptx](Market_Segmentation.pptx) | The 9-slide report in a clean, minimal design, with animations and slide timings. Opens in PowerPoint 2013 and later. |
| [Segmentation_Matrix.xlsx](Segmentation_Matrix.xlsx) | The segmentation matrix, the scores, both bar charts (live formulas) and the desk research with links. Opens in Excel 2013 and later. |
| [src/](src/) | The scripts that build all four files. |

## The business and the segments

SkillUp Academy is a new digital-skills training business: short, practical courses, online and
at weekends. Its customers are grouped by the skill they want to learn, so each segment matches
one Google Trends search term.

| Segment | Who they are | What they want | Google Trends interest |
|---|---|---|---|
| Cybersecurity learners | IT students, and staff of banks, telecoms and government | To protect systems and get security jobs | 43 |
| Digital marketing learners | Small business owners, traders and social media managers | To sell more online with social media and adverts | 33 |
| Data analytics learners | Graduates, and staff in finance, NGOs and research | Data skills for better jobs and decisions | 18 |
| Generative AI learners | Students, content creators and office workers | To use AI tools and prompts to work faster | 13 |
| Web development learners | Young people and freelancers | To build websites and apps for clients | 13 |

The Google Trends figures are the Market Research Lab Task 1 results: Nigeria, past 12 months
(28 September 2025 to 28 September 2026), all categories, web search. They are the averages from
the "Interest over time" chart, the breakdown by state and the rising related queries.

## Other research

Web research backs up the Google Trends results. The figures are as these sources report them
(found on 8 October 2026). They are also in the workbook's Research sheet and on slide 5.

| Finding | Supports | Source |
|---|---|---|
| The CAC confirmed a cyber breach of its systems in April 2026, and the NDPC opened an investigation. This explains the jump to 100 on Google Trends. | Cybersecurity | [AllAfrica, 16 April 2026](https://allafrica.com/stories/202604160559.html) |
| Nigeria had only about 8,352 cybersecurity professionals in 2023, against 57,269 in South Africa. | Cybersecurity | [ISC2 figures, reported by CompTIA](https://www.comptia.org/en/blog/nigeria-and-kenya-cybersecurity-skills-gaps-and-the-workforce-opportunity/) |
| Nigerian organisations faced about 4,388 cyber attacks a week in early 2025, 47% more than a year before. | Cybersecurity | [Check Point, reported by BusinessDay](https://businessday.ng/technology/article/nigerian-organisations-recorded-4388-attacks-per-week-in-q1-check-point/) |
| About 14 million Nigerian small businesses used Facebook, Instagram and WhatsApp in 2025. | Digital marketing | [Public First report for Meta, reported by IT Edge News](https://www.itedgenews.africa/meta-platforms-deliver-820m-annual-economic-value-to-nigeria-ai-could-add-22bn-to-gdp-by-2035-report/) |
| The government's 3MTT programme aims to train three million tech talents by 2027: demand for tech skills is growing, but free training also competes. | All five | [Federal Ministry of Communications, Innovation and Digital Economy](https://3mtt.nitda.gov.ng) |

## The most attractive segment

Each segment is scored 1 (poor) to 5 (best) on five weighted factors:

| Factor | Weight | Where the score comes from |
|---|---|---|
| Search interest | 30% | Google Trends average: `=ROUND(interest/MAX(interest)*5,0)` |
| Growth | 20% | Google Trends interest over time |
| Spread across Nigeria | 15% | Google Trends breakdown by state |
| Ability to pay | 20% | Judgement |
| Competition | 15% | Judgement (5 means little competition) |

| Segment | Weighted score (of 5) | Rank |
|---|---|---|
| Cybersecurity learners | 4.50 | 1 |
| Digital marketing learners | 3.50 | 2 |
| Generative AI learners | 2.85 | 3 |
| Data analytics learners | 2.75 | 4 |
| Web development learners | 2.20 | 5 |

**Cybersecurity learners are the most attractive segment.** They have the highest Google Trends
interest (around 43), and cybersecurity was the most searched programme in most states. Their
interest is growing and urgent: it reached 100 in April 2026, when the CAC confirmed a cyber
breach, and attacks on Nigerian organisations rose 47% in a year. Nigeria has too few experts
(about 8,352 in 2023), so employers need trained people. And the customers, or the banks,
telecoms and government offices that employ them, can pay for training.
The plan is to launch with a cybersecurity course and add digital marketing next.

In Excel, the weighted score is `=SUMPRODUCT($B$5:$F$5,B6:F6)`, ranked with RANK, and
INDEX/MATCH names the most attractive segment. The reasons for each score are listed under the
table.

## The presentations

Each of the nine slides runs by itself for the time shown
(Transitions > Advance Slide > After), about 4 minutes in all; a click moves on sooner.

| Slide | Time |
|---|---|
| 1. Title | 10 s |
| 2. The new business | 25 s |
| 3. The segmentation matrix (table) | 35 s |
| 4. Google Trends research (bar chart of search interest) | 35 s |
| 5. Other research (table of findings and sources) | 35 s |
| 6. Attractiveness scores (table) | 35 s |
| 7. The most attractive segment (bar chart of the weighted scores) | 25 s |
| 8. Why cybersecurity learners | 35 s |
| 9. Thank you | 10 s |

The design is minimal: plain white slides with one teal accent colour. The title and closing
slides have a teal strip down the left edge; the content slides have a left-aligned title in
Calibri Light under a short teal line, a grey subtitle, and a small footer with the slide
number. Text sits on soft grey cards with a teal edge; the tables are open, with teal headings
and thin grey lines; and the bar charts are light grey, with the leading bar in teal. Body text
is in Calibri.

The bar charts are real PowerPoint charts with their data in an embedded workbook. Every slide
has speaker notes and a transition: Fade on the title and closing slides, Push in between.

Every slide is animated, with no clicks needed (Animations > Start: After Previous, 0.5 s each):
the title fades in as its line wipes in from the left, then the subtitle fades in, then the main
object: tables wipe in from the top, bar charts wipe in from the left so the bars grow, and text
boxes fade in. Last come the notes beside or under the chart or table. To change an animation or
timing in PowerPoint, use the Animation Pane (Animations tab) and Advance Slide (Transitions tab).

## Rebuilding

Run `src/build.sh`. It needs Python with openpyxl, python-pptx, XlsxWriter, lxml, numpy and
Pillow, and LibreOffice. The slide figures are read from the finished workbook, so the two
always agree. It reuses the Office 2013 template (`../pz-analysis/src/office2013.py`), the slide
styles and text-fit check (`../assignment/src/deck_kit.py`, `check_fit.py`), and the chart
clean-up, transition and validation scripts in `../marketing-budget/src`. Set `SCHEMA_DIR` to the
ISO/IEC 29500 transitional schemas to check every part of both files against them. The deck can
also be built in the earlier Marketing, PZ (wood) and Mixed designs: add `marketing`, `pz` or
`mixed` to `STYLES` in `build.sh`.
