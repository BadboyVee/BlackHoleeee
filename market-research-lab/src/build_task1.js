// Build Task1_Google_Trends.docx: Part D, Market Research Lab, Task 1 (Google Trends), ready to
// copy into the Module 2 document.
//
// Usage: node build_task1.js out.docx
//
// The results were read from screenshots of Google Trends taken on 28 September 2026 (Nigeria,
// past 12 months, all categories, web search): the "Interest over time" chart of the five
// programmes, "Compared breakdown by sub-region" (sorted by interest in Generative AI + Prompt
// engineering), and the "Rising" related topics and queries of each programme on its own.
// Averages are read off the chart's "Average" bars, so they are given as "about".
//
// Plain black text and simple tables, so it pastes cleanly into another document; saved in
// Word 2013 compatibility mode.
const fs = require("fs");
const {
  BorderStyle, Document, Packer, Paragraph, ShadingType, Table, TableCell, TableRow, TextRun,
  VerticalAlign, WidthType,
} = require("docx");

const outPath = process.argv[2];
const PAGE_W = 11906, MARGIN = 1440, TEXT_W = PAGE_W - 2 * MARGIN;   // A4, 2.54 cm margins

// ------------------------------------------------------------------ what Google Trends showed
const PROGRAMMES = [
  { name: "Generative AI & Prompt Engineering", term: "Generative AI + Prompt engineering", colour: "Blue",
    average: "about 13", rank: "4 (joint)",
    change: "Low all year (about 10 to 20). Rose slightly in November 2025, stayed around 15 to 20 until mid-2026, then fell to about 10 by September 2026.",
    peak: "About 20; no single clear peak",
    topics: ["March (month) (Breakout)", "Türkiye (country) (Breakout)", "Spain (country) (Breakout)", "Documentation (Breakout)",
      "Japan (country) (Breakout)"],
    queries: ["google prompt engineering course free (Breakout)", "wikipedia (Breakout)", "open generative ai github (Breakout)",
      "generative ai news (+1,150%)", "how to bake a cake (+500%)"] },
  { name: "Digital Marketing", term: "Digital marketing", colour: "Red",
    average: "about 33", rank: "2",
    change: "Steady at 30 to 40 until a peak in late January 2026, then a slow fall to about 22 by September 2026.",
    peak: "Late January 2026 (about 50)",
    topics: ["Academic degree (Breakout)", "Digital product (+500%)", "Contented (+500%)", "Average (+400%)", "Brand (+80%)"],
    queries: ["frontend development (Breakout)", "backend development (Breakout)", "lidl near me (Breakout)",
      "miami digital marketing agencies (Breakout)", "openai (+500%)"] },
  { name: "Data Analytics", term: "Data analytics", colour: "Yellow",
    average: "about 18", rank: "3",
    change: "Stable at about 15 to 25 all year, with a dip in late December 2025 and a slight fall towards September 2026.",
    peak: "Small peaks of about 25 (November 2025, January and February 2026)",
    topics: ["Academic degree (Breakout)", "Documentation (Breakout)", "November (month) (Breakout)", "December (month) (Breakout)",
      "April (month) (Breakout)"],
    queries: ["lidl near me (Breakout)", "cisco data analytics free course (Breakout)", "forage deloitte data analytics (+1,050%)",
      "data analytics manager (+250%)", "maven analytics data playground (+250%)"] },
  { name: "Cybersecurity", term: "Cybersecurity", colour: "Green",
    average: "about 43", rank: "1",
    change: "The highest line almost all year (about 40 to 50). It dipped in late December 2025, jumped to 100 in April 2026, then fell back and eased to about 30 by September 2026.",
    peak: "April 2026 (100, the highest point of all five)",
    topics: ["Corporate Affairs Commission (Breakout)", "Reuters (news agency) (Breakout)", "Lidl (Breakout)",
      "Lidl Stiftung & Co. KG (supermarket chain) (Breakout)", "Governance (Breakout)"],
    queries: ["cac cybersecurity breach (Breakout)", "cybersecurity news today (Breakout)", "wikipedia (Breakout)",
      "ai news today (Breakout)", "lagos cybersecurity guidelines (Breakout)"] },
  { name: "Web Development", term: "Web development", colour: "Purple",
    average: "about 13", rank: "4 (joint)",
    change: "Low and stable at about 10 to 20 all year.",
    peak: "No clear peak",
    topics: ["Best practice (Breakout)", "Wikipedia (software) (Breakout)", "Lidl Stiftung & Co. KG (supermarket chain) (Breakout)",
      "June (month) (Breakout)", "April (month) (Breakout)"],
    queries: ["wikipedia (Breakout)", "lidl near me (Breakout)", "python web framework (Breakout)",
      "kubernetes orchestration (Breakout)", "internet of things examples (Breakout)"] },
];
const TOP_STATES = ["Benue", "Cross River", "Federal Capital Territory (Abuja)", "Rivers", "Kwara"];

