// Build the PZ Nigeria PESTLE, SWOT and industry analysis deck.
//
// Usage: node build_deck.js slide_data.json out.pptx
//
// Every rating, score and conclusion comes from slide_data.json, which export_slide_data.py
// reads out of the finished workbook, so the slides always match the Excel file.
//
// Every object gets a name and an animation step. The plan is written next to the deck
// (out.anim.json); finish_deck.py turns it into entrance animations that play by themselves:
// step 1 appears after the slide transition, and each later step after the one before it.
//
// Look (the same as the budget deck): one font (Arial), black text with dark-blue titles,
// white slides in a thin frame, one light box colour. Charts are black, grey and white only.
// Shapes are only rectangles, lines and text boxes.
const fs = require("fs");
const pptxgen = require("pptxgenjs");

const [dataPath, outPath] = process.argv.slice(2);
const data = JSON.parse(fs.readFileSync(dataPath, "utf8"));

// ---------------------------------------------------------------- design tokens
const FONT = "Arial";
const TITLE = "1F3864";    // titles and rules: the only coloured text
const TEXT = "000000";     // all other text
const BOX = "DEEBF7";      // the one box fill
const FRAME = "8FAADC";    // slide frame
const BAR_GRAY = "595959";
const W = 13.333;
const H = 7.5;

const one = (x) => x.toFixed(1);
// Lower-case the first letter for use mid-sentence, but leave acronyms (FX, NAFDAC) alone.
const lc = (t) => (/^[A-Z][a-z]/.test(t) ? t.charAt(0).toLowerCase() + t.slice(1) : t);
const two = (x) => x.toFixed(2);
const byFactor = Object.fromEntries(data.pestleSummary.map((f) => [f.factor, f]));
const issuesOf = (factor) => data.pestle.filter((p) => p.factor === factor);
const top = [...data.pestleSummary].sort((a, b) => b.average - a.average)[0];
const topIssue = [...data.pestle].sort((a, b) => b.score - a.score)[0];
const highCount = data.pestle.filter((p) => p.priority === "High").length;
const threatCount = data.pestle.filter((p) => p.type === "Threat").length;
const oppCount = data.pestle.filter((p) => p.type === "Opportunity").length;
const ieCell = data.position.ieCell;   // I to IX
const force = (name) => data.forces.find((f) => f.force === name);

// ---------------------------------------------------------------- animation plan
// animPlan[slideNumber] = [{ name, step, effect }]; effect is "fade", "wipe-left" or "wipe-up".
const animPlan = {};
let slideNo = 0;
function anim(label, step, effect = "fade") {
  const list = animPlan[slideNo] || (animPlan[slideNo] = []);
  let name = label;
  for (let k = 2; list.some((e) => e.name === name); k++) name = `${label} ${k}`;
  list.push({ name, step, effect });
  return name;
}

function text(slide, value, opts, name, step, effect) {
  slide.addText(value, { fontFace: FONT, color: TEXT, margin: 0, isTextBox: true, ...opts, objectName: anim(name, step, effect) });
}

function rule(slide, pres, x, y, w, name, step, effect = "wipe-left") {
  slide.addShape(pres.shapes.LINE, { x, y, w, h: 0, line: { color: TITLE, width: 1.5 }, objectName: anim(name, step, effect) });
}

function box(slide, pres, x, y, w, h, name, step) {
  slide.addShape(pres.shapes.RECTANGLE, { x, y, w, h, fill: { color: BOX }, line: { color: BOX, width: 0 }, objectName: anim(name, step) });
}

// Centred title over a rule, the layout used on every content slide. Title and rule come in
// first, the subtitle next; returns the first free step.
function title(slide, pres, value, sub) {
  text(slide, value, { x: 0.8, y: 0.5, w: W - 1.6, h: 0.8, fontSize: 36, bold: true, color: TITLE, align: "center", valign: "middle" }, "Title", 1);
  rule(slide, pres, 1.0, 1.42, W - 2.0, "Title Rule", 1);
  if (!sub) return 2;
  text(slide, sub, { x: 0.8, y: 1.55, w: W - 1.6, h: 0.42, fontSize: 18, align: "center", valign: "middle" }, "Subtitle", 2);
  return 3;
}

