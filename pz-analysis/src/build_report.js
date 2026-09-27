// Build the written report: PZ Nigeria PESTLE, SWOT and industry analysis, as a Word document.
//
// Usage: node build_report.js slide_data.json out.docx
//
// Every rating, score and conclusion comes from slide_data.json, which export_slide_data.py
// reads out of the finished workbook, so the report agrees with the Excel file and the slides.
//
// Look: Word 2013's defaults (A4, 2.54 cm margins, Calibri 11 with 1.08 line spacing, Calibri
// Light headings) with the same two colours as the slides and workbook: dark blue for the
// title, headings and table header rows, and orange for the line under the title and for "High"
// ratings. The file is saved in Word 2013 compatibility mode.
const fs = require("fs");
const {
  AlignmentType, BorderStyle, Document, Footer, HeadingLevel, LevelFormat, Packer, PageNumber,
  Paragraph, ShadingType, Table, TableCell, TableRow, TextRun, VerticalAlign, WidthType,
} = require("docx");

const [dataPath, outPath] = process.argv.slice(2);
const data = JSON.parse(fs.readFileSync(dataPath, "utf8"));

const NAVY = "1F4E79";     // Blue, Accent 1, Darker 50%
const ORANGE = "C55A11";   // Orange, Accent 2, Darker 25%
const GREY_LINE = "BFBFBF";
const PAGE_W = 11906, MARGIN = 1440, TEXT_W = PAGE_W - 2 * MARGIN;   // A4, 1" margins

const one = (x) => x.toFixed(1);
const two = (x) => x.toFixed(2);
// Lower-case the first letter for use mid-sentence, but leave acronyms (FX, NAFDAC) alone.
const lc = (t) => (/^[A-Z][a-z]/.test(t) ? t.charAt(0).toLowerCase() + t.slice(1) : t);
const sentence = (t) => (/[.!?]$/.test(t) ? t : `${t}.`);

// ------------------------------------------------------------------ building blocks
const run = (text, o = {}) => new TextRun({ text, ...o });
const para = (children, o = {}) => new Paragraph({ children: typeof children === "string" ? [run(children)] : children, ...o });
const h1 = (text) => new Paragraph({ heading: HeadingLevel.HEADING_1, children: [run(text)] });
const h2 = (text) => new Paragraph({ heading: HeadingLevel.HEADING_2, children: [run(text)] });
const bullet = (children) => para(children, { numbering: { reference: "bullets", level: 0 }, spacing: { after: 60 } });
const numbered = (children) => para(children, { numbering: { reference: "numbers", level: 0 }, spacing: { after: 80 } });
const label = (text) => run(text, { bold: true, color: NAVY });
const priority = (p) => (p === "High" ? run(p, { bold: true, color: ORANGE }) : run(p));

const border = { style: BorderStyle.SINGLE, size: 4, color: GREY_LINE };
const borders = { top: border, bottom: border, left: border, right: border };

// widths: fractions of the text width; rows: arrays of cell contents (a string, or an array
// of TextRuns). The first row is the header: dark blue with white bold text.
function table(widths, rows, { centre = [] } = {}) {
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
        shading: r === 0 ? { fill: NAVY, type: ShadingType.CLEAR, color: "auto" } : undefined,
        children: [new Paragraph({
          alignment: centre.includes(c) ? AlignmentType.CENTER : AlignmentType.LEFT,
          spacing: { after: 0, line: 240 },
          children: r === 0 ? [run(value, { bold: true, color: "FFFFFF" })]
            : (typeof value === "string" ? [run(value)] : value),
        })],
      })),
    })),
  });
}
const gap = () => para("", { spacing: { after: 120 } });

// ------------------------------------------------------------------ figures from Excel
const c = data.company;
const summary = Object.fromEntries(data.pestleSummary.map((f) => [f.factor, f]));
const issuesOf = (factor) => data.pestle.filter((p) => p.factor === factor);
const top = [...data.pestleSummary].sort((a, b) => b.average - a.average)[0];
const low = [...data.pestleSummary].sort((a, b) => a.average - b.average)[0];
const topIssue = [...data.pestle].sort((a, b) => b.score - a.score)[0];
const highCount = data.pestle.filter((p) => p.priority === "High").length;
const threats = data.pestle.filter((p) => p.type === "Threat").length;
const opps = data.pestle.filter((p) => p.type === "Opportunity").length;
const pos = data.position;

