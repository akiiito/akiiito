"""
create_toki3.py ― 「その罪、時効にさせない」第3話『アイスピック』（夜の手術室 → 時が止まる → 成敗バトル → 窓の外へ → 夜明け）
  python create_toki1.py [--samples 18] [--res 0.75] [--start 0] [--end 840] [--test 0,140,...]
  実話（1940〜50年代米国の経眼窩ロボトミー）をもとにしたフィクション。医師・病院は架空。会社名・人物は架空。
"""
import os, sys, math, json, time, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, bmesh
from mathutils import Vector, Matrix
from bpy_extras.object_utils import world_to_camera_view
import s2_world as W, s3_toon as T, s7_world as S7, blk_hair as H
from toki3_timing import *

HERE = os.path.dirname(os.path.abspath(__file__))
arg = lambda k, d: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
SAMPLES = int(arg("--samples", "18")); FPS = 24; N = int(END * FPS)
RS = float(arg("--res", "0.75"))
START = int(arg("--start", "0")); STOP = int(arg("--end", str(N)))
TEST = [int(x) for x in arg("--test", "").split(",") if x]
OUT = os.path.join(HERE, "frames_TOKI3" + ("_test" if TEST else "")); os.makedirs(OUT, exist_ok=True)
LINES = json.load(open(os.path.join(HERE, "toki3_lines.json"), encoding="utf-8"))
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
MAT = [pix("p_planks", "stone", 0.5, (0.42, 0.55, 0.52)), pix("p_stone", "stone", 0.6, (0.85, 0.9, 0.9)),
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
sky = boxes("sky", [((0, Y1 + 30, 6), (90, 0.1, 30))], win_m); sky.visible_shadow = False
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


# ---------------------------------------------------------------- 手術室の小道具
rnd = random.Random(5)
steel = P("steel", (0.7, 0.72, 0.75), 0.25, metal=1.0); white = P("whitecoat", (0.92, 0.93, 0.95), 0.6)
glass_m = bpy.data.materials.new("glass"); glass_m.use_nodes = True; _gb = glass_m.node_tree.nodes["Principled BSDF"]
_gb.inputs["Transmission Weight"].default_value = 1.0; _gb.inputs["Roughness"].default_value = 0.05; _gb.inputs["Base Color"].default_value = (0.85, 0.95, 1.0, 1)
OUTY = Y1 + 1
boxes("yard", [((0, OUTY + 10, -0.5), (40, 20, 1.0))], pix("p_yard", "grass_top", 0.9, (0.5, 0.55, 0.5)))
for k in range(8):
    h = rnd.uniform(5, 10); boxes("bld", [((-16 + k * 4.5, OUTY + 16 + rnd.uniform(0, 4), h / 2), (3.5, 3, h))], pix("p_bld", "stone", 0.9, (0.3, 0.3, 0.33)))
yardl = bpy.data.lights.new("yardl", "POINT"); yardl.color = (0.6, 0.7, 1.0); yardl.shadow_soft_size = 0.5
yardlo = bpy.data.objects.new("yardl", yardl); bpy.context.collection.objects.link(yardlo); yardlo.location = (0.5, OUTY + 4.5, 3.0)
# 窓ガラス（真ん中の窓は割れる）
PANES = []
for wx in WIN_X:
    o = boxes("pane", [((wx + 1.0, Y1 + 0.5, 2.0), (1.96, 0.03, 1.96))], glass_m); PANES.append(o)
MIDWIN = [o for o in bpy.data.objects if o.name.startswith("wframe")][1]
SHARDS = []
for k in range(60):
    o = boxes("shard", [((0, 0, 0), (1, 1, 1))], glass_m); s_ = rnd.uniform(0.04, 0.16)
    SHARDS.append(dict(o=o, p=Vector((rnd.uniform(-0.95, 0.95), Y1 + 0.5, rnd.uniform(1.05, 2.95))), v=Vector((rnd.uniform(-1.5, 1.5), rnd.uniform(2, 6), rnd.uniform(-0.5, 2.5))),
                       w=Vector((rnd.uniform(-9, 9), rnd.uniform(-9, 9), rnd.uniform(-9, 9))), s=(s_, 0.01, s_ * rnd.uniform(0.5, 1.5))))
# 無影灯と手術台（立てた台にベルトで固定）
MIO_P = Vector((-2.2, 4.4, 0.0))
lampdisk = cyl("oplamp", (MIO_P.x + 0.4, MIO_P.y - 0.6, 2.6), 0.42, 0.12, steel, verts=48)
lampglow = cyl("oplampglow", (MIO_P.x + 0.4, MIO_P.y - 0.6, 2.535), 0.36, 0.01, E("oplampe", (1.0, 0.97, 0.9), 12.0), verts=48)
OPL_K = [n for n in lampglow.data.materials[0].node_tree.nodes if n.type == "EMISSION"][0].inputs["Strength"]
opl = bpy.data.lights.new("opspot", "SPOT"); opl.spot_size = math.radians(60); opl.spot_blend = 0.4; opl.shadow_soft_size = 0.35; opl.color = (1.0, 0.97, 0.92)
oplo = bpy.data.objects.new("opspot", opl); bpy.context.collection.objects.link(oplo); oplo.location = (MIO_P.x + 0.4, MIO_P.y - 0.6, 2.5)
oplo.rotation_euler = (MIO_P + Vector((0, 0, 1.3)) - oplo.location).to_track_quat("-Z", "Y").to_euler()
boxes("board", [((MIO_P.x, MIO_P.y + 0.2, 0.95), (0.7, 0.08, 1.9))], P("board", (0.35, 0.42, 0.4), 0.6))
STRAPS = []
for z, w in ((1.2, 0.46), (0.75, 0.42), (0.35, 0.36)):
    o = boxes("strap", [((0, 0, 0), (w, 0.06, 0.07))], P("strap", (0.25, 0.15, 0.08), 0.6)); o.location = MIO_P + Vector((0, 0.12, z)); STRAPS.append(dict(o=o, p0=Vector(o.location)))
boxes("tray", [((MIO_P.x + 1.0, MIO_P.y - 0.5, 0.9), (0.5, 0.35, 0.03)), ((MIO_P.x + 1.0, MIO_P.y - 0.5, 0.45), (0.04, 0.04, 0.9))], steel)
# 戸棚（ガラス戸・薬びん）
CAB_X = X1 - 0.35
for k in range(3):
    y0 = 2.0 + k * 1.1
    boxes("cab", [((CAB_X, y0, 0.9), (0.6, 1.0, 1.8))], P("cabwood", (0.75, 0.78, 0.78), 0.5))
    boxes("cabglass", [((CAB_X - 0.31, y0, 1.25), (0.02, 0.9, 0.9))], glass_m)
    for j in range(5):
        cyl("bottle", (CAB_X - 0.15, y0 - 0.35 + j * 0.17, 1.02 + 0.45 * (j % 2)), 0.04, 0.16, P("btl%d" % j, (0.3 + 0.1 * j, 0.6, 0.5 - 0.08 * j), 0.2))
CSHARD = []
for k in range(36):
    o = boxes("cshard", [((0, 0, 0), (1, 1, 1))], glass_m); s_ = rnd.uniform(0.04, 0.12)
    CSHARD.append(dict(o=o, off=Vector((0, rnd.uniform(-0.5, 0.5), rnd.uniform(0.8, 1.7))), v=Vector((rnd.uniform(-3, -0.5), rnd.uniform(-2, 2), rnd.uniform(0, 3))),
                       w=Vector((rnd.uniform(-9, 9), rnd.uniform(-9, 9), rnd.uniform(-9, 9))), s=(0.01, s_, s_)))
# 天井の明かり（暗い夜の病院）
LAMPS = []
for lx, ly in ((-2.0, 1.5), (2.0, 1.5), (0.0, 5.0)):
    l = bpy.data.lights.new("lamp", "AREA"); l.size = 0.8; l.color = (0.85, 0.95, 1.0)
    lo = bpy.data.objects.new("lamp", l); bpy.context.collection.objects.link(lo); lo.location = (lx, ly, ZH - 0.05); LAMPS.append(l)

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
def fwd(o):
    a = o.rotation_euler.z; return Vector((-math.sin(a), math.cos(a), 0.0))
def side(o): f = fwd(o); return Vector((f.y, -f.x, 0.0))
def hairmat(root, nm): return [m for o in root.children if o.name.startswith(nm + "_hair") for m in o.data.materials][0]
mio, mtex = T.girl("mio", tuple(MIO_P), hair=(0.12, 0.1, 0.12), face="mio", ponytail=False)
face_to(mio, MIO_P, (MIO_P.x, -2.0)); pbr(mio, {"blazer": (0.75, 0.78, 0.8), "skirt": (0.7, 0.72, 0.75), "shirt": (0.9, 0.9, 0.9), "ribbon": (0.6, 0.65, 0.7), "sock": (0.8, 0.8, 0.8)})
H.upgrade(mio, "mio", hairmat(mio, "mio"))
# 医者（白衣・額帯鏡・アイスピック）
DOC_P = Vector((-1.25, 4.0, 0.0))
DPOSE = {"idle": {"L": ((0.22, 0.06, 1.12), (0.14, 0.24, 1.05)), "R": ((-0.22, 0.08, 1.12), (-0.12, 0.26, 1.15))},
         "raise": {"L": ((0.22, 0.06, 1.12), (0.14, 0.24, 1.05)), "R": ((-0.2, 0.2, 1.32), (-0.08, 0.42, 1.5))},
         "lunge": {"L": ((0.22, -0.05, 1.12), (0.25, -0.1, 0.95)), "R": ((-0.18, 0.3, 1.32), (-0.08, 0.6, 1.36))},
         "beg": {"L": ((0.22, 0.12, 1.2), (0.12, 0.3, 1.42)), "R": ((-0.22, 0.12, 1.2), (-0.12, 0.3, 1.42))}}
DM = {}
for k, arms in DPOSE.items():
    nm = "doc" if k == "idle" else "doc" + k
    r_, tx_ = T.boy(nm, tuple(DOC_P), hair=(0.18, 0.17, 0.18), face="doc", arms=arms)
    pbr(r_, {"blazer": (0.9, 0.91, 0.93), "pants": (0.25, 0.25, 0.28), "shirt": (0.6, 0.7, 0.75)})
    bpy.ops.mesh.primitive_cone_add(vertices=40, radius1=0.3, radius2=0.18, depth=0.62); c_ = bpy.context.object; c_.name = nm + "_coat"
    c_.data.materials.append(white); c_.parent = r_; c_.location = (0, 0, 0.62)
    for p_ in c_.data.polygons: p_.use_smooth = True
    mir = cyl(nm + "_mirror", (0, 0, 0), 0.045, 0.01, steel, rot=(math.pi / 2, 0, 0)); mir.parent = r_; mir.location = (0, 0.13, 1.66)
    for sx in (-1, 1):
        g_ = boxes(nm + "_glass", [((0, 0, 0), (0.06, 0.012, 0.035))], P("lens", (0.05, 0.05, 0.07), 0.1)); g_.parent = r_; g_.location = (sx * 0.05, 0.146, 1.585)
    hand = Vector(arms["R"][1])
    if k in ("idle", "raise", "lunge"):
        pk = cyl(nm + "_pick", (0, 0, 0), 0.006, 0.26, steel); pk.parent = r_; pk.location = hand + Vector((0, 0.08, 0.05)); pk.rotation_euler = (math.radians(-70), 0, 0)
    DM[k] = (r_, tx_, [r_] + list(r_.children_recursive))
# トキモリ（懐中時計／右ストレート）
coat_m = P("coat", (0.03, 0.03, 0.035), 0.55); gold = P("gold", (1.0, 0.72, 0.3), 0.22, metal=1.0)
wface_m = E("wface", (1.0, 0.8, 0.4), 4.0); WF_K = [n for n in wface_m.node_tree.nodes if n.type == "EMISSION"][0].inputs["Strength"]
fist_m = E("fist", (1.0, 0.7, 0.3), 0.0); FIST_K = [n for n in fist_m.node_tree.nodes if n.type == "EMISSION"][0].inputs["Strength"]
TOKI_P = Vector((0.7, 1.5, 0.0))
TCOL = {"blazer": (0.04, 0.04, 0.05), "skirt": (0.05, 0.05, 0.06), "shirt": (0.92, 0.9, 0.86), "ribbon": (0.85, 0.62, 0.2), "sock": (0.04, 0.04, 0.05), "shoe": (0.05, 0.04, 0.04)}
POSES = {"idle": {"L": ((0.2, 0.02, 1.0), (0.21, 0.06, 0.8)), "R": ((-0.2, 0.14, 1.1), (-0.1, 0.34, 1.22))},
         "punch": {"L": ((0.2, -0.06, 1.12), (0.12, 0.1, 1.2)), "R": ((-0.16, 0.28, 1.3), (-0.08, 0.54, 1.32))}}
TM = {}
for k, arms in POSES.items():
    nm = "toki" if k == "idle" else "toki" + k
    r_, tx_ = T.girl(nm, tuple(TOKI_P), hair=(0.86, 0.86, 0.92), face="toki", ponytail=False, arms=arms)
    pbr(r_, TCOL); H.upgrade(r_, nm, hairmat(r_, nm), seed=11)
    bpy.ops.mesh.primitive_cone_add(vertices=48, radius1=0.34, radius2=0.19, depth=0.78); c_ = bpy.context.object; c_.name = nm + "_coat"
    c_.data.materials.append(coat_m); c_.parent = r_; c_.location = (0, -0.01, 0.66)
    for p_ in c_.data.polygons: p_.use_smooth = True
    bpy.ops.object.modifier_add(type="SOLIDIFY"); c_.modifiers[-1].thickness = 0.012
    tr_ = cyl(nm + "_trim", (0, 0, 0), 0.343, 0.025, gold, verts=48); tr_.parent = r_; tr_.location = (0, -0.01, 0.28)
    hand = Vector(arms["R"][1])
    if k == "idle":
        w_ = cyl(nm + "_watch", (0, 0, 0), 0.05, 0.016, gold, rot=(math.pi / 2, 0, 0), verts=48); w_.parent = r_; w_.location = hand + Vector((0, 0.05, 0.04))
        f_ = cyl(nm + "_wface", (0, 0, 0), 0.042, 0.018, wface_m, rot=(math.pi / 2, 0, 0), verts=48); f_.parent = r_; f_.location = hand + Vector((0, 0.052, 0.04))
    else:
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.07); g_ = bpy.context.object; g_.name = nm + "_aura"; g_.data.materials.append(fist_m); g_.parent = r_; g_.location = hand; g_.visible_shadow = False
    TM[k] = (r_, tx_, [r_] + list(r_.children_recursive))
