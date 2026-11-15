"""Duplex architecture: plan-driven shell.

The whole building is generated from one description of the plan:
room polygons per floor + a list of openings.  Walls are the footprint minus
the rooms, cut in horizontal bands wherever an opening starts or stops, so no
booleans are needed and every wall face can be given the finish of the room
(or facade) it looks onto.

Axes: X east, Y north, Z up.  The street / front of the house is at -Y.
"""
import math

import bpy
from mathutils import Matrix, Vector
from shapely.geometry import Point, box as B
from shapely.ops import unary_union

from bk import mats
from bk.core import MB, R, T, TR, coll, fillet, rad

# ---------------------------------------------------------------------------
# levels
# ---------------------------------------------------------------------------
Z0 = 0.45            # ground floor finished level (top of plinth)
H0 = 3.15            # ground floor clear height
SL = 0.25            # slab thickness
Z1 = Z0 + H0 + SL    # first floor finished level  (3.85)
H1 = 3.00            # first floor clear height
ZR = Z1 + H1         # underside of roof slab      (6.85)
ZRT = ZR + SL        # top of roof slab            (7.10)
ZP = 7.95            # top of parapet
W, D = 16.0, 12.5    # main footprint
FIN_T = 0.02         # floor finish thickness
BASE = {0: Z0, 1: Z1}
HGT = {0: H0, 1: H1}

RISE, GOING, NRISE = 0.17, 0.28, 20
ST_Y0 = 8.43         # first riser of the up-flight
ST_YL = ST_Y0 + 9 * GOING   # start of landing (10.95)
STAIR_VOID = B(8.0, ST_Y0, 10.6, 12.25)

# ---------------------------------------------------------------------------
# plan
# ---------------------------------------------------------------------------
PORCH = B(7.0, -1.0, 10.5, 1.6)
FP = {
    0: B(0, 0, W, D).difference(PORCH),
    1: B(0, 0, W, D).union(B(6.6, -0.8, 10.9, 0.0)),
}
ROOMS = {
    0: {
        'living': B(0.25, 0.25, 6.75, 6.6),
        'dining': B(0.25, 6.75, 6.75, 12.25),
        'hall': B(6.9, 1.85, 10.6, 12.25),
        'guest': B(10.75, 0.25, 15.75, 4.6),
        'lobby': B(10.75, 4.75, 11.9, 6.6),
        'powder': B(12.05, 4.75, 13.25, 6.6),
        'guest_bath': B(13.4, 4.75, 15.75, 6.6),
        'kitchen': B(10.75, 6.75, 15.75, 12.25),
    },
    1: {
        'master': B(0.25, 0.25, 6.75, 5.6),
        'm_bath': B(0.25, 5.75, 3.6, 8.3),
        'm_dress': B(3.75, 5.75, 6.75, 8.3),
        'bed3': B(0.25, 8.45, 4.9, 12.25),
        'bed3_pass': B(5.05, 8.45, 6.75, 9.45),
        'bed3_bath': B(5.05, 9.6, 6.75, 12.25),
        'lounge': B(6.9, -0.55, 10.6, 12.25),
        'bed2': B(10.75, 0.25, 15.75, 4.6),
        'ff_lobby': B(10.75, 4.75, 13.25, 6.6),
        'bed2_bath': B(13.4, 4.75, 15.75, 6.6),
        'bed4': B(10.75, 6.75, 13.45, 12.25).union(B(10.75, 9.0, 15.75, 12.25)),
        'bed4_bath': B(13.6, 6.75, 15.75, 8.85),
    },
}


class Op:
    """An opening in a wall.  axis 'x': the wall runs along X, (a, b) is the X range and
    (w0, w1) the Y range of the wall thickness; axis 'y' the other way round.
    ext: which side is 'side A' (the exterior for facade openings): S/N for axis x, W/E for axis y.
    z0/z1 are relative to the floor's finished level."""

    def __init__(self, name, fl, axis, a, b, w0, w1, z0, z1, ext, kind, **kw):
        self.name, self.fl, self.axis = name, fl, axis
        self.a, self.b, self.w0, self.w1 = a, b, w0, w1
        self.z0, self.z1, self.ext, self.kind = z0, z1, ext, kind
        self.kw = kw

    @property
    def w(self):
        return self.b - self.a

    @property
    def h(self):
        return self.z1 - self.z0

    @property
    def t(self):
        return self.w1 - self.w0

    def rect(self, grow=0.01, along=0.0):
        if self.axis == 'x':
            return B(self.a - along, self.w0 - grow, self.b + along, self.w1 + grow)
        return B(self.w0 - grow, self.a - along, self.w1 + grow, self.b + along)

    def matrix(self, dz=0.0):
        z = BASE[self.fl] + self.z0 + dz
        if self.axis == 'x':
            if self.ext == 'S':
                return Matrix(((1, 0, 0, self.a), (0, 1, 0, self.w0), (0, 0, 1, z), (0, 0, 0, 1)))
            return Matrix(((-1, 0, 0, self.b), (0, -1, 0, self.w1), (0, 0, 1, z), (0, 0, 0, 1)))
        if self.ext == 'W':
            return Matrix(((0, 1, 0, self.w0), (-1, 0, 0, self.b), (0, 0, 1, z), (0, 0, 0, 1)))
        return Matrix(((0, -1, 0, self.w1), (1, 0, 0, self.a), (0, 0, 1, z), (0, 0, 0, 1)))

    def centre(self):
        if self.axis == 'x':
            return ((self.a + self.b) / 2, (self.w0 + self.w1) / 2)
        return ((self.w0 + self.w1) / 2, (self.a + self.b) / 2)

    def exterior(self):
        return self.kw.get('exterior', self.kind in ('slide', 'fixed', 'case', 'frost', 'entry', 'ext_door', 'cut'))


OPS = []


def op(*a, **k):
    o = Op(*a, **k)
    OPS.append(o)
    return o


