# Marketing Department Budget 2026

An Excel budget for the marketing department's four units, Advertising (Ads), Marketing, Public
Relations (PR) and e-Business, plus a PowerPoint deck that presents each unit and includes the
budget table imported from Excel.

| File | What it is |
|---|---|
| [Marketing_Department_Budget.xlsx](Marketing_Department_Budget.xlsx) | The budget workbook. Opens in Excel 2013 and later. |
| [Marketing_Department_Budget.pptx](Marketing_Department_Budget.pptx) | The 9-slide presentation. Opens in PowerPoint 2013 and later. |
| [src/](src/) | The scripts that generated both files. |

## The Excel workbook

The workbook has one sheet, **Marketing Budget**. Blue figures are the budget inputs and every
black figure is a formula, so changing any blue figure updates the totals, averages, analysis
and charts.

**Budget table (A4:G15).** Each row is a budget item and each column is a unit.

| Cells | Formula | Result |
|---|---|---|
| Total column, F5:F12 | `=SUM(B5:E5)` and so on | each item's total across the units |
| Average per Unit column, G5:G12 | `=AVERAGE(B5:E5)` and so on | each item's average per unit |
| Total Budget row, B13:E13 | `=SUM(B5:B12)` and so on | each unit's total budget |
| Department total, F13 | `=SUM(B13:E13)` | $890,000 |
| Average budget per unit, G13 | `=AVERAGE(B13:E13)` | $222,500 |
| Average per Budget Item row, B14:G14 | `=AVERAGE(B5:B12)` and so on | average spend per budget item |
| Share of Total Budget row, B15:E15 | `=IF($F$13=0,0,B13/$F$13)` and so on | each unit's share of the total |

**Budget Analysis block.** This block shows the department total (SUM), the average per unit
(AVERAGE), the highest and lowest unit (MAX and MIN with INDEX/MATCH), the largest budget item
and the average cost per item.

**Charts.** A column chart of each unit's total and a doughnut chart of each unit's share.

| Unit | Total budget | Share |
|---|---:|---:|
| Advertising | $320,000 | 36.0% |
| Marketing | $260,000 | 29.2% |
| Public Relations | $130,000 | 14.6% |
| e-Business | $180,000 | 20.2% |
| **Total (SUM)** | **$890,000** | **100.0%** |
| **Average per unit (AVERAGE)** | **$222,500** | |

The figures are illustrative sample data prepared for the assignment. The workbook only uses
functions that exist in Excel 2013: SUM, AVERAGE, MAX, MIN, INDEX, MATCH, COUNTA and IF.

## The PowerPoint deck

1. Title slide.
2. Budget at a glance: the total (SUM), the average (AVERAGE) and each unit's share.
3. to 6. One slide per unit, showing its total, share, average per item and a chart of its budget items.
7. **Budget table from Excel.** Cells A4:G15, embedded as a Microsoft Excel Worksheet Object.
   Double-click the table in PowerPoint to open and edit it in Excel.
8. Each unit's budget compared with the average.
9. Key takeaways.

Every slide has speaker notes to present from.

### Importing the table yourself in PowerPoint 2013

1. In Excel, select cells A4:G15 and press Ctrl+C.
2. In PowerPoint, open the slide, then choose Home › Paste (the arrow) › Paste Special.
3. Choose **Microsoft Excel Worksheet Object** and click OK. If the slide should update
   whenever the workbook changes, choose **Paste link** instead.

## Rebuilding

Run `src/build.sh` to regenerate both files. It needs:

- Python with openpyxl, python-pptx, lxml and Pillow
- Node with the packages in `src/package.json` (run `npm install` in `src/` first)
- LibreOffice and poppler
