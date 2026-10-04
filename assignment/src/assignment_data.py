"""The data behind the assignment files, shared by build_workbooks.py and build_deck.py.

- SUBJECTS, STUDENTS: sample test scores (out of 100) of 25 students in 7 subjects. Replace
  them with the real names and scores; every grade and total is a formula.
- GRADES: the grading scale of the assignment's IF formula, with the WAEC remark for each grade.
- PROGRAMMES: the relative-interest observations from Market Research Lab Task 1: each
  programme's average Google Trends interest (0 to 100; Nigeria, past 12 months), read off the
  "Interest over time" chart, so approximate.
- SLICES: the pie chart's slice colours, picked from the Office 2013 theme palette as
  (theme colour, PowerPoint's Lighter/Darker setting): orange for the top programme, then
  dark to light blue.
"""

SUBJECTS = ["Mathematics", "English Language", "Physics", "Chemistry", "Biology", "Economics",
            "Computer Studies"]

STUDENTS = [
    ("Abubakar Fatima", [53, 54, 50, 33, 40, 45, 27]),
    ("Adebayo Tolulope", [76, 96, 69, 62, 73, 69, 70]),
    ("Adesina Precious", [65, 73, 64, 54, 42, 61, 53]),
    ("Adeyemi Funmilayo", [77, 86, 69, 67, 69, 59, 60]),
    ("Afolabi Ruth", [80, 62, 62, 57, 48, 42, 59]),
    ("Akinola Segun", [69, 52, 53, 64, 64, 45, 39]),
    ("Balogun Sodiq", [74, 69, 64, 48, 60, 71, 51]),
    ("Bello Musa", [45, 59, 30, 41, 31, 44, 38]),
    ("Danjuma Grace", [81, 72, 74, 56, 51, 65, 31]),
    ("Ekong Ime", [68, 57, 65, 52, 33, 59, 47]),
    ("Etim Victoria", [60, 74, 57, 51, 53, 39, 61]),
    ("Eze Ngozi", [60, 46, 41, 42, 61, 56, 39]),
    ("Ibrahim Aisha", [54, 65, 53, 61, 40, 55, 45]),
    ("Lawal Zainab", [66, 61, 59, 60, 58, 41, 53]),
    ("Mohammed Hauwa", [47, 66, 40, 34, 38, 42, 37]),
    ("Nnamdi Ifeoma", [69, 68, 51, 52, 53, 62, 51]),
    ("Nwosu Emeka", [73, 66, 65, 74, 72, 70, 58]),
    ("Obi Chukwudi", [86, 84, 59, 60, 46, 54, 61]),
    ("Ogunleye Damilola", [76, 80, 69, 69, 51, 51, 61]),
    ("Okafor Chinedu", [97, 87, 93, 97, 76, 97, 80]),
    ("Okonkwo Chiamaka", [89, 85, 93, 67, 63, 92, 62]),
    ("Okoro Samuel", [91, 83, 86, 83, 82, 84, 90]),
    ("Olawale Kehinde", [37, 40, 52, 18, 27, 25, 24]),
    ("Uche Blessing", [78, 88, 63, 67, 73, 76, 60]),
    ("Yusuf Abdullahi", [72, 97, 75, 69, 70, 81, 84]),
]

# grade, lowest score, highest score, remark
GRADES = [
    ("A1", 80, 100, "Excellent"),
    ("B2", 70, 79, "Very good"),
    ("B3", 66, 69, "Good"),
    ("C4", 60, 65, "Credit"),
    ("C5", 56, 59, "Credit"),
    ("C6", 50, 55, "Credit"),
    ("D7", 46, 49, "Pass"),
    ("E8", 40, 45, "Pass"),
    ("F9", 0, 39, "Fail"),
]

# The formula exactly as the assignment gives it, for the score in F5.
ASSIGNMENT_FORMULA = ('=IF(F5>=80,"A1",IF(F5>=70,"B2",IF(F5>=66,"B3",IF(F5>=60,"C4",IF(F5>=56,"C5",'
                      'IF(F5>=50,"C6",IF(F5>=46,"D7",IF(F5>=40,"E8","F9"))))))))')


def grade_formula(ref):
    """The assignment's nested IF formula, for the score in cell ref."""
    formula = f'"{GRADES[-1][0]}"'
    for grade, low, _, _ in reversed(GRADES[:-1]):
        formula = f'IF({ref}>={low},"{grade}",{formula})'
    return "=" + formula


assert grade_formula("F5") == ASSIGNMENT_FORMULA

PROGRAMMES = [
    ("Cybersecurity", 43),
    ("Digital Marketing", 33),
    ("Data Analytics", 18),
    ("Generative AI & Prompt Engineering", 13),
    ("Web Development", 13),
]
SOURCE = "Google Trends, Nigeria, past 12 months (28 September 2025 to 28 September 2026)"

SLICES = [("accent2", -0.25),   # Orange, Accent 2, Darker 25%   C55A11
          ("accent1", -0.5),    # Blue, Accent 1, Darker 50%     1F4E79
          ("accent1", -0.25),   # Blue, Accent 1, Darker 25%     2E75B6
          ("accent1", 0),       # Blue, Accent 1                 5B9BD5
          ("accent1", 0.4)]     # Blue, Accent 1, Lighter 40%    9DC3E6


def share(score):
    """A programme's share of the total interest, in whole percent (rounded half up, as Excel
    shows 0%)."""
    total = sum(s for _, s in PROGRAMMES)
    return int(score * 100 / total + 0.5)
