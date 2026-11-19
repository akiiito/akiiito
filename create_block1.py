"""
create_block1.py ― 『POV：全部がブロックの世界で目覚めたら、夜まで残り3分だった』パート1 の絵（12fps）
  オリジナルのブロック世界。自分＝男（グレーのパーカーの手）、ルカ＝この世界の少女。木を叩く→チート能力で家が一瞬で建つ→夜、影ブロックの群れ
"""
import os, sys, math, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
from mathutils import Vector
import s2_world as W, s3_toon as T, s7_world as B
from s6_world import recolor

HERE = os.path.dirname(os.path.abspath(__file__))
arg = lambda k, d: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
SAMPLES = int(arg("--samples", "8")); FPS = 12; N = int(28.0 * FPS)
START = int(arg("--start", "0")); STOP = int(arg("--end", str(N)))
TEST = [int(x) for x in arg("--test", "").split(",") if x]
OUT = os.path.join(HERE, "frames_BLK1" + ("_test" if TEST else "")); os.makedirs(OUT, exist_ok=True)
LINES = json.load(open(os.path.join(HERE, "blk1_lines.json"), encoding="utf-8"))
RSPANS = [(l[0], l[1]) for l in LINES if l[5] == "ruka"]
def T0(i): return LINES[i][0]
def T1(i): return LINES[i][1]

sc = W.reset(SAMPLES); sc.view_settings.view_transform = "Standard"
S = B.world()
EYE = 1.62
P0 = Vector((0.0, 0.5, 0))
RK = Vector((0.6, 1.55, 0))
ruka, rtex = T.girl("ruka", tuple(RK), rot=200, hair=(0.3, 0.2, 0.16), face="mei", ponytail=True)
recolor("ruka_blazer", (0.36, 0.56, 0.42)); recolor("ruka_skirt", (0.52, 0.38, 0.26)); recolor("ruka_sock", (0.4, 0.28, 0.2))
cam = W.camera((0, 0.5, EYE), (0.85, 1.9, 1.4), lens=17, fstop=4.0)
S["hand_light"].parent = cam; S["hand_light"].location = (0.12, -0.25, -0.45)

skin = T.toon("me_skin", (1.0, 0.88, 0.8), (0.92, 0.72, 0.66))
hood = T.toon("me_hoodie", (0.52, 0.53, 0.56), (0.36, 0.37, 0.42))
cuff = T.toon("me_cuff", (0.44, 0.45, 0.48))
def piece(name, r, m):
    bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=r, depth=1.0); o = bpy.context.object; o.name = name
    o.data.materials.append(m); bpy.ops.object.shade_smooth(); o.parent = cam; T.link(o); return o
def ball(name, r, m):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8, radius=r); o = bpy.context.object; o.name = name
    o.scale = (0.85, 1.3, 0.8); o.data.materials.append(m); bpy.ops.object.shade_smooth(); o.parent = cam; T.link(o); return o
ARMS = {s: dict(up=piece("upper" + s, 0.055, hood), lo=piece("lower" + s, 0.05, hood), cf=piece("cuff" + s, 0.05, cuff), hd=ball("hand" + s, 0.042, skin))
        for s in "LR"}
def between(o, p0, p1):
    p0, p1 = Vector(p0), Vector(p1); d = p1 - p0
    o.location = (p0 + p1) / 2; o.scale = (1, 1, max(d.length, 1e-3))
    o.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
def set_arm(s, sh, el, hn):
    a = ARMS[s]; hn = Vector(hn); el = Vector(el)
    between(a["up"], sh, el); between(a["lo"], el, el + (hn - el) * 0.86); between(a["cf"], el + (hn - el) * 0.8, el + (hn - el) * 0.92)
    a["hd"].location = hn; a["hd"].rotation_euler = (hn - el).to_track_quat("Y", "Z").to_euler()
hand_glow = T.toon("me_skin_glow", (0.75, 0.95, 1.0))

def ease(x): x = min(max(x, 0.0), 1.0); return x * x * (3 - 2 * x)
def lerpv(a, b, k): return Vector(a).lerp(Vector(b), k)