// A box with a bold heading and bulleted paragraphs. items: [[run, ...], ...] where each run
// is { text, bold?, br? } (br starts a new line inside the same bullet).
function card(slide, pres, { x, y, w, h, heading, sub, items, fontSize = 15, space = 8, name, step, bullets = true }) {
  box(slide, pres, x, y, w, h, `${name} Box`, step);
  text(slide, heading, { x: x + 0.25, y: y + 0.15, w: w - 0.5, h: 0.45, fontSize: 20, bold: true, valign: "middle" }, `${name} Heading`, step);
  const top = sub ? 1.05 : 0.7;
  if (sub) text(slide, sub, { x: x + 0.25, y: y + 0.6, w: w - 0.5, h: 0.35, fontSize: 15, valign: "middle" }, `${name} Subheading`, step);
  const runs = [];
  items.forEach((item, i) => {
    item.forEach((run, k) => {
      const o = { bold: !!run.bold };
      if (k === 0 && bullets) o.bullet = { indent: 18 };
      if (run.br) o.softBreakBefore = true;
      if (k === item.length - 1 && i < items.length - 1) o.breakLine = true;
      runs.push({ text: run.text, options: o });
    });
  });
  text(slide, runs, { x: x + 0.25, y: y + top, w: w - 0.5, h: h - top - 0.15, fontSize, valign: "top", paraSpaceAfter: space }, `${name} Text`, step);
}

// Grey bar chart; horizontal bars read top to bottom in the table's order.
function greyBars(slide, pres, { x, y, w, h, labels, values, max, major, fmt, horizontal, name, step, catSize = 14 }) {
  slide.addChart(pres.charts.BAR, [{ name, labels, values }], {
    x, y, w, h,
    barDir: horizontal ? "bar" : "col", barGapWidthPct: 50,
    chartColors: [BAR_GRAY],
    catAxisOrientation: horizontal ? "maxMin" : "minMax",
    catAxisLabelColor: TEXT, catAxisLabelFontFace: FONT, catAxisLabelFontSize: catSize,
    catAxisLineShow: true, catAxisLineColor: "A6A6A6", catAxisMajorTickMark: "none",
    valAxisHidden: !!horizontal, valAxisMinVal: 0, valAxisMaxVal: max, valAxisMajorUnit: major,
    valAxisLabelColor: TEXT, valAxisLabelFontFace: FONT, valAxisLabelFontSize: 12, valAxisLabelFormatCode: fmt,
    valAxisLineShow: false,
    valGridLine: horizontal ? { style: "none" } : { color: "D9D9D9", size: 0.75 }, catGridLine: { style: "none" },
    showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: fmt,
    dataLabelColor: TEXT, dataLabelFontFace: FONT, dataLabelFontSize: 14, dataLabelFontBold: true,
    showLegend: false, showTitle: false,
    objectName: anim(name, step, horizontal ? "wipe-left" : "wipe-up"),
  });
}

