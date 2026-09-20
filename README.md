# BlackHoleeee

A sandbox of single-file, browser-native 3D experiments built with Three.js. No build step in
any of them — every project is an `index.html` you can open directly.

## Projects

### 🚙 [Waymo Jaguar I-PACE](waymo.html)

A procedurally modelled Waymo robotaxi you can orbit, repaint, relight, drive and take
apart. The body is a single lofted surface driven by keyframed section profiles, with real
wheel-arch and window openings cut into the skin, tinted glazing, a trimmed cabin and the
5th-generation Waymo Driver: roof fairing with the spinning LiDAR dome and camera collar,
front wing pods, mirror cameras and bumper perimeter housings.

Six paint finishes, four lighting scenes (studio, noon, dusk, noir), a drive mode that spins
the wheels and weaves the steering, and three dissection tools - ghost the skin, split the
car into its six layers, or slice it with a live cutaway to look at the seats, the
skateboard battery, the drive units and the cooling pack.

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