// ------------------------------------------------------------------ building blocks
const run = (text, o = {}) => new TextRun({ text, ...o });
const para = (children, o = {}) => new Paragraph({ children: typeof children === "string" ? [run(children)] : children, ...o });
const heading = (text) => para([run(text, { bold: true, size: 26 })], { spacing: { before: 240, after: 80 }, keepNext: true });

const line = { style: BorderStyle.SINGLE, size: 4, color: "000000" };
const borders = { top: line, bottom: line, left: line, right: line };

// widths: fractions of the text width. rows: arrays of cells; a cell is a string or an array of
// strings (one line each). The first row is the header (bold, light grey); the first column is bold.
function table(widths, rows) {
  const cols = widths.map((w) => Math.round(w * TEXT_W));
  cols[cols.length - 1] = TEXT_W - cols.slice(0, -1).reduce((a, b) => a + b, 0);
  return new Table({
    width: { size: TEXT_W, type: WidthType.DXA },
    columnWidths: cols,
    margins: { top: 60, bottom: 60, left: 100, right: 100 },
    rows: rows.map((cells, r) => new TableRow({
      tableHeader: r === 0,
      cantSplit: true,
      children: cells.map((value, c) => new TableCell({
        width: { size: cols[c], type: WidthType.DXA },
        borders,
        verticalAlign: VerticalAlign.CENTER,
        shading: r === 0 ? { fill: "D9D9D9", type: ShadingType.CLEAR, color: "auto" } : undefined,
        children: (Array.isArray(value) ? value : [value]).map((text, k, all) => new Paragraph({
          spacing: { after: k < all.length - 1 ? 40 : 0, line: 240 },
          children: [run(Array.isArray(value) ? `${k + 1}. ${text}` : text, { bold: r === 0 || c === 0 })],
        })),
      })),
    })),
  });
}
const gap = () => para("", { spacing: { after: 60 } });
const byName = Object.fromEntries(PROGRAMMES.map((p) => [p.name, p]));