async function main() {
  const pres = new pptxgen();
  pres.layout = "LAYOUT_WIDE";
  pres.theme = { headFontFace: FONT, bodyFontFace: FONT };
  pres.title = "PZ Nigeria Limited: PESTLE, SWOT and Industry Analysis";
  pres.subject = "PESTLE, SWOT and industry analysis of PZ Nigeria Limited";

  pres.defineSlideMaster({
    title: "FRAMED",
    background: { color: "FFFFFF" },
    objects: [{ rect: { x: 0.3, y: 0.3, w: W - 0.6, h: H - 0.6, fill: { color: "FFFFFF", transparency: 100 }, line: { color: FRAME, width: 1 } } }],
  });
  const newSlide = () => { slideNo += 1; return pres.addSlide({ masterName: "FRAMED" }); };

  // ============================================================ 1. Title
  {
    const s = newSlide();
    text(s, "PZ NIGERIA LIMITED", { x: 0.8, y: 1.9, w: W - 1.6, h: 0.95, fontSize: 44, bold: true, color: TITLE, align: "center", valign: "middle" }, "Title", 1);
    rule(s, pres, 2.5, 3.0, W - 5.0, "Title Rule", 1);
    text(s, "PESTLE, SWOT and Industry Analysis", { x: 0.8, y: 3.15, w: W - 1.6, h: 0.7, fontSize: 32, align: "center", valign: "middle" }, "Subtitle", 2);
    text(s, "Marketing Department  ·  Ilupeju, Lagos", { x: 0.8, y: 4.3, w: W - 1.6, h: 0.6, fontSize: 22, bold: true, align: "center", valign: "middle" }, "Department", 3);
    text(s, "Scores and ratings: PZ_Nigeria_Analysis.xlsx", {
      x: 0.8, y: 6.3, w: W - 1.6, h: 0.4, fontSize: 14, align: "center", valign: "middle",
    }, "Source", 4);
    s.addNotes(
      "Good day. This presentation analyses PZ Nigeria Limited, the company behind Imperial Leather, Premier Cool, Joy and Morning Fresh. " +
      "I will look at its business environment with a PESTLE analysis, at the company itself with a SWOT analysis, and at its industry with Porter's Five Forces. " +
      "All the scores were calculated in Microsoft Excel, in the workbook PZ_Nigeria_Analysis.xlsx."
    );
  }

  // ============================================================ 2. Company overview
  {
    const s = newSlide();
    let step = title(s, pres, "Company Overview", "Who PZ Nigeria is, what it sells and how it is organised");
    const gap = 0.3, x0 = 0.9, cw = (W - 1.8 - gap * 2) / 3, y = 2.2, h = 4.6;
    const c = data.company;
    card(s, pres, {
      x: x0, y, w: cw, h, heading: "Business and Brands", name: "Brands", step,
      items: [
        [{ text: "Family Care (consumer)", bold: true }, { text: c["Consumer business (Family Care)"], br: true }],
        [{ text: "Electrical", bold: true }, { text: c["Electrical business"], br: true }],
      ],
      fontSize: 18, space: 16,
    });
    step += 1;
    card(s, pres, {
      x: x0 + cw + gap, y, w: cw, h, heading: "Leadership", name: "Leadership", step,
      items: [
        [{ text: c["Managing Director"], bold: true }, { text: "Managing Director", br: true }],
        [{ text: c["Chief Financial Officer"], bold: true }, { text: "Chief Financial Officer", br: true }],
        [{ text: "Owner", bold: true }, { text: "PZ Cussons group (United Kingdom)", br: true }],
      ],
      fontSize: 18, space: 16,
    });
    step += 1;
    card(s, pres, {
      x: x0 + (cw + gap) * 2, y, w: cw, h, heading: "Structure", name: "Structure", step,
      items: [
        [{ text: "Managing Director", bold: true }, { text: "with the CFO and HR Director", br: true }],
        [{ text: "Category Managers", bold: true }],
        [{ text: "Brand Managers", bold: true }, { text: "one manager for each brand", br: true }],
        [{ text: "Assistant Brand Managers", bold: true }],
      ],
      fontSize: 18, space: 12,
    });
    s.addNotes(
      "PZ Nigeria has two businesses. Family Care makes Imperial Leather, Premier Cool, Joy and Morning Fresh; the Electrical business sells air conditioners, fridges, freezers and washing machines. " +
      "The company is led by Mr Oghale Ogueni, the Managing Director, and Mr Oladare Oresukan, the Chief Financial Officer, and it is part of the UK-based PZ Cussons group. " +
      "It uses a product and brand structure: the Managing Director, category managers, then a brand manager in charge of each brand, supported by assistant brand managers and shared departments."
    );
  }

  // ============================================================ 3-4. PESTLE
  const pestleSlide = (factors, part) => {
    const s = newSlide();
    let step = title(s, pres, `PESTLE Analysis (${part} of 2)`, `${factors.join(", ").replace(/, ([^,]*)$/, " and $1")} factors, with each issue's score (Impact × Likelihood, out of 25)`);
    const gap = 0.3, x0 = 0.9, cw = (W - 1.8 - gap * 2) / 3, y = 2.2, h = 4.7;
    factors.forEach((factor, i) => {
      const f = byFactor[factor];
      card(s, pres, {
        x: x0 + i * (cw + gap), y, w: cw, h, name: factor, step,
        heading: factor, sub: `Average score: ${one(f.average)} of 25`,
        items: issuesOf(factor).map((p) => [
          { text: p.issue, bold: true },
          { text: p.effect, br: true },
          { text: `Score ${p.score}: ${p.priority} (${p.type.toLowerCase()})`, br: true },
        ]),
        fontSize: 14, space: 10,
      });
      step += 1;
    });
    const say = factors.map((factor) => {
      const list = issuesOf(factor);
      const best = [...list].sort((a, b) => b.score - a.score)[0];
      return `${factor} factors average ${one(byFactor[factor].average)} out of 25; the biggest issue is ${lc(best.issue)}, which scores ${best.score}: ${lc(best.effect)}.`;
    });
    s.addNotes(
      "Each issue is rated for impact and likelihood from 1 to 5; the score is impact times likelihood, so the highest possible score is 25. " +
      "16 or more is high priority. " + say.join(" ")
    );
  };
  pestleSlide(["Political", "Economic", "Social"], 1);
  pestleSlide(["Technological", "Legal", "Environmental"], 2);

  // ============================================================ 5. PESTLE scores
  {
    const s = newSlide();
    const step = title(s, pres, "PESTLE Scores", "Average score of each factor (Impact × Likelihood, out of 25), from the Excel workbook");
    greyBars(s, pres, {
      x: 0.8, y: 2.15, w: 7.2, h: 4.8, horizontal: true, name: "PESTLE Chart", step,
      labels: data.pestleSummary.map((f) => f.factor), values: data.pestleSummary.map((f) => Number(one(f.average))),
      max: 25, major: 5, fmt: "0.0",
    });
    card(s, pres, {
      x: 8.35, y: 2.2, w: 4.2, h: 4.7, heading: "Key Findings", name: "Findings", step: step + 1,
      items: [
        [{ text: "Most important: " }, { text: `${top.factor} (${one(top.average)})`, bold: true }],
        [{ text: "Biggest issue: " }, { text: `${topIssue.issue} (${topIssue.score} of 25)`, bold: true }],
        [{ text: "High priority: " }, { text: `${highCount} of ${data.pestle.length} issues`, bold: true }],
        [{ text: `${threatCount} threats and ${oppCount} opportunities`, bold: true }],
      ],
      fontSize: 18, space: 16,
    });
    const low = [...data.pestleSummary].sort((a, b) => a.average - b.average)[0];
    s.addNotes(
      `The chart shows each factor's average score, calculated in Excel with AVERAGEIF. ${top.factor} factors matter most, with an average of ${one(top.average)} out of 25, ` +
      `and the single biggest issue is ${lc(topIssue.issue)}, which scores the maximum of ${topIssue.score}. ` +
      `${low.factor} factors matter least, at ${one(low.average)}. Overall ${highCount} of the ${data.pestle.length} issues are high priority, ` +
      `and there are ${threatCount} threats against ${oppCount} opportunities, so the environment is difficult.`
    );
  }

  // ============================================================ 6. SWOT
  {
    const s = newSlide();
    let step = title(s, pres, "SWOT Analysis");
    const gap = 0.25, x0 = 0.9, cw = (W - 1.8 - gap) / 2, ch = 2.5, y0 = 1.72;
    const quads = [
      ["Strengths (internal)", data.swot.strengths],
      ["Weaknesses (internal)", data.swot.weaknesses],
      ["Opportunities (external)", data.swot.opportunities],
      ["Threats (external)", data.swot.threats],
    ];
    quads.forEach(([heading, points], i) => {
      const x = x0 + (i % 2) * (cw + gap), y = y0 + Math.floor(i / 2) * (ch + 0.2);
      const name = heading.split(" ")[0];
      box(s, pres, x, y, cw, ch, `${name} Box`, step);
      text(s, heading, { x: x + 0.25, y: y + 0.1, w: cw - 0.5, h: 0.4, fontSize: 18, bold: true, valign: "middle" }, `${name} Heading`, step);
      text(s, points.map((p, k) => ({ text: p, options: { bullet: { indent: 16 }, breakLine: k < points.length - 1 } })), {
        x: x + 0.25, y: y + 0.55, w: cw - 0.45, h: ch - 0.62, fontSize: 14, valign: "top", paraSpaceAfter: 4,
      }, `${name} Points`, step);
      step += 1;
    });
    s.addNotes(
      `PZ's main strengths are its well-known brands, more than a century in Nigeria and a wide distribution network. ` +
      `Its weaknesses are slow decisions, because approvals can wait for the UK owner and there are many management levels, and its dependence on imported raw materials when the naira is weak. ` +
      `The opportunities come from Nigeria's large young population, digital selling, smaller packs and the customers left behind by Unilever and P&G. ` +
      `The threats are the weak naira, high inflation, strong competition, fake products, high energy costs and policy changes.`
    );
  }

  // ============================================================ 7. SWOT scoring
  {
    const s = newSlide();
    const step = title(s, pres, "SWOT Scoring (IFE and EFE)", "Each SWOT point weighted by importance and rated 1 to 4 in Excel; 2.50 is average");
    const p = data.position;
    greyBars(s, pres, {
      x: 0.8, y: 2.15, w: 6.4, h: 4.8, horizontal: false, name: "SWOT Chart", step,
      labels: ["Strengths", "Weaknesses", "Opportunities", "Threats"],
      values: [p.strengths, p.weaknesses, p.opportunities, p.threats].map((v) => Number(two(v))),
      max: 2.5, major: 0.5, fmt: "0.00", catSize: 14,
    });
    const stats = [
      { y: 2.2, name: "IFE", value: two(data.ifeTotal), label: "IFE: internal factors", result: data.ifeResult },
      { y: 3.85, name: "EFE", value: two(data.efeTotal), label: "EFE: external factors", result: data.efeResult },
    ];
    let k = step + 1;
    for (const c of stats) {
      box(s, pres, 7.55, c.y, 5.0, 1.45, `${c.name} Box`, k);
      text(s, c.value, { x: 7.7, y: c.y + 0.12, w: 1.6, h: 1.2, fontSize: 40, bold: true, align: "center", valign: "middle" }, `${c.name} Value`, k);
      text(s, [
        { text: c.label, options: { bold: true, breakLine: true } },
        { text: c.result },
      ], { x: 9.45, y: c.y + 0.12, w: 2.95, h: 1.2, fontSize: 15, valign: "middle" }, `${c.name} Label`, k);
      k += 1;
    }
    box(s, pres, 7.55, 5.5, 5.0, 1.4, "Strategy Box", k);
    text(s, [
      { text: `IE matrix: cell ${ieCell}`, options: { bold: true, breakLine: true } },
      { text: `${p.strategy}: `, options: { bold: true } },
      { text: p.suggested.charAt(0).toLowerCase() + p.suggested.slice(1) },
    ], { x: 7.8, y: 5.6, w: 4.5, h: 1.2, fontSize: 15, valign: "middle" }, "Strategy", k);
    s.addNotes(
      `In Excel each SWOT point has a weight for how important it is and a rating from 1 to 4; weight times rating gives the weighted score. ` +
      `The internal total, IFE, is ${two(data.ifeTotal)}: above the average of 2.50, because strengths (${two(p.strengths)}) outweigh weaknesses (${two(p.weaknesses)}). ` +
      `The external total, EFE, is ${two(data.efeTotal)}: below average, so PZ is not yet making the most of its opportunities or defending well enough against its threats. ` +
      `Together they place PZ in cell ${ieCell} of the internal-external matrix, which means ${p.strategy.toLowerCase()}: ${p.suggested.toLowerCase()}.`
    );
  }

  // ============================================================ 8. Industry overview
  {
    const s = newSlide();
    let step = title(s, pres, "Industry Overview", "Nigerian fast-moving consumer goods (FMCG) and consumer electricals");
    const o = data.overview;
    const gap = 0.3, x0 = 0.9, cw = (W - 1.8 - gap) / 2, y = 2.2, h = 4.7;
    card(s, pres, {
      x: x0, y, w: cw, h, heading: "The Industry", name: "Industry", step,
      items: ["Industry", "Market", "Customers"].map((k) => [{ text: `${k}: `, bold: true }, { text: o[k] }]),
      fontSize: 18, space: 16,
    });
    card(s, pres, {
      x: x0 + cw + gap, y, w: cw, h, heading: "Trends and Success Factors", name: "Trends", step: step + 1,
      items: ["Key trends", "Key success factors"].map((k) => [{ text: `${k}: `, bold: true }, { text: o[k] }]),
      fontSize: 18, space: 16,
    });
    s.addNotes(
      "PZ competes in fast-moving consumer goods, mainly soaps and dishwashing liquid, and in consumer electricals. " +
      "Nigeria has over 200 million people, most of them young, so it is one of Africa's largest consumer markets. " +
      "But prices are rising with inflation, shoppers are moving to smaller packs and cheaper brands, and some multinationals have cut local production. " +
      "To succeed, a company needs strong brands, low costs, wide distribution, local raw materials and affordable pack sizes."
    );
  }

  // ============================================================ 9. Competitors
  {
    const s = newSlide();
    const step = title(s, pres, "Main Competitors", "Who PZ competes with, and where they stand");
    const head = ["Competitor", "Key brands", "Competes with PZ in", "Position"].map((t) => ({
      text: t, options: { bold: true, fill: { color: BOX } },
    }));
    const rows = data.competitors.map((c) => [
      { text: c.name, options: { bold: true } }, { text: c.brands }, { text: c.competes }, { text: c.position },
    ]);
    s.addTable([head, ...rows], {
      x: 0.9, y: 2.2, w: W - 1.8, colW: [2.6, 3.0, 2.3, W - 1.8 - 7.9],
      fontFace: FONT, fontSize: 15, color: TEXT, valign: "middle",
      border: { type: "solid", pt: 0.75, color: "BFBFBF" }, margin: [4, 8, 4, 8],
      rowH: [0.45, ...rows.map(() => 0.7)],
      objectName: anim("Competitors Table", step, "wipe-up"),
    });
    s.addNotes(
      "These are PZ's main competitors. Unilever left home care and soaps in 2023, and Procter and Gamble stopped making products in Nigeria, so both now leave space PZ can fill. " +
      "Reckitt is strong in hygiene with Dettol and Harpic, Hayat Kimya makes low-priced products locally, and many local brands win on price in open markets. " +
      "In electricals, PZ faces LG, Samsung, Hisense and Scanfrost, plus many cheaper imports."
    );
  }

  // ============================================================ 10. Five forces diagram
  {
    const s = newSlide();
    title(s, pres, "Porter's Five Forces");
    const place = {
      "Threat of new entrants": { x: 4.72, y: 1.68, w: 3.9, h: 1.47 },
      "Bargaining power of suppliers": { x: 0.8, y: 3.3, w: 3.5, h: 2.1 },
      "Competitive rivalry": { x: 4.72, y: 3.55, w: 3.9, h: 1.6 },
      "Bargaining power of buyers": { x: W - 0.8 - 3.5, y: 3.3, w: 3.5, h: 2.1 },
      "Threat of substitutes": { x: 4.72, y: 5.5, w: 3.9, h: 1.47 },
    };
    const order = ["Competitive rivalry", "Threat of new entrants", "Bargaining power of suppliers", "Bargaining power of buyers", "Threat of substitutes"];
    const line = (name, x, y, w, h, begin, end, step) => s.addShape(pres.shapes.LINE, {
      x, y, w, h, line: { color: TEXT, width: 1.5, beginArrowType: begin, endArrowType: end }, objectName: anim(name, step),
    });
    order.forEach((name, i) => {
      const f = force(name), p = place[name], step = 2 + i;
      const centre = name === "Competitive rivalry";
      s.addShape(pres.shapes.RECTANGLE, {
        x: p.x, y: p.y, w: p.w, h: p.h, fill: { color: centre ? "FFFFFF" : BOX },
        line: { color: centre ? TITLE : BOX, width: centre ? 2 : 0 }, objectName: anim(`${name} Box`, step),
      });
      text(s, [
        { text: name, options: { bold: true, fontSize: 18, breakLine: true } },
        { text: `${f.level}: ${f.rating} of 5`, options: { bold: true, fontSize: 15, breakLine: true } },
        { text: f.why, options: { fontSize: 14 } },
      ], { x: p.x + 0.15, y: p.y + 0.08, w: p.w - 0.3, h: p.h - 0.16, align: "center", valign: "middle", paraSpaceAfter: 3 }, `${name} Text`, step);
      // Arrows point at the rivalry box in the middle.
      if (name === "Threat of new entrants") line("Arrow Entrants", 6.67, 3.15, 0, 0.4, null, "triangle", step);
      if (name === "Threat of substitutes") line("Arrow Substitutes", 6.67, 5.15, 0, 0.35, "triangle", null, step);
      if (name === "Bargaining power of suppliers") line("Arrow Suppliers", 4.3, 4.35, 0.42, 0, null, "triangle", step);
      if (name === "Bargaining power of buyers") line("Arrow Buyers", 8.62, 4.35, W - 0.8 - 3.5 - 8.62, 0, "triangle", null, step);
    });
    s.addNotes(
      data.forces.map((f) => `${f.force} is ${f.level.toLowerCase()}, rated ${f.rating} out of 5: ${lc(f.why)}.`).join(" ")
    );
  }

  // ============================================================ 11. Five forces ratings
  {
    const s = newSlide();
    const step = title(s, pres, "Five Forces Ratings", "Strength of each force (1 = weak, 5 = strong), from the Excel workbook");
    greyBars(s, pres, {
      x: 0.8, y: 2.15, w: 7.4, h: 4.8, horizontal: true, name: "Forces Chart", step, catSize: 14,
      labels: data.forces.map((f) => f.force), values: data.forces.map((f) => f.rating),
      max: 5, major: 1, fmt: "0",
    });
    box(s, pres, 8.55, 2.2, 4.0, 1.9, "Average Box", step + 1);
    text(s, one(data.forcesAverage), { x: 8.55, y: 2.3, w: 4.0, h: 0.85, fontSize: 44, bold: true, align: "center", valign: "middle" }, "Average Value", step + 1);
    text(s, "Average strength of the five forces (AVERAGE)", { x: 8.75, y: 3.15, w: 3.6, h: 0.8, fontSize: 15, align: "center", valign: "middle" }, "Average Label", step + 1);
    card(s, pres, {
      x: 8.55, y: 4.3, w: 4.0, h: 2.6, heading: `${data.forcesLevel} Pressure`, name: "Verdict", step: step + 2,
      items: [
        [{ text: "Strongest: " }, { text: data.strongestForce, bold: true }],
        [{ text: "Weakest: " }, { text: data.weakestForce, bold: true }],
        [{ text: "Rated high: " }, { text: `${data.forcesHigh} forces`, bold: true }],
      ],
      fontSize: 17, space: 10,
    });
    s.addNotes(
      `On average the five forces score ${one(data.forcesAverage)} out of 5, calculated in Excel with AVERAGE. ${data.forcesVerdict}. ` +
      `The strongest force is ${data.strongestForce.toLowerCase()}; the weakest is the ${data.weakestForce.toLowerCase()}, because it costs a lot to build factories, brands and distribution. ` +
      `${data.forcesHigh} forces are rated high, so PZ must keep costs low and brands strong to stay profitable.`
    );
  }

  // ============================================================ 12. Recommendations
  {
    const s = newSlide();
    let step = title(s, pres, "Recommendations");
    const y0 = 1.72, rh = 0.9, gap = 0.14;
    data.recommendations.forEach((r, i) => {
      const y = y0 + i * (rh + gap);
      const name = `Recommendation ${i + 1}`;
      box(s, pres, 0.9, y, W - 1.8, rh, `${name} Box`, step);
      text(s, String(i + 1), { x: 1.05, y, w: 0.6, h: rh, fontSize: 30, bold: true, color: TITLE, align: "center", valign: "middle" }, `${name} Number`, step);
      text(s, [
        { text: r.title, options: { bold: true, fontSize: 18, breakLine: true } },
        { text: r.why, options: { fontSize: 16 } },
      ], { x: 1.85, y: y + 0.05, w: W - 3.0, h: rh - 0.1, valign: "middle" }, `${name} Text`, step);
      step += 1;
    });
    s.addNotes(
      "Based on the analysis, I recommend five actions. " +
      data.recommendations.map((r, i) => `${i + 1}: ${lc(r.title)}. ${r.why}.`).join(" ")
    );
  }

  // ============================================================ 13. Conclusion
  {
    const s = newSlide();
    let step = title(s, pres, "Conclusion");
    const cards = [
      { head: "PESTLE", value: `${top.factor}`, body: `The most important factor (average ${one(top.average)} of 25). Biggest issue: ${lc(topIssue.issue)}.` },
      { head: "SWOT", value: `${two(data.ifeTotal)} / ${two(data.efeTotal)}`, body: `Strong inside (IFE), but a weaker response to the outside (EFE). Strategy: ${data.position.strategy.toLowerCase()}.` },
      { head: "Industry", value: `${one(data.forcesAverage)} of 5`, body: `${data.forcesLevel.charAt(0) + data.forcesLevel.slice(1).toLowerCase()} competitive pressure; ${data.strongestForce.toLowerCase()} is the strongest force.` },
    ];
    const gap = 0.3, x0 = 0.9, cw = (W - 1.8 - gap * 2) / 3;
    cards.forEach((c, i) => {
      const x = x0 + i * (cw + gap), name = `${c.head} Card`;
      box(s, pres, x, 1.8, cw, 3.1, `${name} Box`, step);
      text(s, c.head, { x: x + 0.2, y: 1.92, w: cw - 0.4, h: 0.45, fontSize: 20, bold: true, align: "center", valign: "middle" }, `${name} Heading`, step);
      text(s, c.value, { x: x + 0.2, y: 2.42, w: cw - 0.4, h: 0.75, fontSize: 32, bold: true, align: "center", valign: "middle" }, `${name} Value`, step);
      text(s, c.body, { x: x + 0.25, y: 3.25, w: cw - 0.5, h: 1.55, fontSize: 17, align: "center", valign: "top" }, `${name} Text`, step);
      step += 1;
    });
    rule(s, pres, 3.2, 5.4, W - 6.4, "Closing Rule", step);
    text(s, "Thank You. Questions?", {
      x: 0.8, y: 5.6, w: W - 1.6, h: 0.7, fontSize: 32, bold: true, color: TITLE, align: "center", valign: "middle",
    }, "Thank You", step);
    s.addNotes(
      `To conclude: PZ Nigeria is strong inside, with well-known brands and a wide distribution network (IFE ${two(data.ifeTotal)}), ` +
      `but its environment is hard. ${top.factor} factors, especially ${lc(topIssue.issue)}, matter most, and the industry is highly competitive (five forces average ${one(data.forcesAverage)} out of 5). ` +
      `The best strategy is to ${data.position.strategy.toLowerCase()}, through ${data.position.suggested.toLowerCase()}. Thank you; I am happy to take questions.`
    );
  }

  await pres.writeFile({ fileName: outPath });
  fs.writeFileSync(outPath.replace(/\.pptx$/, ".anim.json"), JSON.stringify(animPlan, null, 2));
  console.log("wrote " + outPath);
}

main().catch((e) => { console.error(e); process.exit(1); });
