"""
create_tsu1.py ― 『POV：津波警報が出た時、すぐ逃げる人と様子を見に行く人』の絵（上下2画面・8fps）
  上＝すぐ高台へ逃げる自分、下＝スマホを持って海へ様子を見に行く自分。海沿いの町、高台、津波避難ビル、押し寄せる波（流血・犠牲の描写はしない）
"""
import os, sys, math, json, time, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, bmesh
from mathutils import Vector
import s2_world as W, s3_toon as T
from s6_world import recolor

HERE = os.path.dirname(os.path.abspath(__file__))
arg = lambda k, d: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
SAMPLES = int(arg("--samples", "6")); FPS = 8; N = int(63.0 * FPS)
START = int(arg("--start", "0")); STOP = int(arg("--end", str(N)))
TEST = [int(x) for x in arg("--test", "").split(",") if x]
OUT = os.path.join(HERE, "frames_TSU1" + ("_test" if TEST else "")); os.makedirs(OUT, exist_ok=True)
LINES = json.load(open(os.path.join(HERE, "tsu1_lines.json"), encoding="utf-8"))
def T0(i): return LINES[i][0]
def T1(i): return LINES[i][1]

sc = W.reset(SAMPLES, res=(720, 640)); sc.view_settings.view_transform = "Standard"
def tm(n, c, s=None): return T.toon(n, c, s)
def box(n, loc, size, m, rot=(0, 0, 0)):
    o = W.box(n, loc, size, m, rot=rot); T.link(o); return o
grass = tm("grass", (0.5, 0.62, 0.45)); road = tm("road", (0.42, 0.43, 0.46)); sand = tm("sand", (0.86, 0.8, 0.64))
sea = tm("sea", (0.2, 0.42, 0.56), (0.12, 0.28, 0.42)); foam = tm("foam", (0.95, 0.97, 1.0), (0.75, 0.82, 0.9))
wallm = tm("wall", (0.74, 0.74, 0.72)); bldm = tm("bld", (0.86, 0.84, 0.8)); signm = tm("sign", (0.2, 0.7, 0.4))
# 地面・道・浜・海
box("land", (0, -30, -0.05), (240, 110, 0.1), grass)
box("road", (0, -10, 0.005), (5, 70, 0.01), road); box("road2", (0, 10, 0.005), (200, 4, 0.01), road)
box("beach", (0, 27, -0.15), (240, 10, 0.3), sand)
box("seawall", (0, 22, 0.6), (240, 0.8, 1.2), wallm)
box("sea", (0, 220, -0.25), (800, 380, 0.1), sea)
# 高台（y=-30 から坂、y=-60 で高さ14m）
me = bpy.data.meshes.new("hill"); bm = bmesh.new()
pts = [(-60, -30, 0), (60, -30, 0), (60, -60, 14), (-60, -60, 14), (-60, -120, 14), (60, -120, 14)]
v = [bm.verts.new(p) for p in pts]; bm.faces.new([v[0], v[1], v[2], v[3]]); bm.faces.new([v[3], v[2], v[5], v[4]])
bm.to_mesh(me); bm.free(); hill = bpy.data.objects.new("hill", me); bpy.context.collection.objects.link(hill); me.materials.append(grass)
box("hillroad", (2.5, -45, 7.02), (3.0, 33.5, 0.05), road, rot=(math.atan2(14, 30), 0, 0))
def hill_z(y): return 0.0 if y > -30 else (min(14.0, (-30 - y) * 14 / 30))
# 家並み
rnd = random.Random(7)
roofs = [tm("roof%d" % i, c) for i, c in enumerate([(0.55, 0.3, 0.28), (0.3, 0.38, 0.5), (0.35, 0.36, 0.38), (0.6, 0.5, 0.35)])]
walls = [tm("hw%d" % i, c) for i, c in enumerate([(0.92, 0.9, 0.84), (0.85, 0.82, 0.76), (0.78, 0.82, 0.86)])]
for x in range(-56, 57, 8):
    for y in range(-26, 19, 8):
        if abs(x) < 7 or (abs(x - 9) < 7 and abs(y - 12) < 7): continue
        h = rnd.uniform(3, 6.5); w = rnd.uniform(4.5, 6)
        box("house", (x + rnd.uniform(-0.8, 0.8), y, h / 2), (w, w, h), rnd.choice(walls))
        bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=w * 0.78, depth=2.2, location=(x, y, h + 1.1), rotation=(0, 0, math.pi / 4))
        bpy.context.object.data.materials.append(rnd.choice(roofs)); T.link(bpy.context.object)
