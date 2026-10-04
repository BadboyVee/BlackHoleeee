# Assignment: Test Results and a Relative-Interest Pie Chart

| File | What it is |
|---|---|
| [Student_Test_Results.xlsx](Student_Test_Results.xlsx) | The test results of 25 students in 7 subjects, with the grade of each subject. Opens in Excel 2013 and later. |
| [Relative_Interest_Pie_Chart.xlsx](Relative_Interest_Pie_Chart.xlsx) | The relative-interest observations from Task 1 and their pie chart. Opens in Excel 2013 and later. |
| [Relative_Interest_Pie_Chart.pptx](Relative_Interest_Pie_Chart.pptx) | The pie chart in PowerPoint (3 slides). Opens in PowerPoint 2013 and later. |
| [src/](src/) | The scripts that build all three files. |

All three use Office 2013's default look (the Office theme and Calibri) with the same two
colours as the other files: dark blue headers and titles, and orange for highlights.

## Test results

Each student has a score out of 100 in Mathematics, English Language, Physics, Chemistry,
Biology, Economics and Computer Studies. The grade next to each score uses the assignment's
formula, with F5 changed to that score's cell. For the first student's Mathematics score:

    =IF(C5>=80,"A1",IF(C5>=70,"B2",IF(C5>=66,"B3",IF(C5>=60,"C4",IF(C5>=56,"C5",IF(C5>=50,"C6",IF(C5>=46,"D7",IF(C5>=40,"E8","F9"))))))))

| Column | Formula (first student) |
|---|---|
| Grade, for each subject | The IF formula above, on that subject's score |
| Total | `=SUM(C5,E5,G5,I5,K5,M5,O5)` |
| Average | `=AVERAGE(C5,E5,G5,I5,K5,M5,O5)` |
| Overall Grade | The same IF formula, on the average |
| Position | `=RANK(Q5,$Q$5:$Q$29)` |

Under the table are each subject's highest, lowest and average score (MAX, MIN and AVERAGE).
A grade summary counts how many students got each grade in each subject (COUNTIF). F9
grades turn orange through conditional formatting. The score cells only accept whole numbers
from 0 to 100.

| Grade | Score | Remark |
|---|---|---|
| A1 | 80 to 100 | Excellent |
| B2 | 70 to 79 | Very good |
| B3 | 66 to 69 | Good |
| C4, C5, C6 | 60 to 65, 56 to 59, 50 to 55 | Credit |
| D7, E8 | 46 to 49, 40 to 45 | Pass |
| F9 | 0 to 39 | Fail |

The names and scores are sample data. Type the real ones over them and every grade, total,
average, position and count updates.

## Pie chart

The pie chart shows the relative-interest observations from Market Research Lab Task 1
(Google Trends, Nigeria, past 12 months):

| Programme | Average score | Rank | Share of total |
|---|---|---|---|
| Cybersecurity | 43 | 1 | 36% |
| Digital Marketing | 33 | 2 | 28% |
| Data Analytics | 18 | 3 | 15% |
| Generative AI & Prompt Engineering | 13 | 4 | 11% |
| Web Development | 13 | 4 | 11% |

Each slice shows its score and its share of the total. Cybersecurity, the top programme, is
orange, and the rest go from dark to light blue.

The deck has the same chart as a real PowerPoint chart, with its data in an embedded
workbook (right-click the chart, then Edit Data). Its slides are:

1. A title slide.
2. The pie chart.
3. What the chart shows.

It is built on PowerPoint 2013's widescreen Office Theme. Every part of all three files is
checked against the Office Open XML schemas that Office 2013 follows.

To copy the chart from Excel yourself, click the chart's border and press Ctrl+C. Then go to
the slide in PowerPoint and press Ctrl+V.

## Rebuilding

Run `src/build.sh`. It needs Python with openpyxl, python-pptx, XlsxWriter and lxml, and
LibreOffice, which calculates the formulas so previewers show the results. It reuses
`../pz-analysis/src/office2013.py` for the Office 2013 theme and slide template, and the chart
clean-up and validation scripts in `../marketing-budget/src`. Set `SCHEMA_DIR` to the ISO/IEC
29500 transitional schemas to check every part of the three files against them.