PUNCHES = [7.4, 8.15, 8.9, 9.6]          # 4回目で取れる
POP = PUNCHES[-1] + 0.05
BUILD0, BUILD1 = 13.9, 15.6              # 家が組み上がる
NIGHT0 = 18.6                            # 日が沈みきる
MOBS = T0(5) + 0.4                       # 影ブロックが湧く
PB = Vector(B.PUNCH) + Vector((0.5, 0.5, 0.5))
HUTC = Vector((4.0, 5.0, 1.6))
WEST = Vector((0, 26, 3.5))

def state(t):
    stand = ease((t - 1.4) / 1.4)
    pos = Vector((P0.x, P0.y, 0.95 + (EYE - 0.95) * stand))
    face = Vector((RK.x, RK.y, 1.42))
    # 見る先：ルカ → 見回す → 木 → 手 → 家 → ルカ → 西（影ブロック）→ ルカ → 西
    look = face.copy()
    look.z += 0.1 * (1 - stand)
    around = ease((t - T0(1)) / 0.8) * (1 - ease((t - T1(1) + 0.2) / 0.6))
    look = look.lerp(pos + Vector((-6 * math.cos(t * 0.9), 6, 1.2)), around)
    w_tree = ease((t - 6.3) / 0.6) * (1 - ease((t - BUILD0 + 0.5) / 0.6))
    look = look.lerp(PB + Vector((0, 0, -0.05)), w_tree)
    w_hand = ease((t - T0(3) - 0.3) / 0.5) * (1 - ease((t - BUILD0 + 0.4) / 0.5))
    look = look.lerp(look + Vector((0, 0, -0.15)), w_hand)
    w_hut = ease((t - BUILD0 + 0.4) / 0.5) * (1 - ease((t - T0(4) - 0.3) / 0.6))
    look = look.lerp(HUTC, w_hut)
    w_west = ease((t - T0(5) - 0.2) / 0.7) * (1 - ease((t - T0(7)) / 0.5)) + ease((t - T1(7) + 0.2) / 0.6)
    look = look.lerp(WEST, min(1, w_west))
    # 叩く：右手を前へ素早く突き出す
    jab = 0.0
    for p in PUNCHES:
        x = (t - p) / 0.22
        if 0 <= x <= 1: jab = max(jab, math.sin(x * math.pi))
    shake = Vector((0.004 * math.sin(t * 60), 0, 0.004 * math.cos(t * 55))) * jab
    pos += shake
    # 手を光らせて家を建てる：右手を前にかざす
    cast = ease((t - T0(3) - 0.2) / 0.5) * (1 - ease((t - BUILD1 - 0.4) / 0.6))
    arms = {}
    for s, sx in (("L", -1), ("R", 1)):
        sh = Vector((0.22 * sx, -0.55, 0.05)); el = Vector((0.25 * sx, -0.44, -0.24)); hn = Vector((0.15 * sx, -0.3 + 0.01 * math.sin(t * 1.3), -0.46))
        if s == "R":
            ready = ease((t - 6.6) / 0.4) * (1 - ease((t - POP - 0.3) / 0.4))
            hn = hn.lerp(Vector((0.12, -0.22, -0.42)), ready).lerp(Vector((0.03, -0.1, -0.62)), jab)
            el = el.lerp(Vector((0.2, -0.36, -0.3)), ready).lerp(Vector((0.12, -0.25, -0.38)), jab)
            hn = hn.lerp(Vector((0.04, -0.06, -0.42)), cast); el = el.lerp(Vector((0.16, -0.28, -0.3)), cast)
        arms[s] = (sh, el, hn)
    # ルカ：はじめはこちら、影ブロックが来たら西を向く
    turn = ease((t - T0(5)) / 0.6) * (1 - ease((t - T0(7) + 0.2) / 0.5))
    to_me = Vector((pos.x - RK.x, pos.y - RK.y, 0)).normalized()
    rot_me = math.degrees(math.atan2(-to_me.x, to_me.y))
    rrot = rot_me + (0 - rot_me) * turn
    talking = any(st <= t <= en - 0.05 for st, en in RSPANS)
    flap = talking and (int(t * FPS) % 3 != 2)
    if t < T1(2): e = "talk" if flap else "shockc"
    elif t < T0(4): e = "smiletalk" if flap else "smile"
    elif t < T1(4): e = "talk" if flap else "shock"
    elif t < T0(7): e = "talk" if flap else "shockc"
    else: e = "talk" if flap else "base"
    if (t % 3.2) < 0.17 and not talking and e in ("base", "smile"): e = "blink"
    night = ease((t - 15.5) / (NIGHT0 + 6.0 - 15.5))
    sun_elev = 9.0 - 13.0 * ease((t - 2.0) / (NIGHT0 - 2.0))
    mob_k = max(0.0, t - MOBS)
    return pos, look, arms, rrot, e, night, sun_elev, mob_k, cast

