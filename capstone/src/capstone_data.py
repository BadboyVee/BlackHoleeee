"""The research behind the capstone project, shared by build_workbook.py and build_deck.py.

The business is SkillUp Academy, the digital-skills training business from the segmentation
assignment, and the product is CyberStart, a beginner cybersecurity course: the segment that
assignment found most attractive.

The Google Trends figures are the Market Research Lab Task 1 results (screenshots taken on 28
September 2026; Nigeria, past 12 months, all categories, web search). Everything else was found
by web search on 8 and 9 October 2026, and every figure is given as its source reports it. Where
sources disagree, the note says so. Figures marked as assumptions are mine, and the workbook
keeps them in yellow input cells so they can be changed.
"""

BUSINESS = "SkillUp Academy"
PRODUCT = "CyberStart"
PRODUCT_LINE = "a 12-week beginner cybersecurity course in Nigeria"
PRICE = 150_000                       # naira; assumption, set from the price research below
INSTALMENTS = 3
RESEARCH_DATE = "8 and 9 October 2026"
TRENDS_PERIOD = "Nigeria, past 12 months (28 September 2025 to 28 September 2026)"

# ------------------------------------------------------------------ sources
# key: (who, what, link)
SOURCES = {
    "trends": ("Google Trends", "Market Research Lab Task 1 screenshots, 28 September 2026: Nigeria, past 12 months, "
               "all categories, web search", "https://trends.google.com/trends/"),
    "mordor": ("Mordor Intelligence", "Nigeria Cybersecurity Market: size and share",
               "https://www.mordorintelligence.com/industry-reports/nigeria-cybersecurity-market"),
    "datareportal": ("DataReportal", "Digital 2026: Nigeria", "https://datareportal.com/reports/digital-2026-nigeria"),
    "napoleoncat": ("NapoleonCat", "Social media users in Nigeria, 2026 (Facebook, Instagram, LinkedIn)",
                    "https://stats.napoleoncat.com/social-media-users-in-nigeria/2026/"),
    "comptia": ("CompTIA, using ISC2 figures", "Nigeria and Kenya: cybersecurity skills gaps and the workforce "
                "opportunity", "https://www.comptia.org/en/blog/nigeria-and-kenya-cybersecurity-skills-gaps-and-the-"
                "workforce-opportunity/"),
    "checkpoint": ("BusinessDay, reporting Check Point", "Nigerian organisations recorded 4,388 attacks per week in Q1",
                   "https://businessday.ng/technology/article/nigerian-organisations-recorded-4388-attacks-per-week-in-"
                   "q1-check-point/"),
    "cac": ("AllAfrica", "The CAC confirms a cyber breach (16 April 2026)",
            "https://allafrica.com/stories/202604160559.html"),
    "skills2026": ("BusinessDay", "Top six tech skills Nigerians need to stay relevant in 2026",
                   "https://businessday.ng/technology/article/top-six-tech-skills-nigerians-need-to-stay-relevant-in-"
                   "2026/"),
    "jobs": ("Profolio.ng", "Cybersecurity analyst: companies hiring in Nigeria, 2026",
             "https://www.profolio.ng/cybersecurity-analyst/companies-hiring"),
    "3mtt": ("Federal Ministry of Communications, Innovation and Digital Economy", "3 Million Technical Talent (3MTT)",
             "https://3mtt.nitda.gov.ng"),
    "3mtt_skills": ("TechCabal", "3 Million Technical Talent portal: features and FAQs (the twelve skills)",
                    "https://techcabal.com/2023/10/19/3-million-technical-talent-portal-features-faqs-and-more/"),
    "phillips": ("Phillips Consulting", "Certified ISO 27032 Cyber Security Lead Manager (Lagos)",
                 "https://phillipsconsulting.net/courses/certified-iso-27032-cyber-security-lead-manager"),
    "bootcamp": ("TechCabal Radar", "Cybersecurity engineering bootcamp in Nigeria",
                 "https://radar.techcabal.com/t/cybersecurity-engineering-bootcamp-in-nigeria/15318"),
    "legit": ("Legit.ng", "Best cybersecurity courses in Nigeria: top universities, fees, and how to apply",
              "https://www.legit.ng/education/1730778-best-cybersecurity-courses-nigeria-top-universities-fees-how-"
              "apply/"),
    "guide": ("TechNeeds", "How to get started in cyber security: a beginner's guide (March 2026)",
              "https://www.techneeds.com/2026/03/19/how-to-get-started-in-cyber-security-a-beginners-guide/"),
    "coursera_ng": ("BusinessDay", "Coursera's Nigeria prices", "https://businessday.ng/?p=1019597"),
    "isc2": ("ISC2", "One Million Certified in Cybersecurity: conclusion (April 2026)",
             "https://www.isc2.org/Insights/2026/04/one-million-certified-cyber-conclusion"),
    "cybergirls": ("Security Blue Team", "CyberGirls Fellowship success stories",
                   "https://www.securityblue.team/blog/posts/cybergirls-success-empowering-women-in-cybersecurity"),
    "alx": ("Trustpilot", "ALX Africa reviews", "https://fr.trustpilot.com/review/www.alxafrica.com"),
    "alx_review": ("Mctaba", "ALX Africa review", "https://www.mctaba.com/learn/africa/alx-africa-review"),
    "altschool": ("TechCabal", "AltSchool Africa set out to fix education. Now it's learning its own lessons "
                  "(29 October 2025)", "https://techcabal.com/2025/10/29/altschool-africa-cracks-on-the-wall/"),
    "altschool_nano": ("Techpoint Africa", "AltSchool Africa Nano-Diploma",
                       "https://techpoint.africa/news/altschool-africa-nano-diploma/"),
    "tryhackme": ("Trustpilot", "TryHackMe reviews", "https://www.trustpilot.com/review/tryhackme.com"),
    "niit": ("NIIT Nigeria", "About NIIT Nigeria", "https://www.niit.com/nigeria/Pages/about.aspx"),
    "dion": ("Udemy (figures as listed by CTgoodjobs)", "CompTIA Security+ (SY0-701) Complete Course & Practice Exam",
             "https://www2.ctgoodjobs.hk/Learning/1325138996/udemy/comptia-security--sy0-701-complete-course-practice-"
             "exam"),
    "dion_exams": ("Udemy (figures as listed by CTgoodjobs)", "CompTIA Security+ (SY0-701) Practice Exams Set 1",
                   "https://www2.ctgoodjobs.hk/Learning/1356753712/udemy/comptia-security--sy0-701-practice-exams-set-1"),
    "house": ("Udemy", "The Complete Cyber Security Course: Hackers Exposed",
              "https://www.udemy.com/course/the-complete-internet-security-privacy-course-volume-1/"),
    "google_cert": ("Coursera", "Google Cybersecurity Professional Certificate",
                    "https://www.coursera.org/google-certificates/google-cybersecurity"),
    "google_course": ("Coursera", "Foundations of Cybersecurity (Google): reviews",
                      "https://www.coursera.org/learn/foundations-of-cybersecurity/reviews"),
    "vlearn": ("vLearnSecurity", "Pricing: 12-week foundational course", "https://vlearnsecurity.durable.site/pricing"),
    "salary": ("Mobility.com.ng", "Cybersecurity career path: jobs and pay in Nigeria", "https://mobility.com.ng/?p=397570"),
    "careers": ("Profolio.ng", "How to get a cybersecurity analyst job in Nigeria",
                "https://www.profolio.ng/cybersecurity-analyst/how-to-get-a-job"),
    "nitda_ctf": ("Nigeria Startup Act portal", "Apply for the NITDA Capture The Flag (CTF) Competition 2026",
                  "https://www.nigeriastartupact.ng/apply-for-nitda-capture-the-flag-ctf-competition-2026/"),
    "complaints": ("Course.careers", "Overview of course reviews: what drives low ratings",
                   "https://course.careers/course-reviews/overview-reviews-of-courses"),
    "instagram": ("IQHashtags", "#cybersecurity: Instagram hashtag analysis",
                  "https://iqhashtags.com/hashtags/hashtag/cybersecurity"),
    "tiktok": ("Cyber Magazine", "Cybersecurity features in top 10 tech videos on TikTok",
               "https://cybermagazine.com/technology-and-ai/cybersecurity-features-top-10-tech-videos-tiktok"),
    "mentions": ("Datashake", "Cybersecurity social media dataset (2022 to 2026)",
                 "https://www.datashake.com/datasets/cybersecurity-social-media-dataset"),
}

