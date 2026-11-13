"""Showroom: dark launch-event stage with a turntable, a ring of light blades and a softbox rig.

build() -> dict(floor, turntable, backdrop, lights{name: obj}, emissives{name: material}, world)
MOODS / apply_mood(env, mood, frame=None) switch (and optionally keyframe) the lighting state.
"""
import math
import bpy
from . import spec, util, materials

MOODS = {
    #            Key   StripL StripR Front Rear  RimL  RimR  | Blades Ring
    "black":  dict(ENV_Key=0.0, ENV_StripL=0.0, ENV_StripR=0.0, ENV_Front=0.0, ENV_Rear=0.0, ENV_RimL=0.0, ENV_RimR=0.0, blades=0.0, ring=0.0),
    "dark":   dict(ENV_Key=0.40, ENV_StripL=0.30, ENV_StripR=0.10, ENV_Front=0.20, ENV_Rear=0.15, ENV_RimL=0.9, ENV_RimR=0.8, blades=0.5, ring=0.8),
    "reveal": dict(ENV_Key=0.55, ENV_StripL=0.45, ENV_StripR=0.20, ENV_Front=0.35, ENV_Rear=0.30, ENV_RimL=1.0, ENV_RimR=1.0, blades=0.8, ring=1.0),
    "hero":   dict(ENV_Key=1.0, ENV_StripL=1.0, ENV_StripR=1.0, ENV_Front=1.0, ENV_Rear=1.0, ENV_RimL=1.0, ENV_RimR=1.0, blades=1.0, ring=1.0),
    "cabin":  dict(ENV_Key=0.38, ENV_StripL=0.35, ENV_StripR=0.3, ENV_Front=0.3, ENV_Rear=0.2, ENV_RimL=0.5, ENV_RimR=0.5, blades=0.6, ring=0.8),
}


def _mat(name, colour, rough, metallic=0.0, vary=0.0):
    m = bpy.data.materials.new(name)
    n = materials.N(m)
    n.set(Base_Color=colour, Roughness=rough, Metallic=metallic)
    if vary:
        tc = n.new('ShaderNodeTexCoord')
        t = n.new('ShaderNodeTexNoise')
        t.inputs['Scale'].default_value = 0.35
        t.inputs['Detail'].default_value = 4.0
        n.link(tc.outputs['Object'], t.inputs['Vector'])
        r = n.new('ShaderNodeMapRange')
        r.inputs['To Min'].default_value = rough - vary
        r.inputs['To Max'].default_value = rough + vary
        n.link(t.outputs['Factor'], r.inputs['Value'])
        n.link(r.outputs['Result'], n.bsdf.inputs['Roughness'])
    return m


def _emit(name, colour, strength):
    m = bpy.data.materials.new(name)
    materials._emit(m, colour, strength, base=(0.01, 0.01, 0.01))
    return m


