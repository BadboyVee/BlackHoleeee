// Build Relative_Interest_Pie_Chart.pptx: the relative-interest pie chart, presented in a short
// six-slide deck.
//
// Usage: node build_deck.js deck_data.json out.pptx
//
// deck_data.json comes from export_deck_data.py, which reads each programme's average score,
// rank and share out of the finished Relative_Interest_Pie_Chart.xlsx, so the slides always
// match the workbook.
//
// The deck is built to be edited in PowerPoint: a theme (navy and orange, Calibri), three slide
// layouts (Title, Content and Closing) whose placeholders hold the titles, the footer and slide
// number on the Content layout, and sections. Each programme keeps one colour and one icon on
// every slide. The pie chart is a native chart (right-click it, then Edit Data) in the same
// colours as the chart in the workbook.
//
// build.sh then rewrites the chart XML to the strict schema PowerPoint 2013 expects
// (sanitize_charts.py) and gives every slide a Fade transition (finish_deck.py).
const fs = require("fs");
const pptxgen = require("pptxgenjs");
const React = require("react");
const ReactDOMServer = require("react-dom/server");
const sharp = require("sharp");
const fa = require("react-icons/fa");

const [dataPath, outPath] = process.argv.slice(2);
const data = JSON.parse(fs.readFileSync(dataPath, "utf8"));
const P = data.programmes;                    // pie order: largest share first

// ---------------------------------------------------------------- design tokens
const W = 13.333, H = 7.5;                    // PowerPoint 2013's widescreen slide
const MX = 0.6, CW = W - 2 * MX;              // side margins and content width
const NAVY = "1F4E79", TINT = "EEF2F7", INK = "262626";
const THEME = {
  name: "Programme Interest",
  headFontFace: "Calibri",
  bodyFontFace: "Calibri",
  colors: {
    dk1: INK, lt1: "FFFFFF", dk2: NAVY, lt2: TINT,
    // accent1 is the navy; accents 2 to 6 are the five programmes' colours, in pie order.
    accent1: NAVY, accent2: P[0].colour, accent3: P[1].colour, accent4: P[2].colour,
    accent5: P[3].colour, accent6: P[4].colour,
    hlink: P[1].colour, folHlink: "6B6B6B",
  },
};
const MUTED = "595959";                       // captions and small labels (7:1 on white)
const FOOT = "6B6B6B";                        // footer (5.3:1 on white)
const ON_NAVY = "D6DCE5", ON_NAVY_SOFT = "C9D6E3", ON_NAVY_WARM = "F4B183";   // >= 4.7:1 on navy
const RULE = "D9D9D9";

const ICON = {
  "Cybersecurity": fa.FaShieldAlt,
  "Digital Marketing": fa.FaBullhorn,
  "Data Analytics": fa.FaChartBar,
  "Generative AI & Prompt Engineering": fa.FaRobot,
  "Web Development": fa.FaCode,
};
const pct = (x) => `${Math.round(x * 100)}%`;
const [CYBER, DM, DA, GENAI, WEB] = P;
const FOOTER = "Market Research Lab  |  Task 1: Google Trends";
const PERIOD = "28 Sep 2025 to 28 Sep 2026";

// ---------------------------------------------------------------- helpers
const icons = new Map();
async function iconData(Icon, hex) {
  const key = `${Icon.name}-${hex}`;
  if (!icons.has(key)) {
    const svg = ReactDOMServer.renderToStaticMarkup(React.createElement(Icon, { color: `#${hex}`, size: 256 }));
    const png = await sharp(Buffer.from(svg)).png().toBuffer();
    icons.set(key, `image/png;base64,${png.toString("base64")}`);
  }
  return icons.get(key);
}

