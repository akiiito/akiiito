"""
create_gk2.py ― 学園デスゲーム『出席番号13番』第4話「16時44分」（教室から逃げた）（主観・CG＋輪郭線・夕方の教室）
  python create_gk1.py [--samples 14] [--thr 0.06] [--res 0.75] [--start 0] [--end N] [--test 24,100,...]
"""
import os, sys, math, json, time, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
from mathutils import Vector
import s2_world as W, s3_toon as T, blk_hair as H
from gk4_timing import *

HERE = os.path.dirname(os.path.abspath(__file__))
arg = lambda k, d: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
SAMPLES = int(arg("--samples", "14")); FPS = 24; N = int(END * FPS)
RS = float(arg("--res", "0.75"))
START = int(arg("--start", "0")); STOP = int(arg("--end", str(N)))
TEST = [int(x) for x in arg("--test", "").split(",") if x]
OUT = os.path.join(HERE, "frames_GK4" + ("_test" if TEST else "")); os.makedirs(OUT, exist_ok=True)
sc = W.reset(SAMPLES, res=(int(1080 * RS), int(1920 * RS)))
sc.cycles.use_adaptive_sampling = True; sc.cycles.adaptive_threshold = float(arg("--thr", "0.06"))
sc.cycles.max_bounces = 5; sc.render.use_persistent_data = True
try: sc.cycles.denoising_prefilter = "ACCURATE"; sc.cycles.denoising_quality = "HIGH"
except Exception: pass
sc.view_settings.view_transform = "AgX"; sc.view_settings.look = "AgX - Medium High Contrast"; sc.view_settings.exposure = -0.3
LINES = json.load(open(os.path.join(HERE, "gk4_lines.json"), encoding="utf-8"))
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
_pre = set(bpy.data.objects.keys()); W.vase(tuple(VASE), seed=5); VASEOBJ = [bpy.data.objects[n] for n in set(bpy.data.objects.keys()) - _pre]

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
bagm = W.mat("bag", (0.03, 0.035, 0.06), 0.5)
for x_, y_ in ((-1.35, -1.05), (1.15, 2.4), (-1.35, 0.1), (1.15, 0.1), (2.4, -1.05), (-2.6, -1.05), (2.4, 1.25), (-2.6, 1.25), (-0.1, 1.25)):
    W.box("bag", (x_ + 0.355, y_, 0.5), (0.07, 0.3, 0.26), bagm, bevel=0.015)
plane("nametag2", Vector((0.97, -2.33, 0.7355)), 0.18, 0.0675, img_mat("nametag2", os.path.join(A, "gk_nameplate_clean.png"), 0.15), rot=(0, 0, 0))
# ---------------------------------------------------------------- 今の教室（第3話の終わりのまま）
YUI_P2 = Vector((1.72, -2.6, 0))
REACH = {"L": ((0.2, 0.22, 1.08), (0.14, 0.45, 0.95))}
C["yuih"] = add_girl("yuih", "hana", YUI_P2, (0.12, 0.08, 0.07), False, arms=REACH, seed=11)
SAE_E = Vector((1.0, -1.6, 0))
C["sae2"] = add_girl("sae2", "sae", SAE_E, (0.05, 0.05, 0.07), True, seed=21)
EXTRA = {"g5": ("girl", "mina", Vector((2.45, -0.5, 0)), (0.1, 0.07, 0.05)),
         "b6": ("boy", "owner", Vector((-2.0, 0.75, 0)), (0.05, 0.05, 0.05))}
for k, (kind, face, p, hc) in EXTRA.items():
    C[k] = add_girl(k, face, p, hc, False, seed=len(k) * 7) if kind == "girl" else add_boy(k, face, p, hc)
