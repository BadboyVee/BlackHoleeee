# Opus 5 — the launch film in three dimensions

The same eight seconds as [`../launch-film/`](../launch-film/), rebuilt in Three.js: the eggs are
now real geometry, lit, casting soft shadows onto paper, with a camera you can drag.

Still no images, no models and no scans — every shell is painted into a canvas at startup and
wrapped onto a solid of revolution. Three.js itself loads from a CDN, so unlike the 2-D cut this
one needs a network connection.

## Watch

**https://badboyvee.github.io/BlackHoleeee/launch-film-3d/**

| Input | Action |
| --- | --- |
| Drag the frame | Look around |
| Click the frame, or `space` | Play / pause |
| `←` `→` | Seek |
| `r` | Recentre the camera |
| `l` · `f` | Loop · fullscreen |

## What is actually in the scene

- **The eggs are lathed.** An ovoid profile — `x = b·sin t·(1 − k·cos t)`, `y = −a·cos t` — revolved
  through `LatheGeometry` into a solid of revolution, 56 profile points by 48 segments. The
  profile runs pointed pole to blunt pole so the winding faces outward and texture `v` runs with
  the shell. (Reverse it and you render the inside of the egg, which is a very convincing way to
  waste an afternoon.)
- **The shells are painted at startup.** One canvas per egg: mottled ground, a grey-lilac
  underlayer, dark blotches smoothed through their own midpoints, then fine peppering — pigment
  biased toward the blunt pole, as on a real egg. Because `u` wraps around the shell, every mark
  is stamped three times, left of the seam, on it and right of it, so the wrap is invisible. The
  sheet is 1 : 0.7 because the pole-to-pole arc is shorter than the circumference; that keeps the
  markings round on the surface rather than stretched.
- **The same painting becomes relief.** Desaturated and contrast-shifted into a bump map, so the
  blotches sit very slightly proud of the shell.
- **Matte, not glossy.** `MeshLambertMaterial`: an eggshell in a naturalist's plate has no
  specular highlight, and a hotspot on every egg reads as plastic immediately.
- **Light.** A warm key from up-left casting soft (PCF) shadows, a hemisphere for bounce, a cool
  fill from the right. No tone mapping — a flat response suits a printed plate.
- **The paper** is a plane with its own generated texture: uneven ageing, pale flecks in the pulp.

## Choreography

Measured off the original clip and shared with the 2-D cut: eggs arrive from t≈0.08 to t≈2.9 on a
24fps beat, each dropping a little and settling; the finished numeral holds until t=5.0; then a
hard cut to the wordmark, held to t=8.0, and it loops. The arrivals are quantised to 24fps to
keep the stop-motion cadence, while the camera drift stays smooth.

## Note

Unofficial, and built from scratch — none of the original artwork is reused.
