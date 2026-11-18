"""
create_s3e1.py ― 『恋は心理学で落とせる？』第1話「単純接触効果」の絵（アニメ調・静止画を表情ちがいで描く）
  python create_s3e1.py --shot MC|YC|WD1|WD2|WD3|WD4 [--samples 16]
  MC : めいのアップ（表情: base talk blink shock shockc smile smiletalk blush blushtalk blushsmile）
  YC : 陽太のアップ（窓を背に。表情: base talk blink smile）
  WD*: 教室の引き。窓辺の陽太の前を、めいが何度も通る（1回目〜20回目）
出力: frames_S3E1/<shot>_<expr>.png  ― 口パク・まばたきは動画側でこの静止画を切り替える
"""
import os, sys, math, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
import s2_world as W, s3_toon as T

arg = lambda k, d: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
SHOT = arg("--shot", "MC"); SAMPLES = int(arg("--samples", "16"))
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frames_S3E1"); os.makedirs(OUT, exist_ok=True)

sc = W.reset(SAMPLES); sc.view_settings.view_transform = "Standard"
W.classroom(**W.MORNING)
YO = (-3.05, 1.0)
yo_rot = -157
if SHOT == "MC":
    mei, mtex = T.girl("mei", (0.0, 0.0, 0), rot=-13)
    yo, ytex = T.boy("yota", (YO[0], YO[1], 0), rot=yo_rot)
    W.camera((0.35, 1.5, 1.42), (0.0, 0.0, 1.38), lens=45, fstop=3.2)
    plan = [("mei", e) for e in ("base", "talk", "blink", "shock", "shockc", "smile", "smiletalk", "blush", "blushtalk", "blushsmile")]
elif SHOT == "YC":
    yo, ytex = T.boy("yota", (YO[0], YO[1], 0), rot=yo_rot)
    mtex = None
    W.camera((-2.5, -0.35, 1.52), (YO[0], YO[1], 1.5), lens=42, fstop=2.8)
    plan = [("yota", e) for e in ("base", "talk", "blink", "smile", "blush")]
else:
    pose = {"WD1": ((-0.7, -0.5), 34, "down", "smile"), "WD2": ((-1.3, -0.1), 40, "wave", "smile"),
            "WD3": ((-0.9, -0.9), -136, "chin", "smile"), "WD4": ((-2.2, 0.35), 30, "down", "blush")}[SHOT]
    mei, mtex = T.girl("mei", (pose[0][0], pose[0][1], 0), rot=pose[1], arm_pose=pose[2])
    yo, ytex = T.boy("yota", (YO[0], YO[1], 0), rot=yo_rot)
    W.camera((1.25, -2.7, 1.38), (-2.2, 0.7, 1.15), lens=30, fstop=5.6)
    plan = [("mei", pose[3])]
T.outlines(2.0)
t = time.time()
for who, e in plan:
    p = os.path.join(OUT, "%s_%s.png" % (SHOT, e))
    if os.path.exists(p): continue
    T.set_expr(mtex if who == "mei" else ytex, who, e)
    sc.render.filepath = p
    bpy.ops.render.render(write_still=True)
    print("frame %s %.1fs" % (p, time.time() - t), flush=True); t = time.time()
