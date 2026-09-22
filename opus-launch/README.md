# Opus 5.5 — Launch Film

A remake of the 20-second Opus 5.5 launch film, built in real time with Three.js. It uses no
video files or images. Every frame is generated in the browser from shaders and JavaScript.

**▶ [Watch it](https://badboyvee.github.io/BlackHoleeee/opus-launch/)** · or open
[`index.html`](index.html) directly. There's no build step; Three.js r159 ships next to it as `three.min.js`, so the film needs no network (the Newsreader font falls back to Georgia offline).

## The film

It follows the original cut for cut (the cut times were measured from the source video at 25 fps):

| Time | What happens |
| --- | --- |
| 0.0 – 1.2 s | A planet's horizon: a dark limb, a thin orange band and a pale blue atmosphere |
| 1.2 – 8.7 s | Rapid cuts of macro "horizons": amber and bubbles, bread crust, a blueprint, a leaf, a pink gel with red droplets, Greek-key pottery, a thermal image, crayon and moss |
| 8.7 – 12.5 s | **There’s** … **more to**, over a tomato, an engraving, a prismatic rim, a sunset, fabric, bands and lace |
| 12.5 – 15.8 s | **discover**, bent along the horizon, cutting every ~0.25 s through agate, rock, wood, a collage, plant cells, ruled lines, ink, fur and mushroom gills |
| 15.8 – 20 s | **Opus 5.5**, then **✳ Claude**. The horizon then rises back to the opening frame, so the film loops seamlessly |

## How it's built

- **Every shot is the same 3D object.** It's the rim of a sphere seen from just above its
  surface. A per-shot `alpha` (the sphere's angular size) and `rimY` (where the horizon sits on
  screen) place the sphere, so the horizon lands in the same spot at any aspect ratio.
- **One spherical cap, spent where it counts.** The cap's vertices are stored as (angle,
  depth) pairs and bent into a sphere in the vertex shader. The mesh always stops just past the
  horizon, so fur, rock and moss can break the silhouette with real displacement.
- **~25 procedural materials** live in one fragment shader (simplex noise, fbm, Voronoi cells,
  a bit-packed Greek key). Each works in "rim coordinates": distance along the horizon and
  distance in from it. Bump shading uses screen-space derivatives.
- **The backdrop shader knows where the sphere is.** That lets it draw rim glows, the
  prismatic halo, and the planet's defocused limb and atmosphere for the opening and closing
  shots.
- **Beads and droplets** are an `InstancedMesh`, placed on the projected horizon.
- **Typography** is drawn into a canvas texture inside the WebGL frame. "discover" is laid out
  letter by letter along the projected horizon.
- **Sound** (optional) is a small WebAudio score: pad chords per section, ticks on every cut,
  plucks under "discover", and bells on the title cards. It's scheduled against the same clock
  as the picture.

## Controls

| Input | Action |
| --- | --- |
| `Space` | Pause / play |
| `R` | Restart |
| `M` | Sound on / off |
| `H` | Hide the controls |
| **Record** | Captures one full loop, with sound, to `opus-5-5-launch.webm` |
| `?t=12.6` | Freezes on a single moment (for stills) |

> Heads up: like the original, the middle of the film cuts rapidly (up to ~4 cuts a second).
