# A gallop for the horse rig, solved in the side plane (y forward, z up, metres).
# Stance hooves stay planted on the ground (they move backward in the horse's frame at the
# running speed); in swing, the fetlock follows a path while the knee or hock folds.
import numpy as np

S, MID_X = 14.2, 0.015
def P(x, y, z): return np.array([(x - MID_X) * S, y * S, (z + 0.0765) * S])

REST = {  # rest joints (x, y, z), metres
    'nf': [P(0.028, 0.020, 0.030), P(0.030, 0.040, 0.000), P(0.026, 0.0225, -0.021), P(0.0277, 0.0179, -0.0405), P(0.0302, 0.0122, -0.0605), P(0.0307, 0.0147, -0.0690), P(0.0300, 0.0220, -0.0765)],
    'ff': [P(0.002, 0.020, 0.030), P(0.000, 0.040, 0.000), P(-0.0006, 0.0290, -0.0225), P(-0.0019, 0.0293, -0.0405), P(-0.0021, 0.0330, -0.0605), P(-0.0029, 0.0378, -0.0690), P(-0.0036, 0.0460, -0.0765)],
    'nh': [None, P(0.030, -0.058, 0.012), P(0.033, -0.047, -0.010), P(0.0325, -0.0625, -0.035), P(0.0333, -0.0680, -0.0595), P(0.0330, -0.0655, -0.0690), P(0.0330, -0.0565, -0.0765)],
    'fh': [None, P(0.000, -0.058, 0.012), P(-0.002, -0.060, -0.010), P(-0.0021, -0.0800, -0.035), P(-0.0023, -0.0864, -0.0590), P(-0.0030, -0.0845, -0.0690), P(-0.0035, -0.0775, -0.0765)],
}
ROOT = P(0.015, -0.005, 0.012)

STRIDE = 0.40          # seconds per stride (2.5 strides a second)
SPEED = 9.5            # m/s
# footfalls of a right-lead gallop: far hind, near hind, far fore, near fore, then a flight
LEGS = {  # touchdown phase, stance length (phase units), land / lift offsets (m) from the proximal joint
    'fh': dict(on=0.00, dur=0.23, land=+0.55, fore=False),
    'nh': dict(on=0.09, dur=0.23, land=+0.58, fore=False),
    'ff': dict(on=0.33, dur=0.22, land=+0.46, fore=True),
    'nf': dict(on=0.43, dur=0.22, land=+0.50, fore=True),
}

def yz(v): return np.array([v[1], v[2]])
def ang(v): return np.arctan2(v[1], v[0])          # angle of a (y, z) vector
def rot(v, a): c, s = np.cos(a), np.sin(a); return np.array([c * v[0] - s * v[1], s * v[0] + c * v[1]])
def smooth(t): t = np.clip(t, 0, 1); return t * t * (3 - 2 * t)

def lengths(leg):
    J = [yz(p) if p is not None else None for p in REST[leg]]
    return [np.linalg.norm(J[i + 1] - J[i]) for i in range(1, 6)], J

def body(phi):
    """Body height offset (m) and pitch (rad, + = nose up) over the stride."""
    bob = 0.055 * np.cos(2 * np.pi * (phi - 0.85))          # highest in the flight
    pitch = np.radians(4.5) * np.sin(2 * np.pi * (phi - 0.02)) # front up while the hinds push, down as the fores land
    return bob, pitch

def body_xform(p, phi):
    bob, pitch = body(phi)
    r = yz(ROOT)
    return r + rot(p - r, pitch) + np.array([0, bob])

def two_bone(a, L1, L2, target, bend_sign):
    """Knee of a two-bone chain from a to target; bend_sign picks the side the joint points to."""
    d = target - a; dist = np.linalg.norm(d)
    dist_c = np.clip(dist, abs(L1 - L2) + 1e-4, L1 + L2 - 1e-4)
    cosA = (L1 * L1 + dist_c * dist_c - L2 * L2) / (2 * L1 * dist_c)
    A = np.arccos(np.clip(cosA, -1, 1))
    base = ang(d)
    k = a + L1 * np.array([np.cos(base + bend_sign * A), np.sin(base + bend_sign * A)])
    end = a + d / dist * dist_c
    return k, end

def cubic(p0, p1, p2, p3, t):
    return (1 - t) ** 3 * p0 + 3 * (1 - t) ** 2 * t * p1 + 3 * (1 - t) * t * t * p2 + t ** 3 * p3

def solve_chain(prox, L, mid, fet, fore):
    """elbow/stifle, knee/hock and fetlock for a proximal joint, a middle-joint angle and a fetlock target."""
    v_mid = np.array([L[1], 0.0])
    v_can = np.array([np.cos(mid), np.sin(mid)]) * L[2]
    virt = v_mid + v_can
    elbow, fet_r = two_bone(prox, L[0], np.linalg.norm(virt), fet, -1 if fore else 1)
    knee = elbow + rot(v_mid, ang(fet_r - elbow) - ang(virt))
    return elbow, knee, fet_r

