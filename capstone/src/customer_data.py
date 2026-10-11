"""Capstone part 2: customer analysis for CyberStart, SkillUp Academy's beginner cybersecurity
course. Shared by build_customer_workbook.py and build_customer_deck.py.

Customer needs (functional, economic, emotional, social), the five most important needs, four
market segments (demographic, psychographic, behavioural and geographic bases) scored on market
size, accessibility, buying potential and competition, the target segment, a customer persona
and a customer journey map.

The evidence is real, published data: world data (ISC2, the World Economic Forum), Nigerian data
(NUC, the minimum wage, UN population figures) and the part 1 research in capstone_data.py. It
was found by web search on 11 October 2026 and is given as the sources report it. The scores
(1 to 5) are my judgements from that evidence; the workbook keeps them in yellow input cells so
they can be changed. The persona is fictional, built from the research.
"""
from capstone_data import BUSINESS, PRICE, INSTALMENTS, PRODUCT, PRODUCT_LINE, SOURCES as PART1_SOURCES

RESEARCH_DATE = "11 October 2026"

SOURCES = {
    "wef": ("World Economic Forum, Future of Jobs Report 2025 (as summarised by Mwanaspoti)",
            "Networks and cybersecurity is the second fastest-growing skill, after AI and big data",
            "https://www.mwanaspoti.co.tz/bd/corporate/technology/future-of-labour-tech-skills-driving-jobs-growth-in-"
            "2025-4886646"),
    "isc2_2025": ("ISC2", "2025 Cybersecurity Workforce Study (16,029 professionals, December 2025)",
                  "https://www.isc2.org/Insights/2025/12/2025-ISC2-Cybersecurity-Workforce-Study"),
    "isc2_women": ("ISC2", "Women comprise 22 percent of the cybersecurity workforce (March 2025)",
                   "https://www.isc2.org/insights/2025/03/women-comprise-22-percent-of-the-cybersecurity-workforce"),
    "nuc": ("TheCable, reporting the NUC", "NUC: only one percent of Nigerian population in universities",
            "https://www.thecable.ng/?p=271369"),
    "wage": ("Playroll", "Minimum wage in Nigeria in 2026 (National Minimum Wage (Amendment) Act 2024)",
             "https://playroll.com/minimum-wage/nigeria"),
    "age": ("GeoRank, using UN and World Bank data", "Demographics of Nigeria",
            "https://georank.org/demographics/nigeria/norway"),
    "trends": PART1_SOURCES["trends"],
    "datareportal": PART1_SOURCES["datareportal"],
    "napoleoncat": PART1_SOURCES["napoleoncat"],
    "salary": PART1_SOURCES["salary"],
    "mordor": PART1_SOURCES["mordor"],
    "cybergirls": PART1_SOURCES["cybergirls"],
    "altschool": PART1_SOURCES["altschool"],
    "altschool_nano": PART1_SOURCES["altschool_nano"],
    "alx": PART1_SOURCES["alx"],
    "tryhackme": PART1_SOURCES["tryhackme"],
    "complaints": PART1_SOURCES["complaints"],
    "vlearn": PART1_SOURCES["vlearn"],
    "isc2": PART1_SOURCES["isc2"],
    "careers": PART1_SOURCES["careers"],
}

# ------------------------------------------------------------------ world and Nigerian data
# (fact, figure, number for Excel or None, where, source key)
WORLD = [
    ("Fastest-growing skills in the world, 2025 to 2030", "Networks and cybersecurity: 2nd (after AI and big "
     "data)", None, "World", "wef"),
    ("Cybersecurity teams with at least one skills gap", "95%", 0.95, "World", "isc2_2025"),
    ("Skills most in demand in cybersecurity", "AI and cloud security", None, "World", "isc2_2025"),
    ("Women in cybersecurity teams", "22% (26% of professionals under 30)", 0.22, "World", "isc2_women"),
    ("Median age", "About 19 years", 19.2, "Nigeria", "age"),
    ("University students", "2.1 million", 2_100_000, "Nigeria", "nuc"),
    ("National minimum wage", "₦70,000 a month", 70_000, "Nigeria", "wage"),
    ("Junior security analyst pay", "About ₦150,000 to ₦300,000 a month", 150_000, "Nigeria", "salary"),
    ("People using the internet", "109 million (end of 2025)", 109_000_000, "Nigeria", "datareportal"),
]
JUNIOR_PAY_LOW = 150_000
MIN_WAGE = 70_000