def define_openings():
    OPS.clear()
    # ------------------------------ ground floor: facade -------------------
    op('living_front', 0, 'x', 1.2, 5.8, 0.0, 0.25, 0.0, 2.7, 'S', 'slide', panels=4, curtain='both')
    op('living_slit1', 0, 'y', 0.9, 1.45, 0.0, 0.25, 0.25, 2.7, 'W', 'fixed', cols=1)
    op('living_slit2', 0, 'y', 5.4, 5.95, 0.0, 0.25, 0.25, 2.7, 'W', 'fixed', cols=1)
    op('dining_west', 0, 'y', 7.6, 11.4, 0.0, 0.25, 0.0, 2.7, 'W', 'slide', panels=4, curtain='sheer')
    op('dining_north', 0, 'x', 2.0, 5.0, 12.25, 12.5, 0.9, 2.5, 'N', 'case', cols=3, surround=True, curtain='blind')
    op('hall_back', 0, 'x', 7.0, 7.9, 12.25, 12.5, 0.0, 2.2, 'N', 'ext_door')
    op('stair_win_gf', 0, 'x', 8.7, 10.1, 12.25, 12.5, 2.45, H0, 'N', 'cut')
    op('entry', 0, 'x', 7.15, 10.35, 1.6, 1.85, 0.0, 2.75, 'S', 'entry')
    op('guest_front', 0, 'x', 11.9, 14.6, 0.0, 0.25, 0.75, 2.5, 'S', 'case', cols=3, curtain='both')
    op('guest_east', 0, 'y', 1.5, 3.3, 15.75, 16.0, 0.9, 2.5, 'E', 'case', cols=2, surround=True, curtain='drape')
    op('gbath_east', 0, 'y', 5.3, 6.1, 15.75, 16.0, 1.55, 2.35, 'E', 'frost', surround=True)
    op('kitchen_door', 0, 'y', 7.05, 7.95, 15.75, 16.0, 0.0, 2.2, 'E', 'ext_door', glazed=True)
    op('kitchen_north', 0, 'x', 11.35, 13.75, 12.25, 12.5, 1.1, 2.3, 'N', 'case', cols=3, surround=True)
    op('kitchen_east', 0, 'y', 9.2, 10.6, 15.75, 16.0, 1.1, 2.3, 'E', 'case', cols=2, surround=True)
    # ------------------------------ ground floor: interior -----------------
    op('living_dining', 0, 'x', 1.2, 5.8, 6.6, 6.75, 0.0, 2.75, 'S', 'open')
    op('living_hall', 0, 'y', 2.6, 4.8, 6.75, 6.9, 0.0, 2.75, 'W', 'open')
    op('dining_hall', 0, 'y', 7.5, 9.3, 6.75, 6.9, 0.0, 2.75, 'W', 'open')
    op('hall_kitchen', 0, 'y', 6.95, 7.85, 10.6, 10.75, 0.0, 2.2, 'W', 'door', swing=78, hinge='R', into='B')
    op('hall_lobby', 0, 'y', 5.1, 6.1, 10.6, 10.75, 0.0, 2.3, 'W', 'open')
    op('lobby_guest', 0, 'x', 10.9, 11.8, 4.6, 4.75, 0.0, 2.2, 'N', 'door', swing=35, hinge='L', into='B')
    op('lobby_powder', 0, 'y', 5.2, 6.0, 11.9, 12.05, 0.0, 2.2, 'W', 'door', swing=0, hinge='L', into='B')
    op('guest_bath', 0, 'x', 14.3, 15.1, 4.6, 4.75, 0.0, 2.2, 'S', 'door', swing=70, hinge='R', into='B')
    # ------------------------------ first floor: facade --------------------
    op('master_front', 1, 'x', 1.4, 5.4, 0.0, 0.25, 0.0, 2.5, 'S', 'slide', panels=4, curtain='both')
    op('master_west', 1, 'y', 1.6, 4.2, 0.0, 0.25, 0.6, 2.4, 'W', 'case', cols=3, surround=True, curtain='sheer')
    op('mbath_west', 1, 'y', 6.4, 7.7, 0.0, 0.25, 1.15, 2.3, 'W', 'frost', surround=True)
    op('bed3_north', 1, 'x', 1.3, 3.7, 12.25, 12.5, 0.9, 2.4, 'N', 'case', cols=3, surround=True, curtain='both')
    op('bed3_west', 1, 'y', 9.6, 11.2, 0.0, 0.25, 0.9, 2.4, 'W', 'case', cols=2, surround=True, curtain='drape')
    op('b3bath_north', 1, 'x', 5.5, 6.3, 12.25, 12.5, 1.5, 2.3, 'N', 'frost', surround=True)
    op('lounge_front', 1, 'x', 7.35, 10.15, -0.8, -0.55, 0.3, 2.65, 'S', 'fixed', cols=3, curtain='sheer')
    op('stair_win_ff', 1, 'x', 8.7, 10.1, 12.25, 12.5, 0.0, 2.45, 'N', 'cut')
    op('corridor_north', 1, 'x', 7.05, 7.85, 12.25, 12.5, 0.9, 2.4, 'N', 'case', cols=1, surround=True)
    op('bed2_front', 1, 'x', 11.6, 14.9, 0.0, 0.25, 0.0, 2.4, 'S', 'slide', panels=3, curtain='both')
    op('bed2_east', 1, 'y', 1.5, 3.3, 15.75, 16.0, 0.9, 2.4, 'E', 'case', cols=2, surround=True, curtain='drape')
    op('b2bath_east', 1, 'y', 5.3, 6.1, 15.75, 16.0, 1.5, 2.3, 'E', 'frost', surround=True)
    op('bed4_north', 1, 'x', 11.6, 14.6, 12.25, 12.5, 0.9, 2.4, 'N', 'case', cols=3, surround=True, curtain='both')
    op('bed4_east', 1, 'y', 9.8, 11.6, 15.75, 16.0, 0.9, 2.4, 'E', 'case', cols=2, surround=True, curtain='drape')
    op('b4bath_east', 1, 'y', 7.4, 8.2, 15.75, 16.0, 1.5, 2.3, 'E', 'frost', surround=True)
    # ------------------------------ first floor: interior ------------------
    op('master_door', 1, 'y', 4.2, 5.1, 6.75, 6.9, 0.0, 2.2, 'E', 'door', swing=60, hinge='R', into='B')
    op('master_dress', 1, 'x', 5.5, 6.4, 5.6, 5.75, 0.0, 2.2, 'S', 'door', swing=80, hinge='R', into='B')
    op('dress_bath', 1, 'y', 6.6, 7.4, 3.6, 3.75, 0.0, 2.2, 'E', 'door', swing=75, hinge='L', into='B')
    op('bed3_passage', 1, 'y', 8.5, 9.4, 6.75, 6.9, 0.0, 2.3, 'E', 'open')
    op('bed3_door', 1, 'y', 8.5, 9.4, 4.9, 5.05, 0.0, 2.2, 'E', 'door', swing=65, hinge='L', into='B')
    op('bed3_bathdoor', 1, 'y', 10.3, 11.1, 4.9, 5.05, 0.0, 2.2, 'W', 'door', swing=0, hinge='R', into='B')
    op('lounge_lobby', 1, 'y', 5.2, 6.2, 10.6, 10.75, 0.0, 2.3, 'W', 'open')
    op('bed2_door', 1, 'x', 11.0, 11.9, 4.6, 4.75, 0.0, 2.2, 'N', 'door', swing=30, hinge='L', into='B')
    op('bed2_bathdoor', 1, 'x', 14.3, 15.1, 4.6, 4.75, 0.0, 2.2, 'S', 'door', swing=0, hinge='R', into='B')
    op('bed4_door', 1, 'x', 11.0, 11.9, 6.6, 6.75, 0.0, 2.2, 'S', 'door', swing=40, hinge='R', into='B')
    op('bed4_bathdoor', 1, 'y', 7.4, 8.2, 13.45, 13.6, 0.0, 2.2, 'W', 'door', swing=0, hinge='L', into='B')
    return OPS