# 津波避難ビル（外階段）
box("evac", (9, 12, 7.5), (8, 8, 15), bldm)
box("evac_sign", (4.95, 12, 9), (0.1, 3.2, 1.4), signm)
for k in range(10):
    box("stair", (13.6, 9 + (k % 2) * 6 * 0, 1.5 * k + 0.75), (1.4, 1.6, 0.1), wallm)
# 渋滞の車
carcols = [tm("car%d" % i, c) for i, c in enumerate([(0.85, 0.2, 0.2), (0.95, 0.95, 0.95), (0.2, 0.3, 0.6), (0.25, 0.25, 0.28), (0.9, 0.75, 0.2)])]
for k in range(9):
    y = -27 + k * 3.0; box("car", (-0.9, y, 0.7), (1.7, 2.6, 1.0), rnd.choice(carcols)); box("cartop", (-0.9, y - 0.2, 1.35), (1.5, 1.4, 0.5), carcols[3])
# 波（前の壁＋白い波頭）と、陸に上がった水
murk = tm("murk", (0.42, 0.4, 0.34), (0.3, 0.29, 0.25)); wavem = tm("wavem", (0.16, 0.3, 0.36), (0.1, 0.2, 0.26))
# 動かす物は原点で作る（W.box は位置をメッシュに焼き込むため）
wave = box("wave", (0, 0, 0), (400, 3, 4), wavem); crest = box("crest", (0, 0, 0), (400, 4.5, 1.6), foam)
flood = box("flood", (0, 0, 0), (400, 400, 0.2), murk); edge = box("edge", (0, 0, 0), (400, 2.0, 0.5), foam)
# 空（どんより）・光
W.sky_world(((0.72, 0.74, 0.78), (0.6, 0.62, 0.68), (0.42, 0.45, 0.52)), 1.0)
sun = bpy.data.lights.new("sun", "SUN"); sun.energy = 2.2; sun.angle = math.radians(8)
so = bpy.data.objects.new("sun", sun); bpy.context.collection.objects.link(so); so.location = (20, 30, 40); W.aim(so, (0, 0, 0))
# 叫ぶ人（陽太モデル）
yo, ytex = T.boy("stranger", (5, 20.4, 1.2), rot=170)
cam = W.camera((0, 0, 1.6), (0, 10, 1.5), lens=18, fstop=5.6)
skin = tm("me_skin", (1.0, 0.88, 0.8), (0.92, 0.72, 0.66)); sleeve = tm("me_sleeve", (0.35, 0.45, 0.62))
def piece(name, r, m):
    bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=r, depth=1.0); o = bpy.context.object; o.name = name
    o.data.materials.append(m); bpy.ops.object.shade_smooth(); o.parent = cam; T.link(o); return o
def ball(name, r, m):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8, radius=r); o = bpy.context.object; o.name = name
    o.scale = (0.85, 1.3, 0.8); o.data.materials.append(m); bpy.ops.object.shade_smooth(); o.parent = cam; T.link(o); return o
ARMS = {s: dict(up=piece("upper" + s, 0.05, sleeve), lo=piece("lower" + s, 0.045, sleeve), hd=ball("hand" + s, 0.04, skin)) for s in "LR"}
def between(o, p0, p1):
    p0, p1 = Vector(p0), Vector(p1); d = p1 - p0
    o.location = (p0 + p1) / 2; o.scale = (1, 1, max(d.length, 1e-3)); o.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
