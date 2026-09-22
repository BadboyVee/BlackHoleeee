# A Day in the Life of Claude Code

A 30-second, single-shot 3D animation of a day in the life of the Claude Code mascot, built
with Three.js. It wakes up with the sun, walks to work, presses computer, goes brazy, ships,
dances, walks home under the moon and goes to bed. The day closes back at midnight, so it
loops forever. It's signed off by Opus 5.5.

**▶ [Watch it](https://badboyvee.github.io/BlackHoleeee/claude-code-life/)** · or open
[`index.html`](index.html) directly. It works offline: Three.js is vendored in
[`../vendor`](../vendor) and the soundtrack is embedded in [`soundtrack.js`](soundtrack.js).

## The day

| Time | Clock | What happens |
| --- | --- | --- |
| 0 – 5 s | 12:00 – 7:00 AM | Asleep under the moon, Zzz. The sun rises over the hills, birds start up, the alarm rings |
| 5 – 7.5 s | 7:00 AM | Eyes pop open, "!", hops out of bed, big stretch |
| 7.5 – 12 s | 7:30 – 10:00 AM | Commutes along the path, while a train passes behind the trees |
| 12 – 16 s | 10 AM – 1 PM | Clocks in at Claude Code HQ. The monitor boots, then: `> BUILD SOMETHING AMAZING`, thinking, edits and diffs |
| 16 – 18.5 s | 1 – 2:30 PM | **GO. BRAZY.** Tests fill up 48/48 |
| 18.5 – 22.4 s | 2:30 – 6 PM | ✓ Shipped. Gong, fanfare, confetti, **BEST OF THE BEST**, "LESGO!!", and the dance |
| 22.4 – 27 s | 6 – 9 PM | Sunset. Walks home as the street lamps come on and the stars come out. Hops into bed |
| 27 – 30 s | 9 PM – midnight | Lullaby, "Goodnight, Claude Code — Opus 5.5" |

A small life-sim HUD tracks the in-game clock, what Claude Code is doing, and its Energy and
Vibes.

## How it's made

- **One continuous camera move.** The camera follows a periodic Catmull-Rom spline through 16
  keyed positions, so the shot never cuts and the end flows back into the start.
- **Everything is a pure function of time.** The pose, the sun and moon, the sky, the lights,
  the monitor contents, the confetti and the HUD are all computed from `t`, with no stored
  state. That's why `?t=12.8` shows an exact still and the video render is frame-perfect.
- **The mascot** is built from its pixel grid: body, eyes, two arms and four legs, each on its
  own pivot for walking, typing, stretching and dancing.
- **All text** uses a built-in 5×7 pixel font drawn to canvas, so it looks identical on every
  device and in the video.
- **Day/night:** the sun and moon arcs drive a gradient sky shader (with twinkling stars), the
  sun's shadow-casting light, moonlight, the street lamps and the bedside lamp.

## Sound

The soundtrack uses **recorded samples only**, with no synthesis. They all come from the
LibreOffice sound gallery that was already on disk (`/usr/lib/libreoffice/share/gallery/sounds`,
shipped with LibreOffice under the MPL 2.0). [`tools/mix.py`](tools/mix.py) places them on
the timeline:

| Moment | Sample |
| --- | --- |
| Stars | `sparcle.wav` |
| Sunrise | `roll.wav` |
| Birds | `nature1.wav`, `nature2.wav` |
| Alarm | `kling.wav` |
| Hops | `pluck.wav`, pitched up |
| Footsteps and keyboard clicks | single conga hits cut from `kongas.wav`, re-pitched |
| Train | `train.wav` |
| Computer powering on | `strom.wav` |
| GO BRAZY frenzy | `wallewal.wav` |
| Dance beat | `kongas.wav` |
| Shipped | `gong.wav`, `romans.wav`, `applause.wav` |
| Sunset | `falling.wav` |
| Lullaby | `untie.wav` |

Browsers only allow sound after a tap, so press **Sound on**.

## Controls

| Input | Action |
| --- | --- |
| **Sound on** / `M` | Plays the soundtrack, in sync |
| `Space` | Pause / play |
| `R` | Restart |
| `H` | Hide the controls |
| **Record** | Captures one loop with sound to `.webm` (standalone browser only) |
| `?t=19.8` | Freezes on one moment |

## Building

```sh
tools/build-audio.sh                                  # mix → soundtrack.wav/.mp3 → soundtrack.js
node tools/render-video.cjs claude-code-life.mp4      # 1080p30 MP4 with sound (headless Chromium + ffmpeg)
python3 tools/build-standalone.py                     # one self-contained .html
```

`render-video.cjs` needs Playwright and `ffmpeg` with libx264. `build-audio.sh` needs Python 3
with NumPy, and the LibreOffice gallery sounds.