# ------------------------------------------------------------------ customer needs
# (type, need, short name for the chart, what it means, evidence, how often it came up in the
#  research 1-5, effect on the decision to buy 1-5). Importance = frequency x impact (of 25).
NEEDS = [
    ("Functional", "Practical, hands-on skills", "Hands-on skills",
     "Labs and real tools, not just theory", "“No labs” and “too much theory” drive low course ratings; "
     "TryHackMe is praised for its labs", 5, 5),
    ("Functional", "A flexible timetable", "Flexible timetable",
     "Evening, weekend and recorded classes", "ALX is praised for self-paced study; AltSchool's 20 hours a week "
     "was too much for workers", 4, 4),
    ("Functional", "Preparation for a recognised certificate", "Certificate preparation",
     "Ready for Security+ or ISC2 CC", "Guides say get Security+ first; ISC2's free exam offer ended in May 2026",
     4, 5),
    ("Economic", "An affordable price", "Affordable price",
     "A fair price for the value", "Rising “free course” searches; 20,000+ apply for about 500 free CyberGirls "
     "places", 5, 5),
    ("Economic", "Paying in instalments", "Pay in parts",
     "Spread the cost over the course", "The minimum wage is ₦70,000 a month; a rival lets people pay in parts",
     3, 4),
    ("Economic", "A return on the money: a better-paid job", "Better-paid job",
     "The course pays for itself", "Junior analysts earn about ₦150,000 to ₦300,000 a month; people search for "
     "salaries", 4, 5),
    ("Emotional", "Trust that the course is genuine", "Trust, not a scam",
     "Confidence it is not a scam", "AltSchool was called a “scam” on X; local providers have few reviews", 4, 4),
    ("Emotional", "Feeling supported", "Feeling supported",
     "Quick help when stuck", "Slow support is a complaint about ALX, TryHackMe and AltSchool; 48% of cyber "
     "professionals feel exhausted keeping up", 5, 4),
    ("Emotional", "Hope for a future-proof career", "Future-proof career",
     "Pride in a growing field", "Cybersecurity is the 2nd fastest-growing skill in the world", 3, 3),
    ("Social", "Belonging to a learning community", "Community",
     "Learning with others", "ALX learners praise its community", 3, 3),
    ("Social", "Status of a respected tech job", "Status",
     "Being seen as a tech professional", "14 million Nigerians are on LinkedIn", 2, 3),
    ("Social", "Inclusion for women and non-IT people", "Inclusion",
     "Welcome whatever your background", "Women are 22% of cyber teams, 26% of those under 30", 3, 3),
]
NEED_TYPES = ["Functional", "Economic", "Emotional", "Social"]

