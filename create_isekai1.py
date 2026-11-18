"""
create_isekai1.py ― 『POV：異世界に召喚されたら、世界の終わりまで残り3分だった』パート1 の絵（12fps）
  自分＝召喚された女子高生（カメラ。画面下に制服の手）。騎士カイ（陽太モデル＋装備）が叫ぶ。空には落ちてくる巨大な月。
  python create_isekai1.py [--samples 8] [--start 0] [--end 336] [--test 0,60,...]
  口パクとタイミングは isk1_lines.json（make_reel_isekai1.py --voice で作る）に合わせる
"""
import os, sys, math, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
from mathutils import Vector
import s2_world as W, s3_toon as T, s5_world as A

HERE = os.path.dirname(os.path.abspath(__file__))
arg = lambda k, d: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
SAMPLES = int(arg("--samples", "8")); FPS = 12; N = int(28.0 * FPS)
START = int(arg("--start", "0")); STOP = int(arg("--end", str(N)))
TEST = [int(x) for x in arg("--test", "").split(",") if x]
OUT = os.path.join(HERE, "frames_ISK1" + ("_test" if TEST else "")); os.makedirs(OUT, exist_ok=True)
LINES = json.load(open(os.path.join(HERE, "isk1_lines.json"), encoding="utf-8"))
YSPANS = [(l[0], l[1]) for l in LINES if l[5] == "yota"]
def T0(i): return LINES[i][0]
def T1(i): return LINES[i][1]

sc = W.reset(SAMPLES); sc.view_settings.view_transform = "Standard"
S = A.apocalypse()
KN = Vector((0.3, -2.35, 0)); HEAD = 1.55
yo, ytex = T.boy("yota", tuple(KN), rot=180); A.knight_gear(yo)
CAM = Vector((0.0, -4.0, 1.42))
cam = W.camera(tuple(CAM), (0.3, -2.35, 1.5), lens=17, fstop=4.0)
S["hand_light"].parent = cam; S["hand_light"].location = (0, -0.12, -0.55)

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
def lerpv(a, b, k): return Vector(a).lerp(Vector(b), k)
def shake(t, amp):
    return Vector((amp * (math.sin(t * 37.0) + 0.6 * math.sin(t * 23.0 + 1.0)), 0, amp * (math.sin(t * 41.0 + 2.0) + 0.5 * math.sin(t * 19.0))))

FREEZE = T1(3) - 0.15                                   # 岩が止まる瞬間
STOPM = T0(8)                                           # 月に手をのばす
CRACK = 23.6
ROCK_F = CAM + Vector((-0.45, 2.7, 0.6))               # 岩が止まる位置（目の前）
ROCK_0 = Vector((-28, 60, 38))
MOON_HEAD = A.MOON_DIR * 300

