# Clawd Holo Card

A holographic trading card of Clawd, the Claude Code mascot, rendered with
[three.js](https://threejs.org). The front of the card is a window: Clawd stands
in a world behind the glass, so tilting the card shows real depth. Tap it and
Clawd leaps out through the glass.

One HTML file, no build step. Every texture on the card is painted at runtime.

**▶ [Open it](https://badboyvee.github.io/BlackHoleeee/holo-card/)**

Or serve the folder and open `index.html`:

```sh
python3 -m http.server 8000
```

## Controls

| Input | Action |
| --- | --- |
| Move the mouse | The card leans away from the pointer; Clawd watches it |
| Drag | Turn the card. Flick to spin it; it settles on a face |
| Tap the card | Clawd hops out through the glass (on the back, the card turns round) |
| Tilt your phone | Tilts the card. iOS asks for motion access on the first tap |
| Foil thumbnails | Prism holo, Gold foil, Cosmos holo |
| `F` / flip button | Flip the card |
| `P` / pause button | Pause the idle motion |
| Arrow keys, `Space` | Nudge the card, make Clawd hop |

## How it works

### The window

The card face is drawn twice. In the first pass it only writes `1` into the
stencil buffer. The world behind the glass (sky dome, floor, aura, dust,
Clawd) lives in its own scene and every material in it tests for that `1`, so
it can only appear through the face. The depth buffer is then cleared and the
physical card is drawn on top: the iridescent edge, the printed back, and the
glass and foil layers of the front. Everything outside the card that might
cover the window (the far edge of the slab, the wall's shadow) tests for
"not 1".

The inner scene follows the card through a copied matrix, and its lights and
environment rotate with it. That world is about seven units deep inside a
card 0.07 units thick.

### Breaking the glass

A clipping plane sits on the glass. While Clawd hops, it is drawn twice: once
behind the plane through the stencil window, once in front of the plane with
no stencil test, after everything else. When the hop carries Clawd forward,
the part past the glass leaves the window and can cross the card's edge.

### The foil

Holographic foil is a diffraction grating. For light from direction `L` seen
from direction `V`, a grating with line spacing `d` and direction `T` sends
wavelength `λ = d · |(L + V) · T| / m` toward the eye. The shader evaluates
that for the first three orders and two virtual lights, and converts the
wavelengths to colour with Zucconi's spectral fit. What changes between the
three foils is how `T` and `d` vary across the card:

- **Prism**: a sunburst centred on Clawd, with spacing that varies by angle.
- **Gold**: near-parallel brushed lines, tinted gold.
- **Cosmos**: a Voronoi mosaic in which each tile has its own direction and
  spacing ("cracked ice").

Light only leaves a grating close to the plane across its lines. Stamped foil
gets a broad lobe and stays lit. The clear laminate over the window gets a
narrow one, so it shows bands that travel as you tilt. The laminate is masked
away from Clawd, like a reverse-holo card. On top of that sit glitter flakes:
tiny mirrors with random tilts that flash when one lines up with a light.

Each face is painted into three canvases: ink, a foil mask, and a height map.
The height map is blurred and turned into a normal map, so the stamped name,
frame and rosette are embossed and catch reflections at their edges. The
foil also gets a metallic reflection layer, and the whole face gets a glass
reflection layer. Both are additive physically based materials that reflect
the studio.

### Clawd

The model is built from the pixel art Claude Code prints in the terminal:

```
 ▐▛███▜▌
▝▜█████▛▘
  ▘▘ ▝▝
```

Read as quadrant pixels, that is a 6 × 4 body with two tall eyes, one-unit arm
stubs, and four legs. Each part is a rounded box in Clawd orange `#D77757`,
with clearcoat, a little sheen, and a touch of thin-film iridescence. It
breathes, blinks (sometimes twice), looks around or follows your pointer,
waves, does a little tap dance, and on a tap it crouches, leaps with a twirl,
and lands with a squash and a ring of sparks.

### Light

The studio is an environment map built from emissive panels around a grey
room: a big softbox up left, a strip light right, and a soft top light.
`RoomEnvironment` was too bright for glass; its panels saturated into white
hotspots. The wall shadow comes from a directional light at zero intensity,
which still renders its shadow map but puts no point highlight on the glass.
Shadows are VSM, so the card's shadow on the wall is soft. Inside the card,
a key light casts Clawd's shadow on the floor, and two coloured rim lights
match each foil.

If frames run long, the render resolution steps down until they don't.

## The prompt

Built with [Claude Code](https://claude.com/claude-code), from a screenshot of a
holo card demo and this message:

> Build a holo 3D card effect
>
> 100% 4D QAULITY
>
> REALISTIC ASF!
>
> Make CLAWD BE THE CHARACTER TO USE
>
> add Made with Opus 5.5 to it

## Notes

three.js r186 loads from jsDelivr through an import map. The card's type is
Bricolage Grotesque, Instrument Sans and JetBrains Mono from Google Fonts.
Clawd is Anthropic's Claude Code mascot; this is a fan-made card.
