# WALL·E — Interactive Articulation Rig

A single-file, browser-native Three.js showcase: a fully articulated WALL·E you can drive,
pose, tear down and re-light. No build step, no assets on disk — the robot, every material
and all three environments are generated procedurally at boot.

**▶ [Open it](https://badboyvee.github.io/BlackHoleeee/wall-e/)**

## Controls

| Input | Action |
| --- | --- |
| `W` `A` `S` `D` | Drive the tracks (tank steering — turns on the spot) |
| `Shift` | Boost |
| Drag | Orbit the camera |
| Scroll / pinch | Zoom |
| `1`–`8` | Behaviour routines |
| `Q` `E` `Z` `X` `C` | 3/4 · front · side · top · macro |
| `P` | Hold the plant |
| `O` | Auto-orbit |
| `R` | Reset position |
| `H` | Hide the interface |

## What's in the panel

- **Camera** — five framed presets, auto-orbit, follow (keeps the chassis framed while you
  drive), eye contact (he tracks the lens, and crosses his eyes when you get close) and bloom.
- **Environment** — *Studio* (cyclorama, three-point rig, polished floor), *Earth* (graded
  dust sky, scattered debris, trash towers, airborne motes, drive dust) and *Blueprint*
  (datum grid with a glowing wire overlay of every part).
- **Behaviour routine** — idle, curious, wave, scan, EEE-VAH, sad, compact and sleep. Each
  one drives the whole rig: neck, head, both arms, lids, gaze, body lean and tracks.
- **Servo overrides** — neck extension, shoulder lift, gripper and drive gearing. An
  untouched slider mirrors the live joint; dragging one pins that servo until you pick a new
  routine or hit reset.
- **Paint & finish** — six liveries retinting the same weathering maps.
- **Teardown** — an exploded view that separates him into his individual mechanical parts
  with leader lines, plus shadow and plant toggles.
- **Telemetry** — drive speed, heading, routine, servo load, solar charge and framerate.

## How it works

Everything lives in `index.html`, in numbered sections:

1. **Procedural texture lab** — a seeded value-noise/fBm stack paints the albedo, roughness
   and bump maps: dust film, bleached streaks, rust blooms, paint chips and scratches. Paint
   maps are authored greyscale so a livery change is a single `color.set()`.
2. **The robot** — tracks are built from the external-tangent geometry of two pulleys, so
   the frame silhouette, the instanced tread links and the sprocket wrap all share one
   parametric path. The neck is a three-stage telescopic mast; each eye is a barrel with a
   lens dome and two half-dome lids that meet in the middle.
3. **The rig** — every joint is a named scalar channel. Routines only write targets; the
   channels chase them with per-channel damping, which is what makes the motion read as
   servo-driven rather than snapped.
4. **Teardown** — parts are tagged at build time with an explode direction; the pass
   recomposes `position = base + dir × amount` each frame, so animation and teardown coexist.

Rendered with ACES filmic tone mapping, a 4× multisampled HDR target, PCF soft shadows,
an image-based lighting probe and a subtle bloom pass. The projection is shifted left by
the width of the control panel so the subject stays centred in the part of the frame you
can actually see.

## Prompt

> using the uploaded image as the exact visual and UI reference, build an interactive 3d
> WALL-E experience in three.js. recreate WALL-E as a detailed, clean 3d model with his
> weathered yellow metal body, tank tracks, binocular eyes and mechanical arms. match the
> reference's cinematic full-screen presentation with WALL-E large in the center and a sleek
> dark control panel on the right. add camera controls for 3/4, front, side, top and macro
> views, auto-orbit and follow modes, multiple environments including studio, earth and
> blueprint, and interactive behaviour buttons for idle, curious, wave, scan, sad, compact
> and sleep. make every behaviour visibly animate the character — he should wave his arm,
> look around, turn his head and body, move his tracks, react with his eyes and compact
> himself. add sliders for neck extension, shoulder lift, gripper movement and drive gearing,
> plus an exploded-view slider that smoothly separates WALL-E into his individual mechanical
> parts and brings them back together. let me drive him around with WASD and orbit/zoom the
> camera with the mouse. add selectable body color variants and different
> backgrounds/environments. use realistic PBR materials, sharp geometry, soft cinematic
> shadows, reflections, bloom, warm atmospheric lighting and extremely crisp rendering. the
> final result should feel like a premium interactive 3d product showcase, not a basic
> three.js demo.
