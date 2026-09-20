# BlackHoleeee

A sandbox of single-file, browser-native 3D experiments built with Three.js. No build step in
any of them — every project is an `index.html` you can open directly.

## Projects

### 🚙 [Waymo Jaguar I-PACE](waymo.html)

A procedurally modelled Waymo robotaxi in a high-key white studio. The body is a single
lofted surface driven by keyframed section profiles, with real wheel-arch openings, tinted
panoramic glazing and the 5th-generation Waymo Driver: roof fairing with the spinning LiDAR
dome and camera collar, front wing pods, mirror cameras and bumper perimeter housings.
Orbit with the mouse; nothing else on screen.

**▶ [View it](https://badboyvee.github.io/BlackHoleeee/waymo.html)** · [source](waymo.html)

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
repository, so each project is reachable at `badboyvee.github.io/BlackHoleeee/<project>/`, and
single-file pages such as `waymo.html` sit at the repository root.
