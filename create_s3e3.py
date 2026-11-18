"""
create_s3e3.py ― 『恋は心理学で落とせる？』第3話「ネームコーリング」の絵（朝の教室・窓辺で話す二人）
  python create_s3e3.py --shot TW [--samples 16] [--test]
  TW: 窓辺の陽太に話しかけるめい（二人の表情の組み合わせ）
  アップは第1話の frames_S3E1/MC_*（めい）・YC_*（陽太）を使う
出力: frames_S3E3/TW_<mei>_<yota>.png
"""
import os, sys, math, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
import s2_world as W, s3_toon as T

arg = lambda k, d: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
SHOT = arg("--shot", "TW"); SAMPLES = int(arg("--samples", "16")); TEST = "--test" in sys.argv
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frames_S3E3"); os.makedirs(OUT, exist_ok=True)

sc = W.reset(SAMPLES); sc.view_settings.view_transform = "Standard"
W.classroom(**W.MORNING)
YO = (-3.05, 1.0)
yo, ytex = T.boy("yota", (YO[0], YO[1], 0), rot=-73)
mei, mtex = T.girl("mei", (-2.57, 1.58, 0), rot=-162, arm_pose="down")
W.camera((-0.96, -0.25, 1.45), (-2.78, 1.3, 1.3), lens=29, fstop=3.5)
plan = [("smiletalk", "base"), ("smile", "base"), ("talk", "base"), ("base", "base"), ("blink", "base"),
        ("smile", "talk"), ("base", "talk"), ("shock", "base"), ("shockc", "base"), ("blush", "smile"),
        ("blushtalk", "smile"), ("blushsmile", "smile"), ("smile", "blink")]
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