def get_op(name):
    for o in OPS:
        if o.name == name:
            return o
    raise KeyError(name)


# ---------------------------------------------------------------------------
# finishes
# ---------------------------------------------------------------------------
class Fin:
    """Material palette, created lazily so the module can be imported before bpy data exists."""
    _c = {}

    def __getattr__(self, k):
        if k not in self._c:
            self._c[k] = getattr(self, '_' + k)()
        return self._c[k]

    # exterior
    def _ext_white(self): return mats.stucco("ext_render_white", '#efebe2')
    def _ext_dark(self): return mats.stucco("ext_render_charcoal", '#34373a', grain=0.7, dirt=0.03)
    def _plinth(self): return mats.stucco("ext_plinth", '#4b4c4d', grain=1.4, dirt=0.1)
    def _stone(self): return mats.stone_cladding()
    def _coping(self): return mats.concrete("coping", '#5a5b5c', rough=0.7, bump=0.15)
    def _slat(self): return mats.wood('teak', gloss=0.15, name="slat_teak")
    def _slat_back(self): return mats.plain("slat_backing", '#141516', rough=0.8)
    def _roof(self): return mats.concrete("roof_screed", '#a9a8a2', rough=0.85, bump=0.2)
    # interior shell
    def _wall(self): return mats.paint("wall_white", '#f1eee7')
    def _wall_warm(self): return mats.paint("wall_warm", '#e7dfd0')
    def _wall_greige(self): return mats.paint("wall_greige", '#c3baaa')
    def _wall_sage(self): return mats.paint("wall_sage", '#a9b3a0')
    def _wall_blue(self): return mats.paint("wall_dustblue", '#9fb0bd')
    def _wall_blush(self): return mats.paint("wall_blush", '#dcc3b7')
    def _ceiling(self): return mats.paint("ceiling_white", '#f6f5f1', rough=0.75, texture=0.1)
    def _skirt(self): return mats.plain("skirting_white", '#f3f1ec', rough=0.3)
    def _floor_main(self): return mats.tiles('calacatta', (1.2, 0.6), grout='#d8d3c8', gw=0.002, rough=0.06,
                                            name="floor_porcelain_calacatta", scale=0.45, variation=0.02, bump=0.3, cloud=0.16, veins=0.75)
    def _floor_wood(self): return mats.wood_planks('oak', (1.6, 0.16), gloss=0.12, name="floor_oak")
    def _floor_wood_dark(self): return mats.wood_planks('walnut', (1.6, 0.16), gloss=0.15, name="floor_walnut")
    def _floor_bath(self): return mats.tiles('grey', (0.6, 0.6), grout='#55565a', rough=0.35, pattern='plain',
                                            color='#6f7073', name="floor_bath_grey", bump=0.5)
    def _floor_bath_dark(self): return mats.tiles('nero', (0.6, 0.6), grout='#1c1c1d', rough=0.25, pattern='plain',
                                                 color='#2b2c2e', name="floor_bath_dark", bump=0.5)
    def _wall_bath(self): return mats.tiles('carrara', (0.6, 1.2), grout='#d9d7d2', gw=0.002, rough=0.08,
                                           name="wall_tile_carrara", scale=0.5, variation=0.02, bump=0.3)
    def _wall_bath_stat(self): return mats.tiles('statuario', (0.8, 1.6), grout='#e2e0db', gw=0.0015, rough=0.06,
                                                name="wall_tile_statuario", scale=0.4, variation=0.015, bump=0.25)
    def _wall_bath_beige(self): return mats.tiles('crema', (0.3, 0.6), grout='#cfc6b4', gw=0.002, rough=0.12,
                                                 name="wall_tile_crema", scale=0.8, variation=0.03, bump=0.4)
    def _wall_kitchen(self): return mats.paint("wall_kitchen", '#eeece6', rough=0.45)
    def _threshold(self): return mats.marble('nero', 0.08, name="threshold_nero")
    def _terrace(self): return mats.tiles('grey', (0.6, 0.6), grout='#6d6c69', rough=0.5, pattern='plain',
                                          color='#9c9a95', name="terrace_tile", bump=0.6)
    def _porch(self): return mats.granite("porch_granite", '#3a3b3d', rough=0.2)
    # joinery / glazing
    def _frame(self): return mats.alu_dark()
    def _glass(self): return mats.glass("glass_window", tint=(0.86, 0.93, 0.92))
    def _glass_clear(self): return mats.glass("glass_balustrade", tint=(0.9, 0.96, 0.95))
    def _frost(self): return mats.glass_frosted()
    def _door(self): return mats.wood('walnut', gloss=0.25, name="door_walnut")
    def _door_frame(self): return mats.wood('walnut_dark', gloss=0.2, name="doorframe_walnut")
    def _entry_door(self): return mats.wood('iroko', gloss=0.35, name="entry_iroko")
    def _steel(self): return mats.steel()
    def _chrome(self): return mats.chrome()
    def _brass(self): return mats.brass()
    def _black(self): return mats.black_metal()
    def _sill(self): return mats.granite("sill_granite", '#2c2d2f', rough=0.25)
    def _tread(self): return mats.wood('walnut', gloss=0.3, name="stair_tread_walnut")
    def _riser(self): return mats.marble('carrara', 0.1, name="stair_riser_marble")
    def _stair_conc(self): return mats.paint("stair_soffit", '#f1eee7')


F = Fin()

ROOM_FIN = {
    # room: (floor, wall)
    'living': ('floor_main', 'wall'), 'dining': ('floor_main', 'wall_warm'), 'hall': ('floor_main', 'wall'),
    'guest': ('floor_wood', 'wall_greige'), 'lobby': ('floor_main', 'wall'), 'powder': ('floor_bath_dark', 'wall_bath_beige'),
    'guest_bath': ('floor_bath', 'wall_bath'), 'kitchen': ('floor_main', 'wall_kitchen'),
    'master': ('floor_wood_dark', 'wall_warm'), 'm_bath': ('floor_bath_dark', 'wall_bath_stat'),
    'm_dress': ('floor_wood_dark', 'wall'), 'bed3': ('floor_wood', 'wall_sage'), 'bed3_pass': ('floor_wood', 'wall'),
    'bed3_bath': ('floor_bath', 'wall_bath'), 'lounge': ('floor_main', 'wall'), 'bed2': ('floor_wood', 'wall_blue'),
    'ff_lobby': ('floor_main', 'wall'), 'bed2_bath': ('floor_bath', 'wall_bath_beige'),
    'bed4': ('floor_wood', 'wall_blush'), 'bed4_bath': ('floor_bath', 'wall_bath'),
}