PRESENT = ["yuih", "sae2", "g5", "b6"]
# ---------------------------------------------------------------- 1年前の記憶：火事
KAI_M = Vector((1.85, -3.3, 0))
C["kaip"] = add_boy("kaip", "yota", KAI_M, (0.07, 0.06, 0.06), arms=POINT)
W.box("lighter", (-0.12, 0.64, 1.3), (0.025, 0.012, 0.06), W.mat("lighter", (0.75, 0.08, 0.06), 0.3, 0.2), parent=C["kaip"][0])
def emat(name, col, strength):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    o = nt.nodes.new("ShaderNodeOutputMaterial"); e = nt.nodes.new("ShaderNodeEmission")
    e.inputs["Color"].default_value = col + (1,); e.inputs["Strength"].default_value = strength
    nt.links.new(e.outputs[0], o.inputs["Surface"]); return m
fm = emat("flame", (1.0, 0.12, 0.01), 3.0); fm2 = emat("flame2", (1.0, 0.38, 0.03), 5.0)
FX = bpy.data.collections.new("fx"); bpy.context.scene.collection.children.link(FX)
def fxo(name, mesh_mat, sub=2):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=sub, radius=1.0); o = bpy.context.object; o.name = name
    o.data.materials.append(mesh_mat)
    for c_ in list(o.users_collection): c_.objects.unlink(o)
    FX.objects.link(o); return o
lflame = fxo("lflame", fm2); lflame.parent = C["kaip"][0]; lflame.location = (-0.12, 0.64, 1.36); lflame.scale = (0.008, 0.008, 0.02)
FIRE0 = Vector((3.35, -4.05, 0))
rng = random.Random(4); FLAMES = []
for i in range(30):
    o = fxo("flame", fm if i % 3 else fm2)
    base = FIRE0 + Vector((rng.uniform(-1.5, 0.55), rng.uniform(-0.4, 0.25), 0))
    FLAMES.append((o, base, rng.uniform(0.09, 0.2), rng.uniform(0.4, 1.4), rng.uniform(0, 6.28), rng.uniform(5, 9)))
FL = []
for i, (p_, e_) in enumerate((((2.9, -3.5, 1.0), 45), ((2.3, -3.7, 1.6), 30), ((3.3, -3.1, 0.6), 25))):
    l_ = bpy.data.lights.new("firelight%d" % i, "POINT"); l_.color = (1.0, 0.42, 0.12); l_.shadow_soft_size = 0.4; l_.energy = 0
    lo_ = bpy.data.objects.new("firelight%d" % i, l_); bpy.context.collection.objects.link(lo_); lo_.location = p_; FL.append((l_, e_))
YUI_W = Vector((-3.55, -1.62, 0))
C["yuim"] = add_girl("yuim", "hana", YUI_W, (0.12, 0.08, 0.07), False, arms=REACH, seed=11)
pivot = bpy.data.objects.new("pivot", None); bpy.context.collection.objects.link(pivot); pivot.location = (-3.9, -1.62, 0.9)
C["yuim"][0].parent = pivot
MEMORY = ["kaip", "yuim"]
SASH = [bpy.data.objects.get(n) for n in ("sash2",)]
airm = bpy.data.materials.get("air"); PV = [n for n in airm.node_tree.nodes if n.type == "PRINCIPLED_VOLUME"][0]
SUN = room["sun"].data; BG = bpy.context.scene.world.node_tree.nodes["Background"]
# ---------------------------------------------------------------- カメラ
C0 = Vector((1.12, -2.98, 1.52))
cam = W.camera(tuple(C0), (3.96, 2.9, 1.05), lens=30, fstop=2.8)
cam.data.dof.use_dof = True
def vy(p, z): return Vector((p.x, p.y, z))
def lerp3(a, b, u): return a.lerp(b, min(max(u, 0.0), 1.0))
DOORP = Vector((4.2, 2.9, 1.45)); DOORL = Vector((5.5, 3.0, 1.3)); DOORV = Vector((3.96, 2.9, 1.05))
CA = Vector((2.0, 2.4, 1.55)); MID = Vector((3.0, 2.3, 1.55))
CLOCKL = CLOCK + Vector((0, 0, -0.02))
M0 = Vector((0.9, -1.55, 1.55)); MW = Vector((-2.75, -1.62, 1.5)); MP = Vector((-3.25, -1.62, 1.45))
YH = vy(YUI_P2, 1.4); YW = vy(YUI_W, 1.38); KH = vy(KAI_M, 1.38)
def dash_path(u):                      # 席の前 → 扉の向こう
    return lerp3(C0, MID, u / 0.55) if u < 0.55 else lerp3(MID, DOORP, (u - 0.55) / 0.45)
