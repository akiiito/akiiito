"""
create_gk2.py ― 学園デスゲーム『出席番号13番』第2話A「消えた席」（主観・CG＋輪郭線・夕方の教室）
  python create_gk1.py [--samples 14] [--thr 0.06] [--res 0.75] [--start 0] [--end N] [--test 24,100,...]
"""
import os, sys, math, json, time, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
from mathutils import Vector
import s2_world as W, s3_toon as T, blk_hair as H
from gk2_timing import *

HERE = os.path.dirname(os.path.abspath(__file__))
arg = lambda k, d: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
SAMPLES = int(arg("--samples", "14")); FPS = 24; N = int(END * FPS)
RS = float(arg("--res", "0.75"))
START = int(arg("--start", "0")); STOP = int(arg("--end", str(N)))
TEST = [int(x) for x in arg("--test", "").split(",") if x]
OUT = os.path.join(HERE, "frames_GK2" + ("_test" if TEST else "")); os.makedirs(OUT, exist_ok=True)
sc = W.reset(SAMPLES, res=(int(1080 * RS), int(1920 * RS)))
sc.cycles.use_adaptive_sampling = True; sc.cycles.adaptive_threshold = float(arg("--thr", "0.06"))
sc.cycles.max_bounces = 5; sc.render.use_persistent_data = True
try: sc.cycles.denoising_prefilter = "ACCURATE"; sc.cycles.denoising_quality = "HIGH"
except Exception: pass
sc.view_settings.view_transform = "AgX"; sc.view_settings.look = "AgX - Medium High Contrast"; sc.view_settings.exposure = -0.3
LINES = json.load(open(os.path.join(HERE, "gk2_lines.json"), encoding="utf-8"))
def ease(x): x = min(max(x, 0.0), 1.0); return x * x * (3 - 2 * x)
def talking(who, t): return any(l[0] <= t <= l[1] - 0.05 for l in LINES if l[5] == who)
def mouth(who, t): return talking(who, t) and int(t * 12) % 3 != 2
def blink(t, ph): return (t * 10 + ph) % 41 < 1.2

# ---------------------------------------------------------------- 教室（夕方）
random.seed(5)
room = W.classroom(sun_elev=10.0, sun_az=-30.0, haze=0.003, sun_str=12.0, fill=8)
D = room["D"]
kl = bpy.data.lights.new("facefill", "AREA"); kl.size = 2.5; kl.energy = 90; kl.color = (1.0, 0.9, 0.8)
ko = bpy.data.objects.new("facefill", kl); bpy.context.collection.objects.link(ko); ko.location = (0.6, -3.2, 2.2); W.aim(ko, (0, 1.5, 1.3))
# 輪郭線
sc.render.use_freestyle = True
try: sc.render.line_thickness_mode = "ABSOLUTE"; sc.render.line_thickness = 1.3 * RS / 0.75
except Exception: pass
try:
    fs_ = bpy.context.view_layer.freestyle_settings; ls_ = fs_.linesets[0] if fs_.linesets else fs_.linesets.new("ls")
    ls_.select_by_visibility = True; ls_.select_silhouette = True; ls_.select_border = False; ls_.select_crease = False
    if ls_.linestyle is None: ls_.linestyle = bpy.data.linestyles.new("ls")
    ls_.linestyle.color = (0.05, 0.035, 0.03); ls_.linestyle.thickness = 1.5
except Exception as ex: print("freestyle", ex)

def img_mat(name, path, emit=0.0, alpha=False):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; b = nt.nodes["Principled BSDF"]
    tx = nt.nodes.new("ShaderNodeTexImage"); tx.image = bpy.data.images.load(path)
    nt.links.new(tx.outputs["Color"], b.inputs["Base Color"]); b.inputs["Roughness"].default_value = 0.6
    if emit: nt.links.new(tx.outputs["Color"], b.inputs["Emission Color"]); b.inputs["Emission Strength"].default_value = emit
    if alpha: nt.links.new(tx.outputs["Alpha"], b.inputs["Alpha"])
    return m
def plane(name, loc, sx, sy, m, rot=(math.pi / 2, 0, 0)):
    bpy.ops.mesh.primitive_plane_add(size=1, location=loc); p = bpy.context.object; p.name = name
    p.scale = (sx, sy, 1); p.rotation_euler = rot; p.data.materials.append(m); return p