def ext_mat(x, y, z):
    """Facade finish by position (overlays add stone / timber on top of this)."""
    if 6.5 < x < 11.0 and y < 0.3 and z > Z0 + H0 - 0.05:
        return F.ext_dark            # the centre box over the entrance
    return F.ext_white


# ---------------------------------------------------------------------------
# shell
# ---------------------------------------------------------------------------
def shell_coll(fl):
    """Per-level collections so cutaway views can hide the storey above."""
    arch = coll("ARCH", activate=False)
    return coll({0: "GF_SHELL", 1: "FF_SHELL", 2: "ROOF"}[fl], arch, activate=False)


def build_walls(fl):
    base, H = BASE[fl], HGT[fl]
    fp, rooms = FP[fl], ROOMS[fl]
    solid = fp.difference(unary_union(list(rooms.values())))
    ops = [o for o in OPS if o.fl == fl]
    zs = sorted(set([-FIN_T, H] + [round(o.z0 if o.z0 > 0 else -FIN_T, 4) for o in ops] + [round(o.z1, 4) for o in ops]))
    mb = MB(f"walls_{fl}")

    def side_fn(x, y, nx, ny, z):
        p = Point(x + nx * 0.04, y + ny * 0.04)
        for name, poly in rooms.items():
            if poly.contains(p):
                return getattr(F, ROOM_FIN[name][1])
        if not fp.contains(p):
            return ext_mat(x, y, z)
        return F.wall

    for za, zb in zip(zs, zs[1:]):
        if zb - za < 1e-4:
            continue
        cut = [o.rect() for o in ops if (o.z0 if o.z0 > 0 else -FIN_T) <= za + 1e-4 and o.z1 >= zb - 1e-4]
        p = solid.difference(unary_union(cut)) if cut else solid
        mb.prism(p, base + za, base + zb, F.wall, side_fn=side_fn)
    return mb.finish(c=shell_coll(fl))


def build_floors_ceilings(fl):
    base, H = BASE[fl], HGT[fl]
    mb = MB(f"floors_{fl}")
    for name, poly in ROOMS[fl].items():
        p = poly.difference(STAIR_VOID) if (fl == 1 and name == 'lounge') else poly
        mb.prism(p, base - FIN_T, base, getattr(F, ROOM_FIN[name][0]), bottom=False, side=False)
    # door thresholds
    for o in OPS:
        if o.fl == fl and o.z0 == 0 and o.kind in ('door', 'open'):
            tm = F.threshold if o.kind == 'door' else getattr(F, o.kw.get('floor', 'floor_main'))
            mb.prism(o.rect(grow=0.0), base - FIN_T, base, tm, bottom=False, side=False)
    o = mb.finish(c=shell_coll(fl))
    # skirting
    sk = MB(f"skirting_{fl}")
    cuts = unary_union([q.rect(grow=0.06, along=0.035) for q in OPS if q.fl == fl and q.z0 == 0])
    for name, poly in ROOMS[fl].items():
        if 'bath' in name or name in ('powder', 'kitchen'):
            continue
        ring = poly.difference(poly.buffer(-0.014, join_style=2)).difference(cuts)
        if fl == 1 and name == 'lounge':
            ring = ring.difference(STAIR_VOID.buffer(0.02))
        sk.prism(ring, base, base + 0.1, F.skirt, bottom=False)
    sk.finish(c=shell_coll(fl))
    return o


def build_slabs():
    mb = MB("plinth")
    # plinth: full ground-floor footprint incl. porch platform
    plinth = B(0, 0, W, D).union(B(7.0, -1.0, 10.5, 1.6))
    mb.prism(plinth, 0.0, Z0 - FIN_T, F.plinth, mat_side=F.plinth, bottom=False)
    mb.finish(c=shell_coll(0))
    mb = MB("slab_first_floor")
    # first floor slab: everything under the first floor + balconies, minus the stairwell
    win = get_op('stair_win_gf').rect(grow=0.02)
    s1 = FP[0].union(FP[1]).union(PORCH.intersection(B(0, 0, W, D)))
    s1 = s1.difference(STAIR_VOID).difference(win)
    mb.prism(s1, Z0 + H0, Z1 - FIN_T, F.ext_white, mat_bottom=F.ceiling,
             side_fn=lambda x, y, nx, ny, z: ext_mat(x, y, z) if not FP[1].contains(Point(x + nx * .04, y + ny * .04)) else F.wall)
    mb.finish(c=shell_coll(1))
    # roof slab
    mb = MB("roof")
    mb.prism(FP[1], ZR, ZRT, F.roof, mat_bottom=F.ceiling,
             side_fn=lambda x, y, nx, ny, z: ext_mat(x, y, z))
    # parapet + coping
    par = FP[1].difference(FP[1].buffer(-0.2, join_style=2))
    mb.prism(par, ZRT, ZP, F.ext_white, side_fn=lambda x, y, nx, ny, z: ext_mat(x, y, z) if not FP[1].buffer(-0.1).contains(Point(x + nx * .04, y + ny * .04)) else F.ext_white, bottom=False)
    cop = FP[1].buffer(0.035, join_style=2).difference(FP[1].buffer(-0.235, join_style=2))
    mb.prism(cop, ZP, ZP + 0.06, F.coping)
    return mb.finish(c=shell_coll(2))


# ---------------------------------------------------------------------------
# windows
# ---------------------------------------------------------------------------
def _sash(mb, x, y, z, w, h, d=0.032, st=0.05, glass=None, frame=None):
    """One glazed sash / panel: four members and the pane."""
    mb.bx(x, y, z, x + st, y + d, z + h, frame)
    mb.bx(x + w - st, y, z, x + w, y + d, z + h, frame)
    mb.bx(x + st, y, z + h - st, x + w - st, y + d, z + h, frame)
    mb.bx(x + st, y, z, x + w - st, y + d, z + st, frame)
    yc = y + d / 2
    mb.bx(x + st - 0.004, yc - 0.004, z + st - 0.004, x + w - st + 0.004, yc + 0.004, z + h - st + 0.004, glass)


