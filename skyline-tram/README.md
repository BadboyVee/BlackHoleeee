# Skyline Tram

A single-file 3D browser game built with Three.js. You drive a retro aerial tram along a
continuous rail loop between two islands floating above a sea of clouds — Saltlight Terminus
and Mango Tide — while trying to keep your passengers comfortable enough to tip.

Warm, low-poly, dusk-into-night. No build step, no install: it's one `index.html`.

## Play

**https://badboyvee.github.io/BlackHoleeee/skyline-tram/**

Or download [`index.html`](index.html) and open it in any modern browser. That's the whole game —
Three.js loads from a CDN, so nothing else is needed.

## Controls

| Input | Action |
| --- | --- |
| `W` / `↑` | Power (accelerate) |
| `S` / `↓` | Brake |
| `←` / `→` (or `A` / `D`) | Cycle camera: chase, driver's cab, scenic |
| On-screen POWER / BRAKE buttons | Same as above — hold to apply (works on touch) |
| 🛠 Cloudworks button | Enter the workshop to swap parts on the tram |

## What's in it

- **A real track, not a path on a plane.** The rail is a closed `CatmullRomCurve3` loop with
  straights, climbs, descents, an elevated switchback, and a long pylon-supported bridge across
  the sea. The tram is positioned and oriented from the curve's tangent every frame.
- **Passenger comfort.** Sudden acceleration, hard braking, taking curves too fast, and the
  crosswind stretch over the bridge all drain comfort. Arrive smooth and you get a tip bonus
  (up to +75) and build a streak; arrive rough and the streak breaks.
- **Station stops.** Roll into a platform and the tram docks automatically, doors swing open,
  passengers get off and on (capacity 16), and you're sent on to the next stop.
- **The Cloudworks workshop.** An isometric view where you fit a luggage rack, lanterns, or a
  vine garland. Each swap runs a progress bar and visibly changes the tram before it rolls back
  out onto the line.
- **Feel.** Pedal inertia so power spools up instead of snapping on, body roll through corners,
  a gentle sway at speed, and track-clack audio tied to distance travelled.

## The prompt

This was built in one go from the prompt below. Reuse it, remix it, aim it at a different
setting — it holds up well as a template for "describe a whole small game at once."

```
Create a single-file HTML/JS 3D game (Three.js) that can be played directly in the browser,
with a warm, low-poly but polished indie game style, evoking the feel of a Ghibli seaside town
combined with the smoothness of Zelda's mine cart tracks.

【Core Gameplay】
The player drives a retro aerial tram, traveling between islands floating above a sea of clouds
and the ocean surface.
- The track is a continuous 3D railway, featuring straight sections, uphill slopes, downhill
  slopes, elevated curves, and long bridges across the sea
- Controls: W to accelerate (Power), S to brake (Brake), left and right for fine-tuning or
  switching the view
- Real-time display: speed in km/h, number of passengers on board (e.g., 12/16 aboard), road
  conditions (Steady / Crosswind)
- Passenger comfort system: sudden acceleration, hard braking, taking corners too fast, and
  crosswinds all reduce "leg comfort"; arriving at the destination smoothly earns bonus points
  (e.g., +75 at arrival)
- Streak: driving too bumpily will trigger the message "Streak broken. Find your balance to
  rebuild your tips."
- Arrive at the station, open the doors for passengers to get on and off. On the platform,
  there are townsfolk queuing up, with subtitles such as "Doors opening - Mango Tide,"
  "Please wait…"

[World and Stations]
At least two routes/two islands:
1. Saltlight Terminus
2. Mango Tide
The island is a rocky island floating above the clouds, with small Mediterranean/Southern
European-style houses with red-tiled roofs, a lighthouse, a dock, green trees, streetlights,
and warm yellow windows at night. In the distance, there are more floating islands and circling
orbits. The sky is a blue-purple gradient from dusk to night, with stars and thick clouds, and
below is azure seawater.

[Tram Exterior]
Retro tram: dark green body, wood-colored chassis, curved glass windows, roof luggage, green
awning/vine decorations, and various passengers sitting inside. While moving, there is a slight
swaying motion and a sense of track sounds (which can be conveyed with simple sound effects or
visual cues).

[Scene 2: Workshop Modification]
Switch to the top-down isometric view of the workshop "Cloudworks / Oliver Cloudworks / Oliver's
home island." Players can swap parts for the tram, with an interface like an upgrade pop-up:
- Hearth leaves — Lifting the old part
- Little Companion — Preparing the tram
Progress bar + "Sit back and watch the workshop."
Changes to the tram's appearance after modification (e.g., green roof, added luggage rack,
lanterns, vines), then it drives out of the workshop, subtitles "All aboard." / "Next stop: the
Coastal Line."

[UI]
Clean modern casual game UI: destination and currency/streak in the top-left, speed bar and
Power/Brake buttons at the bottom, comfort progress bar connecting the two station names. No
clutter, don't make it horror or cyberpunk.

[Technical Requirements]
- Single file or minimal files, Three.js
- Use curves for the track (CatmullRom, etc.) so the tram follows the rails, camera follows with
  a slight rail feel
- Simple physics feel: acceleration inertia, braking deceleration, body roll when cornering
- On mobile, try to also support tap to accelerate/brake
- Readable code, with comments, playable as soon as it's opened.
```

## Notes if you want to hack on it

Everything lives in `index.html` — HUD markup and CSS at the top, then one ES module with the
scene, world builders, track, tram, physics, and workshop. A few things worth knowing before you
change them:

- `Object3D#lookAt` faces a generic object with local **+Z** toward the target (unlike a camera,
  which uses -Z). The tram is built and the chase camera is offset on that +Z-forward convention.
- `renderer.useLegacyLights = true` keeps the old 0–1 light intensity scale; without it the whole
  scene renders nearly black at these values.
- Track curvature is measured per unit of **arc length**, not per unit of the curve's `u`
  parameter — the comfort system reads those numbers directly, so the conversion matters.
- Big background scenery (sky, ocean, clouds, islands, track) sits on a separate render layer so
  the workshop's isometric camera doesn't pick up the enormous ocean plane.

Track shape is just a list of control points near the top of the module — move them and the
rails, sleepers, and bridge pylons all regenerate around the new curve.
