# Opus 5.5 — Launch Film

A remake of the 20-second Opus 5.5 launch film, built in real time with Three.js. It uses no
video files or images. Every frame is generated in the browser from shaders and JavaScript.

**▶ [Watch it](https://badboyvee.github.io/BlackHoleeee/opus-launch/)** · or open
[`index.html`](index.html) directly. There's no build step; Three.js r159 ships next to it as `three.min.js`, so the film needs no network (the Newsreader font falls back to Georgia offline).

## The film

It follows the original cut for cut: all 38 shots, with every cut measured from the source
video at 25 fps.

| Time | What happens |
| --- | --- |
| 0.00 – 1.24 s | A planet's horizon: a dark limb, a thin orange band and a pale blue atmosphere |
| 1.24 – 8.12 s | Rapid cuts of macro "horizons": a glassy rim of bubbles over amber, an orange sphere with one dark splat, bread crust, red-orange granules on teal, blue crackle glaze, a chalk blueprint, white stone with ink-black cavities, a leaf, a maroon ridge of teeth on teal, pink gel with red beads, Greek-key pottery, and a leather edge with red and green thread |
| 8.12 – 8.72 s | **The horses.** A close-up of a hand-coloured phenakistiscope disc: a chestnut horse and its rider gallop on a green arch, one figure per frame |
| 8.72 – 10.68 s | **There’s**, over a sepia smear, a tomato, a neon herringbone, an engraving and a prismatic rim |
| 10.68 – 12.48 s | **more to**, over a sunset, a ridge against the sky, a tapestry under denim, neon bands and lace |
| 12.48 – 15.96 s | **discover**, bent along the horizon, over agate, crayon, golden moss, white rock, plaster half in shadow, weathered wood, a paper collage, plant cells, rust-red dust, ruled lines, ink, white fur and mushroom gills |
| 15.96 – 20.05 s | **Opus 5.5**, then **✳ Claude** at 17.28 s. From 18.28 s the whole frame rises until the horizon lands on the opening frame, so the film loops |

The words match the original's size. Each one is fitted to its measured width, so the layout
holds whatever serif the browser uses. The words step up in size at every cut: "There’s" goes
from 11% to 17% of the frame's width, and "discover" from 30% to 43%. The title cards are
about 20% of the width. In portrait the frame is cropped a little at the sides, so the words
stay large on a phone.

## How it's built

- **Most shots are the same 3D object.** It's the rim of a sphere seen from just above its
  surface. Three numbers fitted to each shot of the original place the sphere: `alpha` (its
  angular size, which sets how curved the horizon is), `rimY` (where the horizon sits in the
  frame) and `cx` (where its highest point sits across the frame).
- **One spherical cap, spent where it counts.** The cap's vertices are stored as (angle,
  depth) pairs and bent into a sphere in the vertex shader. The mesh always stops just past the
  horizon, so fur, rock, moss and the maroon ridge's teeth can break the silhouette with real
  displacement.
- **~35 procedural materials** live in one fragment shader (simplex noise, fbm, Voronoi cells,
  a bit-packed Greek key). Each works in "rim coordinates": distance along the horizon and
  distance in from it. Bump shading uses screen-space derivatives.
- **The backdrop shader knows where the sphere is.** That lets it draw rim glows, the
  prismatic halo, and the planet's defocused limb and atmosphere for the opening and closing
  shots.
- **The horses are drawn, not modelled.** The foxed paper and the green arches (parabolas,
  one every 2000 px, wobbling from frame to frame exactly as the original's disc does) are in
  the backdrop shader. The horses are drawn in canvas 2D and multiplied onto the paper like
  watercolour and ink. Each leg is a two-bone chain solved by inverse kinematics along an
  eight-pose stride read off the print. The fore knees fold forward, the hocks fold back, and
  the neighbouring figures on the disc peek in at the edges.
- **Beads and droplets** are an `InstancedMesh`, placed on the projected horizon. The red beads
  sit where the original's do across the frame.
- **A few details are drawn in 2D** over the frame, like the horses: the leather's threads and the
  ink shot's pen-drawn grass. The collage's cut-paper shapes are traced from the original and laid
  out where they were.
- **Typography** is drawn into a canvas texture inside the WebGL frame. "discover" is laid out
  letter by letter along the projected horizon.
- **Sound** (optional) is a small WebAudio score: pad chords per section, ticks on every cut,
  hoofbeats under the horses, plucks under "discover", and bells on the title cards. It's
  scheduled against the same clock as the picture.

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