A = os.path.join(HERE, "s3_assets")
# 16:44 で止まった時計（F1）と黒板の文字（F7）
CLOCK = Vector((0.2, D / 2 - 0.05, 2.55))
W.cyl("clock_rim", (CLOCK.x, CLOCK.y + 0.02, CLOCK.z), 0.2, 0.05, W.mat("clockrim", (0.08, 0.08, 0.09), 0.4), rot=(math.pi / 2, 0, 0), verts=40)
cf = plane("clock_face", (CLOCK.x, CLOCK.y - 0.006, CLOCK.z), -0.36, 0.36, img_mat("clockface", os.path.join(A, "gk_clock.png"), 0.6, alpha=True), rot=(math.pi / 2, 0, math.pi))
BOARDT = Vector((0.2, D / 2 - 0.045, 1.6))
plane("chalk", BOARDT, -4.3, 1.075, img_mat("chalk", os.path.join(A, "gk_board.png"), 0.25, alpha=True), rot=(math.pi / 2, 0, math.pi))
SPK = Vector((2.35, D / 2 - 0.12, 2.72))
W.box("speaker", SPK, (0.42, 0.16, 0.3), W.mat("spk", (0.75, 0.74, 0.7), 0.6), bevel=0.02)
W.box("grille", SPK + Vector((0, -0.085, 0)), (0.34, 0.01, 0.22), W.mat("grille", (0.15, 0.15, 0.16), 0.7))
# 前の扉：右の壁に穴を開け、引き戸と真っ白な廊下（教室を出た生徒は「消える」）
wi = bpy.data.objects.get("wall_in")
if wi: bpy.data.objects.remove(wi, do_unlink=True)
DY0, DY1, DZ = 2.45, 3.35, 2.0
wm = W.mat("wall2", (0.78, 0.76, 0.7), 0.85)
W.box("wall_in_a", (4.05, (-D / 2 + DY0) / 2, 1.5), (0.1, DY0 + D / 2, 3.0), wm)
W.box("wall_in_b", (4.05, (DY1 + D / 2) / 2, 1.5), (0.1, D / 2 - DY1, 3.0), wm)
W.box("wall_in_c", (4.05, (DY0 + DY1) / 2, (DZ + 3.0) / 2), (0.1, DY1 - DY0, 3.0 - DZ), wm)
W.box("door_frame", (3.99, (DY0 + DY1) / 2, DZ + 0.03), (0.06, DY1 - DY0 + 0.08, 0.06), W.mat("dframe", (0.45, 0.46, 0.48), 0.4, 0.6))
DOOR_O = Vector((3.96, (DY0 + DY1) / 2, DZ / 2))
door = W.box("door", tuple(DOOR_O), (0.05, DY1 - DY0, DZ), W.mat("doorm", (0.22, 0.15, 0.09), 0.7))
W.box("door_win", (-0.03, -0.15, 0.45), (0.01, 0.35, 0.5), W.mat("doorwin", (0.85, 0.88, 0.9), 0.1), parent=door)
hm = bpy.data.materials.new("hallglow"); hm.use_nodes = True; hb = hm.node_tree.nodes["Principled BSDF"]
hb.inputs["Base Color"].default_value = (1, 1, 1, 1); hb.inputs["Emission Color"].default_value = (1.0, 0.97, 0.92, 1); hb.inputs["Emission Strength"].default_value = 6.0
W.box("hall", (4.35, (DY0 + DY1) / 2, 1.5), (0.1, 2.0, 3.0), hm)
gl = bpy.data.lights.new("doorglow", "AREA"); gl.size = 0.9; gl.energy = 0; gl.color = (1.0, 0.96, 0.9)
glo = bpy.data.objects.new("doorglow", gl); bpy.context.collection.objects.link(glo); glo.location = (4.2, (DY0 + DY1) / 2, 1.1); W.aim(glo, (0, 0, 1.0))
# 後ろの席の白い菊（F6）
VASE = Vector((1.15, -2.2, 0.735))
W.vase(tuple(VASE), seed=5)

