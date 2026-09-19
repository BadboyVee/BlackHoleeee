# BlackHoleeee

A sandbox of single-file, browser-native experiments. No build step in any of them — every
project is an `index.html` you can open directly.

## Projects

### 🎞️ [Claude Opus 5 — launch film](launch-film/)

A 66-second launch film that runs in a browser tab. Every frame is computed live in canvas 2D
and the score is synthesised in Web Audio: no images, no video, no libraries. Scrubbable by
chapter, with the mark, the particle field and the wordmark all drawn from geometry.

**▶ [Watch it](https://badboyvee.github.io/BlackHoleeee/launch-film/)** · [source](launch-film/)

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
