"""s3_lookdev.py ― アニメ調キャラの見た目テスト（朝の教室、めいと陽太）"""
import sys, os, time, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
import s2_world as W, s3_toon as T
samples = int(sys.argv[sys.argv.index("--samples") + 1]) if "--samples" in sys.argv else 16
out = sys.argv[sys.argv.index("--out") + 1] if "--out" in sys.argv else "/tmp/s3_look.png"
sc = W.reset(samples)
sc.view_settings.view_transform = "Standard"
W.classroom(**W.MORNING)
mei, _ = T.girl("mei", (0.0, 0.0, 0), rot=-13)
yo, _ = T.boy("yota", (-0.9, -0.9, 0), rot=-40)
T.outlines(2.0)
cam = W.camera((0.35, 1.5, 1.42), (0.0, 0.0, 1.38), lens=45, fstop=4.0)
sc.render.filepath = out
t = time.time(); bpy.ops.render.render(write_still=True); print("rendered %.1fs" % (time.time() - t))
