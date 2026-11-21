"""
create_toki1.py ― 「その罪、時効にさせない」第1話『光る絵の具』（ブロック世界・夜の時計工場 → 時が止まる → 裁き → 夜明け）
  python create_toki1.py [--samples 18] [--res 0.75] [--start 0] [--end 840] [--test 0,140,...]
  実話（1917〜1928年の米国・夜光塗料の文字盤工場）をもとにしたフィクション。会社名・人物は架空。
"""
import os, sys, math, json, time, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, bmesh
from mathutils import Vector, Matrix
from bpy_extras.object_utils import world_to_camera_view
import s2_world as W, s3_toon as T, s7_world as S7, blk_hair as H
from toki1_timing import *

HERE = os.path.dirname(os.path.abspath(__file__))
arg = lambda k, d: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
SAMPLES = int(arg("--samples", "18")); FPS = 24; N = int(END * FPS)
RS = float(arg("--res", "0.75"))
START = int(arg("--start", "0")); STOP = int(arg("--end", str(N)))
TEST = [int(x) for x in arg("--test", "").split(",") if x]
OUT = os.path.join(HERE, "frames_TOKI1" + ("_test" if TEST else "")); os.makedirs(OUT, exist_ok=True)
LINES = json.load(open(os.path.join(HERE, "toki1_lines.json"), encoding="utf-8"))
TT = os.path.join(HERE, "toki_tex")

sc = W.reset(SAMPLES, res=(int(1080 * RS), int(1920 * RS)))
sc.cycles.max_bounces = 5; sc.cycles.diffuse_bounces = 3; sc.cycles.glossy_bounces = 2; sc.cycles.transparent_max_bounces = 8
sc.cycles.use_adaptive_sampling = True; sc.cycles.adaptive_threshold = float(arg("--thr", "0.04"))
try: sc.cycles.denoising_prefilter = "ACCURATE"; sc.cycles.denoising_quality = "HIGH"
except Exception: pass
sc.render.use_persistent_data = True
sc.view_settings.view_transform = "AgX"; sc.view_settings.look = arg("--look", "AgX - Punchy")
sc.view_settings.exposure = float(arg("--exp", "0.0"))

def ease(x): x = min(max(x, 0.0), 1.0); return x * x * (3 - 2 * x)
def win(t, a, b, fi=0.3, fo=0.3): return ease((t - a) / fi) * (1 - ease((t - b) / fo))

# 霧（パート4の共通ノードをそのまま使う）
_src4 = open(os.path.join(HERE, "create_block4.py"), encoding="utf-8").read()
_i = _src4.index("# ---------------------------------------------------------------- 霧"); _j = _src4.index("# ---------------------------------------------------------------- ドット絵の質感", _i)
exec(_src4[_i:_j])

def pix(name, png, rough=0.8, tint=None):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; b = nt.nodes["Principled BSDF"]
    tx = nt.nodes.new("ShaderNodeTexImage"); tx.image = bpy.data.images.load(os.path.join(S7.TEX, png + ".png")); tx.interpolation = "Closest"
    src = tx.outputs["Color"]
    if tint:
        mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = "RGBA"; mx.blend_type = "MULTIPLY"; mx.inputs["Factor"].default_value = 1.0
        nt.links.new(src, mx.inputs["A"]); mx.inputs["B"].default_value = (*tint, 1); src = mx.outputs["Result"]
    nt.links.new(src, b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = rough; b.inputs["Specular IOR Level"].default_value = 0.3
    bw = nt.nodes.new("ShaderNodeRGBToBW"); bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.5; bump.inputs["Distance"].default_value = 0.02
    nt.links.new(tx.outputs["Color"], bw.inputs[0]); nt.links.new(bw.outputs[0], bump.inputs["Height"]); nt.links.new(bump.outputs[0], b.inputs["Normal"])
    return fogify(m)
def P(name, col, rough=0.6, metal=0.0, emit=None, estr=0.0, sss=0.0):
    m = W.mat(name, col, rough, metal=metal, emit=emit, estr=estr, sss=sss); return fogify(m)
def E(name, col, s): return fogify(S7.emis(name, col, s))
def boxes(name, items, m):
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    for c, s in items:
        r = bmesh.ops.create_cube(bm, size=1.0)
        for v in r["verts"]: v.co = Vector((v.co.x * s[0], v.co.y * s[1], v.co.z * s[2])) + Vector(c)
    bm.to_mesh(me); bm.free(); o = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(o); me.materials.append(m); return o
def cyl(name, loc, r, depth, m, rot=(0, 0, 0), verts=32):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=depth, location=loc, rotation=rot)
    o = bpy.context.object; o.name = name; o.data.materials.append(m)
    for p in o.data.polygons: p.use_smooth = True
    return o
