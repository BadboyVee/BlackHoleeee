# M5 CS — a car modelled in code

An interactive 3D BMW M5 CS (F90) built with [three.js](https://threejs.org). One
HTML file, no build step, no imported meshes or textures — every surface is
generated at runtime.

Open `index.html` in a browser, or serve the folder:

```sh
python3 -m http.server 8000
```

Drag to orbit, scroll (or pinch) to zoom. The dock switches paint, jumps to a
camera preset, and toggles auto-orbit, wheel spin and the lamps.

## How the shape is made

The body is a **loft**: a closed cross-section is swept along the length of the
car and stitched into a mesh. Each section is a Catmull-Rom curve through eleven
control points, and its shape at a given `x` comes from three 1-D profiles:

| profile      | what it controls                                  |
| ------------ | ------------------------------------------------- |
| `topY`       | bonnet line → window sill → boot lid              |
| `baseBotY`   | the rocker, before the arches are cut into it     |
| `halfW`      | width, peaking over each axle                     |

Wheel arches are cut by raising the lower edge along an ellipse centred just
above the rocker, so the arch tips land on the sill line instead of stepping
down to it. A `tipFactor` rolls each section inward over the last 150 mm, which
turns the ends of the loft into rounded bumper faces rather than a flat slab.

The cabin is a second, narrower loft carrying a carbon roof panel, a tubular
window surround and the glass. Wheels are a lathed tyre section plus twenty
extruded Y-spoke arms.

Details (lamps, grilles, intakes, splitter, diffuser) are **mounted onto the
surface** rather than positioned by hand: `surfaceX` and `surfaceZ` probe the
generated cross-sections to find where the body actually is at a given point, so
a bumper insert follows the curve of the fascia in plan instead of protruding at
the centre and sinking at the corners.

Lighting is a canvas-painted equirectangular studio used as `scene.environment`,
which is what gives the paint its long highlights; three directional lights add
the key, rim and fill.

## Dimensions

Real F90 CS figures, at 1 world unit = 1 metre: 4965 long, 1903 wide, 1466 tall,
on a 2982 wheelbase with 885 mm of front overhang and 1098 mm of rear. Wheels are
20-inch, 275-section front and 285 rear.

## The prompt

Built with [Claude Code](https://claude.com/claude-code). The whole thing started
from one line:

> Build a 3d model of BMW M5 CS using three js

followed by a single note once it was running:

> Add more lighting to the background, too dark

Copy the file, copy the prompt, do your own — both are here for the taking.

## Notes

three.js r160 loads from a CDN via import map, with a mirror as fallback. Badging
is deliberately generic — no manufacturer roundel is reproduced.