wl = bpy.data.lights.new("watchl", "POINT"); wl.color = (1.0, 0.75, 0.35); wl.shadow_soft_size = 0.05
wlo = bpy.data.objects.new("watchl", wl); bpy.context.collection.objects.link(wlo)
# 金の鎖・巨大な時計の針・文字盤
chain_m = E("chain", (1.0, 0.6, 0.15), 14.0)
CHAINL = []
for k in range(40):
    bpy.ops.mesh.primitive_torus_add(major_radius=0.075, minor_radius=0.02, major_segments=16, minor_segments=6); o = bpy.context.object; o.data.materials.append(chain_m); o.visible_shadow = False
    CHAINL.append(o)
hand_m = E("bighand", (1.0, 0.5, 0.1), 8.0); BH_K = [n for n in hand_m.node_tree.nodes if n.type == "EMISSION"][0].inputs["Strength"]
def blade(name, L, w):
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    vs = [bm.verts.new(v) for v in ((-w, 0, 0), (w, 0, 0), (w * 0.6, 0, L * 0.85), (0, 0, L), (-w * 0.6, 0, L * 0.85))]
    bm.faces.new(vs); bm.to_mesh(me); bm.free(); o = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(o); me.materials.append(hand_m)
    so = o.modifiers.new("s", "SOLIDIFY"); so.thickness = 0.04; o.visible_shadow = False; return o