// What each PESTLE factor means for PZ.
const SO_WHAT = {
  Political: "PZ needs to follow government policy closely and plan for higher costs.",
  Economic: "A weak naira raises PZ's costs, while high inflation and interest rates reduce what shoppers can spend.",
  Social: "Nigeria's young and growing population is a large market, but shoppers want value for money.",
  Technological: "Digital channels are a cheap way to reach young buyers, but poor power supply raises costs.",
  Legal: "PZ must register its products and follow advertising, consumer and tax rules, which adds cost and time.",
  Environmental: "Plastic rules and climate risks mean PZ must plan greener packaging and protect its deliveries.",
};
const SWOT_INTRO = {
  strengths: "PZ's strengths come from its brands, its long history in Nigeria and the way it is organised.",
  weaknesses: "Most of PZ's weaknesses slow it down or raise its costs.",
  opportunities: "The opportunities come from Nigeria's large market and from changes among competitors.",
  threats: "The threats come mainly from the economy and from competition.",
};

// ------------------------------------------------------------------ the report
const body = [];

// Title block
body.push(new Paragraph({ heading: HeadingLevel.TITLE, children: [run("PZ Nigeria Limited")] }));
body.push(para([run("PESTLE, SWOT and Industry Analysis", { size: 28, color: "404040" })], {
  border: { top: { style: BorderStyle.SINGLE, size: 18, color: ORANGE, space: 8 } }, spacing: { before: 120, after: 60 },
}));
body.push(para("Marketing Department, Ilupeju, Lagos", { spacing: { after: 60 } }));
body.push(para([run("Prepared by: ", { bold: true }), run("______________________________"),
  run("        Date: ", { bold: true }), run("____________________")], { spacing: { after: 240 } }));

// 1. Introduction
body.push(h1("1. Introduction"));
body.push(para("PZ Nigeria Limited is part of the PZ Cussons group, which is based in the United Kingdom. " +
  "The company has two businesses:"));
body.push(bullet([label("Family Care (consumer): "), run(sentence(c["Consumer business (Family Care)"]))]));
body.push(bullet([label("Electrical: "), run(sentence(c["Electrical business"]))]));
body.push(para(
  `The company is led by ${c["Managing Director"]}, the Managing Director, and ${c["Chief Financial Officer"]}, ` +
  "the Chief Financial Officer. It uses a product and brand structure: the Managing Director, supported by the CFO " +
  "and the HR Director, leads the category managers; each brand has its own brand manager, supported by assistant " +
  "brand managers; and shared departments serve all the brands.", { spacing: { before: 120 } }));
body.push(para(
  "This report looks at PZ Nigeria's business environment with a PESTLE analysis, at the company itself with a " +
  "SWOT analysis, and at its industry with Porter's Five Forces, and ends with recommendations. The scores were " +
  "calculated in Microsoft Excel (PZ_Nigeria_Analysis.xlsx) and are presented in PZ_Nigeria_Analysis.pptx."));

// 2. PESTLE
body.push(h1("2. PESTLE Analysis"));
body.push(para(
  "A PESTLE analysis looks at the Political, Economic, Social, Technological, Legal and Environmental factors " +
  "outside the company that affect it. Each issue was rated for its impact on PZ (1 = low, 5 = high) and for how " +
  "likely it is (1 = unlikely, 5 = almost certain). The score is impact × likelihood, out of 25: 16 or more is high " +
  "priority, 9 to 15 is medium and below 9 is low."));
