# Capstone Project: Market Gaps and Opportunities

The task: choose a business or product, define its market, and run customer research with
Google Search, Google Trends, social media trends, competitor reviews and marketplace reviews to
find the market's gaps and opportunities.

The product is **CyberStart**, a 12-week beginner cybersecurity course from **SkillUp Academy**,
the business in the segmentation assignment. Cybersecurity learners were the segment that
assignment found most attractive.

| File | What it is |
|---|---|
| [Capstone_Market_Research.pptx](Capstone_Market_Research.pptx) | The 16-slide report in the minimal teal design, with animations and slide timings (about 7 minutes). Opens in PowerPoint 2013 and later. |
| [Capstone_Market_Research.xlsx](Capstone_Market_Research.xlsx) | The research in seven sheets: Market, Google Search, Google Trends, Social Media, Reviews, Gaps & Opportunities, Sources. Live formulas; assumptions in yellow cells. Opens in Excel 2013 and later. |
| [src/](src/) | The scripts that build both files; all the research is in `src/capstone_data.py`. |

## What the research found

**Gaps** (scored in Excel: demand × fit, out of 25):

| Gap | Priority |
|---|---|
| Affordable courses with live support | 25 |
| Hands-on practice | 25 |
| A route from course to job | 20 |
| Reliable support | 20 |
| Clear prices online | 16 |
| Up-to-date, local content | 15 |
| Trusted local providers | 12 |

**Opportunities:** a market of about US$230 million (2025) growing about 10% a year; only
about 8,352 cybersecurity professionals in Nigeria (2023); rising attacks and the CAC breach of
April 2026; banks, finance and insurance as 29.2% of the market; nationwide search interest; and
the end of ISC2's free exam offer in May 2026.

**Year 1 estimate** (Market sheet): 375 learners and ₦56.25 million, from the 3MTT target,
cybersecurity's share of its twelve skills, and two assumptions you can change.

## Notes on the sources

- Google Trends: the Market Research Lab Task 1 screenshots (28 September 2026; Nigeria, past
  12 months).
- Google Search: the five searches on the Google Search sheet were run with a web search engine
  on 9 October 2026. Run them again on Google to add screenshots to the report.
- Everything else comes from the web sources listed, with links, on the Sources sheet, found on 8
  and 9 October 2026. Figures are as those sources report them, and the sheet notes where they
  disagree.

## Rebuilding

Run `src/build.sh`. It needs Python with openpyxl, python-pptx, lxml, numpy and Pillow, and
LibreOffice. It reuses `../pz-analysis/src/office2013.py`, `../assignment/src` (the slide design
and the text-fit check) and `../marketing-budget/src` (chart clean-up, transitions, animations
and validation). Set `SCHEMA_DIR` to the ISO/IEC 29500 transitional schemas to check both files.