def stance(leg, s, phi):
    L, J = lengths(leg); g = LEGS[leg]; fore = g['fore']
    prox = body_xform(J[1], phi)
    hoof_rest = J[6] - J[5]; past_rest = J[5] - J[4]
    mid_rest = ang(J[4] - J[3]) - ang(J[3] - J[2])
    land_y = J[1][0] + g['land']; lift_y = land_y - SPEED * STRIDE * g['dur']
    toe = np.array([land_y + (lift_y - land_y) * s, 0.0])
    load = np.sin(np.pi * s); heel = smooth((s - 0.7) / 0.3)
    hoof_v = rot(hoof_rest, np.radians(-25) * heel)
    past_v = rot(past_rest, np.radians(22) * load - np.radians(18) * heel)
    cor = toe - hoof_v; fet = cor - past_v
    mid = mid_rest + (np.radians(4) * heel if fore else np.radians(-8) * load)
    elbow, knee, fet = solve_chain(prox, L, mid, fet, fore)
    cor = fet + past_v; toe = cor + hoof_v
    can = fet - knee
    return [prox, elbow, knee, fet, cor, toe], dict(
        fet_rel=fet - J[1], mid=mid, pf=ang(past_v) - ang(can), hf=ang(hoof_v) - ang(past_v))

def catmull(keys, q):
    """Catmull-Rom through equally spaced keys (q in 0..1)."""
    n = len(keys) - 1
    x = np.clip(q, 0, 1) * n; i = min(int(x), n - 1); t = x - i
    p0 = keys[max(i - 1, 0)]; p1 = keys[i]; p2 = keys[i + 1]; p3 = keys[min(i + 2, n)]
    if i == 0: p0 = 2 * p1 - p2
    if i + 2 > n: p3 = 2 * p2 - p1
    return 0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3)

# Swing, as segment angles from straight down (degrees, + = the lower end swings forward) for
# the five bones (humerus/femur, forearm/tibia, cannon, pastern, hoof) at q = 0.25, 0.5, 0.75.
# Lift-off and touchdown come from the stance solution, so the legs leave and meet the ground cleanly.
SWING = {
    True:  [(-45, -5, -95, -140, -165), (-25, 35, -65, -115, -140), (-8, 68, 25, 5, 25)],     # fore: fold, carry, reach
    False: [(-10, -45, -55, -100, -130), (20, -30, -5, -45, -70), (40, -10, 20, 5, 30)],      # hind: lift behind, swing under, reach
}

def seg_angles(j):
    return np.array([np.arctan2(j[i + 1][0] - j[i][0], -(j[i + 1][1] - j[i][1])) for i in range(5)])

def fk(prox, angles, L):
    pts = [prox]
    for a, l in zip(angles, L):
        pts.append(pts[-1] + l * np.array([np.sin(a), -np.cos(a)]))
    return pts

def leg_pose(leg, phi):
    L, J = lengths(leg); g = LEGS[leg]; fore = g['fore']
    p = (phi - g['on']) % 1.0; span = g['dur']
    if p < span:
        joints, _ = stance(leg, p / span, phi)
        return joints
    q = (p - span) / (1 - span)
    a0 = seg_angles(stance(leg, 1.0, (g['on'] + span) % 1.0)[0])
    a1 = seg_angles(stance(leg, 0.0, g['on'] % 1.0)[0])
    keys = [a0] + [np.radians(k) for k in SWING[fore]] + [a1]
    keys = [np.array(k, float) for k in keys]
    for i in range(1, len(keys)):                       # unwrap, so no joint spins the long way round
        keys[i] = keys[i - 1] + (keys[i] - keys[i - 1] + np.pi) % (2 * np.pi) - np.pi
    angles = catmull(keys, q)
    return fk(body_xform(J[1], phi), angles, L)

def pose(phi):
    return {leg: leg_pose(leg, phi) for leg in LEGS}

if __name__ == '__main__':
    from PIL import Image, ImageDraw
    N = 10
    W, H = 360, 300
    img = Image.new('RGB', (W * 5, H * 2), (250, 248, 240)); d = ImageDraw.Draw(img)
    for k in range(N):
        phi = k / N
        ox, oy = (k % 5) * W, (k // 5) * H
        tr = lambda p: (ox + W / 2 + (p[0] - 0.0) * 110, oy + H - 20 - p[1] * 110)
        d.line([tr((-3, 0)), tr((3, 0))], fill=(120, 160, 80), width=2)
        # body outline hint: root, hips, shoulders
        pp = pose(phi)
        for leg, col in [('ff', (170, 120, 90)), ('fh', (170, 120, 90)), ('nh', (60, 30, 10)), ('nf', (60, 30, 10))]:
            pts = [tr(p) for p in pp[leg]]
            d.line(pts, fill=col, width=4)
            for q in pts: d.ellipse([q[0] - 3, q[1] - 3, q[0] + 3, q[1] + 3], fill=col)
        hip = pp['nh'][0]; sh = pp['nf'][0]
        d.line([tr(hip), tr(sh)], fill=(60, 30, 10), width=6)
        d.text((ox + 5, oy + 5), f'phi={phi:.1f}', fill=(0, 0, 0))
    img.save('gait_preview.png')
    print('ok')
