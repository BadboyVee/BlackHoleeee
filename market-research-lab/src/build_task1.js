// Build Task1_Google_Trends.docx: Part D, Market Research Lab, Task 1 (Google Trends), ready to
// copy into the Module 2 document.
//
// Usage: node build_task1.js out.docx
//
// The results were read from screenshots of Google Trends taken on 28 September 2026 (Nigeria,
// past 12 months, all categories, web search): the "Interest over time" chart of the five
// programmes, "Compared breakdown by sub-region" (sorted by interest in Generative AI + Prompt
// engineering), and the "Rising" related topics and queries of each programme on its own.
// Averages are read off the chart's "Average" bars, so they are given as "around".
//
// Written in short, plain sentences. Plain black text and simple tables, so it pastes cleanly
// into another document; saved in Word 2013 compatibility mode.
const fs = require("fs");
const {
  AlignmentType, BorderStyle, Document, LevelFormat, Packer, Paragraph, ShadingType, Table, TableCell, TableRow, TextRun,
  VerticalAlign, WidthType,
} = require("docx");

const outPath = process.argv[2];
const PAGE_W = 11906, MARGIN = 1440, TEXT_W = PAGE_W - 2 * MARGIN;   // A4, 2.54 cm margins

// ------------------------------------------------------------------ what Google Trends showed
const PROGRAMMES = [
  { name: "Generative AI & Prompt Engineering", term: "Generative AI + Prompt engineering",
    average: "Around 13", rank: "4",
    topics: "March, Türkiye, Spain, Documentation, Japan",
    queries: "google prompt engineering course free, wikipedia, open generative ai github, generative ai news, how to bake a cake" },
  { name: "Digital Marketing", term: "Digital marketing",
    average: "Around 33", rank: "2",
    topics: "Academic degree, Digital product, Contented, Average, Brand",
    queries: "frontend development, backend development, lidl near me, miami digital marketing agencies, openai" },
  { name: "Data Analytics", term: "Data analytics",
    average: "Around 18", rank: "3",
    topics: "Academic degree, Documentation, November, December, April",
    queries: "lidl near me, cisco data analytics free course, forage deloitte data analytics, data analytics manager, maven analytics data playground" },
  { name: "Cybersecurity", term: "Cybersecurity",
    average: "Around 43", rank: "1",
    topics: "Corporate Affairs Commission, Reuters, Lidl, Lidl Stiftung & Co. KG, Governance",
    queries: "cac cybersecurity breach, cybersecurity news today, wikipedia, ai news today, lagos cybersecurity guidelines" },
  { name: "Web Development", term: "Web development",
    average: "Around 13", rank: "4",
    topics: "Best practice, Wikipedia, Lidl Stiftung & Co. KG, June, April",
    queries: "wikipedia, lidl near me, python web framework, kubernetes orchestration, internet of things examples" },
];

// ------------------------------------------------------------------ building blocks
const run = (text, o = {}) => new TextRun({ text, ...o });
const para = (children, o = {}) => new Paragraph({ children: typeof children === "string" ? [run(children)] : children, ...o });
const heading = (text) => para([run(text, { bold: true, size: 24 })], { spacing: { before: 200, after: 60 }, keepNext: true });
const bullet = (text) => para(text, { numbering: { reference: "bullets", level: 0 }, spacing: { after: 60 } });

const line = { style: BorderStyle.SINGLE, size: 4, color: "000000" };
const borders = { top: line, bottom: line, left: line, right: line };

// widths: fractions of the text width; the first row is the header (bold, light grey).
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
      children: cells.map((text, c) => new TableCell({
        width: { size: cols[c], type: WidthType.DXA },
        borders,
        verticalAlign: VerticalAlign.CENTER,
        shading: r === 0 ? { fill: "D9D9D9", type: ShadingType.CLEAR, color: "auto" } : undefined,
        children: [new Paragraph({ spacing: { after: 0, line: 240 }, children: [run(text, { bold: r === 0 })] })],
      })),
    })),
  });
}
const gap = () => para("", { spacing: { after: 40 } });

