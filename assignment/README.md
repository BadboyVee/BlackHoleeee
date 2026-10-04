# Assignment: Test Results and a Relative-Interest Pie Chart

| File | What it is |
|---|---|
| [Student_Test_Results.xlsx](Student_Test_Results.xlsx) | The test results of 25 students in 7 subjects, with the grade of each subject. Opens in Excel 2013 and later. |
| [Relative_Interest_Pie_Chart.xlsx](Relative_Interest_Pie_Chart.xlsx) | The relative-interest observations from Task 1 and their pie chart. Opens in Excel 2013 and later. |
| [Relative_Interest_Pie_Chart_Marketing.pptx](Relative_Interest_Pie_Chart_Marketing.pptx) | The 5-slide presentation in the Marketing Budget deck's colours. Opens in PowerPoint 2013 and later. |
| [Relative_Interest_Pie_Chart_PZ.pptx](Relative_Interest_Pie_Chart_PZ.pptx) | The same presentation in the PZ Nigeria deck's wood design. |
| [Relative_Interest_Pie_Chart_Mixed.pptx](Relative_Interest_Pie_Chart_Mixed.pptx) | The same presentation with both palettes mixed. |
| [src/](src/) | The scripts that build all three files. |

The workbooks use Office 2013's default look (the Office theme and Calibri). The test results
workbook has dark blue header rows and orange highlights; the pie chart workbook is black, grey
and white, like the Marketing Budget deck's charts.

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

The slices are in shades of grey, with neighbouring slices far apart in lightness and white
lines between them, as in the Marketing Budget deck. Each slice shows its share of the total,
and the legend names the programmes.

## The presentations

The presentation comes in three colour palettes. The slides are the same in all three, simple,
as if made in PowerPoint 2013, and each slide has a transition:

| Slide | What it shows | Transition |
|---|---|---|
| 1. Relative Interest | The title | Fade |
| 2. Relative-Interest Observations | The table of average scores and ranks | Push |
| 3. Relative Interest by Programme | The pie chart, with a key giving each programme's score and share | Wipe |
| 4. Observations | What the chart shows, in short sentences | Split |
| 5. Thank You | Any questions? | Cover |

| Version | Palette |
|---|---|
| Marketing | The Marketing Budget deck's: dark-blue titles over a dark-blue line, a thin light-blue frame, light-blue boxes, and the pie chart in black and greys |
| PZ | The PZ Nigeria deck's wood design: a wood background with white cards and a thin orange border, two dark straps on the first and last slides, orange-brown lines and table headers, and the pie chart in browns and oranges |
| Mixed | Both together: the wood title and closing slides, and white content slides with dark-blue titles, orange lines, peach and light-blue boxes, and a navy, orange and grey pie chart |

The text is in Calibri, with titles in Calibri Bold (Marketing) or Cambria Bold (PZ and Mixed).
Both fonts come with Office, so the slides look the same on any computer with PowerPoint. The
build checks that every text box fits its text (`src/check_fit.py`), measuring the words with
fonts exactly as wide as Calibri and Cambria.

Each deck's theme carries its palette and fonts, so PowerPoint's colour lists (Shape Fill, Font
Color) offer the same colours. The wood background is a picture drawn by `src/make_wood.py`.

The pie chart is a real PowerPoint chart. Its data sits in an embedded workbook (right-click
the chart, then Edit Data). Every slide has short speaker notes.

Every part of every file is checked against the Office Open XML schemas that Office 2013
follows.

To copy the chart from Excel yourself, click the chart's border and press Ctrl+C. Then go to
the slide in PowerPoint and press Ctrl+V.

## Rebuilding

Run `src/build.sh`. It needs Python with openpyxl, python-pptx, XlsxWriter and lxml, and
LibreOffice, which calculates the formulas so previewers show the results. The deck's figures
are read from the finished workbook, so they always agree. It needs numpy and Pillow for the
wood picture. The build reuses
`../pz-analysis/src/office2013.py` for the Office 2013 theme and slide template, and the chart
clean-up, transition and validation scripts in `../marketing-budget/src`. Set `SCHEMA_DIR` to the ISO/IEC 29500 transitional schemas to check
every part of the three files against them.