hour = blade("hourhand", 1.6, 0.18); minute = blade("minutehand", 2.4, 0.12)
dial = bpy.data.objects.new("bigdial", None); bpy.context.collection.objects.link(dial)
bpy.ops.mesh.primitive_torus_add(major_radius=2.2, minor_radius=0.05, major_segments=96, minor_segments=8); ringd = bpy.context.object; ringd.data.materials.append(hand_m); ringd.parent = dial; ringd.rotation_euler = (math.pi / 2, 0, 0)
for k in range(12):
    a = k * math.pi / 6; o = boxes("tick", [((0, 0, 0), (0.06, 0.04, 0.32 if k % 3 == 0 else 0.18))], hand_m); o.parent = dial
    o.location = (2.0 * math.sin(a), 0, 2.0 * math.cos(a)); o.rotation_euler = (0, a, 0)
DIAL_ALL = [ringd] + [o for o in dial.children]

# ---------------------------------------------------------------- 時を止める金の殻・衝撃・ほこり
shell_m = bpy.data.materials.new("shell"); shell_m.use_nodes = True; _sn = shell_m.node_tree.nodes; _sl = shell_m.node_tree.links.new; _sn.clear()
_so = _sn.new("ShaderNodeOutputMaterial"); _se = _sn.new("ShaderNodeEmission"); _st = _sn.new("ShaderNodeBsdfTransparent"); _sx = _sn.new("ShaderNodeMixShader")
_lw = _sn.new("ShaderNodeLayerWeight"); _lw.inputs["Blend"].default_value = 0.05
_sp = _sn.new("ShaderNodeMath"); _sp.operation = "MULTIPLY"; _sl(_lw.outputs["Facing"], _sp.inputs[0]); SHELL_K = _sp.inputs[1]; SHELL_K.default_value = 0.0
_se.inputs["Color"].default_value = (1.0, 0.7, 0.3, 1); _se.inputs["Strength"].default_value = 6.0
_sl(_sp.outputs[0], _sx.inputs[0]); _sl(_st.outputs[0], _sx.inputs[1]); _sl(_se.outputs[0], _sx.inputs[2]); _sl(_sx.outputs[0], _so.inputs["Surface"])
bpy.ops.mesh.primitive_uv_sphere_add(segments=64, ring_count=32, radius=1.0); shell = bpy.context.object; shell.data.materials.append(shell_m); shell.visible_shadow = False
for a in ("visible_diffuse", "visible_glossy"): setattr(shell, a, False)
hitl = bpy.data.lights.new("hitl", "POINT"); hitl.color = (1.0, 0.82, 0.5); hitl.shadow_soft_size = 0.2
hitlo = bpy.data.objects.new("hitl", hitl); bpy.context.collection.objects.link(hitlo)
dust_m = E("dust", (0.9, 0.95, 1.0), 2.5); gdust_m = E("gdust", (1.0, 0.75, 0.35), 12.0)
DUST = []; rd = random.Random(8)
for k in range(220):
    p = Vector((rd.uniform(-5, 5), rd.uniform(-1.5, 6.5), rd.uniform(0.2, 2.8)))
    o = boxes("dust", [((0, 0, 0), (1, 1, 1))], dust_m); o.visible_shadow = False
    DUST.append(dict(o=o, p=p, s=rd.uniform(0.004, 0.01), ph=rd.uniform(0, 6.28), v=Vector((rd.uniform(-0.04, 0.04), rd.uniform(-0.03, 0.03), rd.uniform(-0.02, 0.03)))))