# ------------------------------------------------------------------ 1. the business and the market
PRODUCT_POINTS = [
    ("Business", f"{BUSINESS}, a new digital-skills training business in Nigeria."),
    ("Product", f"{PRODUCT}, {PRODUCT_LINE}, for people with no IT background."),
    ("How it runs", "Live online classes, plus weekend practical labs in Lagos and Abuja."),
    ("Outcome", "Ready for a first certificate (ISC2 CC or CompTIA Security+) and a first job."),
    ("Proposed price", f"₦{PRICE:,}, paid in {INSTALMENTS} parts of ₦{PRICE // INSTALMENTS:,}."),
]

# (part of the definition, what it is)
MARKET_DEFINITION = [
    ("Market", "Beginner cybersecurity training (education services)"),
    ("Customers", "Students, graduates and career changers aged about 18 to 35; employers who sponsor staff"),
    ("Location", "Nigeria: online nationwide, with labs in Lagos and Abuja, where most jobs are"),
    ("Customer need", "A low-cost, practical route into a well-paid cybersecurity job"),
    ("Competition", "Online tech schools, free programmes, course marketplaces and classroom providers"),
]

# (indicator, value, unit, when, source key)
MARKET_FACTS = [
    ("Nigeria cybersecurity market", 230.03, "US$ million", "2025", "mordor"),
    ("Nigeria cybersecurity market", 253.77, "US$ million", "2026", "mordor"),
    ("Nigeria cybersecurity market (forecast)", 414.92, "US$ million", "2031", "mordor"),
    ("People using the internet", 109, "million", "End of 2025", "datareportal"),
    ("Internet penetration", 0.455, "of the population", "End of 2025", "datareportal"),
    ("Social media user identities", 47.8, "million", "October 2025", "datareportal"),
    ("Cybersecurity professionals in Nigeria", 8352, "people", "2023", "comptia"),
    ("Cybersecurity professionals in South Africa", 57269, "people", "2023", "comptia"),
    ("Banks, finance and insurance share of the market", 0.292, "of the market", "2025", "mordor"),
    ("Cyber attacks on each Nigerian organisation", 4388, "a week", "Q1 2025", "checkpoint"),
    ("Rise in attacks on a year before", 0.47, "growth", "Q1 2025", "checkpoint"),
    ("Tech talents the government aims to train", 3_000_000, "people", "By 2027", "3mtt"),
]
MARKET_SIZE = [("2025", 230.03), ("2026", 253.77), ("2031 (forecast)", 414.92)]      # US$ million, Mordor

