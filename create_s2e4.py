"""
create_s2e4.py ― 『君は写真に写らない』第4話「未読」の3Dカット（夜の旧校舎の階段、懐中電灯）
  python create_s2e4.py --shot N|P [--samples 48] [--test]
  N: 懐中電灯で階段を照らしながら上る。踊り場の床でスマホが光っている … 48コマ
  P: 踊り場に落ちた凛のスマホを上から（画面のUIは動画側で重ねる）… 1枚
"""
import os, sys, math, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
from mathutils import Vector
import s2_world as W

arg = lambda k, d: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
SHOT = arg("--shot", "N"); SAMPLES = int(arg("--samples", "48")); TEST = "--test" in sys.argv
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frames_S2E4", SHOT if not TEST else "test_" + SHOT)
os.makedirs(OUT, exist_ok=True)

sc = W.reset(SAMPLES)
st = W.stairwell(haze=0.015, sun_str=1.2, sun_elev=30.0, night=True)
PH = (0.55, 3.95, 1.8)
W.phone(PH, rot_z=18, glow=1.6)
LOOK = (0.65, 4.2, 2.3)
C0, C1 = (1.05, -1.6, 1.45), (0.95, -0.3, 1.6)
cam = W.camera(C0, LOOK, lens=26, fstop=2.4)
torch = W.flashlight(cam, energy=60.0, spread=30.0)

def lerp(a, b, u): return tuple(x + (y - x) * u for x, y in zip(a, b))
frames = [1]; focus = PH
if SHOT == "N":
    n = 48; frames = list(range(1, n + 1))
    for f in frames:
        u = (f - 1) / (n - 1); u = u * u * (3 - 2 * u)
        p = lerp(C0, C1, u); cam.location = (p[0], p[1], p[2] + 0.03 * math.sin(f / n * 6 * math.pi))
        sway = (0.25 * math.sin(f * 0.21) + 0.12 * math.sin(f * 0.5 + 1.0), 0, 0.15 * math.sin(f * 0.17 + 0.4))
        W.aim(cam, (LOOK[0] + sway[0], LOOK[1], LOOK[2] + sway[2] - 0.35 * (1 - u)))   # 足元→踊り場へ光を振る
        cam.keyframe_insert("location", frame=f); cam.keyframe_insert("rotation_euler", frame=f)
elif SHOT == "P":
    cam.location = (PH[0] + 0.02, PH[1] - 0.15, PH[2] + 0.42); W.aim(cam, (PH[0], PH[1] + 0.01, PH[2]))
    cam.data.lens = 35; cam.data.dof.aperture_fstop = 2.8
    torch.data.energy = 6.0
if SHOT == "P":                                     # 画面の四隅の画素座標（動画側でUIを遠近変形して重ねる）
    import json
    from bpy_extras.object_utils import world_to_camera_view
    so = bpy.data.objects["screen"]; sc.frame_set(1)
    mw = so.matrix_world; vs = [mw @ v.co for v in so.data.vertices]
    top = sorted(vs, key=lambda v: v.z)[-4:]
    px = []
    for v in top:
        c = world_to_camera_view(sc, cam, v); px.append((c.x * 720, (1 - c.y) * 1280))
    cx = sum(p[0] for p in px) / 4; cy = sum(p[1] for p in px) / 4
    import math as m_
    px.sort(key=lambda p: m_.atan2(p[1] - cy, p[0] - cx))          # 左上→右上→右下→左下 の順に並べ替える
    tl = min(px, key=lambda p: p[0] + p[1]); i = px.index(tl); px = px[i:] + px[:i]
    json.dump(px, open(os.path.join(OUT, "screen_quad.json"), "w")); print("quad", px)
if TEST:
    frames = [int(arg("--frame", "48"))] if SHOT == "N" else [1]
t = time.time()
for f in frames:
    p = os.path.join(OUT, "%04d.png" % f)
    if os.path.exists(p) and not TEST: continue
    sc.frame_set(f)
    cam.data.dof.focus_distance = (Vector(cam.location) - Vector(focus)).length
    sc.render.filepath = p
    bpy.ops.render.render(write_still=True)
    print("frame %d %.1fs" % (f, time.time() - t), flush=True); t = time.time()
