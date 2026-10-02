# What-If Analysis: student results

The MS Excel class exercise from Friday, 2nd Oct 2026, worked out for five students. Total,
Average and a Pass/Fail Grade are live formulas, so changing a score updates the result.

**[student-results.xlsx](student-results.xlsx)** opens in Microsoft Excel 2007 or later.

| Name | Eng | Math | Bio | Phy | Chem | Total | Average | Grade |
|---|--:|--:|--:|--:|--:|--:|--:|---|
| Sola Adeyemi | 82 | 93 | 40 | 55 | 83 | 353 | 70.6 | Pass |
| Chinedu Okafor | 68 | 74 | 59 | 71 | 62 | 334 | 66.8 | Pass |
| Aisha Bello | 91 | 85 | 88 | 79 | 90 | 433 | 86.6 | Pass |
| Efe Omoregie | 45 | 38 | 52 | 41 | 47 | 223 | 44.6 | Fail |
| Ngozi Eze | 55 | 47 | 50 | 46 | 52 | 250 | 50.0 | Pass |

Formulas are typed in row 2 and filled down to row 6:

- **G2 Total:** `=SUM(B2:F2)`
- **H2 Average:** `=AVERAGE(B2:F2)`
- **I2 Grade:** `=IF(H2>=50,"Pass","Fail")`

Sola's scores are from the class board. The other four students' scores are sample values.