async function main() {
  const pres = new pptxgen();
  pres.layout = "LAYOUT_WIDE";
  pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
  pres.title = "Relative Interest in Digital-Skills Programmes";
  pres.subject = "Pie chart of the Google Trends relative-interest observations";
  pres.author = "";
  pres.company = "";
  const C = pres.SchemeColor;
  const programmeColour = (i) => C[`accent${i + 2}`];

  function text(slide, value, opts) {
    slide.addText(value, { margin: 0, isTextBox: true, color: C.text1, fontSize: 14, valign: "top", ...opts });
  }

  // A filled circle with an icon in it (the deck's motif).
  async function iconCircle(slide, { x, y, d, fill, Icon, hex, name, ratio = 0.5 }) {
    slide.addShape(pres.shapes.OVAL, { x, y, w: d, h: d, fill: { color: fill }, objectName: `${name} Circle` });
    const s = d * ratio;
    slide.addImage({ data: await iconData(Icon, hex), x: x + (d - s) / 2, y: y + (d - s) / 2, w: s, h: s,
                     altText: `${name} icon`, objectName: `${name} Icon` });
  }

  const shadow = () => ({ type: "outer", color: "000000", blur: 8, offset: 2, angle: 90, opacity: 0.14 });

  // The five programmes on a ring, clockwise from the top in the pie's order (dark slides).
  async function programmeRing(slide, caption) {
    const cx = 10.75, cy = 3.6, R = 1.55, D = 1.15;
    slide.addShape(pres.shapes.OVAL, { x: cx - R, y: cy - R, w: 2 * R, h: 2 * R,
                                       line: { color: C.background1, width: 1.25, transparency: 60 }, objectName: "Ring" });
    for (const [i, p] of P.entries()) {
      const a = (-90 + i * 72) * Math.PI / 180;
      await iconCircle(slide, { x: cx + R * Math.cos(a) - D / 2, y: cy + R * Math.sin(a) - D / 2, d: D,
                                fill: C.background1, Icon: ICON[p.name], hex: p.colour, name: p.name });
    }
    if (caption) {
      text(slide, caption, { x: cx - 1.75, y: cy + R + 0.5, w: 3.5, h: 0.35, fontSize: 14, color: ON_NAVY_SOFT,
                             align: "center", objectName: "Ring Caption" });
    }
  }

  // ---------------------------------------------------------------- layouts
  pres.defineSlideMaster({
    title: "Title",
    background: { color: C.text2 },
    objects: [
      { placeholder: { options: { name: "title", type: "title", x: 0.8, y: 2.0, w: 7.6, h: 1.75, fontSize: 40,
                                  bold: true, color: C.background1, align: "left", valign: "top", margin: 0 },
                       text: "" } },
      { placeholder: { options: { name: "body", type: "body", x: 0.8, y: 3.7, w: 7.6, h: 1.0, fontSize: 20,
                                  color: ON_NAVY, align: "left", valign: "top", margin: 0 }, text: "" } },
    ],
  });
  pres.defineSlideMaster({
    title: "Content",
    background: { color: C.background1 },
    objects: [
      { placeholder: { options: { name: "title", type: "title", x: MX, y: 0.4, w: CW, h: 0.8, fontSize: 32,
                                  bold: true, color: C.text2, align: "left", valign: "middle", margin: 0 },
                       text: "" } },
      { placeholder: { options: { name: "subtitle", type: "body", x: MX, y: 1.2, w: CW, h: 0.45, fontSize: 16,
                                  color: MUTED, align: "left", valign: "top", margin: 0 }, text: "" } },
      { text: { text: FOOTER, options: { x: MX, y: 6.98, w: 8, h: 0.3, fontSize: 10, color: FOOT, margin: 0,
                                         valign: "middle" } } },
    ],
    slideNumber: { x: W - MX - 0.8, y: 6.98, w: 0.8, h: 0.3, fontSize: 10, color: FOOT, align: "right" },
  });
  pres.defineSlideMaster({
    title: "Closing",
    background: { color: C.text2 },
    objects: [
      { placeholder: { options: { name: "title", type: "title", x: 0.8, y: 2.1, w: 7.6, h: 1.2, fontSize: 54,
                                  bold: true, color: C.background1, align: "left", valign: "bottom", margin: 0 },
                       text: "" } },
      { placeholder: { options: { name: "body", type: "body", x: 0.8, y: 3.45, w: 7.6, h: 0.7, fontSize: 24,
                                  color: ON_NAVY, align: "left", valign: "top", margin: 0 }, text: "" } },
    ],
  });
  const title = (slide, value) => slide.addText(value, { placeholder: "title", align: "left" });
  const sub = (slide, value, placeholder = "subtitle") =>
    slide.addText(value, { placeholder, bullet: false, align: "left" });

  // ================================================================ 1. Title
  pres.addSection({ title: "Introduction" });
  let s = pres.addSlide({ masterName: "Title", sectionTitle: "Introduction" });
  text(s, "MARKET RESEARCH LAB  |  TASK 1", { x: 0.8, y: 1.45, w: 7.6, h: 0.4, fontSize: 14, bold: true,
                                               color: ON_NAVY_WARM, charSpacing: 2, objectName: "Overline" });
  title(s, "Relative Interest in Digital-Skills Programmes");
  sub(s, "A Google Trends comparison of five programmes in Nigeria over the past 12 months", "body");
  text(s, `Data: Google Trends  |  Nigeria  |  ${PERIOD}`, { x: 0.8, y: 6.3, w: 7.6, h: 0.4, fontSize: 14,
                                                            color: ON_NAVY_SOFT, objectName: "Data Note" });
  await programmeRing(s, "Five programmes compared");
  s.addNotes("This presentation compares how much people in Nigeria searched online for five digital-skills " +
             "programmes over the past 12 months, using Google Trends.");

  // ================================================================ 2. How the data was collected
  s = pres.addSlide({ masterName: "Content", sectionTitle: "Introduction" });
  title(s, "How the Data Was Collected");
  sub(s, "Google Trends scores search interest from 0 to 100, where 100 is the highest point in the period");
  const METHOD = [
    [fa.FaSearch, "Tool", "Google Trends: web search, all categories"],
    [fa.FaMapMarkerAlt, "Location", "Nigeria, with results for each state"],
    [fa.FaCalendarAlt, "Time period", `Past 12 months: ${PERIOD}`],
    [fa.FaTachometerAlt, "Measure", "Each programme's average interest, from 0 to 100"],
  ];
  const cardW = (CW - 3 * 0.3) / 4;
  for (const [i, [Icon, head, body]] of METHOD.entries()) {
    const x = MX + i * (cardW + 0.3), y = 1.9;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w: cardW, h: 2.3, rectRadius: 0.08, fill: { color: C.background2 },
                                                objectName: `${head} Card` });
    await iconCircle(s, { x: x + 0.3, y: y + 0.3, d: 0.75, fill: C.text2, Icon, hex: "FFFFFF", name: head });
    text(s, head, { x: x + 0.3, y: y + 1.2, w: cardW - 0.6, h: 0.4, fontSize: 18, bold: true, color: C.text2,
                    objectName: `${head} Heading` });
    text(s, body, { x: x + 0.3, y: y + 1.6, w: cardW - 0.6, h: 0.6, fontSize: 14, objectName: `${head} Text` });
  }
  text(s, "Five programmes compared", { x: MX, y: 4.5, w: CW, h: 0.35, fontSize: 16, bold: true, color: C.text2,
                                        objectName: "Programmes Heading" });
  const chipW = CW / 5;
  for (const [i, p] of P.entries()) {
    const x = MX + i * chipW;
    await iconCircle(s, { x: x + (chipW - 0.7) / 2, y: 4.95, d: 0.7, fill: programmeColour(i), Icon: ICON[p.name],
                          hex: "FFFFFF", name: p.name });
    text(s, p === GENAI ? `${p.name}*` : p.name, { x: x + 0.1, y: 5.72, w: chipW - 0.2, h: 0.55, fontSize: 14,
                                                  align: "center", objectName: `${p.name} Label` });
  }
  text(s, "* Google Trends compares at most five search terms at once, so Generative AI and Prompt Engineering " +
          "were searched together as one term.",
       { x: MX, y: 6.42, w: CW, h: 0.3, fontSize: 12, color: MUTED, objectName: "Footnote" });
  s.addNotes("I used Google Trends to compare the five programmes in Nigeria over the past 12 months, using web " +
             "searches in all categories. Google Trends scores interest from 0 to 100, where 100 is the highest " +
             "point. It compares at most five terms, so Generative AI and Prompt Engineering were searched together.");

  // ================================================================ 3. The pie chart
  pres.addSection({ title: "Findings" });
  s = pres.addSlide({ masterName: "Content", sectionTitle: "Findings" });
  title(s, `${CYBER.name} Leads Search Interest`);
  sub(s, "Each programme's share of the total average interest in Nigeria over the past 12 months");
  s.addChart(pres.charts.PIE, [{ name: "Average score", labels: P.map((p) => p.name), values: P.map((p) => p.score) }], {
    x: MX, y: 1.8, w: 5.5, h: 4.55,
    chartColors: P.map((p) => p.colour),
    dataBorder: { pt: 2, color: "FFFFFF" },
    dataNoEffects: true,                      // flat slices: no shadow
    firstSliceAng: 0,
    showLegend: false, showTitle: false,
    showPercent: true, showValue: false, showLabel: false, showLeaderLines: false,
    dataLabelPosition: "inEnd", dataLabelColor: "FFFFFF", dataLabelFontSize: 18, dataLabelFontBold: true,
    dataLabelFontFace: "+mn-lt",
    layout: { x: 0.03, y: 0.03, w: 0.94, h: 0.94 },
    objectName: "Pie Chart",
  });
  const RX = 6.65, RW = W - MX - RX;          // the right-hand panel
  text(s, pct(CYBER.share), { x: RX, y: 1.85, w: 2.0, h: 1.0, fontSize: 60, bold: true, color: programmeColour(0),
                               valign: "middle", objectName: "Key Figure" });
  text(s, `of all the search interest went to ${CYBER.name}, the most of the five programmes`,
       { x: RX + 2.15, y: 1.95, w: RW - 2.15, h: 0.8, fontSize: 16, valign: "middle", objectName: "Key Figure Text" });
  // The key: one row per slice, in the pie's order (clockwise from the top).
  const KEY_Y = 3.2, ROW = 0.55;
  const NAME_X = RX + 0.45, SCORE_X = RX + 3.95, SHARE_X = RX + 5.0;
  text(s, "PROGRAMME", { x: NAME_X, y: KEY_Y, w: 3.0, h: 0.3, fontSize: 11, bold: true, color: MUTED, charSpacing: 1,
                         objectName: "Key Heading Programme" });
  text(s, "AVG. SCORE", { x: SCORE_X - 0.45, y: KEY_Y, w: 1.4, h: 0.3, fontSize: 11, bold: true, color: MUTED,
                          charSpacing: 1, align: "right", objectName: "Key Heading Score" });
  text(s, "SHARE", { x: SHARE_X, y: KEY_Y, w: RW - (SHARE_X - RX), h: 0.3, fontSize: 11, bold: true, color: MUTED,
                     charSpacing: 1, align: "right", objectName: "Key Heading Share" });
  for (const [i, p] of P.entries()) {
    const y = KEY_Y + 0.4 + i * ROW;
    s.addShape(pres.shapes.LINE, { x: RX, y, w: RW, h: 0, line: { color: RULE, width: 0.75 }, objectName: `Key Rule ${i + 1}` });
    s.addShape(pres.shapes.OVAL, { x: RX + 0.08, y: y + (ROW - 0.24) / 2, w: 0.24, h: 0.24, fill: { color: programmeColour(i) },
                                   objectName: `${p.name} Key` });
    const bold = i === 0;
    text(s, p.name, { x: NAME_X, y, w: 3.45, h: ROW, fontSize: 15, bold, valign: "middle", objectName: `${p.name} Name` });
    text(s, String(p.score), { x: SCORE_X, y, w: 0.95, h: ROW, fontSize: 15, bold, align: "right", valign: "middle",
                               objectName: `${p.name} Score` });
    text(s, pct(p.share), { x: SHARE_X, y, w: RW - (SHARE_X - RX), h: ROW, fontSize: 15, bold: true, align: "right",
                            valign: "middle", objectName: `${p.name} Share` });
  }
  text(s, `Source: Google Trends (web search), Nigeria, ${PERIOD}. Share = average score ÷ ${data.total}, ` +
          "the total of all five scores.",
       { x: MX, y: 6.5, w: CW, h: 0.3, fontSize: 11, color: MUTED, objectName: "Source" });
  s.addNotes(`The pie chart shows each programme's share of the total average interest. ${CYBER.name} has the ` +
             `largest share at ${pct(CYBER.share)}, followed by ${DM.name} at ${pct(DM.share)} and ${DA.name} at ` +
             `${pct(DA.share)}. ${GENAI.name} and ${WEB.name} have ${pct(WEB.share)} each.`);

  // ================================================================ 4. What the chart shows
  s = pres.addSlide({ masterName: "Content", sectionTitle: "Findings" });
  title(s, "Two Programmes Draw Almost Two-Thirds of Interest");
  sub(s, `${CYBER.name} and ${DM.name} lead; the other three programmes trail well behind`);
  const OBS = [
    { who: [0], head: `${CYBER.name} is the clear leader`,
      body: `Around ${CYBER.score} on average (${pct(CYBER.share)}). It was the highest almost all year and ` +
            "jumped to 100 in April 2026, probably after news of a breach at the CAC." },
    { who: [1], head: `${DM.name} is a strong second`,
      body: `Around ${DM.score} on average (${pct(DM.share)}). It peaked in late January 2026 and was the most ` +
            "searched programme in some southern states." },
    { who: [2], head: `${DA.name} sits in the middle`,
      body: `Around ${DA.score} on average (${pct(DA.share)}). It stayed steady all year, at about 15 to 25.` },
    { who: [3, 4], head: "Two programmes tie for last",
      body: `${GENAI.name} and ${WEB.name}: around ${WEB.score} each (${pct(WEB.share)} each). Both stayed ` +
            "low all year, at about 10 to 20." },
  ];
  const obsW = (CW - 0.3) / 2, obsH = 2.05;
  for (const [k, o] of OBS.entries()) {
    const x = MX + (k % 2) * (obsW + 0.3), y = 1.95 + Math.floor(k / 2) * (obsH + 0.3);
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w: obsW, h: obsH, rectRadius: 0.08, fill: { color: C.background1 },
                                                line: { color: "E1E6EE", width: 0.75 }, shadow: shadow(),
                                                objectName: `Finding ${k + 1} Card` });
    for (const [j, i] of o.who.entries()) {
      const d = o.who.length > 1 ? 0.68 : 0.85;
      await iconCircle(s, { x: x + 0.3, y: y + 0.3 + j * 0.8, d, fill: programmeColour(i), Icon: ICON[P[i].name],
                            hex: "FFFFFF", name: `Finding ${k + 1} ${P[i].name}` });
    }
    text(s, o.head, { x: x + 1.45, y: y + 0.28, w: obsW - 1.75, h: 0.45, fontSize: 18, bold: true, color: C.text2,
                      objectName: `Finding ${k + 1} Heading` });
    text(s, o.body, { x: x + 1.45, y: y + 0.8, w: obsW - 1.75, h: 1.1, fontSize: 16,
                      objectName: `Finding ${k + 1} Text` });
  }
  s.addNotes(`${CYBER.name} and ${DM.name} together take almost two-thirds of the search interest. ` +
             `${CYBER.name} was the highest almost all year and jumped to 100 in April 2026, probably because of ` +
             `news about a cybersecurity breach at the Corporate Affairs Commission. ${DM.name} peaked in late ` +
             `January. ${DA.name} stayed steady, and ${GENAI.name} and ${WEB.name} stayed low all year.`);

  // ================================================================ 5. What this means
  pres.addSection({ title: "Conclusion" });
  s = pres.addSlide({ masterName: "Content", sectionTitle: "Conclusion" });
  title(s, "What This Means for Promotion");
  sub(s, "Recommendations for promoting the programmes to university students");
  // The headline figures on a navy panel.
  const panelW = 3.9;
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: MX, y: 1.95, w: panelW, h: 4.35, rectRadius: 0.08, fill: { color: C.text2 },
                                              objectName: "Highlights Panel" });
  for (const [k, [p, colour]] of [[CYBER, ON_NAVY_WARM], [DM, "BDD7EE"]].entries()) {
    const y = 2.2 + k * 1.45;
    text(s, pct(p.share), { x: MX + 0.4, y, w: panelW - 0.8, h: 0.85, fontSize: 54, bold: true, color: colour,
                            valign: "middle", objectName: `${p.name} Figure` });
    text(s, p.name, { x: MX + 0.4, y: y + 0.85, w: panelW - 0.8, h: 0.4, fontSize: 16, color: C.background1,
                      objectName: `${p.name} Figure Label` });
  }
  s.addShape(pres.shapes.LINE, { x: MX + 0.4, y: 5.15, w: panelW - 0.8, h: 0, line: { color: C.background1, width: 0.75,
                                 transparency: 50 }, objectName: "Highlights Rule" });
  text(s, "Together, almost two-thirds of all the search interest", { x: MX + 0.4, y: 5.3, w: panelW - 0.8, h: 0.75,
       fontSize: 16, color: ON_NAVY, objectName: "Highlights Text" });
  const RECS = [
    [`Lead with ${CYBER.name} and ${DM.name}`,
     "Put most of the promotion behind the two programmes students already search for most."],
    ["Build awareness for the other three",
     "Explain what Data Analytics, Generative AI and Web Development teach and the jobs they lead to."],
    ["Use the words people search for",
     "Related searches show people want free courses, skills and jobs, so adverts should mention them."],
  ];
  const recX = MX + panelW + 0.5, recW = W - MX - recX;
  for (const [k, [head, body]] of RECS.entries()) {
    const y = 1.95 + k * 1.5;
    s.addShape(pres.shapes.OVAL, { x: recX, y: y + 0.05, w: 0.7, h: 0.7, fill: { color: C.accent2 },
                                   objectName: `Recommendation ${k + 1} Circle` });
    text(s, String(k + 1), { x: recX, y: y + 0.05, w: 0.7, h: 0.7, fontSize: 24, bold: true, color: C.background1,
                             align: "center", valign: "middle", objectName: `Recommendation ${k + 1} Number` });
    text(s, head, { x: recX + 0.95, y, w: recW - 0.95, h: 0.45, fontSize: 20, bold: true, color: C.text2,
                    objectName: `Recommendation ${k + 1} Heading` });
    text(s, body, { x: recX + 0.95, y: y + 0.5, w: recW - 0.95, h: 0.8, fontSize: 16,
                    objectName: `Recommendation ${k + 1} Text` });
  }
  s.addNotes(`Because ${CYBER.name} and ${DM.name} already attract almost two-thirds of the interest, they ` +
             "should lead the promotion. The other three programmes need awareness campaigns that explain what " +
             "they teach and the jobs they lead to. And since people search for free courses, skills and jobs, " +
             "the adverts should use those words.");

  // ================================================================ 6. Thank you
  s = pres.addSlide({ masterName: "Closing", sectionTitle: "Conclusion" });
  title(s, "Thank You");
  sub(s, "Questions and comments are welcome", "body");
  await programmeRing(s);
  text(s, `Data: Google Trends  |  Nigeria  |  ${PERIOD}`, { x: 0.8, y: 6.3, w: 7.6, h: 0.4, fontSize: 14,
                                                            color: ON_NAVY_SOFT, objectName: "Data Note" });
  s.addNotes("Thank you for listening. I am happy to take questions.");

  await pres.writeFile({ fileName: outPath });
  await applyTheme(outPath, THEME);
  console.log(`wrote ${outPath} (${pres.slides.length} slides)`);
}

