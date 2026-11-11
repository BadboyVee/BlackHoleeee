# BlackHoleeee

A sandbox of single-file, browser-native 3D experiments built with Three.js. No build step in
any of them — every project is an `index.html` you can open directly.

## Projects

### 🌸 [Sakura](sakura/)

A cherry tree in full bloom, through a whole day. The tree is grown branch by branch; its blossoms,
bark and turf are modelled as real geometry in Blender and rendered with Cycles into the textures
the page uses. A physical sky lights it from dawn to moonlit night (run the day, or scrub the hour),
with falling petals, a lens with depth of field, and an export of the whole tree back to Blender.

**▶ [Open it](https://badboyvee.github.io/BlackHoleeee/sakura/)** · [source](sakura/)

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
