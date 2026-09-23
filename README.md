# BlackHoleeee

A sandbox of single-file, browser-native 3D experiments built with Three.js. No build step in
any of them — every project is an `index.html` you can open directly.

## Projects

### 🟧 [A Day in the Life of Clawd](clawd-life/)

A 30-second, single-shot 3D life-sim of Clawd, the Claude Code mascot. It wakes up with the sun,
commutes, presses computer, goes brazy, ships, dances, and walks home under the moon. The
soundtrack is made only of recorded samples, and it's signed off by Opus 5.5.

**▶ [Watch it](https://badboyvee.github.io/BlackHoleeee/clawd-life/)** · [source](clawd-life/)

### 🎬 [Opus 5.5 — Launch Film](opus-launch/)

A real-time Three.js remake of the Opus 5.5 launch film. It uses about 30 hard cuts of
procedural macro "horizons" (amber, lace, agate, fur, plant cells…), all rendered on one
shader-driven sphere, with "There’s more to discover" set along the horizon. There's an
optional synthesized soundtrack, and you can record the loop to a .webm file.

**▶ [Watch it](https://badboyvee.github.io/BlackHoleeee/opus-launch/)** · [source](opus-launch/)

### 🚋 [Skyline Tram](skyline-tram/)

Drive a retro aerial tram along a rail loop between two islands floating above a sea of clouds.
Warm low-poly Ghibli-seaside styling, a passenger comfort system that rewards smooth driving,
station stops with boarding passengers, and a workshop where you bolt new parts onto the tram.

**▶ [Play it](https://badboyvee.github.io/BlackHoleeee/skyline-tram/)** · [source & prompt](skyline-tram/)

### 🚗 [BMW M5 CS](bmw-m5-cs/)

A procedural BMW M5 CS model rendered in a studio lighting setup.

**▶ [View it](https://badboyvee.github.io/BlackHoleeee/bmw-m5-cs/)** · [source](bmw-m5-cs/)

## Hosting

`netlify.toml` publishes `bmw-m5-cs/` as the Netlify site root. GitHub Pages serves the whole
repository, so each project is reachable at `badboyvee.github.io/BlackHoleeee/<project>/`.
