# Clawd & Jolly

A one-minute 3D short starring **Clawd**, the Claude Code mascot, and **Jolly**, the plush mascot
of Meta's Muse (in blue). No text, no fonts: everything on screen is geometry, shaders and light.

**▶ [Watch it](clawd-and-jolly.mp4)** (1920×1080, 24 fps, 60 s)

## The film

It is night. A cursor blinks on a laptop running Claude Code. The pixels of the Clawd sprite pop
out of the display one by one and assemble into a 3D Clawd, who drops onto the keyboard, hops
across it lighting every key he lands on, leaps to the desk and scuttles to a bowl of moss by the
window. A blue plush creature is asleep there. They startle each other, wave, and boop. Clawd
pulls a voxel out of his own head and plants it; Jolly blows a little fluff onto it, and it grows
into a tree with an orange voxel trunk and blossoms made of Jolly's fur. The blossoms burst on the
music's climax as the sun rises; the two watch the sunrise together, and back on the laptop the
welcome box now shows both of them as pixel sprites.

| shot | time | |
| --- | --- | --- |
| `s01` | 0:00 – 0:17.4 | one take: subpixel macro of the cursor, glide up the session, the sprite's pixels pop out of the screen and assemble |
| `s03` | 0:17.4 – 0:25 | the keyboard: every landing presses keys and leaves an orange backlight ripple |
| `s04` | 0:25 – 0:31 | across the desk and into the moss bowl |
| `s05a–c` | 0:31 – 0:37.4 | the meeting |
| `s06a–b` | 0:37.4 – 0:50.4 | the gift, and the tree |
| `s07a–b` | 0:50.4 – 0:56 | sunrise |
| `s08` | 0:56 – 1:00 | both of them in the welcome box |

`edit.json` is the cut list. Each shot is a module in `src/shots/` whose `update(t)` is a pure
function of time, so any frame can be rendered on its own.

## How it is rendered

There is no GPU in the machine this was made on, so it is an offline renderer built on three.js
running in headless Chromium through ANGLE on Mesa's llvmpipe:

- **Distributed rasterisation** (`src/engine.js`): every frame is the average of 16–24 sub-frames,
  each with its own shutter time, sub-pixel offset, thin-lens aperture position and jittered light
  positions. That gives real motion blur, depth of field, anti-aliasing and soft area-light shadows.
- **Post**: bloom pyramid, AgX tone mapping, split toning, vignette, light chromatic aberration,
  film grain, dithering, and crepuscular rays from the sun.
- **Clawd** (`src/clawd.js`) is the 18×5 block-character sprite from the Claude Code welcome screen
  (`▐▛███▜▌ / ▝▜█████▛▘ / ▘▘ ▝▝`), extruded four voxels deep with recessed glossy eyes, two arms and
  eight crab legs. Every voxel is animated individually.
- **Jolly** (`src/jolly.js`) wears about 130,000 strands of instanced fur (`src/fur.js`), bent by
  gravity, wind, inertia and clumping in the vertex shader, with forward scattering for backlight.
  It has bead eyes, embroidered closed eyes and smile, and rosy cheeks that can blush.
- **The set** (`src/desk.js`): procedural walnut, an aluminium laptop with an LCD shader that
  resolves to RGB subpixels in macro and a real mirror reflection on the glass, a backlit keyboard,
  a speckled glaze bowl with 150,000 strands of moss, sporophytes, ferns and pebbles, fairy lights,
  and a sky with stars, moon, clouds and layered mountains that turns into a sunrise.
- **The tree** (`src/tree.js`) is a voxelised L-system that grows in time with the music and blooms
  in plush blossoms; `src/particles.js` swirls fluff and voxel embers around it.

## Sound

Music: "Silvan Sanctuary" by Matthias "West" Westlund (The Battle for Wesnoth, GPL-2.0-or-later),
cut so the orchestral climax lands on the blossoms. Every effect is a real recording (CC0 Freesound
samples via Sonic Pi, the Moodist library, SND UI sounds), placed on cue times exported from the
animation itself. See [audio/CREDITS.md](audio/CREDITS.md).

## Rendering it yourself

```
npm install
node render/render.mjs --shot s05a --w 960 --h 540 --spp 8 --every 6     # preview one shot
node render/film.mjs --tag final --w 1920 --h 1080 --jobs 3               # the whole edit
audio/fetch-sounds.sh                                                       # sound sources
for s in s01 s03 s04 s06b; do node render/render.mjs --shot $s --cues audio/cues_$s.json; done
python audio/mix.py out/mix.wav
python tools/assemble.py final clawd-and-jolly.mp4 --audio out/mix.wav
```

It needs Chromium with ANGLE on Mesa (`--use-angle=gl-egl`), Node 22, ffmpeg, and Python with
numpy, scipy, librosa and soundfile. The full film takes about five hours on four CPU cores.
