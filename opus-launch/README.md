# Opus 5.5 — Launch Film

A remake of the 20-second Opus 5.5 launch film, built in real time with Three.js. Every frame
is generated in the browser from shaders and JavaScript, except the galloping horse: its 15
frames are rendered in Blender (in [`horse/`](horse)). There's also a [video file](#video-file) to post.

**▶ [Watch it](https://badboyvee.github.io/BlackHoleeee/opus-launch/)** · or open
[`index.html`](index.html) directly. There's no build step; Three.js r159 ships next to it as `three.min.js`, so the film needs no network (the Newsreader font falls back to Georgia offline).

## The film

It follows the original cut for cut: all 38 shots, with every cut measured from the source
video at 25 fps.

| Time | What happens |
| --- | --- |
| 0.00 – 1.24 s | A planet's horizon: a dark limb, a thin orange band and a pale blue atmosphere |
| 1.24 – 8.12 s | Rapid cuts of macro "horizons": a glassy rim of bubbles over amber, an orange sphere with one dark splat, bread crust, red-orange granules on teal, blue crackle glaze, a chalk blueprint, white stone with ink-black cavities, a leaf, a maroon ridge of teeth on teal, pink gel with red beads, Greek-key pottery, and a leather edge with red and green thread |
| 8.12 – 8.72 s | **The horse.** A real horse, a bay, gallops along the crest of a grassy hill at golden hour, with the camera tracking it. It's rendered in Blender, one frame per film frame. The original shows a hand-coloured phenakistiscope print here; that version, drawn in 2D, is still in the code as a fallback |
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
- **The horse is rendered in Blender.** It's a 3D scan of a real horse (the Cyberware horse),
  rigged and driven through a gallop solved in the side plane. Hooves in stance stay planted
  while the body bobs and pitches, and the swinging legs follow keyed joint angles. Cycles
  renders it with motion blur and depth of field:
  - a bay coat with black legs
  - a mane and tail made of hair curves that wave in the wind
  - particle grass on a hill that rolls under the horse at 9.5 m/s
  - fields and a tree line fading into the haze, under a low golden sun

  The scripts are in [`horse/blender`](horse/blender). The film shows the frames over the
  whole screen, and the hoofbeats in the score land on this gallop's footfalls.
- **The original's drawn horses are the fallback.** If the frames can't load, the film draws
  the phenakistiscope print instead. The foxed paper and the green arches (parabolas, one every
  2000 px, wobbling from frame to frame as the original's disc does) are in the backdrop
  shader. The horses are drawn in canvas 2D and multiplied onto the paper. Each leg is a
  two-bone chain solved by inverse kinematics along an eight-pose stride read off the print.
- **Beads and droplets** are an `InstancedMesh`, placed on the projected horizon. The red beads
  sit where the original's do across the frame.
- **A few details are drawn in 2D** over the frame, like the horses: the leather's threads and the
  ink shot's pen-drawn grass. The collage's cut-paper shapes are traced from the original and laid
  out where they were.
- **Typography** is drawn into a canvas texture inside the WebGL frame. "discover" is laid out
  letter by letter along the projected horizon.
- **Sound** (optional) is a small WebAudio score: pad chords per section, ticks on every cut,
  hoofbeats on the horse's footfalls, plucks under "discover", and bells on the title cards.
  It's scheduled against the same clock as the picture.

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

## Video file

[`export/`](export) renders the film to an MP4 you can post: 1920 × 1080, 25 fps, H.264 and
AAC, 22.6 s long, about 26 MB (a two-pass encode at 9 Mbit/s). It opens on a preview card: three of the film's shots side by side, with the
line split across them ("There’s" · "more to" · "discover."). That makes the card the video's
thumbnail wherever it's posted. After 1.6 s it dissolves into the film. The card is also
embedded in the file as cover art.

```sh
cd opus-launch/export
npm install playwright                      # headless Chromium; software GL is fine
node film.js frames out/frames 0 500        # every frame of the film
node film.js score out/score.wav            # the score, rendered offline
node film.js stills card wall=14.08 rock=13.48
node film.js card out/card.png              # the preview card
./make_mp4.sh out/opus-5-5-remake.mp4       # needs ffmpeg and the horse's frames (below)
```

`film.js` opens the film with `?export`. That compiles one shader program per shot, which lets
software GL render a 1080p frame in about 2 s.

To rebuild the horse's frames, you need Blender 4.5's Python module (`pip install bpy`).
1. Download the [horse scan](https://raw.githubusercontent.com/alecjacobson/common-3d-test-models/master/data/horse.obj)
   into `horse/blender`.
2. In that folder, run `python rig.py`.
3. Then run `python scene.py out 1920 1080 32`. Each frame takes about 3 minutes on four CPU
   cores.

The MP4 uses the full-size PNGs. The web film uses 1280 × 720 JPEG copies, stored in `horse/`.