def set_arm(s, sh, el, hn):
    a = ARMS[s]; hn = Vector(hn); el = Vector(el)
    between(a["up"], sh, el); between(a["lo"], el, el + (hn - el) * 0.88)
    a["hd"].location = hn; a["hd"].rotation_euler = (hn - el).to_track_quat("Y", "Z").to_euler()
# スマホ（下の画面の人が持つ）
phm = tm("phone", (0.1, 0.1, 0.12)); ph = W.box("phone", (0, 0, 0), (0.075, 0.012, 0.15), phm); ph.parent = cam; T.link(ph)
scrm = W.mat("phscr", (0.2, 0.3, 0.4), 0.5, emit=(0.55, 0.7, 0.85), estr=2.0)
phs = W.box("phscr", (0, 0, 0), (0.066, 0.002, 0.135), scrm); phs.parent = ph; phs.location = (0, -0.007, 0)
recm = W.mat("rec", (1, 0.1, 0.1), 0.5, emit=(1, 0.1, 0.1), estr=6.0)
rec = W.box("rec", (0, 0, 0), (0.012, 0.002, 0.012), recm); rec.parent = ph; rec.location = (-0.022, -0.009, 0.055)

def ease(x): x = min(max(x, 0.0), 1.0); return x * x * (3 - 2 * x)
def lerpv(a, b, k): return Vector(a).lerp(Vector(b), k)
def path(t, pts):
    """[(時刻, (x,y,z))…] を時間で補間"""
    if t <= pts[0][0]: return Vector(pts[0][1])
    for (ta, a), (tb, b) in zip(pts, pts[1:]):
        if t <= tb: return lerpv(a, b, ease((t - ta) / (tb - ta)))
    return Vector(pts[-1][1])

QUAKE0, QUAKE1 = T0(1), T0(2) - 0.2
W1_0, W1_1, W1_2 = T0(6), 38.0, 45.0        # 1回目の波：水平線に出る→浜→町の奥
W2_0, W2_2 = T0(11), 56.0                  # 2回目（もっと大きい）
def wave_state(t):
    if t < W1_0: return 400.0, 0.0, -0.2
    if t < W2_0:
        if t < W1_1: y = 260 - (260 - 26) * ease((t - W1_0) / (W1_1 - W1_0)) ** 0.8; h = 9.0
        else: y = 26 - 54 * ease((t - W1_1) / (W1_2 - W1_1)); h = 7.0
        flood = 0.0 if y > 22 else 4.2 * min(1, (22 - y) / 10)
        return y, h, flood
    k = ease((t - W2_0) / (W2_2 - W2_0)); y = 260 - (260 + 30) * k; h = 11.0
    return y, h, 4.2 + (1.6 if y < 22 else 0) * min(1, (22 - y) / 10)

