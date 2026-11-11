"""Shared specification for the Tourbillon model — the single source of truth.

Every module builds against these numbers.  They were measured from the
dimensioned blueprint (side / plan / front / rear) with tools/extract_blueprint.py
and cross-checked against the published overall dimensions.

COORDINATES (metres)
    +X  forward (nose)        +Y  left (driver side, LHD)        +Z  up
    origin: on the ground plane, on the centreline, at mid-wheelbase.
"""

# ---------------------------------------------------------------- overall
LENGTH = 4.671
WIDTH = 2.051            # body only, mirrors excluded
HEIGHT = 1.189
WHEELBASE = 2.740

X_NOSE = 2.411           # most forward point (splitter lip)
X_TAIL = -2.260          # most rearward point
HALF_WIDTH = 1.030       # max body half width (at both axles)
WAIST_HALF_WIDTH = 0.930 # narrowest half width between the axles (x ~ -0.45)
Z_ROOF = 1.189           # roof peak, at x ~ -0.15
X_ROOF_PEAK = -0.15
GROUND_CLEARANCE = 0.120 # sill underside between the axles

# ---------------------------------------------------------------- wheels
FRONT_AXLE_X = 1.370
REAR_AXLE_X = -1.370

# front 285/35 R20, rear 345/30 R21
FRONT_TYRE_RADIUS = 0.354
FRONT_TYRE_WIDTH = 0.285
FRONT_RIM_RADIUS = 0.254     # 20 in
REAR_TYRE_RADIUS = 0.370
REAR_TYRE_WIDTH = 0.345
REAR_RIM_RADIUS = 0.267      # 21 in

FRONT_WHEEL_Y = 0.845        # wheel centre plane (track 1.69)
REAR_WHEEL_Y = 0.830         # wheel centre plane (track 1.66)

FRONT_ARCH_RADIUS = 0.415
REAR_ARCH_RADIUS = 0.435

WHEELS = {
    "FL": dict(x=FRONT_AXLE_X, y=+FRONT_WHEEL_Y, z=FRONT_TYRE_RADIUS, front=True, side=+1),
    "FR": dict(x=FRONT_AXLE_X, y=-FRONT_WHEEL_Y, z=FRONT_TYRE_RADIUS, front=True, side=-1),
    "RL": dict(x=REAR_AXLE_X, y=+REAR_WHEEL_Y, z=REAR_TYRE_RADIUS, front=False, side=+1),
    "RR": dict(x=REAR_AXLE_X, y=-REAR_WHEEL_Y, z=REAR_TYRE_RADIUS, front=False, side=-1),
}

# ---------------------------------------------------------------- body landmarks
# (x, z) pairs on the side view unless noted
WINDSHIELD_BASE_X = 1.32      # centreline, z ~ 0.86
WINDSHIELD_BASE_Z = 0.86
WINDSHIELD_TOP_X = 0.60       # header, z ~ 1.15
WINDSHIELD_TOP_Z = 1.15
BELTLINE_Z = 0.84             # side-glass sill
ROOF_HALF_WIDTH = 0.55        # roof at the header
SHOULDER_Z = 0.86             # top of the fenders / body shoulder

HEADLIGHT = dict(x0=1.80, x1=2.08, y_in=0.50, y_out=0.93, z0=0.585, z1=0.655)
HORSESHOE = dict(half_w=0.285, z0=0.215, z1=0.565, x_face=2.36)
TAIL_BAR = dict(half_w=0.92, z0=0.70, z1=0.82, x=-2.20)
REAR_WING = dict(x0=-2.22, x1=-1.87, half_span=0.68, z=0.88)
MIRROR = dict(x=0.70, y=1.04, z=0.87)

# C-line ("Bugatti line") in side view: rearmost point and the lower branch
CLINE = dict(rear_x=-0.73, rear_z=0.93, top_z=1.10, low_z_mid=0.46, low_z_front=0.40)
# door shut lines (side view): rear cut runs from the roof down/forward to the sill
DOOR = dict(rear_top=(-0.50, 1.10), rear_bottom=(0.06, 0.20), front_x=1.02,
            hinge=(0.98, 0.62, 0.95), hinge_axis=(0.35, 0.28, 0.90), open_angle_deg=68.0)

# ---------------------------------------------------------------- cabin envelope
# Interior parts must stay inside this volume; the body is built around it.
CABIN = dict(
    x_firewall=-0.56,        # rear bulkhead behind the seats
    x_dash_rear=0.66,        # dashboard face towards occupants (top roll)
    x_cowl=1.28,             # windshield base inside
    x_pedals=1.12,
    floor_z=0.160,           # top of the cabin floor
    roof_z=1.130,            # inside of the roof at its peak
    dash_top_z=0.84,
    half_width_floor=0.60,   # inner sill face at floor level
    half_width_shoulder=0.72,# inner door face at shoulder height (z ~ 0.6)
    half_width_roof=0.50,
    tunnel_half_width=0.115, # centre spine
    seat_y=0.375,            # seat centreline (driver = +Y, passenger = -Y)
    hpoint_x=-0.02,          # seating reference point
    hpoint_z=0.300,
    backrest_angle_deg=27.0, # from vertical
    steering_centre=(0.50, 0.375, 0.715),
    steering_rim_radius=0.180,
    steering_rake_deg=22.0,  # column tilt from horizontal
)

# ---------------------------------------------------------------- naming
ROOT = "TB_ROOT"             # empty that parents the whole car
CTRL = "TB_CTRL"             # control object carrying the custom properties
COLLECTIONS = dict(
    body="TB_Body", glass="TB_Glass", doors="TB_Doors", wheels="TB_Wheels",
    interior="TB_Interior", lights="TB_Lights", aero="TB_Aero",
    powertrain="TB_Powertrain", rig="TB_Rig", env="ENV_Showroom",
)

# launch-spec inspired two-tone
COLOURS = dict(
    paint_light=(0.36, 0.56, 0.66),   # pale glacier blue
    paint_dark=(0.012, 0.024, 0.050), # deep navy / blue carbon
    leather_light=(0.30, 0.46, 0.56),
    leather_dark=(0.035, 0.050, 0.070),
    accent_red=(0.60, 0.02, 0.02),
)

# ---------------------------------------------------------------- film
FPS = 24
BPM = 120                    # 1 beat = 12 frames, 1 bar = 48 frames (2 s)
