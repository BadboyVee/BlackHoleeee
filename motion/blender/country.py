"""The countryside on HORIZON's hills: fields of grass, each its own green and some mown in stripes, hedgerows along
their borders with trees standing in them, a few oaks out in the fields, and the shadows of passing clouds.

The fields are one 2-D Voronoi pattern, used twice: the grass shader colours each cell, and Geometry Nodes scatter
points over the terrain and keep the ones that fall on a cell's border for the hedges, so every hedge runs exactly
along the edge of a field. Used by blender/hills.py."""
import math

import bpy
import numpy as np

FIELD = 240.0                  # metres across a field, about
HEDGE = 4.5                    # metres from a field's edge that its hedge reaches


# ---------------------------------------------------------------- node helpers

class Nodes:
    """A little sugar over a node tree: math, vector math and map range by name, constants inlined."""

    def __init__(self, tree):
        self.N, self.L = tree.nodes, tree.links

    def new(self, kind, **props):
        n = self.N.new(kind)
        for k, v in props.items():
            setattr(n, k, v)
        return n

    def _in(self, sock, v):
        if isinstance(v, (int, float)):
            sock.default_value = v
        elif isinstance(v, tuple):
            sock.default_value = v
        elif v is not None:
            self.L.new(v, sock)

    def math(self, op, a, b=None, c=None, clamp=False):
        n = self.new("ShaderNodeMath", operation=op, use_clamp=clamp)
        for i, v in enumerate((a, b, c)):
            self._in(n.inputs[i], v)
        return n.outputs[0]

    def vec(self, op, a, b=None, scale=None):
        n = self.new("ShaderNodeVectorMath", operation=op)
        self._in(n.inputs[0], a)
        self._in(n.inputs[1], b)
        if scale is not None:
            self._in(n.inputs["Scale"], scale)
        return n.outputs[1] if op in ("LENGTH", "DISTANCE", "DOT_PRODUCT") else n.outputs[0]

    def remap(self, v, a, b, lo=0.0, hi=1.0, clamp=True):
        n = self.new("ShaderNodeMapRange", clamp=clamp)
        self._in(n.inputs["Value"], v)
        n.inputs["From Min"].default_value, n.inputs["From Max"].default_value = a, b
        n.inputs["To Min"].default_value, n.inputs["To Max"].default_value = lo, hi
        return n.outputs["Result"]

    def xyz(self, v):
        n = self.new("ShaderNodeSeparateXYZ")
        self.L.new(v, n.inputs[0])
        return n.outputs["X"], n.outputs["Y"], n.outputs["Z"]

    def noise(self, v, scale, detail=2.0, rough=0.5, dims="3D"):
        n = self.new("ShaderNodeTexNoise", noise_dimensions=dims)
        self.L.new(v, n.inputs["Vector"])
        n.inputs["Scale"].default_value = scale
        n.inputs["Detail"].default_value = detail
        n.inputs["Roughness"].default_value = rough
        return n

    def fields(self, v, feature="F1"):
        """The field pattern: 2-D Voronoi over x, y in metres."""
        n = self.new("ShaderNodeTexVoronoi", voronoi_dimensions="2D", feature=feature)
        self.L.new(v, n.inputs["Vector"])
        n.inputs["Scale"].default_value = 1.0 / FIELD
        return n

    def mix(self, fac, a, b):
        n = self.new("ShaderNodeMix", data_type="RGBA")
        self._in(n.inputs["Factor"], fac)
        self._in(n.inputs["A"], a)
        self._in(n.inputs["B"], b)
        return n.outputs["Result"]


# ---------------------------------------------------------------- the grass

PALETTE = [   # each field draws one: lush, deep, fresh, sunlit yellow-green, new-cut hay (linear RGB)
    (0.0, (0.050, 0.300, 0.012)), (0.30, (0.030, 0.210, 0.010)), (0.55, (0.085, 0.380, 0.016)),
    (0.80, (0.150, 0.420, 0.030)), (0.93, (0.300, 0.400, 0.075)),
]


