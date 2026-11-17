"""
create_s2e5.py ― 『君は写真に写らない』第5話「一緒に来て」の3Dカット（夜の旧校舎、踊り場から上を見上げる）
  python create_s2e5.py --shot U1|U2|V [--samples 64] [--test]
  U1: 上の階へ続く階段のいちばん上に湊が立っている … 1枚
  U2: 同じ構図。湊が手を差し出す … 1枚
  V : 同じ構図。スマホのカメラ越し（湊は写らない）… 1枚
"""
import os, sys, math, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
from mathutils import Vector
import s2_world as W

arg = lambda k, d: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
SHOT = arg("--shot", "U1"); SAMPLES = int(arg("--samples", "64")); TEST = "--test" in sys.argv
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frames_S2E5", SHOT if not TEST else "test_" + SHOT)
os.makedirs(OUT, exist_ok=True)

sc = W.reset(SAMPLES)
st = W.stairwell(haze=0.018, sun_str=1.6, sun_elev=22.0, night=True)
W.box("upper_floor", (-0.85, -0.45, 3.6 - 0.1), (1.7, 1.55, 0.2), st["M"]["step"])       # 上の階の床
TOP = (-0.85, -0.05, 3.6)
mi = W.person("minato", TOP, 1.74, rot=0, reach=(SHOT == "U2"), shirt=(0.86, 0.87, 0.86), bottom=(0.05, 0.06, 0.1), hair=(0.025, 0.02, 0.018))
if SHOT == "V":
    for p in [mi] + list(mi.children_recursive):
        p.hide_render = True
cam = W.camera((-0.55, 4.55, 3.15), (-0.85, 0.3, 4.3), lens=30, fstop=2.0)
torch = W.flashlight(cam, energy=45.0, spread=26.0); torch.rotation_euler = (math.radians(-14), math.radians(3), 0)   # 光は足元の段へ
focus = (TOP[0] - 0.19, TOP[1] + 0.53, TOP[2] + 1.31) if SHOT == "U2" else (TOP[0], TOP[1], TOP[2] + 1.0)
cam.data.dof.focus_distance = (Vector(cam.location) - Vector(focus)).length
sc.render.filepath = os.path.join(OUT, "0001.png")
t = time.time(); bpy.ops.render.render(write_still=True); print("frame 1 %.1fs" % (time.time() - t), flush=True)
