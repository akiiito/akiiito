"""
create_s2e3.py ― 『君は写真に写らない』第3話「一年前の今日」の3Dカット（旧校舎の階段、夕方）
  python create_s2e3.py --shot S|E [--samples 48] [--test]
  S: 階段の下から踊り場を見上げ、ゆっくり上る。窓の前に湊のシルエット … 48コマ
  E: 同じ場所、誰もいない階段（ニュース記事の写真に使う）… 1枚
"""
import os, sys, math, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
from mathutils import Vector
import s2_world as W

arg = lambda k, d: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
SHOT = arg("--shot", "S"); SAMPLES = int(arg("--samples", "48")); TEST = "--test" in sys.argv
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frames_S2E3", SHOT if not TEST else "test_" + SHOT)
os.makedirs(OUT, exist_ok=True)

sc = W.reset(SAMPLES)
st = W.stairwell(haze=0.012, sun_str=30.0, sun_elev=16.0)
mi = W.person("minato", (0.75, 4.45, 1.8), 1.74, rot=12, shirt=(0.86, 0.87, 0.86), bottom=(0.05, 0.06, 0.1), hair=(0.025, 0.02, 0.018))
LOOK = (0.6, 4.6, 2.95)
C0, C1 = (1.05, -1.6, 1.45), (0.95, -0.3, 1.6)
cam = W.camera(C0, LOOK, lens=26, fstop=2.8)

def lerp(a, b, u): return tuple(x + (y - x) * u for x, y in zip(a, b))
frames = [1]
if SHOT == "S":
    n = 48; frames = list(range(1, n + 1))
    for f in frames:
        u = (f - 1) / (n - 1); u = u * u * (3 - 2 * u)
        p = lerp(C0, C1, u); cam.location = (p[0], p[1], p[2] + 0.03 * math.sin(f / n * 6 * math.pi))   # 一段ずつ上る上下動
        W.aim(cam, LOOK)
        cam.keyframe_insert("location", frame=f); cam.keyframe_insert("rotation_euler", frame=f)
elif SHOT == "E":
    for p in [mi] + list(mi.children_recursive):
        p.hide_render = True
    cam.location = C1; W.aim(cam, LOOK)
if TEST:
    frames = [int(arg("--frame", "48"))] if SHOT == "S" else [1]
t = time.time()
for f in frames:
    p = os.path.join(OUT, "%04d.png" % f)
    if os.path.exists(p) and not TEST: continue
    sc.frame_set(f)
    cam.data.dof.focus_distance = (Vector(cam.location) - Vector((0.75, 4.35, 2.9))).length
    sc.render.filepath = p
    bpy.ops.render.render(write_still=True)
    print("frame %d %.1fs" % (f, time.time() - t), flush=True); t = time.time()
