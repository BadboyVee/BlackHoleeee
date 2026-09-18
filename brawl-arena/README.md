# Gem Arena

A single-file 3D browser game built with Three.js — a top-down arena brawler in the spirit of
Brawl Stars' Gem Grab. You and three AI bots fight over gems spilling from a glowing centre mine;
first to carry 10 gems and hold them uncontested for 15 seconds wins.

No build step, no install: it's one `index.html`. The build deliberately spends most of its effort
on the light rig, since that's what makes a small low-poly arena read as a real place.

## Play

**https://badboyvee.github.io/BlackHoleeee/brawl-arena/**

Or download [`index.html`](index.html) and open it in any modern browser. Three.js and its
postprocessing addons load from a CDN, so nothing else is needed.

## Controls

| Input | Action |
| --- | --- |
| `WASD` / arrow keys, or drag the left stick | Move |
| Mouse, or drag the right stick | Aim |
| Left click / hold, or drag the right stick past its deadzone | Fire |
| `Space`, or tap the SUPER button | Unleash your Super once charged (deal damage to fill it) |
| DAY / SUNSET / NIGHT (top right) | Swap the whole lighting rig live |
| RESTART | Reset the match |

## What's in it

- **A tuned shadow rig, not a default one.** The sun is a single `DirectionalLight` with its
  orthographic shadow frustum fit exactly to the arena, `PCFSoftShadowMap`, and hand-picked
  bias/normalBias to avoid acne and peter-panning at this scale. Two of the four corner torches
  cast their own small shadow maps; the other two are light-only, which is the usual budget trade
  for "a few shadow casters that matter" over "everything casts."
- **Three lighting presets, one light rig.** Day, Sunset, and Night don't swap assets — they
  retarget the same sun/hemisphere/fill/rim lights (color, intensity, angle), fog, tone-mapping
  exposure, and ground tint. Sunset drops the sun low for long dramatic shadows; Night dims it
  almost to nothing and lets the torches and the gem mine become the dominant light sources, with
  a starfield fading in.
- **Things that are lights, not just lit.** The centre gem mine is a glowing crystal totem with a
  soft vertical beam and a pulsing point light; every gem on the ground carries its own small
  light; torches flicker with layered sine noise; hits, KOs, gem pickups, and Supers all spawn a
  short-lived point-light flash from a small reusable pool (so a busy fight doesn't mean unbounded
  live lights). Bloom (`UnrealBloomPass`) is layered on top so the emissive bits actually read as
  glowing rather than just bright-colored.
- **Brawl Stars-shaped systems, kept small.** Gem Grab win condition with an uncontested hold
  timer, gems that scatter on KO, bushes that hide whoever's standing in them (both from bots and
  from projectile targeting), circular obstacle collision for crates and rocks, and a Super that
  charges off damage dealt and unleashes a radial burst with its own light and damage falloff.
- **Everything procedural.** Characters, crates, rocks, bushes, torches, and the mine are all
  built from primitive geometry at runtime — no imported meshes or textures, same as this repo's
  other projects.

## Notes if you want to hack on it

- The camera has a fixed yaw and just follows the player's position — "forward" is always world
  `-Z`. Aiming works by raycasting the mouse against the `y = 0` ground plane, so it stays correct
  regardless of camera angle.
- Bloom, and the `three/addons/` postprocessing imports it needs, are wrapped in a `try/catch`. If
  the addons fail to load for any reason, the game falls back to a plain `renderer.render()` call
  instead of breaking.
- Lighting presets live in one `PRESETS` object near the top of the script — add a key and a dock
  button and you have a fourth time of day.
- `applyPreset()` is the single place that touches light color/intensity, fog, tone-mapping
  exposure, and ground tint together, so a new preset can't accidentally leave one of those stale.
