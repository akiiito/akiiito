"""
create_s3e2.py ― 『恋は心理学で落とせる？』第2話「吊り橋効果」の絵（文化祭のお化け屋敷）
  python create_s3e2.py --shot HW|HG|HM|HC [--samples 16]
  HW: 暗幕の通路を進む二人（めいは自信まんまん、陽太は眠そう）
  HG: おばけが飛び出す
  HM: めいのアップ（赤い光。表情 shock shockc talk）
  HC: めいが陽太の腕にしがみつく二人のアップ（表情の組み合わせ）
  教室でのめいのアップは第1話の frames_S3E1/MC_* を使う
出力: frames_S3E2/<shot>_<mei>[_<yota>].png
"""
import os, sys, math, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
import s2_world as W, s3_toon as T

arg = lambda k, d: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
SHOT = arg("--shot", "HW"); SAMPLES = int(arg("--samples", "16"))
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frames_S3E2"); os.makedirs(OUT, exist_ok=True)

sc = W.reset(SAMPLES); sc.view_settings.view_transform = "Standard"
T.haunted()
def key(loc, look, e=25.0, col=(0.75, 0.8, 1.0)):
    l = bpy.data.lights.new("key", "SPOT"); l.energy = e; l.color = col; l.spot_size = math.radians(50); l.spot_blend = 0.9
    o = bpy.data.objects.new("key", l); bpy.context.collection.objects.link(o); o.location = loc; W.aim(o, look)
mtex = ytex = None
if SHOT == "HW":
    mei, mtex = T.girl("mei", (0.22, 1.1, 0), rot=172); yo, ytex = T.boy("yota", (-0.32, 1.6, 0), rot=185)
    W.camera((0.1, -1.6, 1.45), (0.0, 1.4, 1.25), lens=32, fstop=4.0); key((0.3, -1.2, 2.2), (0, 1.3, 1.3), 40)
    plan = [("smile", "base")]
elif SHOT == "HG":
    T.ghost("ghost", (0.0, 0.35, 0), rot=180)
    W.camera((0.05, -0.75, 1.45), (0.0, 0.35, 1.38), lens=26, fstop=4.0); key((0.4, -0.6, 2.4), (0, 0.35, 1.3), 35, (1.0, 0.5, 0.5))
    plan = [(None, None)]
elif SHOT == "HM":
    mei, mtex = T.girl("mei", (0.2, 0.8, 0), rot=180)
    W.camera((0.25, -0.62, 1.36), (0.2, 0.8, 1.38), lens=45, fstop=2.8); key((0.6, -0.4, 1.8), (0.2, 0.8, 1.4), 18, (1.0, 0.45, 0.45))
    plan = [(e, None) for e in ("shock", "shockc", "talk", "base", "blink")]
else:  # HC
    yo, ytex = T.boy("yota", (-0.17, 0.9, 0), rot=180); mei, mtex = T.girl("mei", (0.16, 0.84, 0), rot=196, arm_pose="cling")
    W.camera((0.0, -1.05, 1.45), (0.0, 0.88, 1.38), lens=34, fstop=3.2); key((0.2, -0.5, 2.0), (0, 0.9, 1.45), 22)
    plan = [("shockc", "base"), ("shock", "base"), ("blush", "base"), ("blushtalk", "base"), ("blush", "talk"),
            ("blush", "smile"), ("shockc", "talk"), ("blush", "blink")]
T.outlines(2.0)
t = time.time()
for me, yo_e in plan:
    name = SHOT + ("_" + me if me else "") + ("_" + yo_e if yo_e and SHOT in ("HW", "HC") else "")
    p = os.path.join(OUT, name + ".png")
    if os.path.exists(p): continue
    if mtex and me: T.set_expr(mtex, "mei", me)
    if ytex and yo_e: T.set_expr(ytex, "yota", yo_e)
    sc.render.filepath = p
    bpy.ops.render.render(write_still=True)
    print("frame %s %.1fs" % (p, time.time() - t), flush=True); t = time.time()