# ---------------------------------------------------------------- 生徒
def pbr(root, cmap):
    for o in [root] + list(root.children_recursive):
        if o.type != "MESH": continue
        for i, m in enumerate(o.data.materials):
            if not (m and m.node_tree) or "facemat" in m.name: continue
            rp = [n for n in m.node_tree.nodes if n.type == "VALTORGB"]
            if not rp: continue
            key = m.name.split("_")[-1]
            c = cmap.get(key) or tuple(x ** 0.4545 for x in rp[0].color_ramp.elements[1].color[:3])
            lin = tuple(x ** 2.2 for x in c); sk = "skin" in m.name; hr = "hair" in m.name
            nm = W.mat(m.name + "_pbr", lin, 0.5 if sk else (0.36 if hr else 0.8), sss=0.25 if sk else 0.0)
            b = nm.node_tree.nodes["Principled BSDF"]
            if hr: b.inputs["Coat Weight"].default_value = 0.25; b.inputs["Sheen Weight"].default_value = 0.4
            o.data.materials[i] = nm
def face_to(o, p, tgt):
    o.location = (p[0], p[1], 0); d = Vector((tgt[0] - p[0], tgt[1] - p[1], 0)).normalized()
    o.rotation_euler = (0, 0, math.atan2(-d.x, d.y))
P0 = Vector((-0.1, -1.55, 1.18))                      # 自分（席に座っている）
FRONT = Vector((0.2, 9.0, 0))
POINT = {"R": ((-0.2, 0.3, 1.3), (-0.12, 0.62, 1.33))}           # 指さし
CLING = {"L": ((0.2, 0.2, 1.08), (0.12, 0.42, 1.02)), "R": ((-0.2, 0.2, 1.08), (-0.1, 0.4, 1.02))}
BOOK = {"L": ((0.2, 0.15, 1.05), (0.08, 0.3, 1.15)), "R": ((-0.2, 0.15, 1.05), (-0.08, 0.3, 1.15))}
C = {}
def add_girl(nm, face, pos, hair, ponytail, arms=None, seed=3):
    r_, tx_ = T.girl(nm, (0, 0, 0), hair=hair, face=face, ponytail=ponytail, arms=arms)
    pbr(r_, {}); H.upgrade(r_, nm, [m for o in r_.children if o.name.startswith(nm + "_hair") for m in o.data.materials][0], seed=seed)
    return r_, tx_
def add_boy(nm, face, pos, hair, arms=None):
    r_, tx_ = T.boy(nm, (0, 0, 0), hair=hair, face=face, arms=arms); pbr(r_, {}); return r_, tx_
def objs(r_): return [r_] + list(r_.children_recursive)
def show(r_, on):
    for o in objs(r_):
        if o.type == "MESH": o.hide_render = not on
# 塗りつぶされた名札（下から13が透ける）：菊の机の上
TAG = Vector((0.97, -2.33, 0.735))
plane("nametag", TAG, 0.18, 0.0675, img_mat("nametag", os.path.join(A, "gk_nameplate.png"), 0.15), rot=(0, 0, 0))
# 残っている生徒の机にはカバン（消えた人の机にはない）
KDESK = Vector((-0.1, 0.1, 0.72))
bagm = W.mat("bag", (0.03, 0.035, 0.06), 0.5)
for x_, y_ in ((-1.35, -1.05), (1.15, 2.4), (-1.35, 0.1), (1.15, 0.1), (2.4, -1.05), (-2.6, -1.05), (2.4, 1.25), (-2.6, 1.25), (-0.1, 1.25)):
    W.box("bag", (x_ + 0.355, y_, 0.5), (0.07, 0.3, 0.26), bagm, bevel=0.015)