def grass(haze, haze_start, haze_end):
    """Grass: a green per field, mottled at three scales, mown fields striped, darker along the hedge bottoms,
    hazing into the air with distance."""
    m = bpy.data.materials.new("grass")
    m.use_nodes = True
    g = Nodes(m.node_tree)
    b = g.N["Principled BSDF"]
    b.inputs["Roughness"].default_value = 0.92
    b.inputs["Specular IOR Level"].default_value = 0.2
    b.inputs["Sheen Weight"].default_value = 0.6
    b.inputs["Sheen Tint"].default_value = (0.85, 1.0, 0.6, 1)
    P = g.new("ShaderNodeTexCoord").outputs["Object"]
    x, y, _ = g.xyz(P)
    cell = g.fields(P)
    rnd = g.new("ShaderNodeSeparateColor")
    g.L.new(cell.outputs["Color"], rnd.inputs["Color"])
    pal = g.new("ShaderNodeValToRGB")
    pal.color_ramp.interpolation = "CONSTANT"
    els = pal.color_ramp.elements
    els[0].position, els[0].color = PALETTE[0][0], (*PALETTE[0][1], 1)
    els[1].position, els[1].color = PALETTE[1][0], (*PALETTE[1][1], 1)
    for pos, col in PALETTE[2:]:
        e = els.new(pos)
        e.color = (*col, 1)
    g.L.new(rnd.outputs["Red"], pal.inputs["Fac"])
    # mown stripes, in about half the fields, at an angle of their own
    theta = g.math("MULTIPLY", rnd.outputs["Blue"], math.pi)
    s = g.math("ADD", g.math("MULTIPLY", x, g.math("COSINE", theta)), g.math("MULTIPLY", y, g.math("SINE", theta)))
    band = g.math("SINE", g.math("MULTIPLY", s, 2 * math.pi / 13.0))
    mown = g.remap(rnd.outputs["Green"], 0.45, 0.5)
    stripe = g.math("MULTIPLY_ADD", g.math("MULTIPLY", band, mown), 0.07, 1.0)
    # mottling: broad patches, clumps, tufts
    m1 = g.noise(P, 1 / 70.0, 3.0).outputs["Fac"]
    m2 = g.noise(P, 1 / 9.0, 2.0).outputs["Fac"]
    m3 = g.noise(P, 2.2, 2.0).outputs["Fac"]
    tuft = g.new("ShaderNodeTexVoronoi")                              # tufts, with dark gaps between them
    g.L.new(P, tuft.inputs["Vector"])
    tuft.inputs["Scale"].default_value = 6.0
    gap = g.remap(tuft.outputs["Distance"], 0.15, 0.75, 1.08, 0.72)
    mott = g.math("MULTIPLY_ADD", m1, 0.5, 0.75)
    mott = g.math("MULTIPLY", mott, g.math("MULTIPLY_ADD", m2, 0.42, 0.79))
    mott = g.math("MULTIPLY", mott, g.math("MULTIPLY_ADD", m3, 0.3, 0.85))
    mott = g.math("MULTIPLY", mott, gap)
    # the uncut strip under each hedge, darker and lusher
    edge = g.fields(P, "DISTANCE_TO_EDGE").outputs["Distance"]
    verge = g.remap(edge, 0.0, HEDGE * 2.2 / FIELD, 0.62, 1.0)
    k = g.math("MULTIPLY", g.math("MULTIPLY", stripe, mott), verge)
    tint = g.new("ShaderNodeMix", data_type="RGBA", blend_type="MULTIPLY")
    tint.inputs["Factor"].default_value = 1.0
    g.L.new(pal.outputs["Color"], tint.inputs["A"])
    kc = g.new("ShaderNodeCombineColor")
    for ch in ("Red", "Green", "Blue"):
        g.L.new(k, kc.inputs[ch])
    g.L.new(kc.outputs["Color"], tint.inputs["B"])
    # aerial haze, by distance from the eye
    cam = g.new("ShaderNodeCameraData")
    hz = g.remap(cam.outputs["View Distance"], haze_start, haze_end)
    hz = g.math("POWER", hz, 0.8)
    col = g.mix(hz, tint.outputs["Result"], (*haze, 1))
    g.L.new(col, b.inputs["Base Color"])
    b.inputs["Emission Color"].default_value = (*haze, 1)
    g.L.new(g.math("MULTIPLY", hz, 0.75), b.inputs["Emission Strength"])
    # fine grass in the bump
    bump = g.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.25
    bump.inputs["Distance"].default_value = 0.05
    g.L.new(g.math("ADD", g.noise(P, 28.0, 2.0).outputs["Fac"], gap), bump.inputs["Height"])
    g.L.new(bump.outputs["Normal"], b.inputs["Normal"])
    return m


