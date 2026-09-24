// Build the Marketing Department Budget deck (before the Excel table is embedded).
//
// Usage: node build_deck.js slide_data.json table_preview.png table_size.json out.pptx
//
// Every figure comes from slide_data.json, which export_slide_data.py reads out of the
// finished workbook, so the slides always match the Excel file. Slide 7 gets a picture of
// the Excel budget table named "Excel Budget Table"; embed_excel_table.py swaps that
// picture for the real embedded Excel worksheet object.
//
// Look: one font (Arial, as in the Excel table), black text with dark-blue titles, white
// slides in a thin frame, one light box colour. Colour otherwise appears only in the charts,
// one colour per unit.
const fs = require("fs");
const pptxgen = require("pptxgenjs");

const [dataPath, previewPath, sizePath, outPath] = process.argv.slice(2);
const data = JSON.parse(fs.readFileSync(dataPath, "utf8"));
const tableSize = JSON.parse(fs.readFileSync(sizePath, "utf8"));

// ---------------------------------------------------------------- design tokens
const FONT = "Arial";
const TITLE = "1F3864";    // titles and rules: the only coloured text
const TEXT = "000000";     // all other text
const BOX = "DEEBF7";      // the one box fill
const FRAME = "8FAADC";    // slide frame
const W = 13.333;
const H = 7.5;

// One colour per unit, used only for chart marks (validated for colour-blind separation).
const UNIT_COLOR = { "Advertising": "4472C4", "Marketing": "C55A11", "Public Relations": "7030A0", "e-Business": "548235" };

const money = (n) => "$" + Math.round(n).toLocaleString("en-US");
const pct = (x) => (x * 100).toFixed(1) + "%";
const units = data.units;
const RANK_WORDS = ["the largest", "the second largest", "the third largest", "the smallest"];
const [ADV, MKT, PR, EBIZ] = units;
const colorOf = (u) => UNIT_COLOR[u.name];

function text(slide, value, opts) {
  slide.addText(value, { fontFace: FONT, color: TEXT, margin: 0, isTextBox: true, ...opts });
}

function rule(slide, pres, x, y, w) {
  slide.addShape(pres.shapes.LINE, { x, y, w, h: 0, line: { color: TITLE, width: 1.5 } });
}

// Centred title over a rule, the layout used on every content slide.
function title(slide, pres, value, sub) {
  text(slide, value, { x: 0.8, y: 0.5, w: W - 1.6, h: 0.8, fontSize: 36, bold: true, color: TITLE, align: "center", valign: "middle" });
  rule(slide, pres, 1.0, 1.42, W - 2.0);
  if (sub) {
    text(slide, sub, { x: 0.8, y: 1.55, w: W - 1.6, h: 0.42, fontSize: 18, align: "center", valign: "middle" });
  }
}

function box(slide, pres, x, y, w, h) {
  slide.addShape(pres.shapes.RECTANGLE, { x, y, w, h, fill: { color: BOX }, line: { color: BOX, width: 0 } });
}