GD = []
for k in range(90):
    o = boxes("gd", [((0, 0, 0), (1, 1, 1))], gdust_m); o.visible_shadow = False
    GD.append(dict(o=o, a=rd.uniform(0, 6.28), r=rd.uniform(0.6, 1.8), z=rd.uniform(0.1, 1.9), s=rd.uniform(0.01, 0.022), dl=rd.uniform(0, 0.5)))

def alight(name, col, size, loc, look, e=0.0):
    l = bpy.data.lights.new(name, "AREA"); l.size = size; l.color = col; l.energy = e
    o = bpy.data.objects.new(name, l); bpy.context.collection.objects.link(o); o.location = loc
    o.rotation_euler = (Vector(look) - Vector(loc)).to_track_quat("-Z", "Y").to_euler(); return l, o
key, keyo = alight("key", (0.8, 0.88, 1.0), 1.0, (0, 0, 0), (0, 1, 0))
rim, rimo = alight("rim", (0.5, 0.7, 1.0), 1.2, (0, 0, 0), (0, 1, 0))
cam = W.camera((0, -1, 1.4), (0, 3, 1.2), lens=35, fstop=2.0)
cam.data.dof.aperture_blades = 7

# ---------------------------------------------------------------- 時間ごとの値
def stop_at(t): return 1.0 if STOPT <= t < RESUME else 0.0
def dawn_at(t): return ease((t - DAWN + 0.6) / 2.2)
CAB_P = Vector((CAB_X - 0.75, 3.1, 0.0)); TOKI_HIT0 = Vector((0, 2.6, 0)); KN_P = Vector((0.0, 5.7, 0.0)); TOKI_FIN = Vector((0.0, 4.4, 0.0))
def doc_state(t):
    """(姿, 位置, 向き先, 傾きx, 回転z追加, 沈み)"""
    look = MIO_P
    if t < RAISE - 0.2: return "idle", DOC_P, look, 0.0, 0.0, 0.0
    if t < 13.9: return "raise", DOC_P, look, 0.0, 0.0, 0.0
    look = TOKI_P + Vector((0.45, -0.25, 0))
    if t < LUNGE: return "idle", DOC_P, look, 0.0, 0.0, 0.0
    if t < COUNTER: u = ease((t - LUNGE) / 0.35); return "lunge", DOC_P.lerp(DOC_P + (TOKI_P - DOC_P).normalized() * 0.9, u), look, 0.15 * u, 0.0, 0.0
    p1 = DOC_P + (TOKI_P - DOC_P).normalized() * 0.9
    if t < CHAIN: u = ease((t - COUNTER) / 0.3); d_ = (p1 - TOKI_P).normalized(); return "idle", p1 + d_ * 0.7 * u, look, -0.35 * u, 0.0, 0.0
    p2 = p1 + (p1 - TOKI_P).normalized() * 0.7
    if t < SLAM: u = ((t - CHAIN) / (SLAM - CHAIN)) ** 2; return "idle", p2.lerp(CAB_P, u), look, -0.2, 3.0 * u, 0.0
    if t < XSLASH:
        rec = ease((t - SLAM - 0.6) / 1.2); return "idle", CAB_P, TOKI_HIT0, -0.4 * (1 - rec), 0.0, 0.35 * (1 - rec)
    if t < KNEEL: u = ease((t - XSLASH) / 0.8); p = CAB_P.lerp(KN_P, u); p.z = 0.6 * math.sin(math.pi * u); return "idle", p, TOKI_HIT0, -0.3, 9.0 * u, 0.0
    if t < FINISH: return "beg", KN_P, TOKI_FIN, 0.12, 0.0, 0.45
    u = (t - FINISH) / 0.9
    if t < FINISH + 0.9: p = KN_P + Vector((0, 6.0 * u, 1.3 * math.sin(math.pi * min(u, 1)) + 0.5 * u)); return "idle", p, TOKI_FIN, -0.6 - 1.5 * u, 6.0 * u, 0.0
    return "idle", Vector((0.2, OUTY + 6.5, 0.14)), Vector((0.2, OUTY + 10, 0)), -1.52, 0.0, 0.0