# ---------------------------------------------------------------- 生徒
YUI_P = Vector((-0.95, -0.55, 0)); YUI_P2 = Vector((1.72, -2.6, 0))        # 第2話の終わり：あなたの真横に
REACH = {"L": ((0.2, 0.22, 1.08), (0.14, 0.45, 0.95))}
C["yui"] = add_girl("yui", "hana", YUI_P, (0.12, 0.08, 0.07), False, seed=11)
C["yuih"] = add_girl("yuih", "hana", YUI_P2, (0.12, 0.08, 0.07), False, arms=REACH, seed=11)
KAI_P = Vector((-0.72, 0.55, 0))
C["kai"] = add_boy("kai", "yota", KAI_P, (0.07, 0.06, 0.06))
SAE_P = Vector((1.0, 3.45, 0))
C["sae"] = add_girl("sae", "sae", SAE_P, (0.05, 0.05, 0.07), True, arms=BOOK, seed=21)
W.box("rollbook", (0, 0.32, 1.17), (0.24, 0.03, 0.32), W.mat("rollbook", (0.15, 0.2, 0.35), 0.6), rot=(0.5, 0, 0), parent=C["sae"][0])
# 消える生徒（カイトに投票した）と、残る生徒
EXTRA = {"mio": ("girl", "mio", Vector((-1.97, 1.75, 0)), (0.3, 0.18, 0.1), 9.2),
         "b2": ("boy", "boss", Vector((0.55, 0.7, 0)), (0.12, 0.1, 0.09), 10.3),
         "mei": ("girl", "mei", Vector((1.77, 1.9, 0)), (0.08, 0.06, 0.08), 10.9),
         "g3": ("girl", "toki", Vector((-1.97, -0.25, 0)), (0.2, 0.12, 0.08), 11.45),
         "g5": ("girl", "mina", Vector((2.45, -0.5, 0)), (0.1, 0.07, 0.05), None),
         "b6": ("boy", "owner", Vector((-2.0, 0.75, 0)), (0.05, 0.05, 0.05), None)}
for k, (kind, face, p, hc, _) in EXTRA.items():
    C[k] = add_girl(k, face, p, hc, k == "mio", seed=len(k) * 7) if kind == "girl" else add_boy(k, face, p, hc)

# ---------------------------------------------------------------- 光の粒
pm = bpy.data.materials.new("spark"); pm.use_nodes = True; pb = pm.node_tree.nodes["Principled BSDF"]
pb.inputs["Base Color"].default_value = (1, 0.9, 0.7, 1); pb.inputs["Emission Color"].default_value = (1.0, 0.85, 0.55, 1); pb.inputs["Emission Strength"].default_value = 14.0
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=1.0); sp0 = bpy.context.object; sme = sp0.data; sme.materials.append(pm); bpy.data.objects.remove(sp0, do_unlink=True)
SPC = bpy.data.collections.new("sparks"); bpy.context.scene.collection.children.link(SPC)
PARTS = []; rng = random.Random(13)
def body_sparks(c, t0, n=300, pre=0.0, seed=0):
    for i in range(n):
        z = rng.uniform(0.05, 1.75); r = 0.13 if z > 1.45 else (0.21 if z > 0.85 else 0.15)
        a = rng.uniform(0, 2 * math.pi); rr = r * math.sqrt(rng.uniform(0.3, 1.0))
        base = Vector((c.x + rr * math.cos(a), c.y + rr * math.sin(a), z))
        st = t0 - 0.1 + 0.5 * (1.75 - z) / 1.75 + rng.uniform(-0.06, 0.06)
        if i < pre: st = rng.uniform(-0.3, t0)
        vel = Vector((rng.uniform(-0.3, 0.3), rng.uniform(-0.3, 0.3), rng.uniform(0.35, 1.1)))
        o = bpy.data.objects.new("spark", sme); SPC.objects.link(o)
        PARTS.append((o, base, st, vel, rng.uniform(0.011, 0.022), rng.uniform(0.9, 1.6), rng.uniform(0, 6.28)))
body_sparks(KAI_P, KDIS, 360, pre=70)
for k, (kind, face, p, hc, tv) in EXTRA.items():
    if tv: body_sparks(p, tv, 300)
# 自分の体も光りかける（見下ろした視界の下から粒が立ちのぼり、途中で止まる）
for i in range(160):
    base = Vector((P0.x + rng.uniform(-0.32, 0.32), P0.y + rng.uniform(0.15, 0.42), rng.uniform(0.55, 1.0)))
    st = SELF + rng.uniform(0.0, 0.9) ** 1.6
    vel = Vector((rng.uniform(-0.08, 0.08), rng.uniform(-0.05, 0.08), rng.uniform(0.15, 0.4)))
    o = bpy.data.objects.new("spark", sme); SPC.objects.link(o)
    PARTS.append((o, base, st, vel, rng.uniform(0.004, 0.008), rng.uniform(0.5, 0.9), rng.uniform(0, 6.28)))
def sparks(t):
    for o, base, st, vel, rad, life, ph in PARTS:
        u = t - st
        if u < 0 or u > life: o.hide_render = True; continue
        o.hide_render = False
        sw = Vector((0.04 * math.sin(ph + u * 6), 0.04 * math.cos(ph + u * 5), 0))
        o.location = base + vel * (u + 0.6 * u * u) + sw * u
        k = min(1.0, u / 0.12) * (1 - ease((u - 0.25) / (life - 0.25)))
        o.scale = (rad * (0.4 + 0.6 * k),) * 3

