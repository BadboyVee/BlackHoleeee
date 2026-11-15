"""The compound around the duplex: fence, gates, gatehouse, paving, terraces, pool,
planting, service yard, roof plant, street and the surrounding estate."""
import math
import random

import bpy
from mathutils import Matrix, Vector
from shapely.geometry import Point, box as B
from shapely.ops import unary_union

import house as H
from bk import mats, plants
from bk.core import MB, R, T, TR, coll, fillet, inst, link, rad
from house import F, Z0, Z1, ZP, ZR, ZRT

PX0, PX1, PY0, PY1 = -9.0, 25.0, -17.0, 20.0     # plot
DECK = 0.43                                       # raised terrace / pool deck level
POOL = B(-7.0, 1.8, -3.0, 10.6)
PLATFORM = B(-8.5, -3.4, 7.0, 0.0).union(B(-8.5, 0.0, 0.0, 13.2))
GATE = (16.8, 22.3)                               # main gate opening (x range)
PGATE = (15.35, 16.35)                            # pedestrian gate
GATEHOUSE = B(22.3, -16.6, 24.75, -13.9)
PORCH_STEPS = B(7.0, -1.6, 10.5, -1.0)


class SM:
    _c = {}

    def __getattr__(self, k):
        if k not in self._c:
            self._c[k] = getattr(self, '_' + k)()
        return self._c[k]

    def _pavers(self): return mats.pavers("drive_pavers", ('#9a9893', '#84827d', '#aaa8a2'))
    def _pavers_dark(self): return mats.pavers("drive_border", ('#4a4a4b', '#3c3c3d', '#58585a'), wear=0.3)
    def _sidewalk(self): return mats.pavers("sidewalk", ('#a39a8c', '#8f8779', '#b3aa9c'), size=(0.3, 0.15), wear=0.7)
    def _kerb(self): return mats.concrete("kerb", '#a5a39d', rough=0.8, bump=0.25)
    def _deck(self): return mats.wood_planks('teak', (2.4, 0.14), gap=0.005, gloss=0.0, name="deck_teak", rough=0.6)
    def _coping(self): return mats.marble('travertine', 0.35, name="pool_coping", scale=2.0)
    def _mosaic(self): return mats.mosaic()
    def _water(self): return mats.water()
    def _fence(self): return mats.stucco("fence_render", '#ece8de', dirt=0.1)
    def _fence_dark(self): return mats.stucco("fence_band", '#3a3c3e', grain=0.7, dirt=0.04)
    def _gate(self): return mats.plain("gate_charcoal", '#1d1f21', rough=0.45)
    def _gate_wood(self): return mats.wood('teak', gloss=0.1, name="gate_teak")
    def _lawn(self): return mats.lawn()
    def _earth(self): return mats.lawn("estate_ground", '#3d4a25', '#5a5f33')
    def _asphalt(self): return mats.asphalt()
    def _mulch(self): return mats.soil("mulch", '#3d2b1d', '#22180f')
    def _tank(self): return mats.plain("tank_black", '#0d0e0f', rough=0.5)
    def _galv(self): return mats.metal("galvanised", '#9fa3a6', 0.45)
    def _acwhite(self): return mats.plain("ac_casing", '#e4e3df', rough=0.4)
    def _lamp(self): return mats.emit("lamp_warm", '#ffd9a0', 12.0)
    def _lamp_cool(self): return mats.emit("lamp_street", '#fff0d8', 30.0)
    def _solar(self):
        b = mats.NB("solar_cells")
        uv = b.tc('UV')
        bk = b.brick(uv, c1='#0b1326', c2='#101c3a', mortar='#8f949a', scale=1.0, msize=0.003, msmooth=0.0, bias=0.0,
                     bw=0.165, rh=0.165, offset=0.0)
        return b.out(b.principled(color=bk.outputs['Color'], rough=0.12, metallic=0.3, coat=1.0, coat_rough=0.03))


S = SM()


def light(name, kind, loc, energy, color=(1.0, 0.85, 0.65), size=0.05, rot=None, spot=None, c=None, blend=0.5,
          size_y=None, shape=None):
    l = bpy.data.lights.new(name, kind)
    l.energy = energy
    l.color = color
    if kind == 'AREA':
        l.size = size
        if size_y:
            l.shape = 'RECTANGLE'
            l.size_y = size_y
        elif shape:
            l.shape = shape
    else:
        l.shadow_soft_size = size
    if kind == 'SPOT':
        l.spot_size = rad(spot or 90)
        l.spot_blend = blend
    o = bpy.data.objects.new(name, l)
    o.location = loc
    if rot is not None:
        o.rotation_euler = [rad(a) for a in rot]
    link(o, c)
    return o


# ---------------------------------------------------------------------------
# fence / gates
# ---------------------------------------------------------------------------
def _pillar(mb, x, y, h=2.75, s=0.45, lamp=False, lights=None):
    mb.bx(x - s / 2, y - s / 2, 0, x + s / 2, y + s / 2, h, S.fence)
    mb.bx(x - s / 2 - 0.04, y - s / 2 - 0.04, h, x + s / 2 + 0.04, y + s / 2 + 0.04, h + 0.07, S.fence_dark)
    if lamp:
        mb.bx(x - 0.09, y - 0.09, h + 0.07, x + 0.09, y + 0.09, h + 0.1, F.black)
        mb.bx(x - 0.075, y - 0.075, h + 0.1, x + 0.075, y + 0.075, h + 0.3, S.lamp)
        mb.bx(x - 0.1, y - 0.1, h + 0.3, x + 0.1, y + 0.1, h + 0.33, F.black)
        if lights is not None:
            lights.append((x, y, h + 0.2))