def imgmat(name, path, rough=0.7, emit=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; b = nt.nodes["Principled BSDF"]
    tx = nt.nodes.new("ShaderNodeTexImage"); tx.image = bpy.data.images.load(path)
    nt.links.new(tx.outputs["Color"], b.inputs["Base Color"]); b.inputs["Roughness"].default_value = rough
    nt.links.new(tx.outputs["Color"], b.inputs["Emission Color"]); b.inputs["Emission Strength"].default_value = emit
    return m
def card(name, path, w, h, rough=0.7):
    bpy.ops.mesh.primitive_plane_add(size=1.0); o = bpy.context.object; o.name = name
    o.scale = (w, h, 1); bpy.ops.object.transform_apply(scale=True)
    m = imgmat(name + "_m", path, rough); o.data.materials.append(m)
    so = o.modifiers.new("s", "SOLIDIFY"); so.thickness = 0.002
    return o, m

# ---------------------------------------------------------------- 部屋（ブロックの床・石の壁・窓・天井）
MAT = [pix("p_planks", "planks", 0.75, (0.75, 0.62, 0.5)), pix("p_stone", "stone", 0.85, (0.62, 0.62, 0.68)),
       pix("p_dark", "planks", 0.8, (0.32, 0.26, 0.22)), pix("p_log", "log_side", 0.8, (0.7, 0.6, 0.5))]
KINDS = {"floor": (0, 0, 0), "wall": (1, 1, 1), "ceil": (2, 2, 2), "post": (3, 3, 3)}
X0, X1, Y0, Y1, ZH = -6, 6, -3, 7, 4
WIN_X = (-4, -1, 2)                                                       # 奥の壁の窓（x, x+1 の2マス幅、z=1..2）
DOOR = (-6, 1)                                                            # 左の壁の扉（y=1..2, z=0..1）
cells = {}
for x in range(X0, X1):
    for y in range(Y0, Y1):
        cells[(x, y, -1)] = "floor"; cells[(x, y, ZH)] = "ceil"
for z in range(0, ZH):
    for x in range(X0 - 1, X1 + 1):
        if not (z in (1, 2) and any(wx <= x <= wx + 1 for wx in WIN_X)): cells[(x, Y1, z)] = "wall"
    for y in range(Y0, Y1):
        if not (z in (0, 1) and DOOR[1] <= y <= DOOR[1] + 1): cells[(X0 - 1, y, z)] = "wall"
        cells[(X1, y, z)] = "wall"
for x in (-5, 0, 5):
    for z in range(0, ZH): cells[(x, Y1 - 1, z)] = "post"
room = S7.voxel_mesh("room", cells, MAT, KINDS)
# 窓の外（夜は月の青 → 夜明けの金）
win_m = bpy.data.materials.new("winsky"); win_m.use_nodes = True; _wn = win_m.node_tree.nodes; _wn.clear()
_wo = _wn.new("ShaderNodeOutputMaterial"); WIN_E = _wn.new("ShaderNodeEmission"); win_m.node_tree.links.new(WIN_E.outputs[0], _wo.inputs[0])
sky = boxes("sky", [((0, Y1 + 3, 2), (30, 0.1, 10))], win_m); sky.visible_shadow = False
for wx in WIN_X:                                                          # 窓枠と格子
    boxes("wframe", [((wx + 1.0, Y1 + 0.5, 1.0), (2.0, 0.12, 0.08)), ((wx + 1.0, Y1 + 0.5, 3.0), (2.0, 0.12, 0.08)),
                     ((wx + 1.0, Y1 + 0.5, 2.0), (2.0, 0.08, 0.05)), ((wx + 1.0, Y1 + 0.5, 2.0), (0.05, 0.08, 2.0))], P("frame", (0.12, 0.09, 0.07), 0.6))
# 月光／朝日（窓から差しこむ平行光）
sun = bpy.data.lights.new("winlight", "SUN"); sun.angle = math.radians(2.0)
suno = bpy.data.objects.new("winlight", sun); bpy.context.collection.objects.link(suno)
suno.rotation_euler = (-Vector((0.25, -1.0, -0.55)).normalized()).to_track_quat("-Z", "Y").to_euler()
# 扉（記者がなだれこむ光）
door_m = P("door", (0.25, 0.17, 0.11), 0.7)
door = boxes("door", [((0.05, 1.0, 1.0), (0.1, 2.0, 2.0))], door_m); door.location = (X0, DOOR[1], 0)
hall, hallo = None, None
hall = bpy.data.lights.new("hall", "AREA"); hall.size = 2.0; hall.color = (1.0, 0.92, 0.8)
hallo = bpy.data.objects.new("hall", hall); bpy.context.collection.objects.link(hallo); hallo.location = (X0 - 1.5, DOOR[1] + 1.0, 1.0)
hallo.rotation_euler = (Vector((1, 0, 0))).to_track_quat("-Z", "Y").to_euler()

# ---------------------------------------------------------------- 作業台・文字盤・塗料
BY = 3.0                                                                  # 作業台の中心 y
bench_m = pix("p_bench", "planks", 0.6, (0.62, 0.45, 0.32))
boxes("bench", [((0, BY, 0.86), (7.0, 0.9, 0.08))] + [((x, BY + dy, 0.41), (0.1, 0.1, 0.82)) for x in (-3.4, -1.1, 1.1, 3.4) for dy in (-0.38, 0.38)], bench_m)
dial_img = bpy.data.images.load(os.path.join(TT, "dial.png")); mask_img = bpy.data.images.load(os.path.join(TT, "dial_mask.png"))
def dial_mat(name, glow):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; b = nt.nodes["Principled BSDF"]
    tx = nt.nodes.new("ShaderNodeTexImage"); tx.image = dial_img; mk = nt.nodes.new("ShaderNodeTexImage"); mk.image = mask_img
    nt.links.new(tx.outputs["Color"], b.inputs["Base Color"]); b.inputs["Roughness"].default_value = 0.35
    b.inputs["Emission Color"].default_value = (0.35, 1.0, 0.3, 1)
    mul = nt.nodes.new("ShaderNodeMath"); mul.operation = "MULTIPLY"; mul.inputs[1].default_value = glow
    nt.links.new(mk.outputs["Color"], mul.inputs[0]); nt.links.new(mul.outputs[0], b.inputs["Emission Strength"])
    return fogify(m), mul
DIAL_M, DIAL_K = dial_mat("dial", 6.0)
GREEN = E("radium", (0.35, 1.0, 0.3), 8.0); GREEN_K = [n for n in GREEN.node_tree.nodes if n.type == "EMISSION"][0].inputs["Strength"]
brass = P("brass", (0.75, 0.55, 0.25), 0.3, metal=1.0)
rnd = random.Random(5)
for gx in (-2.3, 0.0, 2.3):
    for i in range(4):
        for j in range(2):
            x = gx - 0.75 + i * 0.16 + rnd.uniform(-0.01, 0.01); y = BY - 0.3 + j * 0.14
            if i == 3 and j == 0: continue
            d = cyl("dial", (x + 0.35 * (i > 1), y, 0.905), 0.055, 0.012, DIAL_M); d.rotation_euler.z = rnd.uniform(0, 6.28)
    cyl("pot", (gx + 0.28, BY - 0.28, 0.94), 0.04, 0.08, P("pot", (0.85, 0.85, 0.8), 0.2))
    cyl("potpaint", (gx + 0.28, BY - 0.28, 0.981), 0.034, 0.004, GREEN)
# 天井のランプ（暗い作業場の小さな明かり）
lampm = P("lampshade", (0.1, 0.12, 0.1), 0.4, metal=0.6); bulb_m = E("bulb", (1.0, 0.72, 0.4), 18.0)
LAMPS = []
for lx in (-2.3, 0.0, 2.3):
    bpy.ops.mesh.primitive_cone_add(vertices=24, radius1=0.26, radius2=0.06, depth=0.2, location=(lx, BY, 2.35)); s_ = bpy.context.object; s_.data.materials.append(lampm)
    bpy.ops.object.modifier_add(type="SOLIDIFY"); s_.modifiers[-1].thickness = 0.01
    cyl("cord", (lx, BY, 3.2), 0.008, 1.6, lampm)
    b_ = bpy.ops.mesh.primitive_uv_sphere_add(radius=0.05, location=(lx, BY, 2.27)); bo = bpy.context.object; bo.data.materials.append(bulb_m)
    l = bpy.data.lights.new("lamp", "SPOT"); l.spot_size = math.radians(110); l.spot_blend = 0.6; l.shadow_soft_size = 0.06; l.color = (1.0, 0.72, 0.42)
    lo = bpy.data.objects.new("lamp", l); bpy.context.collection.objects.link(lo); lo.location = (lx, BY, 2.24); lo.rotation_euler = (0, 0, 0)
    LAMPS.append(l)
BULB_K = [n for n in bulb_m.node_tree.nodes if n.type == "EMISSION"][0].inputs["Strength"]
# 金庫（右奥の隅）
iron = P("iron", (0.08, 0.085, 0.09), 0.35, metal=0.9)
safe = boxes("safe", [((0, 0, 0.45), (0.8, 0.7, 0.9))], iron); safe.location = (4.6, 4.6, 0); safe.rotation_euler.z = math.radians(-35)
safe_in = boxes("safein", [((0, -0.36, 0.45), (0.66, 0.02, 0.76))], P("safein", (0.02, 0.02, 0.02), 0.9)); safe_in.parent = safe
sdoor = boxes("safedoor", [((0.34, -0.03, 0), (0.68, 0.06, 0.78))], iron); sdoor.parent = safe; sdoor.location = (-0.34, -0.37, 0.45)
cyl("dialknob", (0.34, -0.07, 0.05), 0.08, 0.04, brass, rot=(math.pi / 2, 0, 0)).parent = sdoor
# 報告書・新聞
report, rep_m = card("report", os.path.join(TT, "report.png"), 0.21, 0.3, 0.6)
news, news_m = card("news", os.path.join(TT, "news.png"), 0.6, 0.84, 0.75)
REP_B = rep_m.node_tree.nodes["Principled BSDF"]; REP_B.inputs["Emission Color"].default_value = (1.0, 0.8, 0.45, 1)
for o in (report, news): o.hide_render = True

# ---------------------------------------------------------------- 人物
face_em = []
def pbr(root, cmap):
    for o in [root] + list(root.children_recursive):
        if o.type != "MESH": continue
        for i, m in enumerate(o.data.materials):
            if not (m and m.node_tree): continue
            if "facemat" in m.name: face_em.extend(n for n in m.node_tree.nodes if n.type == "EMISSION"); continue
            rp = [n for n in m.node_tree.nodes if n.type == "VALTORGB"]
            if not rp: continue
            key = m.name.split("_")[-1]
            c = cmap.get(key) or tuple(x ** 0.4545 for x in rp[0].color_ramp.elements[1].color[:3])
            lin = tuple(x ** 2.2 for x in c); sk = "skin" in m.name; hr = "hair" in m.name
            nm = W.mat(m.name + "_pbr", lin, 0.5 if sk else (0.36 if hr else 0.78), sss=0.25 if sk else 0.0)
            b = nm.node_tree.nodes["Principled BSDF"]
            if hr: b.inputs["Coat Weight"].default_value = 0.25; b.inputs["Sheen Weight"].default_value = 0.4
            if key in ("blazer", "skirt", "pants"): b.inputs["Sheen Weight"].default_value = 0.6
            o.data.materials[i] = fogify(nm)
def face_to(o, p, tgt):
    o.location = p; d = Vector((tgt[0] - p[0], tgt[1] - p[1], 0)).normalized()
    o.rotation_euler = (0, 0, math.atan2(-d.x, d.y))
WORK = {"blazer": (0.42, 0.4, 0.36), "skirt": (0.36, 0.3, 0.26), "shirt": (0.86, 0.82, 0.74), "ribbon": (0.5, 0.36, 0.3), "sock": (0.25, 0.2, 0.18)}
CAMF = Vector((0.0, -1.0, 1.4))
HANA_P = Vector((0.0, BY + 0.62, 0.0))
hana, htex = T.girl("hana", tuple(HANA_P), hair=(0.32, 0.2, 0.12), face="hana", ponytail=True, arm_pose="chin")
face_to(hana, HANA_P, (0.0, -1.0)); pbr(hana, WORK)
H.upgrade(hana, "hana", [m for o in hana.children if o.name.startswith("hana_hair") for m in o.data.materials][0])
others = []
for k, (x, hc) in enumerate(((-2.3, (0.12, 0.09, 0.08)), (2.3, (0.45, 0.28, 0.14)))):
    g, gt = T.girl("w%d" % k, (x, BY + 0.62, 0), hair=hc, face="hana", ponytail=k == 0, arm_pose="chin")
    face_to(g, (x, BY + 0.62, 0), (x * 0.6, -1.0)); pbr(g, WORK)
    H.upgrade(g, "w%d" % k, [m for o in g.children if o.name.startswith("w%d_hair" % k) for m in o.data.materials][0], seed=7 + k)
    others.append((g, gt))
# 筆と、光る唇（夜光塗料）
def brush_for(root):
    b = cyl(root.name + "_brush", (0, 0, 0), 0.006, 0.17, P("brushw", (0.5, 0.35, 0.2), 0.5)); b.parent = root
    b.location = (0.035, 0.155, 1.3); b.rotation_euler = (math.radians(-25), math.radians(-30), 0)
    tip = cyl(root.name + "_tip", (0, 0, 0), 0.0045, 0.03, GREEN); tip.parent = root; tip.location = (0.012, 0.19, 1.37); tip.rotation_euler = b.rotation_euler
    lip = bpy.ops.mesh.primitive_uv_sphere_add(radius=0.012, location=(0, 0, 0)); lo = bpy.context.object; lo.name = root.name + "_lip"
    lo.data.materials.append(GREEN); lo.parent = root; lo.location = (0.0, 0.13, 1.385); lo.scale = (1.6, 0.35, 0.6)
    gl = bpy.data.lights.new(root.name + "_lipl", "POINT"); gl.color = (0.4, 1.0, 0.35); gl.shadow_soft_size = 0.02
    glo = bpy.data.objects.new(root.name + "_lipl", gl); bpy.context.collection.objects.link(glo); glo.parent = root; glo.location = (0.0, 0.2, 1.38)
    return b, tip, lo, gl
HB = brush_for(hana); OB = [brush_for(g) for g, _ in others]
# 工場長
BOSS_P = Vector((2.6, 1.3, 0.0))
boss, btex = T.boy("boss", tuple(BOSS_P), hair=(0.42, 0.42, 0.44), face="boss",
                   arms={"L": ((0.22, 0.04, 1.12), (0.12, 0.12, 0.98)), "R": ((-0.22, 0.04, 1.12), (-0.12, 0.12, 0.98))})
pbr(boss, {"blazer": (0.14, 0.13, 0.12), "pants": (0.12, 0.11, 0.1), "shirt": (0.9, 0.88, 0.82)})
musm = P("mustache", (0.25, 0.25, 0.26), 0.7)
for sx in (-1, 1):
    o = boxes("mus", [((sx * 0.03, 0, 0), (0.05, 0.018, 0.016))], musm); o.parent = boss; o.location = (0, 0.145, 1.535); o.rotation_euler.y = sx * 0.25
tie = boxes("tie", [((0, 0, 0), (0.032, 0.012, 0.17))], P("tie", (0.22, 0.03, 0.04), 0.5)); tie.parent = boss; tie.location = (0, 0.15, 1.3)
face_to(boss, BOSS_P, (0.0, 3.0))
# 時の裁判官トキモリ
TOKI_P = Vector((-1.25, 1.05, 0.0))
toki, ttex = T.girl("toki", tuple(TOKI_P), hair=(0.86, 0.86, 0.92), face="toki", ponytail=False,
                    arms={"L": ((0.2, 0.02, 1.0), (0.21, 0.06, 0.8)), "R": ((-0.2, 0.14, 1.1), (-0.1, 0.34, 1.22))})
pbr(toki, {"blazer": (0.04, 0.04, 0.05), "skirt": (0.05, 0.05, 0.06), "shirt": (0.92, 0.9, 0.86), "ribbon": (0.85, 0.62, 0.2), "sock": (0.04, 0.04, 0.05), "shoe": (0.05, 0.04, 0.04)})
H.upgrade(toki, "toki", [m for o in toki.children if o.name.startswith("toki_hair") for m in o.data.materials][0], seed=11)
coat_m = P("coat", (0.03, 0.03, 0.035), 0.55); gold = P("gold", (1.0, 0.72, 0.3), 0.22, metal=1.0)
bpy.ops.mesh.primitive_cone_add(vertices=48, radius1=0.34, radius2=0.19, depth=0.78, location=(0, 0, 0)); coat = bpy.context.object; coat.name = "toki_coat"
coat.data.materials.append(coat_m); coat.parent = toki; coat.location = (0, -0.01, 0.66)
for p_ in coat.data.polygons: p_.use_smooth = True
bpy.ops.object.modifier_add(type="SOLIDIFY"); coat.modifiers[-1].thickness = 0.012
trim = cyl("toki_trim", (0, 0, 0), 0.343, 0.025, gold, verts=48); trim.parent = toki; trim.location = (0, -0.01, 0.28)
watch = cyl("watch", (0, 0, 0), 0.05, 0.016, gold, rot=(math.pi / 2, 0, 0), verts=48); watch.parent = toki; watch.location = (-0.1, 0.39, 1.26)
wface_m = E("wface", (1.0, 0.8, 0.4), 4.0); WF_K = [n for n in wface_m.node_tree.nodes if n.type == "EMISSION"][0].inputs["Strength"]
wf = cyl("wface", (0, 0, 0), 0.042, 0.018, wface_m, rot=(math.pi / 2, 0, 0), verts=48); wf.parent = toki; wf.location = (-0.1, 0.392, 1.26)
wl = bpy.data.lights.new("watchl", "POINT"); wl.color = (1.0, 0.75, 0.35); wl.shadow_soft_size = 0.05
wlo = bpy.data.objects.new("watchl", wl); bpy.context.collection.objects.link(wlo); wlo.parent = toki; wlo.location = (-0.1, 0.48, 1.3)
TOKI_ALL = [toki] + list(toki.children_recursive)

# ---------------------------------------------------------------- 時が止まる金の輪・ほこり
shell_m = bpy.data.materials.new("shell"); shell_m.use_nodes = True; _sn = shell_m.node_tree.nodes; _sl = shell_m.node_tree.links.new; _sn.clear()
_so = _sn.new("ShaderNodeOutputMaterial"); _se = _sn.new("ShaderNodeEmission"); _st = _sn.new("ShaderNodeBsdfTransparent"); _sx = _sn.new("ShaderNodeMixShader")
_lw = _sn.new("ShaderNodeLayerWeight"); _lw.inputs["Blend"].default_value = 0.05
_sp = _sn.new("ShaderNodeMath"); _sp.operation = "MULTIPLY"; _sl(_lw.outputs["Facing"], _sp.inputs[0]); SHELL_K = _sp.inputs[1]; SHELL_K.default_value = 0.0
_se.inputs["Color"].default_value = (1.0, 0.7, 0.3, 1); _se.inputs["Strength"].default_value = 6.0
_sl(_sp.outputs[0], _sx.inputs[0]); _sl(_st.outputs[0], _sx.inputs[1]); _sl(_se.outputs[0], _sx.inputs[2]); _sl(_sx.outputs[0], _so.inputs["Surface"])
bpy.ops.mesh.primitive_uv_sphere_add(segments=64, ring_count=32, radius=1.0); shell = bpy.context.object; shell.name = "shell"; shell.data.materials.append(shell_m)
for p_ in shell.data.polygons: p_.use_smooth = True
shell.visible_shadow = False
for a in ("visible_diffuse", "visible_glossy"): setattr(shell, a, False)
dust_m = E("dust", (1.0, 0.85, 0.65), 3.0); gdust_m = E("gdust", (1.0, 0.75, 0.35), 12.0)
DUST = []; rd = random.Random(8)
for k in range(260):
    p = Vector((rd.uniform(-4, 5), rd.uniform(-1.5, 6), rd.uniform(0.2, 2.6)))
    o = boxes("dust", [((0, 0, 0), (1, 1, 1))], dust_m); o.visible_shadow = False
    DUST.append(dict(o=o, p=p, s=rd.uniform(0.004, 0.01), ph=rd.uniform(0, 6.28), v=Vector((rd.uniform(-0.04, 0.04), rd.uniform(-0.03, 0.03), rd.uniform(-0.02, 0.03)))))
GD = []                                                                  # トキモリの登場：集まる金の粒
for k in range(90):
    o = boxes("gd", [((0, 0, 0), (1, 1, 1))], gdust_m); o.visible_shadow = False
    a = rd.uniform(0, 6.28); r = rd.uniform(0.6, 1.8)
    GD.append(dict(o=o, a=a, r=r, z=rd.uniform(0.1, 1.9), s=rd.uniform(0.01, 0.022), dl=rd.uniform(0, 0.5)))
# フラッシュ（記者）
FL = []
for k, (dy, dz) in enumerate(((0.6, 1.6), (1.6, 1.9), (1.1, 1.4))):
    l = bpy.data.lights.new("flash", "POINT"); l.color = (0.92, 0.95, 1.0); l.shadow_soft_size = 0.1
    o = bpy.data.objects.new("flash", l); bpy.context.collection.objects.link(o); o.location = (X0 + 0.6, DOOR[1] + dy, dz); FL.append(l)
FLASH_T = [FLASH + x for x in (0.15, 0.5, 0.75, 1.3, 1.55, 2.2, 2.7)]
def flash_at(t):
    return sum(math.exp(-max(0.0, t - f) / 0.07) * (t >= f) for f in FLASH_T)

# ---------------------------------------------------------------- 補助光
def alight(name, col, size, loc, look, e=0.0):
    l = bpy.data.lights.new(name, "AREA"); l.size = size; l.color = col; l.energy = e
    o = bpy.data.objects.new(name, l); bpy.context.collection.objects.link(o); o.location = loc
    o.rotation_euler = (Vector(look) - Vector(loc)).to_track_quat("-Z", "Y").to_euler(); return l, o
key, keyo = alight("key", (0.7, 0.75, 1.0), 1.0, (0, 0, 0), (0, 1, 0))
rim, rimo = alight("rim", (0.5, 0.7, 1.0), 1.2, (0, 0, 0), (0, 1, 0))
bossl, bosslo = alight("bosslight", (1.0, 0.6, 0.35), 0.5, tuple(BOSS_P + Vector((0.2, 0.5, 2.6))), tuple(BOSS_P + Vector((0, 0, 1.4))))

cam = W.camera((0, -1, 1.4), (0, 3, 1.2), lens=35, fstop=2.0)
cam.data.dof.aperture_blades = 7

# ---------------------------------------------------------------- 時間ごとの値
def stop_at(t): return 1.0 if STOPT <= t < FLASH else 0.0          # 世界が止まっている（工場長とトキモリだけ動ける）
def dawn_at(t): return ease((t - DAWN + 0.6) / 2.2)
def toki_vis(t): return t >= STOPT + 0.45
def boss_drop(t): return 0.42 * ease((t - (FLASH + 2.2)) / 0.5)    # ひざから崩れる
def head(o, z=1.45): return o.location + Vector((0, 0, z))
TH = lambda: head(toki, 1.44); BH = lambda: head(boss, 1.56); HH = lambda: head(hana, 1.4)
T_NOW = 0.0
BOSS_LOOK0 = Vector((0.4, 3.4, 0))                                        # 工場長はまず少女たちを見下ろす
def fwd(o):
    a = o.rotation_euler.z; return Vector((-math.sin(a), math.cos(a), 0.0))
def side(o): f = fwd(o); return Vector((f.y, -f.x, 0.0))
SAFE_OPEN = REPORT - 0.9
def report_pos(t):
    a = safe.matrix_world @ Vector((0, -0.2, 0.55)); b = TOKI_P + fwd(toki) * 0.8 - side(toki) * 0.32 + Vector((0, 0, 1.3)); u = ease((t - REPORT) / 1.6)
    p = a.lerp(b, u) + Vector((0, 0, 0.35 * math.sin(math.pi * u)))
    return p + Vector((0, 0, 0.015 * math.sin(t * 2.2)))
def news_pos(t, campos, camlook):
    u = ease((t - FLASH - 0.4) / 1.4)
    a = Vector((-0.6, 3.0, 2.0)); fw = (camlook - campos).normalized()
    b = campos + fw * 0.72
    return a.lerp(b, u), u

def shot(t):
    """(開始, カメラ位置関数, 見る先関数, レンズ, F値)"""
    hf = HANA_P
    S = [
        (0.0, lambda t: hf + Vector((0.3 - 0.04 * t / 3, -1.0 + 0.08 * t / 3, 1.38)), lambda t: hf + Vector((0.0, -0.1, 1.37)), 50, 1.8),
        (3.0, lambda t: hf + Vector((0.5 + 0.03 * (t - 3), -0.75, 1.05)), lambda t: BH() + Vector((0, 0, -0.12)), 48, 2.4),
        (6.8, lambda t: hf + Vector((0.08, -0.95 + 0.05 * (t - 6.8) / 3, 1.42)), lambda t: HH() + Vector((0, 0, -0.02)), 52, 1.8),
        (10.0, lambda t: boss.location + fwd(boss) * (0.95 - 0.02 * (t - 10)) + side(boss) * 0.18 + Vector((0, 0, 1.5)), lambda t: BH(), 48, 2.0),
        (STOPT, lambda t: Vector((-0.4, -2.2 + 0.25 * (t - STOPT), 2.3)), lambda t: Vector((0.3, 2.6, 1.0)), 18, 5.6),
        (13.0, lambda t: TOKI_P + fwd(toki) * (1.15 - 0.05 * (t - 13)) + side(toki) * 0.55 + Vector((0, 0, 0.75)), lambda t: TH(), 30, 2.2),
        (15.6, lambda t: TOKI_P - fwd(toki) * (0.95 - 0.06 * (t - 15.6)) - side(toki) * 0.3 + Vector((0, 0, 1.58)), lambda t: (report_pos(t) if t > REPORT - 0.2 else BH()).lerp(BH(), 0.55), 30, 4.0),
        (19.8, lambda t: boss.location + fwd(boss) * 0.85 - side(boss) * 0.15 + Vector((0, 0, 1.52)), lambda t: BH(), 52, 2.0),
        (FLASH, lambda t: Vector((0.3, -1.2, 1.55)), lambda t: Vector((0.0, 1.6, 1.3)), 24, 4.0),
        (VERDICT, lambda t: TOKI_P + fwd(toki) * 0.8 + side(toki) * 0.12 + Vector((0, 0, 1.45)), lambda t: TH() + Vector((0, 0, -0.03)), 50, 1.8),
        (STAMP, lambda t: boss.location + fwd(boss) * 1.5 + side(boss) * 0.4 + Vector((0, 0, 1.0)), lambda t: BH() + Vector((0, 0, -0.15)), 35, 3.2),
        (DAWN, lambda t: hf + Vector((0.12, -1.0, 1.43)), lambda t: HH(), 50, 1.8),
        (FACT, lambda t: Vector((0.2, -1.6 - 0.12 * (t - FACT), 1.7)), lambda t: Vector((0.0, 3.2, 1.3)), 24, 4.0),
    ]
    i = max(j for j, s in enumerate(S) if s[0] <= t)
    st, pf, lf, lens, fs = S[i]
    pos, look = pf(t), lf(t)
    if i == 5: lens = 30 + 8 * ease((t - 13.0) / 2.6)
    if i == 9: lens = 50 + 6 * ease((t - VERDICT) / 2.5)
    sh = 0.0
    for a, amp, d in ((STOPT, 0.03, 0.5), (19.9, 0.02, 0.8), (FLASH, 0.025, 0.6), (STAMP, 0.05, 0.5)):
        if a <= t < a + d: sh = max(sh, amp * (1 - (t - a) / d))
    if stop_at(t) == 0: pos = pos + Vector((0.004 * math.sin(t * 1.3), 0.003 * math.sin(t * 0.9), 0.004 * math.sin(t * 1.7)))
    pos = pos + Vector((sh * math.sin(t * 47), sh * math.sin(t * 39), sh * math.sin(t * 53)))
    if "--camover" in sys.argv:
        v = [float(x) for x in arg("--camover", "").split(",")]; pos = Vector(v[0:3]); look = Vector(v[3:6]); lens = v[6]
    return pos, look, lens, fs, i

def talking(who, t):
    return any(l[0] <= t <= l[1] - 0.05 for l in LINES if l[5] == who)
def flap(t): return int(t * 12) % 3 != 2
def expr_hana(t):
    tk = talking("hana", t) and flap(t)
    if t < 6.8: e = "talk" if tk else "base"
    elif t < DAWN: e = "tearsadtalk" if tk else "tearsad"
    elif t < 30.8: e = "tearsmiletalk" if tk else "tearsmile"
    else: e = "smile"
    if stop_at(t): e = {"talk": "base"}.get(e, e)
    if (t % 3.3) < 0.12 and not tk and e in ("base", "smile") and not stop_at(t): e = "blink"
    return e
def expr_boss(t):
    tk = talking("boss", t) and flap(t)
    if t < 19.8: e = "coldtalk" if tk else "cold"
    elif t < STAMP: e = "shock" if tk else "shockc"
    else: e = "sad"
    return e
def expr_toki(t):
    tk = talking("toki", t) and flap(t)
    e = "coldtalk" if tk else "cold"
    if STAMP + 0.4 < t: e = "base"
    if (t % 3.7) < 0.12 and not tk: e = "blink"
    return e

def place(t):
    global T_NOW; T_NOW = t
    st = stop_at(t); dn = dawn_at(t); vis = toki_vis(t)
    tf = t if t < STOPT else (STOPT if t < FLASH else t - (FLASH - STOPT))      # 止まっている間は世界の時計を止める
    # 光の量
    night = 1.0 - dn
    sun.color = Vector((0.45, 0.6, 1.0)).lerp(Vector((1.0, 0.66, 0.38)), dn)[:]; sun.energy = 0.6 * night + 5.5 * dn
    WIN_E.inputs["Color"].default_value = (*Vector((0.05, 0.08, 0.2)).lerp(Vector((1.0, 0.62, 0.32)), dn), 1); WIN_E.inputs["Strength"].default_value = 1.0 + 5.0 * dn
    for l in LAMPS: l.energy = (55.0 + 4.0 * math.sin(tf * 7.0)) * (1 - 0.6 * dn)
    BULB_K.default_value = 18.0 * (1 - 0.6 * dn)
    glow = 8.0 * (1.0 if t < DAWN else 0.5)
    GREEN_K.default_value = glow; DIAL_K.inputs[1].default_value = 6.0 if t < DAWN else 3.0
    for b, tip, lip, gl in [HB] + OB:
        gl.energy = 0.25 * (1.0 if t < 12 else 0.4)
        b.hide_render = tip.hide_render = t >= FLASH
    HB[2].hide_render = not (t < 12.0)
    for b, tip, lip, gl in OB: lip.hide_render = t >= FLASH
    FOG.nodes["fogcol"].inputs["Color"].default_value = (*Vector((0.02, 0.03, 0.05)).lerp(Vector((0.55, 0.38, 0.26)), dn), 1)
    FOG.nodes["dens"].outputs[0].default_value = 0.05 - 0.025 * dn
    for n in face_em: n.inputs["Strength"].default_value = 0.9 + 0.2 * dn
    # 扉と記者のフラッシュ
    door.rotation_euler.z = -math.radians(100) * ease((t - FLASH) / 0.35)
    hall.energy = 600.0 * ease((t - FLASH) / 0.3) * (1 - 0.7 * dn)
    fa = flash_at(t)
    for l in FL: l.energy = 3500.0 * fa
    # 人物
    hana.hide_render = False
    toki_on = vis
    for o in TOKI_ALL:
        if o.type in ("MESH", "LIGHT"): o.hide_render = not toki_on
    face_to(toki, TOKI_P, BOSS_P if t < STAMP + 0.6 else (0.0, -1.0))
    WF_K.default_value = 4.0 + 20.0 * math.exp(-max(0.0, t - STOPT) / 0.3) * (t >= STOPT) + 14.0 * math.exp(-max(0.0, t - STAMP) / 0.25) * (t >= STAMP)
    wl.energy = 3.0 + 40.0 * math.exp(-max(0.0, t - STOPT) / 0.4) * (t >= STOPT)
    bz = boss_drop(t)
    face_to(boss, BOSS_P, BOSS_LOOK0 if t < 15.2 else TOKI_P)
    boss.location.z = -bz; boss.rotation_euler.x = -0.15 * ease((t - (FLASH + 2.2)) / 0.5)
    # 時を止める金の殻
    u = (t - STOPT) / 0.9
    shell.hide_render = not (0 <= u < 1.0)
    if not shell.hide_render:
        shell.location = TOKI_P + Vector((0, 0, 1.2)); r = 0.2 + 9.0 * ease(u); shell.scale = (r, r, r); SHELL_K.default_value = 0.55 * (1 - u)
    # 金庫・報告書
    sdoor.rotation_euler.z = -math.radians(115) * ease((t - SAFE_OPEN) / 0.7)
    report.hide_render = not (REPORT - 0.2 <= t < FLASH + 0.4)
    if not report.hide_render:
        p = report_pos(t); report.location = p
        cp = cam.location; d = (cp - p).normalized()
        report.rotation_euler = d.to_track_quat("Z", "Y").to_euler(); report.rotation_euler.rotate_axis("Z", 0.08 * math.sin(t * 1.7))
        REP_B.inputs["Emission Strength"].default_value = 0.6 + 1.6 * math.exp(-max(0.0, t - REPORT) / 0.6)
    # 粒
    for d in DUST:
        o = d["o"]; p = d["p"] + d["v"] * tf + Vector((0.03 * math.sin(tf * 0.7 + d["ph"]), 0.03 * math.cos(tf * 0.5 + d["ph"]), 0.02 * math.sin(tf + d["ph"])))
        o.location = p; s = d["s"] * (1.6 if st else 1.0); o.scale = (s, s, s); o.rotation_euler = (tf + d["ph"], tf * 0.7, 0)
    for g in GD:
        k = (t - STOPT - g["dl"]) / 0.7
        o = g["o"]; o.hide_render = not (0 <= k < 1.15)
        if o.hide_render: continue
        r = g["r"] * (1 - ease(k)); a = g["a"] + 2.5 * k
        o.location = TOKI_P + Vector((r * math.cos(a), r * math.sin(a), g["z"] + (1.0 - g["z"]) * 0.3 * ease(k)))
        o.scale = (g["s"] * (1 - ease((k - 0.9) / 0.25)),) * 3
    # 補助光（ショットごと）
    pos, look, lens, fs, si = shot(t)
    keyo.location = pos + Vector((-0.6, 0.2, 0.5)); keyo.rotation_euler = (look - keyo.location).to_track_quat("-Z", "Y").to_euler()
    key.energy = 14.0; key.color = Vector((0.7, 0.75, 1.0)).lerp(Vector((1.0, 0.82, 0.65)), dn)[:]
    rimo.location = look + (look - pos).normalized() * 1.0 + Vector((0.4, 0, 0.5)); rimo.rotation_euler = (look - rimo.location).to_track_quat("-Z", "Y").to_euler()
    rim.energy = 30.0 * (1 - dn) + (25.0 if si in (5, 9) else 0.0); rim.color = (0.55, 0.7, 1.0) if si not in (5, 9) else (1.0, 0.75, 0.4)
    bossl.energy = 60.0 * (1 - dn)
    cam.location = pos; W.aim(cam, look); cam.data.lens = lens; cam.data.dof.aperture_fstop = fs
    bpy.context.view_layer.update()
    cam.data.dof.focus_distance = max(0.25, (look - pos).length)
    # 新聞（カメラに向かって飛んでくる）
    news.hide_render = not (FLASH + 0.4 <= t < VERDICT)
    if not news.hide_render:
        p, u = news_pos(t, pos, look); news.location = p
        news.rotation_euler = (pos - p).normalized().to_track_quat("Z", "Y").to_euler(); news.rotation_euler.rotate_axis("Z", (1 - u) * 6.0)
        if u >= 1.0: news.rotation_euler.rotate_axis("Z", 0.03 * math.sin(t * 2))
        cam.data.dof.focus_distance = (p - pos).length if u > 0.6 else cam.data.dof.focus_distance
    T.set_expr(htex, "hana", expr_hana(t)); T.set_expr(btex, "boss", expr_boss(t)); T.set_expr(ttex, "toki", expr_toki(t))
    for g, gt in others: T.set_expr(gt, "hana", "sad" if t < DAWN else "smile")
    return dict(stop=st, dawn=dn, flash=fa, shot=si)

frames = TEST or range(START, STOP)
t0 = time.time()
for f in frames:
    p = os.path.join(OUT, "%04d.png" % (f + 1))
    if os.path.exists(p) and not TEST: continue
    t = f / FPS
    meta = place(t)
    bpy.context.view_layer.update()
    wc = Vector((-0.5, Y1 + 2.0, 2.2)); sv = world_to_camera_view(sc, cam, wc)        # 窓からの光の筋（後処理）
    meta.update(t=t, sun=[sv.x, sv.y, sv.z], light=0.25 + 0.75 * meta["dawn"])
    json.dump(meta, open(p[:-4] + ".json", "w"))
    tmp = p[:-4] + "_tmp.png"; sc.render.filepath = tmp
    bpy.ops.render.render(write_still=True); os.replace(tmp, p)
    print("frame %s t=%.2f %.1fs" % (p, t, time.time() - t0), flush=True); t0 = time.time()
