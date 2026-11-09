# Event Horizon: a creative developer portfolio

A portfolio site for a creative frontend developer, built around a real-time,
ray-marched **black hole**. Light bends around it as you move the mouse, and
scrolling the page is a slow orbit that ends with a dive toward the event horizon.

## What's in it

- **Black hole backdrop**: a full-screen GLSL shader that traces light through
  curved spacetime (Schwarzschild orbit equation). It draws the shadow, the photon
  ring, an accretion disk with Doppler beaming and redshift, and a lensed starfield.
  Each section has its own camera "shot"; scrolling blends between them.
- **3D models** in one shared WebGL canvas (drei `View`):
  - a laptop that opens on scroll and shows each project's screen
  - "gravity orbs" for the toolkit: physics spheres you push with the cursor,
    and a click sets off a big bang
  - a glass knot with chrome rings
- **Lenis smooth scrolling**, driven from one GSAP ticker that also renders the 3D,
  so models never lag the page.
- **Parallax and motion**: scroll-scrubbed word highlighting, split-text reveals,
  a velocity-reactive marquee, stacking process cards, hero letters that drift
  apart and stretch on hover (variable font width axis).
- **Interface details**: preloader with real load progress, custom cursor with
  context labels, magnetic buttons, rolling-text links, hide-on-scroll header,
  full-screen mobile menu, live local clock, copy-email button, back-to-top
  progress ring, film grain.
- **Adaptive quality**: the GPU tier sets shader steps and resolution, and frame
  timing lowers or raises resolution while the page runs. Reduced-motion users
  get native scrolling and no scroll animations.

## Tech stack

Vite 8 · React 19 · TypeScript 7 · Tailwind CSS 4 · three.js · React Three Fiber ·
drei · GSAP (ScrollTrigger, SplitText) · Lenis · Zustand · oxlint

## Make it yours

All text lives in **`src/content/site.ts`**: name, role, projects, toolkit,
process, experience, email and social links. The page title and preview tags
are filled from the same file at build time.

## One-file version

**[`portfolio.html`](portfolio.html)** is the whole site in a single file (about 2 MB):
code, styles and fonts are all inside. Download it and double-click to open, with no
install, server or internet connection needed. Rebuild it after editing with
`npm run build:single`.

## Run it

```bash
cd portfolio
npm install
npm run dev        # http://localhost:5173
npm run build      # production build in dist/
npm run preview    # serve the build
npm run typecheck && npm run lint
```

## Deploy

The build is a static folder (`dist/`) with relative paths, so it works on any
static host or sub-path.

- **Netlify**: create a site from this repo with base directory `portfolio`;
  `netlify.toml` has the build settings.
- **Anywhere else**: run `npm run build` and upload `dist/`.

## Files

```
src/content/site.ts                 all copy and links
src/App.tsx                         page layout and the scroll-driven camera shots
src/sections/Sections.tsx           hero, about, work, toolkit, process, experience, contact
src/components/ui.tsx               preloader, cursor, header/menu, magnetic, marquee, grain
src/three/backdrop/                 black hole shader, camera shots, canvas
src/three/Scene.tsx                 laptop, gravity orbs, glass sculpture
src/lib/scroll.ts                   Lenis + the single animation loop
src/lib/quality.ts                  GPU tier and adaptive resolution
```