def window_unit(mb, o):
    """Builds a window / glazed door in the opening's local frame:
    x 0..w along the wall, y 0 (outside face) .. t (inside face), z 0..h."""
    w, h, t, k = o.w, o.h, o.t, o.kind
    fr, dp, inset = 0.055, 0.09, 0.07
    frame, glass = F.frame, (F.frost if k == 'frost' else F.glass)
    y0, y1 = inset, inset + dp
    door_like = o.z0 == 0
    sill_h = 0.03 if door_like else fr
    mb.bx(0, y0, 0, fr, y1, h, frame)
    mb.bx(w - fr, y0, 0, w, y1, h, frame)
    mb.bx(fr, y0, h - fr, w - fr, y1, h, frame)
    mb.bx(fr, y0, 0, w - fr, y1, sill_h, frame)
    iw, ih, zi = w - 2 * fr, h - fr - sill_h, sill_h
    if k == 'slide':
        n = o.kw.get('panels', 2)
        ov = 0.05
        pw = (iw + (n - 1) * ov) / n
        opened = o.kw.get('open', 0.0)
        for i in range(n):
            x = fr + i * (pw - ov)
            trk = i % 2
            if opened and i == 1:
                x -= opened * (pw - ov)
            yy = y0 + 0.008 + trk * 0.04
            _sash(mb, x, yy, zi, pw, ih, 0.034, 0.055, glass, frame)
            # pull handle on the meeting stile
            hx = x + (0.0275 if i % 2 else pw - 0.0275)
            mb.bx(hx - 0.008, yy + 0.034, zi + 0.95, hx + 0.008, yy + 0.052, zi + 1.2, F.steel, bevel=0.003)
    elif k in ('fixed', 'case', 'frost'):
        n = o.kw.get('cols', 2)
        mw = 0.045
        pw = (iw - (n - 1) * mw) / n
        for i in range(n):
            x = fr + i * (pw + mw)
            if i:
                mb.bx(x - mw, y0, zi, x, y1, zi + ih, frame)
            operable = (k == 'case' and (i % 2 == 0 or n == 1)) or k == 'frost'
            if operable:
                _sash(mb, x, y0 + 0.02, zi, pw, ih, 0.05, 0.045, glass, frame)
                # casement handle
                hx = x + pw - 0.022
                mb.bx(hx - 0.009, y0 + 0.07, zi + ih / 2 - 0.06, hx + 0.009, y0 + 0.082, zi + ih / 2 + 0.06, frame, bevel=0.002)
                mb.bx(hx - 0.006, y0 + 0.082, zi + ih / 2 - 0.01, hx + 0.006, y0 + 0.11, zi + ih / 2 + 0.1, F.steel, bevel=0.003)
            else:
                yc = (y0 + y1) / 2
                mb.bx(x - 0.004, yc - 0.005, zi - 0.004, x + pw + 0.004, yc + 0.005, zi + ih + 0.004, glass)
    # external sill + interior window board
    if not door_like:
        mb.bx(-0.03, -0.045, -0.035, w + 0.03, inset + 0.01, 0.0, F.sill, bevel=0.004)
        mb.bx(-0.02, y1 - 0.005, -0.025, w + 0.02, t + 0.03, 0.0, F.sill, bevel=0.004)
    else:
        mb.bx(0, 0.0, -FIN_T, w, t, 0.0, F.sill)
    if o.kw.get('surround'):
        pr, th = 0.2, 0.06
        dk = F.ext_dark
        mb.bx(-th, -pr, -0.035 - th, w + th, 0.0, -0.035, dk)
        mb.bx(-th, -pr, h, w + th, 0.0, h + th, dk)
        mb.bx(-th, -pr, -0.035, 0.0, 0.0, h, dk)
        mb.bx(w, -pr, -0.035, w + th, 0.0, h, dk)


def door_unit(mb, o):
    """Interior hinged door: lining, architraves both sides, leaf with lever handles and hinges."""
    w, h, t = o.w, o.h, o.t
    swing, hinge, into = o.kw.get('swing', 0), o.kw.get('hinge', 'L'), o.kw.get('into', 'B')
    jt = 0.03
    fm, lm = F.door_frame, F.door
    mb.bx(0, -0.002, 0, jt, t + 0.002, h, fm)
    mb.bx(w - jt, -0.002, 0, w, t + 0.002, h, fm)
    mb.bx(jt, -0.002, h - jt, w - jt, t + 0.002, h, fm)
    for ys in (-0.016, t + 0.002):
        mb.bx(-0.06, ys, 0, jt * 0.5, ys + 0.014, h + 0.06, fm, bevel=0.003)
        mb.bx(w - jt * 0.5, ys, 0, w + 0.06, ys + 0.014, h + 0.06, fm, bevel=0.003)
        mb.bx(jt * 0.5, ys, h - jt * 0.5, w - jt * 0.5, ys + 0.014, h + 0.06, fm, bevel=0.003)
    lw, lh, lt = w - 2 * jt - 0.006, h - jt - 0.01, 0.042
    # local frame of the leaf: hinge line at origin, leaf along +x, thickness on -y, swings toward +y
    if into == 'B':
        M = T(jt + 0.003, t, 0.006)
        flip_y = 1
    else:
        M = T(jt + 0.003, 0.0, 0.006) @ Matrix.Diagonal((1, -1, 1, 1))
        flip_y = -1
    if hinge == 'R':
        M = T(w, 0, 0) @ Matrix.Diagonal((-1, 1, 1, 1)) @ M
    mb.push(M @ R(swing))
    mb.bx(0, -lt, 0, lw, 0, lh, lm, bevel=0.002)
    for zz in (lh * 0.25, lh * 0.5, lh * 0.75):           # inlay lines
        for yy in (-lt - 0.0006, 0.0):
            mb.bx(0.0, yy, zz - 0.003, lw, yy + 0.0006, zz + 0.003, F.brass)
    for yy, sgn in ((-lt, -1), (0.0, 1)):                 # handle sets
        mb.cyl(0.026, 0.008, (lw - 0.065, yy + sgn * 0.004, 1.0), F.steel, segs=24, axis='Y')
        mb.cyl(0.009, 0.045, (lw - 0.065, yy + sgn * 0.026, 1.0), F.steel, segs=12, axis='Y')
        mb.box((0.125, 0.012, 0.02), (lw - 0.065 - 0.05, yy + sgn * 0.05, 1.0), F.steel, bevel=0.004)
        mb.cyl(0.022, 0.006, (lw - 0.065, yy + sgn * 0.003, 0.9), F.steel, segs=20, axis='Y')
    for zz in (0.2, lh / 2, lh - 0.2):                    # hinges
        mb.cyl(0.007, 0.09, (-0.002, 0.004, zz), F.steel, segs=10)
    mb.pop()


