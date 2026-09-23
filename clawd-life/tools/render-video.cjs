// Render the animation frame by frame in headless Chromium and encode an MP4 with the soundtrack.
//
//   npm i -g playwright            (or set PW to a local playwright install)
//   FFMPEG=ffmpeg node tools/render-video.cjs [out.mp4]
//
// Env: W, H (default 1920×1080), FPS (30), FROM/TO seconds (0–30).
// Every frame is a pure function of time (window.__renderAt), so the result is exact, not a screen capture.
const path = require("path");
const { spawn, execSync } = require("child_process");
const PW = process.env.PW || path.join(execSync("npm root -g").toString().trim(), "playwright");
const { chromium } = require(PW);

const ROOT = path.resolve(__dirname, "..");
const OUT = path.resolve(process.argv[2] || "a-day-in-the-life-of-clawd.mp4");
const FFMPEG = process.env.FFMPEG || "ffmpeg";
const W = +(process.env.W || 1920), H = +(process.env.H || 1080), FPS = +(process.env.FPS || 30);
const FROM = +(process.env.FROM || 0), TO = +(process.env.TO || 30);

(async () => {
  const browser = await chromium.launch({ args: ["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"] });
  const page = await browser.newPage({ viewport: { width: W, height: H } });
  await page.route(/^https?:/, r => r.abort());
  page.on("pageerror", e => console.error("page error:", e.message));
  await page.goto("file://" + path.join(ROOT, "index.html") + "?capture");
  await page.waitForFunction(() => window.__ready, null, { timeout: 120000 });
  await page.evaluate(([w, h]) => window.__resize(w, h), [W, H]);

  const audio = path.join(ROOT, "soundtrack.mp3");
  const ff = spawn(FFMPEG, [
    "-loglevel", "error", "-y",
    "-f", "image2pipe", "-framerate", String(FPS), "-c:v", "mjpeg", "-i", "-",
    "-ss", String(FROM), "-t", String(TO - FROM), "-i", audio,
    "-map", "0:v", "-map", "1:a",
    "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-pix_fmt", "yuv420p", "-r", String(FPS),
    "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-shortest", OUT,
  ], { stdio: ["pipe", "inherit", "inherit"] });

  const t0 = Date.now();
  const n0 = Math.round(FROM * FPS), n1 = Math.round(TO * FPS);
  for (let f = n0; f < n1; f++) {
    const url = await page.evaluate(t => window.__renderAt(t), f / FPS);
    const buf = Buffer.from(url.slice(url.indexOf(",") + 1), "base64");
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once("drain", r));
    if ((f - n0) % FPS === FPS - 1) console.log(`${f + 1}/${n1} frames, ${((Date.now() - t0) / (f - n0 + 1)).toFixed(0)} ms/frame`);
  }
  ff.stdin.end();
  await new Promise(r => ff.on("close", r));
  await browser.close();
  console.log("wrote " + OUT);
})();
