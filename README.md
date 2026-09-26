# BlackHoleeee

A sandbox of single-file, browser-native 3D experiments built with Three.js, plus motion-design films
rendered from code. No build step for viewing any of them — every project is an `index.html` you can open
directly.

## Projects

### 🎬 [Motion — every frame is code](motion/)

Two motion-design films at 1920×1080, 60 fps, written entirely in Python: **THE FRONTIER**, a fight-card reel
for Astra 6, Gemini 3m and Fable 5.1, and a tribute to Dario Amodei. Pictures are drawn with skia, the 3D
plates are rendered with Blender Cycles, and every sound is synthesised with numpy.

**▶ [Watch them](https://badboyvee.github.io/BlackHoleeee/motion/)** · [source & notes](motion/)

### 🌊 [Saltwind Cove](ocean/)

A WebGPU ocean you can walk, swim, sail and dive in. It has FFT waves, breakers that curl and
plunge on a sandbar, a boat with a real Kelvin wake, a fishing village, a reef and a humpback
whale, all built with three.js TSL, plus volumetric clouds, a physical sky and real recorded
sound.

**▶ [Open it](https://badboyvee.github.io/BlackHoleeee/ocean/)** · [source](ocean/) · [prompt](ocean/PROMPT.md)

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
