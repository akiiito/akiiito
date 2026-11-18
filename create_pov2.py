"""
create_pov2.py ― 『POV：好きな人が7日後に転校する』パート2「残り6日」の絵（1コマずつ・12fps）
  見ている人＝めい（カメラ＝めいの目、画面の下に自分の手が映る）。陽太がこちらに話しかける。
  python create_pov2.py [--samples 10] [--start 0] [--end 312] [--test 0,60,180]
  口パクは pov2_lines.json（make_reel_pov2.py --voice で作る）の陽太の声に合わせる
出力: frames_POV2/0001.png …
"""
import os, sys, math, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
from mathutils import Vector
import s2_world as W, s3_toon as T

HERE = os.path.dirname(os.path.abspath(__file__))
arg = lambda k, d: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
SAMPLES = int(arg("--samples", "10")); FPS = 12; N = int(27.0 * FPS)
START = int(arg("--start", "0")); STOP = int(arg("--end", str(N)))
TEST = [int(x) for x in arg("--test", "").split(",") if x]
OUT = os.path.join(HERE, "frames_POV2" + ("_test" if TEST else "")); os.makedirs(OUT, exist_ok=True)
LINES = json.load(open(os.path.join(HERE, "pov2_lines.json"), encoding="utf-8"))
YSPANS = [(l[0], l[1]) for l in LINES if l[5] == "yota"]

sc = W.reset(SAMPLES); sc.view_settings.view_transform = "Standard"
W.classroom(**W.MORNING)
YO0 = Vector((-3.05, 1.0, 0)); HEAD = 1.55
yo, ytex = T.boy("yota", tuple(YO0), rot=0)
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

B = Vector((-2.2, 0.35, 1.42)); A = Vector((-1.25, -0.75, 1.42))
TO_A = (A.xy - B.xy).normalized()
YP = Vector((B.x + TO_A.x * 1.0, B.y + TO_A.y * 1.0, 0))           # 陽太は後ろ（入口側）から来て立っている
YP2 = Vector((B.x + TO_A.x * 0.88, B.y + TO_A.y * 0.88, 0))          # 「いいよ」で一歩近づく
WIN = Vector((-3.6, 1.6, 1.45))                                     # 最初は窓の外を見ている
B2 = B + Vector((TO_A.x, TO_A.y, 0)) * 0.15                         # 「だめかな？」で少し近づく
L = {round(l[0], 1): l for l in LINES}
def T0(i): return LINES[i][0]
def T1(i): return LINES[i][1]

def state(t):
    ph = t * 2.1 * math.pi
    pos = lerpv(B, B2, ease((t - T0(6)) / 0.8))
    k = ease((t - T1(7) - 0.1) / 0.7)
    yo_p = lerpv(YP, YP2, ease((t - T0(7) - 0.4) / 0.7))
    yo_p.z = 0.02 * math.sin(min(max((t - T0(7) - 0.4) / 0.7, 0), 1) * math.pi)
    face_l = Vector((yo_p.x, yo_p.y, HEAD - 0.02))
    turn = ease((t - 3.05) / 0.45)                                               # 声をかけられて振り向く
    win_l = WIN + Vector((0.15 * math.sin(t * 0.7), 0, 0))
    look = win_l.lerp(face_l, turn)
    look.z += 0.06 * math.sin(math.pi * min(max((t - 3.05) / 0.45, 0), 1))
    # 「まだ秘密！」で少し目をそらす／「作戦2」で上を向いて考える／「反則でしょ」でうつむく
    away = ease((t - T0(2) - 0.6) / 0.3) - ease((t - T1(2) + 0.6) / 0.4)
    up = ease((t - T0(3)) / 0.5) - ease((t - T1(3)) / 0.5)
    down = ease((t - T0(8)) / 0.5)
    d = look - pos; ang = math.radians(-30) * away
    look = pos + Vector((d.x * math.cos(ang) - d.y * math.sin(ang), d.x * math.sin(ang) + d.y * math.cos(ang), d.z))
    look.z += 0.1 * up - 0.12 * down
    look += Vector((0, 0, 0.01 * math.sin(t * 1.3)))
    face = (Vector((pos.x, pos.y, 0)) - yo_p).normalized()
    yrot = math.degrees(math.atan2(-face.x, face.y))
    talking = any(st <= t <= en - 0.05 for st, en in YSPANS)
    flap = talking and (int(t * FPS) % 3 != 2)
    if T0(5) - 0.2 <= t < T1(5): e = "shockc" if not flap else "talk"
    elif T1(5) <= t < T0(7): e = "blush"
    elif T0(7) <= t < T1(7): e = "blushtalk" if flap else "blush"
    elif t >= T1(7): e = "blushsmile"
    else: e = "talk" if flap else "base"
    bl = (t % 3.1) < 0.17 and not talking and e in ("base", "blush")
    if bl: e = "blink"
    # 腕：「一緒に帰ろ？」で右手をのばす（そで口をつまむ感じ）、「作戦2」で左手をぐっ
    reach = ease((t - T0(4) - 0.4) / 0.9) - ease((t - T1(6)) / 0.5)
    fist = ease((t - T0(3)) / 0.4) - ease((t - T1(3)) / 0.4)
    arms = {}
    for s, sx in (("L", -1), ("R", 1)):
        rest_h = Vector((0.15 * sx, -0.28 + 0.01 * math.sin(t * 1.3), -0.46))
        rest_e = Vector((0.24 * sx, -0.42, -0.24))
        if s == "R":
            hn = lerpv(rest_h, Vector((0.07, -0.16, -0.55)), reach); el = lerpv(rest_e, Vector((0.17, -0.32, -0.3)), reach)
        else:
            hn = lerpv(rest_h, Vector((-0.11, -0.12, -0.42)), fist); el = lerpv(rest_e, Vector((-0.22, -0.34, -0.28)), fist)
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
