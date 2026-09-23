# A Day in the Life of Clawd

A 64-second, single-shot 3D life-sim of Clawd, the Claude Code mascot, built with Three.js. Clawd
lives in a little round town with a pond in the middle. In one continuous camera move it wakes up,
hits the gym, ships code at Claude Code HQ, gets Employee of the Month at Anthropic HQ, hangs out
with its friend ChatGPT at the park, and walks home under the moon. The day ends back at
midnight, so it loops forever. It's signed off by Opus 5.5.

**▶ [Watch it](https://badboyvee.github.io/BlackHoleeee/clawd-life/)** · or open
[`index.html`](index.html) directly. It works offline: Three.js is vendored in
[`../vendor`](../vendor) and the soundtrack is embedded in [`soundtrack.js`](soundtrack.js).

## The day

| Time | Clock | Where | What happens |
| --- | --- | --- | --- |
| 0 – 8.8 s | 12 – 8 AM | 🏠 Home | Asleep under the moon. Sunrise over the pond, birds, the alarm rings, "!", hops out of bed and stretches |
| 8.8 – 19.8 s | 8 – 10 AM | 🏋️ Gym | Four barbell reps (+1 STR each), a treadmill sprint, "GAINS!" flex |
| 19.8 – 32.6 s | 10 AM – 1 PM | 💻 Claude Code HQ | Presses computer: `> BUILD SOMETHING AMAZING`, diffs, **GO. BRAZY.**, 48/48 tests, ✓ **SHIPPED!** with confetti |
| 32.6 – 44.3 s | 1 – 3 PM | 🏛️ Anthropic HQ | Glass doors slide open to "WELCOME, CLAWD!", then **Employee of the Month**: trophy, fanfare, applause, confetti, "LESGO!!", the dance, **BEST OF THE BEST** |
| 44.3 – 55 s | 3 – 7 PM | 🌳 Park | ChatGPT waves ("YO CLAWD!" / "HEY GPT!"), they high-five ♥, ride the seesaw (WHEEE!), and watch the sunset from a bench. "GN GPT!" / "GN CLAWD!" |
| 55 – 64 s | 7 PM – midnight | 🏠 Home | Walks home as the street lamps come on, hops into bed. Lullaby, "Goodnight, Clawd — Opus 5.5" |

A train loops the town on its outer track. ChatGPT dozes on the park bench overnight. A small
life-sim HUD tracks the in-game clock, what Clawd is doing, and its **Energy**, **Vibes** and
**Social** bars.

## How it's made

- **One continuous camera move.** Each stop has its own keyed camera path, written in that
  building's frame. During walks a follow-cam takes over. The shots cross-blend, so the camera
  never cuts, and the last frame flows back into the first.
- **The town is a ring.** Five stops sit around a circular path, each built in a local frame that
  faces the pond. The walks go round the ring, so the day ends where it started.
- **Everything is a pure function of time.** The pose, the sun and moon, the sky, the lights,
  the monitor contents, the confetti and the HUD are all computed from `t`, with no stored
  state. That's why `?t=12.8` shows an exact still and the video render is frame-perfect.
- **Clawd** is built from its pixel grid: body, eyes, two arms and four legs, each on its own pivot
  for walking, lifting, running, typing, flexing, dancing and seesawing.
- **ChatGPT, Clawd's friend,** is a round teal buddy with an antenna. It's a character of our own,
  not a logo.
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
| Hops, seesaw bumps | `pluck.wav`, pitched up |
| Footsteps, treadmill, keyboard clicks, high five | single conga hits cut from `kongas.wav`, re-pitched |
| Barbell clanks | `glasses.wav`, played slow |
| "+1 STR" dings | `kling.wav`, pitched up |
| Flex | `gong.wav` |
| Train | `train.wav` |
| Computer powering on | `strom.wav` |
| GO BRAZY frenzy | `wallewal.wav` |
| Shipped | `gong.wav`, `sparcle.wav` |
| Sliding doors | `soft.wav` |
| Welcome jingle, lullaby | `untie.wav` |
| Employee of the Month | `romans.wav`, `applause.wav` |
| Dance beat | `kongas.wav` |
| Sunset | `theetone.wav`, `falling.wav` |

Browsers only allow sound after a tap, so press **Sound on**.

## Controls

| Input | Action |
| --- | --- |
| **Sound on** / `M` | Plays the soundtrack, in sync |
| `Space` | Pause / play |
| `R` | Restart |
| `H` | Hide the controls |
| **Record** | Captures one loop with sound to `.webm` (standalone browser only) |
| `?t=48.4` | Freezes on one moment |

## Building

```sh
tools/build-audio.sh                                  # mix → soundtrack.wav/.mp3 → soundtrack.js
node tools/render-video.cjs clawd-life.mp4           # 1080p30 MP4 with sound (headless Chromium + ffmpeg, ~30 min)
python3 tools/build-standalone.py                     # one self-contained .html
```

`render-video.cjs` needs Playwright and `ffmpeg` with libx264. `build-audio.sh` needs Python 3
with NumPy, and the LibreOffice gallery sounds.