# Market size estimate: (label, value, kind, note). kind: "input" (an assumption in a yellow cell)
# or "formula" (worked out in Excel from the rows above).
SIZING = [
    ("Tech talents Nigeria aims to train by 2027 (3MTT)", 3_000_000, "input", "Government target (3MTT)"),
    ("Technical skills in 3MTT, one of them cybersecurity", 12, "input", "TechCabal: the twelve 3MTT skills"),
    ("Potential cybersecurity learners", None, "formula", "Target ÷ number of skills"),
    ("Share we can reach who can pay", 0.30, "input", "Assumption: online plus Lagos and Abuja"),
    ("Serviceable market (learners)", None, "formula", "Potential learners × share"),
    ("Share we can win in year 1", 0.005, "input", "Assumption: a new, small academy"),
    ("Learners in year 1", None, "formula", "Serviceable market × share"),
    ("Price per learner (₦)", PRICE, "input", "Assumption, from the price research"),
    ("Revenue in year 1 (₦)", None, "formula", "Learners × price"),
]

# ------------------------------------------------------------------ 2. research methods
# (method, where, what I looked for)
METHODS = [
    ("Google Search", "Search results for five searches a customer would make", "Prices, free options, the "
     "steps beginners are told to take, jobs"),
    ("Google Trends", "Five digital skills compared, Nigeria, past 12 months", "How much interest, when it "
     "peaked, where, and the rising searches"),
    ("Social media trends", "Facebook, Instagram, LinkedIn, TikTok and X", "Where the audience is, and how "
     "people talk about cybersecurity"),
    ("Competitor reviews", "Trustpilot and news about ALX Africa, AltSchool Africa, TryHackMe and others", "What "
     "learners like and complain about"),
    ("Marketplace reviews", "Udemy and Coursera cybersecurity courses", "Ratings, number of learners, praise and "
     "complaints"),
]

