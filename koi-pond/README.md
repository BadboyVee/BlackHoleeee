# Koi Pond

A living koi pond built with [three.js](https://threejs.org) in one HTML file. There is no build
step and nothing is loaded except three.js: every rock, plant, fish, texture and sound is
generated when the page opens.

Open `index.html` in a browser, or serve the folder:

```sh
python3 -m http.server 8000
```

## What's in the pond

- **Fifteen koi of thirteen varieties.** Kohaku, Taisho Sanke, Showa, Tancho, Yamabuki, Platinum
  and Orenji Ogon, Asagi, Chagoi, Kumonryu, Hi Utsuri, Kujaku, Ochiba, and two long-finned
  butterfly koi. Each has its own pattern, drawn by a noise shader on the body, plus scales,
  translucent fins, eyes and a mouth that opens.
- **A two-tier waterfall** spilling from an upper pool to a ledge pool and then into the pond,
  with foam, rings spreading from where it lands, mist and spray.
- **Plants:** lily pads that drift and get nudged by passing fish, water lilies, irises and reeds
  in the shallows, eelgrass swaying on the bottom, flowering azaleas and a red Japanese maple
  whose leaves fall, float and drift away.
- **Other life:** three dragonflies that hover, dart and dip to the water, plus a stone lantern
  and a ring of woodland.

## Feeding

Press **Feed the koi** (or `F` / `Space`) to toss a handful of pellets onto the part of the pond
you are looking at. You can also tap the water to drop a smaller handful exactly there.

The pellets fly in an arc, splash and float. The koi notice the splashes (the fish nearest the
food notice first), break off what they were doing and race over at two to three times their
cruising speed. Each fish picks the closest pellet that the others aren't already chasing, rises
to the surface, tilts its head up and gulps the pellet with a splash and a ripple. When the food
is gone they hang around the spot for a few seconds before going back to wandering.

## Controls

| input                         | action                        |
| ----------------------------- | ----------------------------- |
| drag / one-finger drag        | orbit                         |
| scroll / pinch                | zoom                          |
| right-drag / two-finger drag  | pan                           |
| tap or click the water        | drop food there               |
| Feed the koi, `F`, `Space`    | scatter food where you look   |
| ⟳ button                      | slow auto-orbit               |
| speaker button                | waterfall, birds and splashes |

## How it's drawn

Each frame is rendered three times:

1. A **reflection** pass from a camera mirrored in the water plane, at half resolution and
   with an oblique clip plane so nothing below the water shows. Where it draws nothing, the
   water shader uses the same analytic sky (gradient, sun and drifting clouds) as the sky dome.
2. A **refraction** pass of everything above and below the water, with a depth texture. The
   shadow map is updated here, so the koi cast shadows on the pond floor.
3. The **final** pass. The water surface bends the refraction image along its normals,
   measures how far each ray travels through the water using the depth texture, and tints it
   by that distance (red is absorbed fastest, so deep water turns jade green). It then blends in
   the reflection with a Fresnel term and adds sun glints, ripple crests, shoreline foam and
   foam from the waterfall.

The water's normals come from a tiling normal map sampled at three scales, plus up to 24
expanding rings (where food lands, where fish gulp, where leaves and dragonflies touch down) and
constant waves from where the waterfall lands. The pond floor, rocks and pebbles share a shader
that adds animated caustics under the water, wet darkening at the waterline and around the
waterfall, and pebbles in the shallows that fade into silt and algae in the deep.

The koi bodies are lofted from a measured koi profile. A vertex shader makes them swim: a wave
travels down the body and grows toward the tail, the whole body curves when the fish turns,
the pectoral fins paddle when it is slow, and the lips widen for a gulp. The same deformation
runs in the shadow pass.

If frames take too long, the resolution steps down on its own (never below 0.75×).