// ------------------------------------------------------------------ Task 1
const body = [
  para([run("Task 1: Google Trends", { bold: true, size: 30 })], { spacing: { after: 120 } }),
  para([run("Research objective: ", { bold: true }),
    run("To investigate online search interest and search behaviour surrounding the five programme areas.")]),
  para([run("Method: ", { bold: true }),
    run("The five programme areas were compared in one Google Trends search (trends.google.com) on 28 September 2026. " +
      "Google Trends compares up to five search terms at a time, so Generative AI and prompt engineering were combined " +
      "into one search term with a plus sign (+), which counts searches for either of them. Each programme was then " +
      "searched on its own to record its related topics and related queries.")]),
  table([0.34, 0.42, 0.24], [
    ["Programme", "Search term used in Google Trends", "Colour on the chart"],
    ...PROGRAMMES.map((p) => [p.name, p.term, p.colour]),
  ]),

  heading("1. Time period"),
  para("Past 12 months: 28 September 2025 to 28 September 2026, shown week by week."),

  heading("2. Location"),
  para("Nigeria (all states). Category: All categories. Search type: Web search."),
  para("The \"Compared breakdown by sub-region\" map shows that Cybersecurity was the most searched of the five " +
    "programmes in most states (green on the map), especially in the north and the middle of the country. Digital " +
    "marketing was the most searched in several southern states (red on the map)."),
  para([run("Sorted by interest in Generative AI & Prompt Engineering, the top five states were: "),
    run(TOP_STATES.map((s, i) => `${i + 1}. ${s}`).join("; ") + "."),
    run(" Even in these states, Cybersecurity had the largest share of the five programmes' searches.")]),

  heading("3. Relative-interest observations"),
  para("Google Trends measures interest on a scale of 0 to 100, where 100 is the highest point of search interest " +
    "among the five terms during the period. It shows relative popularity, not the number of searches. The averages " +
    "below are read from the \"Average\" bars beside the \"Interest over time\" chart."),
  table([0.5, 0.3, 0.2], [
    ["Programme", "Average interest (0–100)", "Rank"],
    ...[...PROGRAMMES].sort((a, b) => a.rank.localeCompare(b.rank)).map((p) => [p.name, p.average, p.rank]),
  ]),
  gap(),
  para("Cybersecurity had the highest average interest (about 43 out of 100), followed by Digital Marketing (about 33) " +
    "and Data Analytics (about 18). Generative AI & Prompt Engineering and Web Development had the lowest interest " +
    "(about 13 each). This shows that people in Nigeria search most for cybersecurity, and more than three times as " +
    "much as for generative AI or web development."),

  heading("4. Trend changes (over time)"),
  table([0.25, 0.5, 0.25], [
    ["Programme", "How interest changed over the 12 months", "Highest point"],
    ...PROGRAMMES.map((p) => [p.name, p.change, p.peak]),
  ]),
  gap(),
  para("Cybersecurity stayed the most searched programme for almost the whole year. Its interest jumped to the " +
    "maximum of 100 in April 2026; the related searches for \"cac cybersecurity breach\" and the Corporate Affairs " +
    "Commission suggest this was caused by news of a cybersecurity breach at the CAC. Digital Marketing peaked in late " +
    "January 2026 and then slowly declined. Data Analytics, Web Development and Generative AI & Prompt Engineering " +
    "stayed low and fairly stable. Interest in Cybersecurity and Data Analytics dipped in late December 2025, during " +
    "the Christmas and New Year holidays."),

  heading("5. Related topics"),
  para("Related topics are other subjects that people who searched for each programme also searched for. The lists " +
    "below are the \"Rising\" topics (the fastest-growing), top five for each programme, with their growth. \"Breakout\" means searches " +
    "grew by more than 5,000%."),
  table([0.3, 0.7], [
    ["Programme", "Rising related topics"],
    ...PROGRAMMES.map((p) => [p.name, p.topics]),
  ]),
  gap(),
  para("Many rising topics are general (months, countries, Wikipedia and the Lidl supermarket chain), which happens " +
    "when search numbers are small. The useful ones show interest in academic degrees (Digital Marketing and Data " +
    "Analytics), documentation and best practice (learning resources), digital products and brands (Digital " +
    "Marketing), and the Corporate Affairs Commission and governance (Cybersecurity)."),

  heading("6. Related queries"),
  para("Related queries are the exact searches that people who searched for each programme also typed. The lists " +
    "below are the \"Rising\" queries, top five for each programme, with their growth."),
  table([0.3, 0.7], [
    ["Programme", "Rising related queries"],
    ...PROGRAMMES.map((p) => [p.name, p.queries]),
  ]),
  gap(),
  para("The related queries show four kinds of search: free courses (\"google prompt engineering course free\", " +
    "\"cisco data analytics free course\", \"forage deloitte data analytics\"), practical skills (\"frontend " +
    "development\", \"backend development\", \"python web framework\", \"kubernetes orchestration\"), careers (\"data " +
    "analytics manager\") and news (\"generative ai news\", \"cybersecurity news today\", \"cac cybersecurity breach\", " +
    "\"lagos cybersecurity guidelines\"). People searching for Digital Marketing also searched for frontend and backend " +
    "development, so the two programmes attract similar students."),

  heading("Summary of findings"),
  para("Overall, Cybersecurity had the most search interest in Nigeria (about 43 out of 100 on average) and was the " +
    "most searched programme in most states, followed by Digital Marketing (about 33). Data Analytics (about 18), Web " +
    "Development and Generative AI & Prompt Engineering (about 13 each) had much lower interest. Interest in " +
    "Cybersecurity jumped in April 2026 after news of a breach at the CAC, while Digital Marketing peaked in late January " +
    "2026 and then slowly fell. The related queries show that people mainly look for free courses, practical skills, " +
    "jobs and news. The organisation should therefore promote Cybersecurity and Digital Marketing first, and use words " +
    "such as \"free course\" and job titles (for example \"data analytics manager\") in its adverts to university " +
    "students. Generative AI & Prompt Engineering has low search interest, so it will need more awareness-raising " +
    "before it attracts many students."),
];

const doc = new Document({
  creator: "Market Research Lab",
  title: "Task 1: Google Trends",
  styles: {
    default: { document: { run: { font: "Calibri", size: 22 }, paragraph: { spacing: { after: 120, line: 259 } } } },
  },
  sections: [{
    properties: { page: { size: { width: PAGE_W, height: 16838 }, margin: { top: MARGIN, bottom: MARGIN, left: MARGIN, right: MARGIN } } },
    children: body,
  }],
});

Packer.toBuffer(doc).then((buf) => {
  fs.writeFileSync(outPath, buf);
  console.log(`wrote ${outPath}`);
});