def camera(t):
    roll = 0.0
    if t < RESET1:
        u = t / RESET1; pos = lerp3(CA, DOORP, ease(u) * 0.3 + u * 0.7); look = DOORL; lens = 22 - 4 * u
        pos = pos + Vector((0, 0, 0.03 * math.sin(t * 30)))
    elif t < DASH2:
        pos = C0; look = DOORV; lens = 30
    elif t < RESET2:
        u = (t - DASH2) / (RESET2 - DASH2); pos = dash_path(u ** 1.3); look = lerp3(DOORV, DOORL, (u - 0.4) / 0.4); lens = 26 - 6 * u
        pos = pos + Vector((0, 0, 0.03 * math.sin(t * 30)))
    elif t < MONT1:
        s = ((t - MONT0) % 0.25) / 0.25; pos = dash_path(min(1.0, s * 1.15)); look = lerp3(DOORV, DOORL, (s - 0.4) / 0.4); lens = 24
    elif t < CLK - 0.35:
        ks = [(MONT1, DOORV, 30), (5.25, DOORV, 30), (5.65, YH, 34), (8.7, YH, 38), (9.0, YH, 44), (CLK - 0.35, YH, 46)]
        pos = C0; look, lens = ks[0][1], ks[0][2]
        for (a, la, na), (b, lb, nb) in zip(ks, ks[1:]):
            if a <= t <= b: u = ease((t - a) / (b - a)); look = la.lerp(lb, u); lens = na + (nb - na) * u
    elif t < 14.8:
        u = ease((t - (CLK - 0.35)) / 0.35); pos = C0; look = YH.lerp(CLOCKL, u); lens = 46 + (80 - 46) * u + 15 * ease((t - CLK) / 3.5)
    elif t < MEM:
        u = ease((t - 14.8) / 0.3); pos = C0; look = CLOCKL.lerp(YH, u); lens = 95 + (40 - 95) * u
    elif t < WIN - 0.3:
        pos = M0; look = KH.lerp(Vector((3.0, -4.0, 0.9)), 0.4); lens = 34 + 6 * ease((t - MEM) / 3.0)
    elif t < WIN:
        u = ease((t - (WIN - 0.3)) / 0.3); pos = M0; look = KH.lerp(YW, u); lens = 40 + (34 - 40) * u
    elif t < RUN:
        pos = M0; look = YW; lens = 34 + 4 * ease((t - WIN) / (RUN - WIN))
    elif t < PUSH:
        u = ease((t - RUN) / (PUSH - RUN)); pos = M0.lerp(MW, u) + Vector((0, 0, 0.03 * math.sin(t * 26))); look = YW; lens = 38 - 8 * u
    elif t < FALL:
        u = ease((t - PUSH) / 0.45); pos = MW.lerp(MP, u); look = YW.lerp(Vector((-7.0, -1.62, 0.2)), ease((t - PUSH - 0.1) / 0.5)); lens = 30
    elif t < BLACK + 0.2:
        u = ease((t - FALL) / 2.2); pos = MP.lerp(Vector((-2.95, -1.4, 0.32)), u)
        look = Vector((-7.0, -1.62, 0.2)).lerp(CLOCKL, ease((t - FALL) / 1.6)); lens = 30 + 10 * u; roll = math.radians(28) * u
    else:
        pos = C0; look = YH; lens = 36 + 8 * ease((t - PRES) / (CARD - PRES))
    return pos, look, lens, roll
