"""
create_hana1.py ― 『POV：異世界で目を覚ましたら、昔飼っていた犬が女の子になって待っていた』パート1 の絵（12fps）
  自分＝男（カメラ。画面下にグレーのパーカーの手）。ハナ（柴犬の耳・赤いリボン）。夕暮れの花畑、二つの月、影の魔物。
  python create_hana1.py [--samples 8] [--start 0] [--end 336] [--test 0,60,...]
"""
import os, sys, math, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
from mathutils import Vector
import s2_world as W, s3_toon as T, s6_world as M

HERE = os.path.dirname(os.path.abspath(__file__))
arg = lambda k, d: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
SAMPLES = int(arg("--samples", "8")); FPS = 12; N = int(28.0 * FPS)
START = int(arg("--start", "0")); STOP = int(arg("--end", str(N)))
TEST = [int(x) for x in arg("--test", "").split(",") if x]
OUT = os.path.join(HERE, "frames_HANA1" + ("_test" if TEST else "")); os.makedirs(OUT, exist_ok=True)
LINES = json.load(open(os.path.join(HERE, "hana1_lines.json"), encoding="utf-8"))
HSPANS = [(l[0], l[1]) for l in LINES if l[5] == "hana"]
def T0(i): return LINES[i][0]
def T1(i): return LINES[i][1]

sc = W.reset(SAMPLES); sc.view_settings.view_transform = "Standard"
S = M.meadow()
EYE = 1.62
C0 = Vector((0, 0, EYE))
h1, tex1 = M.hana((0.12, 1.15, 0), rot=180)
h2, tex2 = M.hana((0.35, 1.1, 0), rot=0, pull=True)
def show(o, v):
    for c in [o] + list(o.children_recursive):
        c.hide_render = not v
cam = W.camera(tuple(C0), (0.12, 1.15, 1.42), lens=17, fstop=2.8)
glow = bpy.data.lights.new("hanaglow", "POINT"); glow.color = (1.0, 0.85, 0.5); glow.energy = 0.0
gl = bpy.data.objects.new("hanaglow", glow); bpy.context.collection.objects.link(gl)

# 自分の腕（グレーのパーカー）
skin = T.toon("me_skin", (1.0, 0.88, 0.8), (0.92, 0.72, 0.66))
hood = T.toon("me_hoodie", (0.52, 0.53, 0.56), (0.36, 0.37, 0.42))
cuff = T.toon("me_cuff", (0.44, 0.45, 0.48))
def piece(name, r, m):
    bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=r, depth=1.0); o = bpy.context.object; o.name = name
    o.data.materials.append(m); bpy.ops.object.shade_smooth(); o.parent = cam; T.link(o); return o
def ball(name, r, m):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8, radius=r); o = bpy.context.object; o.name = name
    o.scale = (0.85, 1.3, 0.8); o.data.materials.append(m); bpy.ops.object.shade_smooth(); o.parent = cam; T.link(o); return o
ARMS = {s: dict(up=piece("upper" + s, 0.055, hood), lo=piece("lower" + s, 0.05, hood), cf=piece("cuff" + s, 0.05, cuff), hd=ball("hand" + s, 0.04, skin))
        for s in "LR"}
def between(o, p0, p1):
    p0, p1 = Vector(p0), Vector(p1); d = p1 - p0
    o.location = (p0 + p1) / 2; o.scale = (1, 1, max(d.length, 1e-3))
    o.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
def set_arm(s, sh, el, hn):
    a = ARMS[s]; hn = Vector(hn); el = Vector(el)
    between(a["up"], sh, el); between(a["lo"], el, el + (hn - el) * 0.86); between(a["cf"], el + (hn - el) * 0.8, el + (hn - el) * 0.92)
    a["hd"].location = hn; a["hd"].rotation_euler = (hn - el).to_track_quat("Y", "Z").to_euler()

def ease(x): x = min(max(x, 0.0), 1.0); return x * x * (3 - 2 * x)
def lerpv(a, b, k): return Vector(a).lerp(Vector(b), k)

ROAR = T0(2) - 0.9                      # 魔物が出る
RUN0 = T0(2) + 0.5; RUN1 = T0(4) - 0.2  # 走る
STOPY = 17.0
WOLF = Vector((0, -18, 8.2))

