// Build the Marketing Department Budget deck (before the Excel table is embedded).
//
// Usage: node build_deck.js slide_data.json table_preview.png table_size.json out.pptx
//
// Every figure comes from slide_data.json, which export_slide_data.py reads out of the
// finished workbook, so the slides always match the Excel file. Slide 7 gets a picture of
// the Excel budget table named "Excel Budget Table"; embed_excel_table.py swaps that
// picture for the real embedded Excel worksheet object.
const fs = require("fs");
const pptxgen = require("pptxgenjs");
const React = require("react");
const ReactDOMServer = require("react-dom/server");
const fa = require("react-icons/fa");
const sharp = require("sharp");

const [dataPath, previewPath, sizePath, outPath] = process.argv.slice(2);
const data = JSON.parse(fs.readFileSync(dataPath, "utf8"));
const tableSize = JSON.parse(fs.readFileSync(sizePath, "utf8"));

// ---------------------------------------------------------------- design tokens
const INK = "1B2436";      // dark background, primary text
const INK_CARD = "27324A"; // cards on dark slides
const TEXT2 = "5B6475";    // secondary text on light
const MUTED = "8A93A3";    // captions on light
const ON_DARK = "C9D0DC";  // body text on dark
const ON_DARK_MUTED = "9AA5B8";
const LINE = "E1E4EA";     // hairlines
const CARD = "F3F5F9";     // light card fill
const WHITE = "FFFFFF";
const FONT = "Arial";

const W = 13.333;          // LAYOUT_WIDE
const M = 0.6;             // side margin

const money = (n) => "$" + Math.round(n).toLocaleString("en-US");
const pct = (x) => (x * 100).toFixed(1) + "%";
const units = data.units;
const RANK_WORDS = ["the largest", "the second largest", "the third largest", "the smallest"];
const [ADV, MKT, PR, EBIZ] = units;

// ---------------------------------------------------------------- icons
async function icon(name, color, size = 512) {
  const svg = ReactDOMServer.renderToStaticMarkup(
    React.createElement(fa[name], { size, color: "#" + color })
  ).replace(/currentColor/g, "#" + color);
  const buf = await sharp(Buffer.from(svg)).resize(size, size, { fit: "contain", background: { r: 0, g: 0, b: 0, alpha: 0 } }).png().toBuffer();
  return "image/png;base64," + buf.toString("base64");
}

function iconCircle(slide, pres, { x, y, d, fill, img, scale = 0.5, name }) {
  slide.addShape(pres.shapes.OVAL, {
    x, y, w: d, h: d, fill: { color: fill }, line: { color: fill, width: 0 },
    objectName: name ? name + " circle" : undefined,
  });
  const s = d * scale;
  slide.addImage({ data: img, x: x + (d - s) / 2, y: y + (d - s) / 2, w: s, h: s, altText: name || "icon" });
}

function title(slide, text, sub, { dark = false, x = M, w = W - 2 * M } = {}) {
  slide.addText(text, {
    x, y: 0.42, w, h: 0.72, margin: 0, fontFace: FONT, fontSize: 36, bold: true,
    color: dark ? WHITE : INK, valign: "middle", isTextBox: true,
  });
  if (sub) {
    slide.addText(sub, {
      x, y: 1.14, w, h: 0.4, margin: 0, fontFace: FONT, fontSize: 15,
      color: dark ? ON_DARK : TEXT2, valign: "middle", isTextBox: true,
    });
  }
}

function footer(slide, n, { dark = false } = {}) {
  slide.addText(`Marketing Department Budget ${data.year}`, {
    x: M, y: 7.05, w: 6, h: 0.3, margin: 0, fontFace: FONT, fontSize: 10,
    color: dark ? ON_DARK_MUTED : MUTED, isTextBox: true,
  });
  slide.addText(String(n), {
    x: W - M - 1, y: 7.05, w: 1, h: 0.3, margin: 0, fontFace: FONT, fontSize: 10,
    color: dark ? ON_DARK_MUTED : MUTED, align: "right", isTextBox: true,
  });
}