# ---------------------------------------------------------------- 乱れ（バグ）の強さ
RESETS = [RESET1, RESET2] + [MONT0 + 0.25 * k for k in range(1, 7)]
def spike(t, a, g, d): return g * max(0.0, 1 - (t - a) / d) if t >= a else 0.0
def glitch(t):
    g = 0.0
    for a in RESETS: g = max(g, spike(t, a, 1.0 if a < MONT0 + 0.1 else 0.75, 0.3 if a < MONT0 + 0.1 else 0.14))
    g = max(g, spike(t, 4.3, 0.7, 0.4), spike(t, CLKSTOP, 0.9, 0.35), spike(t, MEM, 1.0, 0.7), spike(t, PUSH, 0.55, 0.4),
            spike(t, PRES, 0.6, 0.5), spike(t, CARD, 0.5, 0.3))
    if CLK <= t < CLKSTOP: g = max(g, 0.3 + 0.2 * math.sin(t * 40) ** 2)
    if 14.9 <= t < MEM: g = max(g, 0.9 * ((t - 14.9) / (MEM - 14.9)) ** 2)
    f = int(t * FPS)
    if MONT1 < t < CLK or PRES + 0.6 < t < CARD:                       # ときどき世界がちらつく
        if random.Random(f // 2 * 31 + 7).random() < 0.09: g = max(g, 0.32)
    if 33.2 < t < 34.9 and random.Random(f * 13).random() < 0.3: g = max(g, 0.45)
    return min(1.0, g)
# ---------------------------------------------------------------- 表情
def expr(who, t):
    tk = mouth("yui" if who in ("yuih", "yuim") else who, t)
    if who == "yuih":
        if t >= PRES: return "tearsmiletalk" if tk else "tearsmile"
        return "tearsadtalk" if tk else "tearsad"
    if who == "yuim": return "shockc" if t >= PUSH else ("tearsadtalk" if tk else "tearsad")
    if who == "kaip": return "talk" if tk else "shock"
    if who == "sae2": return "tearsmile"
    return "sad"
def show_all(names, on):
    for n in names: show(C[n][0], on)
def place(t):
    mem = MEM <= t < BLACK + 0.2
    show_all(PRESENT, not mem); show_all(MEMORY, mem)
    for o, *_ in FLAMES: o.hide_render = not mem
    for o in VASEOBJ: o.hide_render = mem
    lflame.hide_render = not (mem and t < WIN)
    for s_ in SASH:
        if s_: s_.hide_render = mem
    # 扉はあけっぱなし（白い廊下）
    door.location = DOOR_O + Vector((0, 0.86, 0)); gl.energy = 0 if mem else 250
    # 時計の針が狂う → 16:44 で止まる
    a = 0.0
    if CLK <= t < CLKSTOP: u = (t - CLK) / (CLKSTOP - CLK); a = 2 * math.pi * 7 * (1 - (1 - u) ** 2)
    if MONT0 <= t < MONT1: a = random.Random(int(t * FPS)).uniform(-3, 3)
    cf.rotation_euler = (math.pi / 2, a, math.pi)
    # 光と煙
    if mem:
        f = int(t * FPS); r_ = random.Random(f)
        smoke = 0.006 + 0.016 * ease((t - MEM) / 6.0) + 0.05 * ease((t - FALL) / 2.4)
        PV.inputs["Density"].default_value = smoke; PV.inputs["Color"].default_value = (0.07, 0.06, 0.055, 1)
        SUN.energy = 0.0; SUN.color = (1.0, 0.35, 0.15); BG.inputs["Strength"].default_value = 0.25
        kl.energy = 25; kl.color = (1.0, 0.45, 0.2)
        for l_, e_ in FL: l_.energy = e_ * (0.75 + 0.5 * r_.random())
        for o, base, rad, hgt, ph, sp_ in FLAMES:
            w = 0.75 + 0.25 * math.sin(t * sp_ + ph) + 0.15 * r_.random()
            o.location = base + Vector((0.03 * math.sin(t * 7 + ph), 0, hgt * w * 0.5))
            o.scale = (rad * w, rad * w, hgt * w * 0.55)
    else:
        PV.inputs["Density"].default_value = 0.003; PV.inputs["Color"].default_value = (1, 1, 1, 1)
        SUN.energy = 12.0; SUN.color = (1.0, 0.55, 0.28); BG.inputs["Strength"].default_value = 2.5
        kl.energy = 90; kl.color = (1.0, 0.9, 0.8)
        for l_, e_ in FL: l_.energy = 0
    g = glitch(t)
    # 今の教室：止まったままの生徒（バグると瞬間移動する）
    jr = random.Random(int(t * FPS) * 7 + 3)
    def jit(p): return p + (Vector((jr.uniform(-0.35, 0.35), jr.uniform(-0.35, 0.35), 0)) if g > 0.5 and t < MEM else Vector((0, 0, 0)))
    face_to(C["yuih"][0], jit(YUI_P2), (C0.x, C0.y)); T.set_expr(C["yuih"][1], "hana", expr("yuih", t))
    face_to(C["sae2"][0], jit(SAE_E), (VASE.x, VASE.y - 0.4)); C["sae2"][0].rotation_euler.x = -0.17; T.set_expr(C["sae2"][1], "sae", expr("sae2", t))
    for k, (kind, face, p_, hc) in EXTRA.items():
        face_to(C[k][0], jit(p_), (VASE.x, VASE.y)); T.set_expr(C[k][1], face, expr(k, t))
    # 記憶：カイト（ライター）とユイ（窓ぎわ）
    face_to(C["kaip"][0], KAI_M, (M0.x, M0.y)); T.set_expr(C["kaip"][1], "yota", expr("kaip", t))
    C["yuim"][0].location = YUI_W - pivot.location; C["yuim"][0].rotation_euler = (0, 0, -math.pi / 2)
    T.set_expr(C["yuim"][1], "hana", expr("yuim", t))
    u = ease((t - PUSH) / 0.18); fl_ = max(0.0, t - PUSH - 0.1)
    pivot.rotation_euler = (0, -math.radians(40) * u, 0)
    pivot.location = Vector((-3.9 - 1.5 * u - 0.5 * fl_, -1.62, 0.9 + 0.3 * u - 4.0 * fl_ * fl_))
    show(C["yuim"][0], mem and t < PUSH + 0.28)
    pos, look, lens, roll = camera(t)
    sway = Vector((0.006 * math.sin(t * 1.3), 0.004 * math.sin(t * 0.9), 0.005 * math.sin(t * 1.7)))
    shake = Vector((jr.uniform(-1, 1), jr.uniform(-1, 1), jr.uniform(-1, 1))) * 0.02 * g
    cam.location = pos + sway + shake; W.aim(cam, look); cam.data.lens = lens
    if roll: cam.rotation_euler.rotate_axis("Z", roll)
    cam.data.dof.focus_distance = max(0.3, (look - cam.location).length)
    imp = 0.0
    for a_, g_ in ((RESET1, 0.8), (RESET2, 0.8), (4.3, 0.6), (CLKSTOP, 0.7), (MEM, 0.8), (17.0, 0.4), (WIN, 0.35), (PUSH, 0.8), (PRES, 0.4), (33.2, 0.35)):
        if t >= a_: imp = max(imp, max(0.0, 1 - (t - a_) / 0.5) * g_)
    dash = 1.0 if (t < RESET1 or DASH2 <= t < MONT1 or RUN <= t < PUSH) else 0.0
    white = max(0.9 * ease((t - RESET1 + 0.25) / 0.25) * (1 - ease((t - RESET1 - 0.02) / 0.08)),
                0.9 * ease((t - RESET2 + 0.2) / 0.2) * (1 - ease((t - RESET2 - 0.02) / 0.08)),
                0.6 * max(0.0, 1 - abs(t - PUSH - 0.1) / 0.18))
    dark = ease((t - FALL - 0.6) / 2.0) if t < PRES else 1 - ease((t - PRES) / 0.6)
    red = 0.5 * ease((t - 14.9) / 1.0) if t < MEM else 0.0
    return dict(t=t, kind="", edit=0.0, pov=True, dash=dash, impact=imp, white=white, red=red,
                glitch=g, mem=1.0 if mem else 0.0, dark=dark)
try:
    ls_.select_by_collection = True; ls_.collection = FX; ls_.collection_negation = "EXCLUSIVE"
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