def fence_run(mb, a, b, h=2.4, t=0.23, spacing=3.4, lamps=False, lights=None, wires=True, band=True, first=True,
              last=True):
    """Rendered block wall between two points with pillars, coping and electric-fence wires."""
    a, b = Vector((a[0], a[1], 0)), Vector((b[0], b[1], 0))
    d = b - a
    L = d.length
    u = d / L
    n = Vector((-u.y, u.x, 0))
    k = max(1, round(L / spacing))
    ang = math.degrees(math.atan2(u.y, u.x))
    M = T(a.x, a.y, 0) @ R(ang)
    mb.push(M)
    mb.bx(0, -t / 2, 0, L, t / 2, h, S.fence)
    if band:
        mb.bx(0, -t / 2 - 0.012, h - 0.5, L, t / 2 + 0.012, h - 0.38, S.fence_dark)
    mb.bx(0, -t / 2 - 0.035, h, L, t / 2 + 0.035, h + 0.06, S.fence_dark)
    if wires:
        for i in range(k * 2 + 1):
            x = L * i / (k * 2)
            mb.rod((x, 0, h + 0.06), (x, 0.12, h + 0.55), 0.008, F.black, segs=6)
        for j in range(5):
            z = h + 0.14 + j * 0.095
            y = 0.02 + j * 0.023
            mb.rod((0, y, z), (L, y, z), 0.0016, S.galv, segs=4, caps=False)
    mb.pop()
    for i in range(k + 1):
        if (i == 0 and not first) or (i == k and not last):
            continue
        p = a + u * (L * i / k)
        _pillar(mb, p.x, p.y, h + 0.3, lamp=lamps and i % 2 == 0, lights=lights)


def sliding_gate(mb, x0, x1, y, h=2.25):
    fr = 0.07
    g, w = S.gate, S.gate_wood
    mb.bx(x0, y - 0.03, 0.09, x1, y + 0.03, 0.09 + fr, g)
    mb.bx(x0, y - 0.03, h - fr, x1, y + 0.03, h, g)
    for x in (x0, x1 - fr):
        mb.bx(x, y - 0.03, 0.09, x + fr, y + 0.03, h, g)
    for x in (x0 + (x1 - x0) / 3, x0 + 2 * (x1 - x0) / 3):
        mb.bx(x - 0.025, y - 0.03, 0.09 + fr, x + 0.025, y + 0.03, h - fr, g)
    n = int((h - 0.09 - 2 * fr) / 0.125)
    for i in range(n):
        z = 0.09 + fr + 0.012 + i * (h - 0.09 - 2 * fr - 0.012) / n
        mb.bx(x0 + fr, y - 0.018, z, x1 - fr, y + 0.018, z + 0.105, w if i % 4 == 1 else g, bevel=0.003)
    # track, rollers, guide posts, motor
    mb.bx(x0 - 5.6, y - 0.03, 0.0, x1 + 0.2, y + 0.03, 0.02, S.galv)
    for x in (x0 + 0.5, x1 - 0.5):
        mb.cyl(0.05, 0.03, (x, y, 0.065), S.galv, segs=16, axis='Y')
    mb.bx(x0 - 0.5, y + 0.25, 0.0, x0 - 0.2, y + 0.5, 0.35, mats.plain("gate_motor", '#3b4046', rough=0.5), bevel=0.01)


def swing_gate(mb, x0, x1, y, h=2.2):
    fr = 0.05
    g, w = S.gate, S.gate_wood
    for x in (x0 + 0.01, x1 - fr - 0.01):
        mb.bx(x, y - 0.025, 0.06, x + fr, y + 0.025, h, g)
    mb.bx(x0 + 0.01, y - 0.025, 0.06, x1 - 0.01, y + 0.025, 0.06 + fr, g)
    mb.bx(x0 + 0.01, y - 0.025, h - fr, x1 - 0.01, y + 0.025, h, g)
    n = int((h - 0.06 - 2 * fr) / 0.125)
    for i in range(n):
        z = 0.06 + fr + 0.012 + i * (h - 0.06 - 2 * fr - 0.012) / n
        mb.bx(x0 + fr, y - 0.016, z, x1 - fr, y + 0.016, z + 0.105, w if i % 4 == 1 else g, bevel=0.003)
    mb.box((0.03, 0.09, 0.16), (x1 - 0.09, y, 1.05), F.steel, bevel=0.005)
    mb.box((0.12, 0.03, 0.2), (x0 - 0.3, y - 0.14, 1.4), mats.plain("intercom", '#202224', rough=0.3), bevel=0.006)


def build_fence(lights):
    mb = MB("fence")
    y = PY0
    fence_run(mb, (PX0, y), (15.125, y), lamps=True, lights=lights)
    fence_run(mb, (22.525, y), (PX1, y), lamps=True, lights=lights, spacing=2.6)
    _pillar(mb, 16.575, y, 2.95, 0.5, True, lights)
    fence_run(mb, (PX1, PY0), (PX1, PY1), first=False)
    fence_run(mb, (PX1, PY1), (PX0, PY1), first=False)
    fence_run(mb, (PX0, PY1), (PX0, PY0), first=False, last=False)
    # lintel beam over the pedestrian gate + number plate
    mb.bx(15.35, y - 0.13, 2.35, 16.35, y + 0.13, 2.6, S.fence_dark)
    mb.box((0.34, 0.02, 0.2), (15.85, y - 0.14, 2.47), mats.plain("plate_brass", '#c9a45a', rough=0.3, metallic=1.0), bevel=0.004)
    sliding_gate(mb, GATE[0] - 0.05, GATE[1] + 0.05, y + 0.2)
    swing_gate(mb, PGATE[0], PGATE[1], y)
    return mb.finish(sharp=35)