def toki_state(t):
    if t < LUNGE: return "idle", TOKI_P, (DOC_P if t < 20 else KN_P)
    if t < COUNTER - 0.1: u = ease((t - LUNGE - 0.15) / 0.25); return "idle", TOKI_P + Vector((0.45, -0.25, 0)) * u, DOC_P
    if t < CHAIN + 0.4: p = TOKI_P + Vector((0.45, -0.25, 0)); hit = doc_state(COUNTER - 0.01)[1]; d = (hit - p).normalized(); return "punch", p.lerp(hit - d * 0.6, ease((t - COUNTER + 0.1) / 0.1)), hit
    base = doc_state(COUNTER - 0.01)[1] - (doc_state(COUNTER - 0.01)[1] - TOKI_P).normalized() * 0.6
    if t < 20.0: return ("punch" if t < SLAM + 0.2 else "idle"), base, doc_state(t)[1]
    if t < FINISH - 0.25: return "idle", base.lerp(TOKI_FIN, ease((t - 20.0) / 0.4)), KN_P
    if t < FINISH + 0.8: return "punch", TOKI_FIN.lerp(KN_P - Vector((0, 0.62, 0)), ease((t - FINISH + 0.25) / 0.25)), KN_P + Vector((0, 1, 0))
    return "idle", KN_P - Vector((0, 0.62, 0)), KN_P + Vector((0, 1, 0))
IMP = [(COUNTER, 1.1, "c"), (SLAM, 1.0, "s"), (XSLASH, 1.2, "x"), (XSLASH + 0.25, 0.9, "x"), (FINISH, 1.4, "f"), (FINISH + 0.25, 1.0, "w")]
def impact_at(t):
    best = (0.0, None, None)
    for ti, s, k in IMP:
        if ti <= t < ti + 0.5:
            v = s * math.exp(-(t - ti) / 0.12)
            if v > best[0]: best = (v, ti, k)
    return best
def impact_point(ti, k):
    if k == "w": return Vector((0, Y1 + 0.5, 2.0))
    return doc_state(ti)[1] + Vector((0, 0, 1.3))

