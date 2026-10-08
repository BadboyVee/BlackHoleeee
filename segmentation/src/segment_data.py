"""The data behind the segmentation assignment, shared by build_workbook.py and build_deck.py.

The new business is SkillUp Academy, a digital-skills training academy. Its customers are
segmented by the skill they want to learn (needs-based segmentation), which gives five segments
that each match one Google Trends search term.

The Google Trends figures are the Market Research Lab Task 1 results (Nigeria, past 12 months,
28 September 2025 to 28 September 2026, all categories, web search), read off the "Interest over
time" averages, the breakdown by state, and each term's rising related queries.

Each segment is scored 1 (poor) to 5 (best) on five attractiveness factors. The search-interest
score is worked out in Excel from the Google Trends average; the other four are judgements, with
their reasons in BASIS. The weighted total (SUMPRODUCT of weights and scores) ranks the segments.
"""

BUSINESS = "SkillUp Academy"
SOURCE = "Google Trends, Nigeria, past 12 months (28 September 2025 to 28 September 2026)"

# name, who they are, what they want, Google Trends search term, average interest (0-100)
SEGMENTS = [
    ("Cybersecurity learners",
     "IT students, and staff of banks, telecoms and government",
     "To protect systems and get security jobs",
     "Cybersecurity", 43),
    ("Digital marketing learners",
     "Small business owners, traders and social media managers",
     "To sell more online with social media and adverts",
     "Digital marketing", 33),
    ("Data analytics learners",
     "Graduates, and staff in finance, NGOs and research",
     "Data skills for better jobs and decisions",
     "Data analytics", 18),
    ("Generative AI learners",
     "Students, content creators and office workers",
     "To use AI tools and prompts to work faster",
     "Generative AI + Prompt engineering", 13),
    ("Web development learners",
     "Young people and freelancers",
     "To build websites and apps for clients",
     "Web development", 13),
]

# factor, weight; the first is scored in Excel from the Google Trends average
FACTORS = [
    ("Search interest", 0.30),
    ("Growth", 0.20),
    ("Spread across Nigeria", 0.15),
    ("Ability to pay", 0.20),
    ("Competition", 0.15),          # 5 means little competition
]

# growth, spread, ability to pay, competition (1-5) for each segment, in SEGMENTS order
SCORES = [
    (5, 5, 4, 3),
    (3, 4, 4, 2),
    (3, 2, 4, 3),
    (3, 3, 3, 4),
    (2, 2, 3, 2),
]

# why each segment got its growth and spread scores (from Google Trends) and its other scores
BASIS = [
    ("Highest almost all year; jumped to 100 in April 2026 after news of a breach at the CAC",
     "Most searched programme in most states, especially in the north and the middle",
     "Professionals and employers pay for training and certificates; some competition"),
    ("Steady; peaked in late January 2026, then slowly dropped",
     "Most searched programme in some southern states",
     "Business owners pay to grow sales; many free courses and agencies compete"),
    ("Steady at a low level, about 15 to 25",
     "Did not lead in any state",
     "Graduates and employers pay for job skills; some competition"),
    ("Low (about 10 to 20), but rising searches for free prompt-engineering courses",
     "Strongest in Benue, Cross River, FCT (Abuja), Rivers and Kwara",
     "Students pay less; few local trainers yet, so little competition"),
    ("Low and flat, about 10 to 20",
     "Did not lead in any state",
     "Young learners pay less; many bootcamps and free tutorials compete"),
]

# Desk research that backs up the Google Trends findings: (finding, segment it supports, source,
# link). Found by web search on 8 October 2026; the figures are as the sources report them.
RESEARCH = [
    ("The CAC confirmed a cyber breach of its systems in April 2026, and the data protection "
     "commission (NDPC) opened an investigation.",
     "Cybersecurity",
     "AllAfrica, 16 April 2026",
     "https://allafrica.com/stories/202604160559.html"),
    ("Nigeria had only about 8,352 cybersecurity professionals in 2023, against 57,269 in South Africa.",
     "Cybersecurity",
     "ISC2 figures, reported by CompTIA",
     "https://www.comptia.org/en/blog/nigeria-and-kenya-cybersecurity-skills-gaps-and-the-workforce-opportunity/"),
    ("Nigerian organisations faced about 4,388 cyber attacks a week in early 2025, 47% more than a year "
     "before.",
     "Cybersecurity",
     "Check Point, reported by BusinessDay",
     "https://businessday.ng/technology/article/nigerian-organisations-recorded-4388-attacks-per-week-in-q1-check-point/"),
    ("About 14 million Nigerian small businesses used Facebook, Instagram and WhatsApp in 2025.",
     "Digital marketing",
     "Public First report for Meta, reported by IT Edge News",
     "https://www.itedgenews.africa/meta-platforms-deliver-820m-annual-economic-value-to-nigeria-ai-could-add-22bn-to-gdp-by-2035-report/"),
    ("The government's 3MTT programme aims to train three million tech talents by 2027, so demand for "
     "tech skills is growing, but free training also competes.",
     "All five",
     "Federal Ministry of Communications, Innovation and Digital Economy",
     "https://3mtt.nitda.gov.ng"),
]