def build_gatehouse():
    mb = MB("gatehouse")
    x0, y0, x1, y1 = GATEHOUSE.bounds
    h = 2.7
    w = 0.15
    outer = B(x0, y0, x1, y1)
    inner = B(x0 + w, y0 + w, x1 - w, y1 - w)
    door = B(x0 - 0.01, y1 - 1.25, x0 + w + 0.01, y1 - 0.35)
    win = B(x0 + 0.5, y0 - 0.01, x1 - 0.5, y0 + w + 0.01)
    win2 = B(x0 - 0.01, y0 + 0.4, x0 + w + 0.01, y1 - 1.6)
    walls = outer.difference(inner)
    mb.prism(walls.difference(door), 0.05, 0.95, F.ext_white)
    mb.prism(walls.difference(door).difference(win).difference(win2), 0.95, 2.1, F.ext_white)
    mb.prism(walls, 2.1, h, F.ext_white)
    mb.prism(inner, 0.0, 0.05, F.terrace)
    mb.prism(outer.buffer(0.35, join_style=2), h, h + 0.14, F.ext_dark)
    # glazing
    mb.bx(x0 + 0.5, y0 + 0.06, 0.95, x1 - 0.5, y0 + 0.075, 2.1, F.glass)
    mb.bx(x0 + 0.06, y0 + 0.4, 0.95, x0 + 0.075, y1 - 1.6, 2.1, F.glass)
    for (a, b_) in (((x0 + 0.5, y0 + 0.04), (x1 - 0.5, y0 + 0.1)), ((x0 + 0.04, y0 + 0.4), (x0 + 0.1, y1 - 1.6))):
        mb.bx(a[0], a[1], 0.93, b_[0], b_[1], 0.97, F.frame)
        mb.bx(a[0], a[1], 2.08, b_[0], b_[1], 2.12, F.frame)
    # door leaf (ajar) -- the door opening is cut from the low band too
    mb.push(T(x0 + 0.075, y1 - 0.36, 0.05) @ R(-200))
    mb.bx(0, -0.02, 0, 0.88, 0.02, 2.0, F.door, bevel=0.002)
    mb.pop()
    # desk + chair inside
    mb.bx(x0 + 0.6, y0 + 0.2, 0.05, x1 - 0.6, y0 + 0.7, 0.8, F.door_frame, bevel=0.004)
    return mb.finish(sharp=35)


# ---------------------------------------------------------------------------
# ground surfaces
# ---------------------------------------------------------------------------
def build_ground():
    plot = B(PX0 + 0.115, PY0 + 0.115, PX1 - 0.115, PY1 - 0.115)
    house_fp = B(0, 0, H.W, H.D).union(B(7.0, -1.0, 10.5, 1.6))
    lawn_front = B(PX0 + 0.115, PY0 + 0.115, 4.4, -3.4)
    lawn_back = B(PX0 + 0.115, 13.2, 9.0, PY1 - 0.115)
    hard = plot.difference(house_fp).difference(PLATFORM).difference(lawn_front).difference(lawn_back) \
        .difference(GATEHOUSE).difference(PORCH_STEPS)
    border = hard.difference(hard.buffer(-0.22, join_style=2))
    mb = MB("paving")
    mb.prism(hard.difference(border), -0.3, 0.0, S.pavers, bottom=False, side=False)
    mb.prism(border, -0.3, 0.004, S.pavers_dark, bottom=False)
    # kerb between lawn and drive
    for lw in (lawn_front, lawn_back):
        kb = lw.buffer(0.0).difference(lw.buffer(-0.1, join_style=2))
        mb.prism(kb, -0.1, 0.06, S.kerb, bottom=False)
    # manhole covers in the service yard
    for (x, y) in ((12.0, 14.2), (13.2, 14.2), (21.0, 3.0)):
        mb.bx(x - 0.35, y - 0.35, 0.0, x + 0.35, y + 0.35, 0.012, mats.concrete("manhole", '#77766f', bump=0.2))
        mb.bx(x - 0.04, y - 0.12, 0.012, x + 0.04, y + 0.12, 0.02, F.black)
    # drain grating inside the gate
    mb.bx(GATE[0], PY0 + 0.75, 0.0, GATE[1], PY0 + 1.0, 0.012, F.black)
    for i in range(44):
        x = GATE[0] + 0.06 + i * (GATE[1] - GATE[0] - 0.12) / 43
        mb.bx(x - 0.02, PY0 + 0.77, 0.012, x + 0.02, PY0 + 0.98, 0.018, S.galv)
    mb.finish()

    # lawns (separate objects so they can carry grass particles)
    lawns = []
    for i, lw in enumerate((lawn_front, lawn_back)):
        m = MB(f"lawn_{i}")
        m.prism(lw.buffer(-0.1, join_style=2), -0.2, 0.02, S.lawn, bottom=False, side=False)
        lawns.append(m.finish())

    # raised platform: front terrace (tiles) + pool deck (timber)
    mb = MB("terrace")
    front = B(-8.5, -3.4, 7.0, 0.0)
    west = B(-8.5, 0.0, 0.0, 13.2)
    cop = POOL.buffer(0.32, join_style=2).difference(POOL)
    mb.prism(front, 0.0, DECK, F.terrace, mat_side=F.ext_dark, bottom=False)
    mb.prism(west.difference(POOL.buffer(0.32, join_style=2)), 0.0, DECK, S.deck, mat_side=F.ext_dark, bottom=False)
    mb.prism(cop, 0.0, DECK + 0.012, S.coping, bottom=False)
    # terrace steps to the lawn and to the drive
    for i, z in enumerate((DECK * 2 / 3, DECK / 3)):
        mb.bx(1.2, -3.4 - 0.3 * (i + 1), 0.0, 5.8, -3.4 - 0.3 * i, z, F.terrace)
    # porch steps
    for i, z in enumerate((Z0 * 2 / 3, Z0 / 3)):
        mb.bx(7.0, -1.0 - 0.3 * (i + 1), 0.0, 10.5, -1.0 - 0.3 * i, z, F.porch)
    mb.bx(7.0, -1.0, Z0 - 0.02, 10.5, 1.6, Z0, F.porch)
    # pool shell
    px0, py0, px1, py1 = POOL.bounds
    depth = 1.45
    zf = DECK - depth
    shell = POOL.buffer(0.2, join_style=2)
    mb.prism(shell.difference(POOL), zf - 0.2, DECK - 0.001, S.mosaic, bottom=False, top=False,
             side_fn=lambda x, y, nx, ny, z: S.mosaic)
    mb.prism(POOL, zf - 0.2, zf, S.mosaic, bottom=False, side=False)
    for i in range(4):   # entry steps at the south end
        mb.bx(px0, py0 + i * 0.32, zf, px1, py0 + (i + 1) * 0.32, DECK - 0.28 - i * 0.27, S.mosaic)
    # ladder
    for x in (px1 - 0.8, px1 - 0.3):
        pts = fillet([(x, py1 + 0.35, DECK), (x, py1 + 0.35, DECK + 0.85), (x, py1 - 0.12, DECK + 0.85), (x, py1 - 0.12, DECK - 1.0)], 0.18, 8)
        mb.tube(pts, 0.019, F.chrome, segs=10)
    for z in (DECK - 0.25, DECK - 0.55, DECK - 0.85):
        mb.bx(px1 - 0.8, py1 - 0.17, z, px1 - 0.3, py1 - 0.07, z + 0.02, F.chrome)
    mb.finish(sharp=35)
    w = MB("pool_water")
    w.prism(POOL, DECK - 0.14, DECK - 0.12, S.water, bottom=False, side=False)
    w.finish()
    return lawns