def shot(t):
    dk, dp, dl, drx, drz, dsk = doc_state(t); tk, tp, tl = toki_state(t)
    dh = dp + Vector((0, 0, 1.57 - dsk)); th = tp + Vector((0, 0, 1.44))
    df = (Vector(dl) - dp).normalized(); df.z = 0; tf = (Vector(tl) - tp); tf.z = 0; tf = tf.normalized()
    mh = MIO_P + Vector((0, 0, 1.4))
    if t < 3.3: return dp + df * 0.95 + Vector((-df.y, df.x, 0)) * 0.25 + Vector((0, 0, 1.55)), dh, 46, 2.0, 0
    if t < 6.1: return MIO_P + Vector((0.12, -0.95, 1.42)), mh, 50, 1.8, 1
    if t < RAISE: return dp + df * 1.25 + Vector((0.1, -0.45, 1.5)), dh + Vector((0, 0, -0.08)), 32, 2.4, 2
    if t < STOPT: m = (dp + MIO_P) / 2; return m + Vector((0.2, -1.7, 1.45)), m + Vector((0, 0, 1.4)), 32 + 10 * ease((t - RAISE) / 2.0), 2.4, 3
    if t < 11.6: return Vector((0.5, -2.0 + 0.25 * (t - STOPT), 2.4)), Vector((-0.8, 3.2, 1.1)), 18, 5.6, 4
    if t < LUNGE: return tp + tf * (1.15 - 0.05 * (t - 11.6)) + Vector((tf.y, -tf.x, 0)) * 0.5 + Vector((0, 0, 0.72)), th, 30 + 8 * ease((t - 11.6) / 2.2), 2.2, 5
    if t < CHAIN: m = (tp + dp) / 2; per = Vector((-(dp - tp).y, (dp - tp).x, 0)).normalized(); per = per if per.y < 0 else -per; return m + per * 4.6 + Vector((0, 0, 1.3)), m + Vector((0, 0, 1.05)), 20, 5.6, 6
    if t < HANDS: return Vector((-1.6, -1.2, 1.8)), dp + Vector((0, 0, 1.0)), 22, 5.6, 7
    if t < KNEEL: return tp - tf * 1.9 + Vector((tf.y, -tf.x, 0)) * 1.0 + Vector((0, 0, 1.4)), dp + Vector((0, 0, 1.2)), 20, 5.6, 8
    if t < CLOCK: return dp + Vector((0.0, -0.9, 1.15)), dh, 36, 2.2, 9
    if t < FINISH: return tp + tf * 1.4 + Vector((0.25, 0, 1.55)), th + Vector((0, 0, 0.1)), 26, 4.0, 10
    if t < RESUME: return Vector((0.3, 1.2, 1.6)), dp + Vector((0, 0, 0.8)), 24, 6.0, 11
    if t < VERDICT: return MIO_P + Vector((0.3, -1.3, 1.3)), mh + Vector((0, 0, -0.3)), 34, 2.8, 12
    if t < STAMP: return tp + tf * 0.8 + Vector((0.12, 0, 1.45)), th + Vector((0, 0, -0.03)), 50, 1.8, 13
    if t < DAWN: return dp + Vector((0.0, -1.4, 1.6)), dp + Vector((0, 0.6, 0.1)), 32, 3.5, 14
    if t < FACT: return MIO_P + Vector((0.12, -1.0, 1.43)), mh, 50, 1.8, 15
    return Vector((0.4, -1.4 - 0.12 * (t - FACT), 1.8)), Vector((-0.8, 3.5, 1.2)), 22, 4.0, 16

def side_of(pos, look):
    d = (look - pos); return Vector((d.y, -d.x, 0)).normalized()
def talking(who, t): return any(l[0] <= t <= l[1] - 0.05 for l in LINES if l[5] == who)
def flap(t): return int(t * 12) % 3 != 2
def expr_mio(t):
    tk = talking("mio", t) and flap(t)
    if t < RESUME: e = "tearsadtalk" if tk else "tearsad"
    elif t < DAWN: e = "shockc" if t < RESUME + 0.6 else "tearsmile"
    else: e = "tearsmiletalk" if tk else "tearsmile"
    return e
def expr_doc(t):
    tk = talking("doc", t) and flap(t)
    if t < 13.9: return "coldtalk" if tk else "cold"
    if t < COUNTER: return "cold" if t > LUNGE else "shockc"
    if t < SLAM + 0.3: return "hurt"
    if t < XSLASH: return "shock" if tk else "shockc"
    if t < KNEEL + 0.2: return "hurt"
    if t < FINISH: return "shock" if tk else "shockc"
    return "hurt" if t < FINISH + 1.0 else "dizzy"
def expr_toki(t):
    tk = talking("toki", t) and flap(t)
    if LUNGE <= t < KNEEL or FINISH - 0.3 <= t < FINISH + 0.5: return "coldtalk" if int(t * 10) % 2 else "cold"
    e = "coldtalk" if tk else "cold"
    if STAMP + 0.4 < t: e = "base"
    if (t % 3.7) < 0.12 and not tk: e = "blink"
    return e