def state(t):
    # 立ち上がる（最初は地面に座りこんでいる）
    stand = ease((t - 2.2) / 1.0)
    pos = CAM + Vector((0, 0, -0.85 * (1 - stand)))
    quake = 0.008 + 0.01 * ease((t - 7.6) / 0.5) * (1 - ease((t - FREEZE) / 0.2)) + 0.025 * ease((t - CRACK) / 0.2) * (1 - ease((t - CRACK - 1.2) / 1.0) * 0.6)
    quake *= 0.3 if FREEZE <= t < FREEZE + 0.8 else 1.0
    pos = pos + shake(t, quake)
    knee = Vector((KN.x, KN.y, HEAD - 0.02))
    moon_look = pos + (A.MOON_DIR * 380 - pos).normalized() * 10
    # どこを見るか：騎士 → 月 → 騎士 → 飛んでくる岩 → 止まった岩 → 騎士 → 月
    rk = ease((t - (FREEZE - 1.6)) / (1.6))                 # 岩の進み（加速）
    rk = min(1.0, max(0.0, (t - (FREEZE - 1.6)) / 1.6)) ** 2
    rock = ROCK_0.lerp(ROCK_F, rk) if t < FREEZE else ROCK_F.copy()
    if t < T0(0) - 0.1: rock = ROCK_0.copy()
    w_moon = ease((t - T0(1) - 0.2) / 0.7) - ease((t - T0(2) - 0.1) / 0.5) + ease((t - T0(6) - 0.2) / 0.7)
    w_rock = ease((t - (FREEZE - 1.0)) / 0.5) - ease((t - T0(5)) / 0.5)
    w_moon = min(1.0, max(0.0, w_moon)); w_rock = min(1.0, max(0.0, w_rock))
    look = knee.lerp(moon_look, w_moon)
    look = look.lerp(rock, w_rock)
    look.z += 0.25 * (1 - stand)
    look = look + shake(t + 1.3, quake * 2)
    # 月：近づいてくる → 止める（20.6〜23.6）→ ひび → また動きだす
    pull = 4.0 * min(t, STOPM + 0.4) + (max(0.0, t - CRACK) * 10.0)
    crack_k = ease((t - CRACK) / 0.5)
    moon_r = 125 + pull * 0.12
    # 魔法陣：岩のまわり（止まった瞬間〜）、月に手をのばすときは手の前に大きく
    rune_k = ease((t - FREEZE) / 0.25) * (1 - ease((t - STOPM) / 0.3))
    # 腕
    up_rock = ease((t - (FREEZE - 0.6)) / 0.45) * (1 - ease((t - T0(5) - 0.3) / 0.6))
    up_moon = ease((t - STOPM) / 0.5) * (1 - ease((t - CRACK - 1.0) / 0.8))
    arms = {}
    for s, sx in (("L", -1), ("R", 1)):
        rest_h = Vector((0.15 * sx, -0.28 + 0.01 * math.sin(t * 1.3), -0.46)); rest_e = Vector((0.24 * sx, -0.42, -0.24))
        hn = lerpv(rest_h, Vector((0.11 * sx, -0.08, -0.5)), up_rock); el = lerpv(rest_e, Vector((0.2 * sx, -0.25, -0.3)), up_rock)
        hn = lerpv(hn, Vector((0.12 * sx, 0.02, -0.5)), up_moon); el = lerpv(el, Vector((0.2 * sx, -0.2, -0.32)), up_moon)
        arms[s] = (Vector((0.22 * sx, -0.55, 0.05)), el, hn)
    glow = max(up_rock * (1 if t >= FREEZE - 0.15 else 0.3), up_moon * (1.6 if t < CRACK else 0.6))
    # 騎士の表情
    talking = any(st <= t <= en - 0.05 for st, en in YSPANS)
    flap = talking and (int(t * FPS) % 3 != 2)
    if t < T1(0): e = "talk" if flap else "shock"
    elif t < T0(3): e = "talk" if flap else "base"
    elif t < FREEZE: e = "talk" if flap else "shockc"
    elif t < T1(5) + 0.4: e = "talk" if flap else "shockc"
    elif t < CRACK: e = "talk" if flap else "shock"
    else: e = "talk" if flap else "shockc"
    if (t % 3.1) < 0.17 and not talking and e == "base": e = "blink"
    return pos, look, arms, e, rock, rune_k, moon_r, pull, crack_k, glow, up_moon

T.outlines(2.0)
frames = TEST or range(START, STOP)
t0 = time.time()
for f in frames:
    p = os.path.join(OUT, "%04d.png" % (f + 1))
    if os.path.exists(p) and not TEST: continue
    t = f / FPS
    pos, look, arms, e, rock, rune_k, moon_r, pull, crack_k, glow, up_moon = state(t)
    cam.location = pos; W.aim(cam, look)
    cam.data.dof.focus_distance = max(0.8, (look - pos).length if (look - pos).length < 6 else 30.0)
    for s, (sh, el, hn) in arms.items(): set_arm(s, sh, el, hn)
    T.set_expr(ytex, "yota", e)
    rune_pos = rock if up_moon < 0.05 else (pos + (look - pos).normalized() * 0.9)
    A.update(t, S, pos, moon_r, pull, crack_k, rune_k if up_moon < 0.05 else up_moon * (1 - crack_k) * 0.6, tuple(rock), None)
    for o in S["rune"]: o.location = tuple(rune_pos)
    S["hand_light"].data.energy = 25.0 * glow
    tmp = p[:-4] + "_tmp.png"
    sc.render.filepath = tmp
    bpy.ops.render.render(write_still=True)
    os.replace(tmp, p)
    print("frame %s t=%.2f %s %.1fs" % (p, t, e, time.time() - t0), flush=True); t0 = time.time()
