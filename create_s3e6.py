"""
create_s3e6.py ― 『恋は心理学で落とせる？』第6話「返報性の原理」の絵（放課後の教室・窓辺の二人とプレゼント）
  python create_s3e6.py --shot GV1|GV2 [--samples 16] [--test]
  GV1: めいが小さなクッキーの箱をさし出す
  GV2: 次の日、陽太が大きすぎる“お返し”の箱を持ってくる
出力: frames_S3E6/<shot>_<mei>_<yota>.png
"""
import os, sys, math, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
import s2_world as W, s3_toon as T

arg = lambda k, d: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
SHOT = arg("--shot", "GV1"); SAMPLES = int(arg("--samples", "16")); TEST = "--test" in sys.argv
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frames_S3E6"); os.makedirs(OUT, exist_ok=True)

def gift(name, root, c, size, wrap, ribbon):
    """リボンをかけたプレゼントの箱（持つ人の子にして一緒に回す）"""
    mw = T.toon(name + "_wrap", wrap, tuple(x * 0.7 for x in wrap)); mr = T.toon(name + "_rib", ribbon, tuple(x * 0.7 for x in ribbon))
    parts = [W.box(name, c, size, mw, bevel=0.006),
             W.box(name + "_r1", c, (size[0] * 0.18, size[1] + 0.006, size[2] + 0.006), mr),
             W.box(name + "_r2", c, (size[0] + 0.006, size[1] * 0.18, size[2] + 0.006), mr)]
    for k in (-1, 1):                                                     # 上の蝶結び
        T.sph(name + "_bow", (c[0] + k * size[0] * 0.09, c[1], c[2] + size[2] / 2 + size[2] * 0.12), size[0] * 0.09, (1.0, 0.6, 0.7), mr, root, 12)
    for o in parts:
        o.parent = root; T.link(o)

sc = W.reset(SAMPLES); sc.view_settings.view_transform = "Standard"
W.classroom(**W.MORNING)
if SHOT == "GV1":
    yo, ytex = T.boy("yota", (-3.05, 1.0, 0), rot=-73)
    mei, mtex = T.girl("mei", (-2.57, 1.58, 0), rot=-150, arms={"L": ((0.17, 0.16, 1.0), (0.07, 0.29, 1.05)), "R": ((-0.17, 0.16, 1.0), (-0.07, 0.29, 1.05))})
    gift("cookie", mei, (0, 0.31, 1.06), (0.15, 0.1, 0.07), (1.0, 0.72, 0.8), (0.9, 0.2, 0.3))
    plan = [("blushtalk", "base"), ("blush", "base"), ("blush", "talk"), ("blush", "smile"), ("blush", "blink"), ("blushsmile", "smile")]
else:
    yo, ytex = T.boy("yota", (-3.05, 1.0, 0), rot=-62, arms={"L": ((0.27, 0.14, 1.1), (0.24, 0.32, 1.14)), "R": ((-0.27, 0.14, 1.1), (-0.24, 0.32, 1.14))})
    gift("big", yo, (0, 0.36, 1.2), (0.46, 0.34, 0.36), (0.45, 0.7, 1.0), (1.0, 0.82, 0.3))
    mei, mtex = T.girl("mei", (-2.57, 1.58, 0), rot=-162)
    plan = [("shockc", "base"), ("shockc", "talk"), ("shock", "base"), ("blush", "talk"), ("blush", "smile"),
            ("blushtalk", "smile"), ("blushsmile", "smile"), ("shockc", "blink"), ("blush", "blink")]
W.camera((-0.96, -0.25, 1.45), (-2.78, 1.3, 1.33), lens=29, fstop=3.5)
if TEST:
    plan = plan[:1]; sc.render.resolution_percentage = 50
T.outlines(2.0)
t = time.time()
for me, yo_e in plan:
    p = os.path.join(OUT, "%s_%s_%s%s.png" % (SHOT, me, yo_e, "_test" if TEST else ""))
    if os.path.exists(p) and not TEST: continue
    T.set_expr(mtex, "mei", me); T.set_expr(ytex, "yota", yo_e)
    sc.render.filepath = p
    bpy.ops.render.render(write_still=True)
    print("frame %s %.1fs" % (p, time.time() - t), flush=True); t = time.time()
