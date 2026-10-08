# Market Segmentation: SkillUp Academy

The assignment: plan a new business or product, design a segmentation matrix with five target
customer segments, decide which segment is the most attractive and why, support the answer with
Google Trends research, and present the report as bar charts in PowerPoint 2013.

| File | What it is |
|---|---|
| [Market_Segmentation_Marketing.pptx](Market_Segmentation_Marketing.pptx) | The 8-slide report in the Marketing Budget deck's colours. Opens in PowerPoint 2013 and later. |
| [Market_Segmentation_PZ.pptx](Market_Segmentation_PZ.pptx) | The same report in the PZ Nigeria deck's wood design. |
| [Market_Segmentation_Mixed.pptx](Market_Segmentation_Mixed.pptx) | The same report with both palettes mixed. |
| [Segmentation_Matrix.xlsx](Segmentation_Matrix.xlsx) | The segmentation matrix, the scores and both bar charts, with live formulas. Opens in Excel 2013 and later. |
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
interest (around 43). Their interest is growing and urgent: it reached 100 in April 2026 after news
of a breach at the CAC. Cybersecurity was the most searched programme in most states. And the
customers, or the banks, telecoms and government offices that employ them, can pay for training.
The plan is to launch with a cybersecurity course and add digital marketing next.

In Excel, the weighted score is `=SUMPRODUCT($B$5:$F$5,B6:F6)`, ranked with RANK, and
INDEX/MATCH names the most attractive segment. The reasons for each score are listed under the
table.

## The presentations

The eight slides are the same in all three palettes:

1. Title
2. The new business
3. The segmentation matrix (table)
4. Google Trends research (bar chart of search interest)
5. Attractiveness scores (table)
6. The most attractive segment (bar chart of the weighted scores)
7. Why cybersecurity learners
8. Thank you

The bar charts are real PowerPoint charts with their data in an embedded workbook. The leading
bar stands out in each palette's accent colour. Text is in Calibri, with titles in Calibri Bold
(Marketing) or Cambria Bold (PZ and Mixed). Every slide has speaker notes and a transition
(Fade, Push, Wipe, Split and Cover, in turn).

## Rebuilding

Run `src/build.sh`. It needs Python with openpyxl, python-pptx, XlsxWriter, lxml, numpy and
Pillow, and LibreOffice. The slide figures are read from the finished workbook, so the two
always agree. It reuses the Office 2013 template (`../pz-analysis/src/office2013.py`), the slide
styles, wood picture and text-fit check (`../assignment/src/deck_kit.py`, `make_wood.py`,
`check_fit.py`), and the chart clean-up, transition and validation scripts in
`../marketing-budget/src`. Set `SCHEMA_DIR` to the ISO/IEC 29500 transitional schemas to check
every part of the four files against them.
