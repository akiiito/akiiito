"""
create_pov1.py ― 『POV：好きな人が7日後に転校する』パート1 の絵（1コマずつ・12fps）
  見ている人＝めい（カメラ＝めいの目、画面の下に自分の手が映る）。陽太がこちらに話しかける。
  python create_pov1.py [--samples 10] [--start 0] [--end 312] [--test 0,60,180]
  口パクは pov1_lines.json（make_reel_pov1.py --voice で作る）の陽太の声に合わせる
出力: frames_POV1/0001.png …
"""
import os, sys, math, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
from mathutils import Vector
import s2_world as W, s3_toon as T

HERE = os.path.dirname(os.path.abspath(__file__))
arg = lambda k, d: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
SAMPLES = int(arg("--samples", "10")); FPS = 12; N = int(26.0 * FPS)
START = int(arg("--start", "0")); STOP = int(arg("--end", str(N)))
TEST = [int(x) for x in arg("--test", "").split(",") if x]
OUT = os.path.join(HERE, "frames_POV1" + ("_test" if TEST else "")); os.makedirs(OUT, exist_ok=True)
LINES = json.load(open(os.path.join(HERE, "pov1_lines.json"), encoding="utf-8"))
YSPANS = [(l[0], l[1]) for l in LINES if l[5] == "yota"]

sc = W.reset(SAMPLES); sc.view_settings.view_transform = "Standard"
W.classroom(**W.MORNING)
YO0 = Vector((-3.05, 1.0, 0)); HEAD = 1.55
yo, ytex = T.boy("yota", tuple(YO0), rot=90)
cam = W.camera((-1.25, -0.75, 1.42), (-3.05, 1.0, 1.5), lens=17, fstop=2.8)

# ---- 自分（めい）の腕：カメラの子。カメラ座標で右が+X、上が+Y、前が-Z
skin = T.toon("me_skin", (1.0, 0.91, 0.86), (0.96, 0.78, 0.74))
navy = T.toon("me_blazer", (0.2, 0.23, 0.4), (0.13, 0.14, 0.28))
cuff = T.toon("me_cuff", (0.97, 0.97, 0.97), (0.78, 0.8, 0.9))
def piece(name, r, m):
    bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=r, depth=1.0); o = bpy.context.object; o.name = name
    o.data.materials.append(m); bpy.ops.object.shade_smooth(); o.parent = cam; T.link(o); return o
def ball(name, r, m):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8, radius=r); o = bpy.context.object; o.name = name
    o.scale = (0.8, 1.25, 0.8); o.data.materials.append(m); bpy.ops.object.shade_smooth(); o.parent = cam; T.link(o); return o
ARMS = {s: dict(up=piece("upper" + s, 0.045, navy), lo=piece("lower" + s, 0.04, navy), cf=piece("cuff" + s, 0.042, cuff), hd=ball("hand" + s, 0.034, skin))
        for s in "LR"}
def between(o, p0, p1):
    p0, p1 = Vector(p0), Vector(p1); d = p1 - p0
    o.location = (p0 + p1) / 2; o.scale = (1, 1, max(d.length, 1e-3))
    o.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
def set_arm(s, sh, el, hn):
    a = ARMS[s]; hn = Vector(hn); el = Vector(el)
    between(a["up"], sh, el); between(a["lo"], el, el + (hn - el) * 0.86); between(a["cf"], el + (hn - el) * 0.84, el + (hn - el) * 0.93)
    a["hd"].location = hn; a["hd"].rotation_euler = (hn - el).to_track_quat("Y", "Z").to_euler()

def ease(x): x = min(max(x, 0.0), 1.0); return x * x * (3 - 2 * x)
def lerp(a, b, k): return a + (b - a) * k
def lerpv(a, b, k): return Vector(a).lerp(Vector(b), k)

A = Vector((-1.25, -0.75, 1.42)); B = Vector((-2.2, 0.35, 1.42))
TO_Y = (YO0.xy - B.xy).normalized()
B2 = B + Vector((TO_Y.x, TO_Y.y, 0)) * -0.25                    # 近づいた位置（陽太の方へ）