def pool_lights(c=None):
    px0, py0, px1, py1 = POOL.bounds
    out = []
    for y in (py0 + 2.0, py0 + 4.4, py0 + 6.8):
        out.append(light("pool_light", 'AREA', (px0 + 0.03, y, DECK - 0.75), 180, (0.55, 0.9, 1.0), 0.18, rot=(0, -90, 0), c=c, shape='DISK'))
    return out


# ---------------------------------------------------------------------------
# planting
# ---------------------------------------------------------------------------
def build_planting(lawns, grass=True):
    mb = MB("hedges")
    plants.hedge(mb, PX0 + 0.25, PY0 + 0.25, PX0 + 0.85, -3.5, 1.15, seed=1)
    plants.hedge(mb, PX0 + 0.85, PY0 + 0.25, 4.2, PY0 + 0.8, 0.9, seed=2)
    plants.hedge(mb, PX0 + 0.25, 13.4, PX0 + 0.85, PY1 - 0.25, 1.3, seed=3)
    plants.hedge(mb, PX0 + 0.85, PY1 - 0.8, 8.8, PY1 - 0.25, 1.3, seed=4)
    # planter between the terrace and the drive
    mb.bx(6.45, -3.4, DECK, 7.0, -1.75, DECK + 0.38, F.ext_dark)
    mb.bx(6.5, -3.35, DECK + 0.36, 6.95, -1.8, DECK + 0.37, S.mulch)
    plants.hedge(mb, 6.5, -3.35, 6.95, -1.8, 0.45, z0=DECK + 0.33, seed=5)
    # bed in front of the guest room
    mb.bx(10.75, -0.95, 0.0, 16.05, -0.08, 0.22, F.ext_dark)
    mb.bx(10.8, -0.9, 0.2, 16.0, -0.12, 0.21, S.mulch)
    for i, x in enumerate((11.4, 12.5, 13.6, 14.7, 15.6)):
        plants.shrub(mb, (x, -0.5, 0.2), 0.36 + 0.05 * (i % 2), seed=10 + i, flowers='#c3222b' if i % 2 == 0 else None)
    # ixora balls along the front lawn edge and the pool deck
    for i, (x, y) in enumerate(((-7.6, -15.4), (-4.8, -15.6), (-1.9, -15.4), (1.0, -15.6), (3.4, -15.4))):
        plants.shrub(mb, (x, y, 0.02), 0.45, seed=20 + i, flowers=('#d8a21d', '#c3222b', '#f0ece2')[i % 3])
    for i, y in enumerate((0.6, 12.4)):
        mb.bx(-8.45, y - 0.45, DECK, -7.55, y + 0.45, DECK + 0.5, F.ext_dark, bevel=0.01)
        plants.shrub(mb, (-8.0, y, DECK + 0.45), 0.42, seed=30 + i)
    mb.finish()
    # palms: two variants, instanced
    c = coll("PLANTS", bpy.data.collections.get("SITE"))
    p1 = plants.palm("royal_palm_a", 7.6, 17, seed=3, lean=0.3, c=c)
    p2 = plants.palm("royal_palm_b", 6.4, 15, seed=8, lean=0.5, c=c)
    p1.location = (-5.6, -13.6, 0)
    p2.location = (-1.2, -14.4, 0)
    spots = [(p1, (2.9, -13.3, 0), 140, 0.95), (p2, (-7.3, -6.2, 0), 60, 1.05), (p1, (-8.0, 14.6, 0), 200, 0.9),
             (p2, (3.5, 17.8, 0), 310, 1.0), (p1, (23.4, 9.5, 0), 20, 0.85), (p2, (23.6, -9.6, 0), 250, 0.9)]
    for o, loc, rz, sc_ in spots:
        inst(o, loc, rz, c, scale=sc_)
    # palm tree pits on the drive side
    pit = MB("tree_pits")
    for (x, y) in ((23.4, 9.5), (23.6, -9.6)):
        pit.cyl(0.75, 0.1, (x, y, 0.0), S.kerb, segs=28, base=True)
        pit.cyl(0.66, 0.11, (x, y, 0.0), S.mulch, segs=28, base=True)
    pit.finish()
    # grass
    if grass:
        plants.add_grass(lawns[0], 30000, 0.075, 26, seed=1)
        plants.add_grass(lawns[1], 14000, 0.075, 22, seed=2)
    coll("SITE")