def build(collection=None):
    col = collection or util.get_collection(spec.COLLECTIONS["env"])
    scene = bpy.context.scene
    w = scene.world or bpy.data.worlds.new("ENV_World")
    scene.world = w
    bg = next(n for n in w.node_tree.nodes if n.bl_idname == 'ShaderNodeBackground')
    bg.inputs['Color'].default_value = (0.003, 0.003, 0.004, 1)
    bg.inputs['Strength'].default_value = 1.0

    S = 70.0
    floor = util.mesh_object("ENV_Floor", [(-S, -S, -0.03), (S, -S, -0.03), (S, S, -0.03), (-S, S, -0.03)],
                             [(0, 1, 2, 3)], collection=col, smooth=False,
                             material=_mat("ENV_FloorMat", (0.010, 0.011, 0.013), 0.17, vary=0.05))
    tt = util.cylinder("ENV_Turntable", 3.2, 0.03, axis='Z', location=(0, 0, -0.015), segments=128, collection=col,
                       material=_mat("ENV_TurntableMat", (0.018, 0.019, 0.022), 0.24, vary=0.04), bevel_w=0.006)
    util.set_origin(tt, (0, 0, 0))
    ring_m = _emit("ENV_RingMat", (0.75, 0.88, 1.0), 9.0)
    prof = [(3.225, -0.0295), (3.27, -0.0295), (3.27, -0.026), (3.225, -0.026)]
    import numpy as np
    secs = [[(r * math.cos(a), r * math.sin(a), z) for r, z in prof] for a in np.linspace(0, 2 * math.pi, 128, endpoint=False)]
    v, f = util.loft(secs, closed_v=True, closed_u=True)
    ring = util.mesh_object("ENV_Ring", v, f, collection=col, material=ring_m)
    util.recalc_normals(ring)

    # cyclorama: full dark drum with tall slim light blades
    R, H = 17.0, 7.5
    v, f = util.lathe([(R, -0.03), (R, H)], segments=96, axis='Z')
    wall = util.mesh_object("ENV_Backdrop", v, f, collection=col,
                            material=_mat("ENV_WallMat", (0.012, 0.013, 0.015), 0.6))
    util.recalc_normals(wall, inside=True)
    blade_m = _emit("ENV_BladeMat", (0.80, 0.90, 1.0), 5.0)
    bl = []
    for i in range(30):
        a = 2 * math.pi * (i + 0.5) / 30
        b = util.box("ENV_Blade_%02d" % i, (0.05, 0.14, 5.2), ((R - 0.08) * math.cos(a), (R - 0.08) * math.sin(a), 2.9),
                     collection=col, material=blade_m)
        b.rotation_euler = (0, 0, a)
        bl.append(b)

    def area(name, loc, size, energy, target=(0, 0, 0.5), colour=(1, 1, 1)):
        l = bpy.data.lights.new(name, 'AREA')
        l.shape = 'RECTANGLE'
        l.size, l.size_y = size
        l.energy = energy
        l.color = colour
        o = bpy.data.objects.new(name, l)
        col.objects.link(o)
        o.location = loc
        util.look_at(o, target)
        o["base_energy"] = float(energy)
        return o

    lights = {
        "ENV_Key": area("ENV_Key", (0.2, 0.0, 4.7), (8.5, 3.4), 520),
        "ENV_StripL": area("ENV_StripL", (0.3, 5.6, 2.1), (9.0, 1.1), 320),
        "ENV_StripR": area("ENV_StripR", (0.3, -5.6, 2.0), (9.0, 1.1), 140),
        "ENV_Front": area("ENV_Front", (7.6, 0.6, 1.9), (1.2, 4.6), 125),
        "ENV_Rear": area("ENV_Rear", (-7.6, 0.4, 2.2), (1.2, 4.6), 135),
        "ENV_RimL": area("ENV_RimL", (-5.8, 5.0, 3.4), (3.0, 1.0), 300, colour=(0.75, 0.86, 1.0)),
        "ENV_RimR": area("ENV_RimR", (-5.2, -5.4, 3.2), (3.0, 1.0), 260, colour=(0.75, 0.86, 1.0)),
    }
    # The softboxes are hidden from the camera, so their reflections in the polished outer floor
    # read as floating grey cards.  Light linking keeps them off the outer floor only; the car and
    # the turntable still receive (and reflect) every light.
    rc = bpy.data.collections.new("ENV_FloorLightExclude")
    rc.use_fake_user = True
    rc.objects.link(floor)
    rc.collection_objects[0].light_linking.link_state = 'EXCLUDE'
    for lo in lights.values():
        lo.light_linking.receiver_collection = rc
    # The big softboxes (overhead key and the two side strips) would fill the door windows with a
    # flat grey reflection, while the references show dark glass: keep them off the door glass too.
    # The paint still receives and reflects them.
    side_glass = [o for o in bpy.data.objects if o.name.startswith("BODY_Door_") and o.name.endswith("Glass")]
    if side_glass:
        rc2 = bpy.data.collections.new("ENV_SideLightExclude")
        rc2.use_fake_user = True
        for o in [floor] + side_glass:
            rc2.objects.link(o)
        for co in rc2.collection_objects:
            co.light_linking.link_state = 'EXCLUDE'
        for name in ("ENV_Key", "ENV_StripL", "ENV_StripR"):
            lights[name].light_linking.receiver_collection = rc2

    return dict(floor=floor, turntable=tt, backdrop=wall, lights=lights,
                emissives=dict(blades=blade_m, ring=ring_m), world=w)


def apply_mood(env, mood, frame=None):
    m = MOODS[mood]
    for name, lo in env["lights"].items():
        lo.data.energy = lo["base_energy"] * m[name]
        if frame is not None:
            lo.data.keyframe_insert("energy", frame=frame)
    for name, mat in env["emissives"].items():
        sock = mat.node_tree.nodes["Strength"].outputs[0]
        sock.default_value = float(mat["strength_on"]) * m[name]
        if frame is not None:
            sock.keyframe_insert("default_value", frame=frame)
