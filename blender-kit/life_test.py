"""Gait / idle check: python3 life_test.py outdir"""
import sys, os, math
import bpy, kit, life
kit.reset()
c = kit.coll("People")
mb = kit.MB(); mb.box(-20, -20, -0.05, 20, 20, 0, kit.mat_pbr("pv", "concrete_pavers", size=1.6)); mb.build("floor")
fl = lambda x, y: 0.0
P = [life.Performer("daniel", c, [{"until": 99, "walk": [(-4, 0), (4, 0)], "speed": 1.3}], fl),
     life.Performer("olivia", c, [{"until": 99, "stand": (0.4, 2.0), "face": (1.4, 2.4), "talk": 1.0}], fl),
     life.Performer("mark", c, [{"until": 99, "stand": (1.4, 2.4), "face": (0.4, 2.0), "talk": 0.6}], fl),
     life.Performer("guard", c, [{"until": 99, "stand": (-2.0, 2.6), "face": -90, "wave": True}], fl)]
P[1].look_at = lambda t: (1.4, 2.4)
P[2].look_at = lambda t: (0.4, 2.0)
n = int(sys.argv[2]) if len(sys.argv) > 2 else 48
life.animate(P, 1, n, 12.0)
kit.world_hdri("kloofendal_48d_partly_cloudy_puresky", "4k", 1.0, sun_az=235)
kit.render_setup(640, 360, samples=8)
cam = kit.camera("c", (0.0, -7.5, 1.4), (0.0, 1.0, 0.95), lens=35)
kit.render_frames(cam, sys.argv[1], 1, n)
