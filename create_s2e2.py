"""
create_s2e2.py ― 『君は写真に写らない』第2話「花瓶の席」の3Dカット（朝の教室）
  python create_s2e2.py --shot A|B|V [--samples 48]
  A: 朝、教室に入る。窓際の席に白い花瓶。その横に湊が立って花を見ている（ゆっくり近づく）… 60コマ
  B: 凛に話しかけられて振り向き直すと、同じ場所に湊はいない（花瓶だけ）… 1枚
  V: 花瓶のアップ（奥に湊がぼやけて立つ）… 1枚
出力: frames_S2E2/<shot>/0001.png ...
"""
import os, sys, math, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
import s2_world as W

arg = lambda k, d: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
SHOT = arg("--shot", "A"); SAMPLES = int(arg("--samples", "48")); TEST = "--test" in sys.argv
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frames_S2E2", SHOT if not TEST else "test")
os.makedirs(OUT, exist_ok=True)

sc = W.reset(SAMPLES)
room = W.classroom(**W.MORNING)
# 窓際・前から2列目の机（花瓶の席）
dk = min((o for o in bpy.data.objects if o.name.startswith("desk") and o.type == "EMPTY"),
         key=lambda o: (o.location.x + 2.6) ** 2 + (o.location.y - 1.25) ** 2)
DX, DY = dk.location.x, dk.location.y
W.vase((DX + 0.08, DY + 0.04, 0.735))
VASE = (DX + 0.08, DY + 0.04, 0.95)
mi = W.person("minato", (DX - 0.62, DY + 0.35, 0), 1.74, rot=72, shirt=(0.86, 0.87, 0.86), bottom=(0.05, 0.06, 0.1), hair=(0.025, 0.02, 0.018))
# 前の方で話しているクラスメイト（誰も湊を見ない）
W.person("cl1", (1.6, 3.5, 0), 1.6, female=True, rot=150, shirt=(0.9, 0.9, 0.9), bottom=(0.1, 0.12, 0.22), long_hair=True)
W.person("cl2", (2.2, 3.2, 0), 1.58, female=True, rot=-150, shirt=(0.9, 0.9, 0.9), bottom=(0.1, 0.12, 0.22))
W.person("cl3", (2.6, 2.4, 0), 1.72, rot=-120, shirt=(0.88, 0.88, 0.88), bottom=(0.05, 0.06, 0.1))

def tree(o):
    yield o
    for c in o.children:
        yield from tree(c)

def ghost(o):
    for p in tree(o):
        p.visible_camera = p.visible_shadow = p.visible_glossy = p.visible_diffuse = p.visible_transmission = False

C0, C1 = (0.5, -3.5, 1.52), (-0.55, -1.45, 1.47)
cam = W.camera(C0, VASE, lens=35, fstop=2.4)

def lerp(a, b, u): return tuple(x + (y - x) * u for x, y in zip(a, b))

frames = [1]
if SHOT == "A":
    n = 60; frames = list(range(1, n + 1))
    for f in frames:
        u = (f - 1) / (n - 1); u = u * u * (3 - 2 * u)
        cam.location = lerp(C0, C1, u); W.aim(cam, VASE)
        cam.keyframe_insert("location", frame=f); cam.keyframe_insert("rotation_euler", frame=f)
elif SHOT == "B":
    ghost(mi); cam.location = C1; W.aim(cam, VASE)
elif SHOT == "V":
    cam.location = (DX + 0.95, DY - 0.75, 1.0); cam.data.lens = 50; cam.data.dof.aperture_fstop = 1.8; W.aim(cam, VASE)
cam.data.dof.use_dof = True
cam.data.dof.focus_object = None
if TEST:
    frames = [int(arg("--frame", "60"))] if SHOT == "A" else [1]
sc.frame_start, sc.frame_end = frames[0], frames[-1]
t = time.time()
for f in frames:
    p = os.path.join(OUT, "%04d.png" % f)
    if os.path.exists(p) and not TEST: continue
    sc.frame_set(f)
    from mathutils import Vector
    cam.data.dof.focus_distance = (Vector(cam.location) - Vector(VASE)).length
    sc.render.filepath = p
    bpy.ops.render.render(write_still=True)
    print("frame %d %.1fs" % (f, time.time() - t), flush=True); t = time.time()
