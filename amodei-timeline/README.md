# Dario Amodei: Career Timeline

An 18-second, 1280×720, 30 fps monochrome motion-graphics timeline of Dario Amodei's public
career. It is one self-contained `index.html`: vanilla JS and canvas, no libraries, no CDNs.

## Preview

Open `index.html` in a browser. It plays once.

| Key | Action |
|---|---|
| `D` | debug overlay (time, frame, scene) |
| `R` or click | replay |
| `Space` | pause / resume |
| `←` `→` | step one frame |

`index.html?t=9.5` shows a single still at 9.5 s.

## Render to video

```sh
npm install
npx playwright install chromium
node capture.js        # writes frames/frame_0000.png … frame_0539.png
ffmpeg -framerate 30 -i frames/frame_%04d.png -i track.mp3 -c:v libx264 -pix_fmt yuv420p -shortest out.mp4
```

`capture.js` serves the folder on a local port, calls `window.renderAt(n / 30)` for
n = 0 to 539, and saves each canvas exactly. `--from`, `--to` and `--out` render part of it.
Put your `track.mp3` next to `index.html` before running ffmpeg.

Rendering is deterministic. Content never comes from `requestAnimationFrame` or the clock.
Grain, dust, flicker, typing glyphs and cut slices come from a seeded generator keyed to the
frame number, so the same `t` always gives the same pixels. The preview player only picks
which `t` to draw.

## Editing

Everything editable is in the `CONFIG` object at the top of `index.html`: scene start/end
times, years, titles, body lines, sources, the watermark, asset filenames, frame positions,
leader-line routes and typing speed.

Typing runs at one character every 0.03 s, as specified. Body lines type in parallel
(each starts 0.04 s after the one above). A line that can't finish at that rate before its
scene ends types just fast enough to finish 0.25 s before the cut. Press `D` to see the
fastest rate used in each scene.

## Assets

Images are converted to grayscale in code, with a little extra contrast and film grain.

| File | Status |
|---|---|
| `portrait.jpg`, `princeton.jpg`, `anthropic_logo.png`, `headline_2026.jpg`, `claude_55.jpg` | included |
| `physics.jpg` | missing: drawn as a circuit diagram |
| `openai.jpg` | missing: drawn as a neural-network diagram |
| `essay_mlg.jpg`, `essay_aot.jpg`, `time_cover.jpg` | missing: drawn as grey boxes with the filename |

Drop a file with the same name into `assets/` and it is used on the next load.
