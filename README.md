# BlackHoleeee

A sandbox of single-file, browser-native experiments. No build step in any of them — every
project is an `index.html` you can open directly.

## Projects

### 🥚 [Opus 5 — the launch film, in code](launch-film/)

Eighteen seconds on tan paper: speckled eggs arrive until they form a **5**, hatch into birds on
the same spots, and the flock lifts off, leaving the wordmark. Eggs and birds are both generated —
ovoid geometry, shell markings, plumage, wingbeats — so there are no images, no video and no
libraries. The first 8 seconds recreate the launch clip; the rest is an extension.

**▶ [Watch it](https://badboyvee.github.io/BlackHoleeee/launch-film/)** · [source](launch-film/)

### 🪺 [Opus 5 — the launch film in 3D](launch-film-3d/)

The same eight seconds in Three.js: the eggs become lathed solids of revolution wearing shell
textures painted at startup, lit and casting soft shadows onto paper, with a camera you can drag.
Still no images and no models — just geometry and canvases.

**▶ [Watch it](https://badboyvee.github.io/BlackHoleeee/launch-film-3d/)** · [source](launch-film-3d/)

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