// pptxgenjs sets the theme's fonts but keeps Office's colours; write the deck's own colours and
// name into ppt/theme/theme1.xml, so the scheme colours used above resolve to them.
async function applyTheme(file, theme) {
  const JSZip = require(require.resolve("jszip", { paths: [require.resolve("pptxgenjs")] }));
  const zip = await JSZip.loadAsync(fs.readFileSync(file));
  const part = "ppt/theme/theme1.xml";
  const slots = ["dk1", "lt1", "dk2", "lt2", "accent1", "accent2", "accent3", "accent4", "accent5", "accent6",
                 "hlink", "folHlink"];
  const scheme = `<a:clrScheme name="${theme.name}">` +
    slots.map((k) => `<a:${k}><a:srgbClr val="${theme.colors[k]}"/></a:${k}>`).join("") + "</a:clrScheme>";
  const xml = (await zip.file(part).async("string"))
    .replace(/<a:clrScheme\b[\s\S]*?<\/a:clrScheme>/, () => scheme)
    .replace(/(<a:(?:theme|fontScheme)\b[^>]*?\bname=")[^"]*"/g, (_, head) => `${head}${theme.name}"`);
  if (!xml.includes(scheme)) throw new Error(`${part} has no colour scheme to replace`);
  zip.file(part, xml);
  for (const name of Object.keys(zip.files)) {        // a scheme colour in a hex-only option
    if (!name.endsWith(".xml")) continue;
    const bad = (await zip.file(name).async("string")).match(/<a:srgbClr val="((?![0-9A-Fa-f]{6}")[^"]*)"/);
    if (bad) throw new Error(`${name} has <a:srgbClr val="${bad[1]}">: pass hex there, not a scheme colour`);
  }
  fs.writeFileSync(file, await zip.generateAsync({ type: "nodebuffer", compression: "DEFLATE" }));
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
