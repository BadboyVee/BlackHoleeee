# BlackHoleeee

A sandbox of browser-native 3D experiments built with Three.js. Most have no build step: the
project is an `index.html` you can open directly.

## Projects

### 🕳️ [Event Horizon](portfolio/)

A frontend developer portfolio built around a real-time, ray-traced black hole. Scrolling flies
the camera through one continuous 3D scene, with Lenis smooth scrolling, GSAP scroll animation,
parallax and code-built 3D models. It is written with React, TypeScript, Vite and React Three
Fiber, and also ships pre-built as one self-contained file, `portfolio/portfolio.html`.

**▶ [Open it](https://badboyvee.github.io/BlackHoleeee/portfolio/portfolio.html)** · [source & how to run](portfolio/)

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

### 🏛️ [Seven Wonders](seven-wonders/)

The Seven Wonders of the Ancient World gathered on one island. Travel through time and watch
them rise and fall, hunt for seven hidden relics, take the Oracle's quiz, and watch the island
turn from dawn to night. Synthesised music and sound, ships, gulls and fireworks, all in one file.

**▶ [Play it](https://badboyvee.github.io/BlackHoleeee/seven-wonders/)** · [source](seven-wonders/)

### 🚗 [BMW M5 CS](bmw-m5-cs/)

A procedural BMW M5 CS model rendered in a studio lighting setup.

**▶ [View it](https://badboyvee.github.io/BlackHoleeee/bmw-m5-cs/)** · [source](bmw-m5-cs/)

## Hosting

`netlify.toml` publishes `bmw-m5-cs/` as the Netlify site root. GitHub Pages serves the whole
repository, so each project is reachable at `badboyvee.github.io/BlackHoleeee/<project>/`.