# ---------------------------------------------------------------------------
# services, roof plant
# ---------------------------------------------------------------------------
def ac_condenser(mb, loc, rz=0.0, bracket=False):
    mb.push(TR(loc[0], loc[1], loc[2], rz))
    mb.box((0.85, 0.32, 0.6), (0, 0, 0), S.acwhite, bevel=0.012, base=True)
    mb.cyl(0.235, 0.012, (-0.12, -0.165, 0.3), mats.plain("ac_fan_dark", '#1c1d1e', rough=0.6), segs=28, axis='Y')
    for r in (0.06, 0.11, 0.16, 0.21):
        mb.torus(r, 0.004, (-0.12, -0.175, 0.3), S.galv, segs=28, rsegs=6, axis='Y')
    for a in range(0, 180, 30):
        d = Vector((math.cos(rad(a)), 0, math.sin(rad(a)))) * 0.22
        mb.rod((-0.12 - d.x, -0.176, 0.3 - d.z), (-0.12 + d.x, -0.176, 0.3 + d.z), 0.003, S.galv, segs=4)
    for i in range(9):
        mb.bx(0.2, -0.163, 0.1 + i * 0.05, 0.39, -0.16, 0.13 + i * 0.05, mats.plain("ac_fan_dark", '#1c1d1e', rough=0.6))
    if bracket:
        for x in (-0.3, 0.3):
            mb.bx(x - 0.02, -0.16, -0.04, x + 0.02, 0.2, 0.0, S.galv)
            mb.rod((x, -0.14, -0.04), (x, 0.2, -0.3), 0.012, S.galv, segs=6)
    else:
        mb.bx(-0.5, -0.25, -0.08, 0.5, 0.25, 0.0, S.kerb)
    mb.pop()