def ext_door_unit(mb, o):
    """Service door to the yard: steel frame, flush or half-glazed leaf."""
    w, h, t = o.w, o.h, o.t
    fr = 0.055
    y0, y1 = 0.07, 0.15
    f = F.frame
    mb.bx(0, y0, 0, fr, y1, h, f)
    mb.bx(w - fr, y0, 0, w, y1, h, f)
    mb.bx(fr, y0, h - fr, w - fr, y1, h, f)
    lw, lh = w - 2 * fr - 0.006, h - fr - 0.012
    x0 = fr + 0.003
    if o.kw.get('glazed'):
        _sash(mb, x0, y0 + 0.02, 0.008, lw, lh, 0.045, 0.1, F.glass, f)
        mb.bx(x0 + 0.1, y0 + 0.02, 0.9, x0 + lw - 0.1, y0 + 0.065, 1.0, f)
    else:
        mb.bx(x0, y0 + 0.02, 0.008, x0 + lw, y0 + 0.065, 0.008 + lh, mats.plain("door_grey", '#55585b', rough=0.4), bevel=0.003)
    for yy, s in ((y0 + 0.02, -1), (y0 + 0.065, 1)):
        mb.box((0.13, 0.014, 0.022), (x0 + lw - 0.12, yy + s * 0.045, 1.02), F.steel, bevel=0.004)
        mb.cyl(0.024, 0.01, (x0 + lw - 0.07, yy + s * 0.005, 1.02), F.steel, segs=20, axis='Y')
    mb.bx(0, 0, -FIN_T, w, t, 0.0, F.sill)


def entry_unit(mb, o):
    """Front entrance: frame, two glazed sidelights and a pair of tall timber leaves with pull bars."""
    w, h, t = o.w, o.h, o.t
    fr = 0.07
    y0, y1 = 0.06, 0.2
    f = F.frame
    side = 0.55
    mb.bx(0, y0, 0, fr, y1, h, f)
    mb.bx(w - fr, y0, 0, w, y1, h, f)
    mb.bx(fr, y0, h - fr, w - fr, y1, h, f)
    mb.bx(fr + side, y0, 0, fr + side + fr, y1, h - fr, f)
    mb.bx(w - fr - side - fr, y0, 0, w - fr - side, y1, h - fr, f)
    yc = (y0 + y1) / 2
    for xa, xb in ((fr, fr + side), (w - fr - side, w - fr)):
        mb.bx(xa - 0.004, yc - 0.006, 0.0, xb + 0.004, yc + 0.006, h - fr + 0.004, F.glass)
        mb.bx(xa, y0, 0, xb, y1, 0.07, f)
    dx0, dx1 = fr + side + fr, w - fr - side - fr
    lw = (dx1 - dx0 - 0.012) / 2
    lh = h - fr - 0.012
    wood = F.entry_door
    for i, (xh, sgn) in enumerate(((dx0 + 0.003, 1), (dx1 - 0.003, -1))):
        ang = o.kw.get('swing', 0) if i == 0 else 0
        M = T(xh, y0 + 0.04, 0.006)
        if sgn < 0:
            M = M @ Matrix.Diagonal((-1, 1, 1, 1))
        mb.push(M @ R(ang))
        mb.bx(0, 0, 0, lw, 0.06, lh, wood, bevel=0.003)
        n = 7
        for j in range(1, n):                               # vertical grooves
            xx = lw * j / n
            for yy in (-0.0008, 0.06):
                mb.bx(xx - 0.004, yy, 0.03, xx + 0.004, yy + 0.0008, lh - 0.03, F.black)
        for yy, s in ((0.0, -1), (0.06, 1)):                # pull bars
            xb = lw - 0.11
            mb.cyl(0.016, 1.5, (xb, yy + s * 0.07, 1.25), F.steel, segs=20)
            for zz in (0.65, 1.85):
                mb.cyl(0.009, 0.07, (xb, yy + s * 0.035, zz), F.steel, segs=12, axis='Y')
        mb.cyl(0.03, 0.01, (lw - 0.11, -0.005, 0.95), F.steel, segs=20, axis='Y')
        mb.pop()
    mb.bx(0, 0, -FIN_T, w, t, 0.0, F.sill)


def build_openings():
    wins = {0: MB("windows_gf"), 1: MB("windows_ff")}
    drss = {0: MB("doors_gf"), 1: MB("doors_ff")}
    for o in OPS:
        win, drs = wins[o.fl], drss[o.fl]
        if o.kind in ('slide', 'fixed', 'case', 'frost'):
            win.push(o.matrix())
            window_unit(win, o)
            win.pop()
        elif o.kind == 'door':
            drs.push(o.matrix())
            door_unit(drs, o)
            drs.pop()
        elif o.kind == 'ext_door':
            drs.push(o.matrix())
            ext_door_unit(drs, o)
            drs.pop()
        elif o.kind == 'entry':
            drs.push(o.matrix())
            entry_unit(drs, o)
            drs.pop()
    # the tall stair window spans both floors
    g = get_op('stair_win_gf')
    tall = Op('stair_win', 0, 'x', g.a, g.b, g.w0, g.w1, g.z0, (Z1 - Z0) + get_op('stair_win_ff').z1, 'N', 'fixed',
              cols=2, surround=True)
    win = MB("window_stair_tall")
    win.push(tall.matrix())
    window_unit(win, tall)
    # transoms on the tall window
    for zz in (1.1, 2.2):
        win.bx(0.055, 0.07, zz, tall.w - 0.055, 0.16, zz + 0.045, F.frame)
    win.pop()
    win.finish(sharp=35, c=shell_coll(1))
    for fl in (0, 1):
        wins[fl].finish(sharp=35, c=shell_coll(fl))
        drss[fl].finish(sharp=35, c=shell_coll(fl))


