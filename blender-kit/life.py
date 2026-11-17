"""Life for the people in a scene: walking, standing and talking, waving, sitting on a ledge.

A Performer follows a script of actions over time; animate() poses every performer for every
frame, plants their feet on the ground and keyframes the result.

Gait values follow standard walk-cycle practice: thigh swing about +-20 deg at 1.3 m/s, knee
flexion peaking near 60 deg in mid-swing, arms swinging opposite the legs with the elbow bending
on the forward swing, pelvis and ribcage counter-rotating 4-6 deg, and a steady head. Standing
figures are never still: slow weight shifts, breathing, small head movements and gestures.
"""
import math

import bpy
from mathutils import Vector

import cast


def _ease(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def _wob(t, s, rate=1.0):
    return (math.sin(0.71 * rate * t + 1.3 * s) + 0.6 * math.sin(1.63 * rate * t + 2.1 * s + 0.7)
            + 0.35 * math.sin(2.9 * rate * t + 0.4 * s + 1.9)) / 1.95


from mathutils import Matrix


def arm(side, down=42.0, swing=0.0, out=0.0):
    """Upper-arm rotation: lower the arm from the rest pose by `down` degrees, then swing it forward
    (+) or back (-) about the shoulder, and `out` away from the body. Order matters: lower first."""
    sg = 1 if side == "L" else -1
    return (Matrix.Rotation(math.radians(-swing), 3, "X") @ Matrix.Rotation(math.radians(sg * out), 3, "Y")
            @ Matrix.Rotation(math.radians(sg * down), 3, "Y"))


def walk_fk(phase, speed=1.3, style=0.0):
    """Pose for a point in the gait cycle (phase 0..1 per stride = two steps). style>0 = more hip sway."""
    th = 9.0 + 9.0 * min(speed, 1.8)                  # thigh swing amplitude, degrees
    out = {}
    for side, off in (("L", 0.0), ("R", 0.5)):
        ph = (phase + off) % 1.0
        hip = -th * math.cos(2 * math.pi * ph)                    # - = forward
        sw = math.sin(2 * math.pi * (ph - 0.5)) if ph > 0.5 else 0.0
        knee = 6 + 52 * (max(0.0, sw) ** 1.3) * min(1.0, speed / 1.2) + 6 * max(0.0, math.sin(2 * math.pi * ph * 2)) * (ph < 0.25)
        foot = -10 * max(0.0, math.cos(2 * math.pi * ph)) + 16 * max(0.0, math.sin(2 * math.pi * (ph - 0.35))) * (0.35 < ph < 0.65)
        out[f"upperleg01.{side}"] = (hip, 0, 0)
        out[f"lowerleg01.{side}"] = (knee, 0, 0)
        out[f"foot.{side}"] = (foot, 0, 0)
        arm = 15 * math.cos(2 * math.pi * ph) * min(1.0, speed / 1.2)   # opposite the same-side leg
        sgn = 1 if side == "L" else -1
        out[f"upperarm01.{side}"] = globals()["arm"](side, 46, -arm, 2)
        out[f"lowerarm01.{side}"] = (40 - 22 * max(0.0, -math.cos(2 * math.pi * ph)), sgn * 4, 0)   # elbow bends on the forward swing
    out["root"] = (0, (1.5 + 2.5 * style) * math.sin(2 * math.pi * phase), 5 * math.cos(2 * math.pi * phase))
    out["spine03"] = (2, 0, -6 * math.cos(2 * math.pi * phase))
    out["head"] = (1.5 * math.sin(4 * math.pi * phase), 0, 1.5 * math.cos(2 * math.pi * phase))
    return out


def idle_fk(t, seed, talk=0.0, gesture_side="R", look=0.0, nod=1.0):
    """Standing: weight shift, breathing, small head motion; talk>0 adds hand gestures and nods.
    look = head yaw (degrees, + = to the figure's left)."""
    w = _wob(t, seed, 0.35)                       # slow weight shift between the feet
    br = math.sin(2 * math.pi * 0.25 * t + seed)  # breathing, about 15 breaths a minute
    out = {
        "root": (0, 2.2 * w, 1.5 * _wob(t, seed + 3, 0.2)),
        "upperleg01.L": (-2 + 2 * w, -1.5 - 2.5 * max(0, -w), 0),
        "upperleg01.R": (-2 - 2 * w, 1.5 + 2.5 * max(0, w), 0),
        "lowerleg01.L": (4 + 5 * max(0, -w), 0, 0),
        "lowerleg01.R": (4 + 5 * max(0, w), 0, 0),
        "spine03": (1.2 * br, -1.5 * w, 2 * _wob(t, seed + 5, 0.3)),
        "upperarm01.L": arm("L", 45, 2 * _wob(t, seed + 7, 0.4), 1),
        "upperarm01.R": arm("R", 45, 2 * _wob(t, seed + 8, 0.4), 1),
        "lowerarm01.L": (40 - 5 * _wob(t, seed + 9, 0.5), 5, 0),
        "lowerarm01.R": (40 - 5 * _wob(t, seed + 10, 0.5), -5, 0),
    }
    hy = look + 6 * _wob(t, seed + 11, 0.5)
    hp = 2 * _wob(t, seed + 12, 0.6)
    if talk > 0:
        # a gesture every few seconds: forearm comes up, the hand turns out, then settles
        g = max(0.0, math.sin(2 * math.pi * (t / 3.7) + seed)) ** 2 * talk
        g2 = max(0.0, math.sin(2 * math.pi * (t / 5.3) + seed * 1.7)) ** 2 * talk * 0.7
        s1, s2 = gesture_side, "L" if gesture_side == "R" else "R"
        sg1 = 1 if s1 == "L" else -1
        sg2 = -sg1
        out[f"upperarm01.{s1}"] = arm(s1, 45 - 10 * g, 22 * g, 6 * g)
        out[f"lowerarm01.{s1}"] = (40 - 75 * g, sg1 * (5 - 20 * g), sg1 * 25 * g)
        out[f"upperarm01.{s2}"] = arm(s2, 45 - 6 * g2, 14 * g2, 3 * g2)
        out[f"lowerarm01.{s2}"] = (40 - 55 * g2, sg2 * 5, 0)
        hp += nod * 4 * max(0.0, math.sin(2 * math.pi * 1.3 * t + seed)) * talk
    out["head"] = (hp, 0, hy)
    out["neck01"] = (0, 0, hy * 0.3)
    return out


def wave_fk(t, seed=0.0):
    out = idle_fk(t, seed)
    k = 0.5 + 0.5 * math.sin(2 * math.pi * 2.2 * t)
    out["upperarm01.R"] = (-35, 62, 0)
    out["lowerarm01.R"] = (-20, -40 + 30 * k, 0)
    return out


def sit_ledge_fk(t, seed):
    """Sitting on a ledge (the pool edge) with the lower legs hanging and swinging in the water."""
    a = 10 * math.sin(2 * math.pi * 0.45 * t + seed)
    return {
        "upperleg01.L": (-86, 3, 0), "upperleg01.R": (-86, -3, 0),
        "lowerleg01.L": (82 + a, 0, 0), "lowerleg01.R": (82 - a, 0, 0),
        "upperarm01.L": arm("L", 40, -14, 4), "upperarm01.R": arm("R", 40, -14, 4),
        "lowerarm01.L": (30, 6, 0), "lowerarm01.R": (30, -6, 0),
        "spine05": (-4, 0, 0), "spine03": (1.2 * math.sin(1.6 * t + seed), 0, 2 * _wob(t, seed, 0.3)),
        "head": (3 * _wob(t, seed + 1, 0.5), 0, 15 * _wob(t, seed + 2, 0.3)),
    }


class Performer:
    """One person and a script. actions = list of dicts, each with "until" (seconds) and one of:
         {"walk": [(x, y), ...], "speed": 1.3}       walk the polyline, then stand at its end
         {"stand": (x, y), "face": deg | (x, y), "talk": 0..1}
         {"wave": True}  (at the last position)    {"sit": (x, y), "face": deg}
    floor(x, y) gives the ground height."""

    def __init__(self, name, collection, actions, floor, seed=None, subdiv=0, style=0.0, look_at=None):
        self.a = cast.actor(name, collection, subdiv=subdiv)
        self.actions = actions
        self.floor = floor
        self.seed = (sum(map(ord, name)) % 97) / 9.7 if seed is None else seed
        self.style = style
        self.look_at = look_at              # callable t -> (x, y) the head turns toward, or None
        self._pos = Vector((0, 0))
        self._yaw = 0.0
        self._phase = 0.0
        self._dist = 0.0

    def _state(self, t):
        t0 = 0.0
        for act in self.actions:
            if t <= act["until"] or act is self.actions[-1]:
                return act, t - t0
            t0 = act["until"]

    def frame(self, t, dt):
        act, lt = self._state(t)
        mode = "stand"
        if "walk" in act:
            pts = [Vector(p) for p in act["walk"]]
            sp = act.get("speed", 1.3)
            d = sp * lt
            seg_len = [(pts[i + 1] - pts[i]).length for i in range(len(pts) - 1)]
            total = sum(seg_len)
            if d < total:
                mode = "walk"
                acc = 0.0
                for i, L in enumerate(seg_len):
                    if acc + L >= d:
                        f = (d - acc) / max(L, 1e-6)
                        p = pts[i].lerp(pts[i + 1], f)
                        dirv = pts[i + 1] - pts[i]
                        break
                    acc += L
                target_yaw = math.atan2(dirv.y, dirv.x)
                self._pos = p
                dy = (target_yaw - self._yaw + math.pi) % (2 * math.pi) - math.pi
                self._yaw += dy * min(1.0, dt * 6.0)          # turn smoothly at corners
                self._phase = (self._phase + sp * dt / (0.62 + 0.42 * min(sp, 1.6))) % 1.0
                fk = walk_fk(self._phase, sp, self.style)
            else:
                self._pos = pts[-1]
                fk = idle_fk(t, self.seed, act.get("talk", 0.0))
        elif "sit" in act:
            self._pos = Vector(act["sit"])
            self._yaw = math.radians(act.get("face", 0.0))
            mode = "sit"
            fk = sit_ledge_fk(t, self.seed)
        else:
            if "stand" in act:
                self._pos = Vector(act["stand"])
            face = act.get("face")
            if face is not None:
                ty = math.atan2(face[1] - self._pos.y, face[0] - self._pos.x) if isinstance(face, tuple) else math.radians(face)
                dy = (ty - self._yaw + math.pi) % (2 * math.pi) - math.pi
                self._yaw += dy * min(1.0, dt * 3.0)
            fk = wave_fk(t, self.seed) if act.get("wave") else idle_fk(t, self.seed, act.get("talk", 0.0),
                                                                          act.get("hand", "R"))
        # head turns toward a point of interest (a passing car, the person being spoken to)
        if self.look_at is not None:
            tgt = self.look_at(t)
            if tgt is not None:
                want = math.degrees(math.atan2(tgt[1] - self._pos.y, tgt[0] - self._pos.x) - self._yaw)
                want = (want + 180) % 360 - 180
                want = max(-65.0, min(65.0, want)) * (0.45 if mode == "walk" else 1.0)
                h = fk.get("head", (0, 0, 0))
                fk["head"] = (h[0], h[1], 0.7 * want)
                fk["neck01"] = (0, 0, 0.3 * want)
                fk["spine03"] = (fk.get("spine03", (0, 0, 0))[0], 0, 0.15 * want)
        self.mode = mode
        return fk

    def place(self, frame):
        a = self.a
        z = self.floor(self._pos.x, self._pos.y)
        if self.mode == "sit":
            hip = a.fk_point("upperleg01.L", a.ad.bones["upperleg01.L"].head_local).z
            a.arm.location = (self._pos.x, self._pos.y, z - hip + 0.12)
        else:
            a.arm.location = (self._pos.x, self._pos.y, z - a.ground_fast())
        a.arm.rotation_euler = (0, 0, self._yaw + math.pi / 2)        # figures face -Y in their own frame
        a.arm.keyframe_insert("location", frame=frame)
        a.arm.keyframe_insert("rotation_euler", frame=frame)
        a.key(frame)
        if not hasattr(self, "track"):
            self.track = {}
        self.track[frame] = (self._pos.x, self._pos.y)


def animate(performers, f0, f1, fps):
    dt = 1.0 / fps
    for fr in range(f0, f1 + 1):
        t = (fr - 1) * dt
        for p in performers:
            fk = p.frame(t, dt)
            p.a.pose(fk, update=False)
            p.place(fr)


def still(performers, t):
    """Pose everyone at one moment (for stills): run the clock up to t so walkers are mid-stride."""
    dt = 1.0 / 12.0
    tt = 0.0
    while tt < t:
        for p in performers:
            p.frame(tt, dt)
        tt += dt
    for p in performers:
        p.a.pose(p.frame(t, dt), update=False)
        p.place(1)