T.outlines(2.0)
frames = TEST or range(START, STOP)
t0 = time.time()
for f in frames:
    p = os.path.join(OUT, "%04d.png" % (f + 1))
    if os.path.exists(p) and not TEST: continue
    t = f / FPS
    pos, look, arms, rrot, e, night, sun_elev, mob_k, cast = state(t)
    cam.location = pos; W.aim(cam, look)
    cam.data.dof.focus_distance = max(0.8, min(30.0, (look - pos).length))
    for s, (sh, el, hn) in arms.items(): set_arm(s, sh, el, hn)
    ruka.rotation_euler = (0, 0, math.radians(rrot)); T.set_expr(rtex, "mei", e)
    # 叩くブロック：ひび3段階 → ポンと取れて手の中へ
    hits = sum(1 for q in PUNCHES if t >= q)
    for i, c in enumerate(S["cracks"]): c.hide_render = not (i < hits and t < POP)
    pb = S["punch"]
    if t < POP: pb.location = B.PUNCH; pb.scale = (1, 1, 1)
    else:
        k = ease((t - POP) / 0.45)
        bpy.context.view_layer.update()
        dst = cam.matrix_world @ Vector((0.14, -0.3, -0.6))
        c0 = Vector(B.PUNCH) + Vector((0.5, 0.5, 0.5))
        c = c0.lerp(dst, k) + Vector((0, 0, 0.4 * math.sin(k * math.pi)))
        sz = 1.0 - 0.75 * k if k < 1 else 0.0
        pb.scale = (max(sz, 1e-4),) * 3; pb.location = c - Vector((0.5, 0.5, 0.5)) * pb.scale[0]
        pb.rotation_euler = (k * 3, k * 2, 0)
        if t > POP + 0.6: pb.hide_render = True
    # 家：手から1つずつ飛んで組み上がる
    bpy.context.view_layer.update()
    src = cam.matrix_world @ Vector((0.08, -0.1, -0.6))
    n = len(S["hut"])
    for i, h in enumerate(S["hut"]):
        st = BUILD0 + (BUILD1 - BUILD0 - 0.45) * i / n
        k = ease((t - st) / 0.45)
        o = h["o"]
        if k <= 0: o.hide_render = True; continue
        o.hide_render = False
        c = src.lerp(h["target"] + Vector((0.5, 0.5, 0.5)), k) + Vector((0, 0, 1.2 * math.sin(k * math.pi)))
        sz = 0.3 + 0.7 * k
        o.scale = (sz,) * 3; o.location = c - Vector((0.5, 0.5, 0.5)) * sz
        o.rotation_euler = ((1 - k) * 4, (1 - k) * 3, 0)
    for s in "LR": ARMS[s]["hd"].data.materials[0] = hand_glow if cast > 0.3 else skin
    S["hand_light"].data.energy = 30.0 * cast
    B.update(t, S, night, sun_elev, mob_k)
    tmp = p[:-4] + "_tmp.png"
    sc.render.filepath = tmp
    bpy.ops.render.render(write_still=True)
    os.replace(tmp, p)
    print("frame %s t=%.2f %s %.1fs" % (p, t, e, time.time() - t0), flush=True); t0 = time.time()
