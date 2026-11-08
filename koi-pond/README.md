# Koi Pond

A living koi pond built with [three.js](https://threejs.org). It is one HTML file with no build
step and no imported models or textures: the terrain, rocks, plants, fish and water are all
generated when the page loads.

Open `index.html` in a browser, or serve the folder with `python3 -m http.server 8000`.

## What's in it

- **14 koi of different varieties.** Kohaku, Sanke, Showa, Ogon, Asagi, Tancho, Kujaku,
  butterfly-finned koi and more. Each has its own size, temperament and pattern. Their bodies
  bend into turns, their tails beat faster when they speed up, and their pectoral fins paddle
  when they slow down. They glide, school loosely, linger near the waterfall and rise to the surface now and then.
- **Feeding.** "Feed the koi" (or `F`) tosses a handful of pellets onto the water where you
  are looking. The koi notice them (nearby fish first), race over, tilt up to the surface and
  gulp each pellet with their mouths pushed out, splashing as they jostle for it.
- **Water.** Refraction through a depth buffer with colour absorption by depth, planar
  reflections, caustics on the floor and fish shadows below. A ripple simulation runs on the
  GPU and is fed by the waterfall, food, feeding fish, insects and your taps. Lily pads,
  leaves and pellets bob on those ripples.
- **Around the pond.** A two-layer waterfall with spray and mist, mossy rocks, lily pads and
  lotus flowers, reeds and cattails, swaying grass, ferns, azaleas, Japanese maples that
  drop leaves onto the water, pines, bamboo, a stone lantern, dragonflies that dip to the
  surface, butterflies, water striders and rising bubbles.

## Controls

| input                 | action                                  |
| --------------------- | --------------------------------------- |
| drag / pinch / scroll | orbit and zoom                          |
| right-drag            | pan                                     |
| tap the water         | ripple (nearby koi dart away)           |
| Feed the koi / `F`    | throw food                              |

The camera drifts around on its own after 25 seconds without input. Add `?q=low` or `?q=high`
to the URL to pin the quality level.
