# Kumoniwa 雲庭 — a voxel garden above the clouds

A Japanese temple garden built out of voxels on a floating island, in one HTML file with
three.js. There is a five-storey pagoda that opens up storey by storey, a koi pond under a
vermilion drum bridge, a raked gravel garden, a bamboo grove with a fox shrine, a small village,
rice paddies, and a stream that runs off the edge of the island. Fourteen tiny villagers go about
their day, a jade dragon flies around the island chasing its pearl, and nearly everything answers
when you click it.

No build step and nothing to download: three.js loads from a CDN, every model is built in code,
and every sound is synthesised.

**▶ [Open it](https://badboyvee.github.io/BlackHoleeee/voxel-garden/)** · [source](index.html)

Or save [`index.html`](index.html) and open it in a browser (Chrome, Edge, Firefox or Safari).

## Controls

| Input | Action |
| --- | --- |
| Drag · right-drag · scroll | Orbit · pan · zoom (pinch on touch screens) |
| Click | Interact with whatever is under the cursor — a tooltip says what it does |
| `Space` | Pause or run the day (one day takes 15 minutes) |
| `1` – `4` | Spring, summer, autumn, winter |
| `R` | Rain (snowfall in winter) |
| `V` | Viewpoints: pagoda, pond, dry garden, tea house, village, shrine, beneath the island, follow a villager |
| `D` | Ride the dragon (drag to look around, `Esc` to step off) |
| `T` | Miniature lens (tilt-shift) on or off |
| `M` | Sound on or off |
| `H` | Help |

The dock at the bottom has the same controls plus a time-of-day slider. `?lite` in the URL
starts with lighter graphics (phones get them automatically).

## Things to try

The **Garden secrets** panel (top right) keeps track of these as you find them.

- **Ring the bronze bell** in the bell tower next to the pagoda. The monk's log swings, the bell
  booms, ripples cross the pond — and the dragon flies in and coils itself around the top of the
  pagoda. Ring it again, or click the dragon, to send it off.
- **Click the pagoda** to lift it apart storey by storey: a golden Buddha on the ground floor,
  a monk meditating on the second, the temple cat asleep on the fourth, the heart pillar running
  through all of them.
- **Click the dragon** to make it roar and loop the loop. It calls the rain (or snow, in winter);
  click it again to part the clouds.
- **Click the pond** to scatter food — the koi come to eat. Every so often one leaps.
- **Drag across the white gravel** to rake it. Taro the gardener rakes a lap around the edge and
  the garden settles back into its rings and lines.
- **Shake a tree** for a shower of cherry petals, maple leaves, ginkgo gold or snow.
- **Click a stone lantern** to light or put it out — the light it throws on the ground is real
  propagated voxel light, so the garden around it brightens or darkens.
- **Talk to the villagers.** Each has a role, a routine and things to say (a few classic haiku
  among them). They walk home with paper lanterns at night and come back out in the morning.
- Bow to the deer, wake the cat, tip the bamboo shishi-odoshi, ring the tea house wind chime,
  make an offering at the fox shrine, knock on doors.
- **At night, click the sky** to launch fireworks. Summer nights have fireflies and a festival.

## What's in it

**The garden** — terraced pagoda grounds with stone retaining walls and three torii on the
approach; a gourd-shaped koi pond with a turtle island, lily pads, lotus and irises; a little
hill with a cascade into the pond; a karesansui dry garden with five rock groups in moss; an
abbot's hall, a thatched tea house with a round window, a stone basin and a deer scarer; a bamboo
grove with a fox shrine and a tunnel of small torii; a village of machiya, thatched farmhouses, a
storehouse, a soba shop, a tea stall and a well; rice paddies with a scarecrow; cherry, weeping
cherry, maple, pine, ginkgo and cedar trees. Underneath, the island tapers into layered rock with
hanging roots, and the stream falls off the rim into the sea of clouds. Floating islets (one with
a lone torii) and Mount Fuji sit out on the horizon.

**The pagoda** — five storeys with vermilion posts, white plaster, gold-tipped upturned eaves,
bracket bands and a bronze spire with rings and a flame. Wind bells hang from every corner and
swing in the breeze. Each storey is meshed separately so it can lift away.

**The villagers** — fourteen chibi villagers built from fifth-of-a-voxel cubes: monks, a gardener,
a tea master, a grandmother who feeds the koi, two children, a farmer, a tea stall keeper, a
pilgrim, a couple out for hanami, a fisherman and a painter at her easel. They path-find over the
garden (A* on the walkable surface, preferring paths over grass), sweep, rake, pray, fish, farm,
paint and sit; they stop and point when the dragon flies low, and open umbrellas in the rain.

**The dragon** — 64 body segments, a horned head with a hinged jaw, four paddling legs, a flame
tail, whiskers that trail behind its nose, and the flaming pearl it chases. The head flies along a
chain of smooth curves (wide arcs around the island, dives under it, high passes over it, a
vertical loop, a helix around the pagoda) and drops a breadcrumb trail of positions and "up"
vectors; the body is laid along that trail, so it follows exactly where the head has been and
banks with it. Coiling round the pagoda falls out of that for free.

**Seasons, time and weather** — spring blossom, summer green with cicadas, fireflies and
fireworks, autumn maples and ginkgo, winter snow that settles on every upward-facing surface open
to the sky. A full day-night cycle with a sun, a moon and stars; lanterns, paper screens and
windows light up at dusk. Rain darkens and wets the garden, ripples the pond and sends people
under umbrellas.

**Sound** — Web Audio only: a temple bell built from inharmonic partials, a bamboo clack, koto
plucks in the In scale playing a sparse tune, the bush warbler's spring call, cicadas, crickets,
wind, water, rain, a dragon roar, fireworks that boom a little after you see them.

## How it's built

- **Voxels.** The world is a 128 × 112 × 128 grid of one-byte materials. It is meshed in 32³
  chunks with hidden faces culled and per-vertex ambient occlusion. Light is propagated through
  the grid Minecraft-style — sky light down open columns and sideways, lantern light outward from
  its source — and baked into the vertices, so eaves and canopies cast soft shade and lanterns
  pool warm light at night at no runtime cost. Switching a lantern relights the grid and re-meshes
  only the chunks around it.
- **Palette in a texture.** Each material has a colour per season in a 256 × 8 texture (plus
  glow, snow and gravel flags). Changing season is a uniform that cross-fades two rows; snow is a
  shader effect on faces that point up and see the sky.
- **One shader.** World, props and characters share a `MeshLambertMaterial` patched with
  `onBeforeCompile`, so three.js still handles the sun, shadows, hemisphere light and fog, while
  the patch adds the palette, AO, sky and lantern light, wetness, swaying leaves and bamboo, and
  the raked-gravel height texture.
- **Props** (lanterns, the bell, statues, the bridge) are built in quarter voxels and lit from
  the world's light field at load; the ones that never move are merged into a single mesh.
  Villagers, deer, the cat and koi use even smaller voxels and sample the world's light where
  they stand, so they glow as they walk past lanterns.
- **Post-processing:** bloom for lanterns and fireworks, a two-pass tilt-shift for the miniature
  look, and adaptive resolution that trades pixels for frame rate.

## The prompt

Built with [Claude Code](https://claude.com/claude-code) from this one line:

> Build a detailed voxel-style Japanese garden in Three.js, with a pagoda, tiny villagers, a flying dragon and interactive details.

## Notes for hacking on it

Everything is in `index.html`: the interface markup and styles at the top, then one ES module in
numbered sections — utilities and the palette, the voxel engine, the world builders (terrain,
pagoda, buildings, trees, props), sky and water, villagers and animals, the dragon, effects, sound,
interaction and interface, and the main loop. three.js r186 comes from jsDelivr through an import
map.

- The layout lives in `genPaths`, `genProps`, `genTrees` and friends as plain voxel coordinates;
  the island centre is (64, 64) and the garden floor is the top of layer 39 (world y = 0).
- Add a material with `defMat(name, [spring, summer, autumn, winter], options)`; give it
  `light: n` to make it a lamp.
- `window.__garden` exposes a few hooks used for automated screenshots (pause, step the
  simulation, set the time, season and camera).