# ---------------------------------------------------------------- カメラ（座って → 立ち上がって歩く）
cam = W.camera(tuple(P0), (0.2, 4.0, 2.4), lens=40, fstop=2.8)
cam.data.dof.use_dof = True
def vy(p, z): return Vector((p.x, p.y, z))
LOOKS = dict(
    kai=vy(KAI_P, 1.45), kaiup=vy(KAI_P, 1.9), spk=SPK, cls=Vector((0.4, 2.6, 1.25)), self=P0 + Vector((0.0, 0.4, -0.75)),
    mio=vy(EXTRA["mio"][2], 1.35), b2=vy(EXTRA["b2"][2], 1.4), mei=vy(EXTRA["mei"][2], 1.35), g3=vy(EXTRA["g3"][2], 1.35),
    yui=vy(YUI_P, 1.42), sae=vy(SAE_P, 1.42), kdesk=Vector((0.6, 0.12, 0.6)), vdesk=Vector((1.08, -2.27, 0.8)), tag=TAG + Vector((0, 0, 0.002)),
    yuih=vy(YUI_P2, 1.4), spkf=SPK + Vector((0, 0, -0.1)))
KEYS = [(0.0, "kai", 42, 0.0), (1.2, "kai", 44, 0.0), (2.6, "kaiup", 48, 1.2),
        (3.2, "spk", 40, 0.5), (5.4, "spk", 42, 0.0),
        (6.0, "cls", 30, 0.45), (8.8, "cls", 31, 0.0),
        (9.1, "mio", 40, 0.25), (9.95, "mio", 42, 0.0),
        (10.2, "b2", 40, 0.25), (10.7, "b2", 41, 0.0),
        (10.85, "mei", 40, 0.2), (11.3, "mei", 41, 0.0),
        (11.45, "g3", 40, 0.2), (11.85, "g3", 41, 0.0),
        (12.25, "self", 30, 0.4), (13.8, "self", 32, 0.0),
        (14.3, "yui", 34, 0.4), (17.0, "yui", 36, 0.0),
        (17.35, "sae", 44, 0.35), (18.9, "sae", 46, 0.0),
        (19.7, "kdesk", 16, 0.6), (21.3, "kdesk", 18, 0.0),
        (22.0, "vdesk", 28, 0.6), (23.9, "vdesk", 32, 0.0),
        (24.35, "tag", 58, 0.35), (25.3, "tag", 66, 0.0),
        (25.8, "spkf", 42, 0.5), (28.3, "spkf", 46, 0.0),
        (28.7, "yuih", 32, 0.3), (31.9, "yuih", 34, 0.0),
        (32.4, "tag", 52, 0.5), (END, "tag", 62, 0.0)]
POS = [(0.0, P0), (18.9, P0), (19.5, P0 + Vector((-0.15, 0.1, 0.4))), (20.6, Vector((0.6, -1.05, 1.58))),
       (21.5, Vector((0.75, -1.6, 1.56))), (22.9, Vector((1.12, -2.95, 1.52))), (END, Vector((1.12, -2.98, 1.52)))]
def shot(t):
    i = max([j for j, k in enumerate(KEYS) if k[0] <= t] or [0]); k1 = KEYS[i]
    if i + 1 < len(KEYS):
        k2 = KEYS[i + 1]; ts_ = k2[0] - k2[3]
        if k2[3] > 0 and t >= ts_:
            u = ease((t - ts_) / k2[3]); return LOOKS[k1[1]].lerp(LOOKS[k2[1]], u), k1[2] + (k2[2] - k1[2]) * u
        u = (t - k1[0]) / max(0.01, ts_ - k1[0])
        if k2[3] == 0: return LOOKS[k1[1]].lerp(LOOKS[k2[1]], u), k1[2] + (k2[2] - k1[2]) * u
        return LOOKS[k1[1]], k1[2] + 1.2 * min(1, u)
    return LOOKS[k1[1]], k1[2]
def campos(t):
    for (a, pa), (b, pb_) in zip(POS, POS[1:]):
        if a <= t <= b: return pa.lerp(pb_, ease((t - a) / max(0.01, b - a)))
    return POS[-1][1]
