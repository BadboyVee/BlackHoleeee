# Saltwind Cove — a WebGPU ocean

A real-time coastal scene built with three.js **WebGPU** and **TSL** (the three.js
shading language). There's no build step: open `index.html` from any static web server in a
browser with WebGPU (recent Chrome, Edge or Safari).

**▶ [Open it](https://badboyvee.github.io/BlackHoleeee/ocean/)**

### One-file version (runs offline)

`tools/build-single.mjs` packs the whole game into a single `saltwind-cove.html`: the code with
three.js bundled in, and every model, texture and sound embedded, so it runs when opened straight
from disk with no server and no internet (about 40 MB, needs a WebGPU browser such as Chrome or Edge):

```
npm i --no-save esbuild three@0.186.0
node tools/build-single.mjs            # writes dist/saltwind-cove.html
```

It embeds the sounds as the compact Opus copies in `assets/audio/opus/`; after changing a sound,
remake them with `pip install av && python tools/audio-opus.py`.

## Controls

| key | action |
| --- | --- |
| click | capture the mouse and look around |
| W A S D | move (boat: throttle / steer) |
| Shift | run · swim fast · fly fast |
| Space | jump · swim up · fly up |
| C | swim down · fly down |
| E | take the helm / leave the boat (when you're next to it) |
| V | boat camera: helm or orbit |
| F | flashlight (works under water) |
| G | free fly on/off (switching back drops you with gravity) |
| Tab | settings panel |

Walk off the end of the pier or into deep water and you start swimming. Near the surface you
float and bob with the waves; once you dive you stay at the depth you choose.

## What's in it

**Ocean**
- Three FFT cascades (420 m / 57 m / 7.7 m) of JONSWAP + TMA spectra with directional
  spreading, a local wind sea plus an ocean swell; choppy displacement, Jacobian whitecaps
  that decay over time. Stockham IFFTs run in workgroup memory, one dispatch per direction.
- CDLOD quadtree mesh with geomorphing and world-anchored vertices (no swimming or popping).
- Shading: exact Fresnel, Beckmann sun glitter whose roughness comes from the slope variance
  the pixel can't resolve (Cox–Munk), sky/cloud reflections plus screen-space reflections,
  depth-checked refraction with Beer–Lambert absorption, backscatter-based water colour,
  crest subsurface glow, and lacy foam from a baked foam texture.
- Shore: a fast-marching travel-time field refracts the swell around the headlands. Waves
  shoal, and a breaking-progress field (distance travelled since breaking began, in wave
  heights, per ray) takes each wave through steepening, curl, plunge and bore on the sandbar
  and the beach. Keyframed breaker profiles give the lip and falling sheet. Swash runs up the
  sand with a rounded leading edge and leaves wet sand and stranded foam behind.
- Surf: whitewater persists behind broken bores in a GPU foam field. Each passing bore
  pushes it shoreward and slow eddies stretch it into streaks. Fresh whitewater is a dense
  blanket that opens into lace within seconds, and the water under foam turns milky
  turquoise. The roller of a broken wave boils. Spray is thrown from where the lip hits the
  water, not from the crest.
- Wake: an interactive iWave height field follows the boat and gives a real Kelvin wake. It
  runs into the beach, soaks into the surf zone and breaks into foam.

**Air/water**
- A GPU probe evaluates the exact rendered surface around the eye, so the waterline on the near
  plane matches the mesh to the pixel. A glass-edge meniscus is drawn along it.
- Under water: spectral Beer–Lambert fog with forward-peaked single scattering plus a diffuse
  multiple-scattering glow, light shafts, Snell's window with total internal reflection,
  caustics from the real wave surface, depth-attenuated sunlight and flashlight beams.
- Drops bead on the lens after you surface, roll off and evaporate; there's no full-screen warp.

**Sky**
- Hillaire 2020 atmosphere (transmittance, multiple-scattering and sky-view LUTs), sun, moon
  and stars, and a time-of-day arc.
- Volumetric cumulus ray-marched into a cached panorama (Nubis-style Perlin–Worley shapes, flat
  bases, eroded tops), cirrus, a baked cloud-shadow map, aerial perspective and god rays.

**World**
- An island with a sandy bay, sandbar, rocky headlands and a reef, rising to an old volcanic
  massif: a ridge spine between two summits whose flanks are carved by baked stream-power
  (river incision) and droplet (rill) erosion into branching valleys and sharp spurs. The bake
  also records drainage, erosion, sky visibility and tree cover; the terrain shader uses them
  for damp green hollows, sun-bleached ridges, rock on crags and scoured gullies, soil scars,
  leaf litter under the canopy and terrain-scale ambient occlusion.
- Ground materials (turf, leaf litter, basalt, volcanic soil) are real geometry modelled and
  rendered in Blender, tiled with anti-tiling; wind ripples appear only where they belong.
- Fishing village: cottages, a timber pier with a T-head and chain-hung lanterns that swing,
  a boat shed, a fish market with a swaying sign, nets, upturned dinghies, crates, pots, buoys,
  rocks and driftwood along the wrack line. Lamps and windows light up at dusk.
- Vegetation modelled in Blender: tropical canopy trees, tiered umbrella trees, ironwoods,
  coconut palms, shrubs and ferns, grown from branch skeletons and dressed with twig and frond
  cards rendered from modelled leaves. Woods follow the baked tree cover (valleys wooded,
  ridges open), with scrub on the forest edges and ferns under the canopy. Two mesh LODs and
  octahedral impostors per tree let the whole massif be forested; LODs cross-fade with a
  temporal dither that never overlaps or leaves holes. Impostors write their true depth, so
  crowns intersect and self-shadow. Branches bend by painted flexibility, cards flutter, crowns
  darken inside and glow when backlit. Meadows are clumps of fanned grass blades over the
  turf texture; they lean away from your feet.
- A lobster boat with buoyancy computed on the rendered waves, rudder and prop physics, bow
  spray, a helm with instruments, and a cab light at night.
- Life: fish schools (GPU boids) over the reef, a humpback whale that surfaces, blows, dives
  and breaches with a knot of pilot fish riding ahead of its head, gulls, ghost crabs that
  scuttle off and dig in, and motes in the sunlight.

**Rendering**
- Frame graph: depth/normal/velocity prepass → GTAO and screen-space contact shadows →
  HDR scene with CSM shadows and sky IBL → water/volume composite → TAA → sharpening, motion
  blur and god rays → bloom → lens flare, vignette, grain → ACES.
- Eye adaptation: the frame's log-average luminance (GPU, read back asynchronously) opens the
  exposure up under the forest canopy and closes it again in the open, on top of the
  day/night curve.
- Motion vectors for everything that moves: the waves (last frame's FFT displacement and
  breaker profile), fish, birds and the boat. TAA reprojects them instead of dragging ghosts
  behind crests. A reactive mask covers what vectors can't describe (spray, glints).

**Sound**
- Real recordings only (see `assets/audio/CREDITS.md`). Surf fades with distance to the shore
  and muffles under water. Also wind, birds by day, crickets at night, 3D gulls and whale song,
  and footsteps that change with sand, planks, grass and shallow water.

## Settings

Tab opens a panel with sea-state presets and the full wave spectrum (wind speed and direction,
fetch, swell, choppiness, whitecaps), surf height and period, sun position and time flow,
clouds, water optics, graphics options (resolution, vegetation detail, eye adaptation, AO,
contact shadows, bloom, motion blur, flare, god rays, vignette, grain) and teleports.

## Code map

```
src/main.js              startup, frame loop, UI glue
src/ocean/               FFT, spectrum, mesh, water material, shore model, surf, wake,
                         probe, caustics, underwater light
src/sky/                 atmosphere LUTs, cloud noise, sky + clouds + shadows
src/world/               island (+ islandShape/erosion/islandData: the baked heightfield),
                         terrain, materials, village, vegetation, grass, collision
tools/bake-island.mjs    bakes assets/terrain/island.bin.gz (node tools/bake-island.mjs)
tools/build-single.mjs   builds the offline one-file dist/saltwind-cove.html
tools/audio-opus.py      the one-file build's compact Opus copies of the sounds
tools/blender/           plant, leaf-card, impostor and ground-texture generators; run with
                         Blender's Python module (pip install bpy), e.g.
                         python tools/blender/leaves.py && python tools/blender/trees.py &&
                         python tools/blender/impostors.py && python tools/blender/ground.py
src/boat/                boat model and physics
src/life/                fish, whale, reef, birds, crabs and motes
src/player/              input, first-person controller, flashlight
src/render/              frame graph, composite, post effects, lens drops, noise, bake
src/fx/spray.js          GPU spray particles
src/audio/audio.js       soundscape
src/core/assets.js       asset URLs (served files, or the one-file build's embedded copies)
```

Debug URL parameters: `?test` (small software-GPU friendly settings), `?pano=2048`,
`?sunEl=8&sunAz=250`, `?t=40&freeze`, `?spawn=fly`, `?off=grass,fish,whale,veg,village,boat,spray,wake,surf,reef,birds,crabs,motes`,
`?veg=0.7` (vegetation LOD distance scale), `?waterDebug=1` (breaker state: breaking index, shore foam, thin lip) or `?waterDebug=2`
(facing: above water, front face, break zone), `?nofit` (keep full resolution: by default a
slow GPU gets a lower render resolution a few seconds after loading).

## References

Tessendorf (Simulating Ocean Water; iWave), Horvath (Empirical directional wave spectra),
Bruneton et al. (real-time ocean lighting), Cox & Munk, Gordon et al. (ocean colour),
Hillaire (A scalable and production ready sky and atmosphere), Schneider (Nubis cloudscapes),
Wrenninge (multiple scattering octaves), Evan Wallace (WebGL water caustics), Sethian (fast
marching), Battjes / McCowan (breaking criteria).
