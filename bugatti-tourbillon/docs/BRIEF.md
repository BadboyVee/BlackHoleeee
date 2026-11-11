# Builder brief — shared rules for every module

You are building one module of a procedural, modular model of a Bugatti Tourbillon
hypercar in Blender, driven entirely by Python. Read this whole file first.

## Environment

- Blender **5.2** is installed as the Python module `bpy` (`python3`, no `blender` binary).
  Run scripts as `python3 path/to/script.py`. There is **no GPU**: 4 CPU cores shared with
  other agents working at the same time.
- Project root: `/home/user/BlackHoleeee/bugatti-tourbillon` (referred to as `$P`).
- In every script: `import sys; sys.path.insert(0, "/home/user/BlackHoleeee/bugatti-tourbillon")`
  then `from tb import spec, util, materials, preview`.
- numpy, scipy, Pillow, opencv (`cv2`), scikit-image are installed.

## Coordinates and units

Metres. **+X forward (nose), +Y left (driver side, LHD), +Z up.**
Origin on the ground, on the centreline, at mid-wheelbase. Ground is Z = 0.
All hard numbers live in `tb/spec.py` — use them, never re-guess them.

## Shared libraries (read them before writing code)

- `tb/spec.py` — dimensions, wheel positions, cabin envelope, colours, collection names.
- `tb/util.py` — `reset_scene`, `get_collection`, `mesh_object`, `bmesh_object`, `loft`,
  `lathe`, `sweep`, `tube`, `extrude_outline`, `prism_cutter`, `boolean`, `box`, `cylinder`,
  `subsurf`, `solidify`, `bevel`, `mirror_y`, `apply_modifiers`, `shade_smooth`,
  `set_material`, `add_material_slot`, `join`, `duplicate`, `parent`, `empty`, `set_origin`,
  `Curve1D`, `catmull_rom`, `resample_polyline`, `superellipse`, `rounded_rect`, `bounds`,
  `look_at`, `tri_count`.
- `tb/materials.py` — `materials.get("name")`; `materials.names()` lists them
  (paint_light, paint_dark, carbon_gloss, glass_tint, alu_polished, alu_knurled, crystal,
  leather_light, leather_dark, leather_perforated, rubber_tyre, brake_disc, caliper,
  emit_headlight, emit_tail, emit_interior, emit_dial, ...). Emissive materials have a
  Value node named `Strength` that the rig drives — use those for anything that lights up,
  do not make your own emission materials.
- `tb/preview.py` — `setup_cycles`, `quick_studio`, `render_view`, `render_views`,
  `part_camera_views`, `render_ortho`.

**Do not edit** spec.py, util.py, materials.py, preview.py, timeline.py or another module's
file. If you need a helper or material that is missing, implement it inside your own module
(for a material: `bpy.data.materials.new("TB_<module>_<name>")` and the `materials.N` helper)
and list it in your final report so it can be promoted to the shared library.

## Blender 5.2 API facts (verified here — older habits will break)

- A new `Material` already has a node tree with a Principled BSDF and an output. Do **not**
  set `use_nodes`. Principled inputs: `Base Color, Metallic, Roughness, IOR, Alpha, Normal,
  Specular IOR Level, Anisotropic, Transmission Weight, Coat Weight, Coat Roughness,
  Sheen Weight, Emission Color, Emission Strength` (and more).
- `ShaderNodeMix` replaces MixRGB: `data_type='RGBA'` → inputs 0 (Factor), 6 (A), 7 (B),
  output 2; `data_type='FLOAT'` → inputs 0, 2, 3, output 0. Noise/Voronoi outputs are
  `Factor`/`Distance`/`Color`.
- No `mesh.use_auto_smooth`. Use `mesh.shade_smooth()` and
  `mesh.set_sharp_from_angle(angle=radians(x))` (wrapped by `util.shade_smooth(obj, deg)`).
- Boolean modifier solvers are `'EXACT'`, `'FLOAT'`, `'MANIFOLD'` (no `'FAST'`).
- Animation: `obj.keyframe_insert(...)` works. F-curves are **not** on `action.fcurves`;
  they are at `action.layers[0].strips[0].channelbags[0].fcurves`.
- Compositor tree is `scene.compositing_node_group` (not `scene.node_tree`).
- Render engines: `'CYCLES'` (use this), `'BLENDER_EEVEE'` (very slow here, avoid),
  `'BLENDER_WORKBENCH'` (fast, fine for pure shape checks).
- Operators that need a UI context mostly fail headless. Prefer `bmesh`, data API and
  modifiers; `util.apply_modifiers` bakes a modifier stack without operators.
- View transform `AgX` with look `AgX - Medium High Contrast` is the project default.

## Performance rules (shared machine)

- Preview renders: Cycles, **≤ 960×540, ≤ 32 samples, denoise on, `threads=2`**
  (`preview.setup_cycles(scene, samples=24, res=(960,540), threads=2)`).
  A preview should finish in well under a minute. Never start a render above these limits.
- Keep geometry sane: use Subdivision modifiers at level ≤ 2 and keep your module within its
  triangle budget (given in your task). Check with `util.tri_count()`.
- Do not leave background processes running. Do not install system packages.

## Module contract

- Your module is one file `tb/<module>.py` exposing `build(collection=None) -> dict`.
  `build` must be idempotent-safe when called once in a fresh scene, must not call
  `reset_scene`, must not create cameras/lights/world unless your task says so, and returns
  a dict of the key objects it created (documented in the module docstring).
- Put objects in the collection named in `spec.COLLECTIONS[...]` for your module unless a
  collection is passed in. Name objects with your module prefix (given in your task).
- Use real-world scale and place things directly in car coordinates.
- Every object must have a material. Smooth-shade curved surfaces; keep hard edges crisp
  with a small bevel rather than leaving razor edges (bevels catch highlights and are what
  make a model look real).
- Add a self-test `tools/test_<module>.py` that builds only your module in a fresh scene
  with `preview.quick_studio`, renders the views your task lists into
  `renders/dev/<module>/`, and prints the triangle count.

## How to work

1. Read the reference images named in your task with the Read tool (they are PNGs) and
   study them before modelling. The references are the standard you are held to.
2. Build, render the self-test views, **look at your renders with the Read tool**, compare
   them side by side with the references, write down what is wrong, fix, repeat.
   Do at least four full look-and-fix rounds. Most first attempts look crude; the quality
   comes from the iterations, so do not stop at "it runs".
3. Be honest in your final report: list what matches the reference, what is approximate,
   and what is missing. An independent critic will compare your renders with the same
   references afterwards.

## Final report (your last message)

- Files you created or changed.
- The return dict of `build()` (key → object name) and any parenting/pivot conventions.
- Triangle count, and typical preview render time.
- What matches the references, what is approximate, what is missing.
- Any helpers/materials you defined locally that should be shared.

Do not use git. Do not touch files outside `$P`.