# ------------------------------------------------------------------ 3. Google Search
# (search, what came up, what it tells us). The searches were run with a web search engine on
# 9 October 2026; run them again on google.com.ng to take screenshots for the report.
SEARCHES = [
    ("cybersecurity course fees in Nigeria", "Course lists, a bootcamp in US dollars, university pages; one local "
     "12-week course asks ₦100,000 first, then instalments", "Naira prices are hard to find; rivals let people "
     "pay in parts"),
    ("free cybersecurity training for Nigerians", "NITDA and Cisco free courses, women's programmes, a 2026 "
     "capture-the-flag contest; most have closed", "Free programmes are popular but short and soon full"),
    ("how to start a career in cybersecurity in Nigeria", "Beginner guides, a paid e-book, a campus event, job "
     "guides: Security+ first, labs on TryHackMe", "Beginners want a clear, step-by-step path"),
    ("cybersecurity jobs in Nigeria salary", "Pay guides: junior analysts about ₦150,000 to ₦300,000 a month; "
     "jobs mostly in Lagos and Abuja", "People search with a job in mind"),
    ("Nigeria cybersecurity market size", "Market reports: about US$230 million in 2025, growing about 10% a "
     "year", "The market is growing"),
]
# (provider, offer, price, length, source key)
PRICES = [
    ("vLearnSecurity", "12-week foundational course, online", "₦100,000 first payment, then instalments",
     "12 weeks", "vlearn"),
    ("Phillips Consulting", "ISO 27032 Lead Manager, classroom (Lagos)", "₦250,000 + US$500 exam", "5 days",
     "phillips"),
    ("Cybersecurity bootcamp", "Specialist tracks, online", "US$1,000 to US$2,850", "Per track", "bootcamp"),
    ("Coursera (Google certificate)", "Coursera Plus, Nigeria price", "US$24 a month", "Self-paced",
     "coursera_ng"),
    ("Cisco, NITDA, CyberGirls", "Free courses, contests and fellowships", "Free", "Varies", "legit"),
]
SEARCH_POINTS = [
    ("Prices are hard to find: ", "few results show a naira price."),
    ("Prices vary widely: ", "₦100,000 to start a 12-week course; ₦250,000 for 5 days in a Lagos classroom; "
                             "US$1,000 or more for a bootcamp track."),
    ("Free options: ", "NITDA, Cisco and CyberGirls run free training, but places are few and close fast."),
    ("Beginner guides agree: ", "get Security+ first, practise in labs, build a portfolio."),
    ("Jobs: ", "junior analysts earn about ₦150,000 to ₦300,000 a month, mostly in Lagos and Abuja."),
]

# ------------------------------------------------------------------ 4. Google Trends (Task 1)
# (programme, average interest 0-100)
TRENDS = [
    ("Cybersecurity", 43),
    ("Digital Marketing", 33),
    ("Data Analytics", 18),
    ("GenAI & Prompt Engineering", 13),
    ("Web Development", 13),
]
TRENDS_POINTS = [
    ("Highest interest: ", "Cybersecurity led almost all year."),
    ("Peak: ", "it hit 100 in April 2026, when the CAC confirmed a cyber breach."),
    ("Where: ", "the most searched skill in most states, especially in the north and the middle."),
    ("Rising searches: ", "“cac cybersecurity breach”, “cybersecurity news today”, “lagos cybersecurity "
                          "guidelines”."),
]
TRENDS_QUERIES = ("cac cybersecurity breach, cybersecurity news today, wikipedia, ai news today, "
                  "lagos cybersecurity guidelines")
TRENDS_OTHER = "Free courses: other skills' rising searches include “google prompt engineering course free” and " \
               "“cisco data analytics free course”."