def pane(t, side):
    A = side == "A"
    run = 0.0
    if A:
        pos = path(t, [(T0(2) + 0.3, (0, 0, 0)), (T0(5) - 0.3, (2.5, -29, 0)), (33.0, (2.5, -58, 14)), (63, (2.5, -60, 14))])
        run = 1.0 if T0(2) + 0.3 < t < 33.0 else 0.0
        look = pos + Vector((0, -10, 1.5)) if t < 33.6 else Vector((0, 14, -2))
        if T0(5) - 1.0 < t < T1(5): look = pos + Vector((-4, -8, 0.5))             # 渋滞の車を横目に
        if t >= T0(12) + 0.5: k = ease((t - T0(12) - 0.5) / 3.0); pos = pos.lerp(Vector((2.5, -62, 40)), k); look = Vector((0, 0, 0)).lerp(Vector((0, 10, 0)), k)
    else:
        pos = path(t, [(T0(3), (0, 0, 0)), (T1(4), (1.5, 24.5, 0)), (36.3, (1.5, 24.5, 0)), (39.0, (8.0, 16.6, 0)), (39.8, (13.6, 15.5, 0)), (T1(9), (13.6, 9.5, 15)), (63, (13.6, 9.5, 15))])
        run = 1.0 if 36.3 < t < T1(9) else (0.35 if T0(3) < t < T1(4) else 0.0)
        look = pos + Vector((0, 10, 1.4))
        if T0(7) - 0.3 <= t < T1(7): look = Vector((5, 20.4, 2.8))                     # 叫ぶ人の方を見る
        if T1(7) <= t < 36.3: look = Vector((0, 120, 6))                                # 振り返ると、波
        if 36.3 <= t < T1(9): look = pos + Vector((4, -6, 1.2))
        if t >= T1(9): look = Vector((0, 4, 0.0))                                        # 屋上から水につかった町を見下ろす
        if t >= T0(12) + 0.5: k = ease((t - T0(12) - 0.5) / 3.0); pos = pos.lerp(Vector((10, -8, 40)), k); look = look.lerp(Vector((0, 10, 0)), k)
    z = (hill_z(pos.y) if pos.z < 14.5 and A else pos.z) if A else pos.z
    eye = Vector((pos.x, pos.y, (z if A else pos.z) + 1.6))
    ph_ = t * 2.6 * math.pi
    if run > 0: eye += Vector((0.03 * math.sin(ph_ * 0.5), 0, 0.05 * run * abs(math.sin(ph_))))
    if QUAKE0 <= t < QUAKE1:
        a = 0.06 * math.sin(math.pi * (t - QUAKE0) / (QUAKE1 - QUAKE0))
        eye += Vector((a * math.sin(t * 41), a * math.sin(t * 37), a * 0.5 * math.sin(t * 53)))
    return eye, look, run, (not A) and T0(3) <= t < 36.3

def place(t, side):
    eye, look, run, phone = pane(t, side)
    cam.location = eye; W.aim(cam, look)
    y, h, fl = wave_state(t)
    wave.location = (0, y, h / 2 - 0.2); wave.scale = (1, 1, max(h, 0.1) / 4)
    if y > 300: wave.location = (0, 2000, 0)
    crest.location = (0, y - 0.6, h); crest.scale = (1, 1, 1)
    flood.location = (0, y + 200, fl - 0.1); edge.location = (0, y - 1.0, fl + 0.1)
    for o in [yo] + list(yo.children_recursive): o.hide_render = not (side == "B" and T0(6) < t < 40)
    T.set_expr(ytex, "yota", "talk" if (T0(7) <= t < T1(7) and int(t * 8) % 3 != 2) else "shockc")
    ph.hide_render = not phone
    for c in ph.children: c.hide_render = not phone
    ph.location = (0.07, -0.12, -0.42); ph.rotation_euler = (math.radians(-80), 0, 0)
    sw = math.sin(t * 2.6 * math.pi) * run
    for s, sx in (("L", -1), ("R", 1)):
        hn = Vector((0.15 * sx, -0.34 + 0.1 * sw * sx, -0.45))
        if s == "R" and phone: hn = Vector((0.08, -0.2, -0.42))
        set_arm(s, Vector((0.22 * sx, -0.55, 0.05)), Vector((0.24 * sx, -0.46, -0.26)), hn)

T.outlines(1.6)
frames = TEST or range(START, STOP)
t0 = time.time()
for f in frames:
    p = os.path.join(OUT, "done_%04d.txt" % (f + 1))
    if os.path.exists(p) and not TEST: continue
    t = f / FPS
    for side in "AB":
        place(t, side)
        hp = os.path.join(OUT, "%s_%04d.png" % (side, f + 1)); tmp = hp[:-4] + "_tmp.png"
        sc.render.filepath = tmp; bpy.ops.render.render(write_still=True); os.replace(tmp, hp)
    open(p, "w").write("ok")
    print("frame %s t=%.2f %.1fs" % (p, t, time.time() - t0), flush=True); t0 = time.time()