def state(t):
    """t秒の時点のカメラ位置・注視点・腕・陽太の位置/向き/表情"""
    walk = ease(t / 3.4)
    pos = lerpv(A, B, walk)
    stepping = 0.0 < t < 3.4
    ph = t * 2.1 * math.pi
    if stepping:
        pos = pos + Vector((0, 0, 0.022 * abs(math.sin(ph)) - 0.011))
    pos = lerpv(pos, B2, ease((t - 14.8) / 2.0) - ease((t - 24.8) / 1.2) * 0.6)
    yo_p = YO0.copy()
    k = ease((t - 21.9) / 0.8); yo_p = lerpv(YO0, YO0 + (Vector((B.x, B.y, 0)) - YO0).normalized() * 0.22, k)
    yo_p.z = 0.02 * math.sin(min(max((t - 21.9) / 0.8, 0), 1) * math.pi)
    look = Vector((yo_p.x, yo_p.y, HEAD - 0.02))
    look += Vector((0.25 * math.sin(ph * 0.5), 0, 0)) * (1 if stepping else 0)       # 歩くときの揺れ
    look.z -= 0.28 * (ease((t - 7.8) / 0.6) - ease((t - 9.9) / 0.5))                 # うつむく
    # 「やっぱり明日言う！」で、ぱっと顔をそむける
    away = ease((t - 17.9) / 0.35) - ease((t - 19.5) / 0.4)
    d = look - pos; ang = math.radians(55) * away
    look = pos + Vector((d.x * math.cos(ang) - d.y * math.sin(ang), d.x * math.sin(ang) + d.y * math.cos(ang), d.z - 0.15 * away))
    look += Vector((0, 0, 0.01 * math.sin(t * 1.3)))                                  # 呼吸
    # 陽太の向き：窓の外(90°) → こちらへ振り向く
    face = (Vector((pos.x, pos.y, 0)) - yo_p).normalized()
    rot_face = math.degrees(math.atan2(-face.x, face.y))
    while rot_face < 90: rot_face += 360
    yrot = lerp(90, rot_face, ease((t - 3.6) / 0.7))
    # 表情
    talking = any(st <= t <= en - 0.05 for st, en in YSPANS)
    flap = talking and (int(t * FPS) % 3 != 2)
    if 17.9 <= t < 19.6: e = "shockc" if not flap else "talk"
    elif 19.6 <= t < 24.6: e = "blushtalk" if flap else "blush"
    elif t >= 24.6: e = "blushsmile"
    else: e = "talk" if flap else "base"
    bl = (t % 3.1) < 0.17 and not talking and e in ("base", "blush")
    if bl: e = "blink"
    # 腕：歩くときは振る、話しかけるときは右手をのばす
    sw = math.sin(ph) if stepping else 0.0
    reach = ease((t - 15.3) / 0.9) - ease((t - 17.8) / 0.3)
    arms = {}
    for s, sx in (("L", -1), ("R", 1)):
        rest_h = Vector((0.15 * sx, -0.28 + 0.035 * sw * sx, -0.46))
        rest_e = Vector((0.24 * sx, -0.42, -0.24))
        if s == "R":
            hn = lerpv(rest_h, Vector((0.06, -0.13, -0.52)), reach); el = lerpv(rest_e, Vector((0.17, -0.3, -0.3)), reach)
        else:
            hn, el = rest_h, rest_e
        arms[s] = (Vector((0.22 * sx, -0.55, 0.05)), el, hn)
    return pos, look, arms, yo_p, yrot, e

T.outlines(2.0)
frames = TEST or range(START, STOP)
t0 = time.time()
for f in frames:
    p = os.path.join(OUT, "%04d.png" % (f + 1))
    if os.path.exists(p) and not TEST: continue
    t = f / FPS
    pos, look, arms, yo_p, yrot, e = state(t)
    cam.location = pos; W.aim(cam, look)
    cam.data.dof.focus_distance = (Vector((yo_p.x, yo_p.y, HEAD)) - pos).length
    for s, (sh, el, hn) in arms.items(): set_arm(s, sh, el, hn)
    yo.location = yo_p; yo.rotation_euler = (0, 0, math.radians(yrot))
    T.set_expr(ytex, "yota", e)
    tmp = p[:-4] + "_tmp.png"
    sc.render.filepath = tmp
    bpy.ops.render.render(write_still=True)
    os.replace(tmp, p)
    print("frame %s t=%.2f %s %.1fs" % (p, t, e, time.time() - t0), flush=True); t0 = time.time()
