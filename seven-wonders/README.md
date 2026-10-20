# Seven Wonders — an interactive 3D atlas

The Seven Wonders of the Ancient World gathered on one island, built with
[three.js](https://threejs.org). One HTML file, no build step, no imported models,
textures or sound files — every wonder, surface, sky and sound is generated at runtime.

Open `index.html` in a browser, or serve the folder:

```sh
python3 -m http.server 8000
```

## What you can do

- **Explore.** Orbit the island and fly to any wonder for its story: when and by whom it
  was built, its size, its fate, a carousel of facts and a lifespan bar.
- **Travel through time.** Scrub or play history from 2600 BCE to 1600 CE. Wonders rise
  out of the ground when they are built and crumble into ruins when they fall. The goal:
  find the few decades when all seven stood at once.
- **Hunt for relics.** Seven glowing relics are hidden around the wonders. The journal
  gives a riddle-like hint for each.
- **Face the Oracle.** Eight questions drawn from a bank of 26, with streak bonuses, ranks
  and a saved best score. The camera flies to each answer.
- **Watch the day turn.** Golden hour, night, dawn and midday, with a matching sky, sea,
  stars, moon, fireflies, lit lamps and the Pharos beam at night.
- **Collect achievements** in the traveller's journal; progress is saved in the browser.
- **Take photos** in photo mode, which hides the interface and saves a PNG.

Ships sail around the island, gulls circle overhead and fireworks mark the big moments.
The music (a slow drone and a wandering melody in a Hijaz-like scale), the surf, the wind
and every sound effect are synthesised with the Web Audio API.

## Controls

| input                     | action                          |
| ------------------------- | ------------------------------- |
| drag / pinch / scroll     | orbit and zoom                  |
| click a wonder or its tag | fly to it and read about it     |
| `1`–`7`                   | jump to a wonder                |
| `0` or `Esc`              | return to the overview          |
| `Y`                       | time travel (`Space` to play)   |
| `Q`                       | the Oracle's quiz (`1`–`4` to answer) |
| `T`                       | guided tour                     |
| `N`                       | change the time of day          |
| `P`                       | photo mode                      |
| `L` / `M` / `J`           | labels, sound, journal          |

## Rendering

The scene renders through an `EffectComposer` (HDR target with MSAA, Unreal bloom,
ACES tone mapping). The sky is a small gradient shader whose colours, sun and moon are
interpolated through the day; a PMREM environment map is rebuilt from it as the hour
changes so metal, marble and water pick up its light. The sea uses a procedurally
generated, seamlessly tiling normal map sampled twice at different scrolls, with a foam
shader around the shore.

It is built to stay fast. Static meshes that share a material are merged at load (about 700
geometries become about 160), and the shadow map is redrawn only when the sun moves or a
wonder rises or falls. Phones skip bloom and render straight to the screen. If the frame
rate still drops below about 40 per second, quality steps down on its own: resolution, then
bloom, then resolution again, then shadows. Add `?q=high` or `?q=low` to the URL to pin it.