data.pestleSummary.forEach((f, i) => {
  body.push(h2(`2.${i + 1} ${f.factor} factors`));
  body.push(para([label("Average score: "), run(`${one(f.average)} out of 25 (rank ${f.rank} of ${data.pestleSummary.length})`)]));
  issuesOf(f.factor).forEach((p) => body.push(bullet([
    run(`${p.issue}: `, { bold: true }), run(`${sentence(p.effect)} Score ${p.score}, `), priority(p.priority),
    run(" priority."),
  ])));
  body.push(para(SO_WHAT[f.factor], { spacing: { before: 120 } }));
});
const n = data.pestleSummary.length;
body.push(h2(`2.${n + 1} PESTLE summary`));
body.push(table([0.34, 0.22, 0.26, 0.18], [
  ["Factor", "Average score (of 25)", "High-priority issues", "Rank"],
  ...data.pestleSummary.map((f) => [[run(f.factor, { bold: true })], one(f.average), String(f.high), String(f.rank)]),
  [[run("All factors", { bold: true })], [run(one(data.pestleAverage), { bold: true })],
    [run(String(highCount), { bold: true })], ""],
], { centre: [1, 2, 3] }));
body.push(gap());
body.push(para(
  `${top.factor} factors matter most, with an average of ${one(top.average)} out of 25, and the biggest single issue ` +
  `is ${lc(topIssue.issue)}, which scores the maximum of ${topIssue.score}. ${low.factor} factors matter least ` +
  `(${one(low.average)}). In total ${highCount} of the ${data.pestle.length} issues are high priority, and there are ` +
  `${threats} threats against ${opps} opportunities, so PZ's business environment is difficult, mainly because of ` +
  "the economy."));

// 3. SWOT
body.push(h1("3. SWOT Analysis"));
body.push(para(
  "A SWOT analysis sums up the company's internal strengths and weaknesses, and the external opportunities and " +
  "threats it faces."));
[["strengths", "Strengths"], ["weaknesses", "Weaknesses"], ["opportunities", "Opportunities"], ["threats", "Threats"]]
  .forEach(([key, name], i) => {
    body.push(h2(`3.${i + 1} ${name}`));
    body.push(para(SWOT_INTRO[key]));
    data.swot[key].forEach((point) => body.push(bullet([run(sentence(point))])));
  });
body.push(h2("3.5 SWOT scoring (IFE and EFE)"));
body.push(para(
  "To see which points matter most, each one was given a weight for its importance (each set of weights adds up " +
  "to 1.00) and a rating from 1 to 4. For the internal factors (IFE), strengths are rated 3 or 4 and weaknesses 1 " +
  "or 2; for the external factors (EFE), the rating shows how well PZ responds today. Weight × rating gives the " +
  "weighted score, and a total of 2.50 is average.", { keepNext: true }));
const total = (text) => [run(text, { bold: true })];
body.push(table([0.6, 0.4], [
  ["Group", "Weighted score"],
  ["Strengths", two(pos.strengths)],
  ["Weaknesses", two(pos.weaknesses)],
  [total("IFE total (internal factors)"), total(two(data.ifeTotal))],
  ["Opportunities", two(pos.opportunities)],
  ["Threats", two(pos.threats)],
  [total("EFE total (external factors)"), total(two(data.efeTotal))],
], { centre: [1] }));
body.push(gap());
body.push(para(
  `The IFE total of ${two(data.ifeTotal)} is ${lc(data.ifeResult).replace(": ", ", so ")}. The EFE total of ` +
  `${two(data.efeTotal)} is ${lc(data.efeResult).replace(": ", ", so ")}. Together they place PZ in cell ` +
  `${pos.ieCell} of the internal-external (IE) matrix, ` +
  `which means ${pos.strategy.toLowerCase()}: the right strategies are ${pos.suggested.toLowerCase()}.`));

// 4. Industry
body.push(h1("4. Industry Analysis"));
body.push(h2("4.1 Industry overview"));
for (const key of ["Industry", "Market", "Customers", "Key trends", "Key success factors"]) {
  body.push(para([label(`${key}: `), run(sentence(data.overview[key]))]));
}
body.push(h2("4.2 Porter's Five Forces"));
body.push(para(
  "Porter's Five Forces shows how strong the competitive pressure in an industry is. Each force was rated from " +
  "1 (weak) to 5 (strong).", { keepNext: true }));
body.push(table([0.3, 0.12, 0.13, 0.45], [
  ["Force", "Strength", "Level", "Why"],
  ...data.forces.map((f) => [[run(f.force, { bold: true })], `${f.rating} of 5`, [priority(f.level)], sentence(f.why)]),
], { centre: [1, 2] }));
body.push(gap());
body.push(para(
  `On average the five forces score ${one(data.forcesAverage)} out of 5, which is ${data.forcesLevel.toLowerCase()}: ` +
  `${lc(data.forcesVerdict).replace(": ", ", so ")}. The strongest force is ${data.strongestForce.toLowerCase()} and the weakest is the ` +
  `${data.weakestForce.toLowerCase()}; ${data.forcesHigh} forces are rated high. PZ must keep its costs low and its ` +
  "brands strong to stay profitable."));
