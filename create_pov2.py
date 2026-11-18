"""
create_pov2.py ― 『POV：好きな人が7日後に転校する』パート2「残り6日」の絵（夕焼けの屋上）（1コマずつ・12fps）
  見ている人＝めい（カメラ＝めいの目、画面の下に自分の手が映る）。陽太がこちらに話しかける。
  python create_pov2.py [--samples 10] [--start 0] [--end 312] [--test 0,60,180]
  口パクは pov2_lines.json（make_reel_pov2.py --voice で作る）の陽太の声に合わせる
出力: frames_POV2/0001.png …
"""
import os, sys, math, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
from mathutils import Vector
import s2_world as W, s3_toon as T, s4_rooftop as RT

HERE = os.path.dirname(os.path.abspath(__file__))
arg = lambda k, d: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
SAMPLES = int(arg("--samples", "10")); FPS = 12; N = int(31.0 * FPS)
START = int(arg("--start", "0")); STOP = int(arg("--end", str(N)))
TEST = [int(x) for x in arg("--test", "").split(",") if x]
OUT = os.path.join(HERE, "frames_POV2" + ("_test" if TEST else "")); os.makedirs(OUT, exist_ok=True)
LINES = json.load(open(os.path.join(HERE, "pov2_lines.json"), encoding="utf-8"))
YSPANS = [(l[0], l[1]) for l in LINES if l[5] == "yota"]

sc = W.reset(SAMPLES); sc.view_settings.view_transform = "Standard"
ROOF = RT.rooftop()
YO0 = Vector((0.3, 4.55, 0)); HEAD = 1.55
yo, ytex = T.boy("yota", tuple(YO0), rot=0)
cam = W.camera((0, -4.5, 1.42), (0.3, 4.55, 1.5), lens=17, fstop=2.8)

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

S0 = Vector((0.0, -4.55, 1.42))                                   # 階段室の中（扉の前）
C = Vector((0.15, 3.0, 1.42))                                      # 駆け寄って止まる位置
TO_Y = (YO0.xy - C.xy).normalized()
C2 = C + Vector((TO_Y.x, TO_Y.y, 0)) * 0.35                       # 「毎日ここで会お？」で近づく
def T0(i): return LINES[i][0]
def T1(i): return LINES[i][1]
RUN0, RUN1 = 0.55, 3.3

def state(t):
    run = ease((t - RUN0) / (RUN1 - RUN0))
    pos = lerpv(S0, C, run)
    running = RUN0 < t < RUN1
    ph = t * 2.6 * math.pi
    if running:
        pos = pos + Vector((0.025 * math.sin(ph * 0.5), 0, 0.04 * abs(math.sin(ph)) - 0.02))
    huff = max(0.0, 1 - (t - RUN1) / 3.5) if t > RUN1 else 0.0                    # 走ったあとの息切れ
    pos = pos + Vector((0, 0, 0.018 * huff * math.sin(t * 9.0)))
    pos = lerpv(pos, C2, ease((t - T0(6) - 0.2) / 1.2))
    yo_p = YO0.copy()
    st_k = (t - T0(9) - 0.4) / 0.7
    yo_p = lerpv(YO0, YO0 + (Vector((C2.x, C2.y, 0)) - YO0).normalized() * 0.22, ease(st_k))
    yo_p.z = 0.02 * math.sin(min(max(st_k, 0), 1) * math.pi)
    look = Vector((yo_p.x, yo_p.y, HEAD - 0.05))
    if running: look += Vector((0.2 * math.sin(ph * 0.5), 0, 0.05 * math.sin(ph)))
    # 扉を開けた瞬間は少し上（夕日）を見る
    look.z += 0.5 * (1 - ease((t - 0.3) / 1.2))
    away = ease((t - T0(4) - 0.6) / 0.3) - ease((t - T1(4) + 0.3) / 0.4)          # 「まだ秘密！」で目をそらす
    up = ease((t - T0(5)) / 0.5) - ease((t - T1(5)) / 0.5)                       # 作戦2で考える
    down = ease((t - T0(10)) / 0.5)                                              # 反則でしょ…でうつむく
    d = look - pos; ang = math.radians(32) * away
    look = pos + Vector((d.x * math.cos(ang) - d.y * math.sin(ang), d.x * math.sin(ang) + d.y * math.cos(ang), d.z))
    look.z += 0.1 * up - 0.14 * down + 0.01 * math.sin(t * 1.3)
    # 陽太：最初は夕日（+y）を見ている → 名前を呼ばれて振り向く
    face = (Vector((pos.x, pos.y, 0)) - yo_p).normalized()
    rot_face = math.degrees(math.atan2(-face.x, face.y))
    while rot_face < 0: rot_face += 360
    yrot = lerp(0, rot_face, ease((t - T0(2) - 0.5) / 0.7))
    talking = any(st <= t <= en - 0.05 for st, en in YSPANS)
    flap = talking and (int(t * FPS) % 3 != 2)
    if t < T0(2) + 0.6: e = "sadtalk" if flap else "sad"
    elif t < T0(3): e = "smile"
    elif t < T1(3): e = "smiletalk" if flap else "smile"
    elif T0(7) - 0.2 <= t < T1(7): e = "shockc" if not flap else "talk"
    elif T1(7) <= t < T0(9): e = "blush"
    elif T0(9) <= t < T1(9): e = "blushtalk" if flap else "blush"
    elif t >= T1(9): e = "blushsmile"
    else: e = "talk" if flap else "base"
    if (t % 3.1) < 0.17 and not talking and e in ("base", "blush", "sad"):
        e = "sadblink" if e == "sad" else "blink"
    reach = ease((t - T0(6) - 0.4) / 0.9) - ease((t - T1(8)) / 0.5)
    fist = ease((t - T0(5)) / 0.4) - ease((t - T1(5)) / 0.4)
    door_k = ease(t / 0.55)
    sw = math.sin(ph) if running else 0.0
    arms = {}
    for s, sx in (("L", -1), ("R", 1)):
        rest_h = Vector((0.15 * sx, -0.28 + 0.08 * sw * sx + 0.01 * math.sin(t * 1.3), -0.46 - 0.05 * abs(sw)))
        rest_e = Vector((0.24 * sx, -0.42, -0.24))
        if s == "R":
            push = (1 - door_k) * (1 if t < 0.6 else 0)                          # 扉を押し開ける右手
            rest_h = lerpv(rest_h, Vector((0.1, -0.05, -0.5)), push)
            hn = lerpv(rest_h, Vector((0.07, -0.15, -0.55)), reach); el = lerpv(rest_e, Vector((0.17, -0.32, -0.3)), reach)
        else:
            hn = lerpv(rest_h, Vector((-0.11, -0.12, -0.42)), fist); el = lerpv(rest_e, Vector((-0.22, -0.34, -0.28)), fist)
        arms[s] = (Vector((0.22 * sx, -0.55, 0.05)), el, hn)
    return pos, look, arms, yo_p, yrot, e, door_k

T.outlines(2.0)
frames = TEST or range(START, STOP)
t0 = time.time()
for f in frames:
    p = os.path.join(OUT, "%04d.png" % (f + 1))
    if os.path.exists(p) and not TEST: continue
    t = f / FPS
    pos, look, arms, yo_p, yrot, e, door_k = state(t)
    ROOF["door"].rotation_euler = (0, 0, math.radians(105) * door_k)
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
