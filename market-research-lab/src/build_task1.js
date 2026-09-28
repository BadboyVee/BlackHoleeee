// Build Task1_Google_Trends.docx: Part D, Market Research Lab, Task 1 (Google Trends), ready to
// copy into the Module 2 document.
//
// Usage: node build_task1.js out.docx
//
// Google Trends could not be reached from the environment that built this file, so no search
// figures are written in. Everything that does not depend on them (objective, method, search
// terms, time period, location) is filled in; each result is a yellow-highlighted blank with a
// ready-made sentence around it. The last page (not to be copied) says where on Google Trends
// each answer is found. Plain black text and simple tables, so it pastes cleanly into another
// document; saved in Word 2013 compatibility mode.
const fs = require("fs");
const JSZip = require("jszip");
const {
  AlignmentType, BorderStyle, Document, ExternalHyperlink, LevelFormat, Packer, PageBreak, Paragraph,
  ShadingType, Table, TableCell, TableRow, TextRun, VerticalAlign, WidthType,
} = require("docx");

const outPath = process.argv[2];
const PAGE_W = 11906, MARGIN = 1440, TEXT_W = PAGE_W - 2 * MARGIN;   // A4, 2.54 cm margins

const PROGRAMMES = [
  ["Generative AI & Prompt Engineering", "Generative AI + Prompt engineering"],
  ["Digital Marketing", "Digital marketing"],
  ["Data Analytics", "Data analytics"],
  ["Cybersecurity", "Cybersecurity"],
  ["Web Development", "Web development"],
];
const TERMS = PROGRAMMES.map(([, term]) => encodeURIComponent(term)).join(",");
const LINK_12M = `https://trends.google.com/trends/explore?date=today%2012-m&geo=NG&q=${TERMS}&hl=en-GB`;
const LINK_5Y = `https://trends.google.com/trends/explore?date=today%205-y&geo=NG&q=${TERMS}&hl=en-GB`;

// ------------------------------------------------------------------ building blocks
const run = (text, o = {}) => new TextRun({ text, ...o });
const blank = (hint = "") => new TextRun({ text: `[${hint || "      "}]`, highlight: "yellow" });
const para = (children, o = {}) => new Paragraph({ children: typeof children === "string" ? [run(children)] : children, ...o });
const heading = (text) => para([run(text, { bold: true, size: 26 })], { spacing: { before: 240, after: 80 }, keepNext: true });
const step = (children) => para(children, { numbering: { reference: "steps", level: 0 }, spacing: { after: 80 } });
const link = (url, text) => new ExternalHyperlink({ link: url, children: [run(text, { style: "Hyperlink" })] });

const line = { style: BorderStyle.SINGLE, size: 4, color: "000000" };
const borders = { top: line, bottom: line, left: line, right: line };

// widths: fractions of the text width. rows: arrays of cells; a cell is a string, a list of
// TextRuns, or null for a blank to fill in. The first row is the header (bold, light grey).
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
        children: [new Paragraph({
          spacing: { after: 0, line: 240 },
          children: r === 0 ? [run(value, { bold: true })]
            : value === null ? [blank()]
              : typeof value === "string" ? [run(value, { bold: c === 0 })] : value,
        })],
      })),
    })),
  });
}
const gap = () => para("", { spacing: { after: 60 } });
const names = PROGRAMMES.map(([name]) => name);