def build_services():
    mb = MB("services")
    # condensers: ground (east) + wall brackets (north) + roof
    ac_condenser(mb, (16.45, 4.0, 0.08), 90)
    ac_condenser(mb, (16.45, 8.6, 0.08), 90)
    for x in (2.6, 12.9):
        ac_condenser(mb, (x, 12.5 + 0.36, Z1 + 0.45), 180, bracket=True)
    ac_condenser(mb, (-0.36, 5.0, Z1 + 0.45), 270, bracket=True)
    for (x, y) in ((4.0, 11.0), (5.2, 11.0), (12.0, 11.0)):
        ac_condenser(mb, (x, y, ZRT + 0.08), 180)
    # refrigerant lines in trunking
    for (x, y) in ((16.02, 4.5), (16.02, 9.1)):
        mb.bx(x, y - 0.03, 0.4, x + 0.05, y + 0.03, Z0 + 2.4, F.ext_white)
    # downpipes
    for (x, y) in ((16.06, 12.44), (-0.06, 12.44), (16.06, 0.4)):
        mb.cyl(0.05, ZRT - 0.1, (x, y, 0.05), F.ext_dark, segs=14, base=True)
        mb.box((0.14, 0.14, 0.16), (x, y, ZRT - 0.1), F.ext_dark, bevel=0.01)
    # water tank tower
    tx, ty = 20.6, 18.3
    for dx in (-1.5, 0.0, 1.5):
        for dy in (-0.75, 0.75):
            mb.box((0.1, 0.1, 3.4), (tx + dx, ty + dy, 0), S.galv, base=True)
    for z in (1.2, 2.4, 3.4):
        for dy in (-0.75, 0.75):
            mb.box((3.1, 0.07, 0.07), (tx, ty + dy, z), S.galv)
        for dx in (-1.5, 0.0, 1.5):
            mb.box((0.07, 1.57, 0.07), (tx + dx, ty, z), S.galv)
    for dy in (-0.75, 0.75):
        for sx in (-1, 1):
            mb.rod((tx + sx * 1.5, ty + dy, 0.1), (tx, ty + dy, 1.2), 0.02, S.galv, segs=6)
            mb.rod((tx + sx * 1.5, ty + dy, 2.4), (tx, ty + dy, 1.2), 0.02, S.galv, segs=6)
    mb.box((3.3, 1.8, 0.05), (tx, ty, 3.43), S.galv, base=True)
    for dx in (-0.8, 0.8):
        prof = [(0, 0), (0.68, 0)]
        z = 0.0
        for i in range(9):
            prof += [(0.7, z + 0.02), (0.7, z + 0.1), (0.68, z + 0.12), (0.68, z + 0.15)]
            z += 0.155
        prof += [(0.62, z + 0.12), (0.3, z + 0.27), (0.27, z + 0.3), (0.27, z + 0.36), (0, z + 0.36)]
        mb.lathe(prof, S.tank, segs=36, loc=(tx + dx, ty, 3.48))
        mb.cyl(0.025, 3.6, (tx + dx + 0.55, ty - 0.76, 0.05), F.ext_white, segs=8, base=True)
    # generator house
    gx, gy = 23.2, 15.4
    mb.bx(gx - 1.3, gy - 0.9, 0.0, gx + 1.3, gy + 0.9, 0.12, S.kerb)
    mb.box((2.3, 1.5, 1.7), (gx, gy, 0.12), mats.plain("gen_canopy", '#2f4a3a', rough=0.45), bevel=0.02, base=True)
    for i in range(10):
        mb.bx(gx - 0.9, gy - 0.757, 0.5 + i * 0.09, gx + 0.9, gy - 0.75, 0.55 + i * 0.09, F.black)
    mb.rod((gx + 0.8, gy + 0.4, 1.8), (gx + 0.8, gy + 0.4, 2.5), 0.035, S.galv, segs=10)
    # boys' quarters
    bq = B(9.6, 16.3, 16.6, 19.7)
    inner = bq.buffer(-0.15, join_style=2)
    doors = [B(10.6, 16.29, 11.5, 16.46), B(14.2, 16.29, 15.1, 16.46)]
    wins = [B(12.0, 16.29, 13.4, 16.46), B(15.5, 16.29, 16.2, 16.46)]
    walls = bq.difference(inner)
    mb.prism(walls.difference(unary_union(doors)), 0.0, 1.0, F.ext_white, bottom=False)
    mb.prism(walls.difference(unary_union(doors + wins)), 1.0, 2.1, F.ext_white)
    mb.prism(walls, 2.1, 2.9, F.ext_white)
    mb.prism(bq.buffer(0.4, join_style=2), 2.9, 3.05, F.ext_dark)
    mb.prism(bq.buffer(0.25, join_style=2), 3.05, 3.1, F.roof, bottom=False)
    for d in doors:
        x0, y0, x1, y1 = d.bounds
        mb.bx(x0 + 0.02, y0 + 0.07, 0.0, x1 - 0.02, y0 + 0.11, 2.08, F.door, bevel=0.003)
        mb.cyl(0.02, 0.05, (x1 - 0.1, y0 + 0.05, 1.0), F.steel, segs=10, axis='Y')
    for wn in wins:
        x0, y0, x1, y1 = wn.bounds
        mb.bx(x0, y0 + 0.07, 1.0, x1, y0 + 0.08, 2.1, F.glass)
        mb.bx(x0 - 0.03, y0 + 0.05, 0.97, x1 + 0.03, y0 + 0.1, 1.02, F.frame)
        mb.bx(x0 - 0.03, y0 + 0.05, 2.08, x1 + 0.03, y0 + 0.1, 2.13, F.frame)
        mb.bx((x0 + x1) / 2 - 0.02, y0 + 0.05, 1.0, (x0 + x1) / 2 + 0.02, y0 + 0.1, 2.1, F.frame)
    mb.finish(sharp=35)


def build_roof_plant():
    c = H.shell_coll(2)
    mb = MB("roof_plant")
    alu = mats.metal("alu_panel_frame", '#b9bcc0', 0.35)
    for (ox, oy) in ((1.2, 1.0), (1.2, 5.3), (11.6, 1.0), (11.6, 5.3)):
        for i in range(4):
            for j in range(2):
                x = ox + i * 1.08
                y = oy + j * 1.76
                M = T(x, y, ZRT + 0.22 + j * 0.3) @ R(10, 'X')
                mb.push(M)
                mb.bx(0, 0, 0, 1.04, 1.72, 0.035, alu)
                mb.bx(0.02, 0.02, 0.035, 1.02, 1.70, 0.037, S.solar)
                mb.pop()
        for i in range(5):
            x = ox - 0.02 + i * 1.08
            mb.bx(x - 0.02, oy, ZRT, x + 0.02, oy + 0.04, ZRT + 0.22, S.galv)
            mb.bx(x - 0.02, oy + 3.4, ZRT, x + 0.02, oy + 3.44, ZRT + 0.82, S.galv)
            mb.rod((x, oy + 0.02, ZRT + 0.22), (x, oy + 3.42, ZRT + 0.82), 0.02, S.galv, segs=6)
    # satellite dish
    dx, dy = 9.0, 10.8
    mb.cyl(0.03, 1.1, (dx, dy, ZRT), S.galv, segs=10, base=True)
    Md = T(dx, dy, ZRT + 1.1) @ R(200) @ R(55, 'X')
    mb.lathe([(0, 0), (0.15, 0.012), (0.3, 0.05), (0.42, 0.105), (0.43, 0.105), (0.3, 0.04), (0.15, 0.0), (0, -0.012)],
             mats.plain("dish", '#d9d9d6', rough=0.5), segs=32, m=Md)
    mb.rod(tuple(Md @ Vector((0.3, 0, 0.06))), tuple(Md @ Vector((0, 0, 0.42))), 0.006, S.galv, segs=6)
    mb.rod(tuple(Md @ Vector((-0.3, 0, 0.06))), tuple(Md @ Vector((0, 0, 0.42))), 0.006, S.galv, segs=6)
    mb.cyl(0.03, 0.09, tuple(Md @ Vector((0, 0, 0.42))), S.acwhite, segs=10)
    # roof hatch + vents
    mb.box((0.9, 0.9, 0.3), (8.3, 11.3, ZRT), S.galv, bevel=0.01, base=True)
    for (x, y) in ((2.0, 9.6), (14.2, 8.2), (6.0, 6.5)):
        mb.cyl(0.055, 0.5, (x, y, ZRT), F.ext_dark, segs=12, base=True)
        mb.cyl(0.1, 0.04, (x, y, ZRT + 0.5), F.ext_dark, segs=12, base=True)
    mb.finish(sharp=35, c=c)