# ---------------------------------------------------------------------------
# stairs + balustrades
# ---------------------------------------------------------------------------
def glass_rail(mb, pts, h=1.05, panel=1.25, gap=0.012, rail=True, shoe=True, zs=None):
    """Frameless glass balustrade along a 3D polyline (bottom line of the glass)."""
    P = [Vector(p) for p in pts]
    for a, b in zip(P, P[1:]):
        d = b - a
        L = d.length
        if L < 0.05:
            continue
        hd = Vector((d.x, d.y, 0))
        n = max(1, round(hd.length / panel)) if hd.length > 0.05 else 1
        ux = d / n
        nrm = Vector((-hd.y, hd.x, 0)).normalized() if hd.length > 1e-6 else Vector((1, 0, 0))
        for i in range(n):
            p0 = a + ux * i + ux.normalized() * gap / 2
            p1 = a + ux * (i + 1) - ux.normalized() * gap / 2
            v = [p0 - nrm * 0.006, p1 - nrm * 0.006, p1 + nrm * 0.006, p0 + nrm * 0.006]
            top = [q + Vector((0, 0, h)) for q in v]
            verts = [tuple(q) for q in v + top]
            faces = [(0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]
            uv = [(0, 0), (1, 0), (1, 1), (0, 1)] * 6
            mb.raw(verts, faces, uv, F.glass_clear, False)
        if shoe:
            mb.tube([a + Vector((0, 0, 0.04)), b + Vector((0, 0, 0.04))], 0, F.steel,
                    profile=[(-0.045, -0.02), (0.045, -0.02), (0.045, 0.02), (-0.045, 0.02)], up=(0, 0, 1), smooth=False)
    if rail:
        top = [p + Vector((0, 0, h + 0.012)) for p in P]
        mb.tube(top, 0.021, F.steel, segs=14)


def build_stairs():
    mb = MB("stairs")
    xa0, xa1 = 8.0, 9.2          # up-flight (runs north)
    xb0, xb1 = 9.4, 10.6         # return flight (runs south)
    zl = Z0 + 10 * RISE          # landing level
    tt, nose = 0.045, 0.025
    for i in range(1, 10):       # flight A
        y0 = ST_Y0 + (i - 1) * GOING
        z = Z0 + i * RISE
        mb.bx(xa0, y0 - nose, z - tt, xa1, y0 + GOING, z, F.tread, bevel=0.004)
        mb.bx(xa0 + 0.005, y0, z - RISE, xa1 - 0.005, y0 + 0.018, z - tt, F.riser)
    mb.bx(xa0 + 0.005, ST_YL, zl - RISE, xa1 - 0.005, ST_YL + 0.018, zl - tt, F.riser)
    for j in range(1, 10):       # flight B
        y1 = ST_YL - (j - 1) * GOING
        z = zl + j * RISE
        mb.bx(xb0, y1 - GOING, z - tt, xb1, y1 + nose, z, F.tread, bevel=0.004)
        mb.bx(xb0 + 0.005, y1 - 0.018, z - RISE, xb1 - 0.005, y1, z - tt, F.riser)
    yt = ST_YL - 9 * GOING
    mb.bx(xb0 + 0.005, yt - 0.018, Z1 - RISE, xb1 - 0.005, yt, Z1 - FIN_T, F.riser)
    # landing
    mb.bx(8.0, ST_YL, zl - 0.2, 10.6, 12.25, zl - tt, F.stair_conc)
    mb.bx(8.0, ST_YL - nose, zl - tt, 10.6, 12.25, zl, F.tread, bevel=0.004)
    # waist slabs (side profile extruded across the flight width)
    wa = 0.16
    k = RISE / GOING
    prof_a = [(ST_Y0, Z0), (ST_YL, Z0 + 9 * RISE), (ST_YL, zl - 0.2), (ST_Y0 + 0.3, Z0 - 0.02), (ST_Y0, Z0 - 0.02)]
    prof_a = [(ST_Y0 - 0.0, Z0 - 0.0), (ST_YL, zl - RISE), (ST_YL, zl - RISE - wa / math.cos(math.atan(k))),
              (ST_Y0 + wa / k, Z0 - 0.0)]
    Mx = Matrix(((0, 0, 1, xa0), (1, 0, 0, 0), (0, 1, 0, 0), (0, 0, 0, 1)))     # local (y, z, x)
    mb.prism(prof_a, 0.0, xa1 - xa0, F.stair_conc, m=Mx)
    prof_b = [(ST_YL, zl), (yt, Z1 - RISE), (yt, Z1 - RISE - wa / math.cos(math.atan(k))), (ST_YL, zl - wa / math.cos(math.atan(k)))]
    Mb = Matrix(((0, 0, 1, xb0), (1, 0, 0, 0), (0, 1, 0, 0), (0, 0, 0, 1)))
    mb.prism(prof_b, 0.0, xb1 - xb0, F.stair_conc, m=Mb)
    # stringer trims
    st = F.black
    for x in (xa0 - 0.012,):
        mb.prism([(ST_Y0 - 0.05, Z0), (ST_YL, zl - RISE + 0.02), (ST_YL, zl - RISE - 0.26), (ST_Y0 - 0.05, Z0 - 0.0)], 0, 0.012, st,
                 m=Matrix(((0, 0, 1, x), (1, 0, 0, 0), (0, 1, 0, 0), (0, 0, 0, 1))))
    # balustrades
    g = MB("stair_glass")
    off = 0.1
    glass_rail(g, [(xa0 - 0.03, ST_Y0 - 0.1, Z0 + off), (xa0 - 0.03, ST_YL, zl + off)], h=0.95, shoe=False)       # flight A, corridor side
    glass_rail(g, [(xa0 - 0.03, ST_YL, zl + 0.03), (xa0 - 0.03, 12.2, zl + 0.03)], h=1.0)                       # landing, corridor side
    glass_rail(g, [(xb0 - 0.03, ST_YL, zl + off), (xb0 - 0.03, yt, Z1 + off)], h=0.95, shoe=False)              # flight B, well side
    glass_rail(g, [(xa0 - 0.03, 12.2, Z1 + 0.03), (xa0 - 0.03, ST_Y0 - 0.03, Z1 + 0.03), (xb0 - 0.03, ST_Y0 - 0.03, Z1 + 0.03)], h=1.0)  # first-floor well edge
    # wall handrail for flight B
    hr = [(xb1 - 0.07, ST_YL + 0.2, zl + 0.92), (xb1 - 0.07, yt - 0.25, Z1 + 0.92)]
    g.tube(hr, 0.02, F.steel, segs=14)
    for q in range(4):
        tq = q / 3
        px = Vector(hr[0]).lerp(Vector(hr[1]), 0.08 + 0.84 * tq)
        g.rod(px, px + Vector((0.07, 0, -0.03)), 0.006, F.steel, segs=8)
    return mb.finish(sharp=35, c=shell_coll(0)), g.finish(sharp=35, c=shell_coll(0))


# ---------------------------------------------------------------------------
# facade features
# ---------------------------------------------------------------------------
def elev_matrix(side, pos):
    """Matrix mapping local (s, z, outward) to world for a facade plane.
    side S: s = x, plane y = pos, outward -Y.  N: outward +Y.  W: s = y, plane x = pos, outward -X.  E: outward +X."""
    if side == 'S':
        return Matrix(((1, 0, 0, 0), (0, 0, -1, pos), (0, 1, 0, 0), (0, 0, 0, 1)))
    if side == 'N':
        return Matrix(((1, 0, 0, 0), (0, 0, 1, pos), (0, 1, 0, 0), (0, 0, 0, 1)))
    if side == 'W':
        return Matrix(((0, 0, -1, pos), (1, 0, 0, 0), (0, 1, 0, 0), (0, 0, 0, 1)))
    return Matrix(((0, 0, 1, pos), (1, 0, 0, 0), (0, 1, 0, 0), (0, 0, 0, 1)))


def facade_panel(mb, side, pos, s0, z0, s1, z1, thick, mat, holes=()):
    poly = B(s0, z0, s1, z1)
    for h_ in holes:
        poly = poly.difference(B(*h_))
    mb.prism(poly, 0.0, thick, mat, m=elev_matrix(side, pos))


def build_facade():
    mb = MB("facade_ff")
    gfm = MB("facade_gf")
    dark, white = F.ext_dark, F.ext_white
    # --- master balcony frame box (front-left) ---------------------------------
    x0, x1, yf = -0.05, 6.65, -1.7
    mb.bx(x0, yf, Z0 + H0 - 0.05, x1, 0.0, Z1 - FIN_T, dark)                 # balcony slab
    mb.bx(x0 + 0.3, yf + 0.05, Z1 - FIN_T, x1 - 0.3, 0.0, Z1, F.terrace)     # balcony floor finish
    mb.bx(x0, yf, ZR - 0.05, x1, 0.0, ZRT + 0.05, dark)                      # frame top
    mb.bx(x0, yf, Z1 - FIN_T, x0 + 0.3, 0.0, ZR - 0.05, dark)                # fins
    mb.bx(x1 - 0.3, yf, Z1 - FIN_T, x1, 0.0, ZR - 0.05, dark)
    glass_rail(mb, [(x0 + 0.3, yf + 0.09, Z1), (x1 - 0.3, yf + 0.09, Z1)], h=1.05)
    # --- bedroom 2 balcony (front-right) -----------------------------------------
    bx0, bx1, byf = 11.2, 15.3, -1.15
    mb.bx(bx0, byf, Z0 + H0 + 0.02, bx1, 0.0, Z1 - FIN_T, white)
    mb.bx(bx0 + 0.05, byf + 0.05, Z1 - FIN_T, bx1 - 0.05, 0.0, Z1, F.terrace)
    glass_rail(mb, [(bx0 + 0.07, 0.0, Z1), (bx0 + 0.07, byf + 0.07, Z1), (bx1 - 0.07, byf + 0.07, Z1), (bx1 - 0.07, 0.0, Z1)], h=1.05)
    mb.bx(10.95, -1.25, ZR - 0.42, 16.05, 0.0, ZR - 0.3, dark)                # slim canopy over the balcony doors
    # --- timber batten screen on the centre box -----------------------------------
    zb0, zb1 = Z0 + H0 - 0.12, ZP - 0.05
    lo = get_op('lounge_front')
    wz0, wz1 = Z1 + lo.z0 - 0.06, Z1 + lo.z1 + 0.06
    sp = 0.085
    n = int((10.9 - 6.6) / sp)
    for i in range(n + 1):
        x = 6.6 + 0.02 + i * (10.9 - 6.6 - 0.04) / n
        if lo.a - 0.07 < x < lo.b + 0.07:
            mb.bx(x - 0.02, -0.85, zb0, x + 0.02, -0.8, wz0, F.slat)
            mb.bx(x - 0.02, -0.85, wz1, x + 0.02, -0.8, zb1, F.slat)
        else:
            mb.bx(x - 0.02, -0.85, zb0, x + 0.02, -0.8, zb1, F.slat)
    for xs in (6.6, 10.9):
        m = int(0.8 / sp)
        for i in range(m + 1):
            y = -0.8 + 0.02 + i * (0.8 - 0.04) / m
            xo = xs - 0.05 if xs < 8 else xs
            mb.bx(xo, y - 0.02, zb0, xo + 0.05, y + 0.02, zb1, F.slat)
    # window frame reveal in the screen
    mb.bx(lo.a - 0.09, -0.9, wz0 - 0.03, lo.b + 0.09, -0.8, wz0 + 0.03, dark)
    mb.bx(lo.a - 0.09, -0.9, wz1 - 0.03, lo.b + 0.09, -0.8, wz1 + 0.03, dark)
    mb.bx(lo.a - 0.09, -0.9, wz0, lo.a - 0.03, -0.8, wz1, dark)
    mb.bx(lo.b + 0.03, -0.9, wz0, lo.b + 0.09, -0.8, wz1, dark)
    # soffit over the porch (timber) -- under the centre box
    mb.bx(6.6, -0.8, Z0 + H0 - 0.14, 10.9, 1.6, Z0 + H0 - 0.1, F.slat)
    mb.finish(sharp=35, c=shell_coll(1))
    mb = gfm
    # --- stone cladding: right bay ground floor + porch cheeks ------------------------
    gf = get_op('guest_front')
    facade_panel(mb, 'S', 0.0, 10.75, 0.0, 16.04, Z0 + H0 - 0.02, 0.04, F.stone,
                 holes=[(gf.a - 0.03, Z0 + gf.z0 - 0.04, gf.b + 0.03, Z0 + gf.z1)])
    ge = get_op('guest_east')
    gb = get_op('gbath_east')
    facade_panel(mb, 'E', 16.0, 0.0, 0.0, 6.8, Z0 + H0 - 0.02, 0.04, F.stone,
                 holes=[(ge.a - 0.03, Z0 + ge.z0 - 0.04, ge.b + 0.03, Z0 + ge.z1),
                        (gb.a - 0.03, Z0 + gb.z0 - 0.04, gb.b + 0.03, Z0 + gb.z1)])
    facade_panel(mb, 'W', 10.5, -0.04, 0.0, 1.6, Z0 + H0 - 0.14, 0.04, F.stone)      # porch cheek (east)
    facade_panel(mb, 'E', 7.0, 0.0, 0.0, 1.6, Z0 + H0 - 0.14, 0.04, F.stone)         # porch cheek (west)
    # --- canopy over the dining doors (west) ---------------------------------------------
    mb.bx(-1.5, 7.2, Z0 + 2.85, 0.0, 11.8, Z0 + 2.97, dark)
    return mb.finish(sharp=35, c=shell_coll(0))


def build_shell():
    """Everything structural.  Returns nothing; objects land in the 'ARCH' collection."""
    coll("ARCH")
    define_openings()
    for fl in (0, 1):
        build_walls(fl)
        build_floors_ceilings(fl)
    build_slabs()
    build_openings()
    build_stairs()
    build_facade()
