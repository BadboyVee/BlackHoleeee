# PZ Nigeria Limited: PESTLE, SWOT and Industry Analysis

An Excel workbook and a PowerPoint deck that analyse PZ Nigeria Limited (Marketing Department,
Ilupeju, Lagos). The company facts come from the PZ Nigeria slides: brands, electrical
business, leadership, structure, strengths and weaknesses.

| File | What it is |
|---|---|
| [PZ_Nigeria_Analysis.xlsx](PZ_Nigeria_Analysis.xlsx) | The analysis workbook. Opens in Excel 2013 and later. |
| [PZ_Nigeria_Analysis.pptx](PZ_Nigeria_Analysis.pptx) | The 13-slide presentation. Opens in PowerPoint 2013 and later. |
| [src/](src/) | The scripts that generated both files. |

## The Excel workbook

Blue figures are inputs (ratings and weights). Every black figure is a formula, so changing a
blue figure updates the scores, summaries, charts and conclusions.

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

1. Title
2. Company overview
3. PESTLE analysis, part 1 (Political, Economic, Social)
4. PESTLE analysis, part 2 (Technological, Legal, Environmental)
5. PESTLE scores (chart and key findings)
6. SWOT analysis
7. SWOT scoring (IFE and EFE)
8. Industry overview
9. Main competitors
10. Porter's Five Forces
11. Five Forces ratings
12. Recommendations
13. Conclusion

The deck uses the same plain look as the budget deck: Arial only, black text with dark-blue
titles, grey charts, and only rectangles, lines and text boxes. Every slide has speaker notes
and a Push transition, and its content builds itself automatically when the slide appears.

## Rebuilding

Run `src/build.sh`. It reuses the chart and slide clean-up scripts in
`../marketing-budget/src` and needs the same tools (Python with openpyxl, python-pptx and lxml;
Node with pptxgenjs; LibreOffice). Set `SCHEMA_DIR` to the ISO/IEC 29500 transitional schemas to
check every part of both files against them.