# ---------------------------------------------------------------------------
# street + estate context
# ---------------------------------------------------------------------------
def simple_house(mb, cx, cy, w, d, floors, color, roof, seed, face='S'):
    rng = random.Random(seed)
    wall = mats.stucco(f"nb_wall_{color}", color, dirt=0.12)
    h = floors * 3.2 + 0.3
    x0, y0, x1, y1 = cx - w / 2, cy - d / 2, cx + w / 2, cy + d / 2
    mb.bx(x0, y0, 0, x1, y1, h, wall)
    glass = mats.plain("nb_glass", '#0d1820', rough=0.05, metallic=0.6)
    for fl in range(floors):
        z = 0.3 + fl * 3.2 + 1.0
        for side in ('S', 'N'):
            n = max(2, int(w / 3.2))
            for i in range(n):
                x = x0 + (i + 0.5) * w / n
                ww = rng.choice((1.2, 1.6, 2.0))
                yy = y0 - 0.02 if side == 'S' else y1 + 0.02
                mb.box((ww, 0.06, 1.4), (x, yy, z + 0.7), glass)
        for side in ('W', 'E'):
            n = max(1, int(d / 4.0))
            for i in range(n):
                y = y0 + (i + 0.5) * d / n
                xx = x0 - 0.02 if side == 'W' else x1 + 0.02
                mb.box((0.06, 1.4, 1.3), (xx, y, z + 0.65), glass)
    if roof == 'flat':
        mb.bx(x0 - 0.05, y0 - 0.05, h, x1 + 0.05, y1 + 0.05, h + 0.75, wall)
        mb.bx(x0 + 0.2, y0 + 0.2, h + 0.3, x1 - 0.2, y1 - 0.2, h + 0.76, S.kerb)
    else:
        rc = {'red': '#6e2f24', 'brown': '#4a3326', 'char': '#2b2d30', 'blue': '#2a3d55'}[roof]
        rm = mats.tiles('grey', (0.33, 0.4), grout=mats.scale_col(rc, 0.5), gw=0.02, rough=0.6, pattern='plain', color=rc,
                        name=f"nb_roof_{roof}", bump=1.0, offset=0.5)
        ov = 0.7
        ex0, ey0, ex1, ey1 = x0 - ov, y0 - ov, x1 + ov, y1 + ov
        rise = min(w, d) * 0.27
        if w >= d:
            r0, r1 = (ex0 + (ey1 - ey0) / 2, cy), (ex1 - (ey1 - ey0) / 2, cy)
        else:
            r0, r1 = (cx, ey0 + (ex1 - ex0) / 2), (cx, ey1 - (ex1 - ex0) / 2)
        V = [(ex0, ey0, h), (ex1, ey0, h), (ex1, ey1, h), (ex0, ey1, h), (r0[0], r0[1], h + rise), (r1[0], r1[1], h + rise)]
        if w >= d:
            Fc = [(0, 1, 5, 4), (1, 2, 5), (2, 3, 4, 5), (3, 0, 4)]
        else:
            Fc = [(0, 1, 4), (1, 2, 5, 4), (2, 3, 5), (3, 0, 4, 5)]
        uv = []
        for f in Fc:
            a = Vector(V[f[0]])
            e = (Vector(V[f[1]]) - a).normalized()
            nn = (Vector(V[f[1]]) - a).cross(Vector(V[f[2]]) - a).normalized()
            vv = nn.cross(e)
            for i in f:
                p = Vector(V[i]) - a
                uv.append((p.dot(e), p.dot(vv)))
        mb.raw(V, Fc, uv, rm, False)
        mb.bx(ex0, ey0, h - 0.18, ex1, ey1, h, mats.plain("nb_fascia", '#e8e4da', rough=0.6))