def walking(t): return 18.9 < t < 22.9

# ---------------------------------------------------------------- 表情・向き
def expr(who, t):
    tk = mouth(who, t); bl = blink(t, len(who) * 7)
    if who == "yui":
        if t < 16.0: return "shockc" if t < 9.0 else ("sadblink" if bl else "sad")
        if t < 17.0: return "tearsmiletalk" if tk else "tearsmile"
        if t < 28.5: return "sadblink" if bl else "sad"
        return "tearsadtalk" if tk else "tearsad"
    if who == "kai": return "talk" if tk else "shock"
    if who == "sae":
        if 17.1 <= t < 19.3: return "coldtalk" if tk else "cold"
        return "blink" if bl else "cold"
    if who in ("mio", "b2") and tk: return "talk"
    return "shock" if t < 14.0 else ("blink" if bl else "sad")
def place(t):
    door.location = DOOR_O + Vector((0, 0.86, 0)); gl.energy = 250
    yh = t >= 26.0
    show(C["yui"][0], not yh); show(C["yuih"][0], yh)
    face_to(C["yui"][0], YUI_P, KAI_P if t < 9.0 else P0); T.set_expr(C["yui"][1], "hana", expr("yui", t))
    cp = campos(t)
    face_to(C["yuih"][0], YUI_P2, (TAG.x, TAG.y) if t < 29.6 else cp); T.set_expr(C["yuih"][1], "hana", expr("yui", t))
    show(C["kai"][0], t < KDIS + 0.22); face_to(C["kai"][0], KAI_P, P0); T.set_expr(C["kai"][1], "yota", expr("kai", t))
    face_to(C["sae"][0], SAE_P, P0 + Vector((0.6, 0, 0)) if t < 19.0 else cp + Vector((0.8, 0, 0))); T.set_expr(C["sae"][1], "sae", expr("sae", t))
    for k, (kind, face, p, hc, tv) in EXTRA.items():
        show(C[k][0], not (tv and t >= tv + 0.22))
        face_to(C[k][0], p, KAI_P if t < 3.0 else (SAE_P if tv is None and t > 14 else P0 + Vector((1.5, 1.5, 0))))
        T.set_expr(C[k][1], face, expr(k, t))
    sparks(t)
    look, lens = shot(t)
    bob = 0.025 * abs(math.sin(t * 7.5)) if walking(t) and not (19.4 < t < 19.6) else 0.0
    sway = Vector((0.006 * math.sin(t * 1.3), 0.004 * math.sin(t * 0.9), 0.005 * math.sin(t * 1.7) + bob))
    cam.location = cp + sway; W.aim(cam, look); cam.data.lens = lens
    cam.data.dof.focus_distance = max(0.3, (look - cam.location).length)
    imp = 0.0
    for a_, g_ in ((KDIS, 0.5), (5.5, 0.6), (9.2, 0.4), (10.3, 0.4), (10.9, 0.35), (11.45, 0.35), (24.4, 0.5)):
        if t >= a_: imp = max(imp, max(0.0, 1 - (t - a_) / 0.5) * g_)
    return dict(t=t, kind="", edit=0.0, pov=True, dash=0.0, impact=imp,
                white=0.5 * max(0.0, 1 - abs(t - KDIS - 0.12) / 0.2) + 0.25 * ease((t - SELF) / 0.4) * (1 - ease((t - SELF - 0.9) / 0.5)),
                red=ease((t - 5.5) / 0.3) * (1 - ease((t - 14.0) / 0.8)) * 0.55 + ease((t - 28.6) / 0.6) * 0.55)

try:
    ls_.select_by_collection = True; ls_.collection = SPC; ls_.collection_negation = "EXCLUSIVE"
except Exception as ex: print("fs coll", ex)
frames = TEST or range(START, STOP)
t0 = time.time()
for f in frames:
    p = os.path.join(OUT, "%04d.png" % (f + 1))
    if os.path.exists(p) and not TEST: continue
    t = f / FPS; meta = place(t); bpy.context.view_layer.update()
    json.dump(meta, open(p[:-4] + ".json", "w"))
    tmp = p[:-4] + "_tmp.png"; sc.render.filepath = tmp
    bpy.ops.render.render(write_still=True); os.replace(tmp, p)
    print("frame %s t=%.2f %.1fs" % (p, t, time.time() - t0), flush=True); t0 = time.time()
