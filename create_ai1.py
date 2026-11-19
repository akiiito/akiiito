"""
create_ai1.py ― 『POV：AIを使う人と使わない人、5年後の末路』の絵（上下2画面・8fps）
  上＝AIを使う自分、下＝使わない自分。同じ机・同じ会社を一人称で。1コマごとに上と下を描いて1枚(720x1280)にまとめる
  python create_ai1.py [--samples 6] [--start 0] [--end 512] [--test 0,40,...]
"""
import os, sys, math, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
from mathutils import Vector
import s2_world as W, s3_toon as T
from s6_world import recolor

HERE = os.path.dirname(os.path.abspath(__file__))
arg = lambda k, d: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
SAMPLES = int(arg("--samples", "6")); FPS = 8; N = int(64.0 * FPS)
START = int(arg("--start", "0")); STOP = int(arg("--end", str(N)))
TEST = [int(x) for x in arg("--test", "").split(",") if x]
OUT = os.path.join(HERE, "frames_AI1" + ("_test" if TEST else "")); os.makedirs(OUT, exist_ok=True)
LINES = json.load(open(os.path.join(HERE, "ai1_lines.json"), encoding="utf-8"))
def T0(i): return LINES[i][0]
def T1(i): return LINES[i][1]

sc = W.reset(SAMPLES, res=(720, 640)); sc.view_settings.view_transform = "Standard"
def tm(name, base, shade=None): return T.toon(name, base, shade)
# ---- オフィス
floor = tm("of_floor", (0.5, 0.52, 0.58)); wall = tm("of_wall", (0.9, 0.9, 0.88)); deskm = tm("of_desk", (0.86, 0.78, 0.66))
dark = tm("of_dark", (0.18, 0.19, 0.22)); part = tm("of_part", (0.62, 0.7, 0.78)); mugm = tm("of_mug", (0.95, 0.5, 0.35))
def box(n, loc, size, m): o = W.box(n, loc, size, m); T.link(o); return o
box("floor", (0, 0, -0.05), (14, 14, 0.1), floor)
box("backwall_l", (-4.3, 2.6, 1.5), (5.4, 0.1, 3.0), wall); box("backwall_r", (4.3, 2.6, 1.5), (5.4, 0.1, 3.0), wall)
box("backwall_b", (0, 2.6, 0.35), (3.2, 0.1, 0.7), wall); box("backwall_t", (0, 2.6, 2.85), (3.2, 0.1, 0.3), wall)
box("ceiling", (0, 0, 3.05), (14, 14, 0.1), wall)
box("desk", (0, 0.05, 0.72), (1.6, 0.8, 0.05), deskm)
for x in (-0.75, 0.75): box("leg", (x, 0.05, 0.36), (0.05, 0.7, 0.72), dark)
box("partition", (0, 0.5, 1.0), (1.8, 0.04, 0.6), part)
for x in (-2.4, 2.4):                                                # となりの席
    box("desk2", (x, 0.05, 0.72), (1.6, 0.8, 0.05), deskm); box("mon2", (x, 0.25, 1.02), (0.55, 0.04, 0.34), dark)
box("monitor", (0, 0.25, 1.05), (0.66, 0.04, 0.42), dark); box("stand", (0, 0.28, 0.82), (0.08, 0.06, 0.2), dark)
box("keyboard", (0, -0.05, 0.752), (0.42, 0.13, 0.012), tm("of_kb", (0.82, 0.84, 0.88)))
W.cyl("mug", (0.5, -0.05, 0.8), 0.045, 0.11, mugm); T.link(bpy.data.objects["mug"])
# 画面（画像を差し替える）
scr_mat = bpy.data.materials.new("screen"); scr_mat.use_nodes = True; nt = scr_mat.node_tree; nt.nodes.clear()
o_ = nt.nodes.new("ShaderNodeOutputMaterial"); em = nt.nodes.new("ShaderNodeEmission"); tx = nt.nodes.new("ShaderNodeTexImage")
nt.links.new(tx.outputs["Color"], em.inputs["Color"]); nt.links.new(em.outputs[0], o_.inputs["Surface"]); em.inputs["Strength"].default_value = 1.0
SCR = {}
for fn in os.listdir(os.path.join(HERE, "ai_screens")):
    SCR[fn[:-4]] = bpy.data.images.load(os.path.join(HERE, "ai_screens", fn))
bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0.228, 1.05), rotation=(math.pi / 2, 0, 0)); scr = bpy.context.object
scr.scale = (0.62, 0.3875, 1); scr.data.materials.append(scr_mat); scr.visible_shadow = False
# 窓の外の街（空の色で朝・夕方・夜を切り替える）
city = tm("of_city", (0.55, 0.6, 0.72), (0.4, 0.44, 0.58)); win = W.mat("of_win", (1.0, 0.9, 0.6), 0.5, emit=(1.0, 0.85, 0.5), estr=0.0)
import random
rnd = random.Random(4)
for k in range(30):
    h = rnd.uniform(4, 22); x = rnd.uniform(-30, 30); y = rnd.uniform(25, 60)
    box("bld", (x, y, h / 2 - 8), (rnd.uniform(4, 9), rnd.uniform(4, 9), h), city)
    W.box("bw", (x, y - 4.6, h / 2 - 8), (2.2, 0.1, h * 0.7), win)
W.sky_world(((0.85, 0.9, 1.0), (0.7, 0.8, 0.95), (0.35, 0.55, 0.9)), 1.0)
sun_l = bpy.data.lights.new("sun", "SUN"); sun_l.energy = 3.0; sun_l.angle = math.radians(3)
so = bpy.data.objects.new("sun", sun_l); bpy.context.collection.objects.link(so); so.location = (0, 20, 10); W.aim(so, (0, 0, 0))
ceil_l = bpy.data.lights.new("ceil", "AREA"); ceil_l.size = 3; ceil_l.energy = 300
co = bpy.data.objects.new("ceil", ceil_l); bpy.context.collection.objects.link(co); co.location = (0, -0.5, 2.9); W.aim(co, (0, -0.5, 0))
TOD = {"day": (((0.85, 0.9, 1.0), (0.7, 0.8, 0.95), (0.35, 0.55, 0.9)), 1.0, 3.0, (1, 0.97, 0.92), 300, 0.0),
       "eve": (((1.0, 0.55, 0.3), (0.9, 0.5, 0.5), (0.3, 0.3, 0.6)), 1.0, 2.5, (1, 0.6, 0.4), 160, 1.5),
       "night": (((0.05, 0.06, 0.14), (0.03, 0.03, 0.09), (0.01, 0.01, 0.04)), 0.6, 0.0, (1, 1, 1), 40, 4.0)}
def set_tod(k):
    sky, st, se, sc_, cl, we = TOD[k]
    ramp = [n for n in bpy.context.scene.world.node_tree.nodes if n.type == "VALTORGB"][0]
    for e, c in zip(sorted(ramp.color_ramp.elements, key=lambda e: e.position), sky): e.color = c + (1,)
    bpy.context.scene.world.node_tree.nodes["Background"].inputs["Strength"].default_value = st
    sun_l.energy = se; sun_l.color = sc_; ceil_l.energy = cl
    win.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].default_value = we
# 同僚（陽太モデル＋ワイシャツ・ネクタイ風）
yo, ytex = T.boy("cowork", (1.05, 0.35, 0), rot=140)
recolor("cowork_blazer", (0.95, 0.95, 0.97)); recolor("cowork_pants", (0.25, 0.27, 0.34))
cam = W.camera((0, -0.75, 1.2), (0, 0.25, 1.05), lens=18, fstop=4.0)
# 自分の腕（ワイシャツ）
skin = tm("me_skin", (1.0, 0.88, 0.8), (0.92, 0.72, 0.66)); shirt = tm("me_shirt", (0.95, 0.96, 0.98), (0.75, 0.78, 0.86))
def piece(name, r, m):
    bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=r, depth=1.0); o = bpy.context.object; o.name = name
    o.data.materials.append(m); bpy.ops.object.shade_smooth(); o.parent = cam; T.link(o); return o
def ball(name, r, m):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8, radius=r); o = bpy.context.object; o.name = name
    o.scale = (0.85, 1.3, 0.8); o.data.materials.append(m); bpy.ops.object.shade_smooth(); o.parent = cam; T.link(o); return o
ARMS = {s: dict(up=piece("upper" + s, 0.05, shirt), lo=piece("lower" + s, 0.045, shirt), hd=ball("hand" + s, 0.04, skin)) for s in "LR"}
def between(o, p0, p1):
    p0, p1 = Vector(p0), Vector(p1); d = p1 - p0
    o.location = (p0 + p1) / 2; o.scale = (1, 1, max(d.length, 1e-3)); o.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
def set_arm(s, sh, el, hn):
    a = ARMS[s]; hn = Vector(hn); el = Vector(el)
    between(a["up"], sh, el); between(a["lo"], el, el + (hn - el) * 0.88)
    a["hd"].location = hn; a["hd"].rotation_euler = (hn - el).to_track_quat("Y", "Z").to_euler()