# ------------------------------------------------------------------ 5. social media trends
# (platform, users in millions, share of the population, when, source key)
PLATFORMS = [
    ("Facebook", 42.057, 0.172, "September 2026", "napoleoncat"),
    ("LinkedIn", 14.04, 0.058, "July 2026", "napoleoncat"),
    ("Instagram", 9.6098, 0.04, "June 2026", "napoleoncat"),
]
# (platform or topic, what we found, source key)
SOCIAL_TRENDS = [
    ("All platforms", "47.8 million social media user identities in Nigeria (October 2025)", "datareportal"),
    ("Instagram", "#cybersecurity has about 3 to 5 million posts (trackers' estimates differ)", "instagram"),
    ("TikTok", "Cybersecurity was one of the top 10 tech topics on TikTok, with 349.1 million views (2021)",
     "tiktok"),
    ("Across 8 networks", "505,330 mentions and 558.6 million views about cybersecurity, 2022 to 2026 (vendor "
     "figures)", "mentions"),
    ("X", "Learners use X to complain in public: AltSchool Africa faced a wave of criticism in October 2025",
     "altschool"),
]
SOCIAL_POINTS = [
    ("Facebook is the biggest: ", "about 42 million users in Nigeria."),
    ("LinkedIn: ", "14 million professionals and employers."),
    ("Content: ", "#cybersecurity has millions of Instagram posts; short how-to videos do well on TikTok."),
    ("Reputation: ", "learners complain in public on X."),
]

# ------------------------------------------------------------------ 6. competitor reviews
# (competitor, what they offer, rating out of 5 or None, where the rating is from, what
#  learners like, what learners complain about, source keys)
COMPETITORS = [
    ("ALX Africa", "Online tech programmes", 4.7, "Trustpilot, 544 reviews",
     "Self-paced, strong community, personal follow-up", "Billing and access problems slow to fix; very demanding",
     ("alx", "alx_review")),
    ("TryHackMe", "Online hands-on cyber labs", 4.5, "Trustpilot, 867 reviews",
     "Beginner-friendly, hands-on rooms, browser AttackBox", "Slow support, discount problems, data privacy",
     ("tryhackme",)),
    ("AltSchool Africa", "Online tech school (no cyber track found)", None, "No Trustpilot rating found",
     "Affordable for self-motivated learners", "Weak grading, missing lectures, login problems (X, Oct 2025)",
     ("altschool",)),
    ("CyberGirls (CyberSafe Foundation)", "Free 7-month fellowship for women", None, "No public rating",
     "Free, with mentoring and internships", "Very hard to get in: 20,000+ applications a year for about 500 places",
     ("cybergirls",)),
    ("NIIT Nigeria, Phillips Consulting", "Classroom courses", None, "No independent reviews found",
     "Classroom teaching; NIIT says 16,000 students a year", "Reviews are hard to find; ₦250,000 for 5 days",
     ("niit", "phillips")),
]

# ------------------------------------------------------------------ 7. marketplace reviews
# (course, platform, rating, ratings count, learners, what learners like, what they complain
#  about, source key)
MARKETPLACE = [
    ("Google Cybersecurity Certificate", "Coursera", 4.8, 41298, 1367882,
     "Great for beginners; good pacing", "Some mistakes in a final quiz", "google_course"),
    ("CompTIA Security+ Complete Course (Jason Dion)", "Udemy", 4.7, 115856, 479288,
     "Clear, thorough instructor", "Exam questions harder than the course", "dion"),
    ("The Complete Cyber Security Course (Nathan House)", "Udemy", 4.6, 58428, 320293,
     "Wide coverage", "Last updated March 2024", "house"),
    ("Security+ Practice Exams, Set 1 (Jason Dion)", "Udemy", 4.5, 3686, 49004,
     "Good exam practice", "Practice only, no teaching", "dion_exams"),
]
MARKETPLACE_NOTE = ("Ratings of the Google certificate are those of its first course, Foundations of Cybersecurity; "
                    "learners are those enrolled in the whole certificate.")
# Complaints that come up again and again in low course reviews
COMMON_COMPLAINTS = ["Outdated content", "Too much theory, no hands-on labs", "Weak support from the instructor"]