def place(t):
    st = stop_at(t); dn = dawn_at(t)
    tf_ = t if t < STOPT else (STOPT if t < RESUME else t - (RESUME - STOPT))
    night = 1.0 - dn
    sun.color = Vector((0.45, 0.6, 1.0)).lerp(Vector((1.0, 0.66, 0.38)), dn)[:]; sun.energy = 0.5 * night + 5.5 * dn
    WIN_E.inputs["Color"].default_value = (*Vector((0.04, 0.06, 0.16)).lerp(Vector((1.0, 0.62, 0.32)), dn), 1); WIN_E.inputs["Strength"].default_value = 1.0 + 5.0 * dn
    for l in LAMPS: l.energy = 70.0 * (1 - 0.5 * dn) * (0.85 + 0.15 * (math.sin(tf_ * 31) > 0.95))
    OPL_K.default_value = 12.0 * (1 - 0.5 * dn); opl.energy = 900.0 * (1 - 0.5 * dn)
    yardl.energy = 300.0 * (t > FINISH) * (1 - 0.5 * dn)
    FOG.nodes["fogcol"].inputs["Color"].default_value = (*Vector((0.02, 0.03, 0.04)).lerp(Vector((0.55, 0.38, 0.26)), dn), 1)
    FOG.nodes["dens"].outputs[0].default_value = 0.045 - 0.02 * dn
    for n in face_em: n.inputs["Strength"].default_value = 0.9 + 0.2 * dn
    door.rotation_euler.z = 0.0; hall.energy = 0.0
    # 医者
    dk, dp, dl, drx, drz, dsk = doc_state(t)
    for k, (r_, tx_, allo) in DM.items():
        on = k == dk
        for o in allo:
            if o.type == "MESH": o.hide_render = not on
        if on:
            face_to(r_, dp, dl); r_.location = dp + Vector((0, 0, -dsk)); r_.location.z = dp.z - dsk
            r_.rotation_euler = (drx, 0, r_.rotation_euler.z + drz)
        T.set_expr(tx_, "doc", expr_doc(t))
    # トキモリ
    tk, tp, tl = toki_state(t); vis = t >= STOPT + 0.45
    for k, (r_, tx_, allo) in TM.items():
        on = vis and k == tk
        for o in allo:
            if o.type == "MESH": o.hide_render = not on
        if k == tk: face_to(r_, tp, tl)
        T.set_expr(tx_, "toki", expr_toki(t))
    tr_ = TM[tk][0]; hand = tr_.matrix_world @ Vector(POSES[tk]["R"][1])
    wlo.location = hand + Vector((0, 0, 0.05)); wl.energy = (3.0 + 40.0 * math.exp(-max(0.0, t - STOPT) / 0.4) * (t >= STOPT)) * vis
    charge = win(t, CLOCK, FINISH + 0.4, 0.8, 0.4)
    FIST_K.default_value = 1.5 * win(t, LUNGE, SLAM + 0.3, 0.2, 0.3) + 25.0 * charge; wl.energy += 120.0 * charge
    WF_K.default_value = 4.0 + 20.0 * math.exp(-max(0.0, t - STOPT) / 0.3) * (t >= STOPT) + 14.0 * math.exp(-max(0.0, t - STAMP) / 0.25) * (t >= STAMP)
    # 金の鎖
    ch_on = CHAIN - 0.05 <= t < SLAM + 0.15
    for i, o in enumerate(CHAINL):
        o.hide_render = not ch_on
        if not ch_on: continue
        reach = ease((t - CHAIN) / 0.25); u = i / (len(CHAINL) - 1) * reach
        a = hand; b = dp + Vector((0, 0, 1.1)); p = a.lerp(b, u) + Vector((0, 0, 0.25 * math.sin(math.pi * u) * (1 - ease((t - CHAIN - 0.3) / 0.3))))
        o.location = p; o.rotation_euler = ((b - a).to_track_quat("Z", "Y").to_euler().x + (i % 2) * 1.57, 0, i * 0.3)
    # 巨大な時計の針・文字盤
    hv = win(t, HANDS, KNEEL + 0.3, 0.4, 0.4) + win(t, CLOCK, FINISH + 0.6, 0.5, 0.4)
    for o in (hour, minute): o.hide_render = hv < 0.02
    tfw = (Vector(tl) - tp); tfw.z = 0; tfw = tfw.normalized(); tsd = Vector((tfw.y, -tfw.x, 0))
    ctr = tp - tfw * 0.5 + Vector((0, 0, 1.9))
    BH_K.default_value = 8.0 * hv + 20.0 * win(t, XSLASH - 0.1, XSLASH + 0.5, 0.1, 0.3)
    spin = (t - HANDS) * 2.0 + 14.0 * ease((t - XSLASH + 0.15) / 0.3) + (t - CLOCK) * 8.0 * (t > CLOCK)
    for o, L, sp in ((hour, 1.0, 0.5), (minute, 1.0, 1.0)):
        ang = spin * sp
        if XSLASH - 0.15 <= t < KNEEL:                                    # 針が前へ伸びて×字に斬る
            reach = ease((t - XSLASH + 0.15) / 0.2); c = ctr.lerp(dp + Vector((0, 0, 1.2)) - tfw * 0.4, reach)
        else: c = ctr
        o.location = c; q = tfw.to_track_quat("Y", "Z"); o.rotation_euler = q.to_euler(); o.rotation_euler.rotate_axis("Y", ang + (0.8 if o is hour else -0.8))
        sc_ = 0.4 + 0.6 * hv; o.scale = (sc_, sc_, sc_)
    dv = win(t, CLOCK, FINISH + 0.6, 0.5, 0.4)
    for o in DIAL_ALL: o.hide_render = dv < 0.02
    dial.location = tp - tfw * 0.7 + Vector((0, 0, 1.6)); dial.rotation_euler = tfw.to_track_quat("Y", "Z").to_euler(); dial.scale = (0.3 + 0.7 * ease((t - CLOCK) / 0.5),) * 3
    # 時を止める金の殻
    u = (t - STOPT) / 0.9; shell.hide_render = not (0 <= u < 1.0)
    if not shell.hide_render: shell.location = TOKI_P + Vector((0, 0, 1.2)); r = 0.2 + 9.0 * ease(u); shell.scale = (r, r, r); SHELL_K.default_value = 0.55 * (1 - u)
    iv, ti, ik = impact_at(t)
    if ti is not None: hitlo.location = impact_point(ti, ik); hitl.energy = 900.0 * iv
    else: hitl.energy = 0.0
    # ガラス
    for d in CSHARD:
        o = d["o"]; dt = t - SLAM
        if dt < 0 or dt > 2.5: o.hide_render = True; continue
        o.hide_render = False; p = Vector((CAB_X - 0.33, CAB_P.y, 0)) + d["off"] + d["v"] * dt + Vector((0, 0, -4.9 * dt * dt)); p.z = max(p.z, 0.01); o.location = p; o.scale = d["s"]; o.rotation_euler = d["w"] * min(dt, 1.0)
    br = t >= FINISH + 0.25
    PANES[1].hide_render = br; MIDWIN.hide_render = br
    for d in SHARDS:
        o = d["o"]; dt = t - FINISH - 0.25
        if dt < 0 or dt > 2.5: o.hide_render = True; continue
        o.hide_render = False; p = d["p"] + d["v"] * dt + Vector((0, 0, -4.9 * dt * dt)); p.z = max(p.z, 0.01); o.location = p; o.scale = d["s"]; o.rotation_euler = d["w"] * min(dt, 1.0)
    # ベルト（時が動きだすとほどける）
    for k, s_ in enumerate(STRAPS):
        o = s_["o"]; dt = t - RESUME - 0.1 * k
        if dt < 0: o.location = s_["p0"]; o.rotation_euler = (0, 0, 0); continue
        o.location = s_["p0"] + Vector((0.3 * (-1) ** k * dt, -0.6 * dt, -2.5 * dt * dt)); o.location.z = max(o.location.z, 0.03); o.rotation_euler = (0, 2.0 * dt * (-1) ** k, 1.0 * dt)
    # 粒
    for d in DUST:
        o = d["o"]; p = d["p"] + d["v"] * tf_ + Vector((0.03 * math.sin(tf_ * 0.7 + d["ph"]), 0.03 * math.cos(tf_ * 0.5 + d["ph"]), 0.02 * math.sin(tf_ + d["ph"])))
        o.location = p; s = d["s"] * (1.4 if st else 1.0); o.scale = (s, s, s)
    for g in GD:
        k = (t - STOPT - g["dl"]) / 0.7; o = g["o"]; o.hide_render = not (0 <= k < 1.15)
        if o.hide_render: continue
        r = g["r"] * (1 - ease(k)); a = g["a"] + 2.5 * k
        o.location = TOKI_P + Vector((r * math.cos(a), r * math.sin(a), g["z"] + (1.0 - g["z"]) * 0.3 * ease(k))); o.scale = (g["s"] * (1 - ease((k - 0.9) / 0.25)),) * 3
    # カメラ
    pos, look, lens, fs, si = shot(t)
    sh = 0.0
    if ti is not None: sh = 0.06 * iv
    pos = pos + Vector((sh * math.sin(t * 61), sh * math.sin(t * 47), sh * math.sin(t * 53)))
    if stop_at(t) == 0 or si >= 6: pos = pos + Vector((0.004 * math.sin(t * 1.3), 0.003 * math.sin(t * 0.9), 0.004 * math.sin(t * 1.7)))
    if "--camover" in sys.argv:
        v = [float(x) for x in arg("--camover", "").split(",")]; pos = Vector(v[0:3]); look = Vector(v[3:6]); lens = v[6]
    keyo.location = pos + side_of(pos, look) * -1.1 + Vector((0, 0, 0.6)); keyo.rotation_euler = (look - keyo.location).to_track_quat("-Z", "Y").to_euler()
    key.energy = 9.0; key.color = Vector((0.8, 0.88, 1.0)).lerp(Vector((1.0, 0.82, 0.65)), dn)[:]
    rimo.location = look + (look - pos).normalized() * 1.0 + Vector((0.4, 0, 0.5)); rimo.rotation_euler = (look - rimo.location).to_track_quat("-Z", "Y").to_euler()
    rim.energy = 30.0 * (1 - dn) + (25.0 if si in (5, 10, 13) else 0.0); rim.color = (0.55, 0.7, 1.0) if si not in (5, 10, 13) else (1.0, 0.75, 0.4)
    cam.location = pos; W.aim(cam, look); cam.data.lens = lens; cam.data.dof.aperture_fstop = fs
    bpy.context.view_layer.update()
    cam.data.dof.focus_distance = max(0.25, (look - pos).length)
    T.set_expr(mtex, "mio", expr_mio(t))
    dash = win(t, LUNGE, COUNTER + 0.15, 0.1, 0.1) + win(t, CHAIN, SLAM, 0.1, 0.05) + win(t, FINISH, FINISH + 0.9, 0.05, 0.3)
    meta = dict(stop=st, dawn=dn, flash=0.0, shot=si, impact=iv, dash=min(1.0, dash))
    if ti is not None:
        sv = world_to_camera_view(sc, cam, impact_point(ti, ik)); meta["imp"] = [sv.x, sv.y, sv.z]
    return meta

frames = TEST or range(START, STOP)
t0 = time.time()
for f in frames:
    p = os.path.join(OUT, "%04d.png" % (f + 1))
    if os.path.exists(p) and not TEST: continue
    t = f / FPS
    meta = place(t)
    bpy.context.view_layer.update()
    wc = Vector((-0.5, Y1 + 2.0, 2.2)); sv = world_to_camera_view(sc, cam, wc)
    meta.update(t=t, sun=[sv.x, sv.y, sv.z], light=0.25 + 0.75 * meta["dawn"])
    json.dump(meta, open(p[:-4] + ".json", "w"))
    tmp = p[:-4] + "_tmp.png"; sc.render.filepath = tmp
    bpy.ops.render.render(write_still=True); os.replace(tmp, p)
    print("frame %s t=%.2f %.1fs" % (p, t, time.time() - t0), flush=True); t0 = time.time()
