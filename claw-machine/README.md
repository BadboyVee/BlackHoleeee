# Claw Craze — an arcade claw machine

A playable 3D claw machine built with [three.js](https://threejs.org). One HTML
file, no build step, no imported meshes or textures — the cabinet, the claw rig
and every toy are generated at runtime.

Open `index.html` in a browser, or serve the folder:

```sh
python3 -m http.server 8000
```

Drag the on-screen joystick (or use the arrow keys / WASD) to slide the claw
over the pile, then hit **GRAB** (or Space/Enter). The claw drops, closes on
whatever's underneath, lifts, carries it to the chute, and opens — land it in
the hole and it drops into the prize tray out front. Miss the toy, or grab one
off-centre, and you'll come up empty, same as the real thing.

## How it works

The cabinet is a stack of primitives: a semi-transparent `MeshPhysicalMaterial`
box for the glass, neon-emissive trim bars along every edge, a canvas-painted
marquee sign with a chasing bulb ring, and an opaque base housing with a
control panel carrying a 3D joystick + button that mirror the HUD input live.

Toys are built from spheres, cones and capsules combined into four small
archetypes (bear, bunny, cat, striped ball), each recolored from a bright
palette on spawn. They fall into the pit under simple hand-rolled physics —
gravity, floor/wall bounce, and O(n²) sphere-sphere collision resolution —
which is cheap enough for a ~16-toy pile and settles into a believable heap.

The claw itself is a state machine (`idle → descend → close → ascend → travel
→ open → return`) driving a hub with three hinged fingers. A grab is resolved
by distance from the hub center to the nearest toy: closer to dead-center means
a much better chance of a clean hold, with a small chance of slipping free
again on the way up — enough randomness to feel like a machine you can get
better at, not one that's rigged.

A dropped toy is just released back into the normal physics sim positioned
over the chute; the same floor-collision check that would normally bounce it
detects the chute opening and hands it off to a short Bezier fall into the
external prize tray, where it's re-parented, counted, and the pile is
replenished with a fresh toy after a beat.

## The prompt

Built with [Claude Code](https://claude.com/claude-code), from:

> build a fully playable 3d arcade claw machine using three.js, with a
> transparent glass cabinet, colorful arcade styling, soft glowing lights and
> a pile of simple colorful toys inside, with a working joystick-controlled
> claw that can grab toys and drop them into the prize chute

Copy the file, copy the prompt, do your own — both are here for the taking.

## Notes

three.js r160 loads from a CDN via import map, with a mirror as fallback.
