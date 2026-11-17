"""The five travellers as live, animated figures inside the 4x4.

    actors = crew.seat(truck_obj, collection, time=1.0)                 # one posed moment (stills)
    actors = crew.seat(truck_obj, collection, frames=110, fps=24,       # keyframed performance
                       steer=lambda t: angle, sway=lambda t: (pitch_deg, roll_deg))
The driver's hands are placed on the steering wheel by arm IK and his fingers close round the rim.
"""
import math

from mathutils import Matrix, Vector

import cast
import suv

ROLES = [("driver", "tunde"), ("front", "amina"), ("rear_l", "jack"), ("rear_c", "sophie"), ("rear_r", "emeka")]
WHEEL_C = Vector((0.66, 0.42, suv.ZB - 0.06))
WHEEL_AX = Vector((-1, 0, 0.42)).normalized()          # from the wheel toward the driver
WHEEL_R = 0.185
LEGS = {"upperleg01.L": (-96, 4, 0), "upperleg01.R": (-96, -4, 0), "lowerleg01.L": (52, 0, 0), "lowerleg01.R": (52, 0, 0)}
REST_ARMS = {"upperarm01.L": (2, 40, 0), "upperarm01.R": (2, -40, 0), "lowerarm01.L": (-48, 14, 0), "lowerarm01.R": (-48, -14, 0)}


def _n(t, s):
    """Smooth wandering value in [-1, 1]."""
    return (math.sin(0.83 * t + 1.7 * s) + 0.6 * math.sin(1.9 * t + 2.9 * s + 1.0) + 0.3 * math.sin(3.7 * t + 0.6 * s)) / 1.9


def _ease(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def _fk(role, t, sp, sr):
    """World-axis pose for a role at time t; sp/sr = body pitch/roll (degrees) thrown by the suspension."""
    fk = dict(LEGS)
    fk["spine05"] = (-8 + 0.5 * sp, 0.6 * sr, 0)
    fk["spine03"] = (0.6 * sp + 1.5 * _n(t, 1), 1.2 * sr + 2.0 * _n(t, 2), 0)
    if role == "driver":
        fk.update({"upperleg01.L": (-94, 5, 0), "upperleg01.R": (-90, -5, 0), "lowerleg01.L": (50, 0, 0), "lowerleg01.R": (42, 0, 0)})
        glance = _ease((math.sin(0.9 * t - 1.0) - 0.75) * 4)             # now and then a look across at the passenger
        fk["head"] = (2 * _n(t, 3), 0, -6 * _n(t, 4) - 28 * glance)
        fk["neck01"] = (0, 0, -8 * glance)
    elif role == "front":
        talk = 0.5 + 0.5 * math.sin(0.8 * t + 0.3)                       # turning to the driver and back to the view
        fk.update(REST_ARMS)
        fk["head"] = (3 * _n(t, 5), 0, 34 * talk - 14 * (1 - talk))
        fk["neck01"] = (0, 0, 10 * talk)
        g = 0.5 + 0.5 * math.sin(2.4 * t)                                # a hand moving as she talks
        fk["upperarm01.R"] = (-28 - 10 * g * talk, -44, 0)
        fk["lowerarm01.R"] = (-78 - 14 * g * talk, -6, 8)
    elif role == "rear_l":
        point = _ease((t - 1.2) / 0.9) * (1 - _ease((t - 3.6) / 0.8))    # spots something and points out of the window
        fk.update(REST_ARMS)
        fk["head"] = (-2, 0, 30 + 22 * point + 5 * _n(t, 6))
        fk["neck01"] = (0, 0, 8 + 6 * point)
        fk["spine03"] = (fk["spine03"][0], fk["spine03"][1], 10 * point)
        fk["upperarm01.L"] = (2 - 52 * point, 40 - 62 * point, 0)
        fk["lowerarm01.L"] = (-48 + 40 * point, 14 - 12 * point, 0)
    elif role == "rear_c":
        fk.update(REST_ARMS)
        fk["spine05"] = (6 + 0.5 * sp + 3 * _n(t, 7), 0.6 * sr, 0)       # leaning in between the front seats
        fk["head"] = (4 * _n(t, 8) - 3, 0, 24 * math.sin(0.7 * t + 2.0))
        fk["upperarm01.L"] = (-30, 34, 0)
        fk["lowerarm01.L"] = (-62, 8, 0)
        fk["upperarm01.R"] = (-30, -34, 0)
        fk["lowerarm01.R"] = (-62, -8, 0)
    else:                                                                 # rear right: watching the dunes, hand on the grab handle
        fk.update(REST_ARMS)
        fk["head"] = (-3 + 3 * _n(t, 9), 0, -36 + 10 * _n(t, 10))
        fk["neck01"] = (0, 0, -10)
        fk["spine03"] = (fk["spine03"][0], fk["spine03"][1], -8)
    return fk


def seat(truck, collection, time=1.0, frames=0, fps=24.0, steer=None, sway=None, subdiv=0):
    actors = []
    for seat_name, who in ROLES:
        a = cast.actor(who, collection, subdiv=subdiv if seat_name in ("driver", "front") else 0)
        a.role = seat_name
        x, y = suv.SEATS[seat_name]
        a.arm.parent = truck
        a.arm.rotation_euler = (0, 0, math.pi / 2)
        a.pose(_fk(seat_name, time, 0.0, 0.0))
        a.pos = Vector((x + 0.02, y, suv.FLOOR - a.ground()))
        a.arm.location = a.pos
        actors.append(a)

    def pose_all(t):
        sp, sr = sway(t) if sway else (0.0, 0.0)
        th = (steer(t) if steer else 0.0) * 9.0                          # steering-wheel angle from road-wheel angle
        th = max(-1.0, min(1.0, th))
        for a in actors:
            fk = _fk(a.role, t, sp, sr)
            ik = grip = None
            if a.role == "driver":
                ey = Vector((0, 1, 0))
                ez = WHEEL_AX.cross(ey)
                ik = {}
                for side, s in (("L", 1.0), ("R", -1.0)):
                    ang = th + (0.18 if s > 0 else -0.18)                # hands at about ten-to-two
                    rim = WHEEL_C + WHEEL_R * s * (math.cos(ang) * ey + math.sin(ang) * s * -ez)
                    wrist = rim + WHEEL_AX * 0.075 - Vector((0, 0, 0.02))
                    loc = Matrix.Rotation(-math.pi / 2, 3, "Z") @ (wrist - a.pos)
                    ik[side] = loc
                grip = {"L": 0.85, "R": 0.85}
            a.pose(fk, ik=ik, grip=grip)

    if frames:
        for fr in range(1, frames + 1):
            pose_all((fr - 1) / fps)
            for a in actors:
                a.key(fr)
    else:
        pose_all(time)
    return actors