// ------------------------------------------------------------------ Task 1
const body = [
  para([run("Task 1: Google Trends", { bold: true, size: 30 })], { spacing: { after: 120 } }),
  para([run("Research objective: ", { bold: true }),
    run("To investigate online search interest and search behaviour surrounding the five programme areas.")]),
  para([run("Method: ", { bold: true }),
    run("The five programme areas were compared in one Google Trends search (trends.google.com), which " +
      "compares up to five search terms at a time. Generative AI and prompt engineering were combined into " +
      "one search term with a plus sign (+), so it counts searches for either of them.")]),
  table([0.08, 0.46, 0.46], [
    ["No.", "Programme", "Search term used in Google Trends"],
    ...PROGRAMMES.map(([name, term], i) => [String(i + 1), name, [run(term)]]),
  ]),

  heading("1. Time period"),
  para("Past 12 months (September 2025 to September 2026). The past 5 years (September 2021 to September 2026) " +
    "were also checked to see how interest has changed over a longer time."),

  heading("2. Location"),
  para("Nigeria (all states). Category: All categories. Search type: Web search."),
  para([run("States with the highest interest: "), blank("state"), run(", "), blank("state"), run(" and "),
    blank("state"), run(".")]),

  heading("3. Relative-interest observations"),
  para("Google Trends measures interest on a scale of 0 to 100, where 100 is the highest point of search interest " +
    "among the five terms during the period. It shows relative popularity, not the number of searches."),
  table([0.5, 0.3, 0.2], [
    ["Programme", "Average interest (0–100)", "Rank"],
    ...names.map((name) => [name, null, null]),
  ]),
  gap(),
  para([blank("programme"), run(" had the highest average interest ("), blank(), run(" out of 100), followed by "),
    blank("programme"), run(" ("), blank(), run(") and "), blank("programme"), run(" ("), blank(),
    run("). "), blank("programme"), run(" had the lowest interest ("), blank(),
    run("). This shows that people in Nigeria search most for "), blank("programme"), run(".")]),

  heading("4. Trend changes (over time)"),
  table([0.34, 0.24, 0.2, 0.22], [
    ["Programme", "Past 12 months (rising, falling or stable)", "Highest point (month)", "Past 5 years"],
    ...names.map((name) => [name, null, null, null]),
  ]),
  gap(),
  para([run("Over the past 12 months, interest in "), blank("programme"), run(" rose, while interest in "),
    blank("programme"), run(" fell. The biggest peak was in "), blank("month"), run(" for "), blank("programme"),
    run(". Over the past 5 years, "), blank("programme"), run(" grew the most.")]),

  heading("5. Related topics"),
  para("Related topics are other subjects that people who searched for each term also searched for. " +
    "\"Top\" shows the most popular ones and \"Rising\" shows the ones growing fastest."),
  table([0.3, 0.35, 0.35], [
    ["Programme", "Top related topics", "Rising related topics"],
    ...names.map((name) => [name, null, null]),
  ]),

  heading("6. Related queries"),
  para("Related queries are the exact searches that people who searched for each term also typed."),
  table([0.3, 0.35, 0.35], [
    ["Programme", "Top related queries", "Rising related queries"],
    ...names.map((name) => [name, null, null]),
  ]),

  heading("Summary of findings"),
  para([run("Overall, "), blank("programme"), run(" had the most search interest in Nigeria and "),
    blank("programme"), run(" had the least. Interest in "), blank("programme"),
    run(" is growing fastest. The related queries show that people mainly search for "),
    blank("for example courses, jobs, salaries or free training"),
    run(". The organisation should therefore promote "), blank("programme"),
    run(" first, and use words such as "), blank("keywords"), run(" in its adverts to university students.")]),
];

// ------------------------------------------------------------------ how to fill it in (not to copy)
const guide = [
  para([new PageBreak()]),
  para([run("How to fill in the yellow blanks (do not copy this page)", { bold: true, size: 26 })], { spacing: { after: 120 } }),
  step([run("Open the 12-month comparison, already set to the five terms and Nigeria: "), link(LINK_12M, "Google Trends: past 12 months")]),
  step([run("Relative interest (item 3): "), run("the small \"Average\" bars on the left of the \"Interest over time\" chart " +
    "give each programme's average. Rank them from 1 (highest) to 5.")]),
  step([run("Trend changes (item 4): "), run("look at the shape of each line in \"Interest over time\" and note the month of " +
    "its highest point. Then open the 5-year view for the last column: "), link(LINK_5Y, "Google Trends: past 5 years")]),
  step([run("Location (item 2): "), run("scroll to \"Compared breakdown by region\" and note the states with the " +
    "highest interest.")]),
  step([run("Related topics and queries (items 5 and 6): "), run("scroll to the bottom. Each programme has its own " +
    "\"Related topics\" and \"Related queries\" boxes; write down the first 3 under \"Top\", then switch to " +
    "\"Rising\" and write down the first 3. If a box says there is not enough data, write \"Not enough data\" " +
    "(it means few people in Nigeria searched for that term).")]),
  step([run("Fill in the Summary of findings from your answers above.")]),
  step([run("Replace every yellow blank, then remove the highlight: select the text and choose Home › Text " +
    "Highlight Color › No Color.")]),
  step([run("To copy into your Module 2 document: click just before \"Task 1: Google Trends\" on the first page, " +
    "hold Shift and click just after the last sentence of the Summary of findings, and press Ctrl+C. In your " +
    "document, choose Home › Paste › Merge Formatting so the text takes your document's font.")]),
];

const doc = new Document({
  creator: "Market Research Lab",
  title: "Task 1: Google Trends",
  styles: {
    default: { document: { run: { font: "Calibri", size: 22 }, paragraph: { spacing: { after: 120, line: 259 } } } },
  },
  numbering: {
    config: [
      { reference: "steps", levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT,
        style: { paragraph: { indent: { left: 360, hanging: 360 } } } }] },
    ],
  },
  sections: [{
    properties: { page: { size: { width: PAGE_W, height: 16838 }, margin: { top: MARGIN, bottom: MARGIN, left: MARGIN, right: MARGIN } } },
    children: [...body, ...guide],
  }],
});

// docx-js writes <w:highlightCs> next to every <w:highlight>. That element is not in the Word file
// standard, and Word 2013 may reject the file for it, so it is removed; the highlight stays.
Packer.toBuffer(doc)
  .then((buf) => JSZip.loadAsync(buf))
  .then(async (zip) => {
    const xml = await zip.file("word/document.xml").async("string");
    zip.file("word/document.xml", xml.replace(/<w:highlightCs\b[^>]*\/>/g, ""));
    return zip.generateAsync({ type: "nodebuffer", compression: "DEFLATE" });
  })
  .then((buf) => {
    fs.writeFileSync(outPath, buf);
    console.log(`wrote ${outPath}`);
  });
