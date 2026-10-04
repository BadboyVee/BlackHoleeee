# Assignment: Test Results and a Relative-Interest Pie Chart

| File | What it is |
|---|---|
| [Student_Test_Results.xlsx](Student_Test_Results.xlsx) | The test results of 25 students in 7 subjects, with the grade of each subject. Opens in Excel 2013 and later. |
| [Relative_Interest_Pie_Chart.xlsx](Relative_Interest_Pie_Chart.xlsx) | The relative-interest observations from Task 1 and their pie chart. Opens in Excel 2013 and later. |
| [Relative_Interest_Pie_Chart.pptx](Relative_Interest_Pie_Chart.pptx) | A 6-slide presentation built around the pie chart. Opens in PowerPoint 2013 and later. |
| [src/](src/) | The scripts that build all three files. |

The workbooks use Office 2013's default look (the Office theme and Calibri), with dark blue
header rows and orange highlights. The deck has its own navy and orange theme, also in Calibri.

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

Each programme has its own colour: orange for Cybersecurity, the top programme, then blue,
green, violet and plum. Each slice shows its share of the total in white. The colours were
checked with a colour-blindness simulation: neighbouring slices, including the last and the
first, stay easy to tell apart, and all five colours carry white text.

## The presentation

The deck uses PowerPoint 2013's widescreen size with a navy and orange theme. Each programme
keeps its colour and its icon on every slide.

| Slide | What it shows |
|---|---|
| 1. Title | The title, with the five programmes' icons in a ring (navy background) |
| 2. How the Data Was Collected | The tool, location, time period and measure, and the five programmes |
| 3. Cybersecurity Leads Search Interest | The pie chart, the headline figure (36%), and a key with each programme's score and share |
| 4. Two Programmes Draw Almost Two-Thirds of Interest | What the chart shows, programme by programme |
| 5. What This Means for Promotion | Three recommendations, beside the two leading shares |
| 6. Thank You | Questions (navy background) |

The pie chart is a real PowerPoint chart with the same colours and labels as the Excel chart.
Its data sits in an embedded workbook (right-click the chart, then Edit Data). The slide
titles, footer and slide numbers come from the slide layouts. Every slide has speaker notes
and a Fade transition.

Every part of all three files is checked against the Office Open XML schemas that Office 2013
follows.

To copy the chart from Excel yourself, click the chart's border and press Ctrl+C. Then go to
the slide in PowerPoint and press Ctrl+V.

## Rebuilding

Run `src/build.sh`. It needs Python with openpyxl, python-pptx and lxml; Node with the
packages in `src/package.json` (run `npm install` in `src/` first); and LibreOffice, which
calculates the formulas so previewers show the results. The deck's figures are read from the
finished workbook, so the two always agree. The build reuses `../pz-analysis/src/office2013.py`
for the workbooks' Office 2013 theme, and the chart clean-up, finishing and validation scripts in
`../marketing-budget/src`. Set `SCHEMA_DIR` to the ISO/IEC 29500 transitional schemas to check
every part of the three files against them.