// ------------------------------------------------------------------ Task 1
const body = [
  para([run("Task 1: Google Trends", { bold: true, size: 28 })], { spacing: { after: 120 } }),
  para([run("Objective: ", { bold: true }),
    run("To find out how much people in Nigeria search online for the five programmes.")]),
  para([run("What I did: ", { bold: true }),
    run("I compared the five programmes on Google Trends on 28 September 2026. Google Trends only allows five " +
      "search terms, so I put Generative AI and Prompt engineering together as one term. I then searched each " +
      "programme on its own to get its related topics and related queries.")]),
  para([run("Search terms used:", { bold: true })], { spacing: { after: 60 } }),
  ...PROGRAMMES.map((p) => bullet(p.term)),

  heading("1. Time period"),
  para("Past 12 months (28 September 2025 to 28 September 2026)."),

  heading("2. Location"),
  para("Nigeria."),
  para("Cybersecurity was the most searched programme in most states, especially in the north and the middle of the " +
    "country. Digital Marketing was the most searched in some southern states."),
  para("The top states for Generative AI & Prompt Engineering were Benue, Cross River, FCT (Abuja), Rivers and Kwara."),

  heading("3. Relative-interest observations"),
  para("Google Trends gives each programme a score from 0 to 100, where 100 means the highest interest."),
  table([0.5, 0.28, 0.22], [
    ["Programme", "Average score", "Rank"],
    ...[...PROGRAMMES].sort((a, b) => a.rank.localeCompare(b.rank)).map((p) => [p.name, p.average, p.rank]),
  ]),
  gap(),
  para("Cybersecurity had the highest interest, followed by Digital Marketing. Generative AI & Prompt Engineering " +
    "and Web Development had the lowest interest."),

  heading("4. Trend changes (over time)"),
  bullet("Cybersecurity was the highest almost all year. It jumped to 100 in April 2026, probably because of news " +
    "about a cybersecurity breach at the CAC (Corporate Affairs Commission)."),
  bullet("Digital Marketing was steady, reached its highest point in late January 2026, then slowly dropped."),
  bullet("Data Analytics stayed steady at a low level (around 15 to 25)."),
  bullet("Generative AI & Prompt Engineering and Web Development stayed low all year (around 10 to 20)."),
  bullet("Cybersecurity and Data Analytics dropped a little in late December 2025 because of the Christmas holidays."),

  heading("5. Related topics"),
  para("These are the rising topics that people also searched for."),
  table([0.34, 0.66], [
    ["Programme", "Related topics"],
    ...PROGRAMMES.map((p) => [p.name, p.topics]),
  ]),
  gap(),
  para("Some topics, like months, countries, Wikipedia and Lidl, are not really linked to the programmes."),

  heading("6. Related queries"),
  para("These are the rising searches that people also typed."),
  table([0.34, 0.66], [
    ["Programme", "Related queries"],
    ...PROGRAMMES.map((p) => [p.name, p.queries]),
  ]),
  gap(),
  para("People mostly search for free courses, skills, jobs and news."),

  heading("Conclusion"),
  para("Cybersecurity is the most popular programme in Nigeria, followed by Digital Marketing. Generative AI & Prompt " +
    "Engineering and Web Development have the lowest interest. Since many people search for free courses, the " +
    "organisation should promote Cybersecurity and Digital Marketing first and use words like \"free course\" in " +
    "its adverts."),
];

const doc = new Document({
  creator: "Market Research Lab",
  title: "Task 1: Google Trends",
  styles: {
    default: { document: { run: { font: "Calibri", size: 22 }, paragraph: { spacing: { after: 120, line: 259 } } } },
  },
  numbering: {
    config: [{ reference: "bullets", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT,
      style: { paragraph: { indent: { left: 360, hanging: 360 } } } }] }],
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