# ------------------------------------------------------------------ market segments
BASES = [
    ("Demographic", "Age, education, job and income"),
    ("Geographic", "Where they live and how they can attend"),
    ("Psychographic", "Values, goals, attitudes and lifestyle"),
    ("Behavioural", "How they search, decide, buy and learn"),
]
# name, then one line for each base (demographic, geographic, psychographic, behavioural), and
# the evidence for its size
SEGMENTS = [
    ("Campus Starters",
     "Students and new graduates, 18 to 24; little or no income",
     "University towns across Nigeria; online",
     "Ambitious and curious; want a head start before graduating",
     "Search for “free course”; learn on YouTube and TikTok; very price-driven",
     "2.1 million university students (NUC)"),
    ("Career Switchers",
     "Working adults, 25 to 35, in non-IT jobs; steady but modest pay",
     "Lagos, Abuja and Port Harcourt; online in the evenings and at weekends",
     "Want a better-paid, future-proof career; careful with money",
     "Compare courses and read reviews; search for salaries; pay in instalments",
     "109 million internet users; median age about 19"),
    ("Corporate Upskillers",
     "Staff of banks, telecoms and government, 25 to 45; the employer pays",
     "Head offices in Lagos and Abuja",
     "Career growth and doing things by the book",
     "Buy through HR in groups; want recognised certificates",
     "Banks, finance and insurance are 29.2% of the cyber market"),
    ("Women in Tech Starters",
     "Women 18 to 30, students and graduates",
     "Nationwide, online, with hubs in Lagos and Abuja",
     "Want a safe, supportive community and role models",
     "Apply for free fellowships; follow women's tech groups",
     "20,000+ applications a year to CyberGirls"),
]
# (criterion, weight)
CRITERIA = [("Market size", 0.25), ("Accessibility", 0.25), ("Buying potential", 0.30), ("Competition", 0.20)]
# Scores 1 (poor) to 5 (best), in CRITERIA order; for competition, 5 means little competition.
SCORES = [
    (5, 4, 2, 2),
    (4, 4, 4, 4),
    (2, 3, 5, 2),
    (3, 4, 2, 3),
]
# why: (market size, accessibility, buying potential, competition)
SCORE_BASIS = [
    ("2.1 million university students", "Easy to reach online and on campus", "Little income; want free courses",
     "Many free courses aim at them"),
    ("Large: young working adults in big cities", "Reach on Facebook, LinkedIn and Google", "Earn above the "
     "minimum wage; can pay in parts", "Few practical, mid-price evening courses"),
    ("Smaller: staff of a few big employers", "Slow sales through HR", "Employers pay; banks are 29% of the market",
     "Classroom firms already serve them"),
    ("About 1 in 4 cyber professionals under 30", "Active online communities", "Often students; want free places",
     "Free fellowships, but places are few"),
]

# ------------------------------------------------------------------ persona (fictional)
PERSONA = {
    "name": "Tunde Bakare",
    "initials": "TB",
    "segment": "Career Switchers",
    "facts": [("Age", "27"), ("Lives in", "Ikeja, Lagos"), ("Job", "Customer service officer at a phone retailer"),
              ("Education", "HND in Business Administration"),
              ("Money", "Steady pay above the minimum wage; can spare about ₦50,000 a month"),
              ("Devices", "Smartphone and a budget laptop")],
    "quote": "“I don't mind paying, if I'm sure it will get me a job.”",
    "goals": ["Move into a cybersecurity job within a year", "Earn more: junior analysts earn ₦150,000+ a month",
              "Learn a skill that will not go out of date"],
    "frustrations": ["Does not know where to start", "Afraid of paying for a scam course",
                     "Works 8 to 5; free programmes are full"],
    "needs": ["Hands-on labs at weekends", "A fair price in 3 parts", "Help when stuck and a route to a job"],
    "channels": ["Google, YouTube and TikTok", "Facebook groups and WhatsApp", "LinkedIn for jobs"],
    # what makes Tunde buy
    "triggers": ["News of a big data breach, like the CAC breach", "A friend who moved into a tech job",
                 "A free first class or a deadline to enrol"],
    "objections": ["“Is it a scam?”  Real reviews and a free first class", "“Can I fit it round work?”  Evenings, "
                   "weekends and recordings", "“Will I get a job?”  Exam prep, CV help, employers"],
    "criteria": ["Hands-on labs and real tools", "The full price and a payment plan", "Reviews from past learners",
                 "A recognised certificate"],
    "payment": [f"₦{PRICE:,} in {INSTALMENTS} parts of ₦{PRICE // INSTALMENTS:,}",
                "Pays from salary, a part each month", "Decides alone; asks friends on WhatsApp first"],
}