def ease(x): x = min(max(x, 0.0), 1.0); return x * x * (3 - 2 * x)
def win_(t, a, b): return a <= t < b

def pane(t, side):
    """side 'A'＝使う人 / 'B'＝使わない人 → (画面, 時間帯, タイピング量, 同僚の有無と表情, 視線の種類, 俯瞰の量)"""
    A = side == "A"
    scr_, tod, typing, cw, look, rise = "login", "day", 0.0, None, "screen", 0.0
    if t >= T0(1) - 0.3:
        if A:
            k = min(3, 1 + int((t - T0(1)) / 1.4)); scr_ = "ai_mail%d" % k; typing = 0.25 if t < T0(1) + 1.5 else 0.0
        else:
            k = min(3, 1 + int((t - T0(1)) / 3.0)); scr_ = "hand_mail%d" % k; typing = 1.0
    if t >= T0(3):
        if A: scr_, tod, look, typing = "blank", "eve", "window", 0.0
        else: scr_, tod, typing = "hand_mail3", "night", 1.0
    if t >= T0(4):
        tod = "day"; look = "screen"
        if A: scr_ = "learn1" if t < T0(5) + 1.5 else "learn2"; typing = 0.6
        else: scr_ = "sheet1"; typing = 0.8
    if t >= T0(6):
        typing = 0.0
        if A: scr_ = "error"
        else: scr_ = "sheet2"
    if T0(7) - 0.4 <= t < T1(8) + 0.3:
        if A: cw = "coldtalk" if win_(t, T0(7), T1(7) - 0.05) and int(t * 8) % 3 != 2 else "cold"; look = "coworker"
        elif t >= T0(8) - 0.4: cw = "smiletalk" if win_(t, T0(8), T1(8) - 0.05) and int(t * 8) % 3 != 2 else "smile"; look = "coworker"
    if t >= T0(10): scr_ = "blank"; look = "screen"; cw = None
    if t >= T0(11):
        if A: scr_ = "check"; typing = 0.5
        else: scr_ = "sheet1"
    if t >= T0(12) and not A: scr_ = "b_ai"; typing = 0.4
    if t >= T0(13): rise = ease((t - T0(13) - 0.3) / 3.0); typing = 0.0
    return scr_, tod, typing, cw, look, rise

def place(t, side):
    scr_, tod, typing, cw, look, rise = pane(t, side)
    set_tod(tod)
    tx.image = SCR[scr_]
    # カメラ：座った目線 → 窓（夕方に帰る）／同僚の方へ → 最後は天井近くまで上がって俯瞰
    base = Vector((0, -0.5, 1.17)); tgt = Vector((0, 0.25, 0.97))
    if look == "window": tgt = Vector((0, 2.6, 1.6)); base = Vector((0, -0.6, 1.55))
    if look == "coworker": tgt = Vector((1.0, 0.35, 1.45))
    base = base.lerp(Vector((0.0, -2.2, 2.9)), rise); tgt = tgt.lerp(Vector((0, 0.1, 0.7)), rise)
    breathe = Vector((0, 0, 0.006 * math.sin(t * 1.3)))
    cam.location = base + breathe; W.aim(cam, tgt)
    for o in [yo] + list(yo.children_recursive): o.hide_render = cw is None
    if cw: T.set_expr(ytex, "yota", cw)
    for s, sx in (("L", -1), ("R", 1)):
        bob = 0.012 * typing * max(0.0, math.sin(t * 22 + (0 if s == "L" else 1.7)))
        hn = Vector((0.1 * sx, -0.28 + bob, -0.5)) if look == "screen" and rise < 0.5 else Vector((0.16 * sx, -0.46, -0.4))
        set_arm(s, Vector((0.22 * sx, -0.55, 0.05)), Vector((0.22 * sx, -0.42, -0.3)), hn)

T.outlines(1.6)
frames = TEST or range(START, STOP)
t0 = time.time()
for f in frames:
    p = os.path.join(OUT, "done_%04d.txt" % (f + 1))
    if os.path.exists(p) and not TEST: continue
    t = f / FPS
    for side in "AB":                                             # 上下は別の画像に書き、書き出し時に ffmpeg で縦につなぐ
        place(t, side)
        hp = os.path.join(OUT, "%s_%04d.png" % (side, f + 1)); tmp = hp[:-4] + "_tmp.png"
        sc.render.filepath = tmp; bpy.ops.render.render(write_still=True); os.replace(tmp, hp)
    open(p, "w").write("ok")
    print("frame %s t=%.2f %.1fs" % (p, t, time.time() - t0), flush=True); t0 = time.time()
