"""s2_lookdev.py ― 新シリーズの見た目テスト（夕方の教室、窓辺の湊、ひより視点）1枚だけ描く"""
import sys, time, math
sys.path.insert(0, __import__("os").path.dirname(__file__))
import bpy
import s2_world as W

samples = int(sys.argv[sys.argv.index("--samples") + 1]) if "--samples" in sys.argv else 64
out = sys.argv[sys.argv.index("--out") + 1] if "--out" in sys.argv else "/tmp/s2_look.png"
sc = W.reset(samples)
room = W.classroom()
W.person("minato", (-3.35, 1.2, 0), 1.74, rot=-70)
cam = W.camera((0.6, -2.6, 1.32), (-3.35, 1.2, 1.45), lens=40, fstop=2.2)
sc.render.filepath = out
t = time.time(); bpy.ops.render.render(write_still=True); print("rendered", out, "%.1fs" % (time.time() - t))