async function main() {
  const pres = new pptxgen();
  pres.layout = "LAYOUT_WIDE";
  pres.title = `Marketing Department Budget ${data.year}`;
  pres.subject = "Budget for the Advertising, Marketing, Public Relations and e-Business units";
  pres.company = "Marketing Department";
  pres.author = "Marketing Department";

  const ICON = {};
  for (const u of units) ICON[u.name] = await icon(u.icon, INK);
  const wallet = await icon("FaWallet", WHITE);
  const scale = await icon("FaBalanceScale", WHITE);
  const excel = await icon("FaFileExcel", "1D6F42");
  const up = await icon("FaArrowUp", INK);
  const down = await icon("FaArrowDown", INK);
  const coinsInk = await icon("FaCoins", INK);
  const usersInk = await icon("FaUsers", INK);

  // ============================================================ 1. Title
  {
    const s = pres.addSlide();
    s.background = { color: INK };
    s.addText("MARKETING DEPARTMENT", {
      x: 0.8, y: 1.55, w: 6.6, h: 0.4, margin: 0, fontFace: FONT, fontSize: 14, bold: true,
      color: ON_DARK_MUTED, charSpacing: 4, isTextBox: true,
    });
    s.addText(`Annual Budget ${data.year}`, {
      x: 0.8, y: 2.05, w: 6.6, h: 1.9, margin: 0, fontFace: FONT, fontSize: 54, bold: true,
      color: WHITE, valign: "top", isTextBox: true,
    });
    s.addText("How the department's budget is planned and shared across its four units.", {
      x: 0.8, y: 4.15, w: 6.2, h: 1.0, margin: 0, fontFace: FONT, fontSize: 18,
      color: ON_DARK, valign: "top", isTextBox: true,
    });
    s.addText("Amounts in US$  ·  Source: Marketing_Department_Budget.xlsx", {
      x: 0.8, y: 6.55, w: 6.6, h: 0.35, margin: 0, fontFace: FONT, fontSize: 12,
      color: ON_DARK_MUTED, isTextBox: true,
    });
    // 2 x 2 grid of the units
    const d = 1.35, cols = [8.35, 10.85], rows = [1.45, 4.0];
    units.forEach((u, i) => {
      const cx = cols[i % 2], y = rows[Math.floor(i / 2)];
      iconCircle(s, pres, { x: cx - d / 2, y, d, fill: u.color, img: ICON[u.name], scale: 0.5, name: u.name });
      s.addText(u.name, {
        x: cx - 1.2, y: y + d + 0.15, w: 2.4, h: 0.4, margin: 0, fontFace: FONT, fontSize: 16,
        bold: true, color: WHITE, align: "center", isTextBox: true,
      });
      s.addText(`Unit ${i + 1}`, {
        x: cx - 1.2, y: y + d + 0.55, w: 2.4, h: 0.3, margin: 0, fontFace: FONT, fontSize: 12,
        color: ON_DARK_MUTED, align: "center", isTextBox: true,
      });
    });
    s.addNotes(
      `Good day. This presentation covers the ${data.year} budget of the Marketing Department. ` +
      "The department has four units: Advertising (Ads), Marketing, Public Relations (PR) and e-Business. " +
      "The figures were prepared in Microsoft Excel, where SUM and AVERAGE formulas calculate the totals and averages."
    );
  }

  // ============================================================ 2. Budget at a glance
  {
    const s = pres.addSlide();
    s.background = { color: WHITE };
    title(s, "Budget at a Glance", `How the ${money(data.departmentTotal)} department budget is shared across the four units`);

    const cards = [
      { y: 1.9, img: wallet, value: money(data.departmentTotal), label: "Total department budget",
        formula: `Excel: =SUM(B${data.totalRow}:E${data.totalRow})` },
      { y: 4.45, img: scale, value: money(data.averagePerUnit), label: "Average budget per unit",
        formula: `Excel: =AVERAGE(B${data.totalRow}:E${data.totalRow})` },
    ];
    for (const c of cards) {
      s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
        x: M, y: c.y, w: 4.3, h: 2.25, fill: { color: CARD }, line: { color: CARD, width: 0 }, rectRadius: 0.12,
      });
      iconCircle(s, pres, { x: M + 0.3, y: c.y + 0.3, d: 0.62, fill: INK, img: c.img, scale: 0.5 });
      s.addText(c.value, {
        x: M + 0.3, y: c.y + 1.0, w: 3.8, h: 0.65, margin: 0, fontFace: FONT, fontSize: 36, bold: true,
        color: INK, valign: "middle", isTextBox: true,
      });
      s.addText([
        { text: c.label, options: { fontSize: 14, color: TEXT2, breakLine: true } },
        { text: c.formula, options: { fontSize: 11, color: MUTED } },
      ], {
        x: M + 0.3, y: c.y + 1.65, w: 3.8, h: 0.5, margin: 0, fontFace: FONT, valign: "top", isTextBox: true,
      });
    }

    // Doughnut: share of total
    const dx = 5.3, dy = 1.85, dd = 4.8;
    s.addChart(pres.charts.DOUGHNUT, [{
      name: "Share of total budget", labels: units.map((u) => u.name), values: units.map((u) => u.total),
    }], {
      x: dx, y: dy, w: dd, h: dd, holeSize: 58,
      chartColors: units.map((u) => u.color),
      dataBorder: { pt: 2, color: WHITE },
      showPercent: true, showValue: false, showLabel: false, showLegend: false, showTitle: false,
      dataLabelColor: INK, dataLabelFontFace: FONT, dataLabelFontSize: 13, dataLabelFontBold: true,
      dataLabelFormatCode: "0.0%",
      firstSliceAng: 0,
    });
    s.addText([
      { text: "Share of", options: { breakLine: true } },
      { text: "total budget" },
    ], {
      x: dx + dd / 2 - 1.1, y: dy + dd / 2 - 0.4, w: 2.2, h: 0.8, margin: 0, fontFace: FONT,
      fontSize: 14, bold: true, color: TEXT2, align: "center", valign: "middle", isTextBox: true,
    });

    // Legend with values (also the readable table view of the doughnut)
    const lx = 10.4;
    units.forEach((u, i) => {
      const y = 2.05 + i * 1.12;
      s.addShape(pres.shapes.OVAL, { x: lx, y: y + 0.06, w: 0.26, h: 0.26, fill: { color: u.color }, line: { color: u.color, width: 0 } });
      s.addText(u.name, {
        x: lx + 0.42, y, w: 1.9, h: 0.38, margin: 0, fontFace: FONT, fontSize: 15, bold: true,
        color: INK, valign: "middle", isTextBox: true,
      });
      s.addText(`${money(u.total)}  ·  ${pct(u.share)}`, {
        x: lx + 0.42, y: y + 0.4, w: 1.9, h: 0.34, margin: 0, fontFace: FONT, fontSize: 13,
        color: TEXT2, valign: "middle", isTextBox: true,
      });
    });
    footer(s, 2);
    s.addNotes(
      `In total the department plans to spend ${money(data.departmentTotal)}. In Excel this is the SUM of the four unit budgets. ` +
      `The average budget per unit is ${money(data.averagePerUnit)}, calculated with the AVERAGE formula. ` +
      `Advertising takes the largest share (${pct(ADV.share)}), followed by Marketing (${pct(MKT.share)}), ` +
      `e-Business (${pct(EBIZ.share)}) and Public Relations (${pct(PR.share)}).`
    );
  }

  // ============================================================ 3-6. One slide per unit
  units.forEach((u, i) => {
    const s = pres.addSlide();
    s.background = { color: WHITE };
    iconCircle(s, pres, { x: M, y: 0.45, d: 0.95, fill: u.color, img: ICON[u.name], scale: 0.52, name: u.name });
    title(s, u.title, u.covers, { x: M + 1.25, w: W - 2 * M - 1.25 });

    // Left: the unit's key numbers
    const cx = M, cy = 1.9, cw = 4.3, ch = 4.95;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
      x: cx, y: cy, w: cw, h: ch, fill: { color: CARD }, line: { color: CARD, width: 0 }, rectRadius: 0.12,
    });
    const ix = cx + 0.35, iw = cw - 0.7;
    s.addText("TOTAL BUDGET", {
      x: ix, y: cy + 0.3, w: iw, h: 0.3, margin: 0, fontFace: FONT, fontSize: 11, bold: true,
      color: MUTED, charSpacing: 1.5, isTextBox: true,
    });
    s.addText(money(u.total), {
      x: ix, y: cy + 0.62, w: iw, h: 0.75, margin: 0, fontFace: FONT, fontSize: 44, bold: true,
      color: INK, valign: "middle", isTextBox: true,
    });
    s.addText(`=SUM(${u.column}5:${u.column}${data.totalRow - 1}) in Excel`, {
      x: ix, y: cy + 1.38, w: iw, h: 0.3, margin: 0, fontFace: FONT, fontSize: 11, color: MUTED, isTextBox: true,
    });
    const top = u.items[0];
    const stats = [
      [pct(u.share), `of the department budget (rank ${u.rank} of ${units.length})`],
      [money(u.averagePerItem), `average per budget item (=AVERAGE)`],
      [money(top.amount), `largest item: ${top.name}`],
    ];
    stats.forEach(([value, label], k) => {
      const y = cy + 1.95 + k * 0.98;
      s.addShape(pres.shapes.LINE, { x: ix, y: y - 0.12, w: iw, h: 0, line: { color: "D5DAE3", width: 0.75 } });
      s.addText(value, {
        x: ix, y, w: iw, h: 0.42, margin: 0, fontFace: FONT, fontSize: 22, bold: true, color: INK,
        valign: "middle", isTextBox: true,
      });
      s.addText(label, {
        x: ix, y: y + 0.42, w: iw, h: k === stats.length - 1 ? 0.55 : 0.36, margin: 0, fontFace: FONT, fontSize: 12, color: TEXT2,
        valign: "top", isTextBox: true,
      });
    });

    // Right: where the money goes
    s.addText("Where the money goes (US$)", {
      x: 5.35, y: 1.9, w: 7.3, h: 0.35, margin: 0, fontFace: FONT, fontSize: 14, bold: true, color: INK, isTextBox: true,
    });
    const max = top.amount;
    s.addChart(pres.charts.BAR, [{
      name: u.name, labels: u.items.map((it) => it.name), values: u.items.map((it) => it.amount),
    }], {
      x: 5.2, y: 2.3, w: 7.55, h: 4.6,
      barDir: "bar", barGapWidthPct: 45,
      chartColors: [u.color],
      catAxisOrientation: "maxMin",
      catAxisLabelColor: INK, catAxisLabelFontFace: FONT, catAxisLabelFontSize: 12,
      catAxisLineShow: false, catAxisMajorTickMark: "none",
      valAxisHidden: true, valAxisMinVal: 0, valAxisMaxVal: Math.ceil((max * 1.22) / 10000) * 10000,
      valGridLine: { style: "none" }, catGridLine: { style: "none" },
      showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "$#,##0",
      dataLabelColor: INK, dataLabelFontFace: FONT, dataLabelFontSize: 12, dataLabelFontBold: true,
      showLegend: false, showTitle: false,
    });
    footer(s, 3 + i);
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
    const s = pres.addSlide();
    s.background = { color: WHITE };
    title(s, "Budget Table from Excel",
      "Imported from Marketing_Department_Budget.xlsx, sheet “Marketing Budget”, cells " + data.tableRange);
    const [pw, ph] = tableSize.points;
    const maxW = W - 2 * M, maxH = 4.55;
    let w = maxW, h = (w * ph) / pw;
    if (h > maxH) { h = maxH; w = (h * pw) / ph; }
    const x = (W - w) / 2, y = 1.8;
    s.addImage({
      path: previewPath, x, y, w, h, objectName: "Excel Budget Table",
      altText: "Budget table from Excel: budget items by unit with SUM totals, AVERAGE rows and each unit's share of the total budget",
    });
    const capY = y + h + 0.2;
    s.addImage({ data: excel, x, y: capY + 0.04, w: 0.3, h: 0.3, altText: "Excel file" });
    s.addText([
      { text: "Double-click the table to open it in Excel.  ", options: { bold: true, color: INK } },
      { text: "Blue figures are the budget inputs; black figures are SUM and AVERAGE formulas.", options: { color: TEXT2 } },
    ], {
      x: x + 0.42, y: capY, w: w - 0.42, h: 0.38, margin: 0, fontFace: FONT, fontSize: 12,
      valign: "middle", isTextBox: true,
    });
    footer(s, 7);
    s.addNotes(
      "This is the budget table imported directly from the Excel workbook as an embedded Excel worksheet object, " +
      "so double-clicking it opens the live spreadsheet. Each row is a budget item and each column is a unit. " +
      `The Total column and the Total Budget row use SUM; the Average per Unit column and the Average per Budget Item row use AVERAGE. ` +
      `The department total is ${money(data.departmentTotal)} and the average per unit is ${money(data.averagePerUnit)}.`
    );
  }

  // ============================================================ 8. Units vs the average
  {
    const s = pres.addSlide();
    s.background = { color: WHITE };
    title(s, "Unit Budgets vs. the Average",
      `Each unit's total (SUM) compared with the average of ${money(data.averagePerUnit)} per unit (AVERAGE)`);
    const labels = units.map((u) => u.name);
    const maxTotal = Math.max(...units.map((u) => u.total));
    s.addChart([
      { type: pres.charts.BAR, data: [{ name: "Total budget", labels, values: units.map((u) => u.total) }],
        options: { chartColors: units.map((u) => u.color), barGapWidthPct: 55 } },
      { type: pres.charts.LINE, data: [{ name: "Average per unit", labels, values: units.map(() => data.averagePerUnit) }],
        options: { chartColors: [INK], lineSize: 2, lineDash: "dash", lineDataSymbol: "none", showValue: false } },
    ], {
      x: M, y: 1.85, w: 7.6, h: 5.0,
      barDir: "col",
      catAxisLabelColor: INK, catAxisLabelFontFace: FONT, catAxisLabelFontSize: 13,
      catAxisLineShow: true, catAxisLineColor: "C3C8D2",
      valAxisLabelColor: MUTED, valAxisLabelFontFace: FONT, valAxisLabelFontSize: 11,
      valAxisLabelFormatCode: "$#,##0", valAxisMinVal: 0,
      valAxisMaxVal: Math.ceil((maxTotal * 1.15) / 50000) * 50000, valAxisMajorUnit: 50000,
      valAxisLineShow: false,
      valGridLine: { color: LINE, size: 0.75 }, catGridLine: { style: "none" },
      showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "$#,##0",
      dataLabelColor: INK, dataLabelFontFace: FONT, dataLabelFontSize: 12, dataLabelFontBold: true,
      showLegend: false, showTitle: false,
    });
    // Right: key for the dashed line, then each unit above / below it
    const rx = 8.75;
    s.addShape(pres.shapes.LINE, { x: rx + 0.06, y: 2.26, w: 0.5, h: 0, line: { color: INK, width: 2, dashType: "dash" } });
    s.addText("Average per unit", {
      x: rx + 0.85, y: 1.91, w: 3.4, h: 0.36, margin: 0, fontFace: FONT, fontSize: 15, bold: true,
      color: INK, valign: "middle", isTextBox: true,
    });
    s.addText(`${money(data.averagePerUnit)}  (dashed line)`, {
      x: rx + 0.85, y: 2.27, w: 3.4, h: 0.34, margin: 0, fontFace: FONT, fontSize: 13,
      color: TEXT2, valign: "middle", isTextBox: true,
    });
    units.forEach((u, i) => {
      const y = 3.0 + i * 1.0;
      const above = u.vsAverage >= 0;
      iconCircle(s, pres, { x: rx, y, d: 0.62, fill: u.color, img: above ? up : down, scale: 0.46 });
      s.addText(u.name, {
        x: rx + 0.85, y: y - 0.04, w: 3.1, h: 0.36, margin: 0, fontFace: FONT, fontSize: 15, bold: true,
        color: INK, valign: "middle", isTextBox: true,
      });
      s.addText(`${money(Math.abs(u.vsAverage))} ${above ? "above" : "below"} the average`, {
        x: rx + 0.85, y: y + 0.32, w: 3.4, h: 0.34, margin: 0, fontFace: FONT, fontSize: 13,
        color: TEXT2, valign: "middle", isTextBox: true,
      });
    });
    footer(s, 8);
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
    const s = pres.addSlide();
    s.background = { color: INK };
    title(s, "Key Takeaways", null, { dark: true });
    const eb = EBIZ.items.find((it) => it.name.startsWith("Digital"));
    const cards = [
      { fill: WHITE, img: coinsInk, head: `${money(data.departmentTotal)} in total`,
        body: `The SUM of the four unit budgets. The AVERAGE budget per unit is ${money(data.averagePerUnit)}.` },
      { fill: ADV.color, img: ICON[ADV.name], head: "Advertising is the largest unit",
        body: `${money(ADV.total)} (${pct(ADV.share)} of the total). Media space alone costs ${money(ADV.items[0].amount)}.` },
      { fill: WHITE, img: usersInk, head: "Staff costs are the biggest item",
        body: `${data.largestItem.name} come to ${money(data.largestItem.total)} across all units, ${pct(data.largestItem.share)} of the budget.` },
      { fill: EBIZ.color, img: ICON[EBIZ.name], head: "Technology leads e-Business",
        body: `${money(eb.amount)} of its ${money(EBIZ.total)} (${pct(eb.amount / EBIZ.total)}) goes to digital platforms and technology.` },
    ];
    const cw = 5.9, chh = 2.1, xs = [M, W - M - cw], ys = [1.6, 4.05];
    cards.forEach((c, i) => {
      const x = xs[i % 2], y = ys[Math.floor(i / 2)];
      s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
        x, y, w: cw, h: chh, fill: { color: INK_CARD }, line: { color: INK_CARD, width: 0 }, rectRadius: 0.12,
      });
      iconCircle(s, pres, { x: x + 0.4, y: y + (chh - 0.8) / 2, d: 0.8, fill: c.fill, img: c.img, scale: 0.5 });
      // One box, two paragraphs: a headline that wraps pushes the body down instead of into it.
      s.addText([
        { text: c.head, options: { fontSize: 20, bold: true, color: WHITE, breakLine: true } },
        { text: c.body, options: { fontSize: 15, color: ON_DARK, paraSpaceBefore: 8 } },
      ], {
        x: x + 1.45, y: y + 0.2, w: cw - 1.75, h: chh - 0.4, margin: 0, fontFace: FONT,
        valign: "middle", isTextBox: true,
      });
    });
    s.addText("Thank you. Questions?", {
      x: M, y: 6.5, w: 8, h: 0.4, margin: 0, fontFace: FONT, fontSize: 16, bold: true,
      color: ON_DARK_MUTED, isTextBox: true,
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