async function main() {
  const pres = new pptxgen();
  pres.layout = "LAYOUT_WIDE";
  pres.theme = { headFontFace: FONT, bodyFontFace: FONT };
  pres.title = `Marketing Department Budget ${data.year}`;
  pres.subject = "Budget for the Advertising, Marketing, Public Relations and e-Business units";

  pres.defineSlideMaster({
    title: "FRAMED",
    background: { color: "FFFFFF" },
    objects: [{ rect: { x: 0.3, y: 0.3, w: W - 0.6, h: H - 0.6, fill: { color: "FFFFFF", transparency: 100 }, line: { color: FRAME, width: 1 } } }],
  });
  const newSlide = () => pres.addSlide({ masterName: "FRAMED" });

  // ============================================================ 1. Title
  {
    const s = newSlide();
    text(s, "MARKETING DEPARTMENT", { x: 0.8, y: 1.9, w: W - 1.6, h: 0.95, fontSize: 44, bold: true, color: TITLE, align: "center", valign: "middle" });
    rule(s, pres, 2.5, 3.0, W - 5.0);
    text(s, `Annual Budget ${data.year}`, { x: 0.8, y: 3.15, w: W - 1.6, h: 0.7, fontSize: 32, align: "center", valign: "middle" });
    // One box, two paragraphs: if the sentence wraps, the unit names move down with it.
    text(s, [
      { text: "How the department's budget is planned and shared across its four units:", options: { breakLine: true } },
      { text: units.map((u) => u.name).join("   •   "), options: { bold: true } },
    ], { x: 1.0, y: 4.3, w: W - 2.0, h: 1.1, fontSize: 20, align: "center", valign: "top", paraSpaceAfter: 6 });
    text(s, "Amounts in US$  ·  Source: Marketing_Department_Budget.xlsx", {
      x: 0.8, y: 6.3, w: W - 1.6, h: 0.4, fontSize: 14, align: "center", valign: "middle",
    });
    s.addNotes(
      `Good day. This presentation covers the ${data.year} budget of the Marketing Department. ` +
      "The department has four units: Advertising (Ads), Marketing, Public Relations (PR) and e-Business. " +
      "The figures were prepared in Microsoft Excel, where SUM and AVERAGE formulas calculate the totals and averages."
    );
  }

  // ============================================================ 2. Budget at a glance
  {
    const s = newSlide();
    title(s, pres, "Budget at a Glance", `How the ${money(data.departmentTotal)} department budget is shared across the four units`);
    const stats = [
      { y: 2.2, value: money(data.departmentTotal), label: "Total department budget",
        formula: `Excel: =SUM(B${data.totalRow}:E${data.totalRow})` },
      { y: 4.55, value: money(data.averagePerUnit), label: "Average budget per unit",
        formula: `Excel: =AVERAGE(B${data.totalRow}:E${data.totalRow})` },
    ];
    for (const c of stats) {
      box(s, pres, 0.9, c.y, 4.3, 2.15);
      text(s, c.value, { x: 0.9, y: c.y + 0.22, w: 4.3, h: 0.8, fontSize: 40, bold: true, align: "center", valign: "middle" });
      text(s, c.label, { x: 0.9, y: c.y + 1.08, w: 4.3, h: 0.42, fontSize: 20, align: "center", valign: "middle" });
      text(s, c.formula, { x: 0.9, y: c.y + 1.52, w: 4.3, h: 0.38, fontSize: 16, align: "center", valign: "middle" });
    }

    const dx = 5.4, dy = 2.3, dd = 4.3;
    s.addChart(pres.charts.DOUGHNUT, [{
      name: "Share of total budget", labels: units.map((u) => u.name), values: units.map((u) => u.total),
    }], {
      x: dx, y: dy, w: dd, h: dd, holeSize: 55,
      chartColors: units.map(colorOf),
      dataBorder: { pt: 1.5, color: "FFFFFF" },
      showPercent: false, showValue: false, showLabel: false, showLegend: false, showTitle: false,
    });
    text(s, [
      { text: "Share of", options: { breakLine: true } },
      { text: "total budget" },
    ], { x: dx + dd / 2 - 1.0, y: dy + dd / 2 - 0.4, w: 2.0, h: 0.8, fontSize: 16, bold: true, align: "center", valign: "middle" });

    // Legend with the values: it is also how the doughnut's numbers are read.
    const lx = 9.9;
    units.forEach((u, i) => {
      const y = 2.45 + i * 1.05;
      s.addShape(pres.shapes.RECTANGLE, { x: lx, y: y + 0.07, w: 0.24, h: 0.24, fill: { color: colorOf(u) }, line: { color: colorOf(u), width: 0 } });
      text(s, [
        { text: u.name, options: { bold: true, breakLine: true } },
        { text: `${money(u.total)}  ·  ${pct(u.share)}` },
      ], { x: lx + 0.38, y, w: 2.45, h: 0.9, fontSize: 17, valign: "top" });
    });
    s.addNotes(
      `In total the department plans to spend ${money(data.departmentTotal)}. In Excel this is the SUM of the four unit budgets. ` +
      `The average budget per unit is ${money(data.averagePerUnit)}, calculated with the AVERAGE formula. ` +
      `Advertising takes the largest share (${pct(ADV.share)}), followed by Marketing (${pct(MKT.share)}), ` +
      `e-Business (${pct(EBIZ.share)}) and Public Relations (${pct(PR.share)}).`
    );
  }

  // ============================================================ 3-6. One slide per unit
  units.forEach((u) => {
    const s = newSlide();
    title(s, pres, u.title, u.covers);
    const top = u.items[0];

    box(s, pres, 0.9, 2.2, 4.4, 4.55);
    text(s, "Key Figures", { x: 1.15, y: 2.35, w: 3.9, h: 0.5, fontSize: 22, bold: true, valign: "middle" });
    const item = { bullet: { indent: 18 } };
    text(s, [
      { text: "Total budget: ", options: item },
      { text: money(u.total), options: { bold: true, breakLine: true } },
      { text: `Excel formula: =SUM(${u.column}5:${u.column}${data.totalRow - 1})`, options: { ...item, breakLine: true } },
      { text: "Share of the department: ", options: item },
      { text: pct(u.share), options: { bold: true } },
      { text: ` (rank ${u.rank} of ${units.length})`, options: { breakLine: true } },
      { text: "Average per budget item: ", options: item },
      { text: money(u.averagePerItem), options: { bold: true, breakLine: true } },
      { text: "Largest item: ", options: item },
      { text: `${top.name}, ${money(top.amount)}`, options: { bold: true } },
    ], { x: 1.15, y: 2.95, w: 3.95, h: 3.65, fontSize: 17, valign: "top", paraSpaceAfter: 10 });

    text(s, "Where the Money Goes (US$)", { x: 5.7, y: 2.2, w: 6.8, h: 0.5, fontSize: 22, bold: true, align: "center", valign: "middle" });
    const max = top.amount;
    s.addChart(pres.charts.BAR, [{
      name: u.name, labels: u.items.map((it) => it.name), values: u.items.map((it) => it.amount),
    }], {
      x: 5.55, y: 2.75, w: 7.05, h: 4.1,
      barDir: "bar", barGapWidthPct: 40,
      chartColors: [colorOf(u)],
      catAxisOrientation: "maxMin",
      catAxisLabelColor: TEXT, catAxisLabelFontFace: FONT, catAxisLabelFontSize: 12,
      catAxisLineShow: false, catAxisMajorTickMark: "none",
      valAxisHidden: true, valAxisMinVal: 0, valAxisMaxVal: Math.ceil((max * 1.25) / 10000) * 10000,
      valGridLine: { style: "none" }, catGridLine: { style: "none" },
      showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "$#,##0",
      dataLabelColor: TEXT, dataLabelFontFace: FONT, dataLabelFontSize: 12, dataLabelFontBold: true,
      showLegend: false, showTitle: false,
    });
    const second = u.items[1];
    s.addNotes(
      `${u.title}: this unit covers ${u.covers.charAt(0).toLowerCase() + u.covers.slice(1)}. ` +
      `Its total budget is ${money(u.total)}, the SUM of its ${data.itemCount} budget items. That is ${pct(u.share)} of the department budget, ` +
      `making it ${RANK_WORDS[u.rank - 1]} of the ${units.length} units. The largest item is ${top.name} at ${money(top.amount)} ` +
      `(${pct(top.amount / u.total)} of the unit's budget), followed by ${second.name} at ${money(second.amount)}. ` +
      `On average the unit spends ${money(u.averagePerItem)} per budget item (AVERAGE formula).`
    );
  });

  // ============================================================ 7. Budget table imported from Excel
  {
    const s = newSlide();
    title(s, pres, "Budget Table from Excel",
      "Imported from Marketing_Department_Budget.xlsx, sheet “Marketing Budget”, cells " + data.tableRange);
    const [pw, ph] = tableSize.points;
    const maxW = 11.6, maxH = 4.3;
    let w = maxW, h = (w * ph) / pw;
    if (h > maxH) { h = maxH; w = (h * pw) / ph; }
    const x = (W - w) / 2, y = 2.2;
    s.addImage({
      path: previewPath, x, y, w, h, objectName: "Excel Budget Table",
      altText: "Budget table from Excel: budget items by unit with SUM totals, AVERAGE rows and each unit's share of the total budget",
    });
    text(s, [
      { text: "Double-click the table to open it in Excel. ", options: { bold: true } },
      { text: "Blue figures are the budget inputs; black figures are SUM and AVERAGE formulas." },
    ], { x: 0.8, y: y + h + 0.15, w: W - 1.6, h: 0.4, fontSize: 15, align: "center", valign: "middle" });
    s.addNotes(
      "This is the budget table imported directly from the Excel workbook as an embedded Excel worksheet object, " +
      "so double-clicking it opens the live spreadsheet. Each row is a budget item and each column is a unit. " +
      `The Total column and the Total Budget row use SUM; the Average per Unit column and the Average per Budget Item row use AVERAGE. ` +
      `The department total is ${money(data.departmentTotal)} and the average per unit is ${money(data.averagePerUnit)}.`
    );
  }

  // ============================================================ 8. Units vs the average
  {
    const s = newSlide();
    title(s, pres, "Unit Budgets vs. the Average",
      `Each unit's total (SUM) compared with the average of ${money(data.averagePerUnit)} per unit (AVERAGE)`);
    const labels = units.map((u) => u.name);
    const maxTotal = Math.max(...units.map((u) => u.total));
    s.addChart([
      { type: pres.charts.BAR, data: [{ name: "Total budget", labels, values: units.map((u) => u.total) }],
        options: { chartColors: units.map(colorOf), barGapWidthPct: 60 } },
      { type: pres.charts.LINE, data: [{ name: "Average per unit", labels, values: units.map(() => data.averagePerUnit) }],
        options: { chartColors: [TEXT], lineSize: 2, lineDash: "dash", lineDataSymbol: "none", showValue: false, dataLabelPosition: "t" } },
    ], {
      x: 0.8, y: 2.15, w: 7.3, h: 4.75,
      barDir: "col",
      catAxisLabelColor: TEXT, catAxisLabelFontFace: FONT, catAxisLabelFontSize: 13,
      catAxisLineShow: true, catAxisLineColor: "BFBFBF",
      valAxisLabelColor: TEXT, valAxisLabelFontFace: FONT, valAxisLabelFontSize: 12,
      valAxisLabelFormatCode: "$#,##0", valAxisMinVal: 0,
      valAxisMaxVal: Math.ceil((maxTotal * 1.15) / 50000) * 50000, valAxisMajorUnit: 50000,
      valAxisLineShow: false,
      valGridLine: { color: "E7E6E6", size: 0.75 }, catGridLine: { style: "none" },
      showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "$#,##0",
      dataLabelColor: TEXT, dataLabelFontFace: FONT, dataLabelFontSize: 12, dataLabelFontBold: true,
      showLegend: false, showTitle: false,
    });

    box(s, pres, 8.45, 2.25, 4.05, 4.5);
    s.addShape(pres.shapes.LINE, { x: 8.75, y: 2.72, w: 0.5, h: 0, line: { color: TEXT, width: 2, dashType: "dash" } });
    text(s, `Average per unit: ${money(data.averagePerUnit)}`, { x: 9.35, y: 2.45, w: 3.05, h: 0.55, fontSize: 16, bold: true, valign: "middle" });
    const rows = [];
    units.forEach((u, i) => {
      const above = u.vsAverage >= 0;
      rows.push({ text: `${u.name}: `, options: { bold: true, bullet: { indent: 18 } } });
      rows.push({ text: `${money(Math.abs(u.vsAverage))} ${above ? "above" : "below"} the average`,
        options: { breakLine: i < units.length - 1 } });
    });
    text(s, rows, { x: 8.75, y: 3.2, w: 3.6, h: 3.4, fontSize: 17, valign: "top", paraSpaceAfter: 12 });
    const aboveNames = units.filter((u) => u.vsAverage > 0).map((u) => u.name);
    const belowNames = units.filter((u) => u.vsAverage < 0).map((u) => u.name);
    s.addNotes(
      `The dashed line marks the average budget per unit, ${money(data.averagePerUnit)}. ` +
      `${aboveNames.join(" and ")} are above the average; ${belowNames.join(" and ")} are below it. ` +
      `Advertising is ${money(ADV.vsAverage)} above the average, while Public Relations is ${money(Math.abs(PR.vsAverage))} below it.`
    );
  }

  // ============================================================ 9. Key takeaways
  {
    const s = newSlide();
    title(s, pres, "Key Takeaways");
    const eb = EBIZ.items.find((it) => it.name.startsWith("Digital"));
    const cards = [
      { head: [`${money(data.departmentTotal)} in Total`],
        body: `The SUM of the four unit budgets. The AVERAGE budget per unit is ${money(data.averagePerUnit)}.` },
      { head: ["Advertising Is the", "Largest Unit"],
        body: `${money(ADV.total)} (${pct(ADV.share)} of the total). Media space alone costs ${money(ADV.items[0].amount)}.` },
      { head: ["Staff Costs Are the", "Biggest Item"],
        body: `${data.largestItem.name} come to ${money(data.largestItem.total)} across all units, ${pct(data.largestItem.share)} of the budget.` },
      { head: ["Technology Leads", "e-Business"],
        body: `${money(eb.amount)} of its ${money(EBIZ.total)} (${pct(eb.amount / EBIZ.total)}) goes to digital platforms and technology.` },
    ];
    const gap = 0.25, x0 = 0.9, total = W - 1.8, cw = (total - gap * 3) / 4;
    cards.forEach((c, i) => {
      const x = x0 + i * (cw + gap);
      box(s, pres, x, 1.85, cw, 3.05);
      // Headlines break where we say, never inside "e-Business".
      text(s, c.head.map((t, k) => ({ text: t, options: { breakLine: k < c.head.length - 1 } })), {
        x: x + 0.15, y: 2.0, w: cw - 0.3, h: 0.75, fontSize: 18, bold: true, align: "center", valign: "middle",
      });
      rule(s, pres, x + 0.4, 2.85, cw - 0.8);
      text(s, c.body, { x: x + 0.2, y: 3.0, w: cw - 0.4, h: 1.8, fontSize: 17, valign: "top" });
    });
    rule(s, pres, 3.2, 5.4, W - 6.4);
    text(s, "Thank You. Questions?", {
      x: 0.8, y: 5.6, w: W - 1.6, h: 0.7, fontSize: 32, bold: true, color: TITLE, align: "center", valign: "middle",
    });
    s.addNotes(
      `To summarise: the department budget is ${money(data.departmentTotal)} with an average of ${money(data.averagePerUnit)} per unit. ` +
      `Advertising is the largest unit at ${money(ADV.total)}, staff salaries and benefits are the biggest single item at ${money(data.largestItem.total)}, ` +
      `and e-Business puts ${pct(eb.amount / EBIZ.total)} of its budget into digital platforms. Thank you; I am happy to take questions.`
    );
  }

  await pres.writeFile({ fileName: outPath });
  console.log("wrote " + outPath);
}

main().catch((e) => { console.error(e); process.exit(1); });