# ------------------------------------------------------------------ 8. what customers want
# (need, the evidence, what CyberStart will do)
INSIGHTS = [
    ("A clear path for beginners", "Beginner guides top the search results; Coursera learners praise its pacing",
     "A step-by-step 12-week plan; no IT background needed"),
    ("Hands-on practice", "TryHackMe is praised for labs; “no labs” and “too much theory” drive low ratings",
     "A lab every week, plus a final project"),
    ("A fair, clear price", "Rising “free course” searches; naira prices are hard to find; free places fill fast",
     f"₦{PRICE:,} in {INSTALMENTS} parts, published online; a free first class"),
    ("A certificate and a job", "Guides say to get Security+ or ISC2 CC; jobs are in banks and telecoms",
     "Exam preparation, CV and LinkedIn help, employer links"),
    ("Support and trust", "Complaints about slow support, missing lectures and outdated content",
     "Replies within 24 hours, recorded classes, updated every cohort"),
]

# ------------------------------------------------------------------ 9. marketing mix
MIX = [
    ("Product", "12-week beginner course: live classes, weekly labs, final project, exam preparation, job support"),
    ("Price", f"₦{PRICE:,} in {INSTALMENTS} parts of ₦{PRICE // INSTALMENTS:,}; free first class; employer-"
              "sponsored places"),
    ("Place", "Online nationwide, with weekend labs in Lagos and Abuja"),
    ("Promotion", "Facebook and Instagram adverts, TikTok how-to videos, LinkedIn for employers, reviews on "
                  "Google and Trustpilot"),
]

CONCLUSION = [
    ("The market is growing: ", "Nigeria's cybersecurity market is worth about US$230 million (2025) and grows "
                                "about 10% a year, while trained experts are scarce."),
    ("Customers are searching: ", "cybersecurity is the most searched digital skill on Google Trends in Nigeria."),
    ("Rivals are rated well, ", "but learners complain about support, missing labs, outdated content and "
                                "unclear prices."),
    ("CyberStart wins by: ", "clear prices, weekly labs, fast support and a path to a first job."),
]

# ------------------------------------------------------------------ 10. gaps and opportunities
# The point of the research. Each gap: (gap in the market, evidence from the research, the
# opportunity for CyberStart, demand 1-5, fit with SkillUp 1-5). Demand and fit are my
# judgements from the evidence; Excel multiplies them into a priority score out of 25.
GAPS = [
    ("Affordable courses with live support", "Free places are scarce (CyberGirls: 20,000+ applications for about "
     "500 places); paid options cost ₦250,000 for 5 days or US$1,000+", f"A mid-price course: ₦{PRICE:,} in "
     f"{INSTALMENTS} parts", 5, 5),
    ("Hands-on practice", "“No labs” and “too much theory” drive low course ratings; TryHackMe is praised for its "
     "labs", "A lab every week and a final project", 5, 5),
    ("A route from course to job", "Guides say to get Security+ and a portfolio; banks and insurers are 29% of the "
     "market", "Exam preparation, CV help and employer-sponsored places", 5, 4),
    ("Reliable support", "AltSchool backlash on X; ALX billing fix took 9 days; TryHackMe support is slow",
     "Replies within 24 hours and recorded classes", 4, 5),
    ("Clear prices online", "Few search results show a naira price", "Publish the price; a free first class", 4, 4),
    ("Up-to-date, local content", "A top Udemy course was last updated in March 2024; the CAC breach drove interest",
     "Update every cohort with Nigerian cases", 3, 5),
    ("Trusted local providers", "No independent reviews found for NIIT Nigeria or Phillips Consulting",
     "Collect reviews on Google and Trustpilot", 3, 4),
]

# Opportunities in the market as a whole: (opportunity, evidence, source key)
OPPORTUNITIES = [
    ("A growing market", "US$230 million in 2025, growing about 10% a year to 2031", "mordor"),
    ("A shortage of experts", "About 8,352 professionals in Nigeria against 57,269 in South Africa (2023)",
     "comptia"),
    ("Rising threats", "4,388 attacks a week on each organisation in early 2025, up 47%; the CAC breach in April "
     "2026", "checkpoint"),
    ("Employers who pay", "Banks, finance and insurance are 29.2% of the cybersecurity market", "mordor"),
    ("Nationwide interest", "Cybersecurity is the most searched digital skill in most states, not only Lagos",
     "trends"),
    ("A free exam offer ended", "ISC2 closed its free CC exam programme on 20 May 2026, so learners need exam "
     "preparation", "isc2"),
]