def state(t):
    run = ease((t - RUN0) / (RUN1 - RUN0))
    running = RUN0 < t < RUN1
    ph = t * 2.7 * math.pi
    y = STOPY * run
    pos = Vector((0, y, EYE)) + Vector((0, 0.08 * ease(t / 5.0), 0))
    if running: pos += Vector((0.03 * math.sin(ph * 0.5), 0, 0.05 * abs(math.sin(ph)) - 0.025))
    huff = max(0.0, 1 - (t - RUN1) / 3.5) if t > RUN1 else 0.0
    pos += Vector((0, 0, 0.022 * huff * math.sin(t * 8.0)))
    pos += Vector((0, 0.1, 0)) * ease((t - T0(6)) / 1.0)
    # ハナの位置（はじめ：正面／走る：右前で手を引く／止まって：正面）
    pulling = T0(2) + 0.2 <= t < RUN1 + 0.25
    if not pulling:
        base_y = 0 if t < RUN0 else STOPY
        hp = Vector((0.12, base_y + 1.15, 0)) + (Vector((0, -0.1, 0)) * ease((t - T0(7) - 0.5) / 0.8) if t > RUN0 else Vector())
        hrot = 180
    else:
        hp = Vector((0.3, y + 1.55, 0.04 * abs(math.sin(ph + 0.6)) if running else 0)); hrot = 0
    face = Vector((hp.x, hp.y, 1.42 + hp.z))
    look = face.copy()
    # 魔物の方へ振り向く → 前へ
    back = ease((t - ROAR) / 0.35) - ease((t - T0(2) - 0.05) / 0.35)
    wolf_look = pos + (WOLF - pos).normalized() * 10
    if back > 0: look = look.lerp(wolf_look, back) + Vector((0.6 * math.sin(back * math.pi), 0, 0))
    if pulling:
        ahead = Vector((0.15, pos.y + 6, EYE - 0.55))
        look = look.lerp(ahead, ease((t - T0(2) - 0.1) / 0.35)) if t < RUN0 + 0.4 else ahead
        if running: look += Vector((0.25 * math.sin(ph * 0.5), 0, 0.06 * math.sin(ph)))
    # 気持ちの視線：リボンを見る／消えかける手を見下ろす
    ribbon = ease((t - T0(6)) / 0.5) * (1 - ease((t - T1(6)) / 0.5))
    look += Vector((0.05, 0, 0.1)) * ribbon
    down = ease((t - T0(8) + 0.2) / 0.5) * (1 - ease((t - T1(8) - 0.2) / 0.6))
    look += Vector((-0.08, 0, -0.3)) * down
    look += Vector((0, 0, 0.012 * math.sin(t * 1.3)))
    # 自分の腕：走る間は右手で手をつながれる（座標はあとでハナの手に合わせる）
    sw = math.sin(ph) if running else 0.0
    arms = {}
    for s, sx in (("L", -1), ("R", 1)):
        arms[s] = (Vector((0.22 * sx, -0.55, 0.05)), Vector((0.25 * sx, -0.44, -0.24)),
                   Vector((0.15 * sx, -0.3 + 0.09 * sw * sx + 0.01 * math.sin(t * 1.3), -0.46 - 0.05 * abs(sw))))
    # 表情
    talking = any(st <= t <= en - 0.05 for st, en in HSPANS)
    flap = talking and (int(t * FPS) % 3 != 2)
    if t < T0(2) - 1.0: e = "tearsmiletalk" if flap else "tearsmile"
    elif t < RUN1 + 0.3: e = "talk" if flap else "shockc"
    elif t < T0(5): e = "base"
    elif t < T1(7) + 0.3: e = "tearsmiletalk" if flap else "tearsmile"
    else: e = "tearsadtalk" if flap else "tearsad"
    if (t % 3.3) < 0.17 and not talking and e in ("tearsad", "base"): e = "tearblink" if e == "tearsad" else "blink"
    fade = ease((t - T0(8) + 0.3) / 1.0)
    return pos, look, arms, hp, hrot, pulling, e, back, fade

T.outlines(2.0)
frames = TEST or range(START, STOP)
t0 = time.time()
for f in frames:
    p = os.path.join(OUT, "%04d.png" % (f + 1))
    if os.path.exists(p) and not TEST: continue
    t = f / FPS
    pos, look, arms, hp, hrot, pulling, e, back, fade = state(t)
    cam.location = pos; W.aim(cam, look)
    S["wolf"].location = (0, -18, -13 + 13 * ease((t - ROAR + 0.6) / 0.8))
    show(h1, not pulling); show(h2, pulling)
    hobj, tex = (h2, tex2) if pulling else (h1, tex1)
    hobj.location = hp; hobj.rotation_euler = (0, 0, math.radians(hrot))
    T.set_expr(tex, "mei", e)
    bpy.context.view_layer.update()
    if pulling:                                                   # ハナの右手（ワールド）→ 自分の右手（カメラ座標）
        hw = hobj.matrix_world @ Vector((-0.22, -0.42, 1.0))
        hc = cam.matrix_world.inverted() @ hw
        sh, el, _ = arms["R"]
        k = ease((t - T0(2) - 0.15) / 0.3)
        arms["R"] = (sh, el.lerp(Vector((0.18, -0.3, -0.35)), k), _.lerp(hc + Vector((0.02, -0.03, 0.03)), k))
    for s, (sh, el, hn) in arms.items(): set_arm(s, sh, el, hn)
    cam.data.dof.focus_distance = max(0.6, (Vector((hp.x, hp.y, 1.42)) - pos).length) if back < 0.5 else 25.0
    M.update(t, S)
    # 消えかけるハナ：手のまわりから光の粒が立ちのぼる
    hand_w = (h1.matrix_world @ Vector((0.2, 0.05, 0.8))) if not pulling else Vector()
    for i, sp in enumerate(S["sparks"]):
        a = sp["ph"] + t * 1.5; z = ((t * sp["v"] + sp["ph"]) % 1.2)
        side = -1 if i % 2 else 1
        c = (h1.matrix_world @ Vector((0.2 * side, 0.05, 0.8)))
        sp["o"].location = c + Vector((sp["r"] * math.cos(a), sp["r"] * math.sin(a), z * 0.9))
        sp["o"].scale = (fade * (1 - z / 1.2) + 1e-4,) * 3
    gl.location = Vector((hp.x, hp.y - 0.25, 1.0)); glow.energy = 20.0 * fade
    tmp = p[:-4] + "_tmp.png"
    sc.render.filepath = tmp
    bpy.ops.render.render(write_still=True)
    os.replace(tmp, p)
    print("frame %s t=%.2f %s %.1fs" % (p, t, e, time.time() - t0), flush=True); t0 = time.time()