body.push(h2("4.3 Main competitors"));
body.push(table([0.24, 0.26, 0.2, 0.3], [
  ["Competitor", "Key brands", "Competes with PZ in", "Position"],
  ...data.competitors.map((m) => [[run(m.name, { bold: true })], m.brands, m.competes, m.position]),
]));
body.push(gap());
body.push(para(
  "Unilever's exit from home care and soaps and Procter & Gamble's move to imports leave customers that PZ can " +
  "win. At the same time, Reckitt is strong in hygiene products, Hayat Kimya and local brands compete hard on price, " +
  "and in electricals PZ faces strong international brands and cheaper imports."));

// 5. Recommendations
body.push(h1("5. Recommendations"));
body.push(para("Based on this analysis, PZ Nigeria should:"));
data.recommendations.forEach((r) => body.push(numbered([run(`${r.title}. `, { bold: true, color: NAVY }), run(sentence(r.why))])));

// 6. Conclusion
body.push(h1("6. Conclusion"));
body.push(para(
  `PZ Nigeria is strong inside, with well-known brands, a long history in Nigeria and a wide distribution network ` +
  `(IFE ${two(data.ifeTotal)}). Its environment, however, is hard: ${top.factor.toLowerCase()} factors matter most ` +
  `(average ${one(top.average)} of 25), led by ${lc(topIssue.issue)}, and the industry is highly competitive ` +
  `(Five Forces average ${one(data.forcesAverage)} of 5). With an EFE of ${two(data.efeTotal)}, PZ is not yet making ` +
  `the most of its opportunities. The best strategy is to ${pos.strategy.toLowerCase()}, through ` +
  `${pos.suggested.toLowerCase()}, supported by the five recommendations above.`));
body.push(para([run(
  "Scores, ratings and weights: PZ_Nigeria_Analysis.xlsx. The ratings are judgements based on the company " +
  "information and public news up to 2025.", { italics: true, size: 18, color: "595959" })], { spacing: { before: 240 } }));

// ------------------------------------------------------------------ document
const doc = new Document({
  creator: "Marketing Department",
  lastModifiedBy: "Marketing Department",
  title: "PZ Nigeria Limited: PESTLE, SWOT and Industry Analysis",
  subject: "Written analysis of PZ Nigeria Limited",
  styles: {
    default: {
      document: { run: { font: "Calibri", size: 22 }, paragraph: { spacing: { after: 160, line: 259 } } },
    },
    paragraphStyles: [
      { id: "Title", name: "Title", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { font: "Calibri Light", size: 56, color: NAVY },
        paragraph: { spacing: { after: 0, line: 240 } } },
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { font: "Calibri Light", size: 32, color: NAVY },
        paragraph: { spacing: { before: 360, after: 120 }, keepNext: true, keepLines: true, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { font: "Calibri Light", size: 26, color: NAVY },
        paragraph: { spacing: { before: 200, after: 80 }, keepNext: true, keepLines: true, outlineLevel: 1 } },
    ],
  },
  numbering: {
    config: [
      { reference: "bullets", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT,
        style: { paragraph: { indent: { left: 360, hanging: 360 } } } }] },
      { reference: "numbers", levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT,
        style: { paragraph: { indent: { left: 360, hanging: 360 } }, run: { bold: true, color: NAVY } } }] },
    ],
  },
  sections: [{
    properties: { page: { size: { width: PAGE_W, height: 16838 }, margin: { top: MARGIN, bottom: MARGIN, left: MARGIN, right: MARGIN } } },
    footers: {
      default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [
        new TextRun({ children: [PageNumber.CURRENT], size: 18, color: "595959" })] })] }),
    },
    children: body,
  }],
});

Packer.toBuffer(doc).then((buf) => {
  fs.writeFileSync(outPath, buf);
  console.log(`wrote ${outPath}`);
});
