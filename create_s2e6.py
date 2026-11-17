"""
create_s2e6.py ― 『君は写真に写らない』第6話「ありがとう」の3Dカット（夜明けの踊り場）
  python create_s2e6.py --shot R1|R2 [--samples 64]
  R1: 朝日の差す踊り場。窓辺の湊と、向かい合う凛（逆光のシルエット）… 1枚
  R2: 同じ構図。湊だけがいない … 1枚
"""
import os, sys, math, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
from mathutils import Vector
import s2_world as W

arg = lambda k, d: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
SHOT = arg("--shot", "R1"); SAMPLES = int(arg("--samples", "64")); TEST = "--test" in sys.argv
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frames_S2E6", SHOT if not TEST else "test_" + SHOT)
os.makedirs(OUT, exist_ok=True)

if os.path.exists(os.path.join(OUT, "0001.png")) and not TEST: sys.exit(0)
sc = W.reset(SAMPLES)
st = W.stairwell(haze=0.014, sun_str=22.0, sun_elev=7.0)
bpy.data.lights["sun"].color = (1.0, 0.72, 0.5)                        # 夜明けの色
mi = W.person("minato", (1.0, 4.55, 1.8), 1.74, rot=90, shirt=(0.86, 0.87, 0.86), bottom=(0.05, 0.06, 0.1), hair=(0.025, 0.02, 0.018))
W.person("rin", (0.05, 4.2, 1.8), 1.6, female=True, rot=-80, shirt=(0.9, 0.9, 0.9), bottom=(0.1, 0.12, 0.22), hair=(0.04, 0.03, 0.025), skirt_r=0.21)
if SHOT == "R2":
    for p in [mi] + list(mi.children_recursive):
        p.hide_render = True
cam = W.camera((0.95, -0.3, 1.6), (0.55, 4.6, 2.75), lens=30, fstop=2.8)
cam.data.dof.focus_distance = (Vector(cam.location) - Vector((0.5, 4.4, 2.6))).length
sc.render.filepath = os.path.join(OUT, "0001.png")
t = time.time(); bpy.ops.render.render(write_still=True); print("frame 1 %.1fs" % (time.time() - t), flush=True)
