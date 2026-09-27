# PZ Nigeria Limited: PESTLE, SWOT and Industry Analysis

A written report, an Excel workbook and a PowerPoint deck that analyse PZ Nigeria Limited
(Marketing Department, Ilupeju, Lagos). The company facts come from the PZ Nigeria slides:
brands, electrical business, leadership, structure, strengths and weaknesses.

| File | What it is |
|---|---|
| [PZ_Nigeria_Analysis_Report.docx](PZ_Nigeria_Analysis_Report.docx) | The written analysis (6 pages). Opens in Word 2013 and later. |
| [PZ_Nigeria_Analysis.xlsx](PZ_Nigeria_Analysis.xlsx) | The analysis workbook. Opens in Excel 2013 and later. |
| [PZ_Nigeria_Analysis.pptx](PZ_Nigeria_Analysis.pptx) | The 15-slide presentation. Opens in PowerPoint 2013 and later. |
| [src/](src/) | The scripts that generated all three files. |

All three files are made in Office 2013's style, as if created in Word, Excel and PowerPoint 2013,
and share two colours from the Office 2013 theme palette: dark blue (Blue, Accent 1, Darker 50%)
and orange (Orange, Accent 2, Darker 25%) for highlights. Every figure in the report and the deck
is read from the workbook, so all three agree.

## The written report

The Word document covers:

1. An introduction to the company.
2. The PESTLE analysis, one section per factor with each issue's score, and a summary table.
3. The SWOT analysis, with the IFE/EFE scoring and the strategy it points to.
4. The industry analysis: an overview, Porter's Five Forces and the main competitors.
5. Recommendations.
6. A conclusion.

It is A4, uses Calibri, and is saved in Word 2013 compatibility mode. It has a "Prepared by" line
to fill in.

## The Excel workbook

The workbook uses the Office 2013 theme, Calibri 11, normal gridlines and Excel 2013's default
chart style. Header rows are dark blue with white text and table lines are light grey. Orange
marks the harmful side of the SWOT, "High" ratings (by conditional formatting, so it follows
the formulas) and the top bar in each chart. The ratings and weights are typed in; every other
figure is a formula, so changing a rating or weight updates the scores, summaries, charts and
conclusions.

| Sheet | Contents |
|---|---|
| Company Profile | Brands, electrical products, leadership and structure |
| PESTLE | 18 issues, each scored Impact × Likelihood (1 to 25) with a priority. A summary per factor uses COUNTIF, AVERAGEIF and COUNTIFS, key findings use INDEX/MATCH, and there is a chart. |
| SWOT | A 2 × 2 matrix of strengths, weaknesses, opportunities and threats, counted with COUNTA |
| SWOT Scoring | IFE and EFE matrices (weight × rating), with the strategy they point to on the IE matrix |
| Industry Analysis | Industry overview, Porter's Five Forces rated 1 to 5, and the main competitors |
| Summary | The key results linked from every sheet, plus five recommendations |

Key results:

| Measure | Result |
|---|---|
| Most important PESTLE factor | Economic (average 20.7 of 25) |
| Highest-scoring issue | Naira devaluation and FX shortages (25 of 25) |
| IFE total | 2.73, above average |
| EFE total | 2.41, below average |
| IE matrix | Cell V: hold and maintain (market penetration and product development) |
| Five Forces average | 3.6 of 5, strong competitive pressure |

The workbook only uses functions that exist in Excel 2013. The ratings and weights are
judgements based on the company information and public news up to 2025.

## The PowerPoint deck

The deck is built on PowerPoint 2013's widescreen Office Theme (Calibri Light titles, Calibri
text) with its standard layouts: Title Slide, Title and Content, Two Content and Title Only.
Tables and charts sit in the content placeholders, as PowerPoint's Insert Table and Insert Chart
icons put them.

It uses two colours from the theme's palette, with black text on white slides:

- **Dark blue** (Blue, Accent 1, Darker 50%): slide titles, table header rows, chart bars,
  labels, box outlines and arrows.
- **Orange** (Orange, Accent 2, Darker 25%): highlights only. That means the most important bar
  in a chart, the weaknesses and threats in the SWOT, "High" priorities, the strongest of the five
  forces, and the line under the title on the first and last slides.

1. Title
2. Company overview
3. PESTLE: Political and Economic (table)
4. PESTLE: Social and Technological (table)
5. PESTLE: Legal and Environmental (table)
6. PESTLE scores (chart and key findings)
7. SWOT analysis (2 × 2 table)
8. SWOT scoring (IFE and EFE chart)
9. Industry overview
10. Main competitors (table)
11. Porter's Five Forces (diagram)
12. Five Forces ratings (chart)
13. Recommendations
14. Conclusion
15. Thank you / questions

Every slide has speaker notes and a Push transition, and its content builds itself
automatically when the slide appears. Click to go to the next slide.

## Rebuilding

Run `src/build.sh`. It needs Python with openpyxl, python-pptx, XlsxWriter and lxml; Node with
the docx package (run `npm install` in `src/` first); and LibreOffice. `src/office2013.py` holds the Office 2013 theme and turns python-pptx's built-in
template into PowerPoint 2013's widescreen Office Theme. The build reuses the chart clean-up,
animation and validation scripts in `../marketing-budget/src`. Set `SCHEMA_DIR` to the ISO/IEC
29500 transitional schemas to check every part of all three files against them.