def build_context(trees=True):
    c = coll("CONTEXT")
    mb = MB("street")
    X0, X1 = -160.0, 170.0
    mb.prism(B(X0, -27.2, X1, -19.9), -0.15, -0.05, S.asphalt, bottom=False, side=False)
    for ya, yb in ((-19.9, -19.72), (-27.38, -27.2)):
        mb.bx(X0, ya, -0.15, X1, yb, 0.1, S.kerb)
    mb.prism(B(X0, -19.72, X1, PY0 - 0.115), -0.1, 0.05, S.sidewalk, bottom=False, side=False)
    mb.prism(B(X0, -30.4, X1, -27.38), -0.1, 0.05, S.sidewalk, bottom=False, side=False)
    white = mats.plain("road_paint", '#d8d6cf', rough=0.6)
    x = X0
    while x < X1:
        mb.bx(x, -23.61, -0.05, x + 3.0, -23.49, -0.046, white)
        x += 9.0
    # gate apron ramp
    mb.prism([(GATE[0] - 0.4, PY0 - 0.115), (GATE[1] + 0.4, PY0 - 0.115), (GATE[1] + 1.2, -19.72), (GATE[0] - 1.2, -19.72)],
             0.05, 0.06, S.pavers_dark, bottom=False)
    # covered drain slabs along our kerb
    slab = mats.concrete("drain_slab", '#8f8d86', bump=0.3)
    x = X0
    while x < X1:
        mb.bx(x + 0.01, -20.55, 0.05, x + 0.59, -19.95, 0.075, slab)
        x += 0.6
    # street lights
    pole = mats.metal("pole_galv", '#868a8d', 0.5)
    lights = []
    for px in (-14.0, 13.0, 40.0, -41.0, 67.0):
        mb.cyl(0.09, 7.5, (px, -20.9, 0.05), pole, segs=12, r2=0.055, base=True)
        mb.rod((px, -20.9, 7.5), (px, -22.6, 7.85), 0.04, pole, segs=8)
        mb.box((0.28, 0.62, 0.1), (px, -22.75, 7.84), pole, bevel=0.02)
        mb.box((0.2, 0.46, 0.02), (px, -22.75, 7.78), S.lamp_cool)
        lights.append((px, -22.75, 7.7))
    mb.finish(c=c)
    # estate ground
    g = MB("estate_ground")
    g.prism(B(-1500, -1500, 1500, 1500).difference(B(PX0, PY0, PX1, PY1)).difference(B(X0, -30.4, X1, PY0)), -0.2, -0.02,
            S.earth, bottom=False, side=False)
    g.prism(B(PX0, PY0, PX1, PY1), -0.4, -0.3, S.earth, bottom=False, side=False)
    g.finish(c=c)
    # neighbouring plots
    nb = MB("neighbours")
    rng = random.Random(11)
    cols = ['#e9e3d5', '#d9cdb8', '#f0ede6', '#c9c4bb', '#e6d7c1', '#bfc5c9', '#efe6d8', '#d5b9a1']
    roofs = ['red', 'brown', 'char', 'flat', 'char', 'blue', 'flat', 'brown']
    plots = []
    for i in range(-4, 5):
        px = 8.0 + i * 36.0
        if i != 0:
            plots.append((px, 2.0, 'S'))
        plots.append((px, 40.0, 'N'))
        plots.append((px, -48.0, 'N'))
        plots.append((px, 78.0, 'S'))
        plots.append((px, -86.0, 'S'))
    tree_spots = []
    for k, (px, py, face) in enumerate(plots):
        w, d = rng.uniform(11, 17), rng.uniform(9, 13)
        fl = rng.choice((1, 2, 2, 2))
        simple_house(nb, px + rng.uniform(-3, 3), py + rng.uniform(-2, 3), w, d, fl, cols[k % len(cols)],
                     roofs[(k * 3 + 1) % len(roofs)], k)
        # plot fence
        fx0, fx1, fy0, fy1 = px - 17, px + 17, py - 18.5, py + 18.5
        fm = mats.stucco("nb_fence", '#ddd6c8', dirt=0.15)
        for (a, b_) in (((fx0, fy0), (fx1, fy0 + 0.2)), ((fx0, fy1 - 0.2), (fx1, fy1)), ((fx0, fy0), (fx0 + 0.2, fy1)),
                        ((fx1 - 0.2, fy0), (fx1, fy1))):
            if abs(py - 2.0) < 1 and False:
                continue
            nb.bx(a[0], a[1], 0, b_[0], b_[1], 2.3, fm)
        for _ in range(rng.choice((1, 2, 3))):
            tree_spots.append((px + rng.uniform(-14, 14), py + rng.choice((-1, 1)) * rng.uniform(9, 15), rng.random()))
    nb.finish(c=c)
    if trees:
        t1 = plants.tree("tree_a", 8.0, 3.4, seed=1, c=c)
        t2 = plants.tree("tree_b", 6.2, 2.8, seed=5, leaf=('#33521f', '#6a8f33'), c=c)
        t3 = plants.tree("tree_c", 9.5, 4.0, seed=9, leaf=('#243f1a', '#476b27'), c=c)
        t1.location, t2.location, t3.location = (-13.5, 23.0, 0), (30.5, -4.0, 0), (-16.0, -7.0, 0)
        kinds = (t1, t2, t3)
        extra = [(-22, -21.0, .1), (-4, -29.3, .3), (22, -29.5, .5), (49, -29.2, .7), (-30, -29.4, .9), (31, 22.5, .2),
                 (12, 24.0, .4), (-2, 23.5, .6), (33, 12.0, .8), (-15.5, 9.0, .15), (76, -29.3, .35), (-58, -29.6, .55)]
        for k, (x, y, r) in enumerate(tree_spots + extra):
            inst(kinds[k % 3], (x, y, 0), r * 360, c, scale=0.8 + 0.5 * ((k * 37) % 10) / 10)
    return lights


def build_site(context=True, grass=True, trees=True):
    coll("SITE")
    lights = []
    build_fence(lights)
    build_gatehouse()
    lawns = build_ground()
    build_services()
    build_roof_plant()
    coll("SITE")
    build_planting(lawns, grass)
    st = build_context(trees) if context else []
    coll("SITE")
    return lights, st
