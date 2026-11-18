"""
create_s3e5.py ― 『恋は心理学で落とせる？』第5話「ゲインロス効果」の絵（朝の教室・窓辺の二人）
  python create_s3e5.py --shot TW|YC [--samples 16]
  TW: 窓辺の二人（めいのツン顔・陽太のしょんぼり顔など）
  YC: 陽太のアップ（しょんぼり）
出力: frames_S3E5/TW_<mei>_<yota>.png, YC_<yota>.png
"""
import os, sys, math, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
import s2_world as W, s3_toon as T

arg = lambda k, d: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
SHOT = arg("--shot", "TW"); SAMPLES = int(arg("--samples", "16"))
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frames_S3E5"); os.makedirs(OUT, exist_ok=True)

sc = W.reset(SAMPLES); sc.view_settings.view_transform = "Standard"
W.classroom(**W.MORNING)
if SHOT == "TW":
    yo, ytex = T.boy("yota", (-3.05, 1.0, 0), rot=-73)
    mei, mtex = T.girl("mei", (-2.57, 1.58, 0), rot=-162)
    W.camera((-0.96, -0.25, 1.45), (-2.78, 1.3, 1.36), lens=29, fstop=3.5)
    plan = [("cold", "base"), ("cold", "talk"), ("coldtalk", "base"), ("cold", "blink"), ("cold", "sad"),
            ("blushtalk", "sad"), ("blush", "sad"), ("shockc", "talk"), ("shockc", "smile"), ("shock", "smile"),
            ("blush", "smile"), ("blush", "talk"), ("blushsmile", "smile"), ("blush", "blink")]
else:
    yo, ytex = T.boy("yota", (-3.05, 1.0, 0), rot=-157); mtex = None
    W.camera((-2.5, -0.35, 1.52), (-3.05, 1.0, 1.5), lens=42, fstop=2.8)
    plan = [(None, e) for e in ("sad", "sadtalk", "sadblink")]
T.outlines(2.0)
t = time.time()
for me, yo_e in plan:
    p = os.path.join(OUT, ("TW_%s_%s.png" % (me, yo_e)) if me else ("YC_%s.png" % yo_e))
    if os.path.exists(p): continue
    if me: T.set_expr(mtex, "mei", me)
    T.set_expr(ytex, "yota", yo_e)
    sc.render.filepath = p
    bpy.ops.render.render(write_still=True)
    print("frame %s %.1fs" % (p, time.time() - t), flush=True); t = time.time()