# Persona personality, 1 (low) to 5 (high): judgements that describe the fictional persona
TRAITS = [("Careful with money", 5), ("Ambitious", 5), ("Confident with tech", 2), ("Free time", 2),
          ("Trust in online courses", 2)]

# Key figures for the context slide: (big figure, what it means, where, source key)
KPIS = [
    ("2nd", "fastest-growing skill in the world: networks and cybersecurity", "World", "wef"),
    ("95%", "of cybersecurity teams have at least one skills gap", "World", "isc2_2025"),
    ("AI & cloud", "the cybersecurity skills most in demand", "World", "isc2_2025"),
    ("22%", "of cyber team members are women (26% under 30)", "World", "isc2_women"),
    ("19", "years: the median age in Nigeria", "Nigeria", "age"),
    ("2.1m", "university students in Nigeria", "Nigeria", "nuc"),
    ("₦70k", "national minimum wage a month", "Nigeria", "wage"),
    ("₦150k+", "a month for a junior security analyst", "Nigeria", "salary"),
]

# The tasks, in the order the assignment sets them: (number, task, what it covers)
TASKS = [
    ("1", "Customer persona", "Who the typical buyer is, and what makes them buy"),
    ("2", "Customer journey map", "From first hearing about the course to a new job"),
    ("3", "The 5 most important needs", "Chosen from 12 functional, economic, emotional and social needs"),
    ("4", "Four market segments", "Demographic, geographic, psychographic and behavioural"),
    ("5", "Segment scores", "Market size, accessibility, buying potential and competition"),
    ("6", "Target segment", "The segment the business should prioritise"),
]

# ------------------------------------------------------------------ customer journey map
STAGES = ["Awareness", "Consideration", "Purchase", "Learning", "After the course"]
# row label: one entry for each stage
JOURNEY = [
    ("Doing", ["Sees breach news and a TikTok video on cyber careers", "Compares courses, reads reviews, asks in "
               "WhatsApp groups", "Joins the free first class, pays the first part", "Attends classes and weekend "
               "labs, takes the exam", "Applies for jobs, shares the result, refers friends"]),
    ("Touchpoints", ["TikTok, Facebook adverts, Google search", "Website, Google and Trustpilot reviews, WhatsApp",
                     "Free class, online payment plan", "Learning platform, Lagos lab, mentor",
                     "Career help, LinkedIn, alumni group"]),
    ("Thinking and feeling", ["“Can I do this without IT?” Curious but unsure", "“Is this a scam?” Anxious",
                              "“I hope it's worth it.” Hopeful, nervous", "“Hard, but I'm getting it.” Proud",
                              "“I got the job!” Relieved and proud"]),
    ("Pain points", ["No clear starting point", "Hidden prices, few reviews", "Big one-off fees",
                     "Slow support, outdated content", "No links to employers"]),
    ("Opportunities", ["Beginner videos on TikTok and Google", "Publish prices and reviews; fast WhatsApp replies",
                       f"Free first class; {INSTALMENTS} instalments", "Weekly labs, 24-hour support, recordings",
                       "Exam prep, CV help, employer partners, referral reward"]),
]
FEELING = [3, 2, 3, 4, 5]                 # 1 (very negative) to 5 (very positive), one per stage

CONCLUSION = [
    ("Top needs: ", "hands-on skills, an affordable price, certificate preparation, a better-paid job and "
                    "feeling supported."),
    ("Target segment: ", "Career Switchers, working adults of 25 to 35 who can pay in parts and want a better "
                         "job."),
    ("Persona: ", "Tunde, 27, in Lagos: wants a cyber job within a year, fears scams, learns at weekends."),
    ("Journey: ", "the low point is choosing a course; clear prices, reviews and a free first class fix it."),
]
