# Event Horizon — a frontend developer portfolio

A scroll-driven portfolio built around a real-time black hole. As you scroll, the camera
flies through one continuous 3D scene: past the hole, out to an orrery of skills, and
finally straight down into the shadow, where the contact button waits.

## What's in it

- **A ray-traced black hole.** `src/three/shaders/blackhole.frag.glsl` bends a light ray per
  pixel around a Schwarzschild black hole. The lensed arcs of the disk and the thin photon
  ring are not painted on; they fall out of the maths.
- **3D models, all made in code.** Code symbols (`</>`, `{}`, `=>`) extruded from JetBrains
  Mono outlines, and an armillary sphere with one ring per skill. Hover a skill in the Stack
  section and its ring lights up.
- **Lenis smooth scrolling**, driven by GSAP's ticker so the page, every scroll animation and
  the 3D camera share one clock.
- **Parallax everywhere.** A scroll-linked camera path, floating 3D objects at different
  depths, a horizontal gallery whose images drift inside their frames, hero lines that slide
  apart, a velocity-reactive marquee and stacking cards.
- **Details.** Preloader that opens like an iris from the black hole, custom cursor, magnetic
  button, line-by-line and word-by-word text reveals, film grain.
- **Care.** Adaptive resolution on slow GPUs, the canvas sleeps when covered, the 3D code is
  split into its own chunk, `prefers-reduced-motion` is respected, and there is a fallback
  when WebGL is missing.

## Stack

React 19 · TypeScript · Vite · Three.js · React Three Fiber · drei · postprocessing ·
GSAP (ScrollTrigger, SplitText) · Lenis · Tailwind CSS 4

## Run it

```bash
npm install
npm run dev        # http://localhost:5173
npm run build      # type-checks, then writes the site to dist/
npm run preview    # serves dist/ on http://localhost:4173
```

## The single HTML file

**`portfolio.html`** is the whole site in one file: scripts, styles, fonts and images are all
inlined. Double-click it and it runs, with no server, no install and no internet connection.
It can also be uploaded as-is to any host.

It is a build of the code in `src/`, so do not edit it by hand. After changing the site,
regenerate it:

```bash
npm run build:single   # rewrites portfolio.html
```

## Make it yours

Every word and link on the site lives in **`src/content.ts`**: name, intro, projects, skills,
contact address. Set `email` there to turn the contact button into a mail link.

- Project screenshots go in `src/assets/work/`; import one at the top of `content.ts` and set
  it as the project's `image`. A project without one gets a generated poster.
- The camera path is in `src/lib/rig.ts`: one pose per section, measured from the real page.
- Colours and fonts are tokens at the top of `src/styles/index.css`.
- `npm run glyphs` rebuilds the 3D code symbols (edit `CHARS` in `scripts/make-glyphs.mjs`).

In development, `/?dpr=0.5&steps=90&snap&nointro` lowers the render cost and skips the
intro, which helps on slow machines.

## Deploy

The quickest route is `portfolio.html`: it is one file and works anywhere.

For the regular build, `dist/` is static and uses relative URLs, so it works on any host and
from any sub-folder. `netlify.toml` is ready: create a Netlify site from this repo with the
base directory set to `portfolio`.