# ---------------------------------------------------------------- hedges and trees

def leaves(name, base, var, haze, haze_start, haze_end):
    """Foliage: clumped leaves in the bump, each instance its own shade, hazing with distance like the grass."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    g = Nodes(m.node_tree)
    b = g.N["Principled BSDF"]
    b.inputs["Roughness"].default_value = 0.75
    b.inputs["Specular IOR Level"].default_value = 0.3
    b.inputs["Sheen Weight"].default_value = 0.4
    P = g.new("ShaderNodeTexCoord").outputs["Object"]
    rnd = g.new("ShaderNodeObjectInfo").outputs["Random"]
    shade = g.mix(rnd, (*base, 1), (*var, 1))
    clump = g.new("ShaderNodeTexVoronoi")
    g.L.new(P, clump.inputs["Vector"])
    clump.inputs["Scale"].default_value = 2.6
    lit = g.math("MULTIPLY_ADD", clump.outputs["Distance"], -0.55, 1.15)
    k = g.new("ShaderNodeCombineColor")
    for ch in ("Red", "Green", "Blue"):
        g.L.new(lit, k.inputs[ch])
    mul = g.new("ShaderNodeMix", data_type="RGBA", blend_type="MULTIPLY")
    mul.inputs["Factor"].default_value = 1.0
    g.L.new(shade, mul.inputs["A"])
    g.L.new(k.outputs["Color"], mul.inputs["B"])
    cam = g.new("ShaderNodeCameraData")
    hz = g.math("POWER", g.remap(cam.outputs["View Distance"], haze_start, haze_end), 0.8)
    g.L.new(g.mix(hz, mul.outputs["Result"], (*haze, 1)), b.inputs["Base Color"])
    b.inputs["Emission Color"].default_value = (*haze, 1)
    g.L.new(g.math("MULTIPLY", hz, 0.75), b.inputs["Emission Strength"])
    bump = g.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.6
    g.L.new(clump.outputs["Distance"], bump.inputs["Height"])
    g.L.new(bump.outputs["Normal"], b.inputs["Normal"])
    return m


def _blob(radius, loc, lumpy, seed, squash=1.0):
    """A lumpy sphere: an icosphere worn by cloud noise, its bottom flattened a little."""
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=4, radius=radius, location=(0, 0, 0))
    o = bpy.context.object
    tex = bpy.data.textures.new(f"lumps{seed}", "CLOUDS")
    tex.noise_scale = radius * 0.45
    tex.noise_depth = 2
    d = o.modifiers.new("lumps", "DISPLACE")
    d.texture = tex
    d.strength = radius * lumpy
    d.mid_level = 0.5
    d.texture_coords = "GLOBAL"
    bpy.ops.object.modifier_apply(modifier="lumps")
    for v in o.data.vertices:
        v.co.z *= squash
        v.co += type(v.co)(loc)
    return o


def _join(parts, name):
    bpy.ops.object.select_all(action="DESELECT")
    for p in parts:
        p.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    bpy.ops.object.join()
    o = bpy.context.object
    o.name = name
    bpy.ops.object.shade_smooth()
    o.location = (0, 0, -2000)                     # out of sight: the hedges and trees are its instances
    return o


def bush(mat):
    o = _blob(1.0, (0, 0, 0.5), 0.55, 1, squash=0.8)
    o.data.materials.append(mat)
    return _join([o], "bush")


def tree(mat, bark, seed):
    """A broadleaf tree in a field: a short trunk, a crown of a few lumpy clumps."""
    rnd = [(0.0, 0.0, 6.2, 3.4), (1.7, 0.6, 5.4, 2.5), (-1.6, -0.4, 5.6, 2.6), (0.3, -1.2, 7.4, 2.3),
           (-0.6, 1.3, 7.0, 2.2)]
    parts = []
    bpy.ops.mesh.primitive_cylinder_add(vertices=10, radius=0.32, depth=4.4, location=(0, 0, 2.0))
    t = bpy.context.object
    t.data.materials.append(bark)
    parts.append(t)
    for i, (x, y, z, r) in enumerate(rnd):
        k = (seed * 7 + i * 3) % 5
        c = _blob(r * (0.9 + 0.05 * k), (x * (1 + 0.1 * (k - 2)), y, z), 0.5, 10 * seed + i, squash=0.85)
        c.data.materials.append(mat)
        parts.append(c)
    return _join(parts, f"tree{seed}")


def countryside(terrain, bush_ob, tree_ob, near=150.0, far=3400.0, wedge=46.0, density=0.05):
    """Geometry Nodes on the terrain: the hedges along the field borders (with gaps), trees standing in them, and
    a few oaks out in the fields, all only where the camera can see them."""
    ng = bpy.data.node_groups.new("country", "GeometryNodeTree")
    ng.interface.new_socket(name="Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    ng.interface.new_socket(name="Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    g = Nodes(ng)
    gin, gout = g.new("NodeGroupInput"), g.new("NodeGroupOutput")
    pts = g.new("GeometryNodeDistributePointsOnFaces", distribute_method="RANDOM")
    pts.inputs["Density"].default_value = density
    pts.inputs["Seed"].default_value = 3
    g.L.new(gin.outputs[0], pts.inputs["Mesh"])
    P = g.new("GeometryNodeInputPosition").outputs[0]
    x, y, _ = g.xyz(P)
    # in view: in front of the camera, within the wedge, neither too near nor too far
    ang = g.math("ABSOLUTE", g.math("ARCTAN2", x, y))
    d = g.math("SQRT", g.math("ADD", g.math("MULTIPLY", x, x), g.math("MULTIPLY", y, y)))
    seen = g.math("MULTIPLY", g.math("LESS_THAN", ang, math.radians(wedge)),
                  g.math("MULTIPLY", g.math("GREATER_THAN", d, near), g.math("LESS_THAN", d, far)))
    edge = g.fields(P, "DISTANCE_TO_EDGE").outputs["Distance"]
    on_edge = g.math("LESS_THAN", edge, HEDGE / FIELD)
    gaps = g.math("GREATER_THAN", g.noise(P, 1 / 55.0, 1.0).outputs["Fac"], 0.36)
    r1 = g.new("FunctionNodeRandomValue", data_type="FLOAT")
    r1.inputs["Seed"].default_value = 11
    rv = r1.outputs[1]
    hedge = g.math("MULTIPLY", g.math("MULTIPLY", seen, on_edge), gaps)
    hedge_tree = g.math("MULTIPLY", hedge, g.math("LESS_THAN", rv, 0.035))
    hedge_bush = g.math("MULTIPLY", hedge, g.math("GREATER_THAN", rv, 0.035))
    field_tree = g.math("MULTIPLY", g.math("MULTIPLY", seen, g.math("GREATER_THAN", edge, 0.12)),
                        g.math("LESS_THAN", rv, 0.0016))

    def scatter(sel, ob, smin, smax, squash, seed):
        info = g.new("GeometryNodeObjectInfo", transform_space="ORIGINAL")
        info.inputs["Object"].default_value = ob
        rs = g.new("FunctionNodeRandomValue", data_type="FLOAT_VECTOR")
        rs.inputs["Min"].default_value = (smin, smin, smin * squash)
        rs.inputs["Max"].default_value = (smax, smax, smax * squash)
        rs.inputs["Seed"].default_value = seed
        rr = g.new("FunctionNodeRandomValue", data_type="FLOAT_VECTOR")
        rr.inputs["Min"].default_value = (0.0, 0.0, 0.0)
        rr.inputs["Max"].default_value = (0.06, 0.06, 2 * math.pi)
        rr.inputs["Seed"].default_value = seed + 1
        inst = g.new("GeometryNodeInstanceOnPoints")
        g.L.new(pts.outputs["Points"], inst.inputs["Points"])
        g.L.new(sel, inst.inputs["Selection"])
        g.L.new(info.outputs["Geometry"], inst.inputs["Instance"])
        g.L.new(rr.outputs[0], inst.inputs["Rotation"])
        g.L.new(rs.outputs[0], inst.inputs["Scale"])
        return inst.outputs["Instances"]

    join = g.new("GeometryNodeJoinGeometry")
    g.L.new(gin.outputs[0], join.inputs[0])
    for part in (scatter(hedge_bush, bush_ob, 1.5, 2.3, 0.85, 21),
                 scatter(hedge_tree, tree_ob[0], 0.8, 1.25, 1.0, 31),
                 scatter(field_tree, tree_ob[1], 0.9, 1.35, 1.0, 41)):
        g.L.new(part, join.inputs[0])
    g.L.new(join.outputs[0], gout.inputs[0])
    terrain.modifiers.new("country", "NODES").node_group = ng
    return ng


def cloud_shadows(height=950.0, cover=0.22, size=24000.0):
    """A sheet high over the land that only the sun sees: open sky with patches of cloud in it, so the hills lie
    in sun with a few soft shadows drifting over them."""
    me = bpy.data.meshes.new("gobo")
    s = size / 2
    me.from_pydata([(-s, -s, height), (s, -s, height), (s, s, height), (-s, s, height)], [], [(0, 1, 2, 3)])
    o = bpy.data.objects.new("gobo", me)
    bpy.context.collection.objects.link(o)
    for vis in ("camera", "diffuse", "glossy", "transmission", "volume_scatter"):
        setattr(o, f"visible_{vis}", False)
    m = bpy.data.materials.new("gobo")
    m.use_nodes = True
    g = Nodes(m.node_tree)
    g.N.remove(g.N["Principled BSDF"])
    P = g.new("ShaderNodeTexCoord").outputs["Object"]
    n = g.noise(P, 1 / 900.0, 5.0, 0.55)
    # this noise is narrow: its median is 0.50 and its 75th, 85th and 95th percentiles 0.548, 0.573 and 0.616
    edge = float(np.interp(1 - cover, [0.5, 0.75, 0.85, 0.95], [0.50, 0.548, 0.573, 0.616]))
    k = g.remap(n.outputs["Fac"], edge - 0.012, edge + 0.012)
    mixs = g.new("ShaderNodeMixShader")
    g.L.new(k, mixs.inputs["Fac"])
    g.L.new(g.new("ShaderNodeBsdfTransparent").outputs[0], mixs.inputs[1])
    dark = g.new("ShaderNodeBsdfDiffuse")
    dark.inputs["Color"].default_value = (0, 0, 0, 1)
    g.L.new(dark.outputs[0], mixs.inputs[2])
    g.L.new(mixs.outputs[0], g.N["Material Output"].inputs["Surface"])
    me.materials.append(m)
    return o
