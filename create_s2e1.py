"""
create_s2e1.py ― 『君は写真に写らない』第1話「写らない」の3Dカット
  python create_s2e1.py --shot A|C|D [--samples 32]
  A: 窓辺の湊（ひよりが撮ろうとする。湊がゆっくり振り向く）… 72コマ
  C: 撮った写真（湊は写らない。影と窓への映り込みだけ残る）… 1枚
  D: 顔を上げると窓辺には誰もいない（影も消えている）… 1枚
出力: frames_S2E1/<shot>/0001.png ...
手持ちの揺れは書き出し後に動画側で足す（静止カットはレンダリング1枚で済ませる）。
"""
import os, sys, math, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
import s2_world as W

arg = lambda k, d: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
SHOT = arg("--shot", "A"); SAMPLES = int(arg("--samples", "32"))
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frames_S2E1", SHOT)
os.makedirs(OUT, exist_ok=True)

sc = W.reset(SAMPLES)
room = W.classroom()
MIN_LOC = (-3.35, 1.2, 0)
mi = W.person("minato", MIN_LOC, 1.74, rot=-80, shirt=(0.86, 0.87, 0.86), bottom=(0.05, 0.06, 0.1), hair=(0.025, 0.02, 0.018))
LOOK = (-3.35, 1.2, 1.45)
cam = W.camera((0.6, -2.6, 1.32), LOOK, lens=40, fstop=2.2)

def tree(o):
    yield o
    for c in o.children:
        yield from tree(c)

def ghost(o, camera=False, shadow=True, glossy=True):
    for p in tree(o):
        p.visible_camera = camera; p.visible_shadow = shadow; p.visible_glossy = glossy
        p.visible_diffuse = shadow; p.visible_transmission = glossy

if SHOT == "A":
    n = 72
    sc.frame_start, sc.frame_end = 1, n
    for f in range(1, n + 1):                      # 窓の外を見ている → 1.0〜2.5秒でこちらへ振り向く
        u = min(1.0, max(0.0, (f - 24) / 36.0)); u = u * u * (3 - 2 * u)
        mi.rotation_euler[2] = math.radians(-80 + 62 * u); mi.keyframe_insert("rotation_euler", index=2, frame=f)
elif SHOT == "C":                                  # 写真：本人は写らない。影と、ガラスへの映り込みだけが残る
    ghost(mi, camera=False, shadow=True, glossy=True)
    mi.rotation_euler[2] = math.radians(-18)
    sc.frame_start = sc.frame_end = 1
elif SHOT == "D":                                  # 顔を上げると誰もいない
    ghost(mi, camera=False, shadow=False, glossy=False)
    cam.location = (0.55, -2.5, 1.5); W.aim(cam, (-3.35, 1.2, 1.5))
    sc.frame_start = sc.frame_end = 1

sc.render.filepath = os.path.join(OUT, "")
t = time.time()
for f in range(sc.frame_start, sc.frame_end + 1):
    p = os.path.join(OUT, "%04d.png" % f)
    if os.path.exists(p): continue
    sc.frame_set(f); sc.render.filepath = p
    bpy.ops.render.render(write_still=True)
    print("frame %d %.1fs" % (f, time.time() - t), flush=True); t = time.time()
