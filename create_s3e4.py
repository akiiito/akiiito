"""
create_s3e4.py ― 『恋は心理学で落とせる？』第4話「ミラーリング」の絵（放課後の教室・窓辺の二人がしぐさを真似る）
  python create_s3e4.py --yp chin|head|banzai|down --mp chin|head|banzai|down [--samples 16] [--test]
  めい（右）は陽太（左）を鏡のように真似する（陽太が右手なら、めいは左手）
  アップは第1話の frames_S3E1/MC_*（めい）・YC_*（陽太）を使う
出力: frames_S3E4/MR_<陽太のポーズ>_<めいのポーズ>_<めいの表情>_<陽太の表情>.png
"""
import os, sys, math, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
import s2_world as W, s3_toon as T

arg = lambda k, d: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
YP = arg("--yp", "down"); MP = arg("--mp", "down"); SAMPLES = int(arg("--samples", "16")); TEST = "--test" in sys.argv
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frames_S3E4"); os.makedirs(OUT, exist_ok=True)

G = {"down": None,
     "chin": {"L": ((0.17, 0.18, 1.08), (0.06, 0.12, 1.27))},
     "head": {"L": ((0.27, 0.05, 1.45), (0.07, 0.0, 1.63))},
     "banzai": {"L": ((0.27, 0.03, 1.56), (0.03, 0.03, 1.69)), "R": ((-0.27, 0.03, 1.56), (-0.03, 0.03, 1.69))}}   # 頭の上で大きなまる
B = {"down": None,
     "chin": {"R": ((-0.2, 0.22, 1.24), (-0.04, 0.13, 1.47))},
     "head": {"R": ((-0.31, 0.05, 1.58), (-0.07, 0.0, 1.76))},
     "banzai": {"L": ((0.31, 0.03, 1.72), (0.03, 0.03, 1.84)), "R": ((-0.31, 0.03, 1.72), (-0.03, 0.03, 1.84))}}
PLAN = {("chin", "down"): [("smile", "base"), ("smiletalk", "base"), ("blink", "base")],
        ("chin", "chin"): [("smile", "base"), ("smiletalk", "base"), ("smile", "blink")],
        ("head", "head"): [("smile", "base"), ("smiletalk", "base"), ("smile", "smile")],
        ("banzai", "down"): [("base", "smile"), ("shock", "smile")],
        ("banzai", "banzai"): [("shockc", "smile"), ("shockc", "talk"), ("blush", "smile"), ("blushtalk", "smile"),
                               ("blush", "talk"), ("blushsmile", "smile"), ("blush", "blink")]}

sc = W.reset(SAMPLES); sc.view_settings.view_transform = "Standard"
W.classroom(**W.MORNING)
yo, ytex = T.boy("yota", (-3.05, 1.0, 0), rot=-73, arms=B[YP])
mei, mtex = T.girl("mei", (-2.57, 1.58, 0), rot=-162, arms=G[MP])
W.camera((-0.96, -0.25, 1.45), (-2.78, 1.3, 1.36), lens=29, fstop=3.5)
plan = PLAN.get((YP, MP), [("base", "base")])
if TEST:
    plan = plan[:1]; sc.render.resolution_percentage = 50
T.outlines(2.0)
t = time.time()
for me, yo_e in plan:
    p = os.path.join(OUT, "MR_%s_%s_%s_%s%s.png" % (YP, MP, me, yo_e, "_test" if TEST else ""))
    if os.path.exists(p) and not TEST: continue
    T.set_expr(mtex, "mei", me); T.set_expr(ytex, "yota", yo_e)
    sc.render.filepath = p
    bpy.ops.render.render(write_still=True)
    print("frame %s %.1fs" % (p, time.time() - t), flush=True); t = time.time()
